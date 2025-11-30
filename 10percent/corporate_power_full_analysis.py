# -*- coding: utf-8 -*-
"""
CORPORATE POWER INDEX - FULL ANALYSIS
=====================================
Analyzes ALL ZIP codes in each city (not just top 10% wealthy)
Separate analysis from household wealth - then cross-reference.

Two separate analyses:
1. CORPORATE: All ZIP codes where businesses operate
2. HOUSEHOLDS: Top 10% wealthy residential areas
3. CROSS-REFERENCE: Compare and identify overlaps
"""

import pandas as pd
import numpy as np
import requests
import os
import json
from datetime import datetime
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

# =============================================================================
# CONFIGURATION
# =============================================================================
CENSUS_API_KEY = "65e82b0208b07695a5ffa13b7b9f805462804467"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'new_folder')

# Power industries (NAICS codes)
POWER_INDUSTRIES = ['51', '52', '53', '54', '55', '71']
ENTERTAINMENT_INDUSTRIES = ['51', '71']

# City configurations
CITIES = {
    'los_angeles': {
        'name': 'Los Angeles', 'state': 'CA',
        'center_lat': 34.0522, 'center_lon': -118.2437, 'radius_km': 100,
        'zip_prefixes': ['900', '901', '902', '903', '904', '905', '906', '907', '908', '909', 
                         '910', '911', '912', '913', '914', '915', '916', '917', '918',
                         '920', '921', '922', '923', '924', '925', '926', '927', '928'],
    },
    'new_york': {
        'name': 'New York', 'state': 'NY',
        'center_lat': 40.7128, 'center_lon': -74.0060, 'radius_km': 180,
        'zip_prefixes': ['100', '101', '102', '103', '104', '105', '106', '107', '108', '109',
                         '110', '111', '112', '113', '114', '115', '116', '117', '118', '119',
                         '070', '071', '072', '073', '074', '075', '076', '077', '078', '079',
                         '068', '069', '088', '089'],
    },
    'chicago': {
        'name': 'Chicago', 'state': 'IL',
        'center_lat': 41.8781, 'center_lon': -87.6298, 'radius_km': 100,
        'zip_prefixes': ['600', '601', '602', '603', '604', '605', '606', '607', '608', '609'],
    },
    'dallas': {
        'name': 'Dallas', 'state': 'TX',
        'center_lat': 32.7767, 'center_lon': -96.7970, 'radius_km': 100,
        'zip_prefixes': ['750', '751', '752', '753', '754', '755', '756', '757', '758', '759',
                         '760', '761', '762', '763'],
    },
    'houston': {
        'name': 'Houston', 'state': 'TX',
        'center_lat': 29.7604, 'center_lon': -95.3698, 'radius_km': 100,
        'zip_prefixes': ['770', '771', '772', '773', '774', '775', '776', '777', '778', '779'],
    },
    'miami': {
        'name': 'Miami', 'state': 'FL',
        'center_lat': 25.7617, 'center_lon': -80.1918, 'radius_km': 100,
        'zip_prefixes': ['330', '331', '332', '333', '334', '335', '336', '337', '338', '339', '340', '341'],
    },
    'san_francisco': {
        'name': 'San Francisco', 'state': 'CA',
        'center_lat': 37.7749, 'center_lon': -122.4194, 'radius_km': 100,
        'zip_prefixes': ['940', '941', '942', '943', '944', '945', '946', '947', '948', '949', '950', '951'],
    }
}

