import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

# Set style for better-looking plots
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

print("=" * 80)
print("EXPEDITION REVENUE STUDIO: EDA & BOOKING CURVE ANALYSIS")
print("=" * 80)

# ============================================================================
# SECTION 1: Load Data
# ============================================================================

sailings = pd.read_csv("sailings.csv")
bookings = pd.read_csv("bookings.csv")

# Convert date columns
sailings['departure_date'] = pd.to_datetime(sailings['departure_date'])
bookings['booking_date'] = pd.to_datetime(bookings['booking_date'])

print(f"\n✅ Loaded {len(sailings)} sailings and {len(bookings)} bookings")

# ============================================================================
# SECTION 2: Basic EDA
# ============================================================================

print("\n" + "=" * 80)
print("EXPLORATORY DATA ANALYSIS")
print("=" * 80)

# Sailings by region
print("\n📊 Sailings by Region:")
region_counts = sailings.groupby('itinerary_region').agg({
    'sailing_id': 'count',
    'capacity_cabins': 'mean',
    'base_fare_per_person': 'mean'
}).round(0)
region_counts.columns = ['Count', 'Avg Capacity', 'Avg Base Fare']
print(region_counts)

# Capacity distribution
print("\n📊 Capacity Statistics:")
print(sailings['capacity_cabins'].describe())

# Booking statistics
print("\n📊 Booking Statistics:")
print(f"Total Bookings: {len(bookings):,}")
print(f"Avg Party Size: {bookings['party_size'].mean():.2f}")
print(f"Avg Days to Departure: {bookings['days_to_departure'].mean():.1f}")
print(f"Avg Fare Paid: ${bookings['fare_paid_per_person'].mean():,.0f}")
print(f"Discount Rate: {bookings['discount_flag'].mean():.1%}")

# Bookings by segment
print("\n📊 Bookings by Segment:")
print(bookings['booking_segment'].value_counts())

# ============================================================================
# SECTION 3: Booking Curves Analysis
# ============================================================================

print("\n" + "=" * 80)
print("BOOKING CURVES ANALYSIS")
print("=" * 80)

# Merge sailings and bookings
df = bookings.merge(sailings, on='sailing_id', how='left')

# Calculate cumulative cabins sold for each sailing
booking_curves = []

for sailing_id in sailings['sailing_id'].unique():
    sailing_bookings = df[df['sailing_id'] == sailing_id].copy()
    sailing_info = sailings[sailings['sailing_id'] == sailing_id].iloc[0]
    
    if len(sailing_bookings) == 0:
        continue
    
    # Sort by days_to_departure (descending, so earliest bookings first)
    sailing_bookings = sailing_bookings.sort_values('days_to_departure', ascending=False)
    
    # Calculate cumulative cabins sold
    # Each booking represents parties, but we track cabins
    # Simplification: assume each party books 1 cabin
    sailing_bookings['cumulative_cabins'] = range(1, len(sailing_bookings) + 1)
    sailing_bookings['percent_filled'] = (
        sailing_bookings['cumulative_cabins'] / sailing_info['capacity_cabins'] * 100
    )
    
    # Add to list
    for _, row in sailing_bookings.iterrows():
        booking_curves.append({
            'sailing_id': sailing_id,
            'itinerary_region': sailing_info['itinerary_region'],
            'ship_name': sailing_info['ship_name'],
            'departure_date': sailing_info['departure_date'],
            'capacity_cabins': sailing_info['capacity_cabins'],
            'days_to_departure': row['days_to_departure'],
            'cumulative_cabins': row['cumulative_cabins'],
            'percent_filled': row['percent_filled']
        })

curves_df = pd.DataFrame(booking_curves)

print(f"\n✅ Generated booking curves for {curves_df['sailing_id'].nunique()} sailings")

# Plot example booking curves by region
print("\n📈 Generating booking curve plots...")

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Booking Curves by Region (Sample Sailings)', fontsize=16, fontweight='bold')

regions = ['Antarctica', 'Galápagos', 'Arctic', 'Alaska']

