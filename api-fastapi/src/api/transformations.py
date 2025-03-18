from fastapi import APIRouter, Request, HTTPException
import pandas as pd
from typing import List, Dict, Any, Optional
import statistics
import numpy as np
import json

router = APIRouter()

def calculate_std(values: List[float]) -> float:
    """
    Calculate standard deviation of a list of values.
    
    Args:
        values: List of numeric values
        
    Returns:
        Standard deviation
    """
    if not values:
        return 0
    
    try:
        return statistics.stdev(values)
    except statistics.StatisticsError:
        # Handle case with only one value
        return 0

def calculate_correlations(df: pd.DataFrame, target_variable: str) -> Dict[str, float]:
    """
    Calculate correlations between target variable and all other numeric variables.
    
    Args:
        df: DataFrame containing variables
        target_variable: Name of the target variable
        
    Returns:
        Dictionary of variable names and their correlation with target
    """
    if df.empty or target_variable not in df.columns:
        return {}
        
    correlations = {}
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    
    for col in numeric_cols:
        if col != target_variable:
            try:
                # Calculate Pearson correlation
                correlation = df[target_variable].corr(df[col])
                if not pd.isna(correlation):
                    correlations[col] = correlation
            except:
                continue
                
    return correlations

def calculate_variable_stats(df, batch_id=None, target_variable=None):
    """Calculate advanced statistics for variables, focusing on recommendation tags."""
    if df.empty:
        return {}

    # Convert DateTime column to datetime if it's not already
    if 'DateTime' in df.columns:
        df['DateTime'] = pd.to_datetime(df['DateTime'])

    # Filter for uptime data only
    df = df[df['run_state'] == 'Uptime'].copy()
    
    if batch_id:
        df = df[df['BATCH'] == batch_id]

    # Get numeric columns excluding specific ones
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    exclude_cols = ['DateTime', 'BATCH']
    numeric_cols = [col for col in numeric_cols if col not in exclude_cols]

    # Calculate correlations if target variable is provided
    correlations = {}
    if target_variable and target_variable in df.columns:
        correlations = calculate_correlations(df, target_variable)

    # For columns that should be numeric but aren't, try to convert them
    for col in df.columns:
        if col not in numeric_cols and col not in exclude_cols:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                if not df[col].isna().all():  # If conversion produced some valid numbers
                    numeric_cols = numeric_cols.append(pd.Index([col]))
            except:
                continue

    stats = {}
    for col in numeric_cols:
        # Skip if column is all NaN
        if df[col].isna().all():
            continue

        values = df[col].dropna()
        if len(values) < 2:  # Need at least 2 points for statistics
            continue

        try:
            # Calculate basic statistics
            mean = float(values.mean())
            std = float(values.std())
            
            # Handle infinite or NaN values
            if pd.isna(mean) or np.isinf(mean):
                mean = 0
            if pd.isna(std) or np.isinf(std):
                std = 0
            
            # Calculate trend (normalized slope)
            time_values = (df['DateTime'] - df['DateTime'].min()).dt.total_seconds()
            trend = 0
            if len(time_values) > 1:
                try:
                    slope = np.polyfit(time_values, values.astype(float), 1)[0]
                    # Normalize slope to represent relative change per hour
                    if mean != 0:
                        trend = (slope * 3600) / mean
                except:
                    trend = 0

            # Calculate volatility (coefficient of variation)
            volatility = (std / mean * 100) if mean != 0 else 0

            # Handle infinite or NaN values in calculated stats
            if pd.isna(trend) or np.isinf(trend):
                trend = 0
            if pd.isna(volatility) or np.isinf(volatility):
                volatility = 0

            # Get min/max values safely
            try:
                min_val = float(values.min())
                max_val = float(values.max())
                if pd.isna(min_val) or np.isinf(min_val):
                    min_val = 0
                if pd.isna(max_val) or np.isinf(max_val):
                    max_val = 0
                range_val = max_val - min_val
            except:
                min_val = max_val = range_val = 0

            # Get correlation safely
            correlation = correlations.get(col, 0)
            if pd.isna(correlation) or np.isinf(correlation):
                correlation = 0

            # Store statistics with safe values
            stats[col] = {
                'mean': mean,
                'std': std,
                'trend': float(trend),
                'volatility': float(volatility),
                'min': min_val,
                'max': max_val,
                'range': range_val,
                'correlation': float(correlation)
            }
        except Exception as e:
            print(f"Error calculating stats for column {col}: {str(e)}")
            continue

    return stats

