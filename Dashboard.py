import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Set up Streamlit page
st.set_page_config(page_title="Tender Dashboard", layout="wide")

# Custom CSS for centered, bigger title and popup styling
st.markdown("""
<style>
.main-title {
    text-align: center;
    font-size: 3rem;
    font-weight: bold;
    color: #1f77b4;
    margin-bottom: 2rem;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
}
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
.tender-link {
    background: #e3f2fd;
    padding: 0.5rem;
    border-radius: 5px;
    margin: 0.2rem 0;
    border-left: 3px solid #2196f3;
}
.calendar-link-button {
    background: #4CAF50;
    color: white;
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    text-decoration: none;
    display: inline-block;
    margin: 5px;
    font-weight: bold;
}
.calendar-link-button:hover {
    background: #45a049;
    color: white;
    text-decoration: none;
}
.day-popup {
    background: #ffffff;
    border: 2px solid #2196f3;
    border-radius: 10px;
    padding: 20px;
    margin: 15px 0;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
.tender-item {
    background: #f8f9fa;
    border-left: 4px solid #007bff;
    padding: 15px;
    margin: 10px 0;
    border-radius: 5px;
}
.urgent-tender {
    border-left-color: #dc3545;
    background: #fff5f5;
}
.normal-tender {
    border-left-color: #28a745;
    background: #f8fff8;
}
</style>
""", unsafe_allow_html=True)

# Centered, bigger title
st.markdown('<h1 class="main-title">Tender Dashboard</h1>', unsafe_allow_html=True)

# Initialize session state for filters and selected date
if 'selected_cpv' not in st.session_state:
    st.session_state.selected_cpv = "All"
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.today().date()
if 'selected_calendar_date' not in st.session_state:
    st.session_state.selected_calendar_date = None
if 'show_day_popup' not in st.session_state:
    st.session_state.show_day_popup = False

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