# Revenue per employee by industry ($1000s)
REVENUE_PER_EMPLOYEE = {
    '11': 150, '21': 800, '22': 600, '23': 200, '31': 350, '32': 350, '33': 350,
    '42': 500, '44': 250, '45': 250, '48': 200, '49': 200,
    '51': 500, '52': 600, '53': 300, '54': 180, '55': 500,  # Power industries
    '56': 100, '61': 80, '62': 100, '71': 150, '72': 50, '81': 80, '99': 100,
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def z_score(series):
    std = series.std()
    if std == 0:
        return pd.Series([0] * len(series), index=series.index)
    return (series - series.mean()) / std

def normalize_minmax(series):
    min_val, max_val = series.min(), series.max()
    if max_val == min_val:
        return pd.Series([0.5] * len(series), index=series.index)
    return (series - min_val) / (max_val - min_val)

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    return R * 2 * np.arcsin(np.sqrt(a))

# =============================================================================
# LOAD ALL ZIP CODES DATA (from wealth analysis cache)
# =============================================================================
def load_all_zips_data():
    """Load ALL ZIP codes from all cities (not just top 10%)"""
    print("\n" + "="*70)
    print("LOADING ALL ZIP CODES DATA")
    print("="*70)
    
    # Load from cached geometry
    cache_geometry = os.path.join(DATA_DIR, 'cache_geometry.gpkg')
    if os.path.exists(cache_geometry):
        import geopandas as gpd
        gdf = gpd.read_file(cache_geometry)
        gdf['zipcode'] = gdf['zipcode'].astype(str).str.zfill(5)
        print(f"  Loaded geometry: {len(gdf)} ZIP codes")
    else:
        print("  [!] Geometry cache not found")
        return None
    
    # Load Census data
    cache_census = os.path.join(DATA_DIR, 'cache_census_all.csv')
    if os.path.exists(cache_census):
        df_census = pd.read_csv(cache_census, dtype={'zipcode': str})
        print(f"  Loaded Census: {len(df_census)} records")
    else:
        df_census = pd.DataFrame()
    
    # Filter to our cities and calculate centroids
    all_city_data = []
    
    for city_key, config in CITIES.items():
        gdf_city = gdf[gdf['zipcode'].str[:3].isin(config['zip_prefixes'])].copy()
        
        # Calculate distance to city center
        gdf_city['centroid_lat'] = gdf_city.geometry.centroid.y
        gdf_city['centroid_lon'] = gdf_city.geometry.centroid.x
        gdf_city['dist_to_center'] = gdf_city.apply(
            lambda r: haversine_distance(r['centroid_lat'], r['centroid_lon'], 
                                        config['center_lat'], config['center_lon']), axis=1
        )
        gdf_city = gdf_city[gdf_city['dist_to_center'] <= config['radius_km']].copy()
        
        gdf_city['city_key'] = city_key
        gdf_city['city_name'] = config['name']
        
        # Merge with census
        if not df_census.empty:
            gdf_city = gdf_city.merge(
                df_census[['zipcode', 'Households_200k', 'Population']], 
                on='zipcode', how='left'
            )
        
        all_city_data.append(gdf_city)
        print(f"    {config['name']}: {len(gdf_city)} ZIP codes")
    
    df_all = pd.concat(all_city_data, ignore_index=True)
    print(f"\n  TOTAL: {len(df_all)} ZIP codes across all cities")
    
    return df_all

# =============================================================================
# GENERATE SYNTHETIC CORPORATE DATA FOR ALL ZIPS
# =============================================================================
def generate_corporate_data(df_all):
    """Generate synthetic corporate data for ALL ZIP codes"""
    print("\n" + "="*70)
    print("GENERATING CORPORATE DATA FOR ALL ZIP CODES")
    print("="*70)
    
    naics_codes = list(REVENUE_PER_EMPLOYEE.keys())
    all_data = []
    
    for _, row in df_all.iterrows():
        zipcode = row['zipcode']
        city_key = row['city_key']
        population = row.get('Population', 10000) or 10000
        hh200k = row.get('Households_200k', 100) or 100
        area = row.get('Area_km2', 10) or 10
        
        # Base corporate activity scales with population density
        pop_density = population / area
        base_establishments = max(20, int(population / 200))
        base_employment = max(100, int(population / 10))
        
        # City-specific adjustments
        is_la = city_key == 'los_angeles'
        is_ny = city_key == 'new_york'
        is_sf = city_key == 'san_francisco'
        is_chicago = city_key == 'chicago'
        
        for naics in naics_codes:
            industry_weight = 1.0
            
            # Power industries more in dense/wealthy areas
            if naics in POWER_INDUSTRIES:
                industry_weight = 1 + (hh200k / 1000) * 0.5
            
            # Entertainment/Media concentration
            if naics in ['51', '71']:
                if is_la:
                    industry_weight *= 3.0  # Hollywood
                elif is_ny:
                    industry_weight *= 2.5  # Media/Broadway
                elif is_sf:
                    industry_weight *= 2.0  # Tech/Streaming
            
            # Finance concentration
            if naics == '52':
                if is_ny:
                    industry_weight *= 3.0  # Wall Street
                elif is_chicago:
                    industry_weight *= 1.5  # CME/Financial district
                elif is_sf:
                    industry_weight *= 1.3  # VC/Tech finance
            
            # Random variation
            variation = np.random.uniform(0.3, 1.7)
            
            estab = int(base_establishments * 0.04 * industry_weight * variation)
            emp = int(base_employment * 0.04 * industry_weight * variation)
            payroll = int(emp * np.random.uniform(45, 85) * 1000)
            
            if estab > 0:
                all_data.append({
                    'zipcode': zipcode,
                    'NAICS2': naics,
                    'establishments': estab,
                    'employment': emp,
                    'annual_payroll': payroll
                })
    
    df_corp = pd.DataFrame(all_data)
    print(f"  Generated {len(df_corp)} industry-ZIP records")
    
    return df_corp

# =============================================================================
# CALCULATE CORPORATE METRICS
# =============================================================================
def calculate_corporate_metrics(df_zbp, df_all):
    """Calculate corporate metrics for ALL ZIP codes"""
    print("\n" + "="*70)
    print("CALCULATING CORPORATE METRICS")
    print("="*70)
    
    # Aggregate by ZIP
    df_total = df_zbp.groupby('zipcode').agg({
        'establishments': 'sum',
        'employment': 'sum',
        'annual_payroll': 'sum'
    }).reset_index()
    df_total.columns = ['zipcode', 'Total_Establishments', 'Total_Employment', 'Total_Payroll']
    
    # Average firm size
    df_total['Avg_Firm_Size'] = df_total['Total_Employment'] / df_total['Total_Establishments'].replace(0, np.nan)
    df_total['Avg_Firm_Size'] = df_total['Avg_Firm_Size'].fillna(0)
    
    # Power industries
    df_power = df_zbp[df_zbp['NAICS2'].isin(POWER_INDUSTRIES)].groupby('zipcode').agg({
        'establishments': 'sum', 'employment': 'sum', 'annual_payroll': 'sum'
    }).reset_index()
    df_power.columns = ['zipcode', 'Power_Establishments', 'Power_Employment', 'Power_Payroll']
    
    df_total = df_total.merge(df_power, on='zipcode', how='left')
    df_total[['Power_Establishments', 'Power_Employment', 'Power_Payroll']] = \
        df_total[['Power_Establishments', 'Power_Employment', 'Power_Payroll']].fillna(0)
    
    # Entertainment/Media
    df_ent = df_zbp[df_zbp['NAICS2'].isin(ENTERTAINMENT_INDUSTRIES)].groupby('zipcode').agg({
        'establishments': 'sum', 'employment': 'sum'
    }).reset_index()
    df_ent.columns = ['zipcode', 'Entertainment_Establishments', 'Entertainment_Employment']
    
    df_total = df_total.merge(df_ent, on='zipcode', how='left')
    df_total[['Entertainment_Establishments', 'Entertainment_Employment']] = \
        df_total[['Entertainment_Establishments', 'Entertainment_Employment']].fillna(0)
    
    # Shares
    df_total['Power_Employment_Share'] = df_total['Power_Employment'] / df_total['Total_Employment'].replace(0, np.nan)
    df_total['Entertainment_Employment_Share'] = df_total['Entertainment_Employment'] / df_total['Total_Employment'].replace(0, np.nan)
    df_total[['Power_Employment_Share', 'Entertainment_Employment_Share']] = \
        df_total[['Power_Employment_Share', 'Entertainment_Employment_Share']].fillna(0)
    
    # Estimate revenue
    revenue_by_zip = {}
    for zipcode in df_total['zipcode'].unique():
        df_zip = df_zbp[df_zbp['zipcode'] == zipcode]
        total_rev = sum(
            row['employment'] * REVENUE_PER_EMPLOYEE.get(row['NAICS2'], 100) * 1000
            for _, row in df_zip.iterrows()
        )
        revenue_by_zip[zipcode] = total_rev
    
    df_total['Estimated_Revenue'] = df_total['zipcode'].map(revenue_by_zip)
    
    # Merge with city info
    df_total = df_total.merge(
        df_all[['zipcode', 'city_key', 'city_name', 'Households_200k', 'Population', 'Area_km2']],
        on='zipcode', how='left'
    )
    
    # Corporate Power Index
    df_total['z_revenue'] = z_score(df_total['Estimated_Revenue'].clip(lower=1))
    df_total['z_employment'] = z_score(df_total['Total_Employment'].clip(lower=1))
    df_total['z_payroll'] = z_score(df_total['Total_Payroll'].clip(lower=1))
    df_total['z_firm_size'] = z_score(df_total['Avg_Firm_Size'].clip(lower=1))
    df_total['z_power_share'] = z_score(df_total['Power_Employment_Share'].clip(lower=0.001))
    
    df_total['Corp_Power_Index_Raw'] = (
        0.30 * df_total['z_revenue'] +
        0.20 * df_total['z_employment'] +
        0.10 * df_total['z_payroll'] +
        0.20 * df_total['z_firm_size'] +
        0.20 * df_total['z_power_share']
    )
    df_total['Corp_Power_Index'] = normalize_minmax(df_total['Corp_Power_Index_Raw']) * 100
    
    print(f"\n  Processed {len(df_total)} ZIP codes")
    print(f"  Total Establishments: {df_total['Total_Establishments'].sum():,.0f}")
    print(f"  Total Employment: {df_total['Total_Employment'].sum():,.0f}")
    print(f"  Total Revenue: ${df_total['Estimated_Revenue'].sum()/1e9:.1f}B")
    
    return df_total

# =============================================================================
# GENERATE CITY STATISTICS
# =============================================================================
def generate_city_statistics(df_corp):
    """Generate statistics comparing ALL ZIP codes vs TOP corporate ZIPs"""
    print("\n" + "="*70)
    print("CITY-LEVEL CORPORATE STATISTICS (ALL ZIP CODES)")
    print("="*70)
    
    # Top 10% corporate ZIPs by Corp Power Index
    threshold_90 = df_corp['Corp_Power_Index'].quantile(0.90)
    df_top_corp = df_corp[df_corp['Corp_Power_Index'] >= threshold_90]
    
    print(f"\n  Corporate Power Index 90th percentile: {threshold_90:.1f}")
    print(f"  Top 10% Corporate ZIPs: {len(df_top_corp)} of {len(df_corp)}")
    
    city_stats = []
    
    for city_key in df_corp['city_key'].unique():
        df_city_all = df_corp[df_corp['city_key'] == city_key]
        df_city_top = df_top_corp[df_top_corp['city_key'] == city_key]
        
        if len(df_city_all) == 0:
            continue
        
        city_name = df_city_all['city_name'].iloc[0]
        
        stats = {
            'city_key': city_key,
            'city_name': city_name,
            
            # ALL ZIP codes
            'all_zips': len(df_city_all),
            'all_establishments': df_city_all['Total_Establishments'].sum(),
            'all_employment': df_city_all['Total_Employment'].sum(),
            'all_revenue': df_city_all['Estimated_Revenue'].sum(),
            'all_power_share': df_city_all['Power_Employment'].sum() / df_city_all['Total_Employment'].sum() * 100,
            'all_entertainment_share': df_city_all['Entertainment_Employment'].sum() / df_city_all['Total_Employment'].sum() * 100,
            'all_mean_corp_index': df_city_all['Corp_Power_Index'].mean(),
            
            # TOP 10% Corporate ZIPs
            'top_zips': len(df_city_top),
            'top_establishments': df_city_top['Total_Establishments'].sum() if len(df_city_top) > 0 else 0,
            'top_employment': df_city_top['Total_Employment'].sum() if len(df_city_top) > 0 else 0,
            'top_revenue': df_city_top['Estimated_Revenue'].sum() if len(df_city_top) > 0 else 0,
            'top_pct_of_city_emp': df_city_top['Total_Employment'].sum() / df_city_all['Total_Employment'].sum() * 100 if len(df_city_top) > 0 else 0,
            
            # Household metrics (for comparison)
            'total_hh200k': df_city_all['Households_200k'].sum(),
            'total_population': df_city_all['Population'].sum(),
        }
        
        city_stats.append(stats)
    
    df_city_stats = pd.DataFrame(city_stats).sort_values('all_revenue', ascending=False)
    
    # Print ALL ZIPs table
    print("\n" + "="*100)
    print("ALL ZIP CODES - CORPORATE ACTIVITY")
    print("="*100)
    print(f"| {'City':<15} | {'ZIPs':>5} | {'Establishments':>12} | {'Employment':>12} | {'Revenue ($B)':>12} | {'Power %':>8} | {'Entertain %':>10} |")
    print("-"*100)
    
    for _, row in df_city_stats.iterrows():
        print(f"| {row['city_name']:<15} | {row['all_zips']:>5} | {row['all_establishments']:>12,.0f} | {row['all_employment']:>12,.0f} | {row['all_revenue']/1e9:>12.1f} | {row['all_power_share']:>7.1f}% | {row['all_entertainment_share']:>9.1f}% |")
    
    print("-"*100)
    total_emp = df_corp['Total_Employment'].sum()
    total_rev = df_corp['Estimated_Revenue'].sum()
    total_power = df_corp['Power_Employment'].sum()
    total_ent = df_corp['Entertainment_Employment'].sum()
    print(f"| {'NATIONAL':<15} | {len(df_corp):>5} | {df_corp['Total_Establishments'].sum():>12,.0f} | {total_emp:>12,.0f} | {total_rev/1e9:>12.1f} | {total_power/total_emp*100:>7.1f}% | {total_ent/total_emp*100:>9.1f}% |")
    
    # Print TOP 10% Corporate table
    print("\n" + "="*100)
    print("TOP 10% CORPORATE ZIP CODES (by Corp Power Index)")
    print("="*100)
    print(f"| {'City':<15} | {'Top ZIPs':>8} | {'Employment':>12} | {'Revenue ($B)':>12} | {'% of City Emp':>13} |")
    print("-"*100)
    
    for _, row in df_city_stats.iterrows():
        print(f"| {row['city_name']:<15} | {row['top_zips']:>8} | {row['top_employment']:>12,.0f} | {row['top_revenue']/1e9:>12.1f} | {row['top_pct_of_city_emp']:>12.1f}% |")
    
    print("-"*100)
    
    return df_city_stats, df_top_corp, threshold_90

# =============================================================================
# CROSS-REFERENCE: CORPORATE vs HOUSEHOLD WEALTH
# =============================================================================
def cross_reference_analysis(df_corp, df_city_stats):
    """Compare corporate power with household wealth"""
    print("\n" + "="*70)
    print("CROSS-REFERENCE: CORPORATE vs HOUSEHOLD WEALTH")
    print("="*70)
    
    # Load household wealth data (top 10%)
    wealth_file = os.path.join(BASE_DIR, 'top10_richest_data.csv')
    if not os.path.exists(wealth_file):
        print("  [!] Household wealth data not found")
        return
    
    df_wealth = pd.read_csv(wealth_file, dtype={'zipcode': str})
    wealthy_zips = set(df_wealth['zipcode'].unique())
    
    # Top 10% corporate ZIPs
    threshold_90 = df_corp['Corp_Power_Index'].quantile(0.90)
    top_corp_zips = set(df_corp[df_corp['Corp_Power_Index'] >= threshold_90]['zipcode'].unique())
    
    # Find overlaps
    overlap_zips = wealthy_zips & top_corp_zips
    only_wealthy = wealthy_zips - top_corp_zips
    only_corporate = top_corp_zips - wealthy_zips
    
    print(f"\n  TOP 10% Wealthy Household ZIPs: {len(wealthy_zips)}")
    print(f"  TOP 10% Corporate Power ZIPs: {len(top_corp_zips)}")
    print(f"  OVERLAP (Both): {len(overlap_zips)} ({len(overlap_zips)/len(wealthy_zips)*100:.1f}% of wealthy)")
    print(f"  Only Wealthy (not top corporate): {len(only_wealthy)}")
    print(f"  Only Corporate (not top wealthy): {len(only_corporate)}")
    
    # By city
    print("\n" + "-"*90)
    print(f"| {'City':<15} | {'Wealthy ZIPs':>12} | {'Corp ZIPs':>10} | {'Overlap':>8} | {'Overlap %':>10} | {'Only Wealth':>11} | {'Only Corp':>10} |")
    print("-"*90)
    
    for city_key in df_corp['city_key'].unique():
        city_name = CITIES[city_key]['name']
        
        city_wealthy = set(df_wealth[df_wealth['city_key'] == city_key]['zipcode'].unique())
        city_corp = set(df_corp[(df_corp['city_key'] == city_key) & (df_corp['Corp_Power_Index'] >= threshold_90)]['zipcode'].unique())
        
        city_overlap = city_wealthy & city_corp
        city_only_w = city_wealthy - city_corp
        city_only_c = city_corp - city_wealthy
        
        overlap_pct = len(city_overlap) / len(city_wealthy) * 100 if len(city_wealthy) > 0 else 0
        
        print(f"| {city_name:<15} | {len(city_wealthy):>12} | {len(city_corp):>10} | {len(city_overlap):>8} | {overlap_pct:>9.1f}% | {len(city_only_w):>11} | {len(city_only_c):>10} |")
    
    print("-"*90)
    
    # Export overlap analysis
    overlap_data = df_corp[df_corp['zipcode'].isin(overlap_zips)].copy()
    overlap_data = overlap_data.merge(
        df_wealth[['zipcode', 'Geometric_Score', 'IRS_Norm', 'AGI_per_return']],
        on='zipcode', how='left'
    )
    overlap_data['Wealth_Score'] = overlap_data['Geometric_Score'] * 100
    
    return overlap_zips, only_wealthy, only_corporate, overlap_data

# =============================================================================
# CREATE VISUALIZATIONS
# =============================================================================
def create_visualizations(df_corp, df_city_stats, overlap_data):
    """Create comparison visualizations"""
    print("\n" + "="*70)
    print("CREATING VISUALIZATIONS")
    print("="*70)
    
    colors = {'new_york': '#1f77b4', 'los_angeles': '#ff7f0e', 'chicago': '#2ca02c', 
              'dallas': '#d62728', 'houston': '#9467bd', 'miami': '#8c564b', 'san_francisco': '#e377c2'}
    
    # Figure 1: ALL ZIPs distribution comparison
    fig1, axes1 = plt.subplots(2, 2, figsize=(14, 12))
    fig1.suptitle('Corporate Analysis - ALL ZIP Codes by City', fontsize=14, fontweight='bold')
    
    # 1. Corporate Power Index - ALL ZIPs
    ax1 = axes1[0, 0]
    for city_key in df_corp['city_key'].unique():
        df_city = df_corp[df_corp['city_key'] == city_key]
        if len(df_city) > 10:
            data = df_city['Corp_Power_Index'].dropna()
            if data.std() > 0:
                kde = gaussian_kde(data)
                x_range = np.linspace(0, 100, 100)
                ax1.plot(x_range, kde(x_range), label=f"{CITIES[city_key]['name']} (n={len(df_city)})",
                        color=colors.get(city_key, 'gray'), linewidth=2)
                ax1.fill_between(x_range, kde(x_range), alpha=0.2, color=colors.get(city_key, 'gray'))
    ax1.set_xlabel('Corporate Power Index')
    ax1.set_ylabel('Density')
    ax1.set_title('Corporate Power Index (ALL ZIPs)')
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)
    
    # 2. Entertainment Share - ALL ZIPs
    ax2 = axes1[0, 1]
    for city_key in df_corp['city_key'].unique():
        df_city = df_corp[df_corp['city_key'] == city_key]
        if len(df_city) > 10:
            data = (df_city['Entertainment_Employment_Share'] * 100).dropna()
            if data.std() > 0:
                kde = gaussian_kde(data)
                x_range = np.linspace(0, max(30, data.max()), 100)
                ax2.plot(x_range, kde(x_range), label=CITIES[city_key]['name'],
                        color=colors.get(city_key, 'gray'), linewidth=2)
                ax2.fill_between(x_range, kde(x_range), alpha=0.2, color=colors.get(city_key, 'gray'))
    ax2.set_xlabel('Entertainment/Media Employment Share (%)')
    ax2.set_ylabel('Density')
    ax2.set_title('Entertainment/Media (TV, Film, Streaming) - ALL ZIPs')
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)
    
    # 3. City comparison bar chart
    ax3 = axes1[1, 0]
    df_sorted = df_city_stats.sort_values('all_revenue', ascending=True)
    y_pos = np.arange(len(df_sorted))
    
    bars = ax3.barh(y_pos, df_sorted['all_revenue'] / 1e9, 
                    color=[colors.get(k, 'gray') for k in df_sorted['city_key']])
    ax3.set_yticks(y_pos)
    ax3.set_yticklabels(df_sorted['city_name'])
    ax3.set_xlabel('Estimated Revenue ($B)')
    ax3.set_title('Total Corporate Revenue by City (ALL ZIPs)')
    ax3.grid(True, alpha=0.3, axis='x')
    
    # 4. Employment comparison
    ax4 = axes1[1, 1]
    df_sorted = df_city_stats.sort_values('all_employment', ascending=True)
    y_pos = np.arange(len(df_sorted))
    
    bars = ax4.barh(y_pos, df_sorted['all_employment'] / 1e6,
                    color=[colors.get(k, 'gray') for k in df_sorted['city_key']])
    ax4.set_yticks(y_pos)
    ax4.set_yticklabels(df_sorted['city_name'])
    ax4.set_xlabel('Total Employment (Millions)')
    ax4.set_title('Total Corporate Employment by City (ALL ZIPs)')
    ax4.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    plt.savefig('corporate_full_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("  [OK] corporate_full_analysis.png")
    
    # Figure 2: Corporate vs Wealth comparison
    if overlap_data is not None and len(overlap_data) > 0:
        fig2, axes2 = plt.subplots(1, 2, figsize=(14, 6))
        fig2.suptitle('Corporate Power vs Household Wealth - Overlap Analysis', fontsize=14, fontweight='bold')
        
        # Scatter: Corp Index vs Wealth Score (overlap ZIPs only)
        ax1 = axes2[0]
        for city_key in overlap_data['city_key'].unique():
            df_city = overlap_data[overlap_data['city_key'] == city_key]
            ax1.scatter(df_city['Wealth_Score'], df_city['Corp_Power_Index'],
                       alpha=0.6, label=CITIES[city_key]['name'], 
                       c=colors.get(city_key, 'gray'), s=50)
        ax1.set_xlabel('Household Wealth Score (%)')
        ax1.set_ylabel('Corporate Power Index')
        ax1.set_title(f'Overlap ZIPs: Corporate vs Wealth (n={len(overlap_data)})')
        ax1.legend(fontsize=8)
        ax1.grid(True, alpha=0.3)
        
        # Correlation by city
        ax2 = axes2[1]
        corr_data = []
        for city_key in overlap_data['city_key'].unique():
            df_city = overlap_data[overlap_data['city_key'] == city_key]
            if len(df_city) > 3:
                corr = df_city['Corp_Power_Index'].corr(df_city['Wealth_Score'])
                corr_data.append({'city': CITIES[city_key]['name'], 'corr': corr, 'city_key': city_key})
        
        if corr_data:
            df_corr = pd.DataFrame(corr_data).sort_values('corr', ascending=True)
            colors_bar = ['#d62728' if c < 0 else '#2ca02c' for c in df_corr['corr']]
            ax2.barh(df_corr['city'], df_corr['corr'], color=colors_bar)
            ax2.axvline(x=0, color='black', linewidth=0.5)
            ax2.set_xlabel('Correlation Coefficient')
            ax2.set_title('Corp-Wealth Correlation (Overlap ZIPs)')
            ax2.set_xlim(-1, 1)
            ax2.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        plt.savefig('corporate_vs_wealth_overlap.png', dpi=150, bbox_inches='tight')
        plt.close()
        print("  [OK] corporate_vs_wealth_overlap.png")

# =============================================================================
# EXPORT DATA
# =============================================================================
def export_data(df_corp, df_city_stats, overlap_data):
    """Export all data to CSV"""
    print("\n" + "="*70)
    print("EXPORTING DATA")
    print("="*70)
    
    # All ZIPs corporate data
    export_cols = ['zipcode', 'city_key', 'city_name', 
                   'Total_Establishments', 'Total_Employment', 'Total_Payroll', 'Estimated_Revenue',
                   'Avg_Firm_Size', 'Power_Employment', 'Power_Employment_Share',
                   'Entertainment_Employment', 'Entertainment_Employment_Share',
                   'Corp_Power_Index', 'Households_200k', 'Population']
    df_corp[export_cols].to_csv('corporate_all_zips.csv', index=False)
    print("  [OK] corporate_all_zips.csv")
    
    # City stats
    df_city_stats.to_csv('corporate_city_stats_full.csv', index=False)
    print("  [OK] corporate_city_stats_full.csv")
    
    # Overlap data
    if overlap_data is not None and len(overlap_data) > 0:
        overlap_data.to_csv('corporate_wealth_overlap.csv', index=False)
        print("  [OK] corporate_wealth_overlap.csv")

# =============================================================================
# MAIN
# =============================================================================
def main():
    print("\n" + "="*70)
    print("CORPORATE POWER INDEX - FULL CITY ANALYSIS")
    print("Analyzing ALL ZIP codes (not just top 10% wealthy)")
    print("="*70)
    
    start_time = datetime.now()
    
    # Load ALL ZIP codes
    df_all = load_all_zips_data()
    if df_all is None:
        print("\n[ERROR] Could not load ZIP code data")
        return
    
    # Generate corporate data
    df_zbp = generate_corporate_data(df_all)
    
    # Calculate metrics
    df_corp = calculate_corporate_metrics(df_zbp, df_all)
    
    # City statistics
    df_city_stats, df_top_corp, threshold = generate_city_statistics(df_corp)
    
    # Cross-reference with wealth
    result = cross_reference_analysis(df_corp, df_city_stats)
    if result:
        overlap_zips, only_wealthy, only_corporate, overlap_data = result
    else:
        overlap_data = None
    
    # Visualizations
    create_visualizations(df_corp, df_city_stats, overlap_data)
    
    # Export
    export_data(df_corp, df_city_stats, overlap_data)
    
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n" + "="*70)
    print(f"COMPLETED in {elapsed:.1f}s")
    print("="*70)

if __name__ == '__main__':
    main()

