# -*- coding: utf-8 -*-
"""
CORPORATE ADVANCED STATISTICS
=============================
Creates advanced statistics for corporate data similar to households:
- Geodesic distance analysis
- Time weighted by corporate wealth (using median of households $200k+)

100% REAL DATA
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import json

# =============================================================================
# CONFIGURATION
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'new_folder')

# Input files
CORPORATE_SCORED_FILE = os.path.join(BASE_DIR, 'corporate_all_zips_with_score.csv')
CORPORATE_TOP10_FILE = os.path.join(BASE_DIR, 'corporate_top10_with_score.csv')
HOUSEHOLD_FILE = os.path.join(BASE_DIR, 'top10_richest_data.csv')
TRAVEL_TIMES_FILE = os.path.join(BASE_DIR, 'cache_corporate_travel_times.json')

# City configurations
CITIES = {
    'los_angeles': {
        'name': 'Los Angeles',
        'airport_code': 'LAX',
        'airport_lat': 33.9416,
        'airport_lon': -118.4085,
    },
    'new_york': {
        'name': 'New York',
        'airport_code': 'JFK',
        'airport_lat': 40.6413,
        'airport_lon': -73.7781,
    },
    'chicago': {
        'name': 'Chicago',
        'airport_code': 'ORD',
        'airport_lat': 41.9742,
        'airport_lon': -87.9073,
    },
    'dallas': {
        'name': 'Dallas',
        'airport_code': 'DFW',
        'airport_lat': 32.8998,
        'airport_lon': -97.0403,
    },
    'houston': {
        'name': 'Houston',
        'airport_code': 'IAH',
        'airport_lat': 29.9902,
        'airport_lon': -95.3368,
    },
    'miami': {
        'name': 'Miami',
        'airport_code': 'MIA',
        'airport_lat': 25.7959,
        'airport_lon': -80.2870,
    },
    'san_francisco': {
        'name': 'San Francisco',
        'airport_code': 'SFO',
        'airport_lat': 37.6213,
        'airport_lon': -122.3790,
    }
}

# =============================================================================
# HAVERSINE DISTANCE
# =============================================================================
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
# GEODESIC DISTANCE ANALYSIS
# =============================================================================
def create_geodesic_distance_analysis(df_top10, df_all):
    """Create geodesic distance analysis similar to households"""
    print("\n" + "="*80)
    print("GEODESIC DISTANCE ANALYSIS")
    print("="*80)
    
    results = []
    
    for city_key, config in CITIES.items():
        city_name = config['name']
        airport_lat = config['airport_lat']
        airport_lon = config['airport_lon']
        airport_code = config['airport_code']
        
        df_city_top = df_top10[df_top10['city_key'] == city_key].copy()
        df_city_all = df_all[df_all['city_key'] == city_key].copy()
        
        if len(df_city_top) == 0:
            continue
        
        # Calculate geodesic distance from each zip to airport
        df_city_top['Distance_km'] = df_city_top.apply(
            lambda r: haversine_distance(r['centroid_lat'], r['centroid_lon'], airport_lat, airport_lon), 
            axis=1
        )
        
        # Weighted distance by travel time (higher travel time = more weight)
        total_time = df_city_top['Travel_Time_Min'].sum()
        if total_time > 0:
            df_city_top['Weight'] = df_city_top['Travel_Time_Min'] / total_time
            weighted_distance = (df_city_top['Distance_km'] * df_city_top['Weight']).sum()
        else:
            weighted_distance = df_city_top['Distance_km'].mean()
        
        # Statistics
        max_distance = df_city_top['Distance_km'].max()
        min_distance = df_city_top['Distance_km'].min()
        mean_distance = df_city_top['Distance_km'].mean()
        median_distance = df_city_top['Distance_km'].median()
        
        # Centroid of top 10% region
        centroid_lat = df_city_top['centroid_lat'].mean()
        centroid_lon = df_city_top['centroid_lon'].mean()
        centroid_distance = haversine_distance(centroid_lat, centroid_lon, airport_lat, airport_lon)
        
        # Region spread (max distance between any two ZIPs)
        max_spread = 0
        for i, row1 in df_city_top.iterrows():
            for j, row2 in df_city_top.iterrows():
                if i < j:
                    d = haversine_distance(row1['centroid_lat'], row1['centroid_lon'], 
                                          row2['centroid_lat'], row2['centroid_lon'])
                    if d > max_spread:
                        max_spread = d
        
        bounding_radius = max_spread / 2
        
        # Travel time statistics
        avg_travel_time = df_city_top['Travel_Time_Min'].mean()
        median_travel_time = df_city_top['Travel_Time_Min'].median()
        
        # Speed
        df_city_top['Speed_kmh'] = df_city_top['Distance_km'] / (df_city_top['Travel_Time_Min'] / 60)
        df_city_top['Speed_kmh'] = df_city_top['Speed_kmh'].replace([np.inf, -np.inf], np.nan)
        avg_speed = df_city_top['Speed_kmh'].mean()
        
        results.append({
            'City': city_name,
            'Airport': airport_code,
            'Top10_Zips': len(df_city_top),
            'Weighted_Distance_km': weighted_distance,
            'Mean_Distance_km': mean_distance,
            'Median_Distance_km': median_distance,
            'Min_Distance_km': min_distance,
            'Max_Distance_km': max_distance,
            'Centroid_to_Airport_km': centroid_distance,
            'Region_Spread_km': max_spread,
            'Bounding_Radius_km': bounding_radius,
            'Mean_Travel_Time_min': avg_travel_time,
            'Median_Travel_Time_min': median_travel_time,
            'Avg_Speed_kmh': avg_speed,
            'Centroid_Lat': centroid_lat,
            'Centroid_Lon': centroid_lon,
        })
    
    df_results = pd.DataFrame(results)
    
    # Print table
    print("\n" + "-"*120)
    print(f"| {'City':<15} | {'Airport':<7} | {'Zips':<5} | {'Weighted Dist':<13} | {'Median Dist':<11} | {'Max Dist':<9} | {'Radius':<9} | {'Median Time':<11} |")
    print("-"*120)
    for _, row in df_results.iterrows():
        print(f"| {row['City']:<15} | {row['Airport']:<7} | {row['Top10_Zips']:<5} | {row['Weighted_Distance_km']:>10.1f} km | {row['Median_Distance_km']:>8.1f} km | {row['Max_Distance_km']:>6.1f} km | {row['Bounding_Radius_km']:>6.1f} km | {row['Median_Travel_Time_min']:>8.1f} min |")
    print("-"*120)
    
    # Save
    df_results.to_csv('corporate_distance_radius_analysis.csv', index=False)
    print("\n  [OK] corporate_distance_radius_analysis.csv")
    
    # Create visualization
    create_geodesic_chart(df_results)
    
    return df_results

# =============================================================================
# TIME WEIGHTED BY CORPORATE WEALTH
# =============================================================================
def create_time_weighted_by_wealth(df_top10, df_all):
    """
    Create time weighted by corporate wealth analysis.
    Uses median of households $200k+ as weight (similar to household analysis)
    """
    print("\n" + "="*80)
    print("TIME WEIGHTED BY CORPORATE WEALTH")
    print("="*80)
    
    # Load household data to get median AGI for weighting
    df_hh = pd.read_csv(HOUSEHOLD_FILE, dtype={'zipcode': str})
    
    # Calculate median AGI per return for households $200k+ by city
    hh_medians = {}
    for city_key in CITIES.keys():
        df_city_hh = df_hh[df_hh['city_key'] == city_key]
        if len(df_city_hh) > 0:
            # Use median AGI per return as weight
            hh_medians[city_key] = df_city_hh['AGI_per_return'].median()
        else:
            # Fallback: use overall median
            hh_medians[city_key] = df_hh['AGI_per_return'].median()
    
    print(f"\n  Median AGI per Return (Households $200k+) by City:")
    for city_key, median_agi in hh_medians.items():
        print(f"    {CITIES[city_key]['name']}: ${median_agi:,.0f}")
    
    results = []
    
    for city_key, config in CITIES.items():
        city_name = config['name']
        df_city_top = df_top10[df_top10['city_key'] == city_key].copy()
        
        if len(df_city_top) == 0:
            continue
        
        # Get median AGI for this city
        median_agi = hh_medians.get(city_key, df_hh['AGI_per_return'].median())
        
        # Weight by corporate wealth (revenue × employment)
        # Similar to household analysis: weight by (HH200k × AGI)
        df_city_top['Corporate_Wealth'] = (
            df_city_top['estimated_revenue_M'] * df_city_top['total_employment']
        )
        
        # Weight travel time by corporate wealth
        total_wealth = df_city_top['Corporate_Wealth'].sum()
        if total_wealth > 0:
            df_city_top['Wealth_Weight'] = df_city_top['Corporate_Wealth'] / total_wealth
            weighted_time = (df_city_top['Travel_Time_Min'] * df_city_top['Wealth_Weight']).sum()
        else:
            weighted_time = df_city_top['Travel_Time_Min'].mean()
        
        # Also weight by median AGI (as in household analysis)
        # This gives more weight to ZIPs in areas with higher household wealth
        df_city_top['AGI_Weight'] = median_agi / df_city_top['Corporate_Wealth'].sum() if df_city_top['Corporate_Wealth'].sum() > 0 else 1.0
        
        # Combined weight: corporate wealth × AGI weight
        df_city_top['Combined_Weight'] = df_city_top['Wealth_Weight'] * (median_agi / df_city_top['Corporate_Wealth'].sum() if df_city_top['Corporate_Wealth'].sum() > 0 else 1.0)
        df_city_top['Combined_Weight'] = df_city_top['Combined_Weight'] / df_city_top['Combined_Weight'].sum()  # Normalize
        
        weighted_time_combined = (df_city_top['Travel_Time_Min'] * df_city_top['Combined_Weight']).sum()
        
        # Simple statistics
        mean_time = df_city_top['Travel_Time_Min'].mean()
        median_time = df_city_top['Travel_Time_Min'].median()
        
        results.append({
            'City': city_name,
            'Top10_Zips': len(df_city_top),
            'Mean_Travel_Time_min': mean_time,
            'Median_Travel_Time_min': median_time,
            'Weighted_Time_by_Wealth_min': weighted_time,
            'Weighted_Time_by_Wealth_AGI_min': weighted_time_combined,
            'Median_AGI_per_Return': median_agi,
            'Total_Revenue_M': df_city_top['estimated_revenue_M'].sum(),
            'Total_Employment': df_city_top['total_employment'].sum(),
        })
    
    df_results = pd.DataFrame(results)
    
    # Print table
    print("\n" + "-"*100)
    print(f"| {'City':<15} | {'Zips':<5} | {'Mean Time':<10} | {'Median Time':<12} | {'Weighted Time':<13} | {'Weighted+AGI':<13} |")
    print("-"*100)
    for _, row in df_results.iterrows():
        print(f"| {row['City']:<15} | {row['Top10_Zips']:<5} | {row['Mean_Travel_Time_min']:>7.1f} min | {row['Median_Travel_Time_min']:>9.1f} min | {row['Weighted_Time_by_Wealth_min']:>10.1f} min | {row['Weighted_Time_by_Wealth_AGI_min']:>10.1f} min |")
    print("-"*100)
    
    # Save
    df_results.to_csv('corporate_time_weighted_by_wealth.csv', index=False)
    print("\n  [OK] corporate_time_weighted_by_wealth.csv")
    
    return df_results

# =============================================================================
# CREATE VISUALIZATIONS
# =============================================================================
def create_geodesic_chart(df_results):
    """Create visualization for geodesic distance analysis"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Distance statistics
    ax1 = axes[0, 0]
    x_pos = np.arange(len(df_results))
    width = 0.35
    
    ax1.bar(x_pos - width/2, df_results['Mean_Distance_km'], width, 
           label='Mean', color='#0066cc', alpha=0.8)
    ax1.bar(x_pos + width/2, df_results['Median_Distance_km'], width,
           label='Median', color='#99ccff', alpha=0.8)
    
    ax1.set_xlabel('City', fontsize=11)
    ax1.set_ylabel('Distance (km)', fontsize=11)
    ax1.set_title('Distance to Airport Statistics', fontsize=12, fontweight='bold')
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(df_results['City'], rotation=45, ha='right')
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    
    # 2. Travel time statistics
    ax2 = axes[0, 1]
    ax2.bar(x_pos, df_results['Median_Travel_Time_min'], color='#0066cc', alpha=0.8)
    ax2.set_xlabel('City', fontsize=11)
    ax2.set_ylabel('Travel Time (minutes)', fontsize=11)
    ax2.set_title('Median Travel Time to Airport', fontsize=12, fontweight='bold')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(df_results['City'], rotation=45, ha='right')
    ax2.grid(axis='y', alpha=0.3)
    
    # 3. Region spread
    ax3 = axes[1, 0]
    ax3.bar(x_pos, df_results['Region_Spread_km'], color='#0066cc', alpha=0.8)
    ax3.set_xlabel('City', fontsize=11)
    ax3.set_ylabel('Region Spread (km)', fontsize=11)
    ax3.set_title('Top 10% Region Spread', fontsize=12, fontweight='bold')
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(df_results['City'], rotation=45, ha='right')
    ax3.grid(axis='y', alpha=0.3)
    
    # 4. Average speed
    ax4 = axes[1, 1]
    ax4.bar(x_pos, df_results['Avg_Speed_kmh'], color='#0066cc', alpha=0.8)
    ax4.set_xlabel('City', fontsize=11)
    ax4.set_ylabel('Average Speed (km/h)', fontsize=11)
    ax4.set_title('Average Speed to Airport', fontsize=12, fontweight='bold')
    ax4.set_xticks(x_pos)
    ax4.set_xticklabels(df_results['City'], rotation=45, ha='right')
    ax4.grid(axis='y', alpha=0.3)
    
    fig.suptitle('Geodesic Distance Analysis - Top 10% Corporate ZIP Codes', 
                fontsize=14, fontweight='bold')
    plt.tight_layout()
    fig.savefig('corporate_geodesic_analysis.png', dpi=150, bbox_inches='tight')
    print("  [OK] corporate_geodesic_analysis.png")
    plt.close(fig)

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
    print("\n" + "="*80)
    print("CORPORATE ADVANCED STATISTICS")
    print("="*80)
    print("\n*** 100% REAL DATA ***")
    print()
    
    # Load data
    df_all = pd.read_csv(CORPORATE_SCORED_FILE, dtype={'zipcode': str})
    df_top10 = pd.read_csv(CORPORATE_TOP10_FILE, dtype={'zipcode': str})
    
    print(f"  All Corporate ZIPs: {len(df_all):,}")
    print(f"  Top 10% Corporate ZIPs: {len(df_top10):,}")
    
    # Geodesic distance analysis
    df_geodesic = create_geodesic_distance_analysis(df_top10, df_all)
    
    # Time weighted by wealth
    df_weighted = create_time_weighted_by_wealth(df_top10, df_all)
    
    print("\n" + "="*80)
    print("COMPLETED")
    print("="*80)

