import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Expedition Revenue Studio",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better visual hierarchy
# I wanted the status colors to be intuitive and the metrics to stand out
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# LOAD DATA
# ============================================================================

@st.cache_data
def load_data():
    """
    Load all generated CSVs. Using cache here so data loads once per session.
    In production, this would connect to a database with refresh logic.
    """
    sailings = pd.read_csv("sailings.csv")
    bookings = pd.read_csv("bookings.csv")
    classification = pd.read_csv("sailing_classification.csv")
    forecast = pd.read_csv("revenue_forecast.csv")
    
    # Date conversions
    sailings['departure_date'] = pd.to_datetime(sailings['departure_date'])
    bookings['booking_date'] = pd.to_datetime(bookings['booking_date'])
    classification['departure_date'] = pd.to_datetime(classification['departure_date'])
    forecast['departure_date'] = pd.to_datetime(forecast['departure_date'])
    
    # Merge bookings with sailing info for detailed curve analysis
    bookings_full = bookings.merge(sailings, on='sailing_id', how='left')
    
    return sailings, bookings, bookings_full, classification, forecast

sailings, bookings, bookings_full, classification, forecast = load_data()

# ============================================================================
# HEADER
# ============================================================================

st.title("🚢 Expedition Revenue Studio")
st.markdown("**Simulated Revenue & Inventory Analytics for Expedition Cruises**")
st.markdown("""
This dashboard demonstrates core revenue management analytics: pace tracking, occupancy forecasting, 
and risk classification. Built to showcase analytical thinking for expedition cruise operations.
""")
st.markdown("---")

# ============================================================================
# SIDEBAR FILTERS
# ============================================================================
# Design choice: Put filters in sidebar to keep main area clean for analysis.
# Real RM teams would have date range selectors too, but keeping it simple here.

st.sidebar.header("📊 Filters")

# Region filter
regions = ["All"] + sorted(classification['itinerary_region'].unique().tolist())
selected_region = st.sidebar.selectbox("Region", regions)

# Ship filter (dynamically updates based on region selection)
if selected_region == "All":
    ships = ["All"] + sorted(classification['ship_name'].unique().tolist())
else:
    ships = ["All"] + sorted(
        classification[classification['itinerary_region'] == selected_region]['ship_name'].unique().tolist()
    )
selected_ship = st.sidebar.selectbox("Ship", ships)

# Status filter (this is the key action driver)
statuses = ["All", "At Risk", "On Track", "Overperforming"]
selected_status = st.sidebar.selectbox("Status", statuses)

# Apply filters to classification data
filtered_df = classification.copy()

if selected_region != "All":
    filtered_df = filtered_df[filtered_df['itinerary_region'] == selected_region]

if selected_ship != "All":
    filtered_df = filtered_df[filtered_df['ship_name'] == selected_ship]

if selected_status != "All":
    filtered_df = filtered_df[filtered_df['status'] == selected_status]

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Showing {len(filtered_df)} of {len(classification)} sailings**")

# ============================================================================
# KEY METRICS
# ============================================================================
# These are the metrics I'd want to see first thing as a revenue analyst:
# total inventory, current state, projected state, and problem count.

