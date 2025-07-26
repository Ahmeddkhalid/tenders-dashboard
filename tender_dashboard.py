import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Set up Streamlit page
st.set_page_config(page_title="Tender Dashboard", layout="wide")
st.title("📅 Tender Submission Dashboard")

# Initialize session state for filters
if 'selected_cpv' not in st.session_state:
    st.session_state.selected_cpv = "All"
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.today().date()

# Load JSON data
json_file = "output/tender_opportunities.json"

# Location mapping (latitude and longitude for UK regions)
uk_location_mapping = {
    "UKH1 - East Anglia": (52.2000, 0.1313),
    "UKG21 - Telford and Wrekin": (52.6784, -2.4469),
    "UK - United Kingdom": (55.3781, -3.4360),
    "UKC1 - Tees Valley and Durham": (54.5700, -1.3200),
    "UKC2 - Northumberland and Tyne and Wear": (54.9700, -1.6100),
    "UKD1 - Cumbria": (54.4600, -2.7400),
    "UKD3 - Greater Manchester": (53.4808, -2.2426),
    "UKD6 - Cheshire": (53.2000, -2.5200),
    "UKE1 - East Yorkshire and Northern Lincolnshire": (53.7600, -0.3300),
    "UKE4 - West Yorkshire": (53.8000, -1.5500),
    "UKF1 - Derbyshire and Nottinghamshire": (53.1000, -1.5500),
    "UKF2 - Leicestershire, Rutland and Northamptonshire": (52.6369, -1.1398),
    "UKG1 - Herefordshire, Worcestershire and Warwickshire": (52.1900, -2.2200),
    "UKH2 - Bedfordshire and Hertfordshire": (51.7500, -0.4100),
    "UKH3 - Essex": (51.7340, 0.4700),
    "UKI3 - Inner London": (51.5074, -0.1278),
    "UKJ1 - Berkshire, Buckinghamshire and Oxfordshire": (51.7500, -1.2500),
    "UKJ2 - Surrey, East and West Sussex": (51.0500, -0.3200),
    "UKJ3 - Hampshire and Isle of Wight": (50.9000, -1.4000),
    "UKK1 - Gloucestershire, Wiltshire and Bath/Bristol area": (51.4500, -2.5800),
    "UKK4 - Devon": (50.7100, -3.5300),
    "UKL1 - West Wales and The Valleys": (51.7700, -3.7800),
    "UKL2 - East Wales": (52.3200, -3.8600),
    "UKM6 - Highlands and Islands": (57.4800, -5.0700),
    "UKN0 - Northern Ireland": (54.7877, -6.4923),
}

