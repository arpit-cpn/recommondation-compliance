<template>
  <div class="dashboard-container">
    <div class="controls">
      <div class="control-group">
        <v-select
          v-model="filters.site"
          :items="availableSites"
          label="Site"
          density="compact"
          variant="outlined"
          class="control-select"
        />
      </div>

      <div class="control-group">
        <v-select
          v-model="filters.line"
          :items="availableLines"
          label="Line"
          density="compact"
          variant="outlined"
          :item-value="line => line.toLowerCase()"
          class="control-select"
        />
      </div>

      <div class="control-group">
        <v-select
          v-model="filters.partFamily"
          :items="availablePartFamilies"
          label="Part Family"
          density="compact"
          variant="outlined"
          class="control-select"
          style="min-width: 200px;"
        />
      </div>

      <div class="control-group">
        <v-select
          v-model="filters.targetVariable"
          :items="availableTargetVariables"
          label="Target Variable"
          density="compact"
          variant="outlined"
          item-title="label"
          item-value="value"
          class="control-select"
          style="min-width: 150px;"
        />
      </div>

      <div class="control-group">
        <v-select
          v-model="filters.timeRange"
          :items="availableTimeRanges"
          label="Time Range"
          density="compact"
          variant="outlined"
          item-title="label"
          item-value="value"
          class="control-select"
        />
      </div>

      <v-btn
        @click="updateChart"
        :loading="loading"
        :disabled="loading"
        color="primary"
        class="ml-2 update-btn"
      >
        {{ loading ? 'Loading...' : 'Update Chart' }}
      </v-btn>
    </div>

    <v-card class="legend-info mb-4" variant="flat">
      <v-card-text class="d-flex align-center">
        <div class="d-flex align-center legend-item"><v-icon color="success" size="small" class="me-1">mdi-circle</v-icon> Recommendation batches</div>
        <div class="d-flex align-center legend-item"><v-icon color="error" size="small" class="me-1">mdi-circle</v-icon> Deviation batches</div>
        <div class="d-flex align-center legend-item"><v-icon color="grey" size="small" class="me-1">mdi-circle</v-icon> No reference</div>
      </v-card-text>
    </v-card>

    <div id="container" ref="chartContainer" />
  </div>

  <!-- Detail Modal -->
  <BatchDetailModal
    v-model:show="detailModal.show"
    :batch-id="detailModal.batchId"
    :loading="detailModal.loading"
    :data="detailModal.data"
    :variable-stats="detailModal.variableStats"
    :target-variable="filters.targetVariable"
  />

  <!-- Error Snackbar -->
  <v-snackbar
    v-model="errorSnackbar.show"
    :color="errorSnackbar.color"
    :timeout="errorSnackbar.timeout"
  >
    {{ errorSnackbar.text }}
    <template #actions>
      <v-btn
        variant="text"
        @click="errorSnackbar.show = false"
      >
        Close
      </v-btn>
    </template>
  </v-snackbar>
</template>

<script>
import { defineComponent, ref, onMounted, reactive, computed, watch, nextTick } from 'vue';
import Highcharts from 'highcharts';
import HighchartsStock from 'highcharts/modules/stock';
import HighchartsAccessibility from 'highcharts/modules/accessibility';
import 'highcharts/modules/data';
import 'highcharts/modules/exporting';
import 'highcharts/modules/export-data';
import _ from 'lodash';
import Fetcher from '../Fetcher';
import useNexusStore from '../stores/nexus';
import useKeycloakStore from '../stores/keycloak';
import { useTheme } from 'vuetify';
import BatchDetailModal from '../components/BatchDetailModal.vue';

// Initialize Highcharts modules
HighchartsStock(Highcharts);
HighchartsAccessibility(Highcharts);

const keycloakStore = useKeycloakStore();

const http = new Fetcher('api/', async (options) => {
      await keycloakStore.ensureAccessToken();
      _.set(options, 'headers.Authorization', `Bearer ${keycloakStore.tokens.access_token}`);
    });

