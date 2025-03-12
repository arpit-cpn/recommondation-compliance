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

def calculate_variable_stats(df, batch_id=None):
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
            
            # Calculate trend (normalized slope)
            time_values = (df['DateTime'] - df['DateTime'].min()).dt.total_seconds()
            if len(time_values) > 1:
                slope = np.polyfit(time_values, values.astype(float), 1)[0]
                # Normalize slope to represent relative change per hour
                trend = (slope * 3600) / mean if mean != 0 else 0  # Convert to hourly rate
            else:
                trend = 0

            # Calculate volatility (coefficient of variation)
            volatility = (std / mean * 100) if mean != 0 else 0

            # Store statistics
            stats[col] = {
                'mean': mean,
                'std': std,
                'trend': float(trend),  # Relative change per hour
                'volatility': float(volatility),  # Coefficient of variation in percentage
                'min': float(values.min()),
                'max': float(values.max()),
                'range': float(values.max() - values.min()),
            }
        except Exception as e:
            print(f"Error calculating stats for column {col}: {str(e)}")
            continue

    return stats

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
        except json.JSONDecodeError:
            return {"error": "Invalid JSON in request body"}

        # Extract and validate required fields
        production_data = data.get("production_data", {})
        alertman_data = data.get("alertman_data", {})
        batch_id = data.get("batch_id")
        target_variable = data.get("target_variable")
        if not production_data or not isinstance(production_data, dict):
            return {"error": "Invalid or missing production data"}
            
        if not batch_id:
            return {"error": "Batch ID not specified"}
        
        if not target_variable:
            return {"error": "Target variable not specified"}
        
        # Convert to pandas DataFrame with error handling
        try:
            df_production = pd.DataFrame.from_dict(production_data.get("items", []))
            df_alertman = pd.DataFrame.from_dict(alertman_data.get("items", []))
        except Exception as e:
            return {"error": f"Error converting data to DataFrame: {str(e)}"}
        
        if df_production.empty:
            return {"error": "No data found in production data"}
            
        # Get recommendation tags from alertman data
        reco_tags = []
        if not df_alertman.empty and 'decision' in df_alertman.columns and 'tag' in df_alertman.columns:
            reco_tags = df_alertman[df_alertman['decision'].notna() & (df_alertman['decision'] != '')]['tag'].unique().tolist()
        
        if not reco_tags:
            return {"error": "No recommendation tags found in alertman data"}
            
        # Convert DateTime column with error handling
        try:
            if 'DateTime' in df_production.columns:
                df_production['DateTime'] = pd.to_datetime(df_production['DateTime'])
        except Exception as e:
            return {"error": f"Error converting DateTime column: {str(e)}"}
        
        # Filter for the specific batch
        batch_data = df_production[df_production['BATCH'] == batch_id]

        print(batch_id)
        print(batch_data.run_state.value_counts())
        
        if batch_data.empty:
            return {"error": f"No data found for batch {batch_id}"}
        
        # Convert numeric columns (only for recommendation tags)
        for tag in reco_tags:
            if tag in df_production.columns:
                try:
                    df_production[tag] = pd.to_numeric(df_production[tag], errors='coerce')
                except Exception as e:
                    print(f"Error converting column {tag}: {str(e)}")
                    continue
        
        # Calculate variable statistics (only for recommendation tags)
        try:
            # Filter DataFrame to only include recommendation tags and necessary columns
            cols_to_keep = ['DateTime', 'BATCH', 'run_state'] + reco_tags + [target_variable]
            cols_available = [col for col in cols_to_keep if col in df_production.columns]
            df_filtered = df_production.loc[df_production['run_state'] == 'Uptime', cols_available]
            variable_stats = calculate_variable_stats(df_filtered, batch_id)
        except Exception as e:
            return {"error": f"Error calculating statistics: {str(e)}"}
        
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
                        if pd.isna(value):
                            record[key] = None
                        elif isinstance(value, pd.Timestamp):
                            record[key] = value.isoformat()
                        elif isinstance(value, (np.int64, np.float64)):
                            record[key] = float(value)
            except Exception as e:
                return {"error": f"Error converting data to JSON: {str(e)}"}
                
            return {
                "processed_data": processed_data,
                "variable_stats": variable_stats
            }
        except Exception as e:
            return {"error": f"Error processing batch data: {str(e)}"}
            
    except Exception as e:
        print(f"Unexpected error in batch details: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"} 