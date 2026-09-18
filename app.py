import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Strava AI Analyzer", page_icon="🚴‍♂️", layout="wide")

from src.visualizations import plot_route, plot_hr_zones, plot_hr_curve, plot_power_curve, plot_power_zones, plot_pedal_dynamics, plot_speed, plot_elevation, plot_cadence
from src.data_processing import process_zip_export, parse_fit_file
from src.trends import plot_weekly_distance, plot_weekly_elevation, plot_activity_heatmap, plot_ytd_comparison, plot_activity_breakdown, calculate_eddington, plot_fitness_fatigue, plot_suffer_score
from src.records import get_power_records
from src.ai_insights import get_ai_coaching

import base64

def render_header(icon_path, title):
    if os.path.exists(icon_path):
        with open(icon_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        st.markdown(f'''
            <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 10px;">
                <img src="data:image/jpeg;base64,{encoded}" width="45" style="border-radius: 8px; box-shadow: 0 0 10px rgba(0,255,204,0.3);">
                <h3 style="margin: 0; padding: 0;">{title}</h3>
            </div>
        ''', unsafe_allow_html=True)
    else:
        st.markdown(f"### {title}")

def main():
    query_params = st.query_params
    if "code" in query_params:
        from src.strava_api import exchange_token
        code = query_params["code"]
        st.success("Authorization code received! Exchanging for token...")
        token_data = exchange_token(code)
        if token_data and 'access_token' in token_data:
            st.session_state['strava_access_token'] = token_data['access_token']
            st.success("Successfully connected to Strava API!")
            st.query_params.clear()
        else:
            st.error("Failed to exchange token.")

    if os.path.exists("Icons/App_Header.jpeg"):
        st.image("Icons/App_Header.jpeg", use_container_width=True)
        
    st.title("Strava AI Local Analyzer")
    if os.path.exists("Icons/LLM_App_Icon.jpeg"):
        st.sidebar.image("Icons/LLM_App_Icon.jpeg", use_container_width=True)
        
    st.sidebar.title("Navigation")
    
    page = st.sidebar.radio("Go to", ["Single Route", "Trends", "Personal Records", "AI Coach", "Data & Sync"], key="page_selector")
    
    data_path = "data/processed_activities.csv"
    
    if page == "Single Route":
        st.header("Single Route")
        if os.path.exists(data_path):
            df = pd.read_csv(data_path)
            
            if not df.empty:
                # Create a mapping for the selectbox format_func
                name_map = dict(zip(df['id'].astype(str), df.get('name', pd.Series(["Unnamed"] * len(df))).fillna("Unnamed Activity")))
                
                activity_id = st.selectbox(
                    "Select Activity", 
                    df['id'].astype(str).tolist(), 
                    format_func=lambda x: f"{name_map.get(x)} - {x}",
                    key="selected_activity_id"
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
                    
                col1, col2 = st.columns(2)
                with col1:
                    render_header("Icons/Speed_icon.jpeg", "Speed")
                    fig_speed = plot_speed(activity_data, stream_df)
                    if fig_speed:
                        st.plotly_chart(fig_speed, use_container_width=True)
                    else:
                        st.info("No Speed data available.")
                with col2:
                    render_header("Icons/Elevation_icon.jpeg", "Elevation")
                    fig_elev = plot_elevation(activity_data, stream_df)
                    if fig_elev:
                        st.plotly_chart(fig_elev, use_container_width=True)
                    else:
                        st.info("No Elevation data available.")
                        
                col3, col4 = st.columns(2)
                with col3:
                    render_header("Icons/Power_icon.jpeg", "Power Curve")
                    fig_power = plot_power_curve(activity_data, stream_df)
                    if fig_power:
                        st.plotly_chart(fig_power, use_container_width=True)
                    else:
                        st.info("No Power Curve data available.")
                with col4:
                    render_header("Icons/Power_icon.jpeg", "Power Zones")
                    fig_power_zones = plot_power_zones(activity_data, stream_df)
                    if fig_power_zones:
                        st.plotly_chart(fig_power_zones, use_container_width=True)
                    else:
                        st.info("No Power Zones data available.")
                        
                col5, col6 = st.columns(2)
                with col5:
                    render_header("Icons/Heart_rate_icon.jpeg", "Heart Rate")
                    fig_hr_curve = plot_hr_curve(activity_data, stream_df)
                    if fig_hr_curve:
                        st.plotly_chart(fig_hr_curve, use_container_width=True)
                    else:
                        st.info("No Heart Rate over time data available.")
                with col6:
                    render_header("Icons/Heart_rate_icon.jpeg", "HR Zones")
                    fig_hr = plot_hr_zones(activity_data, stream_df)
                    if fig_hr:
                        st.plotly_chart(fig_hr, use_container_width=True)
                    else:
                        st.info("No HR Zones data available.")
                        
                col7, col8 = st.columns(2)
                with col7:
                    render_header("Icons/Pedal_metrics_icon.jpeg", "Pedal Dynamics")
                    fig_pedal = plot_pedal_dynamics(activity_data)
                    if fig_pedal:
                        st.plotly_chart(fig_pedal, use_container_width=True)
                    else:
                        st.info("No Pedal Dynamics data available.")
                with col8:
                    render_header("Icons/Cadence_icon.jpeg", "Cadence")
                    fig_cad = plot_cadence(activity_data, stream_df)
                    if fig_cad:
                        st.plotly_chart(fig_cad, use_container_width=True)
                    else:
                        st.info("No Cadence data available for this activity.")

        else:
            st.warning("No data found. Please go to 'Upload Data'.")
            
    elif page == "Trends":
        render_header("Icons/Trends_icon.jpeg", "Aggregated Trends")
        if os.path.exists(data_path):
            df = pd.read_csv(data_path)
            
            timescale = st.selectbox("Timescale", ["All Time", "Last 30 Days", "Last 6 Months", "Last Year"])
            df['date'] = pd.to_datetime(df['activity_date'], errors='coerce')
            now = pd.Timestamp.now()
            if timescale == "Last 30 Days":
                df = df[df['date'] >= now - pd.DateOffset(days=30)]
            elif timescale == "Last 6 Months":
                df = df[df['date'] >= now - pd.DateOffset(months=6)]
            elif timescale == "Last Year":
                df = df[df['date'] >= now - pd.DateOffset(years=1)]
                
            # Top Level Metrics
            eddington = calculate_eddington(df)
            if eddington > 0:
                st.metric("Cycling Eddington Number", f"E{eddington}", help=f"You have ridden at least {eddington}km on {eddington} different days.")
                st.markdown("---")
                
            # Row 1: Weekly Distance & Elevation
            col1, col2 = st.columns(2)
            with col1:
                fig1 = plot_weekly_distance(df)
                if fig1: st.plotly_chart(fig1, use_container_width=True)
            with col2:
                fig2 = plot_weekly_elevation(df)
                if fig2: st.plotly_chart(fig2, use_container_width=True)
                
            # Row 2: Heatmap & Breakdown
            col3, col4 = st.columns([2, 1])
            with col3:
                fig_hm = plot_activity_heatmap(df)
                if fig_hm: st.plotly_chart(fig_hm, use_container_width=True)
            with col4:
                fig_bd = plot_activity_breakdown(df)
                if fig_bd: st.plotly_chart(fig_bd, use_container_width=True)
                
            # Row 3: PMC & Suffer Score
            st.markdown("### Training Load")
            col5, col6 = st.columns(2)
            with col5:
                fig_pmc = plot_fitness_fatigue(df)
                if fig_pmc: st.plotly_chart(fig_pmc, use_container_width=True)
            with col6:
                fig_ss = plot_suffer_score(df)
                if fig_ss: st.plotly_chart(fig_ss, use_container_width=True)
                
            # Row 4: YTD
            st.markdown("### Year-to-Date Progress")
            fig_ytd = plot_ytd_comparison(df)
            if fig_ytd: st.plotly_chart(fig_ytd, use_container_width=True)
        else:
            st.warning("No data found.")
            
    elif page == "Personal Records":
        render_header("Icons/Records_icon.jpeg", "Personal Records")
        if os.path.exists(data_path):
            df = pd.read_csv(data_path)
            if not df.empty:
                st.subheader("Activity Summary Highs")
                
                df['date'] = pd.to_datetime(df['activity_date'], errors='coerce')
                years = [str(int(y)) for y in df['date'].dt.year.dropna().unique()]
                years.sort(reverse=True)
                options = ["All Time"] + years
                selected_timescale = st.selectbox("Filter Records By Year", options, key="records_timescale")
                
                df_ride = df[df['activity_type'].isin(['Ride', 'Virtual Ride'])].copy()
                
                if selected_timescale != "All Time":
                    df_ride = df_ride[df_ride['date'].dt.year == int(selected_timescale)]
                
                col1, col2, col3 = st.columns(3)
                
                # Distance
                if 'distance' in df_ride.columns:
                    df_ride['distance_numeric'] = pd.to_numeric(df_ride['distance'], errors='coerce')
                    if not df_ride['distance_numeric'].isna().all():
                        max_dist_idx = df_ride['distance_numeric'].idxmax()
                        if pd.notna(max_dist_idx):
                            max_dist = df_ride.loc[max_dist_idx]
                            col1.metric("Longest Ride", f"{max_dist['distance_numeric']:.2f} km", f"{max_dist.get('name', 'Activity')}")
                
                # Elevation
                if 'elevation_gain' in df_ride.columns:
                    df_ride['elevation_numeric'] = pd.to_numeric(df_ride['elevation_gain'], errors='coerce')
                    if not df_ride['elevation_numeric'].isna().all():
                        max_elev_idx = df_ride['elevation_numeric'].idxmax()
                        if pd.notna(max_elev_idx):
                            max_elev = df_ride.loc[max_elev_idx]
                            col2.metric("Most Elevation Gain", f"{max_elev['elevation_numeric']:.0f} m", f"{max_elev.get('name', 'Activity')}")
                
                # Speed
                if 'max_speed' in df_ride.columns:
                    df_ride['max_speed_numeric'] = pd.to_numeric(df_ride['max_speed'], errors='coerce')
                    if not df_ride['max_speed_numeric'].isna().all():
                        max_speed_idx = df_ride['max_speed_numeric'].idxmax()
                        if pd.notna(max_speed_idx):
                            max_speed = df_ride.loc[max_speed_idx]
                            col3.metric("Highest Max Speed", f"{max_speed['max_speed_numeric']*3.6:.1f} km/h", f"{max_speed.get('name', 'Activity')}")
                        
                col4, col5, col6 = st.columns(3)
                
                # Avg Power
                if 'average_watts' in df_ride.columns:
                    df_ride['avg_watts_numeric'] = pd.to_numeric(df_ride['average_watts'], errors='coerce')
                    if not df_ride['avg_watts_numeric'].isna().all():
                        max_avg_power_idx = df_ride['avg_watts_numeric'].idxmax()
                        if pd.notna(max_avg_power_idx):
                            max_avg_power = df_ride.loc[max_avg_power_idx]
                            col4.metric("Highest Avg Power", f"{max_avg_power['avg_watts_numeric']:.0f} W", f"{max_avg_power.get('name', 'Activity')}")
                        
                # Max Power
                if 'max_watts' in df_ride.columns:
                    df_ride['max_watts_numeric'] = pd.to_numeric(df_ride['max_watts'], errors='coerce')
                    if not df_ride['max_watts_numeric'].isna().all():
                        max_pwr_idx = df_ride['max_watts_numeric'].idxmax()
                        if pd.notna(max_pwr_idx):
                            max_pwr = df_ride.loc[max_pwr_idx]
                            col5.metric("Highest Max Power", f"{max_pwr['max_watts_numeric']:.0f} W", f"{max_pwr.get('name', 'Activity')}")
                        
                st.markdown("---")
                
        st.subheader("Detailed Power Curve & Distance Records")
        st.info("These records are calculated by scanning your high-resolution .fit files.")
        
        global_records_path = "data/global_records.json"
        
        if st.button("Scan All Activities for Records (Takes a few minutes)"):
            from src.data_processing import scan_global_records
            with st.spinner("Scanning all local .fit files... Please wait."):
                success = scan_global_records(data_path, global_records_path)
                if success:
                    st.success("Global records calculated and saved!")
                else:
                    st.error("Failed to scan records. Make sure activities have been uploaded.")
                    
        if os.path.exists(global_records_path):
            import json
            with open(global_records_path, 'r') as f:
                records = json.load(f)
                
            record_key = "all_time" if selected_timescale == "All Time" else selected_timescale
            year_records = records.get(record_key, {})
                
            st.markdown(f"### {selected_timescale} Best Power")
            power_recs = year_records.get('power', {})
            if power_recs:
                # Group by rows of 4
                durations = list(power_recs.keys())
                for i in range(0, len(durations), 4):
                    cols = st.columns(4)
                    for j in range(4):
                        if i + j < len(durations):
                            dur = durations[i+j]
                            rec = power_recs[dur]
                            cols[j].metric(label=f"Best {dur} Power", value=f"{rec['value']} W", delta=rec['activity_name'], delta_color="off")
                            if cols[j].button(f"View Ride", key=f"btn_pwr_{selected_timescale}_{dur}"):
                                st.session_state.page_selector = "Single Route"
                                st.session_state.selected_activity_id = str(rec['activity_id'])
                                st.rerun()
            st.markdown(f"### {selected_timescale} Fastest Distances")
            dist_recs = year_records.get('distance', {})
            if dist_recs:
                durations = list(dist_recs.keys())
                for i in range(0, len(durations), 3):
                    cols = st.columns(3)
                    for j in range(3):
                        if i + j < len(durations):
                            dur = durations[i+j]
                            rec = dist_recs[dur]
                            # Format time nicely: HH:MM:SS
                            total_seconds = rec['value']
                            hours = total_seconds // 3600
                            minutes = (total_seconds % 3600) // 60
                            seconds = total_seconds % 60
                            if hours > 0:
                                time_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
                            else:
                                time_str = f"{int(minutes):02d}:{int(seconds):02d}"
                            cols[j].metric(label=f"Fastest {dur}", value=time_str, delta=rec['activity_name'], delta_color="off")
                            if cols[j].button(f"View Ride", key=f"btn_dist_{selected_timescale}_{dur}"):
                                st.session_state.page_selector = "Single Route"
                                st.session_state.selected_activity_id = str(rec['activity_id'])
                                st.rerun()
        else:
            st.warning("No detailed records found. Please click 'Scan All Activities' to generate them.")
            
        st.markdown("---")
        st.subheader("Analyze Specific Ride")
        st.info("Upload a specific .fit file to extract exact power curve records for that ride.")
        fit_file = st.file_uploader("Upload .fit file", type=["fit"])
        if fit_file:
            # Save temp
            with open("temp.fit", "wb") as f:
                f.write(fit_file.getbuffer())
            stream_df = parse_fit_file("temp.fit")
            if not stream_df.empty:
                from src.records import get_power_records
                ride_records = get_power_records(stream_df)
                for duration, power in ride_records.items():
                    st.metric(label=f"Best {duration} Power", value=f"{power} W" if power else "N/A")
            os.remove("temp.fit")
            
    elif page == "AI Coach":
        st.header("AI Training Insights")
        if os.path.exists(data_path):
            df = pd.read_csv(data_path)
            # Create a mock weekly summary text from the dataframe
            distance_sum = pd.to_numeric(df['distance'], errors='coerce').sum()
            summary_text = f"Total Activities: {len(df)}. Total distance: {distance_sum * 0.000621371:.0f} miles."
            
            api_key_input = st.text_input("Enter Gemini API Key (or set GEMINI_API_KEY env var)", type="password")
            if api_key_input:
                os.environ["GEMINI_API_KEY"] = api_key_input
                
            if st.button("Generate Coaching Insights"):
                with st.spinner("Consulting AI Coach..."):
                    insights = get_ai_coaching(summary_text)
                    st.markdown(insights)
        else:
            st.warning("No data found.")
            
    elif page == "Data & Sync":
        st.header("Data & API Sync")
        
        st.subheader("1. Live Strava API Connection")
        if 'strava_access_token' not in st.session_state:
            from src.strava_api import get_auth_url
            auth_url = get_auth_url()
            if auth_url:
                st.markdown(f'<a href="{auth_url}" target="_self"><button style="background-color:#fc4c02; color:white; padding:10px; border-radius:5px; border:none; cursor:pointer;">Connect to Strava</button></a>', unsafe_allow_html=True)
            else:
                st.error("Strava API credentials not found in .env file.")
        else:
            st.success("✅ Connected to Strava API")
            if st.button("Sync Recent Activities"):
                from src.strava_api import fetch_recent_activities, fetch_activity_streams, streams_to_dataframe
                with st.spinner("Fetching recent activities..."):
                    activities = fetch_recent_activities(st.session_state['strava_access_token'])
                    st.write(f"Found {len(activities)} recent activities.")
                    
                    if os.path.exists(data_path):
                        df = pd.read_csv(data_path)
                        existing_ids = set(df['id'].astype(str))
                    else:
                        df = pd.DataFrame()
                        existing_ids = set()
                        
                    new_rows = []
                    
                    for act in activities:
                        act_id = str(act['id'])
                        if act_id not in existing_ids:
                            st.write(f"Downloading stream for new activity: {act['name']}")
                            streams = fetch_activity_streams(act_id, st.session_state['strava_access_token'])
                            stream_df = streams_to_dataframe(streams)
                            
                            if not stream_df.empty:
                                raw_dir = "data/raw"
                                os.makedirs(raw_dir, exist_ok=True)
                                save_path = os.path.join(raw_dir, f"{act_id}_api.csv")
                                stream_df.to_csv(save_path, index=False)
                                
                                # Map Strava API activity summary format to our CSV format
                                new_row = {
                                    'id': act_id,
                                    'name': act['name'],
                                    'distance': act.get('distance', 0),
                                    'moving_time': act.get('moving_time', 0),
                                    'elapsed_time': act.get('elapsed_time', 0),
                                    'elevation_gain': act.get('total_elevation_gain', 0),
                                    'type': act.get('type', ''),
                                    'activity_date': act.get('start_date_local', ''),
                                    'average_speed': act.get('average_speed', 0),
                                    'max_speed': act.get('max_speed', 0),
                                    'average_watts': act.get('average_watts', 0),
                                    'max_watts': act.get('max_watts', 0),
                                    'average_heart_rate': act.get('average_heartrate', 0),
                                    'max_heart_rate': act.get('max_heartrate', 0),
                                    'local_raw_path': save_path
                                }
                                new_rows.append(new_row)
                                
                    if new_rows:
                        new_df = pd.DataFrame(new_rows)
                        df = pd.concat([df, new_df], ignore_index=True)
                        df.to_csv(data_path, index=False)
                        st.success(f"Successfully synced {len(new_rows)} new activities!")
                        
                        # Trigger global records update
                        from src.data_processing import scan_global_records
                        st.info("Updating Global Records with new data...")
                        scan_global_records(data_path, "data/global_records.json")
                        st.success("Global Records Updated!")
                    else:
                        st.info("No new activities to sync.")
                        
        st.markdown("---")
        st.subheader("2. Historical Bulk Upload")
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