def load_and_process_data():
    """Load and process tender data"""
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        tenders = data.get("tenders", [])
        today = datetime.today()
        
        # Prepare data
        deadline_list = []
        events = []
        all_cpv_details = set()
        
        for tender in tenders:
            details = tender.get("details", {})
            deadline_raw = details.get("Submission deadline")
            contract_location = details.get("Contract location", "Unknown")
            
            try:
                deadline_dt = pd.to_datetime(deadline_raw, dayfirst=True, errors="coerce")
            except:
                deadline_dt = None
            
            if deadline_dt and deadline_dt >= pd.Timestamp(today):
                location_coords = uk_location_mapping.get(contract_location)
                cpv_codes = tender.get("cpv_codes", [])
                cpv_descriptions = tender.get("cpv_descriptions", [])
                
                # Combine CPV codes and descriptions
                combined_cpv = ", ".join([f"{code} - {desc}" for code, desc in zip(cpv_codes, cpv_descriptions)])
                
                # Add individual CPV code-description pairs to the set
                cpv_pairs = [f"{code} - {desc}" for code, desc in zip(cpv_codes, cpv_descriptions)]
                all_cpv_details.update(cpv_pairs)
                
                tender_data = {
                    "title": tender.get("title", "Untitled"),
                    "deadline": deadline_dt,
                    "organisation": tender.get("organisation", "Unknown"),
                    "cpv": combined_cpv,
                    "individual_cpvs": cpv_codes,
                    "cpv_pairs": cpv_pairs,
                    "link": tender.get("link", "#"),
                    "Contract location": contract_location,
                    "latitude": location_coords[0] if location_coords else None,
                    "longitude": location_coords[1] if location_coords else None
                }
                
                deadline_list.append(tender_data)
                
                # Create events for calendar - ENSURE ALL VALUES ARE JSON SERIALIZABLE
                events.append({
                    "title": str(tender.get("title", "Untitled")),
                    "start": deadline_dt.strftime('%Y-%m-%d'),
                    "end": deadline_dt.strftime('%Y-%m-%d'),
                    "url": str(tender.get("link", "#")),
                    "backgroundColor": "#e74c3c" if deadline_dt <= pd.Timestamp(today + timedelta(days=7)) else "#3498db",
                    "borderColor": "#c0392b" if deadline_dt <= pd.Timestamp(today + timedelta(days=7)) else "#2980b9",
                    "extendedProps": {
                        "organisation": str(tender.get("organisation", "Unknown")),
                        "contract_location": str(contract_location),
                        "cpv_pairs": [str(pair) for pair in cpv_pairs],
                        "deadline_str": deadline_dt.strftime('%d %b %Y')
                    }
                })
        
        return pd.DataFrame(deadline_list), events, sorted(all_cpv_details)
    
    except Exception as e:
        st.error(f"❌ Error loading or processing file: {e}")
        return pd.DataFrame(), [], []

def apply_filters(df, events, selected_cpv, selected_date):
    """Apply filters to both dataframe and events"""
    # Filter dataframe
    filtered_df = df.copy()
    
    if selected_cpv != "All":
        filtered_df = filtered_df[filtered_df["cpv_pairs"].apply(lambda x: selected_cpv in x)]
    
    filtered_df = filtered_df[filtered_df["deadline"] >= pd.Timestamp(selected_date)]
    
    # Filter events with consistent logic
    filtered_events = []
    for event in events:
        # Check CPV filter
        cpv_match = (selected_cpv == "All" or 
                    selected_cpv in event.get('extendedProps', {}).get('cpv_pairs', []))
        
        # Check date filter
        date_match = pd.to_datetime(event['start']) >= pd.Timestamp(selected_date)
        
        if cpv_match and date_match:
            filtered_events.append(event)
    
    return filtered_df, filtered_events

def create_timeline_chart(df):
    """Create a timeline chart showing tender deadlines"""
    if df.empty:
        return None
    
    # Group by date for better visualization
    daily_counts = df.groupby(df['deadline'].dt.date).size().reset_index()
    daily_counts.columns = ['date', 'count']
    
    fig = px.bar(
        daily_counts, 
        x='date', 
        y='count',
        title='Tender Deadlines Over Time',
        labels={'date': 'Deadline Date', 'count': 'Number of Tenders'},
        color='count',
        color_continuous_scale='viridis'
    )
    
    fig.update_layout(
        xaxis_title="Deadline Date",
        yaxis_title="Number of Tenders",
        height=300,
        showlegend=False
    )
    
    return fig

def create_map_visualization(df):
    """Create map visualization using Plotly"""
    if df.empty:
        return None
    
    map_data = df.dropna(subset=["latitude", "longitude"])
    if map_data.empty:
        return None
    
    # Create scatter mapbox
    fig = px.scatter_map(
        map_data,
        lat="latitude",
        lon="longitude",
        hover_name="title",
        hover_data={
            "Contract location": True,
            "organisation": True,
            "Tender Count": True,
            "latitude": False,
            "longitude": False
        },
        size="Tender Count",
        size_max=30,
        zoom=5,
        height=500,
        color="Tender Count",
        color_continuous_scale="viridis",
        title="Tender Locations"
    )
    
    # Calculate center
    center_lat = map_data["latitude"].mean()
    center_lon = map_data["longitude"].mean()
    
    fig.update_layout(
        map_style="open-street-map",
        map_center={"lat": center_lat, "lon": center_lon},
        coloraxis_colorbar=dict(title="Tender Count")
    )
    
    return fig