@st.cache_data
def load_and_process_data():
    """Load and process tender data - cached to prevent reloading"""
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
            
            # Better link extraction
            tender_link = tender.get("link", "")
            
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
                    "link": tender_link,  # Keep original link
                    "Contract location": contract_location,
                    "latitude": location_coords[0] if location_coords else None,
                    "longitude": location_coords[1] if location_coords else None
                }
                
                deadline_list.append(tender_data)
                
                # Create events for calendar
                events.append({
                    "title": str(tender.get("title", "Untitled"))[:80] + "..." if len(str(tender.get("title", "Untitled"))) > 80 else str(tender.get("title", "Untitled")),
                    "start": deadline_dt.strftime('%Y-%m-%d'),
                    "end": deadline_dt.strftime('%Y-%m-%d'),
                    "backgroundColor": "#e74c3c" if deadline_dt <= pd.Timestamp(today + timedelta(days=7)) else "#3498db",
                    "borderColor": "#c0392b" if deadline_dt <= pd.Timestamp(today + timedelta(days=7)) else "#2980b9",
                    "extendedProps": {
                        "organisation": str(tender.get("organisation", "Unknown")),
                        "contract_location": str(contract_location),
                        "cpv_pairs": [str(pair) for pair in cpv_pairs],
                        "deadline_str": deadline_dt.strftime('%d %b %Y'),
                        "tender_link": tender_link,
                        "tender_id": tender.get("title", "Untitled")[:50],
                        "full_title": str(tender.get("title", "Untitled")),
                        "cpv_codes": combined_cpv
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

def get_tenders_for_date(events, target_date):
    """Get all tenders for a specific date"""
    target_date_str = target_date.strftime('%Y-%m-%d')
    day_tenders = []
    
    for event in events:
        if event['start'] == target_date_str:
            day_tenders.append(event)
    
    return day_tenders

def create_timeline_chart(df):
    """Create a timeline chart showing tender deadlines for six months"""
    if df.empty:
        return None 
    
    # Filter tenders with deadlines within the next six months
    today = pd.Timestamp(datetime.today())
    six_months_later = today + pd.DateOffset(months=6)
    df_six_months = df[(df['deadline'] >= today) & (df['deadline'] <= six_months_later)]
    
    # Group by month for better visualization
    monthly_counts = df_six_months.groupby(df_six_months['deadline'].dt.to_period('M')).size().reset_index()
    monthly_counts.columns = ['Month', 'Tender Count']  # FIXED: Consistent naming
    monthly_counts['Month'] = monthly_counts['Month'].dt.to_timestamp()
    
    fig = px.bar(
        monthly_counts,
        x='Month', 
        y='Tender Count',  # FIXED: Use correct column name
        title='Tender Deadlines Over the Next Six Months',
        labels={'Month': 'Deadline Month', 'Tender Count': 'Number of Tender'},  # FIXED: Singular "Tender"
        color='Tender Count',  # FIXED: Use correct column name
        color_continuous_scale='viridis'
    )
    
    fig.update_layout(
        xaxis_title="Deadline Month",
        yaxis_title="Number of Tender",  # FIXED: Singular "Tender"
        height=400,
        showlegend=False
    )
    
    return fig

def create_map_visualization(df):
    """Create map visualization using Plotly - without embedded title"""
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
            "Tender Count": True,  # FIXED: Use correct column name
            "latitude": False,
            "longitude": False
        },
        size="Tender Count",  # FIXED: Use correct column name
        size_max=30,
        zoom=5,
        height=500,
        color="Tender Count",  # FIXED: Use correct column name
        color_continuous_scale="viridis"
    )
    
    # Calculate center
    center_lat = map_data["latitude"].mean()
    center_lon = map_data["longitude"].mean()
    
    fig.update_layout(
        map_style="open-street-map",
        map_center={"lat": center_lat, "lon": center_lon},
        coloraxis_colorbar=dict(title="Tender Count"),
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    return fig

def create_styled_table(df):
    """Create a beautifully styled table with priority indicators and clean links"""
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
    
    # Clean link column
    def create_link_column(row):
        if row['link'] and row['link'].startswith('http'):
            return row['link']
        else:
            return ""
    
    display_df['Link'] = display_df.apply(create_link_column, axis=1)
    
    # Select and order columns for display
    final_columns = {
        'Priority': 'Priority',
        'Title': 'Tender Title',  # FIXED: Singular "Tender"
        'deadline_str': 'Deadline',
        'days_left': 'Days Left',
        'organisation': 'Organisation',
        'Contract location': 'Location',
        'Link': 'Tender Link',  # FIXED: Singular "Tender"
        'CPV': 'CPV Codes'
    }
    
    # Filter available columns
    available_cols = {k: v for k, v in final_columns.items() if k in display_df.columns}
    final_df = display_df[list(available_cols.keys())].rename(columns=available_cols)
    
    return final_df

# Load data (cached)
df_deadlines, events, sorted_cpv_details = load_and_process_data()

if df_deadlines.empty:
    st.warning("No tender data available.")  # FIXED: Singular "tender"
    st.stop()

# Sidebar Filters
st.sidebar.header("🔍 Filters")

# CPV Filter
cpv_options = ["All"] + sorted_cpv_details

def on_cpv_change():
    st.session_state.selected_cpv = st.session_state.cpv_selectbox

selected_cpv = st.sidebar.selectbox(
    "Select or Search CPV(s)", 
    options=cpv_options, 
    index=cpv_options.index(st.session_state.selected_cpv) if st.session_state.selected_cpv in cpv_options else 0,
    key="cpv_selectbox",
    on_change=on_cpv_change
)

# Date Filter
def on_date_change():
    st.session_state.selected_date = st.session_state.date_input

selected_date = st.sidebar.date_input(
    "Show tender from this date onwards",  # FIXED: Singular "tender"
    value=st.session_state.selected_date,
    key="date_input",
    on_change=on_date_change
)

# Quick date filters
st.sidebar.write("Quick filters:")
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("Today", key="today_filter"):
        st.session_state.selected_date = datetime.today().date()
        st.session_state.date_input = datetime.today().date()
        st.rerun()
    if st.button("This Week", key="week_filter"):
        st.session_state.selected_date = datetime.today().date()
        st.session_state.date_input = datetime.today().date()
        st.rerun()

with col2:
    if st.button("Next Week", key="next_week_filter"):
        new_date = (datetime.today() + timedelta(days=7)).date()
        st.session_state.selected_date = new_date
        st.session_state.date_input = new_date
        st.rerun()
    if st.button("Next Month", key="next_month_filter"):
        new_date = (datetime.today() + timedelta(days=30)).date()
        st.session_state.selected_date = new_date
        st.session_state.date_input = new_date
        st.rerun()

# Reset Buttons
st.sidebar.divider()
col1, col2, col3 = st.sidebar.columns(3)
with col1:
    if st.button("Reset CPV", key="reset_cpv"):
        st.session_state.selected_cpv = "All"
        st.session_state.cpv_selectbox = "All"
        st.rerun()

with col2:
    if st.button("Reset Date", key="reset_date"):
        today = datetime.today().date()
        st.session_state.selected_date = today
        st.session_state.date_input = today
        st.rerun()

with col3:
    if st.button("Reset All", key="reset_all"):
        today = datetime.today().date()
        st.session_state.selected_cpv = "All"
        st.session_state.selected_date = today
        st.session_state.cpv_selectbox = "All"
        st.session_state.date_input = today
        st.rerun()

# Apply filters
filtered_df, filtered_events = apply_filters(df_deadlines, events, selected_cpv, selected_date)

# Aggregate tenders per location
if not filtered_df.empty:
    location_counts = filtered_df.groupby("Contract location").size().reset_index(name="Tender Count")
    filtered_df = filtered_df.merge(location_counts, on="Contract location", how="left")

# Layout: Callout Cards
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📌 Filtered Tender", len(filtered_df))  # FIXED: Singular "Tender"
with col2:
    nearest_deadline = "N/A"
    if not filtered_df.empty:
        nearest_deadline = filtered_df["deadline"].min().strftime('%d %b %Y')
    st.metric("📆 Nearest Deadline", nearest_deadline)
with col3:
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

# Layout: Calendar and Map side by side
left, right = st.columns([1, 1], gap="medium")

with left:
    st.subheader("📅 Calendar View")
    
    if filtered_events:
        try:
            from streamlit_calendar import calendar
            
            initial_date = selected_date.strftime('%Y-%m-%d')
            
            events_with_links = sum(1 for event in filtered_events if event.get('extendedProps', {}).get('tender_link', '').startswith('http'))
            st.info(f"📅 Showing {len(filtered_events)} tender ({events_with_links} with links) from {selected_date.strftime('%d %b %Y')} onwards")  # FIXED: Singular "tender"
            
            # Calendar configuration
            calendar_options = {
                "initialView": "dayGridMonth",
                "initialDate": initial_date,
                "headerToolbar": {
                    "left": "prev,next today",
                    "center": "title",
                    "right": "dayGridMonth,listWeek"
                },
                "height": 450,
                "eventDisplay": "block",
                "eventClick": True,
                "selectable": False,
                "selectMirror": False,
                "dayMaxEvents": 3,
                "weekends": True,
                "navLinks": False,
                "editable": False,
                "droppable": False
            }
            
            # Clean events data
            clean_events = []
            for event in filtered_events:
                clean_event = {
                    "title": event["title"],
                    "start": str(event["start"]),
                    "end": str(event["end"]),
                    "backgroundColor": str(event.get("backgroundColor", "#3498db")),
                    "borderColor": str(event.get("borderColor", "#2980b9")),
                    "textColor": "#ffffff",
                    "extendedProps": event.get("extendedProps", {})
                }
                clean_events.append(clean_event)
            
            calendar_key = f"calendar_{selected_date}_{len(filtered_events)}_{hash(str(selected_cpv))}"
            
            calendar_result = calendar(
                events=clean_events, 
                options=calendar_options, 
                key=calendar_key,
                custom_css="""
                .fc-event-title {
                    font-weight: bold;
                    font-size: 12px;
                }
                .fc-event {
                    cursor: pointer;
                    border-radius: 3px;
                }
                .fc-event:hover {
                    opacity: 0.8;
                    transform: scale(1.02);
                }
                """
            )
            
            # Handle calendar event clicks with day popup
            if calendar_result and "eventClick" in calendar_result:
                clicked_event = calendar_result["eventClick"]["event"]
                clicked_date = pd.to_datetime(clicked_event["start"]).date()
                
                # Get all tenders for this date
                day_tenders = get_tenders_for_date(filtered_events, clicked_date)
                
                st.session_state.selected_calendar_date = clicked_date
                st.session_state.show_day_popup = True
            
        except ImportError:
            st.warning("📅 streamlit-calendar not installed. Install with: pip install streamlit-calendar")
            
        except Exception as e:
            st.error(f"Calendar error: {e}")

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
                st.warning("No geographic data available for filtered tender.")  # FIXED: Singular "tender"
                
                st.subheader("📍 Locations Summary")
                if "Contract location" in filtered_df.columns:
                    location_summary = filtered_df.groupby("Contract location").size().sort_values(ascending=False)
                    for location, count in location_summary.head(10).items():
                        st.write(f"**{location}**: {count} tender")  # FIXED: Singular "tender"
        except Exception as e:
            st.error(f"Map error: {e}")
            st.subheader("📍 Locations Summary")
            if "Contract location" in filtered_df.columns:
                location_summary = filtered_df.groupby("Contract location").size().sort_values(ascending=False)
                for location, count in location_summary.head(10).items():
                    st.write(f"**{location}**: {count} tender")  # FIXED: Singular "tender"
    else:
        st.info("No location data available for current filters.")

# Day Popup Window
if st.session_state.get('show_day_popup', False) and st.session_state.get('selected_calendar_date'):
    selected_date_obj = st.session_state.selected_calendar_date
    day_tenders = get_tenders_for_date(filtered_events, selected_date_obj)
    
    st.markdown(f"""
    <div class="day-popup">
        <h2>📅 Tender for {selected_date_obj.strftime('%A, %d %B %Y')}</h2>
        <p><strong>Total tender:</strong> {len(day_tenders)}</p>
    </div>
    """, unsafe_allow_html=True)  # FIXED: Singular "Tender"
    
    if day_tenders:
    
        col1, col2 = st.columns([6, 1])
        with col2:
            if st.button("❌ Close", key="close_popup"):
                st.session_state.show_day_popup = False
                st.rerun()
        
     
        for i, tender in enumerate(day_tenders):
            props = tender.get('extendedProps', {})
            tender_link = props.get('tender_link', '')
            is_urgent = tender.get('backgroundColor') == '#e74c3c'
            
            tender_class = "urgent-tender" if is_urgent else "normal-tender"
            priority_icon = "🔴" if is_urgent else "🟢"
            
            st.markdown(f"""
            <div class="tender-item {tender_class}">
                <h4>{priority_icon} {props.get('full_title', tender['title'])}</h4>
                <p><strong>Organisation:</strong> {props.get('organisation', 'Unknown')}</p>
                <p><strong>Location:</strong> {props.get('contract_location', 'Unknown')}</p>
                <p><strong>CPV Codes:</strong> {props.get('cpv_codes', 'N/A')}</p>
                <p><strong>Deadline:</strong> {props.get('deadline_str', 'Unknown')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Add link button if available
            if tender_link and tender_link.startswith('http'):
                st.markdown(f"""
                <div style="text-align: center; margin: 10px 0;">
                    <a href="{tender_link}" target="_blank" rel="noopener noreferrer" class="calendar-link-button">
                        🚀 Open Tender {i+1} in New Tab
                    </a>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning(f"⚠️ No link available for tender {i+1}")  # FIXED: Singular "tender"
            
            if i < len(day_tenders) - 1:
                st.markdown("---")
    else:
        st.info("No tender found for this date.")  # FIXED: Singular "tender"

st.divider()


st.subheader("📋 Tender Details")

if not filtered_df.empty:

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
            st.dataframe(
                styled_table,
                use_container_width=True,
                height=400,
                column_config={
                    "Priority": st.column_config.TextColumn("Priority", width="small"),
                    "Tender Title": st.column_config.TextColumn("Tender Title", width="large"),
                    "Deadline": st.column_config.TextColumn("Deadline", width="small"),
                    "Days Left": st.column_config.NumberColumn("Days Left", width="small", format="%d days"),
                    "Organisation": st.column_config.TextColumn("Organisation", width="medium"),
                    "Location": st.column_config.TextColumn("Location", width="medium"),
                    "Tender Link": st.column_config.LinkColumn(
                        "Tender Link", 
                        width="medium",
                        display_text="Open Tender"
                    ),
                    "CPV Codes": st.column_config.TextColumn("CPV Codes", width="large")
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
        simple_df = filtered_df[["title", "organisation", "Contract location", "link"]].copy()
        simple_df["Tender Link"] = simple_df["link"].apply(
            lambda x: x if x and x.startswith('http') else ""
        )
        st.dataframe(simple_df.drop('link', axis=1), use_container_width=True)
else:
    st.info("No tender match the current filters.")  # FIXED: Singular "tender"
