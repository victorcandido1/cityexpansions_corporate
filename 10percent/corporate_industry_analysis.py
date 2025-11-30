# -*- coding: utf-8 -*-
"""
CORPORATE INDUSTRY BREAKDOWN ANALYSIS
=====================================
Detailed analysis of Power Industries by type:
- Finance & Insurance (NAICS 52)
- Information/Media/Streaming (NAICS 51)
- Professional Services (NAICS 54)
- Real Estate (NAICS 53)
- Management of Companies (NAICS 55)
- Entertainment & Arts (NAICS 71)

Box plots, distributions, and revenue breakdown by city.
"""

import pandas as pd
import numpy as np
import geopandas as gpd
import os
import json
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from scipy.stats import gaussian_kde

# =============================================================================
# CONFIGURATION
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'new_folder')

# Power Industries - detailed breakdown
POWER_INDUSTRIES = {
    '51': {'name': 'Information/Media/Streaming', 'short': 'Media/Tech', 'color': '#e41a1c', 'rev_per_emp': 500},
    '52': {'name': 'Finance & Insurance', 'short': 'Finance', 'color': '#377eb8', 'rev_per_emp': 600},
    '53': {'name': 'Real Estate', 'short': 'Real Estate', 'color': '#4daf4a', 'rev_per_emp': 300},
    '54': {'name': 'Professional Services', 'short': 'Professional', 'color': '#984ea3', 'rev_per_emp': 180},
    '55': {'name': 'Management of Companies', 'short': 'Management', 'color': '#ff7f00', 'rev_per_emp': 500},
    '71': {'name': 'Entertainment & Arts', 'short': 'Entertainment', 'color': '#ffff33', 'rev_per_emp': 150},
}

# All industries for comparison
ALL_INDUSTRIES = {
    '11': {'name': 'Agriculture', 'rev_per_emp': 150},
    '21': {'name': 'Mining', 'rev_per_emp': 800},
    '22': {'name': 'Utilities', 'rev_per_emp': 600},
    '23': {'name': 'Construction', 'rev_per_emp': 200},
    '31': {'name': 'Manufacturing', 'rev_per_emp': 350},
    '42': {'name': 'Wholesale Trade', 'rev_per_emp': 500},
    '44': {'name': 'Retail Trade', 'rev_per_emp': 250},
    '48': {'name': 'Transportation', 'rev_per_emp': 200},
    '51': {'name': 'Information/Media', 'rev_per_emp': 500},
    '52': {'name': 'Finance', 'rev_per_emp': 600},
    '53': {'name': 'Real Estate', 'rev_per_emp': 300},
    '54': {'name': 'Professional', 'rev_per_emp': 180},
    '55': {'name': 'Management', 'rev_per_emp': 500},
    '56': {'name': 'Admin Services', 'rev_per_emp': 100},
    '61': {'name': 'Education', 'rev_per_emp': 80},
    '62': {'name': 'Health Care', 'rev_per_emp': 100},
    '71': {'name': 'Entertainment', 'rev_per_emp': 150},
    '72': {'name': 'Accommodation/Food', 'rev_per_emp': 50},
    '81': {'name': 'Other Services', 'rev_per_emp': 80},
}

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
                         '070', '071', '072', '073', '074', '075', '076', '077', '078', '079'],
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
        'zip_prefixes': ['330', '331', '332', '333', '334', '335', '336', '337', '338', '339'],
    },
    'san_francisco': {
        'name': 'San Francisco', 'state': 'CA',
        'center_lat': 37.7749, 'center_lon': -122.4194, 'radius_km': 100,
        'zip_prefixes': ['940', '941', '942', '943', '944', '945', '946', '947', '948', '949'],
    }
}

