// Helper function to calculate standard deviation
function calculateStd(values) {
    const mean = _.mean(values);
    const squareDiffs = values.map(value => {
        const diff = value - mean;
        return diff * diff;
    });
    const variance = _.mean(squareDiffs);
    return Math.sqrt(variance);
}

// Process production and alertman data to calculate deviations
function processData(productionData, alertmanData, targetVariable) {
    if (!productionData || !productionData.length) {
        console.warn('No production data available');
        return [];
    }

    // Remove outliers using quantiles (3% and 97%)
    const values = productionData
        .map(row => row[targetVariable])
        .filter(v => v !== null && !isNaN(v))
        .sort((a, b) => a - b);
    
    const lowQuantile = values[Math.floor(values.length * 0.03)];
    const highQuantile = values[Math.floor(values.length * 0.97)];
    
    const filteredData = productionData.filter(row => 
        row[targetVariable] >= lowQuantile && 
        row[targetVariable] <= highQuantile
    );

    // Get recommendation tags and batches from alertman data
    const recoTags = _.uniq(
        alertmanData
            .filter(row => row.decision !== '')
            .map(row => row.tag)
    );

    const productBatches = _.uniq(
        alertmanData.map(row => row.state__extra__batch_id)
    );

    const allBatches = _.uniq(
        filteredData.map(row => row.BATCH)
    );

    // Process batch data
    let currentProductBatch = null;
    const processedData = allBatches.map(batch => {
        const batchRows = filteredData.filter(row => row.BATCH === batch);
        const meanValue = _.meanBy(batchRows, targetVariable);
        const firstTimestamp = _.minBy(batchRows, 'minute_level').minute_level;

        const result = {
            BATCH: batch,
            BATCHSTART: firstTimestamp,
            [targetVariable]: meanValue
        };

        if (!productBatches.includes(batch)) {
            if (!currentProductBatch) {
                // No reference batch yet
                result.deviation_info = {
                    total_deviation: -1,
                    deviation_percent: 0,
                    deviations: []
                };
            } else {
                const currentBatchMeans = {};
                const refBatchMeans = {};
                const deviations = {};
                const deviationPercents = {};
                let totalDeviationPercent = 0;

                // Calculate means for all tags
                recoTags.forEach(tag => {
                    currentBatchMeans[tag] = _.meanBy(batchRows, tag);
                    const refBatchRows = filteredData.filter(row => row.BATCH === currentProductBatch);
                    refBatchMeans[tag] = _.meanBy(refBatchRows, tag);
                    
                    // Calculate standard deviation for normalization
                    const refValues = refBatchRows.map(row => row[tag]);
                    const refStd = Math.max(calculateStd(refValues) || 1, 1);
                    const refMean = refBatchMeans[tag];
                    
                    // Calculate normalized deviation
                    deviations[tag] = Math.abs(currentBatchMeans[tag] - refBatchMeans[tag]) / refStd;
                    
                    // Calculate percentage deviation
                    deviationPercents[tag] = refMean !== 0 ? 
                        (Math.abs(currentBatchMeans[tag] - refMean) / Math.abs(refMean)) * 100 : 0;
                });

                // Calculate total deviation percentage as the sum
                totalDeviationPercent = _.sum(Object.values(deviationPercents)) || 0;

                // Include top 5 deviating variables sorted by percentage
                const allDeviations = Object.entries(deviationPercents)
                    .map(([variable, percent]) => ({
                        variable,
                        deviation: deviations[variable],
                        percent: percent,
                        contribution: (percent / totalDeviationPercent) * 100
                    }))
                    .sort((a, b) => b.percent - a.percent)  // Sort by percentage deviation
                    .slice(0, 5);  // Take top 5

                result.deviation_info = {
                    total_deviation: totalDeviationPercent,  // Use total percentage deviation for heatmap
                    deviation_percent: totalDeviationPercent,
                    deviations: allDeviations
                };
            }
        } else {
            // This is a recommendation batch
            previousProductBatch = currentProductBatch;
            currentProductBatch = batch;
            console.log("Changing product batch from", previousProductBatch, "to", currentProductBatch);
            result.deviation_info = {
                total_deviation: 0,
                deviation_percent: 0,
                deviations: []
            };
        }

        return result;
    });

    return processedData;
} 