export default defineComponent({
  name: 'DashboardView',

  components: {
    BatchDetailModal,
  },

  setup() {
    const chartContainer = ref(null);
    const loading = ref(false);
    const chartConfig = ref(null);
    const nexusStore = useNexusStore();
    const theme = useTheme();

    // Detail modal state
    const detailModal = reactive({
      show: false,
      loading: false,
      batchId: null,
      data: null,
      variableStats: {},
      targetVariable: null,
    });

    // Error snackbar state
    const errorSnackbar = reactive({
      show: false,
      text: '',
      color: 'error',
      timeout: 5000,
    });

    // Computed properties for theme-based colors
    const backgroundColor = computed(() => theme.current.value.dark ? '#1E1E1E' : '#ffffff');
    const textColor = computed(() => theme.current.value.dark ? '#E0E0E0' : '#2c3e50');
    const controlsBackgroundColor = computed(() => theme.current.value.dark ? '#2D2D2D' : '#f8f9fa');
    const shadowColor = computed(() => theme.current.value.dark ? 'rgba(0, 0, 0, 0.3)' : 'rgba(0, 0, 0, 0.1)');
    const borderColor = computed(() => theme.current.value.dark ? '#333333' : '#ebeef5');

    // List of available part families
    const availablePartFamilies = [
      "0.5 High Density Cgf-Cgf",
      "0.5 High Density Blk-Blk",
      "Q Taper Blk-Blk 20psi",
      "Y Taper Blk-Blk 20psi",
      "X Taper Blk-Blk 20psi",
      "1.5 Flat Blk-Blk 20psi",
      "2.0 Flat Blk-Blk 20psi",
      "2.2 Flat Blk-Blk 20psi",
      "2.6 Flat Blk-Blk 20psi",
      "1.0 Flat Blk-Blk 20psi",
      "3.5 Flat Blk-Blk 20psi",
      "C Taper Blk-Blk 20psi",
      "C Taper Blk-Blk 25psi",
      "3.0 Flat Blk-Blk 20psi",
      "2.5 Flat Blk-Blk 20psi",
      "2.6 Flat Cgf-Cgf 20psi",
    ];

    // List of available target variables
    const availableTargetVariables = [
      { value: "Running_Wet_Density", label: "Running Wet Density" },
      { value: "avg_t1_thk", label: "Average T1 Thickness" },
      { value: "avg_t1_core", label: "Average T1 Core" },
      { value: "avg_t1_comp", label: "Average T1 Compression" },
      { value: "KF_KF1_VALUE", label: "KF KF1 Value" },
    ];

    // List of available time ranges
    const availableTimeRanges = [
      { value: "1", label: "Last Month" },
      { value: "3", label: "Last 3 Months" },
      { value: "6", label: "Last 6 Months" },
      { value: "12", label: "Last Year" },
      { value: "18", label: "Last 1.5 Years" },
    ];

    // Parse user groups to extract available sites and lines
    const userGroups = computed(() => {
      return keycloakStore.accessClaims?.user_groups || [];
    });

    // Extract sites from user groups
    const availableSites = computed(() => {
      const sites = new Set();

      userGroups.value.forEach(group => {
        // Match pattern like "/org-CCM/site-Mont/line-L1"
        const match = group.match(/\/org-([^/]+)\/site-([^/]+)/);
        if (match && match[1] === 'CCM') {
          const site = match[2];
          // Format site name as "CCM-{Site}" with first letter capitalized
          sites.add(`CCM-${site.charAt(0).toUpperCase() + site.slice(1)}`);
        }
      });

      // If no sites found, provide default options
      if (sites.size === 0) {
        return ['CCM-Mont', 'CCM-Terrel', 'CCM-Tooele', 'CCM-Sikeston'];
      }

      return Array.from(sites);
    });

    // Extract lines for the selected site
    const availableLines = computed(() => {
      const lines = new Set();
      const selectedSite = filters.site.replace('CCM-', '').toLowerCase();

      userGroups.value.forEach(group => {
        // Match pattern like "/org-CCM/site-mont/line-L1"
        const match = group.match(/\/org-([^/]+)\/site-([^/]+)\/line-([^/]+)/);
        if (match && match[1] === 'CCM' && match[2].toLowerCase() === selectedSite) {
          lines.add(match[3]);
        }
      });

      // If no lines found, provide default options
      if (lines.size === 0) {
        return ['L1', 'L2'];
      }

      return Array.from(lines);
    });

    const filters = reactive({
      site: 'Tooele',
      line: 'L1',
      partFamily: '0.5 High Density Cgf-Cgf',
      targetVariable: 'Running_Wet_Density',
      timeRange: '1',
    });

    // Set initial site and line based on available options
    watch(availableSites, (sites) => {
      if (sites.length > 0 && !filters.site) {
        filters.site = sites[0];
      }
    }, { immediate: true });

    watch(availableLines, (lines) => {
      if (lines.length > 0 && !filters.line) {
        filters.line = lines[0].toLowerCase();
      }
    }, { immediate: true });

    // Watch for site changes and update line accordingly
    watch(() => filters.site, () => {
      // Wait for availableLines to update based on the new site
      nextTick(() => {
        if (availableLines.value.length > 0) {
          // Set line to the first available line for the new site
          filters.line = availableLines.value[0].toLowerCase();
        }
      });
    });

    // Watch for theme changes
    watch(() => theme.current.value.dark, (isDark) => {
      // Get current chart
      const chart = Highcharts.charts.find(c => c && c.renderTo === chartContainer.value);

      if (chart) {
        // Store original dimensions
        const originalWidth = chart.chartWidth;
        const originalHeight = chart.chartHeight;
        const originalContainer = chart.container;

        // Basic color variables
        const textColor = isDark ? '#E0E0E0' : '#2c3e50';
        const backgroundColor = isDark ? '#1E1E1E' : '#ffffff';
        const gridColor = isDark ? '#333333' : '#ebeef5';
        const borderColor = isDark ? '#333333' : '#dcdfe6';
        const tooltipBackgroundColor = isDark ? "rgba(40, 40, 40, 0.7)" : "rgba(255, 255, 255, 0.7)";
        const tooltipBorderColor = isDark ? "rgba(70, 70, 70, 0.5)" : "rgba(200, 200, 200, 0.5)";
        const tooltipTextColor = isDark ? "#E0E0E0" : "#333333";

        // Hide any visible tooltips before theme update
        chart.tooltip.hide();

        // Update ONLY theme colors - no layout properties
        chart.update({
          chart: {
            backgroundColor: backgroundColor,
          },
          title: {
            style: {
              color: textColor,
            },
          },
          xAxis: {
            labels: {
              style: {
                color: textColor,
              },
            },
            lineColor: borderColor,
            tickColor: borderColor,
            gridLineColor: gridColor,
          },
          yAxis: {
            labels: {
              style: {
                color: textColor,
              },
            },
            title: {
              style: {
                color: textColor,
              },
            },
            gridLineColor: gridColor,
          },
          legend: {
            itemStyle: {
              color: textColor,
            },
          },
          tooltip: {
            backgroundColor: tooltipBackgroundColor,
            borderColor: tooltipBorderColor,
            style: {
              color: tooltipTextColor,
            },
          },
        }, false);  // false = don't redraw yet

        // Restore original dimensions
        if (originalContainer) {
          originalContainer.style.width = `${originalWidth}px`;
          originalContainer.style.height = `${originalHeight}px`;
        }

        // Force the chart to be exactly the specified dimensions
        chart.setSize(originalWidth, originalHeight, false);

        // Now redraw with the correct dimensions
        chart.redraw();

        // Update CSS tooltips
        document.documentElement.classList.toggle('tooltip-theme-update', true);
        setTimeout(() => {
          document.documentElement.classList.toggle('tooltip-theme-update', false);
        }, 10);

        // Double-check dimensions after all updates
        setTimeout(() => {
          if (chart && chart.chartWidth !== originalWidth || chart.chartHeight !== originalHeight) {
            chart.setSize(originalWidth, originalHeight);
          }
        }, 100);
      } else if (chartContainer.value) {
        // Handle other UI elements that might be showing
        if (chartContainer.value.querySelector('.initial-message')) {
          const messageEl = chartContainer.value.querySelector('.initial-message');
          messageEl.style.color = isDark ? '#E0E0E0' : '#2c3e50';
        } else if (chartContainer.value.querySelector('.no-data-message')) {
          const messageEl = chartContainer.value.querySelector('.no-data-message');
          messageEl.style.color = isDark ? '#E0E0E0' : '#2c3e50';
        } else if (chartContainer.value.querySelector('.error-message')) {
          const messageEl = chartContainer.value.querySelector('.error-message');
          messageEl.style.color = isDark ? '#ff6b6b' : '#f56c6c';
        }
      }
    });

    // Function to get color based on deviation
    const getColor = (deviation, minDeviation, maxDeviation) => {
      if (deviation === 0) return '#67c23a';  // Green for recommendation
      if (deviation === -1) return 'rgba(144, 147, 153, 0.5)';  // Gray for no reference

      // Scale the deviation to be between 0 and 1 based on min and max values
      const normalizedDeviation = (deviation - minDeviation) / (maxDeviation - minDeviation);

      // Calculate color based on normalized deviation
      // Use a gradient from yellow to red for deviations
      if (normalizedDeviation < 0.5) {
        // Yellow to orange gradient for lower deviations
        const g = Math.floor(195 - normalizedDeviation * 2 * 100);
        return `rgb(230, ${g}, 60)`;
      } else {
        // Orange to red gradient for higher deviations
        const g = Math.floor(95 - (normalizedDeviation - 0.5) * 2 * 95);
        return `rgb(230, ${g}, 60)`;
      }
    };

    // Function to render the chart
    const renderChart = (processedData, targetVariable, isDark) => {
      if (!processedData || !processedData.length) {
        console.warn('No processed data available');
        // Display a message in the chart container
        chartContainer.value.innerHTML = `
          <div class="no-data-message">
            <v-icon icon="mdi-alert-circle" size="large" color="warning"></v-icon>
            <p>No data available for the selected filters.</p>
            <p>Try changing your filter criteria.</p>
          </div>
        `;
        return;
      }

      const textColor = isDark ? '#E0E0E0' : '#2c3e50';
      const backgroundColor = isDark ? '#1E1E1E' : '#ffffff';
      const gridColor = isDark ? '#333333' : '#ebeef5';
      const borderColor = isDark ? '#333333' : '#dcdfe6';
      const tooltipBackgroundColor = isDark ? "rgba(40, 40, 40, 0.7)" : "rgba(255, 255, 255, 0.7)";
      const tooltipBorderColor = isDark ? "rgba(70, 70, 70, 0.5)" : "rgba(200, 200, 200, 0.5)";
      const tooltipTextColor = isDark ? "#E0E0E0" : "#333333";

      // Find min and max deviations for color scaling
      const deviationValues = processedData
        .filter(d => d.deviation_info && d.deviation_info.total_deviation >= 0)
        .map(d => d.deviation_info.total_deviation);
      const minDeviation = Math.min(...deviationValues) || 0;
      const maxDeviation = Math.max(...deviationValues) || 1;

      // Create new chart configuration
      const config = {
        chart: {
          backgroundColor: backgroundColor,
          style: {
            fontFamily: "'Avenir', Helvetica, Arial, sans-serif",
            color: textColor,
          },
          height: 600,
          width: null, // Auto width based on container
          animation: false, // Disable animations to prevent sizing issues
          accessibility: {
            enabled: true,
            description: `Time series chart showing ${targetVariable.replace(/_/g, ' ')} values over time with deviation indicators`,
            announceNewData: {
              announcementFormatter: function (allSeries, newSeries, newPoint) {
                if (newPoint) {
                  return `New point added. Value: ${newPoint.y}`;
                }
                return false;
              },
            },
          },
        },
        title: {
          text: `${targetVariable.replace(/_/g, ' ')} Over Time with Normalized Deviation from Recommendations`,
          style: {
            color: textColor,
            fontWeight: 'bold',
            fontSize: '18px',
          },
        },
        xAxis: {
          type: 'datetime',
          labels: {
            style: {
              color: textColor,
              fontSize: '14px',
            },
          },
          lineColor: borderColor,
          tickColor: borderColor,
          gridLineColor: gridColor,
        },
        yAxis: {
          opposite: false,
          title: {
            text: targetVariable.replace(/_/g, ' '),
            style: {
              color: textColor,
              fontSize: '14px',
            },
          },
          labels: {
            style: {
              color: textColor,
              fontSize: '14px',
            },
          },
          gridLineColor: gridColor,
        },
        legend: {
          enabled: true,
          itemStyle: {
            color: textColor,
            fontSize: '14px',
          },
          backgroundColor: backgroundColor,
          borderColor: borderColor,
        },
        rangeSelector: {
          buttons: [
            {
              type: 'month',
              count: 1,
              text: '1m',
            },
            {
              type: 'month',
              count: 3,
              text: '3m',
            },
            {
              type: 'month',
              count: 6,
              text: '6m',
            },
            {
              type: 'year',
              count: 1,
              text: '1y',
            },
            {
              type: 'all',
              text: 'All',
            },
          ],
          selected: 3,
          inputEnabled: true,
          inputStyle: {
            backgroundColor: tooltipBackgroundColor,
            color: textColor,
            fontSize: '14px',
          },
          labelStyle: {
            color: textColor,
            fontSize: '14px',
          },
          buttonTheme: {
            fill: isDark ? '#333333' : '#f5f7fa',
            stroke: borderColor,
            style: {
              color: textColor,
            },
            states: {
              hover: {
                fill: isDark ? '#444444' : '#e6e8eb',
                style: {
                  color: isDark ? '#ffffff' : '#303133',
                },
              },
              select: {
                fill: '#409eff',
                style: {
                  color: '#ffffff',
                },
              },
            },
          },
        },
        navigator: {
          enabled: true,
          handles: {
            backgroundColor: isDark ? '#333333' : '#f5f7fa',
            borderColor: borderColor,
          },
          outlineColor: borderColor,
          maskFill: 'rgba(64, 158, 255, 0.2)',
          series: {
            color: '#409eff',
            lineColor: '#66b1ff',
          },
          xAxis: {
            gridLineColor: gridColor,
            labels: {
              style: {
                color: textColor,
              },
            },
          },
        },
        scrollbar: {
          barBackgroundColor: isDark ? '#333333' : '#f5f7fa',
          barBorderColor: borderColor,
          buttonArrowColor: textColor,
          buttonBackgroundColor: isDark ? '#333333' : '#f5f7fa',
          buttonBorderColor: borderColor,
          rifleColor: isDark ? '#666666' : '#909399',
          trackBackgroundColor: backgroundColor,
          trackBorderColor: borderColor,
        },
        tooltip: {
          backgroundColor: tooltipBackgroundColor,
          borderColor: tooltipBorderColor,
          borderRadius: 8,
          borderWidth: 1,
          shadow: true,
          style: {
            color: tooltipTextColor,
            fontSize: "12px",
          },
          useHTML: true,
          formatter: function() {
            const point = this.point;
            const deviationInfo = point.deviation_info || {};
            const deviations = deviationInfo.deviations || [];

            let devsHtml = '';
            if (deviations.length > 0) {
              devsHtml = '<div class="tooltip-section"><b>Variable Deviations:</b><br/>' +
                deviations.map(d => {
                  return `<div class="deviation-row">
                    <span class="tooltip-label">${d.variable.replace(/_/g, ' ')}:</span>
                    <span class="deviation-percent">${d.percent.toFixed(1)}%</span>
                  </div>`;
                }).join('') + '</div>';
            }

            return `<div class="tooltip-container">
              <div class="tooltip-header">
                ${Highcharts.dateFormat('%Y-%m-%d', point.x)}
              </div>
              <div class="tooltip-content">
                <div class="tooltip-section">
                  <span class="tooltip-label">${targetVariable}:</span>
                  <span class="tooltip-value">${point.y.toFixed(2)}</span>
                </div>
                ${deviationInfo.total_deviation !== undefined ? `
                <div class="tooltip-section">
                  <span class="tooltip-label">Total Deviation:</span>
                  <span class="tooltip-value" style="color: ${
                    getColor(deviationInfo.total_deviation, minDeviation, maxDeviation)
                  }">${deviationInfo.deviation_percent.toFixed(1)}%</span>
                </div>` : ''}
                ${devsHtml}
                <div class="tooltip-section tooltip-batch">
                  <span class="tooltip-label">Batch:</span>
                  <span class="tooltip-value">${point.batch}</span>
                </div>
              </div>
            </div>`;
          },
        },
        credits: {
          enabled: false,
        },
        series: [{
          type: 'line',
          name: targetVariable,
          data: processedData.map(item => ({
            x: new Date(item.BATCHSTART).getTime(),
            y: item[targetVariable],
            batch: item.BATCH,
            deviation_info: item.deviation_info,
            color: getColor(
              item.deviation_info?.total_deviation || 0,
              minDeviation,
              maxDeviation,
            ),
          })),
          marker: {
            enabled: true,
            radius: 6,
            symbol: 'circle',
            lineWidth: 1,
            lineColor: '#ffffff',
            fillColor: undefined,
            states: {
              hover: {
                lineColor: '#ffffff',
                lineWidth: 2,
                radius: 8,
              },
            },
          },
          opacity: 0.85,
          lineWidth: 2,
          states: {
            hover: {
              lineWidthPlus: 0,
              halo: {
                size: 10,
                opacity: 0.25,
              },
            },
          },
          point: {
            events: {
              click: function() {
                detailModal.show = true;
                detailModal.batchId = this.batch;
                detailModal.loading = true;
                detailModal.data = null;
                detailModal.variableStats = {};

                // Process the data with batch filter
                http.post('transformations/batch-details', {
                  production_data: apiResponses.production,
                  alertman_data: apiResponses.alertman,
                  batch_id: this.batch,
                  target_variable: filters.targetVariable,
                }).then(response => {
                  if (response && !response.error) {
                    detailModal.data = response.processed_data;
                    detailModal.variableStats = response.variable_stats;
                  } else {
                    throw new Error(response.error || 'Failed to process batch details');
                  }
                }).catch(error => {
                  console.error('Error processing detail data:', error);
                  showErrorMessage('Failed to load batch details');
                  detailModal.show = false;
                }).finally(() => {
                  detailModal.loading = false;
                });
              },
            },
          },
        }],
      };

      // Create the chart with the new configuration
      Highcharts.stockChart(chartContainer.value, config);

      // Store the config for future theme updates
      chartConfig.value = config;
    };

    // Store API responses
    const apiResponses = reactive({
      production: null,
      alertman: null,
    });

    // Function to update the chart
    const updateChart = async () => {
      loading.value = true;

      try {
        // Get tenant ID from the store
        const tenantId = nexusStore.getTenantId(nexusStore.currentOrg);

        if (!tenantId) {
          throw new Error('No tenant ID available');
        }

        console.log(nexusStore.currentOrg);
        // Prepare queries for production and alertman data
        const productionQuery = `SELECT * EXCEPT(FT_WTLEN_STARTTIME) FROM ccm.${filters.site.replace("CCM-", "").toLowerCase()}_${filters.line.toLowerCase()}_ct WHERE DateTime BETWEEN now() - INTERVAL ${filters.timeRange} MONTH AND now() AND part_number ILIKE '%${filters.partFamily}%' ORDER BY DateTime;`;

        const alertmanQuery = `SELECT *, CASE WHEN state__parts REGEXP '^${filters.partFamily}.*' THEN '${filters.partFamily}' END AS part_family FROM ccm.alertman_full FINAL WHERE environment ILIKE '%${filters.site.replace("CCM-", "").toLowerCase()}%';`;

        // Make Nexus API calls
        try {
          apiResponses.production = await http.post('tfnexus/v1/datasources/2/query', {
            query: productionQuery,
          }, {
            headers: {
              'X-Tenant-ID': tenantId,
            },
            timeout: 60000, // 1 minute timeout
          });
          // Check if the response contains an error
          if (apiResponses.production && apiResponses.production.error) {
            throw new Error(`Production data error: ${apiResponses.production.error}`);
          }
        } catch (apiError) {
          console.error('Error fetching production data:', apiError);
          throw new Error('Failed to fetch production data');
        }

        try {
          apiResponses.alertman = await http.post('tfnexus/v1/datasources/2/query', {
            query: alertmanQuery,
          }, {
            headers: {
              'X-Tenant-ID': tenantId,
            },
            timeout: 60000, // 1 minute timeout
          });

          // Check if the response contains an error
          if (apiResponses.alertman && apiResponses.alertman.error) {
            throw new Error(`Alertman data error: ${apiResponses.alertman.error}`);
          }
        } catch (apiError) {
          console.error('Error fetching alertman data:', apiError);
          throw new Error('Failed to fetch alertman data');
        }

        // Process the data
        let processDataResponse;
        try {
          processDataResponse = await http.post('transformations/process-data', {
            production_data: apiResponses.production,
            alertman_data: apiResponses.alertman,
            target_variable: filters.targetVariable,
          });

          if (processDataResponse && processDataResponse.error) {
            throw new Error(processDataResponse.error);
          }
        } catch (processError) {
          console.error('Error processing data:', processError);
          throw new Error('Failed to process data');
        }

        renderChart(processDataResponse.processed_data, filters.targetVariable, theme.current.value.dark);
      } catch (error) {
        console.error('Error fetching data:', error);
        showErrorMessage(`Error: ${error.message || 'Failed to load data'}`);

        // Display error message in chart container
        if (chartContainer.value) {
          chartContainer.value.innerHTML = `
            <div class="error-message">
              <v-icon icon="mdi-alert-circle-outline" size="large" color="error"></v-icon>
              <p>Error loading chart data.</p>
              <p>Please check your filters and try again.</p>
            </div>
          `;
        }
      } finally {
        loading.value = false;
      }
    };

    // Function to show error message
    const showErrorMessage = (message) => {
      errorSnackbar.text = message;
      errorSnackbar.show = true;
    };

    // Load chart configuration and initialize
    onMounted(() => {
      // Default chart configuration
      chartConfig.value = {
        chart: {
          backgroundColor: '#ffffff',
          style: {
            fontFamily: "'Avenir', Helvetica, Arial, sans-serif",
            color: '#2c3e50',
          },
        },
        title: {
          text: 'Deviation Analysis Dashboard',
          style: {
            color: '#2c3e50',
            fontWeight: 'bold',
          },
        },
        xAxis: {
          type: 'datetime',
          labels: {
            style: {
              color: '#606266',
            },
          },
          lineColor: '#dcdfe6',
          tickColor: '#dcdfe6',
        },
        yAxis: {
          title: {
            text: 'Value',
            style: {
              color: '#606266',
              fontWeight: 'normal',
            },
          },
          labels: {
            style: {
              color: '#606266',
            },
          },
          gridLineColor: '#ebeef5',
        },
        legend: {
          enabled: true,
          itemStyle: {
            color: '#2c3e50',
            fontWeight: 'normal',
          },
          backgroundColor: '#ffffff',
          borderColor: '#ebeef5',
        },
        rangeSelector: {
          buttons: [
            {
              type: 'month',
              count: 1,
              text: '1m',
            },
            {
              type: 'month',
              count: 3,
              text: '3m',
            },
            {
              type: 'month',
              count: 6,
              text: '6m',
            },
            {
              type: 'year',
              count: 1,
              text: '1y',
            },
            {
              type: 'all',
              text: 'All',
            },
          ],
          selected: 3,
          inputEnabled: true,
          inputStyle: {
            color: '#606266',
          },
          labelStyle: {
            color: '#606266',
          },
          buttonTheme: {
            fill: '#f5f7fa',
            stroke: '#dcdfe6',
            style: {
              color: '#606266',
            },
            states: {
              hover: {
                fill: '#e6e8eb',
                stroke: '#dcdfe6',
                style: {
                  color: '#303133',
                },
              },
              select: {
                fill: '#409eff',
                stroke: '#409eff',
                style: {
                  color: 'white',
                },
              },
            },
          },
        },
        navigator: {
          enabled: true,
          handles: {
            backgroundColor: '#f5f7fa',
            borderColor: '#dcdfe6',
          },
          outlineColor: '#dcdfe6',
          maskFill: 'rgba(64, 158, 255, 0.2)',
          series: {
            color: '#409eff',
            lineColor: '#66b1ff',
          },
          xAxis: {
            gridLineColor: '#ebeef5',
          },
        },
        scrollbar: {
          barBackgroundColor: '#f5f7fa',
          barBorderColor: '#dcdfe6',
          buttonArrowColor: '#606266',
          buttonBackgroundColor: '#f5f7fa',
          buttonBorderColor: '#dcdfe6',
          rifleColor: '#909399',
          trackBackgroundColor: '#ffffff',
          trackBorderColor: '#ebeef5',
        },
        credits: {
          enabled: false,
        },
      };

      // Use nextTick to ensure the DOM is updated
      nextTick(() => {
        // Display initial message in chart container
        if (chartContainer.value) {
          chartContainer.value.innerHTML = `
            <div class="initial-message">
              <v-icon icon="mdi-chart-line" size="large" color="primary"></v-icon>
              <p>Select your filters and click "Update Chart" to view data.</p>
            </div>
          `;
        }
      });
    });

    return {
      chartContainer,
      filters,
      loading,
      updateChart,
      availableSites,
      availableLines,
      availablePartFamilies,
      availableTargetVariables,
      availableTimeRanges,
      errorSnackbar,
      theme,
      backgroundColor,
      textColor,
      controlsBackgroundColor,
      shadowColor,
      borderColor,
      detailModal,
    };
  },
});
</script>

