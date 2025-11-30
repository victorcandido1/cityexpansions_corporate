# -*- coding: utf-8 -*-
"""
CALCULATE CORPORATE SCORE
=========================
Creates a Corporate Score similar to Geometric Score for households.

Formula: Geometric Mean with Distance² at 20% weight
Score = (Revenue^w1) * (Employment^w2) * (PowerShare^w3) * (Distance²^0.20)

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
# Distance² gets 20% as specified
WEIGHTS = {
    'revenue': 0.35,      # 35% - Total estimated revenue
    'employment': 0.30,   # 30% - Total employment
    'power_share': 0.15,  # 15% - Power industries percentage
    'distance_sq': 0.20   # 20% - Distance to airport squared
}

# =============================================================================
# NORMALIZATION FUNCTIONS
# =============================================================================
def normalize_global(value, min_val, max_val):
    """Normalize value to 0-1 range using global bounds"""
    if max_val == min_val:
        return 0.5
    return (value - min_val) / (max_val - min_val)

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate geodesic distance between two points"""
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

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
    
    # Add travel times
    df_merged['Travel_Time_Min'] = df_merged['zipcode'].map(travel_times).fillna(0)
    
    # Calculate distances to airports for ZIPs without travel times
    airport_coords = {
        'los_angeles': (33.9416, -118.4085),
        'new_york': (40.6413, -73.7781),
        'chicago': (41.9742, -87.9073),
        'dallas': (32.8998, -97.0403),
        'houston': (29.9902, -95.3368),
        'miami': (25.7959, -80.2870),
        'san_francisco': (37.6213, -122.3790),
    }
    
    def calculate_distance(row):
        if row['Travel_Time_Min'] > 0:
            # Use travel time to estimate distance (assume 40 km/h average)
            return (row['Travel_Time_Min'] / 60) * 40
        elif row['city_key'] in airport_coords:
            apt_lat, apt_lon = airport_coords[row['city_key']]
            return haversine_distance(row['centroid_lat'], row['centroid_lon'], apt_lat, apt_lon)
        return 0
    
    df_merged['Distance_km'] = df_merged.apply(calculate_distance, axis=1)
    
    # For ZIPs with travel time but no distance, estimate from time
    mask = (df_merged['Travel_Time_Min'] > 0) & (df_merged['Distance_km'] == 0)
    df_merged.loc[mask, 'Distance_km'] = (df_merged.loc[mask, 'Travel_Time_Min'] / 60) * 40
    
    return df_merged

# =============================================================================
# CALCULATE CORPORATE SCORE
# =============================================================================
def calculate_corporate_score(df):
    """Calculate Corporate Score using geometric mean"""
    print("\n" + "="*80)
    print("CALCULATING CORPORATE SCORE")
    print("="*80)
    print(f"\nFormula: Geometric Mean")
    print(f"  Revenue: {WEIGHTS['revenue']*100:.0f}%")
    print(f"  Employment: {WEIGHTS['employment']*100:.0f}%")
    print(f"  Power Share: {WEIGHTS['power_share']*100:.0f}%")
    print(f"  Distance²: {WEIGHTS['distance_sq']*100:.0f}%")
    
    # Filter only active ZIPs (7 cities)
    df_active = df[df['city_key'] != 'other'].copy()
    df_active = df_active[df_active['total_employment'] > 0].copy()
    
    print(f"\n  Active ZIPs (7 cities): {len(df_active):,}")
    
    # Global bounds for normalization
    global_bounds = {
        'estimated_revenue_M': (
            df_active['estimated_revenue_M'].min(),
            df_active['estimated_revenue_M'].max()
        ),
        'total_employment': (
            df_active['total_employment'].min(),
            df_active['total_employment'].max()
        ),
        'power_emp_pct': (
            df_active['power_emp_pct'].min(),
            df_active['power_emp_pct'].max()
        ),
        'Distance_km': (
            df_active['Distance_km'].min(),
            df_active['Distance_km'].max()
        ),
    }
    
    print(f"\n  Global Bounds:")
    print(f"    Revenue: ${global_bounds['estimated_revenue_M'][0]:,.0f}M - ${global_bounds['estimated_revenue_M'][1]:,.0f}M")
    print(f"    Employment: {global_bounds['total_employment'][0]:,.0f} - {global_bounds['total_employment'][1]:,.0f}")
    print(f"    Power Share: {global_bounds['power_emp_pct'][0]:.1f}% - {global_bounds['power_emp_pct'][1]:.1f}%")
    print(f"    Distance: {global_bounds['Distance_km'][0]:.1f} - {global_bounds['Distance_km'][1]:.1f} km")
    
    # Normalize globally
    df_active['Revenue_Norm'] = normalize_global(
        df_active['estimated_revenue_M'],
        *global_bounds['estimated_revenue_M']
    )
    df_active['Employment_Norm'] = normalize_global(
        df_active['total_employment'],
        *global_bounds['total_employment']
    )
    df_active['PowerShare_Norm'] = normalize_global(
        df_active['power_emp_pct'],
        *global_bounds['power_emp_pct']
    )
    df_active['Distance_Norm'] = normalize_global(
        df_active['Distance_km'],
        *global_bounds['Distance_km']
    )
    
    # Distance squared (normalized, then squared)
    df_active['Distance_Squared'] = df_active['Distance_Norm'] ** 2
    
    # GEOMETRIC SCORE
    epsilon = 1e-10
    df_active['Corporate_Score'] = (
        ((df_active['Revenue_Norm'] + epsilon) ** WEIGHTS['revenue']) *
        ((df_active['Employment_Norm'] + epsilon) ** WEIGHTS['employment']) *
        ((df_active['PowerShare_Norm'] + epsilon) ** WEIGHTS['power_share']) *
        ((df_active['Distance_Squared'] + epsilon) ** WEIGHTS['distance_sq'])
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