def calculate_point_correlation(data, variable1, variable2):
    """Calculate simple point-by-point correlations between two variables.
    
    Args:
        data: DataFrame containing the variables
        variable1: Name of first variable
        variable2: Name of second variable
        
    Returns:
        List of [timestamp, correlation, run_state] triplets
    """
    if not all(col in data.columns for col in [variable1, variable2, 'DateTime', 'run_state']):
        return []
        
    try:
        # Convert to numeric, handling NaN and inf values
        data.loc[:, variable1] = pd.to_numeric(data.loc[:, variable1], errors='coerce')
        data.loc[:, variable2] = pd.to_numeric(data.loc[:, variable2], errors='coerce')
        
        # Replace infinite values with 0
        data.loc[:, variable1] = data.loc[:, variable1].replace([np.inf, -np.inf], 0)
        data.loc[:, variable2] = data.loc[:, variable2].replace([np.inf, -np.inf], 0)
        
        # Replace NaN with 0
        data.loc[:, variable1] = data.loc[:, variable1].fillna(0)
        data.loc[:, variable2] = data.loc[:, variable2].fillna(0)
        
        # Calculate means and standard deviations
        mean1 = data[variable1].mean()
        mean2 = data[variable2].mean()
        std1 = data[variable1].std() or 1  # Use 1 if std is 0
        std2 = data[variable2].std() or 1  # Use 1 if std is 0
            
        # Calculate point-by-point correlations
        result = []
        for _, row in data.iterrows():
            ts = int(pd.Timestamp(row['DateTime']).timestamp() * 1000)  # Convert to milliseconds
            
            # Calculate z-scores
            z1 = (row[variable1] - mean1) / std1
            z2 = (row[variable2] - mean2) / std2
            
            # Calculate correlation as product of z-scores, normalized to [-1, 1]
            corr = (z1 * z2) / max(abs(z1 * z2), 1) if abs(z1 * z2) > 0 else 0
            
            # Ensure correlation is finite and in [-1, 1] range
            corr = max(min(float(corr), 1), -1)
            result.append([ts, corr, row['run_state']])

        return sorted(result, key=lambda x: x[0])  # Sort by timestamp
        
    except Exception as e:
        print(f"Error calculating correlation: {str(e)}")
        return []

