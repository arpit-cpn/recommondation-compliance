<template>
  <v-dialog
    :model-value="show"
    @update:model-value="$emit('update:show', $event)"
    max-width="90%"
    max-height="90%"
    persistent
    scrollable
  >
    <v-card class="detail-modal">
      <v-card-title class="d-flex flex-wrap align-center pa-4">
        <div class="batch-header">
          <span class="text-h6">Batch Details: {{ batchId }}</span>
        </div>

        <v-divider vertical class="mx-6" />

        <div class="d-flex align-center gap-4 stats-container flex-grow-1">
          <div class="stat-item" v-for="(value, key) in selectedStats" :key="key">
            <div class="stat-label text-caption text-medium-emphasis">{{ formatStatName(key) }}</div>
            <div class="stat-value">{{ formatStatValue(value) }}</div>
          </div>
        </div>

        <v-btn icon @click="$emit('update:show', false)" class="ms-auto close-btn">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-divider />

      <v-card-text>
        <v-row>
          <!-- Left Panel - Variables List -->
          <v-col cols="4" class="variables-panel">
            <v-list density="compact">
              <v-list-subheader>Variables by Interest</v-list-subheader>

              <!-- Target Variable -->
              <v-list-item
                :active="selectedVariable === targetVariable"
                @click="selectVariable(targetVariable)"
                class="target-variable"
              >
                <template #prepend>
                  <v-icon size="small" color="primary">mdi-target</v-icon>
                </template>
                <v-list-item-title class="d-flex align-center justify-space-between gap-2">
                  <span class="variable-name">{{ formatVariableName(targetVariable) }}</span>
                  <v-chip size="x-small" color="primary">Target</v-chip>
                </v-list-item-title>
                <v-list-item-subtitle class="variable-stats">
                  {{ formatTrendInfo(variableStats[targetVariable]) }}
                </v-list-item-subtitle>
              </v-list-item>

              <v-divider class="my-2" />

              <!-- Other Variables -->
              <v-list-item
                v-for="(stats, variable) in sortedVariables"
                :key="variable"
                :active="selectedVariable === variable"
                @click="selectVariable(variable)"
              >
                <v-list-item-title class="d-flex align-center justify-space-between gap-2">
                  <span class="variable-name">{{ formatVariableName(variable) }}</span>
                  <v-chip
                    size="x-small"
                    :color="getTrendColor(stats)"
                  >
                    {{ getTrendLabel(stats) }}
                  </v-chip>
                </v-list-item-title>
                <v-list-item-subtitle class="variable-stats">
                  {{ formatTrendInfo(stats) }}
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-col>

          <!-- Right Panel - Charts -->
          <v-col cols="8" class="charts-panel">
            <!-- Time Series Chart -->
            <v-card variant="flat" class="mb-4">
              <v-card-title class="text-subtitle-1">Time Series Analysis</v-card-title>
              <div ref="timeSeriesChart" class="time-series-chart" />
            </v-card>

            <!-- Distribution Plot -->
            <v-card variant="flat">
              <v-card-title class="text-subtitle-1">Distribution</v-card-title>
              <div ref="kdePlot" class="kde-plot" />
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script>
import { defineComponent, ref, watch, computed } from 'vue';
import Highcharts from 'highcharts';
import { useTheme } from 'vuetify';

