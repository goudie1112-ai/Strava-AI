import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
REDIRECT_URI = "http://localhost:8501"

def get_auth_url():
    """Generates the Strava OAuth login URL."""
    if not CLIENT_ID:
        return None
    return f"https://www.strava.com/oauth/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&approval_prompt=force&scope=activity:read_all"

def exchange_token(code):
    """Exchanges the authorization code for an access token."""
    url = "https://www.strava.com/oauth/token"
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code'
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        return response.json()
    print(f"Error exchanging token: {response.text}")
    return None

def fetch_recent_activities(access_token, per_page=30):
    """Fetches recent activities from the Strava API."""
    url = "https://www.strava.com/api/v3/athlete/activities"
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {'per_page': per_page}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    print(f"Error fetching activities: {response.text}")
    return []

def fetch_activity_streams(activity_id, access_token):
    """Fetches high-resolution stream data for a specific activity."""
    url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
    headers = {'Authorization': f'Bearer {access_token}'}
    # Request all important streams
    keys = "time,distance,latlng,altitude,velocity_smooth,heartrate,cadence,watts,temp,moving,grade_smooth"
    params = {'keys': keys, 'key_by_type': 'true'}
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    print(f"Error fetching streams for {activity_id}: {response.text}")
    return None

def streams_to_dataframe(streams_data):
    """Converts the Strava API streams format into a pandas DataFrame similar to our FIT parser."""
    if not streams_data:
        return pd.DataFrame()
        
    df_data = {}
    
    # Map Strava stream keys to our local column names
    mapping = {
        'time': 'timestamp',  # Strava provides time in seconds from start
        'distance': 'distance',
        'altitude': 'altitude',
        'velocity_smooth': 'speed',
        'heartrate': 'heart_rate',
        'cadence': 'cadence',
        'watts': 'power'
    }
    
    for strava_key, local_key in mapping.items():
        if strava_key in streams_data:
            df_data[local_key] = streams_data[strava_key]['data']
            
    # Handle latlng separately
    if 'latlng' in streams_data:
        latlng = streams_data['latlng']['data']
        df_data['position_lat'] = [coord[0] for coord in latlng]
        df_data['position_long'] = [coord[1] for coord in latlng]
        
    df = pd.DataFrame(df_data)
    return df