@router.post("/transformations/process-data")
async def process_data(request: Request):
    """
    Process production and alertman data to calculate deviations.
    
    Request body should contain:
    - production_data: List of production data records
    - alertman_data: List of alertman data records
    - target_variable: Name of the target variable to analyze
    - batch_id: Optional batch ID for detailed statistics
    
    Returns:
        Processed data with deviation information
    """
    try:
        data = await request.json()
        production_data = data.get("production_data", [])
        alertman_data = data.get("alertman_data", [])
        target_variable = data.get("target_variable")
        
        if not production_data:
            return {"error": "No production data available"}
            
        if not target_variable:
            return {"error": "Target variable not specified"}
        
        # Convert to pandas DataFrames
        df_production = pd.DataFrame.from_dict(production_data["items"])
        df_alertman = pd.DataFrame(alertman_data["items"])

        # remove downtime data
        df_production = df_production[df_production['run_state'] == 'Uptime']
        
        # Check if target variable exists in the data
        if target_variable not in df_production.columns:
            return {"error": f"Target variable '{target_variable}' not found in production data"}
        
        # Remove rows with missing or non-numeric target values
        df_production = df_production[pd.to_numeric(df_production[target_variable], errors='coerce').notna()]
        
        if df_production.empty:
            return {"error": f"No valid values found for target variable: {target_variable}"}
        
        # Remove outliers using quantiles (3% and 97%)
        low_quantile = df_production[target_variable].quantile(0.03)
        high_quantile = df_production[target_variable].quantile(0.97)
        
        df_filtered = df_production[(df_production[target_variable] >= low_quantile) & 
                                    (df_production[target_variable] <= high_quantile)]
        
        # Get recommendation tags and batches from alertman data
        if not df_alertman.empty:
            # Check if required columns exist
            if 'decision' in df_alertman.columns and 'tag' in df_alertman.columns:
                reco_tags = df_alertman[df_alertman['decision'].notna() & (df_alertman['decision'] != '')]['tag'].unique().tolist()
            else:
                reco_tags = []
                
            if 'state__extra__batch_id' in df_alertman.columns:
                product_batches = df_alertman['state__extra__batch_id'].dropna().unique().tolist()
            else:
                product_batches = []
        else:
            reco_tags = []
            product_batches = []
        
        print(reco_tags)
        # Get all batches from filtered data
        if 'BATCH' in df_filtered.columns:
            all_batches = df_filtered['BATCH'].dropna().unique().tolist()
        else:
            return {"error": "BATCH column not found in filtered data"}
        
        # Process batch data
        current_product_batch = None
        previous_product_batch = None
        processed_data = []
        
        for batch in all_batches:
            # Get rows for this batch
            batch_df = df_filtered[df_filtered['BATCH'] == batch]
            
            if batch_df.empty:
                continue
            
            # Calculate mean value for target variable
            mean_value = batch_df[target_variable].mean()
            
            # Find the earliest timestamp for this batch
            if 'minute_level' in batch_df.columns:
                first_timestamp = batch_df['minute_level'].min()
            elif 'BATCHSTART' in batch_df.columns:
                first_timestamp = batch_df['BATCHSTART'].min()
            else:
                first_timestamp = None
            
            result = {
                "BATCH": batch,
                "BATCHSTART": first_timestamp,
                target_variable: mean_value
            }
            
            if batch not in product_batches:
                if not current_product_batch:
                    # No reference batch yet
                    result["deviation_info"] = {
                        "total_deviation": -1,
                        "deviation_percent": 0,
                        "deviations": []
                    }
                else:
                    # Get reference batch data
                    ref_batch_df = df_filtered[df_filtered['BATCH'] == current_product_batch]
                    
                    if not ref_batch_df.empty:
                        current_batch_means = {}
                        ref_batch_means = {}
                        deviations = {}
                        deviation_percents = {}
                        
                        # Calculate means for all tags
                        for tag in reco_tags:
                            if tag in batch_df.columns:
                                # Calculate mean for current batch
                                current_batch_means[tag] = batch_df[tag].mean()
                                
                                # Calculate mean for reference batch
                                if tag in ref_batch_df.columns:
                                    ref_batch_means[tag] = ref_batch_df[tag].mean()
                                    
                                    # Calculate standard deviation for normalization
                                    ref_values = ref_batch_df[tag].dropna().tolist()
                                    ref_std = max(calculate_std(ref_values) or 1, 1)
                                    ref_mean = ref_batch_means[tag]
                                    
                                    # Calculate normalized deviation
                                    deviations[tag] = abs(current_batch_means[tag] - ref_batch_means[tag]) / ref_std
                                    
                                    # Calculate percentage deviation
                                    if ref_mean != 0:
                                        deviation_percents[tag] = (abs(current_batch_means[tag] - ref_mean) / abs(ref_mean)) * 100
                                    else:
                                        deviation_percents[tag] = 0
                        
                        # Calculate total deviation percentage as the sum
                        total_deviation_percent = sum(deviation_percents.values()) if deviation_percents else 0
                        
                        # Create list of deviations
                        all_deviations = [
                            {
                                "variable": variable,
                                "deviation": deviations[variable],
                                "percent": percent,
                                "contribution": (percent / total_deviation_percent) * 100 if total_deviation_percent > 0 else 0
                            }
                            for variable, percent in deviation_percents.items()
                        ]
                        
                        # Sort by percentage deviation (descending) and take top 5
                        all_deviations.sort(key=lambda x: x["percent"], reverse=True)
                        top_deviations = all_deviations[:5]
                        
                        result["deviation_info"] = {
                            "total_deviation": total_deviation_percent,
                            "deviation_percent": total_deviation_percent,
                            "deviations": top_deviations
                        }
                    else:
                        result["deviation_info"] = {
                            "total_deviation": 0,
                            "deviation_percent": 0,
                            "deviations": []
                        }
            else:
                # This is a recommendation batch
                previous_product_batch = current_product_batch
                current_product_batch = batch
                result["deviation_info"] = {
                    "total_deviation": 0,
                    "deviation_percent": 0,
                    "deviations": []
                }
            
            processed_data.append(result)
        
        return {
            "processed_data": processed_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e)}")

