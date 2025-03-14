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
              <v-list-subheader class="d-flex align-center justify-space-between">
                <span>Variables by Correlation & Interest</span>
                <v-btn
                  icon="mdi-matrix"
                  size="small"
                  variant="text"
                  @click="showCorrelationMatrix = true"
                  title="Show Correlation Matrix"
                />
              </v-list-subheader>

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
                  <div class="d-flex align-center gap-1">
                    <v-chip
                      size="x-small"
                      :color="getCorrelationColor(stats)"
                      class="correlation-chip"
                    >
                      {{ formatCorrelation(stats.correlation) }}
                    </v-chip>
                    <v-chip
                      size="x-small"
                      :color="getTrendColor(stats)"
                    >
                      {{ getTrendLabel(stats) }}
                    </v-chip>
                  </div>
                </v-list-item-title>
                <v-list-item-subtitle class="variable-stats">
                  {{ formatTrendInfo(stats) }}
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-col>

          <!-- Right Panel - Charts -->
          <v-col cols="8" class="charts-panel">
            <v-card variant="flat" class="h-100">
              <v-tabs v-model="activeChartTab">
                <v-tab value="analysis">Analysis</v-tab>
                <v-tab value="correlation">Correlation</v-tab>
                <v-switch
                  v-model="showDowntime"
                  label="Show Downtime"
                  hide-details
                  density="compact"
                  color="primary"
                  class="ma-0 pa-0 ms-auto"
                  style="margin-right: 8px"
                />
              </v-tabs>

              <v-window v-model="activeChartTab">
                <!-- Analysis Tab -->
                <v-window-item value="analysis">
                  <v-card-text class="pa-2">
                    <div class="d-flex flex-column gap-2">
                      <!-- Time Series Chart -->
                      <v-card variant="flat" class="pa-2">
                        <div class="d-flex align-center px-2">
                          <span class="text-subtitle-2">Time Series Analysis</span>
                        </div>
                        <div ref="timeSeriesChart" class="time-series-chart" />
                      </v-card>

                      <!-- Distribution Plot -->
                      <v-card variant="flat" class="pa-2">
                        <div class="d-flex align-center px-2">
                          <span class="text-subtitle-2">Distribution Analysis</span>
                        </div>
                        <div ref="kdePlot" class="kde-plot" />
                      </v-card>
                    </div>
                  </v-card-text>
                </v-window-item>

                <!-- Correlation Tab -->
                <v-window-item value="correlation">
                  <v-card-text class="pa-2">
                    <v-card variant="flat" class="pa-2">
                      <div class="d-flex align-center px-2">
                        <span class="text-subtitle-2">Cross-Correlation Analysis</span>
                      </div>
                      <div ref="correlationTimeSeries" class="correlation-time-series" />
                    </v-card>
                  </v-card-text>
                </v-window-item>
              </v-window>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>

      <!-- Correlation Matrix Dialog -->
      <v-dialog
        v-model="showCorrelationMatrix"
        max-width="900px"
        class="correlation-dialog"
      >
        <v-card>
          <v-card-title class="d-flex align-center justify-space-between pa-4">
            <span>Correlation Analysis</span>
            <v-btn icon="mdi-close" variant="text" @click="showCorrelationMatrix = false" />
          </v-card-title>

          <v-card-text>
            <div class="correlation-matrix">
              <div class="correlation-table">
                <table>
                  <thead>
                    <tr>
                      <th>Variable</th>
                      <th>Correlation with {{ formatVariableName(targetVariable) }}</th>
                      <th>Trend</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(stats, variable) in sortedByCorrelation" :key="variable">
                      <td>{{ formatVariableName(variable) }}</td>
                      <td>
                        <div class="d-flex align-center gap-2">
                          <div
                            class="correlation-bar"
                            :style="getCorrelationBarStyle(stats.correlation)"
                          />
                          <span>{{ formatCorrelation(stats.correlation) }}</span>
                        </div>
                      </td>
                      <td>
                        <v-chip
                          size="x-small"
                          :color="getTrendColor(stats)"
                        >
                          {{ getTrendLabel(stats) }}
                        </v-chip>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-dialog>
    </v-card>
  </v-dialog>