export default defineComponent({
  name: 'BatchDetailModal',

  emits: ['update:show'],

  props: {
    show: {
      type: Boolean,
      required: true,
    },
    batchId: {
      type: String,
      required: false,
      default: null,
    },
    loading: {
      type: Boolean,
      required: true,
    },
    data: {
      type: Array,
      required: false,
      default: null,
    },
    variableStats: {
      type: Object,
      required: true,
    },
    targetVariable: {
      type: String,
      required: true,
    },
  },

  setup(props) {
    const theme = useTheme();
    const timeSeriesChart = ref(null);
    const kdePlot = ref(null);
    const selectedVariable = ref(props.targetVariable);

    const formatVariableName = (name) => {
      return name.replace(/_/g, ' ').replace(/([A-Z])/g, ' $1').trim();
    };

    // Watch for theme changes
    watch(() => theme.current.value.dark, (isDark) => {
      updateChartTheme(isDark);
    });

    // Watch for data changes
    watch(() => props.data, (newData) => {
      if (newData && timeSeriesChart.value) {
        updateCharts();
      }
    });

    // Watch for selected variable changes
    watch(selectedVariable, () => {
      updateCharts();
    });

    // Computed property to sort variables by interest
    const sortedVariables = computed(() => {
      const stats = { ...props.variableStats };
      delete stats[props.targetVariable];

      return Object.entries(stats)
        .sort(([, a], [, b]) => {
          // Sort by absolute trend value (descending)
          const trendA = Math.abs(a?.trend || 0);
          const trendB = Math.abs(b?.trend || 0);
          return trendB - trendA;
        })
        .reduce((acc, [key, value]) => {
          acc[key] = value;
          return acc;
        }, {});
    });

    const getTrendLabel = (stats) => {
      if (!stats) return 'No Data';
      const trend = stats.trend || 0;
      if (Math.abs(trend) < 0.05) return 'Stable';
      return trend > 0 ? 'Increasing' : 'Decreasing';
    };

    const getTrendColor = (stats) => {
      if (!stats) return 'grey';
      const trend = stats.trend || 0;
      if (Math.abs(trend) < 0.05) return 'info';
      return trend > 0 ? 'success' : 'error';
    };

    const formatTrendInfo = (stats) => {
      if (!stats) return 'No statistics available';
      const trend = (stats.trend || 0).toFixed(2);
      const volatility = (stats.volatility || 0).toFixed(1);
      const mean = (stats.mean || 0).toFixed(2);
      return `Trend: ${trend}/hr • Vol: ${volatility}% • Mean: ${mean}`;
    };

    const updateChartTheme = (isDark) => {
      const textColor = isDark ? '#E0E0E0' : '#2c3e50';
      const backgroundColor = isDark ? '#1E1E1E' : '#ffffff';
      const gridColor = isDark ? '#333333' : '#ebeef5';

      // Update time series chart theme
      if (timeSeriesChart.value) {
        const tsChart = Highcharts.charts[Highcharts.charts.length - 2];
        if (tsChart) {
          tsChart.update({
            chart: { backgroundColor },
            title: { style: { color: textColor } },
            xAxis: {
              gridLineColor: gridColor,
              labels: { style: { color: textColor } },
            },
            yAxis: {
              gridLineColor: gridColor,
              labels: { style: { color: textColor } },
            },
          });
        }
      }

      // Update KDE plot theme
      if (kdePlot.value) {
        const kdeChart = Highcharts.charts[Highcharts.charts.length - 1];
        if (kdeChart) {
          kdeChart.update({
            chart: { backgroundColor },
            title: { style: { color: textColor } },
            xAxis: {
              gridLineColor: gridColor,
              labels: { style: { color: textColor } },
            },
            yAxis: {
              gridLineColor: gridColor,
              labels: { style: { color: textColor } },
            },
          });
        }
      }
    };

    const updateCharts = () => {
      if (!props.data || !selectedVariable.value) return;

      const isDark = theme.current.value.dark;
      const textColor = isDark ? '#E0E0E0' : '#2c3e50';
      const backgroundColor = isDark ? '#1E1E1E' : '#ffffff';
      const gridColor = isDark ? '#333333' : '#ebeef5';

      // Prepare time series data and run state zones
      const timeSeriesData = props.data.map(item => [
        new Date(item.DateTime).getTime(),
        item[selectedVariable.value],
      ]).filter(point => point[1] !== null);

      // Create zones for run states
      const zones = [];
      let currentZone = null;

      props.data.forEach((item, index) => {
        const time = new Date(item.DateTime).getTime();
        const isUptime = item.run_state === 'Uptime';

        if (!currentZone || currentZone.isUptime !== isUptime) {
          if (currentZone) {
            currentZone.end = time;
          }
          currentZone = {
            start: time,
            isUptime,
          };
          zones.push(currentZone);
        }

        // Handle last point
        if (index === props.data.length - 1) {
          currentZone.end = time;
        }
      });

      // Create time series chart
      Highcharts.chart(timeSeriesChart.value, {
        chart: {
          type: 'line',
          backgroundColor: backgroundColor,
          height: 300,
        },
        title: {
          text: `${formatVariableName(selectedVariable.value)} Over Time`,
          style: { color: textColor },
        },
        xAxis: {
          type: 'datetime',
          gridLineColor: gridColor,
          labels: { style: { color: textColor } },
          plotBands: zones.map(zone => ({
            from: zone.start,
            to: zone.end,
            color: zone.isUptime
              ? 'rgba(76, 175, 80, 0.1)' // Light green for Uptime
              : 'rgba(244, 67, 54, 0.1)', // Light red for Downtime
          })),
        },
        yAxis: {
          title: {
            text: formatVariableName(selectedVariable.value),
            style: { color: textColor },
          },
          gridLineColor: gridColor,
          labels: { style: { color: textColor } },
        },
        tooltip: {
          formatter: function() {
            const point = this.point;
            const timestamp = Highcharts.dateFormat('%Y-%m-%d %H:%M:%S', point.x);
            const value = point.y.toFixed(2);
            const runState = props.data.find(d => new Date(d.DateTime).getTime() === point.x)?.run_state;

            return `<b>Time:</b> ${timestamp}<br/>
                    <b>Value:</b> ${value}<br/>
                    <b>State:</b> <span style="color: ${runState === 'Uptime' ? '#4CAF50' : '#F44336'}">${runState || 'Unknown'}</span>`;
          },
        },
        series: [{
          name: formatVariableName(selectedVariable.value),
          data: timeSeriesData,
          color: '#409eff',
          states: {
            hover: {
              lineWidth: 2,
            },
          },
        }],
        credits: { enabled: false },
        legend: {
          enabled: true,
          align: 'right',
          verticalAlign: 'top',
          floating: true,
          backgroundColor: backgroundColor,
          itemStyle: {
            color: textColor,
          },
        },
      });

      // Create KDE plot
      const values = timeSeriesData.map(point => point[1]);
      const kde = calculateKDE(values);

      Highcharts.chart(kdePlot.value, {
        chart: {
          type: 'area',
          backgroundColor: backgroundColor,
          height: 200,
        },
        title: {
          text: 'Distribution',
          style: { color: textColor },
        },
        xAxis: {
          gridLineColor: gridColor,
          labels: { style: { color: textColor } },
        },
        yAxis: {
          title: { text: 'Density' },
          gridLineColor: gridColor,
          labels: { style: { color: textColor } },
        },
        series: [{
          name: 'Density',
          data: kde,
          color: '#409eff',
          fillOpacity: 0.3,
        }],
        credits: { enabled: false },
      });
    };

    const calculateKDE = (data) => {
      // Simple KDE implementation
      const min = Math.min(...data);
      const max = Math.max(...data);
      const points = 50;
      const bandwidth = (max - min) / Math.sqrt(data.length);
      const step = (max - min) / points;

      const kde = [];
      for (let x = min; x <= max; x += step) {
        let density = 0;
        for (const point of data) {
          density += Math.exp(-Math.pow(x - point, 2) / (2 * Math.pow(bandwidth, 2)));
        }
        density /= (data.length * bandwidth * Math.sqrt(2 * Math.PI));
        kde.push([x, density]);
      }

      return kde;
    };

    // Initialize charts when mounted
    if (props.data) {
      updateCharts();
    }

    return {
      timeSeriesChart,
      kdePlot,
      selectedVariable,
      theme,
      updateCharts,
      calculateKDE,
      formatVariableName,
      sortedVariables,
      getTrendLabel,
      getTrendColor,
      formatTrendInfo,
    };
  },

  methods: {
    selectVariable(variable) {
      this.selectedVariable = variable;
    },

    formatStatName(name) {
      const nameMap = {
        mean: 'Mean',
        std: 'Std Dev',
        trend: 'Trend (per hour)',
        volatility: 'Volatility (%)',
        min: 'Minimum',
        max: 'Maximum',
        range: 'Range',
      };
      return nameMap[name] || name;
    },

    formatStatValue(value) {
      if (typeof value !== 'number') return value;
      if (Math.abs(value) < 0.01) return value.toExponential(2);
      return value.toFixed(2);
    },
  },

  computed: {
    selectedStats() {
      return this.variableStats[this.selectedVariable] || {};
    },
  },
});
</script>