def create_styled_table(df):
    """Create a beautifully styled table with priority indicators"""
    if df.empty:
        return None
    
    # Create a clean copy for display
    display_df = df.copy()
    
    # Convert datetime to string and calculate days
    display_df['deadline_str'] = display_df['deadline'].dt.strftime('%d %b %Y')
    display_df['days_left'] = (display_df['deadline'] - pd.Timestamp.now()).dt.days
    
    # Add priority status
    def get_priority_status(days):
        if days <= 3:
            return "🔴 Critical"
        elif days <= 7:
            return "🟠 Urgent"
        elif days <= 14:
            return "🟡 Soon"
        elif days <= 30:
            return "🟢 Normal"
        else:
            return "🔵 Future"
    
    display_df['Priority'] = display_df['days_left'].apply(get_priority_status)
    
    # Truncate long titles and CPV codes for better display
    display_df['Title'] = display_df['title'].apply(lambda x: x[:60] + "..." if len(str(x)) > 60 else x)
    display_df['CPV'] = display_df['cpv'].apply(lambda x: x[:80] + "..." if len(str(x)) > 80 else x)
    
    # Select and order columns for display
    final_columns = {
        'Priority': 'Priority',
        'Title': 'Tender Title',
        'deadline_str': 'Deadline',
        'days_left': 'Days Left',
        'organisation': 'Organisation',
        'Contract location': 'Location',
        'CPV': 'CPV Codes'
    }
    
    # Filter available columns
    available_cols = {k: v for k, v in final_columns.items() if k in display_df.columns}
    final_df = display_df[list(available_cols.keys())].rename(columns=available_cols)
    
    return final_df

# Load data
df_deadlines, events, sorted_cpv_details = load_and_process_data()

if df_deadlines.empty:
    st.warning("No tender data available.")
    st.stop()

# Sidebar Filters
st.sidebar.header("🔍 Filters")

# CPV Filter
cpv_options = ["All"] + sorted_cpv_details
current_cpv_index = 0
if st.session_state.selected_cpv in cpv_options:
    current_cpv_index = cpv_options.index(st.session_state.selected_cpv)

selected_cpv = st.sidebar.selectbox(
    "Select CPV Code", 
    options=cpv_options, 
    index=current_cpv_index,
    key="cpv_selectbox"
)

# Date Filter
st.sidebar.subheader("📅 Date Range")
selected_date = st.sidebar.date_input(
    "Show tenders from this date onwards", 
    value=st.session_state.selected_date,
    key="date_input"
)

# Quick date filters
st.sidebar.write("Quick filters:")
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("Today", key="today_filter"):
        st.session_state.selected_date = datetime.today().date()
        st.rerun()
    if st.button("This Week", key="week_filter"):
        st.session_state.selected_date = datetime.today().date()
        st.rerun()

with col2:
    if st.button("Next Week", key="next_week_filter"):
        st.session_state.selected_date = (datetime.today() + timedelta(days=7)).date()
        st.rerun()
    if st.button("Next Month", key="next_month_filter"):
        st.session_state.selected_date = (datetime.today() + timedelta(days=30)).date()
        st.rerun()

# Reset Buttons
st.sidebar.divider()
col1, col2, col3 = st.sidebar.columns(3)
with col1:
    if st.button("Reset CPV", key="reset_cpv"):
        st.session_state.selected_cpv = "All"
        st.rerun()

with col2:
    if st.button("Reset Date", key="reset_date"):
        st.session_state.selected_date = datetime.today().date()
        st.rerun()

with col3:
    if st.button("Reset All", key="reset_all"):
        st.session_state.selected_cpv = "All"
        st.session_state.selected_date = datetime.today().date()
        st.rerun()

# Update session state
st.session_state.selected_cpv = selected_cpv
st.session_state.selected_date = selected_date

# Apply filters
filtered_df, filtered_events = apply_filters(df_deadlines, events, selected_cpv, selected_date)