for idx, region in enumerate(regions):
    ax = axes[idx // 2, idx % 2]
    
    # Get sample sailings from this region
    region_sailings = curves_df[curves_df['itinerary_region'] == region]['sailing_id'].unique()
    sample_sailings = region_sailings[:3] if len(region_sailings) >= 3 else region_sailings
    
    for sailing_id in sample_sailings:
        sailing_data = curves_df[curves_df['sailing_id'] == sailing_id].sort_values('days_to_departure', ascending=False)
        ax.plot(sailing_data['days_to_departure'], sailing_data['percent_filled'], 
                marker='o', markersize=2, linewidth=2, label=sailing_id, alpha=0.7)
    
    ax.set_xlabel('Days to Departure', fontsize=11)
    ax.set_ylabel('% of Capacity Filled', fontsize=11)
    ax.set_title(f'{region}', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=9)
    ax.invert_xaxis()  # So time moves forward left to right
    ax.set_ylim(0, 100)

plt.tight_layout()
plt.savefig('booking_curves_by_region.png', dpi=300, bbox_inches='tight')
print("✅ Saved: booking_curves_by_region.png")

# Calculate average booking curve by region
print("\n📊 Average Booking Curves by Region:")

# Bin days_to_departure into buckets for averaging
def bin_days(days):
    if days >= 180:
        return "180+"
    elif days >= 120:
        return "120-180"
    elif days >= 90:
        return "90-120"
    elif days >= 60:
        return "60-90"
    elif days >= 30:
        return "30-60"
    else:
        return "0-30"

curves_df['days_bin'] = curves_df['days_to_departure'].apply(bin_days)

avg_curves = curves_df.groupby(['itinerary_region', 'days_bin']).agg({
    'percent_filled': 'mean'
}).reset_index()

print(avg_curves.pivot(index='days_bin', columns='itinerary_region', values='percent_filled').round(1))

# ============================================================================
# SECTION 4: Pace vs Target Analysis
# ============================================================================

print("\n" + "=" * 80)
print("PACE VS TARGET ANALYSIS")
print("=" * 80)

# Define "today" for analysis (let's use a fixed reference date)
# In practice, this would be datetime.now()
ANALYSIS_DATE = datetime(2025, 9, 1)  # Simulated "today"
print(f"\nAnalysis Reference Date: {ANALYSIS_DATE.strftime('%Y-%m-%d')}")

# Calculate current state for each sailing
current_state = []

for sailing_id in sailings['sailing_id'].unique():
    sailing_info = sailings[sailings['sailing_id'] == sailing_id].iloc[0]
    departure_date = sailing_info['departure_date']
    
    # Skip sailings that have already departed
    if departure_date < ANALYSIS_DATE:
        continue
    
    days_until_departure = (departure_date - ANALYSIS_DATE).days
    
    # Get bookings made before analysis date
    sailing_bookings = df[
        (df['sailing_id'] == sailing_id) & 
        (df['booking_date'] <= ANALYSIS_DATE)
    ]
    
    current_cabins_sold = len(sailing_bookings)
    current_occupancy_pct = (current_cabins_sold / sailing_info['capacity_cabins']) * 100
    
    current_state.append({
        'sailing_id': sailing_id,
        'itinerary_region': sailing_info['itinerary_region'],
        'ship_name': sailing_info['ship_name'],
        'departure_date': departure_date,
        'days_until_departure': days_until_departure,
        'capacity_cabins': sailing_info['capacity_cabins'],
        'current_cabins_sold': current_cabins_sold,
        'current_occupancy_pct': round(current_occupancy_pct, 1)
    })

current_df = pd.DataFrame(current_state)

# Calculate target curves by region
# Target = historical average % filled at each days_to_departure
target_curves = curves_df.groupby(['itinerary_region', 'days_to_departure']).agg({
    'percent_filled': 'mean'
}).reset_index()
target_curves = target_curves.rename(columns={'percent_filled': 'target_percent_filled'})

# For each current sailing, find target at its days_until_departure
pace_analysis = []

for _, sailing in current_df.iterrows():
    region = sailing['itinerary_region']
    days_out = sailing['days_until_departure']
    
    # Find closest target in historical data
    region_targets = target_curves[target_curves['itinerary_region'] == region]
    
    if len(region_targets) > 0:
        # Find closest days_to_departure in targets
        region_targets = region_targets.copy()
        region_targets['days_diff'] = abs(region_targets['days_to_departure'] - days_out)
        closest_target = region_targets.nsmallest(1, 'days_diff').iloc[0]
        target_pct = closest_target['target_percent_filled']
    else:
        target_pct = 50.0  # Default fallback
    
    pace_delta = sailing['current_occupancy_pct'] - target_pct
    
    pace_analysis.append({
        'sailing_id': sailing['sailing_id'],
        'itinerary_region': region,
        'departure_date': sailing['departure_date'],
        'capacity_cabins': sailing['capacity_cabins'],
        'days_until_departure': days_out,
        'current_occupancy_pct': sailing['current_occupancy_pct'],
        'target_occupancy_pct': round(target_pct, 1),
        'pace_delta': round(pace_delta, 1)
    })

pace_df = pd.DataFrame(pace_analysis)

print(f"\n✅ Pace analysis complete for {len(pace_df)} future sailings")
print("\n📊 Summary Statistics:")
print(f"Average Pace Delta: {pace_df['pace_delta'].mean():+.1f}%")
print(f"Sailings Ahead of Pace: {(pace_df['pace_delta'] > 0).sum()}")
print(f"Sailings Behind Pace: {(pace_df['pace_delta'] < 0).sum()}")

print("\n📊 Top 5 Sailings Ahead of Pace:")
print(pace_df.nlargest(5, 'pace_delta')[['sailing_id', 'itinerary_region', 'days_until_departure', 
                                           'current_occupancy_pct', 'pace_delta']])

print("\n📊 Top 5 Sailings Behind Pace:")
print(pace_df.nsmallest(5, 'pace_delta')[['sailing_id', 'itinerary_region', 'days_until_departure', 
                                            'current_occupancy_pct', 'pace_delta']])

# Save pace analysis
pace_df.to_csv("pace_analysis.csv", index=False)
print("\n✅ Saved: pace_analysis.csv")

print("\n" + "=" * 80)
print("EDA COMPLETE")
print("=" * 80)