<style scoped>
.dashboard-container {
  background-color: v-bind('backgroundColor');
  color: v-bind('textColor');
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  margin: 20px;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px v-bind('shadowColor');
  font-size: 16px;
}

#container {
  min-width: 310px;
  width: 100% !important;
  height: 600px !important; /* Force fixed height */
  min-height: 600px !important;
  margin: 0 auto;
  font-size: 14px;
  position: relative;
  overflow: visible;
}

.controls {
  margin-bottom: 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: center;
  background-color: v-bind('controlsBackgroundColor');
  padding: 20px;
  border-radius: 8px;
}

.control-group {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 200px;
  max-width: 300px;
}

.control-select {
  width: 100%;
  font-size: 14px;
}

.control-select :deep(.v-field__input) {
  font-size: 14px !important;
}

.control-select :deep(.v-label) {
  font-size: 14px !important;
}

.control-select :deep(.v-field__input) {
  font-size: 14px !important;
}

.control-select :deep(.v-label) {
  font-size: 14px !important;
}

.update-btn {
  height: 40px !important;
  font-size: 14px !important;
  padding: 0 24px !important;
  align-self: flex-end;
}

.legend-info {
  background-color: v-bind('controlsBackgroundColor') !important;
  border-left: 4px solid #409eff !important;
  font-size: 14px;
  padding: 8px 16px;
}

