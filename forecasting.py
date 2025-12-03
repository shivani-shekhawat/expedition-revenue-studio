import pandas as pd
import numpy as np
from datetime import datetime

print("=" * 80)
print("EXPEDITION REVENUE STUDIO: FORECASTING MODULE")
print("=" * 80)

# ============================================================================
# Load Data
# ============================================================================

sailings = pd.read_csv("sailings.csv")
bookings = pd.read_csv("bookings.csv")
pace_df = pd.read_csv("pace_analysis.csv")

sailings['departure_date'] = pd.to_datetime(sailings['departure_date'])
bookings['booking_date'] = pd.to_datetime(bookings['booking_date'])
pace_df['departure_date'] = pd.to_datetime(pace_df['departure_date'])

# Merge for full context
df = bookings.merge(sailings, on='sailing_id', how='left')

# Analysis date: In production, this would be datetime.now()
# For this project, using a fixed date to simulate "what would I see on Sept 1, 2025?"
ANALYSIS_DATE = datetime(2025, 9, 1)
print(f"\nForecasting from Analysis Date: {ANALYSIS_DATE.strftime('%Y-%m-%d')}")

# ============================================================================
# STEP 1: Build Historical Completion Ratios
# ============================================================================
# The core logic here: if a sailing was X% full at Y days out, what did it finish at?
# This ratio (final/current) becomes our forecasting multiplier.
# 
# Key assumption: bookings follow similar patterns within regions. Antarctica sailings
# that are 60% full at 120 days out tend to finish around the same final occupancy.
# This is simpler than time-series forecasting but captures the essential dynamic.

print("\n" + "-" * 80)
print("STEP 1: Building Historical Completion Ratios")
print("-" * 80)

historical_sailings = sailings[sailings['departure_date'] < ANALYSIS_DATE].copy()
print(f"\nHistorical sailings (already departed): {len(historical_sailings)}")

completion_ratios = []

# For each past sailing, calculate what % it was at different anchor points
# and what it ultimately achieved. This builds our "lookup table" for forecasting.
for _, sailing in historical_sailings.iterrows():
    sailing_id = sailing['sailing_id']
    capacity = sailing['capacity_cabins']
    region = sailing['itinerary_region']
    departure_date = sailing['departure_date']
    
    sailing_bookings = df[df['sailing_id'] == sailing_id].copy()
    
    if len(sailing_bookings) == 0:
        continue
    
    final_cabins_sold = len(sailing_bookings)
    final_occupancy_pct = (final_cabins_sold / capacity) * 100
    
    # Anchor points: standard checkpoints in the booking window
    # 180 days = ~6 months (common first look), 120 = 4 months, 90 = 3 months, etc.
    anchor_points = [180, 120, 90, 60, 30]
    
    for anchor_days in anchor_points:
        anchor_date = departure_date - pd.Timedelta(days=anchor_days)
        
        # How many bookings had we received by that anchor date?
        bookings_at_anchor = sailing_bookings[sailing_bookings['booking_date'] <= anchor_date]
        cabins_at_anchor = len(bookings_at_anchor)
        occupancy_at_anchor = (cabins_at_anchor / capacity) * 100
        
        # Completion ratio = where we ended up / where we were at anchor
        if occupancy_at_anchor > 0:
            completion_ratio = final_occupancy_pct / occupancy_at_anchor
        else:
            completion_ratio = None  # No bookings yet at this point
        
        completion_ratios.append({
            'sailing_id': sailing_id,
            'region': region,
            'departure_date': departure_date,
            'anchor_days_out': anchor_days,
            'occupancy_at_anchor': round(occupancy_at_anchor, 1),
            'final_occupancy': round(final_occupancy_pct, 1),
            'completion_ratio': round(completion_ratio, 3) if completion_ratio else None
        })

completion_df = pd.DataFrame(completion_ratios)
completion_df = completion_df.dropna(subset=['completion_ratio'])

print(f"✅ Calculated {len(completion_df)} completion ratio data points")

# Average completion ratios by region and anchor point
# This is the core forecasting lookup: "For Antarctica sailings at 120 days out,
# they typically grow by a factor of X before departure"
avg_completion = completion_df.groupby(['region', 'anchor_days_out']).agg({
    'completion_ratio': 'mean',
    'sailing_id': 'count'
}).reset_index()
avg_completion.columns = ['region', 'anchor_days_out', 'avg_completion_ratio', 'sample_size']
avg_completion = avg_completion.sort_values(['region', 'anchor_days_out'], ascending=[True, False])

print("\n📊 Average Completion Ratios by Region & Anchor Point:")
print(avg_completion.to_string(index=False))

# ============================================================================
# STEP 2: Apply Forecasts to Future Sailings
# ============================================================================
# Now we take current sailings and apply the appropriate completion ratio
# based on their region and how far out they are from departure.

print("\n" + "-" * 80)
print("STEP 2: Forecasting Future Sailings")
print("-" * 80)

future_sailings = sailings[sailings['departure_date'] >= ANALYSIS_DATE].copy()
print(f"\nFuture sailings to forecast: {len(future_sailings)}")

forecasts = []

