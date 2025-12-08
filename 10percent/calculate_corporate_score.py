# -*- coding: utf-8 -*-
"""
CALCULATE CORPORATE SCORE
=========================
Creates a Corporate Score similar to Geometric Score for households.

Formula: Geometric Mean with Travel Time² at 20% weight (same as household)
Score = (Revenue^0.30) * (Employment^0.25) * (Rev/Emp^0.15) * (PowerShare^0.10) * (Time²^0.20)

Components:
  - Revenue Total (30%): Volume measure
  - Employment Total (25%): Volume measure
  - Revenue per Employee (15%): Productivity/Quality measure
  - Power Share (10%): Industry concentration
  - Travel Time² (20%): Geographic exclusivity

100% REAL DATA - U.S. Census Bureau + Google Distance Matrix API
"""

import pandas as pd
import numpy as np
import geopandas as gpd
import json
import os
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'new_folder')

# Input files
CORPORATE_ALL_FILE = os.path.join(BASE_DIR, 'corporate_all_zips.csv')
GEOMETRY_FILE = os.path.join(DATA_DIR, 'cache_geometry.gpkg')
TRAVEL_TIMES_FILE = os.path.join(BASE_DIR, 'cache_corporate_travel_times.json')

# Output files
OUTPUT_FILE = os.path.join(BASE_DIR, 'corporate_all_zips_with_score.csv')
OUTPUT_TOP10 = os.path.join(BASE_DIR, 'corporate_top10_with_score.csv')

# Weights for Corporate Score (must sum to 1.0)
# This uses GEOMETRIC MEAN (multiplicative) for Top 10% selection
# Travel Time² gets 20% as specified (same methodology as household)
# NOTE: This is different from Corporate_Power_Index which uses arithmetic mean (40/30/30) without time/distance
WEIGHTS = {
    'revenue': 0.30,           # 30% - Total estimated revenue (volume)
    'employment': 0.25,        # 25% - Total employment (volume)
    'revenue_per_emp': 0.15,   # 15% - Revenue per Employee (productivity/quality)
    'power_share': 0.10,       # 10% - Power industries percentage
    'time_sq': 0.20            # 20% - Travel time to airport squared (normalized)
}

# =============================================================================
# NORMALIZATION FUNCTIONS
# =============================================================================
def normalize_global(value, min_val, max_val):
    """Normalize value to 0-1 range using global bounds"""
    if max_val == min_val:
        return 0.5
    return (value - min_val) / (max_val - min_val)

# Note: haversine_distance function removed - we now use travel time directly (same as household)

# =============================================================================
# LOAD DATA
# =============================================================================
def load_data():
    """Load all required data"""
    print("\n" + "="*80)
    print("LOADING DATA")
    print("="*80)
    
    # Load corporate data
    df_corp = pd.read_csv(CORPORATE_ALL_FILE, dtype={'zipcode': str})
    df_corp = df_corp[df_corp['total_employment'] > 0].copy()
    print(f"  Corporate ZIPs: {len(df_corp):,}")
    
    # Load geometry
    if not os.path.exists(GEOMETRY_FILE):
        print(f"  [!] Geometry file not found: {GEOMETRY_FILE}")
        return None, None
    
    gdf = gpd.read_file(GEOMETRY_FILE)
    gdf['zipcode'] = gdf['ZCTA5CE20'].astype(str).str.zfill(5)
    print(f"  Geometry loaded: {len(gdf):,} ZIP codes")
    
    # Calculate centroids
    gdf['centroid_lat'] = gdf.geometry.centroid.y
    gdf['centroid_lon'] = gdf.geometry.centroid.x
    
    # Merge
    df_merged = df_corp.merge(
        gdf[['zipcode', 'centroid_lat', 'centroid_lon']],
        on='zipcode',
        how='left'
    )
    df_merged = df_merged[df_merged['centroid_lat'].notna()].copy()
    print(f"  ZIPs with geometry: {len(df_merged):,}")
    
    # Load travel times
    travel_times = {}
    if os.path.exists(TRAVEL_TIMES_FILE):
        with open(TRAVEL_TIMES_FILE, 'r') as f:
            travel_times = json.load(f)
        print(f"  Travel times loaded: {len(travel_times):,} ZIP codes")
    else:
        print(f"  [!] Travel times file not found: {TRAVEL_TIMES_FILE}")
    
    # Add travel times (same methodology as household - use Google Maps API travel time directly)
    df_merged['Travel_Time_Min'] = df_merged['zipcode'].map(travel_times).fillna(0)
    
    # Note: We use travel time directly (not converted to distance) to match household methodology
    # For ZIPs without travel time data, they will have Travel_Time_Min = 0
    
    return df_merged