CITY_COLORS = {
    'new_york': '#1f77b4', 'los_angeles': '#ff7f0e', 'chicago': '#2ca02c', 
    'dallas': '#d62728', 'houston': '#9467bd', 'miami': '#8c564b', 'san_francisco': '#e377c2'
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    return R * 2 * np.arcsin(np.sqrt(a))

# =============================================================================
# LOAD ALL ZIP CODES
# =============================================================================
def load_all_zips():
    """Load ALL ZIP codes from geometry cache"""
    print("\n" + "="*70)
    print("LOADING ALL ZIP CODES")
    print("="*70)
    
    cache_file = os.path.join(DATA_DIR, 'cache_geometry.gpkg')
    if not os.path.exists(cache_file):
        print(f"  [!] Cache not found: {cache_file}")
        return None
    
    gdf = gpd.read_file(cache_file)
    gdf['zipcode'] = gdf['ZCTA5CE20'].astype(str).str.zfill(5)
    gdf['centroid_lat'] = gdf.geometry.centroid.y
    gdf['centroid_lon'] = gdf.geometry.centroid.x
    gdf['Area_km2'] = gdf['ALAND20'] / 1e6  # Convert to km²
    
    print(f"  Loaded {len(gdf)} ZIP codes from geometry")
    
    # Filter to our cities
    all_city_data = []
    for city_key, config in CITIES.items():
        gdf_city = gdf[gdf['zipcode'].str[:3].isin(config['zip_prefixes'])].copy()
        gdf_city['dist_to_center'] = gdf_city.apply(
            lambda r: haversine_distance(r['centroid_lat'], r['centroid_lon'],
                                        config['center_lat'], config['center_lon']), axis=1
        )
        gdf_city = gdf_city[gdf_city['dist_to_center'] <= config['radius_km']].copy()
        gdf_city['city_key'] = city_key
        gdf_city['city_name'] = config['name']
        
        all_city_data.append(gdf_city[['zipcode', 'city_key', 'city_name', 'centroid_lat', 'centroid_lon', 'Area_km2']])
        print(f"    {config['name']}: {len(gdf_city)} ZIP codes")
    
    df_all = pd.concat(all_city_data, ignore_index=True)
    print(f"\n  TOTAL: {len(df_all)} ZIP codes")
    
    return df_all

# =============================================================================
# GENERATE INDUSTRY DATA
# =============================================================================
def generate_industry_data(df_all):
    """Generate synthetic industry data by ZIP code"""
    print("\n" + "="*70)
    print("GENERATING INDUSTRY DATA")
    print("="*70)
    
    all_data = []
    
    for _, row in df_all.iterrows():
        zipcode = row['zipcode']
        city_key = row['city_key']
        area = row.get('Area_km2', 10) or 10
        
        # Base activity scales with area (proxy for development)
        base_establishments = max(10, int(area * 5))
        base_employment = max(50, int(area * 50))
        
        # City-specific multipliers for power industries
        city_multipliers = {
            'new_york': {'52': 3.5, '51': 2.5, '54': 2.0, '55': 2.5, '53': 1.5, '71': 2.0},
            'los_angeles': {'51': 3.5, '71': 3.0, '54': 1.8, '52': 1.2, '53': 1.5, '55': 1.0},
            'san_francisco': {'51': 3.0, '54': 2.5, '52': 1.5, '55': 1.5, '53': 1.3, '71': 1.5},
            'chicago': {'52': 2.0, '54': 1.8, '55': 1.5, '51': 1.2, '53': 1.3, '71': 1.0},
            'dallas': {'52': 1.5, '54': 1.5, '53': 1.5, '55': 1.3, '51': 1.0, '71': 0.8},
            'houston': {'21': 3.0, '52': 1.3, '54': 1.3, '53': 1.2, '55': 1.0, '51': 0.8, '71': 0.7},
            'miami': {'53': 2.0, '52': 1.5, '72': 2.0, '54': 1.2, '51': 1.0, '71': 1.2, '55': 0.8},
        }
        
        multipliers = city_multipliers.get(city_key, {})
        
        for naics, info in ALL_INDUSTRIES.items():
            mult = multipliers.get(naics, 1.0)
            variation = np.random.uniform(0.3, 1.7)
            
            estab = int(base_establishments * 0.05 * mult * variation)
            emp = int(base_employment * 0.05 * mult * variation)
            payroll = int(emp * np.random.uniform(45, 85) * 1000)
            revenue = emp * info['rev_per_emp'] * 1000
            
            if estab > 0:
                all_data.append({
                    'zipcode': zipcode,
                    'city_key': city_key,
                    'city_name': row['city_name'],
                    'NAICS2': naics,
                    'industry_name': info['name'],
                    'establishments': estab,
                    'employment': emp,
                    'payroll': payroll,
                    'revenue': revenue,
                    'is_power': naics in POWER_INDUSTRIES
                })
    
    df_industry = pd.DataFrame(all_data)
    print(f"  Generated {len(df_industry)} industry-ZIP records")
    
    return df_industry

# =============================================================================
# CALCULATE CITY INDUSTRY BREAKDOWN
# =============================================================================
def calculate_city_breakdown(df_industry):
    """Calculate industry breakdown by city"""
    print("\n" + "="*70)
    print("CALCULATING CITY INDUSTRY BREAKDOWN")
    print("="*70)
    
    # Aggregate by city and industry
    df_city_ind = df_industry.groupby(['city_key', 'city_name', 'NAICS2', 'industry_name', 'is_power']).agg({
        'establishments': 'sum',
        'employment': 'sum',
        'payroll': 'sum',
        'revenue': 'sum'
    }).reset_index()
    
    # Calculate totals per city
    city_totals = df_industry.groupby('city_key').agg({
        'employment': 'sum',
        'revenue': 'sum'
    }).reset_index()
    city_totals.columns = ['city_key', 'total_employment', 'total_revenue']
    
    df_city_ind = df_city_ind.merge(city_totals, on='city_key')
    df_city_ind['employment_share'] = df_city_ind['employment'] / df_city_ind['total_employment'] * 100
    df_city_ind['revenue_share'] = df_city_ind['revenue'] / df_city_ind['total_revenue'] * 100
    
    # Power industries only
    df_power = df_city_ind[df_city_ind['is_power']].copy()
    
    # Print summary
    print("\n" + "="*100)
    print("POWER INDUSTRIES REVENUE BREAKDOWN BY CITY")
    print("="*100)
    
    for city_key in CITIES.keys():
        city_data = df_power[df_power['city_key'] == city_key].sort_values('revenue', ascending=False)
        if len(city_data) == 0:
            continue
        
        city_name = CITIES[city_key]['name']
        total_power_rev = city_data['revenue'].sum()
        
        print(f"\n  {city_name.upper()}")
        print(f"  Total Power Industries Revenue: ${total_power_rev/1e9:.2f}B")
        print("  " + "-"*70)
        
        for _, row in city_data.iterrows():
            pct = row['revenue'] / total_power_rev * 100
            bar = "#" * int(pct / 2)
            print(f"    {row['industry_name']:<25} ${row['revenue']/1e9:>6.2f}B  {pct:>5.1f}% {bar}")
    
    return df_city_ind, df_power

# =============================================================================
# CREATE VISUALIZATIONS
# =============================================================================
def create_visualizations(df_industry, df_city_ind, df_power):
    """Create detailed visualizations"""
    print("\n" + "="*70)
    print("CREATING VISUALIZATIONS")
    print("="*70)
    
    # Figure 1: Power Industries Revenue Breakdown by City (Stacked Bar)
    fig1, ax1 = plt.subplots(figsize=(14, 8))
    fig1.suptitle('Power Industries Revenue Breakdown by City', fontsize=14, fontweight='bold')
    
    cities = list(CITIES.keys())
    city_names = [CITIES[c]['name'] for c in cities]
    x = np.arange(len(cities))
    width = 0.7
    
    # Stack data
    bottom = np.zeros(len(cities))
    
    for naics, info in POWER_INDUSTRIES.items():
        values = []
        for city_key in cities:
            city_data = df_power[(df_power['city_key'] == city_key) & (df_power['NAICS2'] == naics)]
            rev = city_data['revenue'].sum() / 1e9 if len(city_data) > 0 else 0
            values.append(rev)
        
        ax1.bar(x, values, width, label=info['name'], bottom=bottom, color=info['color'])
        bottom += values
    
    ax1.set_ylabel('Revenue ($B)')
    ax1.set_xlabel('City')
    ax1.set_xticks(x)
    ax1.set_xticklabels(city_names, rotation=45, ha='right')
    ax1.legend(loc='upper right', fontsize=9)
    ax1.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('power_industries_revenue_breakdown.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("  [OK] power_industries_revenue_breakdown.png")
    
    # Figure 2: Employment Share by Power Industry (100% Stacked)
    fig2, ax2 = plt.subplots(figsize=(14, 8))
    fig2.suptitle('Power Industries Employment Share by City (% of Total)', fontsize=14, fontweight='bold')
    
    bottom = np.zeros(len(cities))
    
    for naics, info in POWER_INDUSTRIES.items():
        values = []
        for city_key in cities:
            city_power = df_power[df_power['city_key'] == city_key]
            total_power_emp = city_power['employment'].sum()
            industry_data = city_power[city_power['NAICS2'] == naics]
            emp = industry_data['employment'].sum() if len(industry_data) > 0 else 0
            share = emp / total_power_emp * 100 if total_power_emp > 0 else 0
            values.append(share)
        
        ax2.bar(x, values, width, label=info['name'], bottom=bottom, color=info['color'])
        bottom += values
    
    ax2.set_ylabel('Share of Power Industries Employment (%)')
    ax2.set_xlabel('City')
    ax2.set_xticks(x)
    ax2.set_xticklabels(city_names, rotation=45, ha='right')
    ax2.set_ylim(0, 100)
    ax2.legend(loc='upper right', fontsize=9)
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('power_industries_employment_share.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("  [OK] power_industries_employment_share.png")
    
    # Figure 3: Box Plots - Revenue per ZIP by Industry
    fig3, axes3 = plt.subplots(2, 3, figsize=(16, 10))
    fig3.suptitle('Revenue Distribution per ZIP Code by Industry (Box Plots)', fontsize=14, fontweight='bold')
    
    for i, (naics, info) in enumerate(POWER_INDUSTRIES.items()):
        ax = axes3[i // 3, i % 3]
        
        # Get data for each city
        data_by_city = []
        city_labels = []
        
        for city_key in cities:
            city_data = df_industry[(df_industry['city_key'] == city_key) & (df_industry['NAICS2'] == naics)]
            if len(city_data) > 0:
                data_by_city.append(city_data['revenue'].values / 1e6)  # In millions
                city_labels.append(CITIES[city_key]['name'])
        
        if data_by_city:
            bp = ax.boxplot(data_by_city, patch_artist=True)
            for j, patch in enumerate(bp['boxes']):
                patch.set_facecolor(CITY_COLORS.get(cities[j], 'gray'))
                patch.set_alpha(0.6)
            ax.set_xticklabels(city_labels, rotation=45, ha='right', fontsize=8)
        
        ax.set_ylabel('Revenue per ZIP ($M)')
        ax.set_title(f"{info['short']}", fontsize=10, fontweight='bold', color=info['color'])
        ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('power_industries_boxplots.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("  [OK] power_industries_boxplots.png")
    
    # Figure 4: KDE Distributions by Industry
    fig4, axes4 = plt.subplots(2, 3, figsize=(16, 10))
    fig4.suptitle('Revenue Distribution Density by Industry (KDE)', fontsize=14, fontweight='bold')
    
    for i, (naics, info) in enumerate(POWER_INDUSTRIES.items()):
        ax = axes4[i // 3, i % 3]
        
        for city_key in cities:
            city_data = df_industry[(df_industry['city_key'] == city_key) & (df_industry['NAICS2'] == naics)]
            if len(city_data) > 5:
                data = city_data['revenue'].values / 1e6  # In millions
                if data.std() > 0:
                    try:
                        kde = gaussian_kde(data)
                        x_range = np.linspace(0, np.percentile(data, 95), 100)
                        ax.plot(x_range, kde(x_range), label=CITIES[city_key]['name'],
                               color=CITY_COLORS.get(city_key, 'gray'), linewidth=2)
                        ax.fill_between(x_range, kde(x_range), alpha=0.2, 
                                       color=CITY_COLORS.get(city_key, 'gray'))
                    except:
                        pass
        
        ax.set_xlabel('Revenue per ZIP ($M)')
        ax.set_ylabel('Density')
        ax.set_title(f"{info['short']}", fontsize=10, fontweight='bold', color=info['color'])
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('power_industries_kde.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("  [OK] power_industries_kde.png")
    
    # Figure 5: Heatmap - Industry Concentration by City
    fig5, ax5 = plt.subplots(figsize=(12, 8))
    fig5.suptitle('Power Industry Concentration by City (Employment Share %)', fontsize=14, fontweight='bold')
    
    # Create matrix
    matrix = []
    industry_names = []
    
    for naics, info in POWER_INDUSTRIES.items():
        row = []
        for city_key in cities:
            city_data = df_power[df_power['city_key'] == city_key]
            total_emp = city_data['employment'].sum()
            industry_emp = city_data[city_data['NAICS2'] == naics]['employment'].sum()
            share = industry_emp / total_emp * 100 if total_emp > 0 else 0
            row.append(share)
        matrix.append(row)
        industry_names.append(info['short'])
    
    matrix = np.array(matrix)
    
    im = ax5.imshow(matrix, cmap='YlOrRd', aspect='auto')
    
    ax5.set_xticks(np.arange(len(cities)))
    ax5.set_yticks(np.arange(len(industry_names)))
    ax5.set_xticklabels(city_names, rotation=45, ha='right')
    ax5.set_yticklabels(industry_names)
    
    # Add text annotations
    for i in range(len(industry_names)):
        for j in range(len(cities)):
            text = ax5.text(j, i, f"{matrix[i, j]:.1f}%", ha="center", va="center", 
                           color="white" if matrix[i, j] > matrix.max()/2 else "black", fontsize=9)
    
    cbar = ax5.figure.colorbar(im, ax=ax5)
    cbar.ax.set_ylabel('Employment Share (%)', rotation=-90, va="bottom")
    
    plt.tight_layout()
    plt.savefig('power_industries_heatmap.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("  [OK] power_industries_heatmap.png")
    
    # Figure 6: Radar/Spider Chart - City Industry Profiles
    fig6, axes6 = plt.subplots(2, 4, figsize=(18, 10), subplot_kw=dict(projection='polar'))
    fig6.suptitle('City Power Industry Profiles (Radar Charts)', fontsize=14, fontweight='bold')
    
    # Categories for radar
    categories = [info['short'] for naics, info in POWER_INDUSTRIES.items()]
    N = len(categories)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # Complete the loop
    
    for idx, city_key in enumerate(cities):
        if idx < 7:
            ax = axes6[idx // 4, idx % 4]
            
            values = []
            for naics in POWER_INDUSTRIES.keys():
                city_data = df_power[df_power['city_key'] == city_key]
                total_emp = city_data['employment'].sum()
                industry_emp = city_data[city_data['NAICS2'] == naics]['employment'].sum()
                share = industry_emp / total_emp * 100 if total_emp > 0 else 0
                values.append(share)
            
            values += values[:1]  # Complete the loop
            
            ax.plot(angles, values, 'o-', linewidth=2, color=CITY_COLORS.get(city_key, 'gray'))
            ax.fill(angles, values, alpha=0.25, color=CITY_COLORS.get(city_key, 'gray'))
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories, fontsize=7)
            ax.set_title(CITIES[city_key]['name'], fontsize=10, fontweight='bold', 
                        color=CITY_COLORS.get(city_key, 'gray'))
    
    # Hide last subplot if odd number
    if len(cities) < 8:
        axes6[1, 3].set_visible(False)
    
    plt.tight_layout()
    plt.savefig('power_industries_radar.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("  [OK] power_industries_radar.png")

# =============================================================================
# EXPORT DATA
# =============================================================================
def export_data(df_industry, df_city_ind, df_power):
    """Export data to CSV"""
    print("\n" + "="*70)
    print("EXPORTING DATA")
    print("="*70)
    
    # Industry by ZIP
    df_industry.to_csv('industry_by_zip_all.csv', index=False)
    print("  [OK] industry_by_zip_all.csv")
    
    # City industry breakdown
    df_city_ind.to_csv('industry_by_city.csv', index=False)
    print("  [OK] industry_by_city.csv")
    
    # Power industries summary
    df_power.to_csv('power_industries_by_city.csv', index=False)
    print("  [OK] power_industries_by_city.csv")

# =============================================================================
# MAIN
# =============================================================================
def main():
    print("\n" + "="*70)
    print("CORPORATE INDUSTRY BREAKDOWN ANALYSIS")
    print("Detailed Power Industries Analysis by City")
    print("="*70)
    
    start_time = datetime.now()
    
    # Load ZIP codes
    df_all = load_all_zips()
    if df_all is None:
        return
    
    # Generate industry data
    df_industry = generate_industry_data(df_all)
    
    # Calculate breakdowns
    df_city_ind, df_power = calculate_city_breakdown(df_industry)
    
    # Create visualizations
    create_visualizations(df_industry, df_city_ind, df_power)
    
    # Export data
    export_data(df_industry, df_city_ind, df_power)
    
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n" + "="*70)
    print(f"COMPLETED in {elapsed:.1f}s")
    print("="*70)

if __name__ == '__main__':
    main()

