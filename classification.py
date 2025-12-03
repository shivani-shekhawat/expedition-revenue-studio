import pandas as pd
import numpy as np

print("=" * 80)
print("EXPEDITION REVENUE STUDIO: RISK & OPPORTUNITY CLASSIFICATION")
print("=" * 80)

# ============================================================================
# Load Forecast Data
# ============================================================================

forecast_df = pd.read_csv("revenue_forecast.csv")
forecast_df['departure_date'] = pd.to_datetime(forecast_df['departure_date'])

print(f"\n✅ Loaded {len(forecast_df)} sailing forecasts")

# ============================================================================
# Define Classification Logic
# ============================================================================
# The goal here is to bucket sailings into actionable categories that drive
# different revenue management strategies. This isn't about perfect prediction—
# it's about identifying which sailings need attention and what type of action.
#
# In real cruise RM, you'd have more sophisticated scoring (incorporating 
# group holds, wave periods, competitive set analysis), but this framework
# captures the essential decision tree.

print("\n" + "-" * 80)
print("Classification Rules")
print("-" * 80)

# Thresholds are based on what I've read about expedition cruise operators:
# - 5% variance is meaningful but not alarming
# - Beyond that, it signals need for intervention
# These would be tuned based on historical save rates and revenue impact
OVERPERFORM_THRESHOLD = 5.0  # 5% above target = pricing opportunity
AT_RISK_THRESHOLD = -5.0      # 5% below target = stimulation needed

print(f"• Overperforming: Projected occupancy > Target + {OVERPERFORM_THRESHOLD}%")
print(f"• At Risk: Projected occupancy < Target + {AT_RISK_THRESHOLD}%")
print(f"• On Track: Everything else")

# ============================================================================
# Classify Sailings & Generate Recommendations
# ============================================================================
# This is where the business logic lives. Each classification drives a different
# playbook. The recommendations consider:
# 1. Time to departure (urgency)
# 2. Competitive positioning (are we priced wrong?)
# 3. Current performance vs projection (how much intervention needed?)

classifications = []