<style scoped>
.detail-modal {
  max-height: 90vh;
}

.variables-panel {
  border-right: 1px solid v-bind('theme.current.value.dark ? "#333333" : "#ebeef5"');
  max-height: 70vh;
  overflow-y: auto;
  padding-right: 16px;
}

.charts-panel {
  max-height: 70vh;
  overflow-y: auto;
}

.time-series-chart {
  height: 300px;
  border-radius: 8px;
  overflow: hidden;
}

.kde-plot {
  height: 250px;
  border-radius: 8px;
  overflow: hidden;
}

.variable-name {
  font-size: 0.9rem;
  line-height: 1.2;
  flex: 1;
  white-space: normal;
  word-wrap: break-word;
}

.variable-stats {
  font-size: 0.75rem !important;
  color: v-bind('theme.current.value.dark ? "#aaa" : "#666"');
  margin-top: 4px;
  white-space: normal;
  line-height: 1.3;
}

.target-variable {
  background-color: v-bind('theme.current.value.dark ? "#1a237e15" : "#e3f2fd"');
  border-left: 3px solid v-bind('theme.current.value.dark ? "#5c6bc0" : "#1976d2"');
}

.target-variable:hover {
  background-color: v-bind('theme.current.value.dark ? "#1a237e25" : "#bbdefb"') !important;
}

