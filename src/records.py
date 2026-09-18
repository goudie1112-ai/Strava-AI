import pandas as pd

def get_power_records(df):
    """
    Extracts best power efforts for standard durations from a stream dataframe.
    """
    if df.empty or 'power' not in df.columns or 'timestamp' not in df.columns:
        return {}
        
    # Ensure it's sorted by time
    df = df.sort_values('timestamp')
    
    # Standard durations in seconds
    durations = {'5s': 5, '1m': 60, '5m': 300, '20m': 1200}
    records = {}
    
    for label, seconds in durations.items():
        # Using rolling mean assuming 1 record per second (typical for FIT)
        # For a robust implementation, we should resample to 1s first
        if len(df) >= seconds:
            max_power = df['power'].rolling(window=seconds).mean().max()
            records[label] = round(max_power) if pd.notna(max_power) else None
        else:
            records[label] = None
            
    return records
