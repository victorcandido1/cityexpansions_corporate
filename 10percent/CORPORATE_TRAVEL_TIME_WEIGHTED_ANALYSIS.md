# Corporate Travel Time Weighted by Revenue Analysis

## Overview

This analysis weights corporate travel time to airports by revenue metrics, providing insights into which cities have the most economically significant corporate presence relative to airport accessibility.

## Methodology

### Data Sources
- **Corporate Data**: U.S. Census Bureau - County Business Patterns 2021
- **Travel Times**: Google Distance Matrix API (driving with traffic)
- **Scope**: Top 10% Corporate Power ZIP codes across 7 major metros

### Weighting Methods

#### 1. Revenue per Employee Weighting
```
Weighted_Time = Σ(Travel_Time × Revenue_per_Employee) / Σ(Revenue_per_Employee)
```
- **Purpose**: Emphasizes ZIP codes with higher-productivity companies
- **Interpretation**: Higher weight to areas with more valuable/productive businesses
- **Use Case**: Identifying areas with high-value corporate clients

#### 2. Total Revenue Weighting
```
Weighted_Time = Σ(Travel_Time × Total_Revenue) / Σ(Total_Revenue)
```
- **Purpose**: Emphasizes ZIP codes with larger total economic output
- **Interpretation**: Higher weight to areas with greater overall business volume
- **Use Case**: Identifying areas with highest total market potential

#### 3. Employment Weighting (for comparison)
```
Weighted_Time = Σ(Travel_Time × Total_Employment) / Σ(Total_Employment)
```
- **Purpose**: Emphasizes ZIP codes with more employees
- **Interpretation**: Higher weight to areas with more workers
- **Use Case**: Identifying areas with largest workforce

## Key Findings

### Travel Time Summary (in minutes)

| City | Simple Mean | Rev/Employee | Total Revenue | Employment |
|------|-------------|--------------|---------------|------------|
| **Los Angeles** | 67.9 | 67.8 | 69.7 | 69.8 |
| **New York** | 56.9 | 57.3 | 59.3 | 59.1 |
| **San Francisco** | 36.9 | 36.4 | 35.3 | 35.7 |
| **Dallas** | 26.4 | 26.3 | 25.1 | 25.1 |
| **Chicago** | 49.2 | 49.2 | 49.4 | 49.4 |
| **Miami** | 101.8 | 102.5 | 109.1 | 108.9 |
| **Houston** | 41.3 | 41.4 | 40.3 | 40.2 |

### Revenue per Employee

| City | Rev/Employee | Ranking |
|------|--------------|---------|
| **San Francisco** | $237,826 | 🥇 Highest |
| **Chicago** | $237,628 | 🥈 |
| **New York** | $236,131 | 🥉 |
| **Los Angeles** | $231,468 | 4th |
| **Miami** | $229,716 | 5th |
| **Dallas** | $229,673 | 6th |
| **Houston** | $223,673 | 7th |

### Total Revenue (Top 10% ZIPs only)

| City | Total Revenue | Employment |
|------|---------------|------------|
| **Los Angeles** | $757B | 3.3M |
| **New York** | $551B | 2.3M |
| **San Francisco** | $507B | 2.1M |
| **Dallas** | $376B | 1.6M |
| **Chicago** | $372B | 1.6M |
| **Miami** | $246B | 1.1M |
| **Houston** | $230B | 1.0M |

## Insights

### 1. **Weighted vs Simple Mean Differences**

**Los Angeles**: 
- Weighted by revenue: **+2.6% higher** than simple mean
- Indicates: High-revenue areas are farther from LAX

**New York**:
- Weighted by revenue: **+4.2% higher** than simple mean
- Indicates: Major corporate centers in outer boroughs

**San Francisco**:
- Weighted by revenue: **-4.3% lower** than simple mean
- Indicates: High-revenue tech companies closer to SFO

**Miami**:
- Weighted by revenue: **+7.1% higher** than simple mean
- Indicates: Significant corporate activity far from MIA

### 2. **Best Airport Access (by weighted time)**

1. **Dallas** - 25.1 min (revenue-weighted)
2. **San Francisco** - 35.3 min (revenue-weighted)
3. **Houston** - 40.3 min (revenue-weighted)

### 3. **Productivity Leaders (Revenue per Employee)**

1. **San Francisco** - $238k/employee (Tech hub)
2. **Chicago** - $238k/employee (Finance hub)
3. **New York** - $236k/employee (Finance/Services hub)

## Business Implications

### For Service Providers (e.g., Helicopter Services)

**Priority Markets by Weighted Travel Time × Revenue:**

1. **Los Angeles** - Highest total market ($757B) but longer commutes (70 min weighted)
2. **New York** - Large market ($551B) with moderate commutes (59 min weighted)
3. **San Francisco** - Strong market ($507B) with best access (35 min weighted)

**Key Insight**: Cities with higher weighted times (vs simple mean) indicate that major corporate centers are located farther from airports - **higher service demand potential**.

### For Real Estate/Location Analysis

- **San Francisco**: Highest-productivity companies already near airport
- **Los Angeles & Miami**: High-value companies spread far from airports
- **New York**: Major corporate activity in outer areas

## Visualizations

The analysis generates:

1. **Travel Time Weighted by Revenue per Employee** - Shows impact of productivity weighting
2. **Travel Time Weighted by Total Revenue** - Shows impact of scale weighting
3. **Comparison Chart** - All weighting methods side-by-side
4. **Revenue per Employee by City** - Economic productivity comparison
5. **Total Revenue by City** - Market size comparison

## Files Generated

- `corporate_travel_time_weighted_by_revenue.png` - Comprehensive visualization
- `corporate_travel_time_weighted_by_revenue.csv` - Detailed statistics

## Interpretation Guide

### When Weighted Time > Simple Mean:
- Indicates that high-revenue/productive companies are **farther** from airports
- **Higher service demand potential** (longer commutes for valuable clients)
- Example: Miami (+7.1%), Los Angeles (+2.6%)

### When Weighted Time < Simple Mean:
- Indicates that high-revenue/productive companies are **closer** to airports
- **Convenient access already exists**
- Example: San Francisco (-4.3%), Dallas (-5.0%)

### When Weighted Time ≈ Simple Mean:
- Indicates **uniform distribution** of corporate power
- Example: Chicago (±0.4%)

## Usage

Run the analysis:
```bash
cd 10percent
python create_corporate_travel_time_weighted_charts.py
```

View results:
- Open `dashboard_integrated.html` in browser
- Navigate to "Corporate Statistical Analysis" section
- See "Airport Travel Time Weighted by Revenue"

## Technical Notes

- **Data Points**: 334 ZIP codes (with valid travel times)
- **Exclusions**: ZIPs with missing travel times or zero employment
- **Revenue Calculation**: Employment × BLS revenue-per-employee ratios
- **Travel Time Source**: Google Distance Matrix API (real traffic conditions)

---

**Generated**: December 2025  
**Script**: `create_corporate_travel_time_weighted_charts.py`  
**Data Source**: U.S. Census Bureau CBP 2021, Google Distance Matrix API


