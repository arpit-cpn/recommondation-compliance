from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import clickhouse_connect
import numpy as np
import pandas as pd

app = Flask(__name__)
# Configure CORS properly with all necessary settings
CORS(app, 
     resources={r"/api/*": {
         "origins": ["http://localhost:8000"],
         "methods": ["POST", "OPTIONS"],
         "allow_headers": ["Content-Type"],
         "supports_credentials": True
     }}
)

# Load datasources configuration
with open('datasources.json', 'r') as f:
    datasources = json.load(f)

def get_clickhouse_client():
    """Get a connection to ClickHouse using clickhouse-connect"""
    host = 'localhost'
    port = 18123
    
    print(f"Connecting to ClickHouse at {host}:{port}")
    return clickhouse_connect.get_client(
        host=host,
        port=port,
        database='ccm'
    )

def format_query(query_template, **kwargs):
    """Format query template with proper string replacements"""
    formatted_query = query_template
    if 'site' in kwargs:
        site_name = kwargs['site'].replace("CCM-", "").lower()
        formatted_query = formatted_query.replace("${site.replace(\"CCM-\", \"\").toLowerCase()}", site_name)
    if 'line' in kwargs:
        formatted_query = formatted_query.replace("${line.toLowerCase()}", kwargs['line'].lower())
    if 'partFamily' in kwargs:
        formatted_query = formatted_query.replace("${partFamily}", kwargs['partFamily'])
    if 'timeRange' in kwargs:
        formatted_query = formatted_query.replace("${timeRange}", str(kwargs['timeRange']))
    return formatted_query

def clean_dataframe(df):
    """Clean DataFrame by replacing NaN values with None and converting datetime objects"""
    if df.empty:
        return df
        
    # Replace NaN, inf, -inf with None
    df = df.replace([np.nan, np.inf, -np.inf], None)
    
    # Convert datetime objects to ISO format strings
    for col in df.select_dtypes(include=['datetime64']).columns:
        df[col] = df[col].astype(str)
    
    return df

@app.route('/api/data', methods=['POST', 'OPTIONS'])
def get_data():
    try:
        if request.method == 'OPTIONS':
            return '', 204

        params = request.json
        site = params.get('site')
        line = params.get('line')
        part_family = params.get('partFamily')
        time_range = params.get('timeRange')

        print(f"Received request with params: {params}")
        
        client = get_clickhouse_client()
        print("Successfully connected to ClickHouse")
        
        # Execute production data query
        prod_query = format_query(
            datasources['production_data']['query'],
            site=site,
            line=line,
            partFamily=part_family,
            timeRange=time_range
        )
        
        print(f"Production query: {prod_query}")
        prod_result = client.query_df(prod_query)
        prod_result = clean_dataframe(prod_result)
        production_data = prod_result.to_dict(orient='records') if not prod_result.empty else []
        
        # Execute alertman data query
        alert_query = format_query(
            datasources['alertman_data']['query'],
            site=site,
            partFamily=part_family
        )
        
        print(f"Alertman query: {alert_query}")
        alert_result = client.query_df(alert_query)
        alert_result = clean_dataframe(alert_result)
        alertman_data = alert_result.to_dict(orient='records') if not alert_result.empty else []

        response_data = {
            'production_data': production_data,
            'alertman_data': alertman_data
        }
        
        return jsonify(response_data)

    except Exception as e:
        error_msg = str(e) if str(e) != 'None' else "Unknown error occurred"
        print(f"Error processing request: {error_msg}")
        return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    print("Starting Flask server on http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=True) 