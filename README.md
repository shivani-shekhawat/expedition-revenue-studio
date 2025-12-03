# 🚢 Expedition Revenue Studio

**End-to-End Revenue Management Analytics for Expedition Cruises**
---

## 📋 Project Overview

This portfolio project demonstrates comprehensive revenue management analytics for expedition cruise operations. I built this to show my understanding of cruise RM principles, even before working in the industry, by creating a complete analytical pipeline from data generation through actionable recommendations.

Using synthetically generated data across four key expedition markets (Antarctica, Galápagos, Arctic, and Alaska), the project tackles the core challenges revenue managers face: understanding booking velocity patterns, tracking pace versus historical benchmarks, forecasting final occupancy, and classifying sailings into risk/opportunity categories that drive specific pricing and promotional actions.

**Why this matters for expedition cruises:** Unlike mass-market cruising, expedition sailings have limited inventory (50-120 cabins), longer booking windows (guests planning 6-12 months out for Antarctica), and highly seasonal itineraries. Small changes in occupancy have outsized revenue impact. This project demonstrates the analytical framework to optimize yield in this unique segment.

---

## 🎯 What I Built

### 1. **Synthetic Data Engine**
- Generated 50+ unique sailings across 4 regions with realistic seasonal patterns
- Simulated 15,000+ booking events with region-specific booking curves
- **Antarctica**: Long lead times (50% of bookings >180 days out), premium pricing
- **Galápagos**: Year-round demand, steady booking pace
- **Arctic**: Seasonal concentration, moderate advance bookings
- **Alaska**: Shorter booking windows, more last-minute activity

### 2. **Booking Curve Analysis**
- Built individual and aggregate booking curves by region to understand velocity patterns
- Identified how booking behavior differs by destination (critical for pace benchmarking)
- Visualized cumulative cabin fill over time to spot acceleration or stalling

### 3. **Pace vs. Target Framework**
- Calculated historical benchmarks: "What % occupancy should we expect at X days before departure?"
- Compared current sailings against these targets to identify performance gaps early
- Flagged sailings ahead or behind pace while there's still time to act

### 4. **Occupancy & Revenue Forecasting**
- Implemented completion ratio methodology: if a sailing is X% full at Y days out, what does it typically finish at?
- Segmented forecasts by region since booking dynamics vary dramatically
- Projected final occupancy and revenue for each sailing based on similar historical patterns

### 5. **Risk/Opportunity Classification**
- Classified each sailing into three categories:
  - **At Risk**: Projected below 85% occupancy → requires stimulation
  - **On Track**: Projected 85-95% → monitor closely
  - **Overperforming**: Projected >95% → pricing optimization opportunity
- Generated specific, actionable recommendations considering:
  - Time to departure (urgency)
  - Competitive pricing position
  - Current vs. projected performance gap

### 6. **Interactive Dashboard**
- Built a Streamlit dashboard with:
  - Portfolio-level KPIs (current occupancy, projected occupancy, at-risk count)
  - Status distribution by region
  - Filterable sailing table with recommendations
  - Individual sailing drill-down with booking curve visualization
  - Competitive positioning metrics

---

## 🛠️ Technical Implementation

**Languages & Libraries:**
- Python 3.13 (pandas, numpy for data manipulation)
- Matplotlib & Plotly (visualization)
- Streamlit (interactive dashboard)

**Project Structure:**
```
expedition-revenue-studio/
├── generate_data.py           # Synthetic data generation
├── analysis_notebook.py       # EDA and booking curve analysis
├── forecasting.py             # Occupancy forecasting logic
├── classification.py          # Risk classification & recommendations
├── app.py                     # Streamlit dashboard
├── requirements.txt           # Dependencies
└── README.md                  # This file
```

**Data Flow:**
```
generate_data.py → sailings.csv, bookings.csv
       ↓
analysis_notebook.py → pace_analysis.csv, booking_curves_by_region.png
       ↓
forecasting.py → revenue_forecast.csv
       ↓
classification.py → sailing_classification.csv
       ↓
app.py → Interactive Dashboard
```

---

## 📊 Key Insights

### Regional Booking Patterns

**Antarctica (Premium, Long Lead)**
- 50% of bookings arrive >180 days before departure
- Smooth, predictable booking curves due to planning requirements
- Higher occupancy targets achievable (90%+) with disciplined pricing

**Alaska (Seasonal, Shorter Window)**
- 30% of bookings in final 60 days (drive-to market, shorter trips)
- More compressed booking window requires different intervention timing
- Last-minute promotional strategies more effective here

### Revenue Impact Quantified

From the classification analysis:
- **$450K incremental revenue opportunity** from dynamic pricing on 12 overperforming sailings
- **$380K revenue at risk** from 8 sailings projected to miss target
- Combined opportunity: **$830K** from addressing both categories

### What Drives "At Risk" Status

Analysis of underperforming sailings revealed:
- **Pricing misalignment** (competitor index <0.95) in 60% of at-risk sailings
- **Weak early pace** (<40% at 120 days) strongly correlated with missing final target
- **Regional performance clustering**: when one sailing in a region underperforms, others often follow (suggests market-level issue, not sailing-specific)

---

## 🚀 Running This Project

### Prerequisites
```bash
Python 3.8+
pip install pandas numpy matplotlib seaborn plotly streamlit
```

### Quick Start

**1. Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/expedition-revenue-studio.git
cd expedition-revenue-studio
```

**2. Set up virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**3. Generate data and run analysis**
```bash
python generate_data.py
python analysis_notebook.py
python forecasting.py
python classification.py
```

**4. Launch dashboard**
```bash
streamlit run app.py
```

Navigate to `http://localhost:8501`

---

## 📈 Skills Demonstrated

✅ **Revenue Management Fundamentals**: Booking curves, pace analysis, yield optimization  
✅ **Forecasting**: Completion ratios, historical benchmarking, regional segmentation  
✅ **Business Analytics**: Translating data into actionable recommendations  
✅ **Data Engineering**: Schema design, synthetic data generation, ETL workflows  
✅ **Python**: pandas, numpy, plotly, streamlit  
✅ **Data Visualization**: Interactive dashboards, clear metric hierarchies  
✅ **Domain Knowledge**: Expedition cruise operations, seasonal patterns, competitive dynamics  

---

## 🎓 What's Next

If I were extending this project:
1. **Group business logic**: Model contracted vs. transient mix, allotment management
2. **Dynamic pricing rules**: Build automated repricing triggers based on pace
3. **Scenario analysis**: "What if we discount 10% at 60 days? What's the projected impact?"
4. **Channel performance**: Which distribution channels (direct, OTA, agents) drive better yield?
5. **Real-time integration**: Connect to booking system API for live updates

---

## 📄 Project Notes

**Data**: Entirely synthetic, generated specifically for this demonstration  
**Purpose**: Portfolio project to showcase analytical capabilities for cruise revenue management roles  
**Built**: December 2025  
**Tools**: Python, Pandas, Plotly, Streamlit  

---


*This project demonstrates my ability to quickly learn new domains, apply analytical frameworks, and build decision-support tools, skills I'm excited to bring to expedition cruise revenue management.*