.legend-info .v-card-text {
  padding: 0 !important;
}

.legend-info .v-card-text div {
  margin-bottom: 0;
  display: flex;
  align-items: center;
  font-size: 14px;
}

.legend-info .v-card-text div .v-icon {
  margin-right: 8px;
  font-size: 16px !important;
}

.no-data-message, .initial-message {
  color: v-bind('textColor');
  font-size: 16px;
  text-align: center;
  padding: 40px;
}

.error-message {
  color: v-bind('theme.current.value.dark ? "#ff6b6b" : "#f56c6c"');
  font-size: 16px;
  text-align: center;
  padding: 40px;
}

.error-message .v-icon {
  margin-bottom: 16px;
  opacity: 0.8;
}

.detail-modal {
  .v-card {
    max-height: 90vh;
    overflow-y: auto;
  }
}

.variable-summary {
  height: 500px;
  overflow-y: auto;
}

.legend-item {
  margin-right: 32px;
}

.legend-item:last-child {
  margin-right: 0;
}
</style>

<style>
/* Global styles for Highcharts tooltips */
.tooltip-theme-update .tooltip-container,
.tooltip-container {
  background-color: v-bind('theme.current.value.dark ? "rgba(40, 40, 40, 0.7)" : "rgba(255, 255, 255, 0.7)"') !important;
  border: 1px solid v-bind('theme.current.value.dark ? "rgba(70, 70, 70, 0.5)" : "rgba(200, 200, 200, 0.5)"') !important;
  border-radius: 8px !important;
  padding: 12px !important;
  font-family: 'Avenir', Helvetica, Arial, sans-serif !important;
  box-shadow: 1px 1px 3px rgba(0, 0, 0, 0.3) !important;
  min-width: 280px !important;
  font-size: 12px !important;
}

