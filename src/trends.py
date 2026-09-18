import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def plot_weekly_distance(df):
    """
    Plots weekly distance trends.
    """
    if df.empty or 'distance' not in df.columns or 'activity_date' not in df.columns:
        return None
        
    df['date'] = pd.to_datetime(df['activity_date'])
    df['distance'] = pd.to_numeric(df['distance'], errors='coerce').fillna(0)
    weekly = df.set_index('date').resample('W-MON').agg({'distance': 'sum'}).reset_index()
    # Convert meters to km
    weekly['distance_km'] = weekly['distance']
    
    fig = px.bar(weekly, x='date', y='distance_km', title="Weekly Distance (km)", template="plotly_dark")
    fig.update_traces(marker_color='#00ffcc')
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="monospace", color="#00ffcc"))
    return fig

def plot_weekly_elevation(df):
    """
    Plots weekly elevation gain.
    """
    if df.empty or 'elevation_gain' not in df.columns or 'activity_date' not in df.columns:
        return None
        
    df['date'] = pd.to_datetime(df['activity_date'])
    df['elevation_gain'] = pd.to_numeric(df['elevation_gain'], errors='coerce').fillna(0)
    weekly = df.set_index('date').resample('W-MON').agg({'elevation_gain': 'sum'}).reset_index()
    # Use meters for elevation
    weekly['elevation_m'] = weekly['elevation_gain']
    
    fig = px.bar(weekly, x='date', y='elevation_m', title="Weekly Elevation Gain (m)", template="plotly_dark")
    fig.update_traces(marker_color='#ff0044')
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="monospace", color="#00ffcc"))
    return fig

def plot_activity_heatmap(df):
    if df.empty or 'activity_date' not in df.columns: return None
    df['date'] = pd.to_datetime(df['activity_date']).dt.date
    daily = df.groupby('date').size().reset_index(name='count')
    fig = px.scatter(daily, x='date', y='count', size='count', color='count', 
                     color_continuous_scale='Mint', title="Activity Heatmap (Daily Count)", template="plotly_dark")
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="monospace", color="#00ffcc"))
    return fig

def plot_ytd_comparison(df):
    if df.empty or 'activity_date' not in df.columns or 'distance' not in df.columns: return None
    df['date'] = pd.to_datetime(df['activity_date'])
    df['distance_km'] = pd.to_numeric(df['distance'], errors='coerce').fillna(0)
    df['year'] = df['date'].dt.year
    df['day_of_year'] = df['date'].dt.dayofyear
    ytd = df.groupby(['year', 'day_of_year'])['distance_km'].sum().groupby(level=0).cumsum().reset_index()
    fig = px.line(ytd, x='day_of_year', y='distance_km', color='year', 
                  title="YTD Distance Comparison (km)", template="plotly_dark")
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="monospace", color="#00ffcc"))
    return fig

def plot_activity_breakdown(df):
    if df.empty or 'activity_type' not in df.columns: return None
    breakdown = df['activity_type'].value_counts().reset_index()
    breakdown.columns = ['type', 'count']
    fig = px.pie(breakdown, values='count', names='type', hole=0.4, 
                 title="Activity Type Breakdown", template="plotly_dark")
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="monospace", color="#00ffcc"))
    return fig

def calculate_eddington(df):
    if df.empty or 'activity_date' not in df.columns or 'distance' not in df.columns: return 0
    rides = df[df['activity_type'].isin(['Ride', 'Virtual Ride'])].copy()
    if rides.empty: return 0
    rides['date'] = pd.to_datetime(rides['activity_date']).dt.date
    rides['distance'] = pd.to_numeric(rides['distance'], errors='coerce').fillna(0)
    daily_dist = rides.groupby('date')['distance'].sum()
    sorted_dist = sorted(daily_dist.values, reverse=True)
    E = 0
    for i, d in enumerate(sorted_dist):
        if d >= (i + 1): E = i + 1
        else: break
    return E

def plot_fitness_fatigue(df):
    if df.empty or 'activity_date' not in df.columns or 'relative_effort' not in df.columns: return None
    df['date'] = pd.to_datetime(df['activity_date']).dt.date
    df['relative_effort'] = pd.to_numeric(df['relative_effort'], errors='coerce').fillna(0)
    daily = df.groupby('date')['relative_effort'].sum().reset_index()
    daily['date'] = pd.to_datetime(daily['date'])
    daily = daily.set_index('date').asfreq('D', fill_value=0)
    daily['Fitness (CTL)'] = daily['relative_effort'].ewm(span=42, min_periods=1).mean()
    daily['Fatigue (ATL)'] = daily['relative_effort'].ewm(span=7, min_periods=1).mean()
    daily['Form (TSB)'] = daily['Fitness (CTL)'] - daily['Fatigue (ATL)']
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily.index, y=daily['Fitness (CTL)'], name='Fitness (CTL)', line=dict(color='#00ffcc', width=2)))
    fig.add_trace(go.Scatter(x=daily.index, y=daily['Fatigue (ATL)'], name='Fatigue (ATL)', line=dict(color='#ff00aa', width=1)))
    fig.add_trace(go.Scatter(x=daily.index, y=daily['Form (TSB)'], name='Form (TSB)', fill='tozeroy', line=dict(color='rgba(255, 255, 255, 0.2)')))
    fig.update_layout(title="Performance Management Chart (Fitness/Fatigue)", template="plotly_dark", 
                      plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="monospace", color="#00ffcc"))
    return fig

def plot_suffer_score(df):
    if df.empty or 'activity_date' not in df.columns or 'relative_effort' not in df.columns: return None
    df['date'] = pd.to_datetime(df['activity_date']).dt.date
    df['relative_effort'] = pd.to_numeric(df['relative_effort'], errors='coerce').fillna(0)
    daily = df.groupby('date')['relative_effort'].sum().reset_index()
    fig = px.bar(daily, x='date', y='relative_effort', title="Daily Relative Effort", template="plotly_dark")
    fig.update_traces(marker_color='#ffaa00')
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="monospace", color="#00ffcc"))
    return fig