</template>

<script>
import { defineComponent, ref, watch, computed, nextTick, onMounted } from 'vue';
import Highcharts from 'highcharts';
import HighchartsHeatmap from 'highcharts/modules/heatmap';
import { useTheme } from 'vuetify';

// Initialize Highcharts modules
HighchartsHeatmap(Highcharts);

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
    correlationsData: {
      type: Object,
      required: false,
      default: () => ({}),
    },
  },

  setup(props) {
    const theme = useTheme();
    const timeSeriesChart = ref(null);
    const kdePlot = ref(null);
    const correlationTimeSeries = ref(null);
    const selectedVariable = ref(props.targetVariable);
    const showCorrelationMatrix = ref(false);
    const activeChartTab = ref('analysis');
    const showDowntime = ref(true);
    let charts = {
      timeSeries: null,
      kde: null,
      correlation: null,
    };

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
        updateAnalysisCharts();
      }
    });

    // Watch for selected variable changes
    watch(selectedVariable, () => {
      if (activeChartTab.value === 'analysis') {
        updateAnalysisCharts();
      } else if (activeChartTab.value === 'correlation') {
        updateCorrelationTimeSeries();
      }
    });

    // Watch for correlation matrix visibility
    watch(showCorrelationMatrix, (isVisible) => {
      if (isVisible && activeChartTab.value === 'correlation') {
        nextTick(() => {
          updateCorrelationTimeSeries();
        });
      }
    });

    // Watch for tab changes
    watch(activeChartTab, (newTab) => {
      nextTick(() => {
        if (newTab === 'analysis') {
          updateAnalysisCharts();
        } else if (newTab === 'correlation') {
          updateCorrelationTimeSeries();
        }
      });
    }, { immediate: true });

    // Watch for correlationsData changes
    watch(() => props.correlationsData, (newData) => {
      if (newData && activeChartTab.value === 'correlation') {
        nextTick(() => {
          updateCorrelationTimeSeries();
        });
      }
    }, { deep: true });

    // Watch for showDowntime changes
    watch(showDowntime, () => {
      nextTick(() => {
        if (activeChartTab.value === 'analysis') {
          updateAnalysisCharts();
        } else if (activeChartTab.value === 'correlation') {
          updateCorrelationTimeSeries();
        }
      });
    });

    // Computed property to sort variables by interest
    const sortedVariables = computed(() => {
      const stats = { ...props.variableStats };
      delete stats[props.targetVariable];

      return Object.entries(stats)
        .sort(([, a], [, b]) => {
          // First sort by correlation magnitude (absolute value, descending)
          const corrA = Math.abs(a?.correlation || 0);
          const corrB = Math.abs(b?.correlation || 0);
          if (Math.abs(corrA - corrB) > 0.001) return corrB - corrA;

          // Then sort by trend status (increasing/decreasing before stable)
          const trendA = Math.abs(a?.trend || 0);
          const trendB = Math.abs(b?.trend || 0);
          const isStableA = Math.abs(trendA) < 0.05;
          const isStableB = Math.abs(trendB) < 0.05;

          if (isStableA !== isStableB) {
            return isStableA ? 1 : -1; // Non-stable (increasing/decreasing) comes first
          }

          // For variables with same stability status, sort by trend magnitude
          return Math.abs(trendB) - Math.abs(trendA);
        })
        .reduce((acc, [key, value]) => {
          acc[key] = value;
          return acc;
        }, {});
    });

    const sortedByCorrelation = computed(() => {
      const stats = { ...props.variableStats };
      delete stats[props.targetVariable];

      return Object.entries(stats)
        .sort(([, a], [, b]) => {
          // First sort by correlation magnitude (absolute value, descending)
          const corrA = Math.abs(a?.correlation || 0);
          const corrB = Math.abs(b?.correlation || 0);
          if (Math.abs(corrA - corrB) > 0.001) return corrB - corrA;

          // Then sort by trend status (increasing/decreasing before stable)
          const trendA = Math.abs(a?.trend || 0);
          const trendB = Math.abs(b?.trend || 0);
          const isStableA = Math.abs(trendA) < 0.05;
          const isStableB = Math.abs(trendB) < 0.05;

          if (isStableA !== isStableB) {
            return isStableA ? 1 : -1; // Non-stable (increasing/decreasing) comes first
          }

          // For variables with same stability status, sort by trend magnitude
          return Math.abs(trendB) - Math.abs(trendA);
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

    const getCorrelationColor = (stats) => {
      if (!stats?.correlation) return 'grey';
      const correlation = Math.abs(stats.correlation);
      if (correlation > 0.7) return 'error';
      if (correlation > 0.4) return 'warning';
      return 'info';
    };

    const formatCorrelation = (correlation) => {
      if (!correlation) return 'N/A';
      return correlation.toFixed(2);
    };

    const getCorrelationBarStyle = (correlation) => {
      if (!correlation) return { width: '0%' };
      const width = Math.abs(correlation) * 100;
      const color = correlation > 0 ? '#4CAF50' : '#F44336';
      return {
        width: `${width}%`,
        backgroundColor: color,
      };
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

    const updateAnalysisCharts = () => {
      if (!props.data || !selectedVariable.value) return;
      const isDark = theme.current.value.dark;
      const textColor = isDark ? '#E0E0E0' : '#2c3e50';
      const backgroundColor = isDark ? '#1E1E1E' : '#ffffff';
      const gridColor = isDark ? '#333333' : '#ebeef5';

      // Prepare time series data
      const TWO_MINUTES = 2 * 60 * 1000; // 2 minutes in milliseconds

      // First find all transition points
      const transitions = [];
      props.data.forEach((item, index) => {
        if (index > 0) {
          const prevState = props.data[index - 1].run_state;
          const currentState = item.run_state;
          if (prevState !== currentState) {
            transitions.push(new Date(item.DateTime).getTime());
          }
        }
      });

      // Filter data points
      const timeSeriesData = props.data
        .filter(item => {
          if (!showDowntime.value && item.run_state !== 'Uptime') return false;

          // Check if point is within 2 minutes of any transition
          const itemTime = new Date(item.DateTime).getTime();
          const isNearTransition = transitions.some(transitionTime =>
            Math.abs(itemTime - transitionTime) <= TWO_MINUTES,
          );

          return !isNearTransition;
        })
        .map(item => {
          const time = new Date(item.DateTime).getTime();
          const value = item[selectedVariable.value];
          const runState = item.run_state;

          return {
            x: time,
            y: value,
            runState: runState,
          };
        })
        .filter(point => point.y !== null);

      // length of timeSeriesData
      console.log(timeSeriesData.length);

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

        if (index === props.data.length - 1) {
          currentZone.end = time;
        }
      });

      // Update or create time series chart
      if (timeSeriesChart.value) {
        if (charts.timeSeries) {
          charts.timeSeries.destroy();
        }
        charts.timeSeries = Highcharts.chart(timeSeriesChart.value, {
          chart: {
            type: 'line',
            backgroundColor: backgroundColor,
            height: 260,
            marginTop: 10,
            marginBottom: 40,
            marginRight: 20,
            marginLeft: 80,
            spacingBottom: 0,
            spacingTop: 0,
          },
          title: {
            text: null,
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
            connectNulls: false,
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
      }

      // Update or create KDE plot
      if (kdePlot.value) {
        const values = timeSeriesData.map(point => point.y);
        const kde = calculateKDE(values);

        if (charts.kde) {
          charts.kde.destroy();
        }
        charts.kde = Highcharts.chart(kdePlot.value, {
          chart: {
            type: 'area',
            backgroundColor: backgroundColor,
            height: 180,
            marginTop: 10,
            marginBottom: 50,
            marginRight: 20,
            marginLeft: 80,
            spacingBottom: 0,
            spacingTop: 0,
          },
          title: {
            text: null,
          },
          xAxis: {
            gridLineColor: gridColor,
            labels: { style: { color: textColor } },
            title: {
              text: formatVariableName(selectedVariable.value),
              style: { color: textColor },
            },
          },
          yAxis: {
            title: {
              text: 'Density',
              style: { color: textColor },
              margin: 60,
              rotation: 0,
              align: 'high',
              y: -20,
            },
            gridLineColor: gridColor,
            labels: { style: { color: textColor } },
          },
          tooltip: {
            formatter: function() {
              return `<b>Value:</b> ${this.x.toFixed(2)}<br/>
                      <b>Density:</b> ${this.y.toFixed(4)}`;
            },
          },
          series: [{
            name: 'Density',
            data: kde,
            color: '#409eff',
            fillOpacity: 0.3,
          }],
          credits: { enabled: false },
          legend: {
            enabled: false,
          },
        });
      }
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

    const updateCorrelationTimeSeries = () => {
      if (!correlationTimeSeries.value || !selectedVariable.value) return;
      const isDark = theme.current.value.dark;
      const textColor = isDark ? '#E0E0E0' : '#2c3e50';
      const backgroundColor = isDark ? '#1E1E1E' : '#ffffff';
      const gridColor = isDark ? '#333333' : '#ebeef5';

      // If selected variable is target variable, show heatmap
      if (selectedVariable.value === props.targetVariable) {
        if (charts.correlation) {
          charts.correlation.destroy();
        }

        // Prepare heatmap data
        const variables = Object.keys(props.variableStats).filter(v => v !== props.targetVariable);
        const heatmapData = variables.map((variable, i) => {
          const stats = props.variableStats[variable];
          return [0, i, stats?.correlation || 0];
        });

        charts.correlation = Highcharts.chart(correlationTimeSeries.value, {
          chart: {
            type: 'heatmap',
            backgroundColor: backgroundColor,
            height: 400,
            marginTop: 10,
            marginBottom: 80,
            marginRight: 20,
            marginLeft: 200,
            spacingBottom: 0,
            spacingTop: 0,
          },
          title: {
            text: null,
          },
          xAxis: {
            visible: false,
            min: -0.5,
            max: 0.5,
          },
          yAxis: {
            categories: variables.map(formatVariableName),
            title: null,
            labels: {
              style: { color: textColor },
            },
          },
          colorAxis: {
            stops: [
              [0, '#ef5350'],    // Strong negative - red
              [0.2, '#ff8a65'],  // Moderate negative - light red
              [0.4, '#ffcc80'],  // Weak negative - orange
              [0.6, '#a5d6a7'],  // Weak positive - light green
              [0.8, '#66bb6a'],  // Moderate positive - green
              [1, '#43a047'],    // Strong positive - dark green
            ],
            min: -1,
            max: 1,
          },
          legend: {
            align: 'center',
            layout: 'horizontal',
            verticalAlign: 'bottom',
            symbolWidth: 300,
            symbolHeight: 12,
            margin: 24,
            y: 15,
            title: {
              text: 'Correlation Scale',
              style: { color: textColor },
            },
          },
          tooltip: {
            formatter: function() {
              const variable = variables[this.point.y];
              const correlation = this.point.value.toFixed(3);
              const stats = props.variableStats[variable];
              const trend = getTrendLabel(stats);
              const trendColor = getTrendColor(stats);

              return `<b>${formatVariableName(variable)}</b><br/>
                     <b>Correlation:</b> ${correlation}<br/>
                     <b>Trend:</b> <span style="color: ${trendColor === 'success' ? '#4CAF50' : trendColor === 'error' ? '#F44336' : '#2196F3'}">${trend}</span>`;
            },
          },
          series: [{
            name: 'Correlation with ' + formatVariableName(props.targetVariable),
            data: heatmapData,
            dataLabels: {
              enabled: true,
              color: textColor,
              formatter: function() {
                return this.point.value.toFixed(2);
              },
            },
          }],
          credits: { enabled: false },
        });
        return;
      }

      // Regular correlation time series code for non-target variables
      const correlationData = props.correlationsData[selectedVariable.value] || [];
      console.log(correlationData.length);

      const TWO_MINUTES = 2 * 60 * 1000; // 2 minutes in milliseconds

      // Create zones for run states using correlation data
      const zones = [];
      let currentZone = null;

      correlationData.forEach((point, index) => {
        const timestamp = point[0];
        const isUptime = point[2] === 'Uptime';

        if (!currentZone || currentZone.isUptime !== isUptime) {
          if (currentZone) {
            currentZone.end = timestamp;
            zones.push(currentZone);
          }
          currentZone = {
            start: timestamp,
            isUptime,
          };
        }

        // Handle the last point
        if (index === correlationData.length - 1) {
          currentZone.end = timestamp;
          zones.push(currentZone);
        }
      });

      // Process correlation data to include run state
      const correlationTransitions = [];
      correlationData.forEach((point, index) => {
        if (index > 0) {
          const prevState = correlationData[index - 1][2];
          const currentState = point[2];
          if (prevState !== currentState) {
            correlationTransitions.push(point[0]);
          }
        }
      });

      const processedData = correlationData
        .filter(point => {
          if (!showDowntime.value && point[2] !== 'Uptime') return false;

          // Check if point is within 2 minutes of any transition
          const pointTime = point[0];
          const isNearTransition = correlationTransitions.some(transitionTime =>
            Math.abs(pointTime - transitionTime) <= TWO_MINUTES,
          );

          return !isNearTransition;
        })
        .map(point => {
          const timestamp = point[0];
          const correlation = point[1];
          const runState = point[2];

          return {
            x: timestamp,
            y: correlation,
            runState: runState,
            color: runState === 'Uptime' ? undefined : '#9e9e9e',
          };
        });

      if (charts.correlation) {
        charts.correlation.destroy();
      }

      charts.correlation = Highcharts.chart(correlationTimeSeries.value, {
        chart: {
          type: 'line',
          backgroundColor: backgroundColor,
          height: 400,
          marginTop: 10,
          marginBottom: 40,
          marginRight: 20,
          marginLeft: 80,
          spacingBottom: 0,
          spacingTop: 0,
        },
        title: {
          text: null,
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
            text: 'Correlation',
            style: { color: textColor },
          },
          min: -1,
          max: 1,
          tickInterval: 0.2,
          gridLineColor: gridColor,
          labels: { style: { color: textColor } },
          plotLines: [{
            value: 0,
            color: gridColor,
            width: 1,
            zIndex: 1,
          }],
        },
        tooltip: {
          formatter: function() {
            const point = this.point;
            const timestamp = Highcharts.dateFormat('%Y-%m-%d %H:%M:%S', point.x);
            const correlation = point.y.toFixed(3);
            const runState = point.runState;

            return `<b>Time:</b> ${timestamp}<br/>
                    <b>Correlation:</b> ${correlation}<br/>
                    <b>State:</b> <span style="color: ${runState === 'Uptime' ? '#4CAF50' : '#9e9e9e'}">${runState}</span>`;
          },
        },
        plotOptions: {
          series: {
            states: {
              hover: {
                enabled: true,
                lineWidth: 2,
              },
            },
          },
        },
        series: [{
          name: `Correlation with ${formatVariableName(props.targetVariable)}`,
          data: processedData,
          zones: [{
            value: -0.6,
            color: '#ef5350',  // Strong negative - red
          }, {
            value: -0.3,
            color: '#ff8a65',  // Moderate negative - light red
          }, {
            value: 0,
            color: '#ffcc80',  // Weak negative - orange
          }, {
            value: 0.3,
            color: '#a5d6a7',  // Weak positive - light green
          }, {
            value: 0.6,
            color: '#66bb6a',  // Moderate positive - green
          }, {
            color: '#43a047',  // Strong positive - dark green
          }],
          zoneAxis: 'y',
          lineWidth: 2,
          marker: {
            enabled: true,
            radius: 3,
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
    };

    // Initialize charts when mounted
    onMounted(() => {
      if (props.data) {
        nextTick(() => {
          updateAnalysisCharts();
        });
      }
    });

    return {
      timeSeriesChart,
      kdePlot,
      correlationTimeSeries,
      selectedVariable,
      theme,
      showCorrelationMatrix,
      activeChartTab,
      showDowntime,
      updateAnalysisCharts,
      calculateKDE,
      formatVariableName,
      sortedVariables,
      sortedByCorrelation,
      getTrendLabel,
      getTrendColor,
      getCorrelationColor,
      formatCorrelation,
      getCorrelationBarStyle,
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
  display: flex;
  flex-direction: column;
}

.variables-panel {
  border-right: 1px solid v-bind('theme.current.value.dark ? "#333333" : "#ebeef5"');
  height: calc(90vh - 120px);
  overflow-y: auto;
  padding-right: 16px;
}

.charts-panel {
  height: calc(90vh - 120px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

:deep(.v-window) {
  flex: 1;
  margin-top: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

:deep(.v-window__container) {
  height: 100%;
}

:deep(.v-window-item) {
  height: 100%;
  overflow: auto;
  padding: 16px;
}

:deep(.v-card-text) {
  padding: 8px;
  height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.time-series-chart {
  height: 260px;
  border-radius: 4px;
  overflow: visible;
  margin: 0;
  margin-bottom: 8px;
}

.kde-plot {
  height: 180px;
  border-radius: 4px;
  overflow: visible;
  margin: 0;
  margin-bottom: 8px;
}

.correlation-time-series {
  height: 400px;
  border-radius: 4px;
  overflow: visible;
  margin: 0;
  width: 100%;
  min-height: 400px;
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
  padding: 8px 12px;
  min-height: unset;
  border-bottom: 1px solid v-bind('theme.current.value.dark ? "#333333" : "#ebeef5"');
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

.correlation-chip {
  min-width: 48px;
  text-align: center;
}

.correlation-matrix {
  max-height: 60vh;
  overflow-y: auto;
}

.correlation-table {
  width: 100%;
}

.correlation-table table {
  width: 100%;
  border-collapse: collapse;
}

.correlation-table th,
.correlation-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid v-bind('theme.current.value.dark ? "#333333" : "#ebeef5"');
  vertical-align: middle;
}

.correlation-table th {
  font-weight: 500;
  background-color: v-bind('theme.current.value.dark ? "#1E1E1E" : "#f8f9fa"');
}

.correlation-bar {
  height: 8px;
  border-radius: 4px;
  background-color: #4CAF50;
  min-width: 2px;
  transition: width 0.3s ease;
}

.correlation-dialog {
  border-radius: 8px;
  overflow: hidden;
}

.v-tabs {
  border-bottom: 1px solid v-bind('theme.current.value.dark ? "#333333" : "#ebeef5"');
}

.v-window {
  margin-top: 16px;
}

:deep(.v-tabs) {
  height: 36px;
  .v-tab {
    height: 36px;
  }
}

:deep(.v-card.v-card--flat) {
  margin-bottom: 8px;
  .pa-2 {
    padding: 4px 8px !important;
  }
}
</style>