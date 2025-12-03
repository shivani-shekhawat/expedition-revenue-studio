import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

print("Generating Expedition Cruise Revenue Management Dataset...")

# ============================================================================
# PART 1: Generate Sailings
# ============================================================================

ships = ["Explorer", "Endeavour", "Venture", "Resolution"]

# Define regions with their characteristics
regions_config = {
    "Antarctica": {
        "itineraries": ["Antarctica Classic 10D", "Antarctica Explorer 12D", "Falklands & South Georgia 14D"],
        "season_start": datetime(2025, 11, 1),
        "season_end": datetime(2026, 3, 15),
        "base_fare_range": (8000, 15000),
        "capacity_range": (60, 100),
        "avg_booking_lead": 240  # days
    },
    "Galápagos": {
        "itineraries": ["Galápagos Outer Loop 7D", "Galápagos Complete 10D"],
        "season_start": datetime(2025, 6, 1),
        "season_end": datetime(2026, 5, 31),
        "base_fare_range": (5000, 9000),
        "capacity_range": (80, 120),
        "avg_booking_lead": 180
    },
    "Arctic": {
        "itineraries": ["Svalbard Explorer 8D", "Iceland & Greenland 12D", "Norwegian Fjords 10D"],
        "season_start": datetime(2025, 6, 1),
        "season_end": datetime(2025, 9, 15),
        "base_fare_range": (6000, 11000),
        "capacity_range": (70, 110),
        "avg_booking_lead": 200
    },
    "Alaska": {
        "itineraries": ["Inside Passage 7D", "Glacier Bay & Islands 10D"],
        "season_start": datetime(2025, 5, 1),
        "season_end": datetime(2025, 9, 30),
        "base_fare_range": (4000, 7500),
        "capacity_range": (50, 90),
        "avg_booking_lead": 120
    }
}

sailings_list = []
sailing_id_counter = 1

# Generate sailings for each region
for region, config in regions_config.items():
    season_days = (config["season_end"] - config["season_start"]).days
    num_sailings = random.randint(10, 18)  # Varying number of sailings per region
    
    for i in range(num_sailings):
        departure_date = config["season_start"] + timedelta(
            days=random.randint(0, season_days)
        )
        
        itinerary = random.choice(config["itineraries"])
        duration = int(itinerary.split()[-1].replace("D", ""))
        
        sailings_list.append({
            "sailing_id": f"S{sailing_id_counter:03d}",
            "ship_name": random.choice(ships),
            "itinerary_region": region,
            "itinerary_name": itinerary,
            "departure_date": departure_date,
            "duration_days": duration,
            "capacity_cabins": random.randint(*config["capacity_range"]),
            "cabin_mix_class": random.choice(["luxury-heavy", "balanced", "economy-mix"]),
            "base_fare_per_person": random.randint(*config["base_fare_range"])
        })
        sailing_id_counter += 1

sailings_df = pd.DataFrame(sailings_list)
sailings_df = sailings_df.sort_values("departure_date").reset_index(drop=True)

print(f"Generated {len(sailings_df)} sailings across {len(regions_config)} regions")

# ============================================================================
# PART 2: Generate Bookings with Realistic Booking Curves
# ============================================================================

bookings_list = []
booking_id_counter = 1