@router.post("/transformations/batch-details")
async def get_batch_details(request: Request):
    """
    Get detailed statistics for a specific batch.
    
    Request body should contain:
    - production_data: List of production data records
    - alertman_data: List of alertman data records
    - batch_id: Batch ID to analyze
    - target_variable: Name of the target variable to analyze
    
    Returns:
        Detailed statistics for the batch
    """
    try:
        # Parse request body
        try:
            data = await request.json()
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400, 
                detail={
                    "message": "Invalid JSON in request body",
                    "error": str(e)
                }
            )

        # Extract and validate required fields
        production_data = data.get("production_data", {})
        alertman_data = data.get("alertman_data", {})
        batch_id = data.get("batch_id")
        target_variable = data.get("target_variable")

        # Validate request data
        if not isinstance(production_data, dict) or not production_data.get("items"):
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Invalid production data format",
                    "expected": {
                        "production_data": {
                            "items": "[array of records]"
                        }
                    }
                }
            )
            
        if not batch_id:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Batch ID not specified",
                    "field": "batch_id"
                }
            )
        
        if not target_variable:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Target variable not specified",
                    "field": "target_variable"
                }
            )
        
        # Convert to pandas DataFrame with error handling
        try:
            df_production = pd.DataFrame.from_dict(production_data.get("items", []))
            df_alertman = pd.DataFrame.from_dict(alertman_data.get("items", []))
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Error converting data to DataFrame",
                    "error": str(e)
                }
            )
        
        if df_production.empty:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "No data found in production data",
                    "error": "Empty DataFrame"
                }
            )
            
        # Get recommendation tags from alertman data
        reco_tags = []
        if not df_alertman.empty and 'decision' in df_alertman.columns and 'tag' in df_alertman.columns:
            reco_tags = df_alertman[df_alertman['decision'].notna() & (df_alertman['decision'] != '')]['tag'].unique().tolist()
        
        if not reco_tags:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "No recommendation tags found in alertman data",
                    "required_columns": ["decision", "tag"]
                }
            )
            
        # Convert DateTime column with error handling
        try:
            if 'DateTime' in df_production.columns:
                df_production['DateTime'] = pd.to_datetime(df_production['DateTime'])
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Error converting DateTime column",
                    "error": str(e)
                }
            )
        
        # Filter for the specific batch
        batch_data = df_production[df_production['BATCH'] == batch_id]
        
        if batch_data.empty:
            raise HTTPException(
                status_code=404,
                detail={
                    "message": f"No data found for batch {batch_id}",
                    "batch_id": batch_id
                }
            )
        
        # Convert numeric columns (only for recommendation tags)
        numeric_conversion_errors = []
        for tag in reco_tags:
            if tag in df_production.columns:
                try:
                    df_production[tag] = pd.to_numeric(df_production[tag], errors='coerce')
                except Exception as e:
                    numeric_conversion_errors.append({"tag": tag, "error": str(e)})
        
        if numeric_conversion_errors:
            print("Warning - Numeric conversion errors:", numeric_conversion_errors)
        
        # Calculate variable statistics (only for recommendation tags)
        try:
            # Filter DataFrame to only include recommendation tags and necessary columns
            cols_to_keep = ['DateTime', 'BATCH', 'run_state'] + reco_tags + [target_variable]
            cols_available = [col for col in cols_to_keep if col in df_production.columns]
            df_filtered = df_production.loc[df_production['run_state'] == 'Uptime', cols_available]
            variable_stats = calculate_variable_stats(df_filtered, batch_id, target_variable)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Error calculating statistics",
                    "error": str(e)
                }
            )
        
        # Calculate rolling correlations for each variable with target
        correlations_data = {}
        correlation_errors = []
        for variable in reco_tags:
            if variable != target_variable:
                try:
                    corr_data = calculate_point_correlation(
                        batch_data,
                        variable,
                        target_variable
                    )
                    if corr_data:  # Only include if we have correlation data
                        correlations_data[variable] = corr_data
                except Exception as e:
                    correlation_errors.append({"variable": variable, "error": str(e)})
        
        if correlation_errors:
            print("Warning - Correlation calculation errors:", correlation_errors)
        
        # Get batch data for visualization
        try:
            # Include only recommendation tags in the processed data
            viz_cols = ['DateTime', 'BATCH', 'run_state'] + reco_tags + [target_variable]
            available_cols = [col for col in viz_cols if col in batch_data.columns]
            batch_data_filtered = batch_data[available_cols]
            
            # Convert to records with error handling for JSON serialization
            try:
                processed_data = batch_data_filtered.to_dict('records')
                # Ensure all values are JSON serializable
                for record in processed_data:
                    for key, value in record.items():
                        if pd.isna(value) or (isinstance(value, float) and np.isinf(value)):
                            record[key] = None
                        elif isinstance(value, pd.Timestamp):
                            record[key] = value.isoformat()
                        elif isinstance(value, (np.int64, np.float64)):
                            # Convert numpy types to Python types and handle inf values
                            try:
                                float_val = float(value)
                                if np.isinf(float_val) or np.isnan(float_val):
                                    record[key] = None
                                else:
                                    record[key] = float_val
                            except:
                                record[key] = None
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "message": "Error converting data to JSON",
                        "error": str(e)
                    }
                )
                
            return {
                "processed_data": processed_data,
                "variable_stats": variable_stats,
                "correlations_data": correlations_data,
                "warnings": {
                    "numeric_conversion_errors": numeric_conversion_errors if numeric_conversion_errors else None,
                    "correlation_errors": correlation_errors if correlation_errors else None
                }
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Error processing batch data",
                    "error": str(e)
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in batch details: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Unexpected error in batch details",
                "error": str(e)
            }
        ) 