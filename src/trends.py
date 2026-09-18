import pandas as pd
import plotly.express as px

def plot_weekly_distance(df):
    """
    Plots weekly distance trends.
    """
    if df.empty or 'distance' not in df.columns or 'start_date_local' not in df.columns:
        return None
        
    df['date'] = pd.to_datetime(df['start_date_local'])
    weekly = df.set_index('date').resample('W-MON').agg({'distance': 'sum'}).reset_index()
    # Convert meters to miles
    weekly['distance_miles'] = weekly['distance'] * 0.000621371
    
    fig = px.bar(weekly, x='date', y='distance_miles', title="Weekly Distance (Miles)", template="plotly_dark")
    fig.update_traces(marker_color='#00ffcc')
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="monospace", color="#00ffcc"))
    return fig

def plot_weekly_elevation(df):
    """
    Plots weekly elevation gain.
    """
    if df.empty or 'total_elevation_gain' not in df.columns or 'start_date_local' not in df.columns:
        return None
        
    df['date'] = pd.to_datetime(df['start_date_local'])
    weekly = df.set_index('date').resample('W-MON').agg({'total_elevation_gain': 'sum'}).reset_index()
    # Convert meters to feet
    weekly['elevation_feet'] = weekly['total_elevation_gain'] * 3.28084
    
    fig = px.bar(weekly, x='date', y='elevation_feet', title="Weekly Elevation Gain (Feet)", template="plotly_dark")
    fig.update_traces(marker_color='#ff0044')
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="monospace", color="#00ffcc"))
    return fig