for _, sailing in future_sailings.iterrows():
    sailing_id = sailing['sailing_id']
    capacity = sailing['capacity_cabins']
    region = sailing['itinerary_region']
    base_fare = sailing['base_fare_per_person']
    departure_date = sailing['departure_date']
    
    days_until_departure = (departure_date - ANALYSIS_DATE).days
    
    # Current bookings for this sailing
    sailing_bookings = df[
        (df['sailing_id'] == sailing_id) & 
        (df['booking_date'] <= ANALYSIS_DATE)
    ]
    
    current_cabins_sold = len(sailing_bookings)
    current_occupancy_pct = (current_cabins_sold / capacity) * 100
    
    # Find the most relevant completion ratio
    # Match to the closest anchor point we have data for
    anchor_options = [180, 120, 90, 60, 30]
    closest_anchor = min(anchor_options, key=lambda x: abs(x - days_until_departure))
    
    # Look up completion ratio for this region at this anchor point
    ratio_data = avg_completion[
        (avg_completion['region'] == region) & 
        (avg_completion['anchor_days_out'] == closest_anchor)
    ]
    
    if len(ratio_data) > 0:
        completion_ratio = ratio_data.iloc[0]['avg_completion_ratio']
    else:
        # Fallback: use any available ratio for this region
        region_ratios = avg_completion[avg_completion['region'] == region]
        if len(region_ratios) > 0:
            completion_ratio = region_ratios['avg_completion_ratio'].mean()
        else:
            # Conservative default if we have no data
            # Rationale: assume modest growth of 20%
            completion_ratio = 1.2

    # Project final occupancy
    # If sailing has bookings, apply the ratio. If no bookings yet, use regional average.
    if current_occupancy_pct > 0:
        projected_final_occupancy = current_occupancy_pct * completion_ratio
    else:
        # For sailings with zero bookings, fall back to regional average final occupancy
        regional_avg = completion_df[completion_df['region'] == region]['final_occupancy'].mean()
        projected_final_occupancy = regional_avg if not pd.isna(regional_avg) else 75.0
    
    # Cap at 100% (can't exceed capacity)
    projected_final_occupancy = min(projected_final_occupancy, 100.0)
    
    # Revenue calculations
    projected_cabins_sold = (projected_final_occupancy / 100) * capacity
    
    # Average fare: use actual average from current bookings, or estimate from base fare
    if len(sailing_bookings) > 0:
        avg_fare = sailing_bookings['fare_paid_per_person'].mean()
    else:
        # Assume some discounting: 5% off base fare on average
        avg_fare = base_fare * 0.95
    
    # Revenue = cabins * fare * 2 (assuming double occupancy)
    # In reality, this would vary by cabin type, but this is a reasonable approximation
    projected_revenue = projected_cabins_sold * avg_fare * 2
    
    # Target comparison: industry standard for expedition cruises is ~90% occupancy
    # (Leaving 10% buffer for last-minute cancellations, no-shows, repositioning needs)
    target_occupancy = 90.0
    projected_vs_target = projected_final_occupancy - target_occupancy
    
    # Competitor positioning: average competitor price index for this sailing
    if len(sailing_bookings) > 0:
        avg_competitor_idx = sailing_bookings['competitor_price_index'].mean()
    else:
        avg_competitor_idx = 1.0  # Neutral positioning
    
    forecasts.append({
        'sailing_id': sailing_id,
        'itinerary_region': region,
        'ship_name': sailing['ship_name'],
        'departure_date': departure_date,
        'days_until_departure': days_until_departure,
        'capacity_cabins': capacity,
        'current_cabins_sold': current_cabins_sold,
        'current_occupancy_pct': round(current_occupancy_pct, 1),
        'completion_ratio_used': round(completion_ratio, 3),
        'projected_final_occupancy_pct': round(projected_final_occupancy, 1),
        'projected_cabins_sold': round(projected_cabins_sold, 1),
        'avg_fare_per_person': round(avg_fare, 0),
        'projected_revenue': round(projected_revenue, 0),
        'target_occupancy_pct': target_occupancy,
        'projected_vs_target': round(projected_vs_target, 1),
        'competitor_price_index': round(avg_competitor_idx, 2)
    })

forecast_df = pd.DataFrame(forecasts)

print(f"✅ Forecasted {len(forecast_df)} future sailings")

print("\n📊 Forecast Summary Statistics:")
print(f"Average Current Occupancy: {forecast_df['current_occupancy_pct'].mean():.1f}%")
print(f"Average Projected Final Occupancy: {forecast_df['projected_final_occupancy_pct'].mean():.1f}%")
print(f"Total Projected Revenue: ${forecast_df['projected_revenue'].sum():,.0f}")

print("\n📊 Sailings by Projected Performance:")
print(f"Above Target (90%+): {(forecast_df['projected_final_occupancy_pct'] >= 90).sum()}")
print(f"On Target (80-90%): {((forecast_df['projected_final_occupancy_pct'] >= 80) & (forecast_df['projected_final_occupancy_pct'] < 90)).sum()}")
print(f"Below Target (<80%): {(forecast_df['projected_final_occupancy_pct'] < 80).sum()}")

print("\n📊 Top 5 Highest Projected Revenue Sailings:")
print(forecast_df.nlargest(5, 'projected_revenue')[
    ['sailing_id', 'itinerary_region', 'projected_final_occupancy_pct', 'projected_revenue']
])

print("\n📊 Top 5 Lowest Projected Occupancy Sailings:")
print(forecast_df.nsmallest(5, 'projected_final_occupancy_pct')[
    ['sailing_id', 'itinerary_region', 'days_until_departure', 'current_occupancy_pct', 'projected_final_occupancy_pct']
])

# Save forecast
forecast_df.to_csv("revenue_forecast.csv", index=False)
print("\n✅ Saved: revenue_forecast.csv")

print("\n" + "=" * 80)
print("FORECASTING COMPLETE")
print("=" * 80)