# Aggregate tenders per location
if not filtered_df.empty:
    location_counts = filtered_df.groupby("Contract location").size().reset_index(name="Tender Count")
    filtered_df = filtered_df.merge(location_counts, on="Contract location", how="left")

# Layout: Callout Cards with better styling
st.markdown("""
<style>
.metric-container {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin: 0.5rem 0;
}
.priority-legend {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    border-left: 4px solid #007bff;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📌 Filtered Tenders", len(filtered_df))
with col2:
    nearest_deadline = "N/A"
    if not filtered_df.empty:
        nearest_deadline = filtered_df["deadline"].min().strftime('%d %b %Y')
    st.metric("📆 Nearest Deadline", nearest_deadline)
with col3:
    # Count urgent tenders (within 7 days)
    urgent_count = 0
    if not filtered_df.empty:
        urgent_deadline = datetime.now() + timedelta(days=7)
        urgent_count = len(filtered_df[filtered_df["deadline"] <= pd.Timestamp(urgent_deadline)])
    st.metric("⚠️ Urgent (7 days)", urgent_count)
with col4:
    st.metric("🏆 Total CPV Codes", len(sorted_cpv_details))

st.divider()

# Timeline Chart
if not filtered_df.empty:
    timeline_fig = create_timeline_chart(filtered_df)
    if timeline_fig:
        st.plotly_chart(timeline_fig, use_container_width=True)

st.divider()

# Layout: Calendar and Map
left, right = st.columns([1, 1])

with left:
    st.subheader("📅 Calendar View")
    
    if filtered_events:
        try:
            from streamlit_calendar import calendar
            
            initial_date = selected_date.strftime('%Y-%m-%d')
            calendar_options = {
                "initialView": "dayGridMonth",
                "initialDate": initial_date,
                "headerToolbar": {
                    "left": "prev,next today",
                    "center": "title",
                    "right": "dayGridMonth,listWeek"
                },
                "eventClick": {"url": True},
                "height": 400,
                "eventDisplay": "block"
            }
            
            st.info(f"📅 Showing {len(filtered_events)} tenders from {selected_date.strftime('%d %b %Y')} onwards")
            
            # Clean events data to ensure JSON serialization
            clean_events = []
            for event in filtered_events:
                clean_event = {
                    "title": str(event["title"]),
                    "start": str(event["start"]),
                    "end": str(event["end"]),
                    "url": str(event["url"]),
                    "backgroundColor": str(event.get("backgroundColor", "#3498db")),
                    "borderColor": str(event.get("borderColor", "#2980b9"))
                }
                clean_events.append(clean_event)
            
            calendar(events=clean_events, options=calendar_options, key=f"calendar_{selected_date}_{selected_cpv}")
            
        except ImportError:
            st.warning("📅 streamlit-calendar not installed. Install with: pip install streamlit-calendar")
            
            # Show events list as fallback
            st.subheader("Upcoming Deadlines")
            for i, event in enumerate(filtered_events[:10]):
                event_date = pd.to_datetime(event['start']).strftime('%d %b %Y')
                st.write(f"**{event_date}**: {event['title']}")
                if i < len(filtered_events) - 1:
                    st.write("---")
                    
        except Exception as e:
            st.error(f"Calendar error: {e}")
            # Show events list as fallback
            st.subheader("Upcoming Deadlines")
            for event in filtered_events[:10]:
                event_date = pd.to_datetime(event['start']).strftime('%d %b %Y')
                st.write(f"**{event_date}**: {event['title']}")
                
    else:
        st.info("No events match the current filters.")

with right:
    st.subheader("🗺️ Tender Locations")
    
    if not filtered_df.empty:
        try:
            map_fig = create_map_visualization(filtered_df)
            if map_fig:
                st.plotly_chart(map_fig, use_container_width=True)
            else:
                st.warning("No geographic data available for filtered tenders.")
                
                # Show location summary as fallback
                st.subheader("Locations Summary")
                if "Contract location" in filtered_df.columns:
                    location_summary = filtered_df.groupby("Contract location").size().sort_values(ascending=False)
                    for location, count in location_summary.head(10).items():
                        st.write(f"**{location}**: {count} tenders")
        except Exception as e:
            st.error(f"Map error: {e}")
            # Show location summary as fallback
            st.subheader("Locations Summary")
            if "Contract location" in filtered_df.columns:
                location_summary = filtered_df.groupby("Contract location").size().sort_values(ascending=False)
                for location, count in location_summary.head(10).items():
                    st.write(f"**{location}**: {count} tenders")
    else:
        st.info("No location data available for current filters.")

st.divider()

# Enhanced Table Section
st.subheader("📋 Tender Details")

if not filtered_df.empty:
    # Priority Legend
    st.markdown("""
    <div class="priority-legend">
        <h4>📊 Priority Legend</h4>
        <div style="display: flex; flex-wrap: wrap; gap: 15px; margin-top: 10px;">
            <span>🔴 <strong>Critical:</strong> ≤3 days</span>
            <span>🟠 <strong>Urgent:</strong> 4-7 days</span>
            <span>🟡 <strong>Soon:</strong> 8-14 days</span>
            <span>🟢 <strong>Normal:</strong> 15-30 days</span>
            <span>🔵 <strong>Future:</strong> >30 days</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        styled_table = create_styled_table(filtered_df)
        if styled_table is not None:
            # Display with enhanced styling
            st.dataframe(
                styled_table,
                use_container_width=True,
                height=400,
                column_config={
                    "Priority": st.column_config.TextColumn(
                        "Priority",
                        width="small",
                    ),
                    "Tender Title": st.column_config.TextColumn(
                        "Tender Title",
                        width="large",
                    ),
                    "Deadline": st.column_config.TextColumn(
                        "Deadline",
                        width="small",
                    ),
                    "Days Left": st.column_config.NumberColumn(
                        "Days Left",
                        width="small",
                        format="%d days"
                    ),
                    "Organisation": st.column_config.TextColumn(
                        "Organisation",
                        width="medium",
                    ),
                    "Location": st.column_config.TextColumn(
                        "Location",
                        width="medium",
                    ),
                    "CPV Codes": st.column_config.TextColumn(
                        "CPV Codes",
                        width="large",
                    )
                }
            )
            
            # Summary statistics
            col1, col2, col3, col4, col5 = st.columns(5)
            
            days_left = (filtered_df['deadline'] - pd.Timestamp.now()).dt.days
            
            with col1:
                critical = len(days_left[days_left <= 3])
                st.metric("🔴 Critical", critical)
            with col2:
                urgent = len(days_left[(days_left > 3) & (days_left <= 7)])
                st.metric("🟠 Urgent", urgent)
            with col3:
                soon = len(days_left[(days_left > 7) & (days_left <= 14)])
                st.metric("🟡 Soon", soon)
            with col4:
                normal = len(days_left[(days_left > 14) & (days_left <= 30)])
                st.metric("🟢 Normal", normal)
            with col5:
                future = len(days_left[days_left > 30])
                st.metric("🔵 Future", future)
            
    except Exception as e:
        st.error(f"Table display error: {e}")
        # Fallback to simple table
        simple_cols = ["title", "organisation", "Contract location"]
        available_simple_cols = [col for col in simple_cols if col in filtered_df.columns]
        if available_simple_cols:
            st.dataframe(filtered_df[available_simple_cols], use_container_width=True)
else:
    st.info("No tenders match the current filters.")

# Display filter summary
st.sidebar.divider()
st.sidebar.subheader("📊 Filter Summary")
st.sidebar.write(f"**CPV Filter:** {selected_cpv}")
st.sidebar.write(f"**Date Filter:** From {selected_date}")
st.sidebar.write(f"**Results:** {len(filtered_df)} tenders")

if not filtered_df.empty:
    try:
        date_range = f"{filtered_df['deadline'].min().strftime('%d %b')} - {filtered_df['deadline'].max().strftime('%d %b %Y')}"
        st.sidebar.write(f"**Date Range:** {date_range}")
    except:
        st.sidebar.write("**Date Range:** Available in results")