:deep(.v-list-item--active) {
  background-color: v-bind('theme.current.value.dark ? "#333333" : "#f0f9ff"');
  border-left: 3px solid v-bind('theme.current.value.dark ? "#5c6bc0" : "#1976d2"');
}

:deep(.v-list-item) {
  margin-bottom: 6px;
  padding: 8px 12px;
  border-radius: 4px;
  border-left: 3px solid transparent;
}

:deep(.v-list-item:hover) {
  background-color: v-bind('theme.current.value.dark ? "#333333" : "#f5f5f5"');
}

:deep(.v-card) {
  border: 1px solid v-bind('theme.current.value.dark ? "#333333" : "#ebeef5"');
  border-radius: 8px;
}

:deep(.v-card-title) {
  font-size: 1rem !important;
  padding: 12px 16px;
  border-bottom: 1px solid v-bind('theme.current.value.dark ? "#333333" : "#ebeef5"');
}

:deep(.v-card-text) {
  padding: 16px;
}

:deep(.v-table) {
  background-color: transparent !important;
}

:deep(.v-list) {
  padding: 8px;
}

:deep(.gap-2) {
  gap: 8px;
}

.batch-header {
  min-width: 200px;
  flex-shrink: 0;
  padding-right: 8px;
}

.stats-container {
  overflow-x: auto;
  flex-wrap: nowrap;
  min-width: 0;
  padding-left: 8px;
}

.stat-item {
  min-width: 100px;
  padding: 0 12px;
  border-right: 1px solid v-bind('theme.current.value.dark ? "#333333" : "#e0e0e0"');
  white-space: nowrap;
}

.stat-item:last-child {
  border-right: none;
  padding-right: 0;
}

.stat-label {
  font-size: 0.7rem;
  margin-bottom: 2px;
  color: v-bind('theme.current.value.dark ? "#aaa" : "#666"');
}

.stat-value {
  font-size: 0.9rem;
  font-weight: 500;
  color: v-bind('theme.current.value.dark ? "#E0E0E0" : "#2c3e50"');
}

:deep(.v-card-title) {
  min-height: 64px;
}

.close-btn {
  flex-shrink: 0;
  margin-left: 8px !important;
}
</style>