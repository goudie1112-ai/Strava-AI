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
    durations = {'1s': 1, '2s': 2, '5s': 5, '15s': 15, '30s': 30, '1m': 60, '2m': 120, '3m': 180, '5m': 300, '10m': 600, '20m': 1200, '30m': 1800, '1h': 3600, '2h': 7200}
    records = {}
    
    for label, seconds in durations.items():
        if len(df) >= seconds:
            max_power = df['power'].rolling(window=seconds).mean().max()
            records[label] = round(max_power) if pd.notna(max_power) else None
        else:
            records[label] = None
            
    return records

def get_distance_records(df):
    """
    Extracts fastest times for standard distances from a stream dataframe.
    """
    if df.empty or 'distance' not in df.columns or 'timestamp' not in df.columns:
        return {}
        
    df = df.sort_values('timestamp')
    
    # Standard distances in meters
    distances = {'5km': 5000, '10km': 10000, '20km': 20000, '40km': 40000, '50km': 50000, '100km': 100000}
    records = {}
    
    # Pre-calculate time and distance differences
    # We want to find the minimum time to cover X distance
    # A simple way (though O(N^2) naive) is needed. For speed, we can use searchsorted or rolling.
    # Since distance is cumulative, we can use searchsorted to find the index where distance is current_dist + target_dist
    
    dist_arr = df['distance'].values
    time_arr = df['timestamp'].values
    
    import numpy as np
    
    for label, target_dist in distances.items():
        best_time = float('inf')
        
        # Fast vectorised approach:
        # Find the index of distance + target_dist
        target_distances = dist_arr + target_dist
        # Using searchsorted to find where these target distances would be inserted
        idx = np.searchsorted(dist_arr, target_distances)
        
        # Valid indices are those less than len(dist_arr)
        valid_mask = idx < len(dist_arr)
        
        if valid_mask.any():
            start_times = time_arr[valid_mask]
            end_times = time_arr[idx[valid_mask]]
            time_diffs = end_times - start_times
            
            # Additional check: ensure distance was actually covered (might be slightly less at end of array, but searchsorted goes to end)
            actual_dist_diffs = dist_arr[idx[valid_mask]] - dist_arr[valid_mask]
            
            # Filter strictly by those that reached the target distance
            dist_mask = actual_dist_diffs >= target_dist
            
            if dist_mask.any():
                min_time = np.min(time_diffs[dist_mask])
                min_seconds = pd.Timedelta(min_time).total_seconds()
                if min_seconds > 0:
                    records[label] = int(min_seconds)
                else:
                    records[label] = None
            else:
                records[label] = None
        else:
            records[label] = None
            
    return records

