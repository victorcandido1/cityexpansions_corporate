# Complete Methodology - GeoEco City Ranking Analysis

**Last Updated:** December 8, 2025  
**Version:** 2.0 (December 2025 Update)

---

## Table of Contents

1. [Overview](#overview)
2. [Data Sources](#data-sources)
3. [Household Wealth Score (Geometric Score)](#household-wealth-score)
4. [Corporate Power Score](#corporate-power-score)
5. [Final Integrated City Ranking](#final-integrated-city-ranking)
6. [Premium Flight Analysis](#premium-flight-analysis)
7. [Results Summary](#results-summary)

---

## 1. Overview

This analysis provides a comprehensive ranking of 7 major U.S. metropolitan areas for helicopter transportation services, combining:

- **Household Wealth Analysis** (IRS & Census data)
- **Corporate Power Analysis** (Census Bureau business data)
- **Infrastructure Assessment** (FAA airport data)
- **Geographic Clustering** (K-means spatial analysis)
- **Premium Flight Patterns** (FlightRadar24 data)

**Geographic Coverage:** Los Angeles, New York, Chicago, Dallas, Houston, Miami, San Francisco

---

## 2. Data Sources

### 2.1 Primary Data Sources

| Source | Type | Coverage | Status |
|--------|------|----------|--------|
| **IRS SOI 2022** | Tax returns, AGI | All ZIP codes | 100% Real |
| **Census ACS 2022** | Demographics, income | All ZCTAs | 100% Real |
| **Census CBP 2021** | Business establishments, employment, payroll | 30,917 ZIPs | 100% Real |
| **Google Distance Matrix API** | Travel times | As needed | Real-time |
| **FAA Airport Data** | Airports, heliports | 19,768 facilities | 100% Real |
| **FlightRadar24** | Premium flights | 3.1M+ flights | Real data |

### 2.2 Estimated Data

- **Revenue:** Estimated using BLS revenue-per-employee ratios (not directly available from Census)
- **Employment by Industry:** Proportionally estimated when Census suppresses data for privacy

---

## 3. Household Wealth Score (Geometric Score)

### 3.1 Formula

```
Geometric_Score = (IRS_Norm^0.50) × (Time²^0.20) × (Pop200k_Norm^0.20) × (Density_Norm^0.10)
```

### 3.2 Components

| Component | Weight | Description | Source |
|-----------|--------|-------------|--------|
| **IRS_Norm** | 50% | Normalized AGI per return (wealth quality) | IRS SOI 2022 |
| **Time_Squared** | 20% | Travel time to airport² (exclusivity) | Google API |
| **Pop200k_Norm** | 20% | Number of households earning $200k+ | Census ACS 2022 |
| **Density_Norm** | 10% | HH $200k+ per km² (concentration) | Calculated |

### 3.3 Normalization

All variables normalized to [0,1] scale using **global bounds** (across all 7 cities):

```
Normalized_Value = (Value - Min_Global) / (Max_Global - Min_Global)
```

### 3.4 Top 10% Selection

- **Threshold:** 90th percentile of Geometric_Score
- **Result:** 272 ZIP codes (out of 2,716 total)
- **Distribution:**
  - New York: 132 ZIPs
  - Los Angeles: 46 ZIPs
  - Houston: 28 ZIPs
  - San Francisco: 23 ZIPs
  - Chicago: 20 ZIPs
  - Dallas: 17 ZIPs
  - Miami: 6 ZIPs

### 3.5 Rationale

The **50% weight on IRS wealth** captures individual/household affluence, while **20% on volume** (Pop200k) ensures sufficient market size. The **20% travel time** component identifies exclusive, secluded areas away from high-traffic zones.

---

## 4. Corporate Power Score

### 4.1 Formula (Updated December 2025)

```
Corporate_Score = (Revenue_Norm^0.30) × (Employment_Norm^0.25) × (RevPerEmp_Norm^0.15) × (PowerShare_Norm^0.10) × (Time²^0.20)
```

### 4.2 Components

| Component | Weight | Description | Measures |
|-----------|--------|-------------|----------|
| **Revenue_Norm** | 30% | Total estimated revenue ($M) | Volume |
| **Employment_Norm** | 25% | Total employment | Volume |
| **RevPerEmp_Norm** | 15% | Revenue per employee | **Productivity/Quality** 🆕 |
| **PowerShare_Norm** | 10% | % employment in power industries | Quality |
| **Time_Squared** | 20% | Travel time to airport² | Exclusivity |

### 4.3 Revenue per Employee Calculation

```
Revenue_per_Employee = (Estimated_Revenue_M × 1,000,000) / Total_Employment
```

**Why this matters:** Captures productivity and business quality. A ZIP with high-value tech companies (e.g., $500k/employee) scores higher than one with many low-wage retail jobs (e.g., $100k/employee), even with similar employment totals.

### 4.4 Power Industries

Power industries (NAICS codes with high-value workers):
- **51** - Information/Technology
- **52** - Finance/Insurance
- **53** - Real Estate
- **54** - Professional Services
- **55** - Management/Holdings
- **71** - Entertainment/Arts

### 4.5 Top 10% Selection

- **Threshold:** 90th percentile of Corporate_Score
- **Result:** 321 ZIP codes (out of 3,204 active ZIPs)
- **Distribution (Updated):**
  - Los Angeles: 110 ZIPs
  - Miami: 55 ZIPs
  - New York: 45 ZIPs
  - Chicago: 38 ZIPs
  - San Francisco: 34 ZIPs
  - Dallas: 20 ZIPs
  - Houston: 19 ZIPs

### 4.6 Changes from Previous Version

**Before (November 2025):**
```
Corporate_Score = Revenue^0.35 × Employment^0.30 × PowerShare^0.15 × Time²^0.20
```

**After (December 2025):**
```
Corporate_Score = Revenue^0.30 × Employment^0.25 × RevPerEmp^0.15 × PowerShare^0.10 × Time²^0.20
```

**Impact:** Now prioritizes **high-productivity** zones, not just high-volume. San Francisco and New York benefit from this change due to their tech/finance sectors with high revenue per employee.

---

## 5. Final Integrated City Ranking

### 5.1 Formula

```
Final_Score = 0.25×HH_Quality + 0.15×HH_Volume + 0.25×Corp_Quality + 0.15×Corp_Volume + 0.10×Intersection + 0.10×Infrastructure
```

### 5.2 Components (All Normalized to 0-100 Scale)

| Component | Weight | Metric | Description |
|-----------|--------|--------|-------------|
| **HH Quality** | 25% | Median Geometric Score | Quality of household wealth |
| **HH Volume** | 15% | Total HH $200k+ | Number of wealthy households |
| **Corp Quality** | 25% | Median Corporate Score | Productivity & quality |
| **Corp Volume** | 15% | Total Employment | Size of corporate base |
| **Intersection** | 10% | # ZIPs in both Top 10% | HH-Corp overlap |
| **Infrastructure** | 10% | Airports×2 + Heliports | Aviation facilities |

### 5.3 Normalization Process

Each component normalized before weighting:

```python
Normalized_Component = ((Value - Min) / (Max - Min)) × 100
```

This ensures all components contribute equally despite different scales (e.g., thousands of households vs. number of airports).

### 5.4 Infrastructure Score Calculation

```
Infrastructure_Score = (Number_of_Airports × 2) + Number_of_Heliports
```

Airports weighted 2× heliports because they represent larger-scale infrastructure and serve as anchors for helicopter operations.

---

## 6. Premium Flight Analysis

### 6.1 Data Processing

**Source:** FlightRadar24 data for 6 major airports  
**Volume:** 3,135,856 premium flights analyzed

**Premium Flight Criteria:**
1. **Widebody aircraft only:**
   - Boeing: 747, 767, 777, 787
   - Airbus: A330, A340, A350, A380
   - McDonnell Douglas: MD-11, DC-10
2. **Flight duration:** Minimum 5 hours (long-haul/international)
3. **Premium seats:** First Class + Business + Premium Economy

### 6.2 Local Time Conversion

**All timestamps converted from UTC to local airport timezone:**

| Airport | Timezone | UTC Offset |
|---------|----------|------------|
| **KJFK** (New York) | America/New_York | UTC-5 (EST) / UTC-4 (EDT) |
| **KLAX** (Los Angeles) | America/Los_Angeles | UTC-8 (PST) / UTC-7 (PDT) |
| **KORD** (Chicago) | America/Chicago | UTC-6 (CST) / UTC-5 (CDT) |
| **KDFW** (Dallas) | America/Chicago | UTC-6 (CST) / UTC-5 (CDT) |
| **KSFO** (San Francisco) | America/Los_Angeles | UTC-8 (PST) / UTC-7 (PDT) |
| **KIAH** (Houston) | America/Chicago | UTC-6 (CST) / UTC-5 (CDT) |

### 6.3 Heatmap Methodology

**Grid Structure:**
- **X-Axis:** Hours of day (00:00 - 23:00, local time)
- **Y-Axis:** Days of week (Monday - Sunday)
- **Values:** Average premium seats per (day, hour) combination
- **Separation:** DEPARTURES and ARRIVALS shown side-by-side

**Calculation:**
```
Avg_Premium_Seats(day, hour) = Mean(Premium_Seats) across all occurrences of that (day, hour)
```

**Purpose:** Identify temporal patterns in premium flight demand to optimize helicopter service scheduling.

---

## 7. Results Summary

### 7.1 Final City Ranking

| Rank | City | Final Score | Key Strengths |
|:----:|------|:-----------:|---------------|
| 🥇 **1** | **New York** | **72.1** | Balanced excellence across all metrics |
| 🥈 **2** | **Los Angeles** | **58.5** | Largest volume: $799B revenue, 3.4M employees, 50 heliports |
| 🥉 **3** | **Chicago** | **37.4** | Highest household score (13.67%), 95% overlap |
| 4 | Miami | 35.4 | 100% household-corporate overlap |
| 5 | Houston | 29.6 | Best infrastructure: 69 facilities |
| 6 | San Francisco | 28.1 | Highest productivity ($238k/employee) |
| 7 | Dallas | 9.5 | Emerging market with growth potential |

### 7.2 Household Top 10% Leaders

| City | ZIPs | HH $200k+ | Median AGI | Median Score |
|------|------|-----------|------------|--------------|
| **New York** | 132 | 476,222 | $343 | 12.39% |
| **Los Angeles** | 46 | 169,722 | $322 | 12.78% |
| **Chicago** | 20 | 92,187 | $322 | **13.67%** |

**Note:** Chicago has highest median score but lower absolute volume - reflects high per-capita wealth in concentrated areas.

### 7.3 Corporate Top 10% Leaders (With Productivity)

| City | ZIPs | Employment | Revenue ($B) | Rev/Emp | Score |
|------|------|------------|--------------|---------|-------|
| **Los Angeles** | 110 | 3.4M | $799 | $233k | 0.1189 |
| **New York** | 45 | 2.3M | $549 | **$237k** | **0.1375** |
| **San Francisco** | 34 | 1.6M | $378 | **$238k** | 0.1285 |

**Note:** New York leads in Corporate Score despite lower volume than LA due to higher productivity ($237k vs $233k/employee) and higher power industry concentration (43.5% vs 39.9%).

### 7.4 Infrastructure Leaders

| City | Airports | Heliports | Total Facilities |
|------|----------|-----------|------------------|
| **Houston** | 23 | 46 | **69** 🥇 |
| **Los Angeles** | 2 | 50 | **52** 🥈 |
| **Miami** | 9 | 29 | **38** 🥉 |
| Chicago | 12 | 14 | 26 |
| Dallas | 9 | 14 | 23 |
| New York | 5 | 5 | 10 |
| San Francisco | 1 | 5 | 6 |

### 7.5 Intersection Analysis

**Updated Results (December 2025):**

| Metric | Value | Change |
|--------|-------|--------|
| Household Top 10% | 272 ZIPs | - |
| Corporate Top 10% | 321 ZIPs | ↓ from 360 |
| **Intersection** | **67 ZIPs** | ↓ from 197 |
| % of Household | 24.6% | ↓ from 72.4% |

**Why the decrease?** Adding **Revenue per Employee** prioritizes high-productivity corporate zones, which don't always overlap with wealthy residential areas. This is expected: wealthy households may prefer residential suburbs while high-productivity companies cluster in business districts.

**Strategic Implication:** Lower overlap suggests opportunity for helicopter services **connecting** distinct wealthy residential and corporate zones.

---

## 8. Detailed Methodology

### 8.1 Household Geometric Score - Step by Step

#### Step 1: Load Raw Data
- **IRS Data:** AGI per return from tax filings
- **Census Data:** Households earning $200k+, population
- **Geographic Data:** ZIP boundaries, centroids, areas
- **Travel Times:** Google Distance Matrix API

#### Step 2: Calculate IRS Wealth Proxy

Composite of 8 income indicators (normalized locally, then combined):

```python
IRS_Wealth_Raw = (
    0.20 × AGI_per_return +
    0.20 × Capital_Gains_per_return +
    0.15 × Dividends_per_return +
    0.10 × Interest_per_return +
    0.10 × Business_Income_per_return +
    0.10 × Real_Estate_Taxes_per_return +
    0.10 × Charitable_per_return +
    0.05 × Retirement_per_return
)
```

#### Step 3: Calculate Density

```python
HH200k_per_km² = Households_200k / Land_Area_km²
```

#### Step 4: Normalize Globally

```python
IRS_Norm = (IRS_Wealth_Raw - Global_Min) / (Global_Max - Global_Min)
Pop200k_Norm = (Households_200k - Global_Min) / (Global_Max - Global_Min)
Density_Norm = (HH200k_per_km² - Global_Min) / (Global_Max - Global_Min)
Time_Norm = (Travel_Time_Min - Global_Min) / (Global_Max - Global_Min)
```

#### Step 5: Calculate Geometric Score

```python
epsilon = 1e-10  # Prevent zeros
Geometric_Score = (
    (IRS_Norm + epsilon)^0.50 ×
    (Time_Norm² + epsilon)^0.20 ×
    (Pop200k_Norm + epsilon)^0.20 ×
    (Density_Norm + epsilon)^0.10
)
```

#### Step 6: Filter Top 10%

```python
threshold_90 = Geometric_Score.quantile(0.90)
Top_10_Percent = ZIPs where Geometric_Score ≥ threshold_90
```

---

### 8.2 Corporate Power Score - Step by Step

#### Step 1: Load Census Business Data

- Total establishments per ZIP
- Total employment (NAICS '00' - all industries)
- Annual payroll (thousands $)
- Detailed establishments by NAICS code

#### Step 2: Estimate Employment by Industry

When Census suppresses employment data:

```python
Emp_industry = Emp_total × (Estab_industry / Estab_total)
```

#### Step 3: Estimate Revenue

Using BLS revenue-per-employee ratios:

```python
Revenue = Employment × Revenue_per_Employee_Ratio × MSA_Multiplier
```

**MSA Multipliers** (from real payroll data):
- San Francisco: 1.686× (tech-driven)
- New York: 1.108×
- Chicago: 0.900×
- Houston: 0.804×
- Los Angeles: 0.796×
- Dallas: 0.740×
- Miami: 0.672×

#### Step 4: Calculate Power Industries

Sum employment in power NAICS codes (51, 52, 53, 54, 55, 71):

```python
Power_Employment = Σ Employment_by_NAICS for power industries
Power_Emp_Pct = (Power_Employment / Total_Employment) × 100
```

#### Step 5: Calculate Revenue per Employee 🆕

```python
Revenue_per_Employee = (Estimated_Revenue_M × 1,000,000) / Total_Employment
```

#### Step 6: Normalize Globally

```python
Revenue_Norm = (Revenue - Global_Min) / (Global_Max - Global_Min)
Employment_Norm = (Employment - Global_Min) / (Global_Max - Global_Min)
RevPerEmp_Norm = (Rev_per_Emp - Global_Min) / (Global_Max - Global_Min)
PowerShare_Norm = (Power_Emp_Pct - Global_Min) / (Global_Max - Global_Min)
Time_Norm = (Travel_Time_Min - Global_Min) / (Global_Max - Global_Min)
```

#### Step 7: Calculate Corporate Score

```python
Corporate_Score = (
    (Revenue_Norm + epsilon)^0.30 ×
    (Employment_Norm + epsilon)^0.25 ×
    (RevPerEmp_Norm + epsilon)^0.15 ×
    (PowerShare_Norm + epsilon)^0.10 ×
    (Time_Norm² + epsilon)^0.20
)
```

#### Step 8: Filter Top 10%

```python
threshold_90 = Corporate_Score.quantile(0.90)
Top_10_Percent = ZIPs where Corporate_Score ≥ threshold_90
```

**Result:** 321 ZIPs with 11.7M employees and $2.77 trillion revenue

---

### 8.3 Final Integrated Ranking - Step by Step

#### Step 1: Aggregate by City

For each city, calculate:
- **Household metrics:** Total HH $200k+, median Geometric Score, number of top 10% ZIPs
- **Corporate metrics:** Total employment, total revenue, median Corporate Score, number of top 10% ZIPs
- **Intersection:** Number of ZIPs in both household AND corporate top 10%
- **Infrastructure:** Count of airports and heliports

#### Step 2: Normalize Each Component (0-100 Scale)

```python
HH_Quality_Norm = normalize_to_100(Median_Geometric_Score)
HH_Volume_Norm = normalize_to_100(Total_Households_200k)
Corp_Quality_Norm = normalize_to_100(Median_Corporate_Score)
Corp_Volume_Norm = normalize_to_100(Total_Employment)
Intersection_Norm = normalize_to_100(Intersection_ZIPs)
Infra_Norm = normalize_to_100(Airports×2 + Heliports)
```

#### Step 3: Calculate Final Score

```python
Final_Score = (
    0.25 × HH_Quality_Norm +
    0.15 × HH_Volume_Norm +
    0.25 × Corp_Quality_Norm +
    0.15 × Corp_Volume_Norm +
    0.10 × Intersection_Norm +
    0.10 × Infra_Norm
)
```

#### Step 4: Rank Cities

Sort by `Final_Score` descending.

---

### 8.4 Weight Rationale - Final Score

**Quality vs Volume Balance (50/30):**
- **50% Quality** (25% HH + 25% Corp): Prioritizes per-capita wealth and productivity
- **30% Volume** (15% HH + 15% Corp): Ensures sufficient market size

**Synergy Factors (20%):**
- **10% Intersection:** Measures co-location of wealth and corporate power
- **10% Infrastructure:** Captures existing aviation ecosystem

**Why this balance?**
- Pure volume would favor LA overwhelmingly
- Pure quality would favor SF/Chicago with small markets
- This formula balances market size with target customer concentration

---

## 9. Premium Flight Analysis

### 9.1 Heatmap Methodology

**Grid Structure:**
- **X-Axis:** 24 hours (00h - 23h) in local time
- **Y-Axis:** 7 days (Monday - Sunday)
- **Value:** Average premium seats

**Two Panels per Airport:**
1. **DEPARTURES:** Flights leaving the airport
2. **ARRIVALS:** Flights arriving at the airport

**Aggregation:**
```python
# For each (day_of_week, hour) combination
Avg_Premium_Seats = df.groupby(['day_of_week', 'hour_local'])['premium_seats'].mean()
```

### 9.2 Purpose

- Identify **peak demand hours** for helicopter services
- Understand **weekly patterns** (business vs leisure travel)
- Compare **departures vs arrivals** temporal asymmetry
- Support **operational planning** (crew scheduling, fleet positioning)

---

## 10. Key Findings & Interpretations

### 10.1 Household Wealth

**Surprising Finding:** Chicago has highest median Geometric Score (13.67%) despite having only 92k HH $200k+ (vs 476k in New York).

**Explanation:** 
- Chicago's top 10% ZIPs have very high per-capita wealth (AGI)
- But smaller absolute numbers
- Methodology prioritizes **per-capita indicators** (50% weight) over volume (20% weight)

**Implication:** Chicago represents a **high-quality, concentrated** market. Smaller but wealthier.

### 10.2 Corporate Power

**Key Finding:** After adding productivity component, ranking changed significantly:

**New Top 3:**
1. New York (0.1375) - High productivity + power industries
2. Miami (0.1318) - Unexpected performer
3. San Francisco (0.1285) - Tech productivity

**LA dropped to 4th** despite largest revenue because:
- Lower revenue per employee ($233k vs $237k in NY)
- Lower power industry concentration (39.9% vs 43.5% in NY)

**Implication:** The market is not just about size - **productivity matters** for targeting high-value customers.

### 10.3 Final Ranking Insights

**New York's Dominance (Score 72.1):**
- #1 in household quality
- #1 in corporate quality
- Strong in both volume metrics
- Good (but not best) infrastructure

**Los Angeles' Strength (Score 58.5):**
- #1 in absolute volumes (employment, revenue)
- #2 in infrastructure (50 heliports!)
- 96% household-corporate overlap (highest)

**Chicago's Quality Punch (Score 37.4):**
- Highest per-capita household wealth
- High overlap (95%)
- Good infrastructure relative to size

**Houston's Infrastructure Advantage (Score 29.6):**
- Best infrastructure (69 facilities)
- But needs stronger wealth concentration

---

## 11. Data Quality & Limitations

### 11.1 What is 100% Real

✅ All establishment counts (Census CBP)  
✅ Total employment per ZIP (Census CBP)  
✅ Total payroll (Census CBP)  
✅ Households $200k+, population (Census ACS)  
✅ AGI per return (IRS SOI)  
✅ Travel times (Google Distance Matrix API)  
✅ Airport/heliport locations (FAA)  
✅ Premium flight counts (FlightRadar24)

### 11.2 What is Estimated

⚠️ **Revenue:** Not available from Census; estimated using BLS ratios  
⚠️ **Employment by Industry:** Proportional estimation when Census suppresses  
⚠️ **Scores:** Calculated metrics combining real and estimated data

### 11.3 Key Assumptions

1. **Revenue Estimation:** Assumes industry-average revenue/employee ratios apply locally
2. **Travel Time:** Single snapshot (varies by time of day, traffic conditions)
3. **Time² Component:** Assumes "farther = more exclusive" (normative choice)
4. **Geographic Scope:** Limited to 7 major metros (Boston, Seattle, DC not included)

### 11.4 Model Design Choices

**Distance/Time Component (20% weight in both scores):**
- **Assumption:** ZIP codes farther from airports are more exclusive/valuable
- **Reality Check:** Wealthy people also live near airports (e.g., Manhattan)
- **Sensitivity:** Reducing this weight to 10% could change rankings
- **Not tested:** U-shaped function (penalize very close AND very far)

**Why keep it?** 
- Identifies spread across metro area (not just airport clusters)
- Consistent with identifying helicopter service opportunities (connecting distant wealthy areas to airports)

---

## 12. Technical Implementation

### 12.1 Key Technologies

- **Python 3.x** - Primary language
- **Pandas/NumPy** - Data manipulation
- **GeoPandas** - Geographic processing
- **Folium** - Interactive maps
- **Matplotlib/Seaborn** - Visualizations
- **pytz** - Timezone conversions

### 12.2 Performance

- **Parallel processing:** 20-30 workers for API calls
- **Caching:** All API results cached (travel times, census data)
- **Batch processing:** Google API requests in batches of 25
- **Processing time:** ~3-5 minutes per full run

### 12.3 Files Generated

**Essential for Dashboard:**
- `top10_richest_data.csv` - Household top 10% (272 ZIPs)
- `corporate_top10_with_score.csv` - Corporate top 10% (321 ZIPs)
- `intersection_analysis.csv` - Overlap ZIPs (67 ZIPs)
- `intersection_by_city.csv` - City-level summary
- `final_city_ranking.csv` - Integrated ranking
- `dashboard_integrated.html` - Main dashboard
- `METHODOLOGY.html` - This documentation
- Map files (`.html`) for each city and analysis type

**Large Files (Excluded from GitHub):**
- `premium_flights_analysis.csv` - 866 MB (raw flight data)
- `flights_with_cabin_data_final.csv` - 129 MB
- Individual airport CSVs - 50-105 MB each

---

## 13. Changelog

### December 8, 2025 - Major Update

#### Corporate Score Enhancement
- **Added:** Revenue per Employee component (15% weight)
- **Adjusted:** Revenue 30% (was 35%), Employment 25% (was 30%), Power Share 10% (was 15%)
- **Impact:** Prioritizes high-productivity zones; New York moves to #1 corporate rank

#### Premium Flight Analysis
- **Added:** 3.1M+ flight records with temporal patterns
- **Implemented:** UTC to local time conversion for all airports
- **Created:** Day/Hour heatmaps for DEPARTURES and ARRIVALS
- **Purpose:** Identify demand patterns for helicopter service scheduling

#### Final Integrated Ranking
- **Created:** New comprehensive city ranking
- **Components:** 6 dimensions (HH quality/volume, Corp quality/volume, intersection, infrastructure)
- **Formula:** Weighted average with normalization
- **Result:** New York #1 (72.1), LA #2 (58.5), Chicago #3 (37.4)

#### Intersection Analysis
- **Updated:** 67 ZIPs intersection (was 197)
- **Reason:** New corporate score focuses on high-productivity zones
- **Interpretation:** Lower overlap = opportunity for connecting services

### November 30, 2025 - MSA Revenue Adjustments
- Added metropolitan-specific multipliers for revenue estimation
- Based on real payroll per employee data from Census CBP

---

## 14. References

### 14.1 Data Sources

- **IRS SOI:** https://www.irs.gov/statistics/soi-tax-stats
- **Census ACS:** https://www.census.gov/data/developers/data-sets/acs-5year.html
- **Census CBP:** https://www.census.gov/data/developers/data-sets/cbp-nonemp.html
- **Google Distance Matrix:** https://developers.google.com/maps/documentation/distance-matrix
- **FAA Airport Data:** https://www.faa.gov/airports/airport_safety/airportdata_5010/

### 14.2 Methodology References

- **Geometric Mean:** Standard statistical measure for multiplicative relationships
- **NAICS Classification:** North American Industry Classification System
- **Haversine Formula:** Great-circle distance calculation
- **K-Means Clustering:** Standard spatial clustering algorithm

---

## 15. Contact & Version Control

**GitHub Repository:** `cityexpansions_corporate`  
**Branch:** `main`  
**Latest Commit:** `fb72057` (December 8, 2025)

**Analysis Version:**
- Data: 2021-2022 (Census/IRS)
- Analysis: December 2025
- Methodology Version: 2.0

---

## Appendix A: Quick Reference Formulas

### Household Geometric Score
```
Score = IRS^0.50 × Time²^0.20 × Pop200k^0.20 × Density^0.10
```

### Corporate Score (Updated)
```
Score = Revenue^0.30 × Employment^0.25 × RevPerEmp^0.15 × PowerShare^0.10 × Time²^0.20
```

### Final City Ranking
```
Final = 0.25×HH_Qual + 0.15×HH_Vol + 0.25×Corp_Qual + 0.15×Corp_Vol + 0.10×Intersect + 0.10×Infra
```

### Revenue per Employee
```
Rev/Emp = (Revenue_M × 1,000,000) / Employment
```

### Infrastructure Score
```
Infra = (Airports × 2) + Heliports
```

---

**End of Methodology Document**