# =============================================================================
# CALCULATE CORPORATE SCORE
# =============================================================================
def calculate_corporate_score(df):
    """Calculate Corporate Score using geometric mean"""
    print("\n" + "="*80)
    print("CALCULATING CORPORATE SCORE")
    print("="*80)
    print(f"\nFormula: Geometric Mean (same methodology as household)")
    print(f"  Revenue Total: {WEIGHTS['revenue']*100:.0f}%")
    print(f"  Employment Total: {WEIGHTS['employment']*100:.0f}%")
    print(f"  Revenue per Employee: {WEIGHTS['revenue_per_emp']*100:.0f}% (PRODUCTIVITY)")
    print(f"  Power Share: {WEIGHTS['power_share']*100:.0f}%")
    print(f"  Travel Time²: {WEIGHTS['time_sq']*100:.0f}%")
    
    # Filter only active ZIPs (7 cities)
    df_active = df[df['city_key'] != 'other'].copy()
    df_active = df_active[df_active['total_employment'] > 0].copy()
    
    print(f"\n  Active ZIPs (7 cities): {len(df_active):,}")
    
    # Calculate Revenue per Employee (productivity measure)
    df_active['revenue_per_employee'] = df_active['estimated_revenue_M'] * 1_000_000 / df_active['total_employment']
    df_active['revenue_per_employee'] = df_active['revenue_per_employee'].replace([np.inf, -np.inf], np.nan).fillna(0)
    
    # Global bounds for normalization (same methodology as household)
    global_bounds = {
        'estimated_revenue_M': (
            df_active['estimated_revenue_M'].min(),
            df_active['estimated_revenue_M'].max()
        ),
        'total_employment': (
            df_active['total_employment'].min(),
            df_active['total_employment'].max()
        ),
        'revenue_per_employee': (
            df_active['revenue_per_employee'].min(),
            df_active['revenue_per_employee'].max()
        ),
        'power_emp_pct': (
            df_active['power_emp_pct'].min(),
            df_active['power_emp_pct'].max()
        ),
        'Travel_Time_Min': (
            df_active['Travel_Time_Min'].min(),
            df_active['Travel_Time_Min'].max()
        ),
    }
    
    print(f"\n  Global Bounds:")
    print(f"    Revenue Total: ${global_bounds['estimated_revenue_M'][0]:,.0f}M - ${global_bounds['estimated_revenue_M'][1]:,.0f}M")
    print(f"    Employment Total: {global_bounds['total_employment'][0]:,.0f} - {global_bounds['total_employment'][1]:,.0f}")
    print(f"    Revenue/Employee: ${global_bounds['revenue_per_employee'][0]:,.0f} - ${global_bounds['revenue_per_employee'][1]:,.0f}")
    print(f"    Power Share: {global_bounds['power_emp_pct'][0]:.1f}% - {global_bounds['power_emp_pct'][1]:.1f}%")
    print(f"    Travel Time: {global_bounds['Travel_Time_Min'][0]:.1f} - {global_bounds['Travel_Time_Min'][1]:.1f} min")
    
    # Normalize globally (same methodology as household)
    df_active['Revenue_Norm'] = normalize_global(
        df_active['estimated_revenue_M'],
        *global_bounds['estimated_revenue_M']
    )
    df_active['Employment_Norm'] = normalize_global(
        df_active['total_employment'],
        *global_bounds['total_employment']
    )
    df_active['RevPerEmp_Norm'] = normalize_global(
        df_active['revenue_per_employee'],
        *global_bounds['revenue_per_employee']
    )
    df_active['PowerShare_Norm'] = normalize_global(
        df_active['power_emp_pct'],
        *global_bounds['power_emp_pct']
    )
    df_active['Time_Norm'] = normalize_global(
        df_active['Travel_Time_Min'],
        *global_bounds['Travel_Time_Min']
    )
    
    # Travel time squared (normalized, then squared - same as household)
    df_active['Time_Squared'] = df_active['Time_Norm'] ** 2
    
    # GEOMETRIC SCORE (same methodology as household Geometric_Score)
    # NOW INCLUDING REVENUE PER EMPLOYEE (PRODUCTIVITY)
    epsilon = 1e-10
    df_active['Corporate_Score'] = (
        ((df_active['Revenue_Norm'] + epsilon) ** WEIGHTS['revenue']) *           # 30% Revenue Total
        ((df_active['Employment_Norm'] + epsilon) ** WEIGHTS['employment']) *     # 25% Employment Total
        ((df_active['RevPerEmp_Norm'] + epsilon) ** WEIGHTS['revenue_per_emp']) * # 15% Productivity
        ((df_active['PowerShare_Norm'] + epsilon) ** WEIGHTS['power_share']) *    # 10% Power Share
        ((df_active['Time_Squared'] + epsilon) ** WEIGHTS['time_sq'])             # 20% Time²
    )
    
    # Statistics
    print(f"\n  Corporate Score Statistics:")
    print(f"    Min: {df_active['Corporate_Score'].min():.6f}")
    print(f"    Max: {df_active['Corporate_Score'].max():.6f}")
    print(f"    Mean: {df_active['Corporate_Score'].mean():.6f}")
    print(f"    Median: {df_active['Corporate_Score'].median():.6f}")
    
    # By city
    print(f"\n  Median Scores by City:")
    for city_key in sorted(df_active['city_key'].unique()):
        city_data = df_active[df_active['city_key'] == city_key]
        print(f"    {city_data['city_name'].iloc[0]}: median={city_data['Corporate_Score'].median():.6f}, mean={city_data['Corporate_Score'].mean():.6f}")
    
    return df_active

