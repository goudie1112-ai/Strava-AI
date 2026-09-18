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
    import shutil
    extracted_paths = []
    
    with zipfile.ZipFile(uploaded_zip, 'r') as zip_ref:
        for member in zip_ref.namelist():
            if member.startswith('activities/') and (member.endswith('.fit.gz') or member.endswith('.fit') or member.endswith('.gpx') or member.endswith('.tcx')):
                source = zip_ref.open(member)
                target_filename = os.path.basename(member)
                target_path = os.path.join(extract_dir, target_filename)
                with open(target_path, "wb") as target:
                    shutil.copyfileobj(source, target)
                extracted_paths.append(target_path)
    
    # Process activities.csv
    try:
        with zipfile.ZipFile(uploaded_zip, 'r') as zip_ref:
            with zip_ref.open('activities.csv') as f:
                df = pd.read_csv(f)
                df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
                if 'activity_id' in df.columns and 'id' not in df.columns:
                    df['id'] = df['activity_id']
                if 'activity_name' in df.columns and 'name' not in df.columns:
                    df['name'] = df['activity_name']
                
                # Match local paths
                def match_local_path(filename):
                    if pd.isna(filename): return None
                    base = os.path.basename(filename)
                    for path in extracted_paths:
                        if base in path:
                            return path
                    return None
                    
                if 'filename' in df.columns:
                    df['local_raw_path'] = df['filename'].apply(match_local_path)
                
                os.makedirs('data', exist_ok=True)
                df.to_csv('data/processed_activities.csv', index=False)
                return df
    except Exception as e:
        st.error(f"Error processing CSV inside zip: {e}")
        return pd.DataFrame()

def scan_global_records(activities_csv_path, output_json_path):
    """
    Scans all local raw fit files and calculates absolute best power and distance records.
    Saves to JSON.
    """
    import json
    from src.records import get_power_records, get_distance_records
    
    if not os.path.exists(activities_csv_path):
        return False
        
    df = pd.read_csv(activities_csv_path)
    if 'local_raw_path' not in df.columns:
        return False
        
    global_records = {}
    scanned_activities = []
    
    if os.path.exists(output_json_path):
        try:
            with open(output_json_path, 'r') as f:
                existing = json.load(f)
                if 'all_time' in existing:
                    global_records = existing
                    scanned_activities = existing.get('scanned_activities', [])
        except:
            pass
            
    if 'all_time' not in global_records:
        global_records = {'all_time': {'power': {}, 'distance': {}}}
        scanned_activities = []
        
    scanned_set = set(scanned_activities)
    
    import streamlit as st
    progress_bar = st.progress(0)
    status_text = st.empty()
    total_files = len(df)
    
    for idx, row in df.iterrows():
        # Update progress
        progress_bar.progress((idx + 1) / total_files)
        status_text.text(f"Processing activity {idx + 1} of {total_files}...")
        raw_path = row['local_raw_path']
        activity_id = str(row.get('id', ''))
        
        year = None
        if 'activity_date' in row and pd.notna(row['activity_date']):
            try:
                year = str(pd.to_datetime(row['activity_date']).year)
            except:
                pass
                
        if year and year not in global_records:
            global_records[year] = {'power': {}, 'distance': {}}
            
        if pd.isna(raw_path) or not os.path.exists(str(raw_path)):
            continue
            
        if activity_id in scanned_set:
            continue
            
        if str(raw_path).endswith('.fit') or str(raw_path).endswith('.fit.gz'):
            stream_df = parse_fit_file(str(raw_path))
            if stream_df is not None and not stream_df.empty:
                # Power
                p_recs = get_power_records(stream_df)
                for dur, val in p_recs.items():
                    if val is not None:
                        # all_time
                        if dur not in global_records['all_time']['power'] or val > global_records['all_time']['power'][dur]['value']:
                            global_records['all_time']['power'][dur] = {
                                'value': val,
                                'activity_name': row.get('name', 'Unnamed Activity'),
                                'activity_id': str(row.get('id', ''))
                            }
                        # year
                        if year:
                            if dur not in global_records[year]['power'] or val > global_records[year]['power'][dur]['value']:
                                global_records[year]['power'][dur] = {
                                    'value': val,
                                    'activity_name': row.get('name', 'Unnamed Activity'),
                                    'activity_id': str(row.get('id', ''))
                                }
                
                # Distance
                d_recs = get_distance_records(stream_df)
                for dur, val in d_recs.items():
                    if val is not None:
                        # all_time
                        if dur not in global_records['all_time']['distance'] or val < global_records['all_time']['distance'][dur]['value']:
                            global_records['all_time']['distance'][dur] = {
                                'value': val,
                                'activity_name': row.get('name', 'Unnamed Activity'),
                                'activity_id': str(row.get('id', ''))
                            }
                        # year
                        if year:
                            if dur not in global_records[year]['distance'] or val < global_records[year]['distance'][dur]['value']:
                                global_records[year]['distance'][dur] = {
                                    'value': val,
                                    'activity_name': row.get('name', 'Unnamed Activity'),
                                    'activity_id': str(row.get('id', ''))
                                }
        scanned_set.add(activity_id)
                             
    global_records['scanned_activities'] = list(scanned_set)
    
    status_text.text("Saving records...")
    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    with open(output_json_path, 'w') as f:
        json.dump(global_records, f, indent=4)
        
    progress_bar.empty()
    status_text.empty()
    return True
