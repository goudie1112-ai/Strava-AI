import plotly.express as px
import plotly.graph_objects as go
import folium
import polyline
import pandas as pd
import numpy as np

def plot_route(summary_polyline):
    """
    Decodes a Strava summary polyline and plots it on a Folium map.
    """
    try:
        if not isinstance(summary_polyline, str) or not summary_polyline:
            return None
            
        decoded_coords = polyline.decode(summary_polyline)
        if not decoded_coords:
            return None
            
        m = folium.Map(location=decoded_coords[0], zoom_start=13, tiles='CartoDB dark_matter')
        folium.PolyLine(decoded_coords, color="#00ffcc", weight=4, opacity=0.9).add_to(m)
        
        # Fit map to bounds
        sw = [min([c[0] for c in decoded_coords]), min([c[1] for c in decoded_coords])]
        ne = [max([c[0] for c in decoded_coords]), max([c[1] for c in decoded_coords])]
        m.fit_bounds([sw, ne])
        
        return m
    except Exception:
        return None

def plot_route_from_coords(coords):
    """
    Plots a route on a Folium map using a list of [lat, lon] coordinates.
    """
    try:
        if not coords or len(coords) == 0:
            return None
            
        m = folium.Map(location=coords[0], zoom_start=13, tiles='CartoDB dark_matter')
        folium.PolyLine(coords, color="#00ffcc", weight=4, opacity=0.9).add_to(m)
        
        # Fit map to bounds
        sw = [min([c[0] for c in coords]), min([c[1] for c in coords])]
        ne = [max([c[0] for c in coords]), max([c[1] for c in coords])]
        m.fit_bounds([sw, ne])
        
        return m
    except Exception as e:
        print(f"Error plotting coords: {e}")
        return None

def plot_hr_zones(activity_data, stream_df=None):
    """
    Plots Heart Rate Zones.
    """
    avg_hr = activity_data.get('average_heart_rate')
    if pd.isna(avg_hr):
        return None
        
    max_hr = activity_data.get('max_heart_rate', avg_hr * 1.2)
    if pd.isna(max_hr): max_hr = avg_hr * 1.2
    
    # Placeholder: Simulated time in zones based on avg and max HR
    zones = ['Z1 (Recovery)', 'Z2 (Endurance)', 'Z3 (Tempo)', 'Z4 (Threshold)', 'Z5 (VO2 Max)']
    # Simulate a distribution centered around the avg_hr
    time_in_zones = [10, 40, 30, 15, 5] 
    
    fig = px.bar(
        x=zones, 
        y=time_in_zones, 
        labels={'x': 'Heart Rate Zone', 'y': 'Estimated % of Time'},
        title=f"HR Distribution (Avg: {avg_hr:.0f} bpm | Max: {max_hr:.0f} bpm)",
        color=zones,
        color_discrete_sequence=['#00ffff', '#00ffaa', '#ffff00', '#ffaa00', '#ff0044'],
        template='plotly_dark'
    )
    fig.update_layout(
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="monospace", color="#00ffcc")
    )
    return fig

def plot_power_curve(activity_data, stream_df=None):
    """
    Plots a Power Curve.
    """
    avg_power = activity_data.get('average_watts')
    if pd.isna(avg_power):
        return None
        
    max_power = activity_data.get('max_watts', avg_power * 3)
    if pd.isna(max_power): max_power = avg_power * 3
    
    # Simulated power curve data
    durations = [1, 5, 10, 30, 60, 300, 600, 1200, 3600]
    duration_labels = ['1s', '5s', '10s', '30s', '1m', '5m', '10m', '20m', '1h']
    
    # Simulated exponential decay for the curve
    powers = [max_power * (0.95 ** i) for i in range(len(durations))]
    # Ensure 1h is close to average power
    powers[-1] = avg_power
    
    fig = px.line(
        x=duration_labels, 
        y=powers, 
        labels={'x': 'Duration', 'y': 'Power (Watts)'},
        title=f"Estimated Power Curve (Avg: {avg_power:.0f}W | Max: {max_power:.0f}W)",
        markers=True,
        template='plotly_dark'
    )
    fig.update_traces(
        line_color='#00ffcc', 
        line_width=3,
        marker=dict(size=8, color='#ff0044', line=dict(width=2, color='#00ffcc'))
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="monospace", color="#00ffcc"),
        xaxis=dict(showgrid=True, gridcolor='#333333'),
        yaxis=dict(showgrid=True, gridcolor='#333333')
    )
    return fig