for _, sailing in forecast_df.iterrows():
    sailing_id = sailing['sailing_id']
    region = sailing['itinerary_region']
    days_until = sailing['days_until_departure']
    current_occ = sailing['current_occupancy_pct']
    projected_occ = sailing['projected_final_occupancy_pct']
    target_occ = sailing['target_occupancy_pct']
    competitor_idx = sailing['competitor_price_index']
    projected_vs_target = sailing['projected_vs_target']
    
    # Status determination
    if projected_vs_target > OVERPERFORM_THRESHOLD:
        status = "Overperforming"
        status_category = "opportunity"
    elif projected_vs_target < AT_RISK_THRESHOLD:
        status = "At Risk"
        status_category = "risk"
    else:
        status = "On Track"
        status_category = "monitor"
    
    # ========================================================================
    # Generate Recommendations
    # ========================================================================
    # These recommendations reflect actual cruise RM tactics I researched:
    # - Price increases when demand exceeds supply
    # - Targeted promotions (not blanket discounts) when pace lags
    # - Channel-specific strategies (agents vs direct)
    # - Urgency actions when close to departure
    
    actions = []
    
    if status == "Overperforming":
        # SCENARIO: Strong demand, projected to exceed target
        # STRATEGY: Revenue optimization through dynamic pricing
        
        if competitor_idx > 1.05:
            # We're already cheaper than competitors AND selling well
            # This is prime pricing power territory
            actions.append("Increase price 8-12% for remaining inventory")
            actions.append("Consider closed-to-arrival restrictions for lowest categories")
        else:
            # Competitive market but strong demand - moderate increase
            actions.append("Increase price 3-5% for remaining inventory")
        
        if days_until > 90:
            # Far out sailings: opportunity to capture group business at premium
            actions.append("Explore charter/group opportunities at premium rates")
        
        if projected_occ > 95:
            # Near sell-out: implement scarcity pricing
            actions.append("Activate premium pricing tier for final cabins")
            actions.append("Consider waitlist protocol")
    
    elif status == "At Risk":
        # SCENARIO: Weak demand, projected to miss target
        # STRATEGY: Stimulation to recover pace, but diagnosing root cause first
        
        # Root cause analysis: is this a pricing issue or demand issue?
        if competitor_idx < 0.95:
            # Competitors are 5%+ cheaper - we have a price problem
            price_gap = (1 - competitor_idx) * 100
            actions.append(f"⚠️ Pricing misalignment: competitors {price_gap:.0f}% cheaper")
            actions.append("Recommend targeted price reduction (10-15%) on mid-tier cabins")
            actions.append("Audit competitive set pricing weekly")
        else:
            # Price isn't the issue - likely awareness or value perception
            actions.append("Increase marketing spend: digital + email remarketing")
            actions.append("Activate past guest outreach with limited-time incentive")
        
        # Time-based escalation
        if days_until < 90:
            # Inside 90 days: urgency mode
            actions.append("Launch flash sale: 15-20% off select categories (48-72hr window)")
            actions.append("Engage travel agent partners with override commission")
        
        if days_until < 60:
            # Inside 60 days: critical intervention
            actions.append("Coordinate with sales team for direct outreach to qualified leads")
            actions.append("Consider bundled value-adds (pre/post hotel, excursions) vs straight discount")
        
        if current_occ < 50 and days_until < 120:
            # Red flag: less than half full with <4 months to go
            actions.append("🚨 CRITICAL: Evaluate sailing viability vs consolidation")
            actions.append("Prepare passenger communication plan if itinerary change needed")
    
    else:  # On Track
        # SCENARIO: Performing as expected
        # STRATEGY: Monitoring with readiness to act if pace shifts
        
        actions.append("Monitor pace weekly against forecast")
        
        if days_until > 120:
            actions.append("Maintain current pricing strategy")
            actions.append("Focus on awareness-building and early booker campaigns")
        elif days_until > 60:
            actions.append("Prepare shoulder-season promotional offers")
            actions.append("Review cabin mix availability for targeted marketing")
        else:
            actions.append("Activate final push: 'Last Chance' messaging")
            actions.append("Leverage scarcity messaging in marketing creative")
        
        # Competitive monitoring is always important
        if competitor_idx < 1.0:
            actions.append("Note: Competitors priced lower - monitor for pace impact")
    
    # Combine all recommendations
    recommended_action = " | ".join(actions)
    
    classifications.append({
        'sailing_id': sailing_id,
        'itinerary_region': region,
        'ship_name': sailing['ship_name'],
        'departure_date': sailing['departure_date'],
        'days_until_departure': days_until,
        'capacity_cabins': sailing['capacity_cabins'],
        'current_occupancy_pct': current_occ,
        'projected_final_occupancy_pct': projected_occ,
        'target_occupancy_pct': target_occ,
        'projected_vs_target': projected_vs_target,
        'competitor_price_index': competitor_idx,
        'status': status,
        'status_category': status_category,
        'recommended_action': recommended_action
    })

classification_df = pd.DataFrame(classifications)

# ============================================================================
# Display Results
# ============================================================================

print("\n" + "=" * 80)
print("CLASSIFICATION RESULTS")
print("=" * 80)

# Summary by status
print("\n📊 Sailings by Status:")
status_summary = classification_df.groupby('status').agg({
    'sailing_id': 'count',
    'projected_final_occupancy_pct': 'mean'
}).round(1)
status_summary.columns = ['Count', 'Avg Projected Occupancy']
print(status_summary)

# Status by region
print("\n📊 Status Distribution by Region:")
region_status = pd.crosstab(
    classification_df['itinerary_region'],
    classification_df['status']
)
print(region_status)