# =============================================================================
# FILTER TOP 10%
# =============================================================================
def filter_top_10_percent(df):
    """Filter top 10% by Corporate Score"""
    print("\n" + "="*80)
    print("FILTERING TOP 10% BY CORPORATE SCORE")
    print("="*80)
    
    # Calculate 90th percentile threshold
    threshold_90 = df['Corporate_Score'].quantile(0.90)
    print(f"\n  90th Percentile Threshold: {threshold_90:.6f}")
    
    # Filter
    df_top10 = df[df['Corporate_Score'] >= threshold_90].copy()
    print(f"  Total ZIPs in top 10%: {len(df_top10):,}")
    
    # Distribution by city
    print(f"\n  Distribution by City:")
    city_counts = df_top10.groupby('city_name').size().sort_values(ascending=False)
    total_by_city = df.groupby('city_name').size()
    
    for city_name, count in city_counts.items():
        total = total_by_city.get(city_name, 0)
        pct = count / total * 100 if total > 0 else 0
        print(f"    {city_name}: {count} ZIPs ({pct:.1f}% of city's ZIPs)")
    
    # Statistics
    print(f"\n  Top 10% Statistics:")
    print(f"    Score Range: {df_top10['Corporate_Score'].min():.6f} - {df_top10['Corporate_Score'].max():.6f}")
    print(f"    Median Score: {df_top10['Corporate_Score'].median():.6f}")
    print(f"    Mean Score: {df_top10['Corporate_Score'].mean():.6f}")
    print(f"    Total Employment: {df_top10['total_employment'].sum():,.0f}")
    print(f"    Total Revenue: ${df_top10['estimated_revenue_M'].sum()/1000:,.1f}B")
    
    return df_top10, threshold_90

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
    print("\n" + "="*80)
    print("CORPORATE SCORE CALCULATOR")
    print("="*80)
    print("\n*** 100% REAL DATA FROM U.S. CENSUS BUREAU + GOOGLE API ***")
    print()
    
    # Load data
    df = load_data()
    if df is None:
        exit(1)
    
    # Calculate score
    df_scored = calculate_corporate_score(df)
    
    # Filter top 10%
    df_top10, threshold_90 = filter_top_10_percent(df_scored)
    
    # Add threshold to dataframes
    df_scored['threshold_90'] = threshold_90
    df_top10['threshold_90'] = threshold_90
    
    # Save
    print("\n" + "="*80)
    print("SAVING RESULTS")
    print("="*80)
    
    df_scored.to_csv(OUTPUT_FILE, index=False)
    print(f"  [OK] {OUTPUT_FILE}")
    print(f"      Records: {len(df_scored):,}")
    
    df_top10.to_csv(OUTPUT_TOP10, index=False)
    print(f"  [OK] {OUTPUT_TOP10}")
    print(f"      Records: {len(df_top10):,}")
    print(f"      Threshold: {threshold_90:.6f}")
    
    print("\n" + "="*80)
    print("COMPLETED")
    print("="*80)