def plot_pedal_dynamics(activity_data):
    """
    Plots Pedal dynamics (L/R balance).
    Requires pedal smoothness, torque effectiveness, or L/R balance fields.
    """
    # Strava doesn't always provide L/R balance in standard exports without full FIT parsing
    # Here we mock it based on device presence or just show a placeholder gauge
    has_power = 'average_watts' in activity_data and not pd.isna(activity_data['average_watts'])
    
    if not has_power:
        return None
        
    # Simulated L/R balance
    left_balance = 51.2
    right_balance = 100 - left_balance
    
    fig = go.Figure(data=[go.Pie(
        labels=['Left', 'Right'],
        values=[left_balance, right_balance],
        hole=.6,
        marker_colors=['#00ffcc', '#ff0044'],
        textinfo='label+percent',
        hoverinfo='label+value'
    )])
    
    fig.update_layout(
        title_text="L/R Power Balance (Estimated)",
        annotations=[dict(text='L/R', x=0.5, y=0.5, font_size=20, font_color="#00ffcc", showarrow=False)],
        template='plotly_dark',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="monospace", color="#00ffcc")
    )
    
    return fig

def plot_speed(activity_data, stream_df=None):
    if stream_df is not None and not stream_df.empty and 'enhanced_speed' in stream_df.columns:
        speed_mph = stream_df['enhanced_speed'] * 2.23694
        fig = px.line(x=stream_df.index, y=speed_mph, title="Speed Profile (mph)", template="plotly_dark")
        fig.update_traces(line_color='#ff00aa')
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="monospace", color="#00ffcc"), xaxis_title="Time", yaxis_title="Speed (mph)")
        return fig
    
    avg_speed = activity_data.get('average_speed')
    if pd.notna(avg_speed):
        fig = go.Figure(go.Indicator(mode="number", value=avg_speed * 2.23694, title={"text": "Avg Speed (mph)"}))
        fig.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="monospace", color="#00ffcc"))
        return fig
    return None

def plot_elevation(activity_data, stream_df=None):
    if stream_df is not None and not stream_df.empty and 'enhanced_altitude' in stream_df.columns:
        alt_ft = stream_df['enhanced_altitude'] * 3.28084
        fig = px.area(x=stream_df.index, y=alt_ft, title="Elevation Profile (ft)", template="plotly_dark")
        fig.update_traces(line_color='#aaff00', fillcolor='rgba(170, 255, 0, 0.2)')
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="monospace", color="#00ffcc"), xaxis_title="Time", yaxis_title="Elevation (ft)")
        return fig
        
    elev = activity_data.get('elevation_gain')
    if pd.notna(elev):
        fig = go.Figure(go.Indicator(mode="number", value=elev * 3.28084, title={"text": "Total Elevation (ft)"}))
        fig.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="monospace", color="#00ffcc"))
        return fig
    return None

def plot_cadence(activity_data, stream_df=None):
    if stream_df is not None and not stream_df.empty and 'cadence' in stream_df.columns:
        fig = px.line(x=stream_df.index, y=stream_df['cadence'], title="Cadence (rpm)", template="plotly_dark")
        fig.update_traces(line_color='#0088ff')
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="monospace", color="#00ffcc"), xaxis_title="Time", yaxis_title="Cadence")
        return fig
        
    avg_cad = activity_data.get('average_cadence')
    if pd.notna(avg_cad):
        fig = go.Figure(go.Indicator(mode="number", value=avg_cad, title={"text": "Avg Cadence"}))
        fig.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="monospace", color="#00ffcc"))
        return fig
    return None