.tooltip-theme-update .tooltip-header,
.tooltip-header {
  font-size: 14px !important;
  color: v-bind('theme.current.value.dark ? "#E0E0E0" : "#333333"') !important;
  margin-bottom: 10px !important;
  border-bottom: 1px solid v-bind('theme.current.value.dark ? "rgba(70, 70, 70, 0.5)" : "rgba(200, 200, 200, 0.5)"') !important;
  padding-bottom: 6px !important;
  font-weight: bold !important;
}

.tooltip-theme-update .tooltip-content,
.tooltip-content {
  font-size: 12px !important;
  color: v-bind('theme.current.value.dark ? "#E0E0E0" : "#333333"') !important;
}

.tooltip-theme-update .tooltip-label,
.tooltip-label {
  color: v-bind('theme.current.value.dark ? "#E0E0E0" : "#333333"') !important;
}

.tooltip-theme-update .tooltip-value,
.tooltip-value {
  color: v-bind('theme.current.value.dark ? "#E0E0E0" : "#333333"') !important;
}

.deviation-bar {
  display: inline-block;
  height: 6px;
  background: linear-gradient(to right, #f56c6c, #e64242);
  margin-left: 10px;
  border-radius: 3px;
  vertical-align: middle;
  transition: width 0.2s ease;
}

.deviation-row {
  display: flex;
  align-items: center;
  margin: 4px 0;
  justify-content: space-between;
}

.deviation-info {
  flex: 1;
  display: flex;
  align-items: center;
}

.deviation-percent {
  color: #f56c6c;
  font-weight: bold;
  margin-left: 10px;
}

.tooltip-theme-update .tooltip-batch,
.tooltip-batch {
  margin-top: 10px !important;
  border-top: 1px solid v-bind('theme.current.value.dark ? "rgba(70, 70, 70, 0.5)" : "rgba(200, 200, 200, 0.5)"') !important;
  padding-top: 8px !important;
}

.tooltip-theme-update .tooltip-section,
.tooltip-section {
  margin: 8px 0 !important;
  line-height: 1.4 !important;
}

.tooltip-theme-update .tooltip-label,
.tooltip-label {
  color: v-bind('theme.current.value.dark ? "#E0E0E0" : "#333333"') !important;
}
</style>