# At-risk sailings (highest priority for action)
print("\n🚨 AT RISK SAILINGS (Require Immediate Action):")
at_risk = classification_df[classification_df['status'] == 'At Risk'].sort_values(
    'projected_final_occupancy_pct'
)
print(at_risk[['sailing_id', 'itinerary_region', 'days_until_departure', 
                'current_occupancy_pct', 'projected_final_occupancy_pct', 
                'competitor_price_index']].to_string(index=False))

if len(at_risk) > 0:
    print("\n🎯 Recommended Actions for At-Risk Sailings:")
    for _, row in at_risk.iterrows():
        print(f"\n{row['sailing_id']} ({row['itinerary_region']}) - Departs in {row['days_until_departure']} days:")
        print(f"  Current: {row['current_occupancy_pct']:.1f}% | Projected: {row['projected_final_occupancy_pct']:.1f}%")
        print(f"  {row['recommended_action']}")

# Overperforming sailings (revenue optimization opportunities)
print("\n🎉 OVERPERFORMING SAILINGS (Revenue Optimization Opportunities):")
overperform = classification_df[classification_df['status'] == 'Overperforming'].sort_values(
    'projected_final_occupancy_pct', ascending=False
)
print(overperform[['sailing_id', 'itinerary_region', 'days_until_departure', 
                    'current_occupancy_pct', 'projected_final_occupancy_pct']].to_string(index=False))

if len(overperform) > 0:
    print("\n💰 Recommended Actions for Overperforming Sailings:")
    for _, row in overperform.iterrows():
        print(f"\n{row['sailing_id']} ({row['itinerary_region']}) - Departs in {row['days_until_departure']} days:")
        print(f"  Current: {row['current_occupancy_pct']:.1f}% | Projected: {row['projected_final_occupancy_pct']:.1f}%")
        print(f"  {row['recommended_action']}")

# ============================================================================
# Revenue Impact Analysis
# ============================================================================
# Quantifying the financial stakes helps prioritize which sailings need
# immediate attention and justifies the time investment in intervention.

print("\n" + "=" * 80)
print("REVENUE IMPACT ANALYSIS")
print("=" * 80)

# At-risk revenue exposure
# This is the revenue we're leaving on the table if these sailings don't recover
at_risk_revenue_gap = 0
if len(at_risk) > 0:
    for _, row in at_risk.iterrows():
        occupancy_gap = (row['target_occupancy_pct'] - row['projected_final_occupancy_pct']) / 100
        cabins_gap = occupancy_gap * row['capacity_cabins']
        # Assuming average fare of $8k per person, double occupancy
        revenue_at_risk = cabins_gap * 8000 * 2
        at_risk_revenue_gap += revenue_at_risk

# Overperforming revenue opportunity
# This is incremental revenue from dynamic pricing on strong-demand sailings
overperform_revenue_opportunity = 0
if len(overperform) > 0:
    for _, row in overperform.iterrows():
        # Remaining inventory
        remaining_pct = (100 - row['current_occupancy_pct']) / 100
        remaining_cabins = remaining_pct * row['capacity_cabins']
        # Conservative 5% price increase on remaining inventory
        incremental_revenue = remaining_cabins * 8000 * 0.05 * 2
        overperform_revenue_opportunity += incremental_revenue

print(f"\n💰 Potential Revenue at Risk: ${at_risk_revenue_gap:,.0f}")
print(f"   ({len(at_risk)} sailings projected to miss target)")
print(f"   Action required: Stimulation campaigns to close occupancy gap")

print(f"\n💰 Potential Additional Revenue: ${overperform_revenue_opportunity:,.0f}")
print(f"   ({len(overperform)} sailings with pricing power)")
print(f"   Action required: Dynamic pricing on remaining inventory")

print(f"\n💰 Total Revenue Opportunity: ${(at_risk_revenue_gap + overperform_revenue_opportunity):,.0f}")
print(f"   Combined impact of addressing both at-risk and overperforming sailings")

# Save classification results
classification_df.to_csv("sailing_classification.csv", index=False)
print("\n✅ Saved: sailing_classification.csv")

print("\n" + "=" * 80)
print("CLASSIFICATION COMPLETE")
print("=" * 80)