st.header("📈 Portfolio Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_sailings = len(filtered_df)
    st.metric("Total Sailings", f"{total_sailings}")

with col2:
    avg_current_occ = filtered_df['current_occupancy_pct'].mean()
    st.metric("Avg Current Occupancy", f"{avg_current_occ:.1f}%")

with col3:
    avg_projected_occ = filtered_df['projected_final_occupancy_pct'].mean()
    target_occ = filtered_df['target_occupancy_pct'].iloc[0] if len(filtered_df) > 0 else 90
    delta = avg_projected_occ - target_occ
    st.metric("Avg Projected Occupancy", f"{avg_projected_occ:.1f}%", 
              f"{delta:+.1f}% vs target",
              delta_color="normal")

with col4:
    at_risk_count = len(filtered_df[filtered_df['status'] == 'At Risk'])
    # Show as red if there are at-risk sailings
    if at_risk_count > 0:
        st.metric("⚠️ At Risk Sailings", f"{at_risk_count}", 
                  help="Sailings projected to miss occupancy target")
    else:
        st.metric("✅ At Risk Sailings", f"{at_risk_count}")

st.markdown("---")

# ============================================================================
# STATUS DISTRIBUTION
# ============================================================================
# Visual breakdown helps identify patterns: is one region struggling? 
# Are we generally ahead or behind pace?

st.header("🎯 Sailing Status Distribution")

col1, col2 = st.columns([1, 1])

with col1:
    # Status counts with color coding
    status_counts = filtered_df['status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    
    # Using specific colors that are intuitive: red = risk, green = good, yellow = watch
    fig_status = px.bar(
        status_counts,
        x='Status',
        y='Count',
        color='Status',
        color_discrete_map={
            'At Risk': '#ff4b4b',
            'On Track': '#ffa500',
            'Overperforming': '#00cc00'
        },
        title="Sailings by Status"
    )
    fig_status.update_layout(showlegend=False, height=350)
    st.plotly_chart(fig_status, use_container_width=True)

with col2:
    # Regional breakdown - important because performance varies by destination
    if len(filtered_df) > 0:
        region_status = pd.crosstab(
            filtered_df['itinerary_region'],
            filtered_df['status']
        ).reset_index()
        
        # Reshape for grouped bar chart
        region_status_melted = region_status.melt(
            id_vars='itinerary_region',
            var_name='Status',
            value_name='Count'
        )
        
        fig_region = px.bar(
            region_status_melted,
            x='itinerary_region',
            y='Count',
            color='Status',
            title="Status by Region",
            barmode='group',
            color_discrete_map={
                'At Risk': '#ff4b4b',
                'On Track': '#ffa500',
                'Overperforming': '#00cc00'
            }
        )
        fig_region.update_layout(height=350, xaxis_title="Region")
        st.plotly_chart(fig_region, use_container_width=True)

st.markdown("---")

# ============================================================================
# SAILING DETAIL TABLE
# ============================================================================
# The action layer: analysts need to see individual sailings with recommendations.
# Color-coding makes at-risk sailings immediately visible.

st.header("📋 Sailing Details & Recommendations")

if len(filtered_df) > 0:
    # Sort by urgency: at-risk sailings closest to departure first
    display_df = filtered_df.copy()
    display_df['urgency_score'] = display_df.apply(
        lambda x: (1 if x['status'] == 'At Risk' else 2 if x['status'] == 'On Track' else 3) * 1000 - x['days_until_departure'],
        axis=1
    )
    display_df = display_df.sort_values('urgency_score', ascending=False)
    
    # Select columns for display
    table_df = display_df[[
        'sailing_id', 'itinerary_region', 'ship_name', 'departure_date',
        'days_until_departure', 'current_occupancy_pct', 'projected_final_occupancy_pct',
        'status', 'recommended_action'
    ]].copy()
    
    table_df['departure_date'] = table_df['departure_date'].dt.strftime('%Y-%m-%d')
    
    # Color coding function for status column
    def highlight_status(row):
        if row['status'] == 'At Risk':
            return ['background-color: #ffcccc'] * len(row)
        elif row['status'] == 'Overperforming':
            return ['background-color: #ccffcc'] * len(row)
        else:
            return ['background-color: #ffffcc'] * len(row)
    
    # Display styled dataframe
    st.dataframe(
        table_df.style.apply(highlight_status, axis=1),
        use_container_width=True,
        height=400
    )
    
    # Download option - analysts need to export for further analysis or presentations
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Filtered Data as CSV",
        data=csv,
        file_name=f"sailing_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
else:
    st.info("No sailings match the selected filters.")

st.markdown("---")

# ============================================================================
# INDIVIDUAL SAILING DEEP DIVE
# ============================================================================
# This is where you'd drill down in a real workflow: examine the booking curve,
# understand velocity, see competitive positioning, decide on action.

st.header("🔍 Individual Sailing Deep Dive")

if len(filtered_df) > 0:
    # Sailing selector with helpful formatting
    sailing_options = filtered_df.sort_values('departure_date')['sailing_id'].tolist()
    
    selected_sailing = st.selectbox(
        "Select a sailing to analyze:",
        sailing_options,
        format_func=lambda x: f"{x} - {filtered_df[filtered_df['sailing_id']==x].iloc[0]['itinerary_region']} ({filtered_df[filtered_df['sailing_id']==x].iloc[0]['status']})"
    )
    
    # Get full details for selected sailing
    sailing_detail = filtered_df[filtered_df['sailing_id'] == selected_sailing].iloc[0]
    
    # Display key metrics in a clean grid
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Region", sailing_detail['itinerary_region'])
    
    with col2:
        st.metric("Days to Departure", f"{sailing_detail['days_until_departure']}")
    
    with col3:
        st.metric("Current Occupancy", f"{sailing_detail['current_occupancy_pct']:.1f}%")
    
    with col4:
        delta = sailing_detail['projected_final_occupancy_pct'] - sailing_detail['target_occupancy_pct']
        st.metric(
            "Projected Final", 
            f"{sailing_detail['projected_final_occupancy_pct']:.1f}%",
            f"{delta:+.1f}% vs target"
        )
    
    with col5:
        comp_idx = sailing_detail['competitor_price_index']
        # Interpret competitor index for user
        if comp_idx > 1.0:
            comp_status = f"We're {((comp_idx-1)*100):.0f}% cheaper"
            comp_color = "normal"
        else:
            comp_status = f"We're {((1-comp_idx)*100):.0f}% pricier"
            comp_color = "inverse"
        st.metric("vs Competitors", comp_status, delta_color=comp_color)
    
    # Status banner with visual indicator
    status_emoji = {
        'At Risk': '🔴',
        'On Track': '🟡',
        'Overperforming': '🟢'
    }
    
    st.markdown(f"### {status_emoji[sailing_detail['status']]} Status: **{sailing_detail['status']}**")
    
    # Recommendations in a callout box
    st.info(f"**💡 Recommended Actions:**\n\n{sailing_detail['recommended_action'].replace(' | ', '\n\n')}")
    
    # ========================================================================
    # BOOKING CURVE VISUALIZATION
    # ========================================================================
    # This is critical for understanding velocity. A flat curve means stalled bookings.
    # A steep curve means strong recent pace. The shape tells the story.
    
    st.markdown("### 📈 Booking Curve Analysis")
    
    sailing_bookings = bookings_full[bookings_full['sailing_id'] == selected_sailing].copy()
    
    if len(sailing_bookings) > 0:
        # Sort and calculate cumulative bookings
        sailing_bookings = sailing_bookings.sort_values('days_to_departure', ascending=False)
        sailing_bookings['cumulative_cabins'] = range(1, len(sailing_bookings) + 1)
        sailing_bookings['percent_filled'] = (
            sailing_bookings['cumulative_cabins'] / sailing_detail['capacity_cabins'] * 100
        )
        
        # Create interactive booking curve
        fig = go.Figure()
        
        # Main booking curve
        fig.add_trace(go.Scatter(
            x=sailing_bookings['days_to_departure'],
            y=sailing_bookings['percent_filled'],
            mode='lines+markers',
            name='Booking Curve',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=4),
            hovertemplate='<b>%{x} days out</b><br>%{y:.1f}% filled<extra></extra>'
        ))
        
        # Target occupancy reference line
        fig.add_hline(
            y=sailing_detail['target_occupancy_pct'],
            line_dash="dash",
            line_color="red",
            annotation_text=f"Target: {sailing_detail['target_occupancy_pct']:.0f}%",
            annotation_position="right"
        )
        
        # Projected final occupancy
        fig.add_hline(
            y=sailing_detail['projected_final_occupancy_pct'],
            line_dash="dot",
            line_color="green",
            annotation_text=f"Projected: {sailing_detail['projected_final_occupancy_pct']:.1f}%",
            annotation_position="left"
        )
        
        # Formatting
        fig.update_layout(
            title=f"Booking Curve: {selected_sailing} - {sailing_detail['itinerary_region']}",
            xaxis_title="Days to Departure",
            yaxis_title="% of Capacity Filled",
            height=450,
            hovermode='x unified',
            showlegend=True
        )
        
        # Time moves forward left to right (more intuitive for booking curves)
        fig.update_xaxes(autorange="reversed")
        fig.update_yaxes(range=[0, 105])
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Key insights about this curve
        st.markdown("**📊 Curve Insights:**")
        
        # Calculate booking velocity (recent vs early)
        recent_bookings = sailing_bookings[sailing_bookings['days_to_departure'] < 60]
        early_bookings = sailing_bookings[sailing_bookings['days_to_departure'] >= 180]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Early Bookings (180+ days)", f"{len(early_bookings)}")
        with col2:
            st.metric("Recent Bookings (<60 days)", f"{len(recent_bookings)}")
        with col3:
            avg_lead_time = sailing_bookings['days_to_departure'].mean()
            st.metric("Avg Booking Lead Time", f"{avg_lead_time:.0f} days")
        
    else:
        st.warning("⚠️ No bookings yet for this sailing - immediate action required!")
        st.markdown("""
        **Recommended First Steps:**
        - Verify sailing is active in distribution channels
        - Check competitive pricing for similar itineraries
        - Launch awareness campaign targeting past guests
        - Consider early booker incentive
        """)

else:
    st.info("No sailings match the selected filters. Adjust filters to see sailing details.")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>Expedition Revenue Studio</strong> | Portfolio Project by Shivani</p>
    <p style='font-size: 0.9em;'>Synthetic data for demonstration purposes | Built with Python, Pandas, Plotly, Streamlit</p>
    <p style='font-size: 0.8em;'>This dashboard showcases revenue management analytics capabilities for expedition cruise operations</p>
</div>
""", unsafe_allow_html=True)