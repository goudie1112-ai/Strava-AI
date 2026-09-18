import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Strava AI Analyzer", page_icon="🚴‍♂️", layout="wide")

from src.visualizations import plot_route, plot_hr_zones, plot_power_curve, plot_pedal_dynamics, plot_speed, plot_elevation, plot_cadence
from src.data_processing import process_zip_export, parse_fit_file
from src.trends import plot_weekly_distance, plot_weekly_elevation
from src.records import get_power_records
from src.ai_insights import get_ai_coaching

def render_header(icon_path, title):
    col1, col2 = st.columns([1, 10])
    with col1:
        if os.path.exists(icon_path):
            st.image(icon_path, width=40)
    with col2:
        st.markdown(f"### {title}")

def main():
    if os.path.exists("Icons/App_Header.jpeg"):
        st.image("Icons/App_Header.jpeg", use_container_width=True)
        
    st.title("Strava AI Local Analyzer")
    st.sidebar.title("Navigation")
    
    page = st.sidebar.radio("Go to", ["Dashboard", "Trends", "Personal Records", "AI Coach", "Upload Data"])
    
    data_path = "data/processed_activities.csv"
    
    if page == "Dashboard":
        st.header("Activity Dashboard")
        if os.path.exists(data_path):
            df = pd.read_csv(data_path)
            
            if not df.empty:
                # Create a mapping for the selectbox format_func
                name_map = dict(zip(df['id'].astype(str), df.get('name', pd.Series(["Unnamed"] * len(df))).fillna("Unnamed Activity")))
                
                activity_id = st.selectbox(
                    "Select Activity", 
                    df['id'].astype(str).tolist(), 
                    format_func=lambda x: f"{name_map.get(x)} - {x}"
                )
                activity_data = df[df['id'].astype(str) == activity_id].iloc[0]
                
                st.subheader(f"{activity_data.get('name', 'Unnamed Activity')}")
                
                # Check for high-res data
                raw_path = activity_data.get('local_raw_path')
                stream_df = None
                if pd.notna(raw_path) and os.path.exists(str(raw_path)):
                    if str(raw_path).endswith('.fit') or str(raw_path).endswith('.fit.gz'):
                        stream_df = parse_fit_file(str(raw_path))
                        if stream_df is not None and not stream_df.empty:
                            st.success(f"High-res data loaded: {os.path.basename(str(raw_path))} ({len(stream_df)} points)")
                
                col1, col2 = st.columns(2)
                with col1:
                    render_header("Icons/Routes_icon.jpeg", "Route Map")
                    map_obj = None
                    if stream_df is not None and not stream_df.empty and 'position_lat' in stream_df.columns and 'position_long' in stream_df.columns:
                        coords = []
                        for _, row in stream_df.dropna(subset=['position_lat', 'position_long']).iterrows():
                            lat = row['position_lat'] * (180.0 / (2**31))
                            lon = row['position_long'] * (180.0 / (2**31))
                            coords.append([lat, lon])
                        from src.visualizations import plot_route_from_coords
                        map_obj = plot_route_from_coords(coords)
                    
                    if map_obj:
                        st.components.v1.html(map_obj._repr_html_(), height=400)
                    else:
                        st.info("No route data available.")
                with col2:
                    render_header("Icons/Speed_icon.jpeg", "Speed")
                    fig_speed = plot_speed(activity_data, stream_df)
                    if fig_speed:
                        st.plotly_chart(fig_speed, use_container_width=True)
                    else:
                        st.info("No Speed data available.")
                        
                col3, col4 = st.columns(2)
                with col3:
                    st.markdown("### HR Zones")
                    fig_hr = plot_hr_zones(activity_data, stream_df)
                    if fig_hr:
                        st.plotly_chart(fig_hr, use_container_width=True)
                    else:
                        st.info("No HR data available.")
                with col4:
                    st.markdown("### Power Curve & Zones")
                    fig_power = plot_power_curve(activity_data, stream_df)
                    if fig_power:
                        st.plotly_chart(fig_power, use_container_width=True)
                    else:
                        st.info("No Power data available.")
                        
                col5, col6 = st.columns(2)
                with col5:
                    render_header("Icons/Pedal_metrics_icon.jpeg", "Pedal Dynamics")
                    fig_pedal = plot_pedal_dynamics(activity_data)
                    if fig_pedal:
                        st.plotly_chart(fig_pedal, use_container_width=True)
                    else:
                        st.info("No Pedal Dynamics data available.")
                        
                col7, col8 = st.columns(2)
                with col7:
                    render_header("Icons/Elevation_icon.jpeg", "Elevation")
                    fig_elev = plot_elevation(activity_data, stream_df)
                    if fig_elev:
                        st.plotly_chart(fig_elev, use_container_width=True)
                    else:
                        st.info("No Elevation data available.")
                with col8:
                    render_header("Icons/Cadence_icon.jpeg", "Cadence")
                    fig_cad = plot_cadence(activity_data, stream_df)
                    if fig_cad:
                        st.plotly_chart(fig_cad, use_container_width=True)
                    else:
                        st.info("No Cadence data available.")

        else:
            st.warning("No data found. Please go to 'Upload Data'.")
            
    elif page == "Trends":
        st.header("Aggregated Trends")
        if os.path.exists(data_path):
            df = pd.read_csv(data_path)
            col1, col2 = st.columns(2)
            with col1:
                fig1 = plot_weekly_distance(df)
                if fig1: st.plotly_chart(fig1, use_container_width=True)
            with col2:
                fig2 = plot_weekly_elevation(df)
                if fig2: st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("No data found.")
            
    elif page == "Personal Records":
        st.header("Personal Records")
        st.info("Upload a .fit file to extract power records.")
        fit_file = st.file_uploader("Upload .fit file", type=["fit"])
        if fit_file:
            # Save temp
            with open("temp.fit", "wb") as f:
                f.write(fit_file.getbuffer())
            stream_df = parse_fit_file("temp.fit")
            if not stream_df.empty:
                records = get_power_records(stream_df)
                for duration, power in records.items():
                    st.metric(label=f"Best {duration} Power", value=f"{power} W" if power else "N/A")
            os.remove("temp.fit")
            
    elif page == "AI Coach":
        st.header("AI Training Insights")
        if os.path.exists(data_path):
            df = pd.read_csv(data_path)
            # Create a mock weekly summary text from the dataframe
            summary_text = f"Total Activities: {len(df)}. Total distance: {df['distance'].sum() * 0.000621371:.0f} miles."
            
            api_key_input = st.text_input("Enter Gemini API Key (or set GEMINI_API_KEY env var)", type="password")
            if api_key_input:
                os.environ["GEMINI_API_KEY"] = api_key_input
                
            if st.button("Generate Coaching Insights"):
                with st.spinner("Consulting AI Coach..."):
                    insights = get_ai_coaching(summary_text)
                    st.markdown(insights)
        else:
            st.warning("No data found.")
            
    elif page == "Upload Data":
        st.header("Upload Strava Archive")
        st.write("Upload your full Strava export `.zip` file.")
        
        uploaded_file = st.file_uploader("Choose a ZIP file", type="zip")
        if uploaded_file is not None:
            if st.button("Process Archive"):
                with st.spinner("Extracting and Processing..."):
                    df = process_zip_export(uploaded_file)
                    df.to_csv("data/processed_activities.csv", index=False)
                    st.success(f"Processed {len(df)} activities successfully!")

if __name__ == "__main__":
    main()
