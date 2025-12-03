# -*- coding: utf-8 -*-
"""
CORPORATE STATISTICAL ANALYSIS
===============================
Comprehensive statistical analysis for Corporate Top 10% data,
similar to household analysis.

Creates:
- Histograms and distributions
- City comparisons
- Geographic analysis
- Weighted averages
- Power Industries analysis

100% REAL DATA - U.S. Census Bureau 2021
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import os
from datetime import datetime
from scipy import stats

# =============================================================================
# CONFIGURATION
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'new_folder')

# Input files
CORPORATE_ALL_FILE = os.path.join(BASE_DIR, 'corporate_all_zips.csv')
CORPORATE_TOP10_FILE = os.path.join(BASE_DIR, 'top10_corporate_data.csv')
GEOMETRY_FILE = os.path.join(DATA_DIR, 'cache_geometry.gpkg')

# City configurations
CITIES = {
    'los_angeles': {'name': 'Los Angeles', 'color': '#ff7f0e'},
    'new_york': {'name': 'New York', 'color': '#1f77b4'},
    'chicago': {'name': 'Chicago', 'color': '#2ca02c'},
    'dallas': {'name': 'Dallas', 'color': '#d62728'},
    'houston': {'name': 'Houston', 'color': '#9467bd'},
    'miami': {'name': 'Miami', 'color': '#8c564b'},
    'san_francisco': {'name': 'San Francisco', 'color': '#e377c2'},
}

CITY_COLORS = {k: v['color'] for k, v in CITIES.items()}

# =============================================================================
# CALCULATE CORPORATE POWER INDEX
# =============================================================================
def calculate_power_index(df):
    """
    Calculate Corporate Power Index for a dataframe.
    
    NOTE: This is DIFFERENT from Corporate_Score:
    - Corporate_Score: Geometric mean with 4 components (35/30/15/20) INCLUDING distance - used for Top 10% selection
    - Corporate_Power_Index: Arithmetic weighted average with 3 components (40/30/30) WITHOUT distance - used for statistical analysis
    
    This index is used in intersection analysis and Combined_Score calculation.
    """
    WEIGHTS = {'revenue': 0.40, 'employment': 0.30, 'power_share': 0.30}
    
    df_active = df[df['total_employment'] > 0].copy()
    
    # Normalize components
    revenue_min = df_active['estimated_revenue_M'].min()
    revenue_max = df_active['estimated_revenue_M'].max()
    if revenue_max > revenue_min:
        revenue_norm = (df_active['estimated_revenue_M'] - revenue_min) / (revenue_max - revenue_min)
    else:
        revenue_norm = pd.Series([0.5] * len(df_active), index=df_active.index)
    
    emp_min = df_active['total_employment'].min()
    emp_max = df_active['total_employment'].max()
    if emp_max > emp_min:
        employment_norm = (df_active['total_employment'] - emp_min) / (emp_max - emp_min)
    else:
        employment_norm = pd.Series([0.5] * len(df_active), index=df_active.index)
    
    power_min = df_active['power_emp_pct'].min()
    power_max = df_active['power_emp_pct'].max()
    if power_max > power_min:
        power_share_norm = (df_active['power_emp_pct'] - power_min) / (power_max - power_min)
    else:
        power_share_norm = pd.Series([0.5] * len(df_active), index=df_active.index)
    
    # Calculate weighted index
    df_active['Corporate_Power_Index'] = (
        WEIGHTS['revenue'] * revenue_norm +
        WEIGHTS['employment'] * employment_norm +
        WEIGHTS['power_share'] * power_share_norm
    ) * 100
    
    return df_active

# =============================================================================
# LOAD DATA
# =============================================================================
def load_data():
    """Load corporate data"""
    print("\n" + "="*80)
    print("LOADING CORPORATE DATA")
    print("="*80)
    
    # All corporate ZIPs - filter only 7 metros (exclude 'other')
    df_all = pd.read_csv(CORPORATE_ALL_FILE, dtype={'zipcode': str})
    df_all = df_all[df_all['total_employment'] > 0].copy()  # Only active ZIPs
    df_all = df_all[df_all['city_key'] != 'other'].copy()  # Only 7 metros
    
    # Calculate Corporate Power Index for all ZIPs
    df_all = calculate_power_index(df_all)
    print(f"  All Corporate ZIPs: {len(df_all):,}")
    
    # Top 10% corporate - filter only 7 metros (exclude 'other')
    df_top10 = pd.read_csv(CORPORATE_TOP10_FILE, dtype={'zipcode': str})
    df_top10 = df_top10[df_top10['city_key'] != 'other'].copy()  # Only 7 metros
    print(f"  Top 10% Corporate ZIPs (7 metros): {len(df_top10):,}")
    
    # Calculate threshold
    threshold_90 = df_top10['Corporate_Power_Index'].min() if len(df_top10) > 0 else 0
    
    print(f"  90th Percentile Threshold: {threshold_90:.2f}")
    print(f"  Data Source: U.S. Census Bureau - County Business Patterns 2021")
    
    return df_all, df_top10, threshold_90

# =============================================================================
# CREATE HISTOGRAMS
# =============================================================================
def create_histograms(df_top10, df_all, threshold_90):
    """Create histogram visualizations"""
    print("\n" + "="*80)
    print("CREATING HISTOGRAMS")
    print("="*80)
    
    # Figure 1: Corporate Power Index Distribution (Top 10%)
    fig1, ax1 = plt.subplots(figsize=(12, 7))
    
    for city_key in df_top10['city_key'].unique():
        if city_key == 'other':
            continue  # Skip 'other' category
        city_data = df_top10[df_top10['city_key'] == city_key]
        city_name = CITIES.get(city_key, {}).get('name', city_key)
        if city_name == city_key:  # Not in CITIES dict
            continue
        ax1.hist(city_data['Corporate_Power_Index'].values, bins=20, alpha=0.6, 
                 label=f"{city_name} (n={len(city_data)})", 
                 color=CITY_COLORS.get(city_key, 'gray'))
    
    ax1.axvline(threshold_90, color='red', linestyle='--', linewidth=2, 
                label=f'90th Percentile: {threshold_90:.2f}')
    ax1.set_xlabel('Corporate Power Index', fontsize=12)
    ax1.set_ylabel('Number of Zip Codes', fontsize=12)
    ax1.set_title('Corporate Power Index Distribution - TOP 10% Corporate ZIP Codes', 
                  fontsize=14, fontweight='bold')
    ax1.legend(loc='upper right')
    ax1.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    fig1.savefig('corporate_histogram_top10_power_index.png', dpi=150, bbox_inches='tight')
    print("  [OK] corporate_histogram_top10_power_index.png")
    plt.close(fig1)
    
    # Figure 2: Comparison All vs Top 10%
    fig2, (ax2a, ax2b) = plt.subplots(1, 2, figsize=(14, 6))
    
    # All ZIPs
    all_data = df_all['Corporate_Power_Index'].dropna()
    if len(all_data) > 0:
        ax2a.hist(all_data.values, bins=50, color='#0066cc', alpha=0.7, edgecolor='white')
        ax2a.axvline(threshold_90, color='red', linestyle='--', linewidth=2, 
                    label=f'Top 10% Threshold: {threshold_90:.2f}')
        ax2a.axvline(all_data.median(), color='orange', linestyle=':', linewidth=2, 
                    label=f'Median: {all_data.median():.2f}')
        ax2a.set_xlabel('Corporate Power Index', fontsize=11)
        ax2a.set_ylabel('Zip Codes', fontsize=11)
        ax2a.set_title(f'All Corporate ZIPs (n={len(df_all):,})', fontsize=12, fontweight='bold')
        ax2a.legend(fontsize=9)
        ax2a.grid(axis='y', alpha=0.3)
    
    # Top 10%
    top10_data = df_top10['Corporate_Power_Index'].dropna()
    if len(top10_data) > 0:
        ax2b.hist(top10_data.values, bins=30, color='#0066cc', alpha=0.7, edgecolor='white')
        ax2b.axvline(top10_data.median(), color='orange', linestyle=':', linewidth=2, 
                    label=f'Median: {top10_data.median():.2f}')
        ax2b.set_xlabel('Corporate Power Index', fontsize=11)
        ax2b.set_ylabel('Zip Codes', fontsize=11)
        ax2b.set_title(f'Top 10% Corporate Power (n={len(df_top10):,})', fontsize=12, fontweight='bold')
        ax2b.legend(fontsize=9)
        ax2b.grid(axis='y', alpha=0.3)
    
    fig2.suptitle('Corporate Power Index: All vs Top 10%', fontsize=14, fontweight='bold')
    plt.tight_layout()
    fig2.savefig('corporate_histogram_all_vs_top10.png', dpi=150, bbox_inches='tight')
    print("  [OK] corporate_histogram_all_vs_top10.png")
    plt.close(fig2)
    
    # Figure 3: Box Plot by City
    fig3, ax3 = plt.subplots(figsize=(12, 7))
    
    city_data = []
    city_labels = []
    city_colors = []
    
    sorted_cities = df_top10[df_top10['city_key'] != 'other'].groupby('city_key').apply(
        lambda x: x['Corporate_Power_Index'].median()
    ).sort_values(ascending=False)
    
    for city_key in sorted_cities.index:
        if city_key == 'other':
            continue
        data = df_top10[df_top10['city_key'] == city_key]['Corporate_Power_Index'].values
        city_name = CITIES.get(city_key, {}).get('name', city_key)
        if len(data) > 0 and city_name != city_key:
            city_data.append(data)
            city_labels.append(city_name)
            city_colors.append(CITY_COLORS.get(city_key, 'gray'))
    
    if city_data:
        bp = ax3.boxplot(city_data, tick_labels=city_labels, patch_artist=True)
        for idx, box in enumerate(bp['boxes']):
            box.set_facecolor(city_colors[idx])
            box.set_alpha(0.7)
        
        ax3.set_ylabel('Corporate Power Index', fontsize=12)
        ax3.set_title('Top 10% Corporate Power Index by City\n(Sorted by Median)', 
                     fontsize=14, fontweight='bold')
        ax3.grid(axis='y', alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        fig3.savefig('corporate_histogram_top10_boxplot.png', dpi=150, bbox_inches='tight')
        print("  [OK] corporate_histogram_top10_boxplot.png")
        plt.close(fig3)
    
    # Figure 4: Revenue Distribution
    fig4, ax4 = plt.subplots(figsize=(12, 7))
    
    for city_key in df_top10['city_key'].unique():
        if city_key == 'other':
            continue
        city_data = df_top10[df_top10['city_key'] == city_key]
        city_name = CITIES.get(city_key, {}).get('name', city_key)
        if city_name == city_key:
            continue
        revenue_data = city_data['estimated_revenue_M'].values / 1000  # Convert to billions
        ax4.hist(revenue_data, bins=20, alpha=0.6,
                 label=f"{city_name}", color=CITY_COLORS.get(city_key, 'gray'))
    
    median_rev = df_top10['estimated_revenue_M'].median() / 1000
    ax4.axvline(median_rev, color='red', linestyle='--', linewidth=2, 
                label=f'Median: ${median_rev:.1f}B')
    ax4.set_xlabel('Estimated Revenue ($B)', fontsize=12)
    ax4.set_ylabel('Number of Zip Codes', fontsize=12)
    ax4.set_title('Revenue Distribution - Top 10% Corporate ZIP Codes', 
                  fontsize=14, fontweight='bold')
    ax4.legend(loc='upper right')
    ax4.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    fig4.savefig('corporate_histogram_top10_revenue.png', dpi=150, bbox_inches='tight')
    print("  [OK] corporate_histogram_top10_revenue.png")
    plt.close(fig4)
    
    # Figure 5: Employment Distribution
    fig5, ax5 = plt.subplots(figsize=(12, 7))
    
    for city_key in df_top10['city_key'].unique():
        if city_key == 'other':
            continue
        city_data = df_top10[df_top10['city_key'] == city_key]
        city_name = CITIES.get(city_key, {}).get('name', city_key)
        if city_name == city_key:
            continue
        emp_data = city_data['total_employment'].values / 1000  # Convert to thousands
        ax5.hist(emp_data, bins=20, alpha=0.6,
                 label=f"{city_name}", color=CITY_COLORS.get(city_key, 'gray'))
    
    median_emp = df_top10['total_employment'].median() / 1000
    ax5.axvline(median_emp, color='red', linestyle='--', linewidth=2, 
                label=f'Median: {median_emp:.0f}k')
    ax5.set_xlabel('Total Employment (thousands)', fontsize=12)
    ax5.set_ylabel('Number of Zip Codes', fontsize=12)
    ax5.set_title('Employment Distribution - Top 10% Corporate ZIP Codes', 
                  fontsize=14, fontweight='bold')
    ax5.legend(loc='upper right')
    ax5.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    fig5.savefig('corporate_histogram_top10_employment.png', dpi=150, bbox_inches='tight')
    print("  [OK] corporate_histogram_top10_employment.png")
    plt.close(fig5)
    
    # Figure 6: City Count Bar Chart
    fig6, ax6 = plt.subplots(figsize=(12, 7))
    
    city_counts = df_top10[df_top10['city_key'] != 'other'].groupby('city_name').size().sort_values(ascending=True)
    colors_list = [CITY_COLORS.get(k.lower().replace(' ', '_'), 'gray') 
                   for k in city_counts.index]
    
    bars = ax6.barh(city_counts.index, city_counts.values, 
                   color=colors_list, alpha=0.8, edgecolor='black')
    
    # Add value labels
    for bar, val in zip(bars, city_counts.values):
        ax6.text(val + max(city_counts.values) * 0.02, 
                bar.get_y() + bar.get_height()/2, f'{val}', 
                va='center', fontsize=11, fontweight='bold')
    
    ax6.set_xlabel('Number of Zip Codes in Top 10%', fontsize=12)
    ax6.set_title('Top 10% Corporate Power ZIP Codes by City', 
                  fontsize=14, fontweight='bold')
    ax6.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    fig6.savefig('corporate_histogram_top10_by_city.png', dpi=150, bbox_inches='tight')
    print("  [OK] corporate_histogram_top10_by_city.png")
    plt.close(fig6)
    
    # Figure 7: Power Industries Percentage
    fig7, ax7 = plt.subplots(figsize=(12, 7))
    
    for city_key in df_top10['city_key'].unique():
        if city_key == 'other':
            continue
        city_data = df_top10[df_top10['city_key'] == city_key]
        city_name = CITIES.get(city_key, {}).get('name', city_key)
        if city_name == city_key:
            continue
        power_pct = city_data['power_emp_pct'].values
        ax7.hist(power_pct, bins=20, alpha=0.6,
                 label=f"{city_name}", color=CITY_COLORS.get(city_key, 'gray'))
    
    median_power = df_top10['power_emp_pct'].median()
    ax7.axvline(median_power, color='red', linestyle='--', linewidth=2, 
                label=f'Median: {median_power:.1f}%')
    ax7.set_xlabel('Power Industries Employment %', fontsize=12)
    ax7.set_ylabel('Number of Zip Codes', fontsize=12)
    ax7.set_title('Power Industries Share - Top 10% Corporate ZIP Codes', 
                  fontsize=14, fontweight='bold')
    ax7.legend(loc='upper right')
    ax7.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    fig7.savefig('corporate_histogram_top10_power_share.png', dpi=150, bbox_inches='tight')
    print("  [OK] corporate_histogram_top10_power_share.png")
    plt.close(fig7)

# =============================================================================
# GEOGRAPHIC ANALYSIS
# =============================================================================
def create_geographic_analysis(df_top10):
    """Create geographic distance analysis (if geometry available)"""
    print("\n" + "="*80)
    print("GEOGRAPHIC ANALYSIS")
    print("="*80)
    
    try:
        import geopandas as gpd
        import json
        
        # Load travel times cache
        TRAVEL_TIMES_CACHE = os.path.join(BASE_DIR, 'cache_corporate_travel_times.json')
        travel_times = {}
        
        if os.path.exists(TRAVEL_TIMES_CACHE):
            with open(TRAVEL_TIMES_CACHE, 'r') as f:
                travel_times = json.load(f)
            print(f"  Travel times loaded: {len(travel_times)} ZIP codes")
        else:
            print(f"  [!] Travel times cache not found: {TRAVEL_TIMES_CACHE}")
            print(f"      Run fetch_corporate_travel_times.py first")
            return
        
        # Load geometry
        if os.path.exists(GEOMETRY_FILE):
            gdf = gpd.read_file(GEOMETRY_FILE)
            gdf['zipcode'] = gdf['ZCTA5CE20'].astype(str).str.zfill(5)
            print(f"  Geometry loaded: {len(gdf)} ZIP codes")
            
            # Merge with corporate data
            df_geo = df_top10.merge(
                gdf[['zipcode', 'geometry']], 
                on='zipcode', 
                how='left'
            )
            
            # Calculate centroids
            df_geo = df_geo[df_geo['geometry'].notna()].copy()
            if len(df_geo) > 0 and hasattr(df_geo.geometry.iloc[0], 'centroid'):
                centroids = df_geo.geometry.centroid
                df_geo['centroid_lat'] = centroids.y
                df_geo['centroid_lon'] = centroids.x
            else:
                print("  [!] Cannot calculate centroids, skipping geographic analysis")
                return
            
            # Add travel times
            df_geo['Travel_Time_Min'] = df_geo['zipcode'].map(travel_times).fillna(0)
            
            # Calculate distances to main airports
            airport_distances = []
            
            for city_key, config in CITIES.items():
                city_data = df_geo[df_geo['city_key'] == city_key]
                if len(city_data) > 0:
                    # Get airport coordinates from config
                    airport_lat = {
                        'los_angeles': 33.9416,
                        'new_york': 40.6413,
                        'chicago': 41.9742,
                        'dallas': 32.8998,
                        'houston': 29.9902,
                        'miami': 25.7959,
                        'san_francisco': 37.6213,
                    }
                    airport_lon = {
                        'los_angeles': -118.4085,
                        'new_york': -73.7781,
                        'chicago': -87.9073,
                        'dallas': -97.0403,
                        'houston': -95.3368,
                        'miami': -80.2870,
                        'san_francisco': -122.3790,
                    }
                    
                    apt_lat = airport_lat.get(city_key, 0)
                    apt_lon = airport_lon.get(city_key, 0)
                    
                    if apt_lat != 0:
                        # Haversine distance
                        R = 6371  # Earth radius in km
                        lat1 = np.radians(city_data['centroid_lat'])
                        lon1 = np.radians(city_data['centroid_lon'])
                        lat2 = np.radians(apt_lat)
                        lon2 = np.radians(apt_lon)
                        
                        dlat = lat2 - lat1
                        dlon = lon2 - lon1
                        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
                        c = 2 * np.arcsin(np.sqrt(a))
                        distance_km = R * c
                        
                        city_data = city_data.copy()
                        city_data['distance_to_airport_km'] = distance_km
                        airport_distances.append(city_data)
            
            if airport_distances:
                df_distances = pd.concat(airport_distances, ignore_index=True)
                
                # Filter only ZIPs with travel times
                df_distances = df_distances[df_distances['Travel_Time_Min'] > 0].copy()
                
                if len(df_distances) > 0:
                    # Create visualization
                    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
                    
                    # 1. Travel Time Distribution
                    ax1 = axes[0, 0]
                    ax1.hist(df_distances['Travel_Time_Min'], bins=30, 
                            color='#0066cc', alpha=0.7, edgecolor='white')
                    ax1.axvline(df_distances['Travel_Time_Min'].median(), 
                               color='red', linestyle='--', linewidth=2,
                               label=f'Median: {df_distances["Travel_Time_Min"].median():.1f} min')
                    ax1.set_xlabel('Travel Time to Airport (minutes)', fontsize=11)
                    ax1.set_ylabel('Number of ZIP Codes', fontsize=11)
                    ax1.set_title('Travel Time Distribution - Top 10% Corporate ZIPs', 
                                 fontsize=12, fontweight='bold')
                    ax1.legend()
                    ax1.grid(axis='y', alpha=0.3)
                    
                    # 2. Distance Distribution
                    ax2 = axes[0, 1]
                    ax2.hist(df_distances['distance_to_airport_km'], bins=30, 
                            color='#0066cc', alpha=0.7, edgecolor='white')
                    ax2.axvline(df_distances['distance_to_airport_km'].median(), 
                               color='red', linestyle='--', linewidth=2,
                               label=f'Median: {df_distances["distance_to_airport_km"].median():.1f} km')
                    ax2.set_xlabel('Distance to Main Airport (km)', fontsize=11)
                    ax2.set_ylabel('Number of ZIP Codes', fontsize=11)
                    ax2.set_title('Distance Distribution - Top 10% Corporate ZIPs', 
                                 fontsize=12, fontweight='bold')
                    ax2.legend()
                    ax2.grid(axis='y', alpha=0.3)
                    
                    # 3. Travel Time vs Corporate Power Index
                    ax3 = axes[1, 0]
                    for city_key in df_distances['city_key'].unique():
                        if city_key == 'other':
                            continue
                        city_data = df_distances[df_distances['city_key'] == city_key]
                        city_name = CITIES.get(city_key, {}).get('name', city_key)
                        if city_name != city_key:
                            ax3.scatter(city_data['Travel_Time_Min'], 
                                      city_data['Corporate_Power_Index'],
                                      alpha=0.6, label=city_name,
                                      color=CITY_COLORS.get(city_key, 'gray'), s=30)
                    
                    ax3.set_xlabel('Travel Time to Airport (minutes)', fontsize=11)
                    ax3.set_ylabel('Corporate Power Index', fontsize=11)
                    ax3.set_title('Corporate Power vs Travel Time', 
                                 fontsize=12, fontweight='bold')
                    ax3.legend(fontsize=9)
                    ax3.grid(alpha=0.3)
                    
                    # 4. Speed (Distance/Time)
                    df_distances['Speed_kmh'] = df_distances['distance_to_airport_km'] / (df_distances['Travel_Time_Min'] / 60)
                    df_distances['Speed_kmh'] = df_distances['Speed_kmh'].replace([np.inf, -np.inf], np.nan)
                    df_speed = df_distances[df_distances['Speed_kmh'].notna() & (df_distances['Speed_kmh'] > 0) & (df_distances['Speed_kmh'] < 200)]
                    
                    if len(df_speed) > 0:
                        ax4 = axes[1, 1]
                        ax4.hist(df_speed['Speed_kmh'], bins=30, 
                                color='#0066cc', alpha=0.7, edgecolor='white')
                        ax4.axvline(df_speed['Speed_kmh'].median(), 
                                   color='red', linestyle='--', linewidth=2,
                                   label=f'Median: {df_speed["Speed_kmh"].median():.1f} km/h')
                        ax4.set_xlabel('Average Speed (km/h)', fontsize=11)
                        ax4.set_ylabel('Number of ZIP Codes', fontsize=11)
                        ax4.set_title('Average Speed to Airport', 
                                     fontsize=12, fontweight='bold')
                        ax4.legend()
                        ax4.grid(axis='y', alpha=0.3)
                    
                    fig.suptitle('Geographic Analysis - Top 10% Corporate ZIP Codes', 
                               fontsize=14, fontweight='bold')
                    plt.tight_layout()
                    fig.savefig('corporate_distance_radius_analysis.png', dpi=150, bbox_inches='tight')
                    print("  [OK] corporate_distance_radius_analysis.png")
                    plt.close(fig)
                    
                    # Save CSV
                    df_distances[['zipcode', 'city_key', 'city_name', 'Corporate_Power_Index',
                                'total_employment', 'estimated_revenue_M', 'power_emp_pct',
                                'distance_to_airport_km', 'Travel_Time_Min', 'Speed_kmh']].to_csv(
                        'corporate_distance_analysis.csv', index=False
                    )
                    print("  [OK] corporate_distance_analysis.csv")
                else:
                    print("  [!] No ZIP codes with travel times found")
        else:
            print("  [!] Geometry file not found, skipping geographic analysis")
            
    except Exception as e:
        print(f"  [!] Error in geographic analysis: {e}")

# =============================================================================
# WEIGHTED AVERAGES
# =============================================================================
def create_weighted_averages(df_top10):
    """Create weighted averages analysis"""
    print("\n" + "="*80)
    print("WEIGHTED AVERAGES ANALYSIS")
    print("="*80)
    
    # Calculate weighted averages by city
    city_stats = []
    
    for city_key in df_top10['city_key'].unique():
        if city_key == 'other':
            continue  # Skip 'other' category
        city_data = df_top10[df_top10['city_key'] == city_key]
        city_name = CITIES.get(city_key, {}).get('name', city_key)
        if city_name == city_key:
            continue  # Skip if not in CITIES dict
        
        # Weights: employment
        total_emp = city_data['total_employment'].sum()
        total_rev = city_data['estimated_revenue_M'].sum()
        
        # Weighted Corporate Power Index (by employment)
        if total_emp > 0:
            weighted_power = (city_data['Corporate_Power_Index'] * 
                            city_data['total_employment']).sum() / total_emp
        else:
            weighted_power = 0
        
        # Weighted Revenue (by employment)
        if total_emp > 0:
            weighted_revenue = (city_data['estimated_revenue_M'] * 
                              city_data['total_employment']).sum() / total_emp
        else:
            weighted_revenue = 0
        
        # Simple averages
        simple_avg_power = city_data['Corporate_Power_Index'].mean()
        simple_avg_revenue = city_data['estimated_revenue_M'].mean()
        median_power = city_data['Corporate_Power_Index'].median()
        median_revenue = city_data['estimated_revenue_M'].median()
        
        city_stats.append({
            'city': city_name,
            'city_key': city_key,
            'zip_count': len(city_data),
            'total_employment': total_emp,
            'total_revenue_M': total_rev,
            'weighted_power_index': weighted_power,
            'simple_avg_power': simple_avg_power,
            'median_power': median_power,
            'weighted_revenue_M': weighted_revenue,
            'simple_avg_revenue_M': simple_avg_revenue,
            'median_revenue_M': median_revenue,
        })
    
    df_weighted = pd.DataFrame(city_stats)
    df_weighted = df_weighted.sort_values('total_employment', ascending=False)
    
    # Create visualization
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Weighted vs Simple Average Power Index
    ax1 = axes[0, 0]
    x_pos = np.arange(len(df_weighted))
    width = 0.35
    
    ax1.bar(x_pos - width/2, df_weighted['weighted_power_index'], width, 
           label='Weighted (by Employment)', color='#0066cc', alpha=0.8)
    ax1.bar(x_pos + width/2, df_weighted['simple_avg_power'], width,
           label='Simple Average', color='#99ccff', alpha=0.8)
    
    ax1.set_xlabel('City', fontsize=11)
    ax1.set_ylabel('Corporate Power Index', fontsize=11)
    ax1.set_title('Weighted vs Simple Average Power Index', fontsize=12, fontweight='bold')
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(df_weighted['city'], rotation=45, ha='right')
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    
    # 2. Weighted vs Simple Average Revenue
    ax2 = axes[0, 1]
    ax2.bar(x_pos - width/2, df_weighted['weighted_revenue_M'] / 1000, width,
           label='Weighted (by Employment)', color='#0066cc', alpha=0.8)
    ax2.bar(x_pos + width/2, df_weighted['simple_avg_revenue_M'] / 1000, width,
           label='Simple Average', color='#99ccff', alpha=0.8)
    
    ax2.set_xlabel('City', fontsize=11)
    ax2.set_ylabel('Revenue ($B)', fontsize=11)
    ax2.set_title('Weighted vs Simple Average Revenue', fontsize=12, fontweight='bold')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(df_weighted['city'], rotation=45, ha='right')
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)
    
    # 3. Total Employment by City
    ax3 = axes[1, 0]
    bars = ax3.barh(df_weighted['city'], df_weighted['total_employment'] / 1e6,
                    color=[CITY_COLORS.get(k.lower().replace(' ', '_'), 'gray') 
                          for k in df_weighted['city']], alpha=0.8)
    ax3.set_xlabel('Total Employment (Millions)', fontsize=11)
    ax3.set_title('Total Employment by City', fontsize=12, fontweight='bold')
    ax3.grid(axis='x', alpha=0.3)
    
    # 4. Total Revenue by City
    ax4 = axes[1, 1]
    bars = ax4.barh(df_weighted['city'], df_weighted['total_revenue_M'] / 1000,
                    color=[CITY_COLORS.get(k.lower().replace(' ', '_'), 'gray') 
                          for k in df_weighted['city']], alpha=0.8)
    ax4.set_xlabel('Total Revenue ($B)', fontsize=11)
    ax4.set_title('Total Revenue by City', fontsize=12, fontweight='bold')
    ax4.grid(axis='x', alpha=0.3)
    
    fig.suptitle('Weighted Averages Analysis - Top 10% Corporate ZIP Codes', 
                fontsize=14, fontweight='bold')
    plt.tight_layout()
    fig.savefig('corporate_weighted_averages_chart.png', dpi=150, bbox_inches='tight')
    print("  [OK] corporate_weighted_averages_chart.png")
    plt.close(fig)
    
    # Save CSV
    df_weighted.to_csv('corporate_weighted_averages_analysis.csv', index=False)
    print("  [OK] corporate_weighted_averages_analysis.csv")
    
    return df_weighted

# =============================================================================
# POWER INDUSTRIES BY REGION
# =============================================================================
def create_power_industries_analysis(df_top10):
    """Create Power Industries analysis by region"""
    print("\n" + "="*80)
    print("POWER INDUSTRIES BY REGION")
    print("="*80)
    
    # Aggregate by city
    city_power = []
    
    for city_key in df_top10['city_key'].unique():
        if city_key == 'other':
            continue
        city_data = df_top10[df_top10['city_key'] == city_key]
        city_name = CITIES.get(city_key, {}).get('name', city_key)
        if city_name == city_key:
            continue
        
        city_power.append({
            'city': city_name,
            'city_key': city_key,
            'zip_count': len(city_data),
            'total_employment': city_data['total_employment'].sum(),
            'power_employment': city_data['power_employment'].sum(),
            'power_employment_pct': (city_data['power_employment'].sum() / 
                                    city_data['total_employment'].sum() * 100) if city_data['total_employment'].sum() > 0 else 0,
            'total_revenue_M': city_data['estimated_revenue_M'].sum(),
            'power_revenue_M': city_data['power_revenue_M'].sum(),
            'power_revenue_pct': (city_data['power_revenue_M'].sum() / 
                                city_data['estimated_revenue_M'].sum() * 100) if city_data['estimated_revenue_M'].sum() > 0 else 0,
            'avg_power_index': city_data['Corporate_Power_Index'].mean(),
        })
    
    df_power = pd.DataFrame(city_power)
    df_power = df_power.sort_values('power_employment', ascending=False)
    
    # Create visualization
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Power Employment by City
    ax1 = axes[0, 0]
    bars = ax1.barh(df_power['city'], df_power['power_employment'] / 1e6,
                   color=[CITY_COLORS.get(k.lower().replace(' ', '_'), 'gray') 
                         for k in df_power['city']], alpha=0.8)
    ax1.set_xlabel('Power Industries Employment (Millions)', fontsize=11)
    ax1.set_title('Power Industries Employment by City', fontsize=12, fontweight='bold')
    ax1.grid(axis='x', alpha=0.3)
    
    # 2. Power Employment Percentage
    ax2 = axes[0, 1]
    bars = ax2.barh(df_power['city'], df_power['power_employment_pct'],
                   color=[CITY_COLORS.get(k.lower().replace(' ', '_'), 'gray') 
                         for k in df_power['city']], alpha=0.8)
    ax2.set_xlabel('Power Industries % of Total Employment', fontsize=11)
    ax2.set_title('Power Industries Share by City', fontsize=12, fontweight='bold')
    ax2.grid(axis='x', alpha=0.3)
    
    # 3. Power Revenue by City
    ax3 = axes[1, 0]
    bars = ax3.barh(df_power['city'], df_power['power_revenue_M'] / 1000,
                   color=[CITY_COLORS.get(k.lower().replace(' ', '_'), 'gray') 
                         for k in df_power['city']], alpha=0.8)
    ax3.set_xlabel('Power Industries Revenue ($B)', fontsize=11)
    ax3.set_title('Power Industries Revenue by City', fontsize=12, fontweight='bold')
    ax3.grid(axis='x', alpha=0.3)
    
    # 4. Average Corporate Power Index
    ax4 = axes[1, 1]
    bars = ax4.barh(df_power['city'], df_power['avg_power_index'],
                   color=[CITY_COLORS.get(k.lower().replace(' ', '_'), 'gray') 
                         for k in df_power['city']], alpha=0.8)
    ax4.set_xlabel('Average Corporate Power Index', fontsize=11)
    ax4.set_title('Average Corporate Power Index by City', fontsize=12, fontweight='bold')
    ax4.grid(axis='x', alpha=0.3)
    
    fig.suptitle('Power Industries Analysis - Top 10% Corporate ZIP Codes', 
                fontsize=14, fontweight='bold')
    plt.tight_layout()
    fig.savefig('corporate_power_industries_by_region.png', dpi=150, bbox_inches='tight')
    print("  [OK] corporate_power_industries_by_region.png")
    plt.close(fig)
    
    # Save CSV
    df_power.to_csv('corporate_power_industries_by_region.csv', index=False)
    print("  [OK] corporate_power_industries_by_region.csv")
    
    return df_power

# =============================================================================
# COMPARATIVE ANALYSIS
# =============================================================================
def create_comparative_analysis(df_top10, df_all):
    """Create comparative analysis charts"""
    print("\n" + "="*80)
    print("COMPARATIVE ANALYSIS")
    print("="*80)
    
    # Figure: Scatter plots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Revenue vs Employment
    ax1 = axes[0, 0]
    for city_key in df_top10['city_key'].unique():
        if city_key == 'other':
            continue
        city_data = df_top10[df_top10['city_key'] == city_key]
        city_name = CITIES.get(city_key, {}).get('name', city_key)
        if city_name == city_key:
            continue
        ax1.scatter(city_data['total_employment'] / 1000,
                   city_data['estimated_revenue_M'] / 1000,
                   alpha=0.6, label=city_name,
                   color=CITY_COLORS.get(city_key, 'gray'), s=30)
    
    ax1.set_xlabel('Employment (thousands)', fontsize=11)
    ax1.set_ylabel('Revenue ($B)', fontsize=11)
    ax1.set_title('Revenue vs Employment', fontsize=12, fontweight='bold')
    ax1.legend(fontsize=9)
    ax1.grid(alpha=0.3)
    
    # 2. Power Index vs Power Share
    ax2 = axes[0, 1]
    for city_key in df_top10['city_key'].unique():
        if city_key == 'other':
            continue
        city_data = df_top10[df_top10['city_key'] == city_key]
        city_name = CITIES.get(city_key, {}).get('name', city_key)
        if city_name == city_key:
            continue
        ax2.scatter(city_data['power_emp_pct'],
                   city_data['Corporate_Power_Index'],
                   alpha=0.6, label=city_name,
                   color=CITY_COLORS.get(city_key, 'gray'), s=30)
    
    ax2.set_xlabel('Power Industries %', fontsize=11)
    ax2.set_ylabel('Corporate Power Index', fontsize=11)
    ax2.set_title('Power Index vs Power Share', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=9)
    ax2.grid(alpha=0.3)
    
    # 3. Employment vs Establishments
    ax3 = axes[1, 0]
    for city_key in df_top10['city_key'].unique():
        if city_key == 'other':
            continue
        city_data = df_top10[df_top10['city_key'] == city_key]
        city_name = CITIES.get(city_key, {}).get('name', city_key)
        if city_name == city_key:
            continue
        ax3.scatter(city_data['total_establishments'] / 1000,
                   city_data['total_employment'] / 1000,
                   alpha=0.6, label=city_name,
                   color=CITY_COLORS.get(city_key, 'gray'), s=30)
    
    ax3.set_xlabel('Establishments (thousands)', fontsize=11)
    ax3.set_ylabel('Employment (thousands)', fontsize=11)
    ax3.set_title('Employment vs Establishments', fontsize=12, fontweight='bold')
    ax3.legend(fontsize=9)
    ax3.grid(alpha=0.3)
    
    # 4. Revenue per Employee (scatter plot instead of histogram)
    ax4 = axes[1, 1]
    df_top10['revenue_per_employee'] = (df_top10['estimated_revenue_M'] * 1e6) / df_top10['total_employment'].replace(0, 1)
    
    for city_key in df_top10['city_key'].unique():
        if city_key == 'other':
            continue
        city_data = df_top10[df_top10['city_key'] == city_key]
        city_name = CITIES.get(city_key, {}).get('name', city_key)
        if city_name == city_key:
            continue
        rev_per_emp = city_data['revenue_per_employee'] / 1000
        rev_per_emp = rev_per_emp[rev_per_emp.notna() & (rev_per_emp > 0) & (rev_per_emp < np.inf)]
        if len(rev_per_emp) > 0:
            # Use scatter plot instead of histogram
            ax4.scatter(rev_per_emp.values, 
                       np.random.normal(0, 0.1, len(rev_per_emp)),  # Jitter for visibility
                       alpha=0.6, label=city_name, 
                       color=CITY_COLORS.get(city_key, 'gray'), s=30)
    
    ax4.set_xlabel('Revenue per Employee ($k)', fontsize=11)
    ax4.set_ylabel('Jitter (for visibility)', fontsize=11)
    ax4.set_title('Revenue per Employee by City', fontsize=12, fontweight='bold')
    ax4.set_yticks([])  # Hide y-axis ticks
    ax4.legend(fontsize=9)
    ax4.grid(axis='y', alpha=0.3)
    
    fig.suptitle('Comparative Analysis - Top 10% Corporate ZIP Codes', 
                fontsize=14, fontweight='bold')
    plt.tight_layout()
    fig.savefig('corporate_comparative_analysis.png', dpi=150, bbox_inches='tight')
    print("  [OK] corporate_comparative_analysis.png")
    plt.close(fig)

# =============================================================================
# SUMMARY STATISTICS
# =============================================================================
def print_summary_statistics(df_top10, df_all, threshold_90):
    """Print comprehensive summary statistics"""
    print("\n" + "="*80)
    print("SUMMARY STATISTICS - TOP 10% CORPORATE")
    print("="*80)
    
    print(f"\nThreshold (90th Percentile): {threshold_90:.2f}")
    print(f"Total ZIPs in Top 10%: {len(df_top10):,}")
    print(f"Total ZIPs (All): {len(df_all):,}")
    print(f"Percentage: {len(df_top10)/len(df_all)*100:.2f}%")
    
    print("\n" + "-"*80)
    print("CORPORATE POWER INDEX")
    print("-"*80)
    print(f"  Mean: {df_top10['Corporate_Power_Index'].mean():.2f}")
    print(f"  Median: {df_top10['Corporate_Power_Index'].median():.2f}")
    print(f"  Std Dev: {df_top10['Corporate_Power_Index'].std():.2f}")
    print(f"  Min: {df_top10['Corporate_Power_Index'].min():.2f}")
    print(f"  Max: {df_top10['Corporate_Power_Index'].max():.2f}")
    
    print("\n" + "-"*80)
    print("EMPLOYMENT")
    print("-"*80)
    print(f"  Total: {df_top10['total_employment'].sum():,.0f}")
    print(f"  Mean per ZIP: {df_top10['total_employment'].mean():,.0f}")
    print(f"  Median per ZIP: {df_top10['total_employment'].median():,.0f}")
    print(f"  Power Industries: {df_top10['power_employment'].sum():,.0f}")
    print(f"  Power Industries %: {df_top10['power_employment'].sum()/df_top10['total_employment'].sum()*100:.1f}%")
    
    print("\n" + "-"*80)
    print("REVENUE")
    print("-"*80)
    print(f"  Total: ${df_top10['estimated_revenue_M'].sum()/1000:,.1f}B")
    print(f"  Mean per ZIP: ${df_top10['estimated_revenue_M'].mean():,.0f}M")
    print(f"  Median per ZIP: ${df_top10['estimated_revenue_M'].median():,.0f}M")
    print(f"  Power Industries: ${df_top10['power_revenue_M'].sum()/1000:,.1f}B")
    
    print("\n" + "-"*80)
    print("ESTABLISHMENTS")
    print("-"*80)
    print(f"  Total: {df_top10['total_establishments'].sum():,.0f}")
    print(f"  Power Industries: {df_top10['power_establishments'].sum():,.0f}")
    
    print("\n" + "-"*80)
    print("BY CITY")
    print("-"*80)
    city_summary = df_top10.groupby('city_name').agg({
        'zipcode': 'count',
        'total_employment': 'sum',
        'estimated_revenue_M': 'sum',
        'Corporate_Power_Index': 'mean',
        'power_emp_pct': 'mean'
    }).sort_values('total_employment', ascending=False)
    
    for city, row in city_summary.iterrows():
        print(f"\n  {city}:")
        print(f"    ZIPs: {int(row['zipcode'])}")
        print(f"    Employment: {int(row['total_employment']):,}")
        print(f"    Revenue: ${row['estimated_revenue_M']/1000:,.1f}B")
        print(f"    Avg Power Index: {row['Corporate_Power_Index']:.2f}")
        print(f"    Avg Power %: {row['power_emp_pct']:.1f}%")

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
    print("\n" + "="*80)
    print("CORPORATE STATISTICAL ANALYSIS")
    print("="*80)
    print("\n*** 100% REAL DATA FROM U.S. CENSUS BUREAU ***")
    print("\nThis analysis creates comprehensive statistics for Corporate Top 10%")
    print("similar to the household wealth analysis.")
    print()
    
    # Load data
    df_all, df_top10, threshold_90 = load_data()
    
    # Create histograms
    create_histograms(df_top10, df_all, threshold_90)
    
    # Geographic analysis
    create_geographic_analysis(df_top10)
    
    # Weighted averages
    df_weighted = create_weighted_averages(df_top10)
    
    # Power industries by region
    df_power = create_power_industries_analysis(df_top10)
    
    # Comparative analysis
    create_comparative_analysis(df_top10, df_all)
    
    # Summary statistics
    print_summary_statistics(df_top10, df_all, threshold_90)
    
    print("\n" + "="*80)
    print("COMPLETED")
    print("="*80)
    print("\nGenerated files:")
    print("  - corporate_histogram_*.png (6 histogram charts)")
    print("  - corporate_distance_radius_analysis.png")
    print("  - corporate_weighted_averages_chart.png")
    print("  - corporate_power_industries_by_region.png")
    print("  - corporate_comparative_analysis.png")
    print("  - corporate_distance_analysis.csv")
    print("  - corporate_weighted_averages_analysis.csv")
    print("  - corporate_power_industries_by_region.csv")

