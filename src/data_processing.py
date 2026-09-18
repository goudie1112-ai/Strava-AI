import pandas as pd
import streamlit as st
import zipfile
import os
import tempfile
import fitparse
import gpxpy

def process_uploaded_file(uploaded_file):
    """
    Process the uploaded activities.csv from Strava bulk export.
    Returns a cleaned Pandas DataFrame.
    """
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
        if 'activity_id' in df.columns and 'id' not in df.columns:
            df['id'] = df['activity_id']
        if 'activity_name' in df.columns and 'name' not in df.columns:
            df['name'] = df['activity_name']
        return df
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return pd.DataFrame()

def parse_fit_file(file_path):
    """
    Parses a FIT file into a pandas dataframe containing the record streams.
    """
    try:
        import gzip
        
        if file_path.endswith('.gz'):
            with gzip.open(file_path, 'rb') as f:
                fit_data = f.read()
        else:
            with open(file_path, 'rb') as f:
                fit_data = f.read()
                
        fitfile = fitparse.FitFile(fit_data)
        
        records = []
        for record in fitfile.get_messages('record'):
            record_data = {}
            for record_data_field in record:
                record_data[record_data_field.name] = record_data_field.value
            records.append(record_data)
        
        if records:
            df = pd.DataFrame(records)
            return df
        return pd.DataFrame()
    except Exception as e:
        print(f"Error parsing FIT {file_path}: {e}")
        return pd.DataFrame()

def process_zip_export(uploaded_zip):
    """
    Extracts a Strava zip export, reads activities.csv, and attempts to process raw FIT/GPX files.
    For demonstration, it extracts them to a local temp directory and links them.
    """
    extract_dir = "data/raw"
    os.makedirs(extract_dir, exist_ok=True)
    
    with zipfile.ZipFile(uploaded_zip, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
        
    # Find activities.csv
    activities_csv = os.path.join(extract_dir, "activities.csv")
    if os.path.exists(activities_csv):
        df = pd.read_csv(activities_csv)
        df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
        if 'activity_id' in df.columns and 'id' not in df.columns:
            df['id'] = df['activity_id']
        if 'activity_name' in df.columns and 'name' not in df.columns:
            df['name'] = df['activity_name']
            
        # Optional: Add a column for local raw file path if it exists
        def get_raw_file(filename):
            if pd.isna(filename):
                return None
            path = os.path.join(extract_dir, filename)
            # Sometimes strava appends .gz, we'd need to unzip. 
            # For this demo we just store the path
            return path if os.path.exists(path) else None
            
        if 'filename' in df.columns:
            df['local_raw_path'] = df['filename'].apply(get_raw_file)
            
        return df
    else:
        st.error("Could not find activities.csv in the zip file.")
        return pd.DataFrame()