for idx, sailing in sailings_df.iterrows():
    region = sailing["itinerary_region"]
    config = regions_config[region]
    capacity = sailing["capacity_cabins"]
    base_fare = sailing["base_fare_per_person"]
    departure_date = sailing["departure_date"]
    
    # Determine target occupancy with some variation
    target_occupancy = random.uniform(0.75, 0.95)
    target_bookings = int(capacity * target_occupancy)
    
    # Create booking curve based on region characteristics
    # Different regions have different booking patterns
    if region == "Antarctica":
        # Strong early booking pattern
        early_weight = 0.50  # 50% of bookings 300-180 days out
        mid_weight = 0.35    # 35% of bookings 180-60 days out
        late_weight = 0.15   # 15% of bookings 60-0 days out
    elif region == "Galápagos":
        # Balanced booking pattern
        early_weight = 0.40
        mid_weight = 0.40
        late_weight = 0.20
    elif region == "Arctic":
        # Moderate early booking
        early_weight = 0.45
        mid_weight = 0.35
        late_weight = 0.20
    else:  # Alaska
        # More last-minute bookings
        early_weight = 0.30
        mid_weight = 0.40
        late_weight = 0.30
    
    # Generate bookings across timeframes
    early_bookings = int(target_bookings * early_weight)
    mid_bookings = int(target_bookings * mid_weight)
    late_bookings = target_bookings - early_bookings - mid_bookings
    
    # Create booking events
    all_booking_days = []
    
    # Early bookings (300-180 days before)
    for _ in range(early_bookings):
        days_out = random.randint(180, 300)
        all_booking_days.append(days_out)
    
    # Mid bookings (180-60 days before)
    for _ in range(mid_bookings):
        days_out = random.randint(60, 180)
        all_booking_days.append(days_out)
    
    # Late bookings (60-0 days before)
    for _ in range(late_bookings):
        days_out = random.randint(0, 60)
        all_booking_days.append(days_out)
    
    # Generate actual booking records
    for days_to_departure in all_booking_days:
        booking_date = departure_date - timedelta(days=days_to_departure)
        
        # Skip bookings in the future
        if booking_date > datetime.now():
            continue
        
        # Determine if discount applied (more likely for last-minute)
        discount_prob = 0.15 if days_to_departure > 90 else 0.35
        discount_flag = 1 if random.random() < discount_prob else 0
        
        # Calculate fare paid
        if discount_flag:
            discount_pct = random.uniform(0.10, 0.25)
            fare_paid = base_fare * (1 - discount_pct)
        else:
            # Some random variation even without discount
            fare_paid = base_fare * random.uniform(0.95, 1.05)
        
        # Determine price version (simulate repricing events)
        if days_to_departure > 180:
            price_version = "P1"
        elif days_to_departure > 90:
            price_version = random.choice(["P1", "P2"])
        else:
            price_version = random.choice(["P2", "P3"])
        
        # Competitor price index (varies by time and region)
        # Lower index = competitors are cheaper, higher = we're cheaper
        base_competitor_idx = 1.0
        if region == "Antarctica":
            base_competitor_idx = 1.05  # We're premium
        elif region == "Alaska":
            base_competitor_idx = 0.98  # More competitive market
        
        competitor_price_index = base_competitor_idx + random.uniform(-0.15, 0.15)
        
        # Booking segment
        if days_to_departure > 180:
            segment = random.choice(["early_planner", "early_planner", "loyal_guest"])
        elif days_to_departure > 60:
            segment = random.choice(["early_planner", "mid_booker", "mid_booker"])
        else:
            segment = random.choice(["last_minute", "last_minute", "mid_booker"])
        
        bookings_list.append({
            "booking_id": f"B{booking_id_counter:05d}",
            "sailing_id": sailing["sailing_id"],
            "booking_date": booking_date,
            "days_to_departure": days_to_departure,
            "channel": random.choice(["direct", "direct", "web", "travel_agent"]),
            "party_size": random.choice([1, 2, 2, 2, 3, 4]),
            "fare_paid_per_person": round(fare_paid, 2),
            "discount_flag": discount_flag,
            "price_version": price_version,
            "competitor_price_index": round(competitor_price_index, 2),
            "booking_segment": segment
        })
        booking_id_counter += 1

bookings_df = pd.DataFrame(bookings_list)

print(f"Generated {len(bookings_df)} booking events")

# ============================================================================
# PART 3: Save to CSV
# ============================================================================

sailings_df.to_csv("sailings.csv", index=False)
bookings_df.to_csv("bookings.csv", index=False)

print("\n✅ Data generation complete!")
print(f"   - sailings.csv: {len(sailings_df)} rows")
print(f"   - bookings.csv: {len(bookings_df)} rows")
print("\nSample Sailings by Region:")
print(sailings_df.groupby("itinerary_region").size())