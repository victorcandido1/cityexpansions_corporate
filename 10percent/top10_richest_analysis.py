# -*- coding: utf-8 -*-
"""
TOP 10% RICHEST ZIP CODES - NATIONAL ANALYSIS
==============================================
Filters the top 10% wealthiest zip codes across all cities
using MEDIAN-based metrics for robust analysis.

Creates:
- National map dashboard with top 10% regions
- Per-city breakdown maps
- Histograms and statistics
"""

import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
import branca.colormap as cm
from census import Census
import requests
import tempfile
import zipfile
import os
import numpy as np
import time
import math
import json
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# =============================================================================
# CONFIGURATION
# =============================================================================
CENSUS_API_KEY = "65e82b0208b07695a5ffa13b7b9f805462804467"
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, 'new_folder')
AIRPORTS_FILE = os.path.join(BASE_DIR, 'all-airport-data.xlsx')
IRS_FILE = os.path.join(BASE_DIR, '22zpallagi.csv')
CACHE_GEOMETRY = os.path.join(DATA_DIR, 'cache_geometry.gpkg')
CACHE_CENSUS = os.path.join(DATA_DIR, 'cache_census_all.csv')

# City configurations (same as main analysis)
CITIES = {
    'los_angeles': {
        'name': 'Los Angeles', 'state': 'CA',
        'center_lat': 34.0522, 'center_lon': -118.2437,
        'airport_code': 'LAX', 'airport_lat': 33.9416, 'airport_lon': -118.4085,
        'radius_km': 100,
        'zip_prefixes': ['900', '901', '902', '903', '904', '905', '906', '907', '908', '909', 
                         '910', '911', '912', '913', '914', '915', '916', '917', '918',
                         '920', '921', '922', '923', '924', '925', '926', '927', '928'],
    },
    'new_york': {
        'name': 'New York', 'state': 'NY',
        'center_lat': 40.7128, 'center_lon': -74.0060,
        'airport_code': 'JFK', 'airport_lat': 40.6413, 'airport_lon': -73.7781,
        'radius_km': 180,
        'zip_prefixes': ['100', '101', '102', '103', '104', '105', '106', '107', '108', '109',
                         '110', '111', '112', '113', '114', '115', '116', '117', '118', '119',
                         '070', '071', '072', '073', '074', '075', '076', '077', '078', '079',
                         '068', '069', '088', '089'],
    },
    'chicago': {
        'name': 'Chicago', 'state': 'IL',
        'center_lat': 41.8781, 'center_lon': -87.6298,
        'airport_code': 'ORD', 'airport_lat': 41.9742, 'airport_lon': -87.9073,
        'radius_km': 100,
        'zip_prefixes': ['600', '601', '602', '603', '604', '605', '606', '607', '608', '609'],
    },
    'dallas': {
        'name': 'Dallas', 'state': 'TX',
        'center_lat': 32.7767, 'center_lon': -96.7970,
        'airport_code': 'DFW', 'airport_lat': 32.8998, 'airport_lon': -97.0403,
        'radius_km': 100,
        'zip_prefixes': ['750', '751', '752', '753', '754', '755', '756', '757', '758', '759',
                         '760', '761', '762', '763'],
    },
    'houston': {
        'name': 'Houston', 'state': 'TX',
        'center_lat': 29.7604, 'center_lon': -95.3698,
        'airport_code': 'IAH', 'airport_lat': 29.9902, 'airport_lon': -95.3368,
        'radius_km': 100,
        'zip_prefixes': ['770', '771', '772', '773', '774', '775', '776', '777', '778', '779'],
    },
    'miami': {
        'name': 'Miami', 'state': 'FL',
        'center_lat': 25.7617, 'center_lon': -80.1918,
        'airport_code': 'MIA', 'airport_lat': 25.7959, 'airport_lon': -80.2870,
        'radius_km': 100,
        'zip_prefixes': ['330', '331', '332', '333', '334', '335', '336', '337', '338', '339', '340', '341'],
    },
    'san_francisco': {
        'name': 'San Francisco', 'state': 'CA',
        'center_lat': 37.7749, 'center_lon': -122.4194,
        'airport_code': 'SFO', 'airport_lat': 37.6213, 'airport_lon': -122.3790,
        'radius_km': 100,
        'zip_prefixes': ['940', '941', '942', '943', '944', '945', '946', '947', '948', '949', '950', '951'],
    }
}

# IRS columns
IRS_COLS = {
    'A00100': 'AGI', 'A00300': 'Interest_Income', 'A00600': 'Dividends',
    'A00650': 'Qualified_Dividends', 'A01000': 'Capital_Gains', 'A00900': 'Business_Income',
    'A01400': 'IRA_Distributions', 'A01700': 'Pensions_Annuities',
    'A18500': 'Real_Estate_Taxes', 'A19700': 'Charitable_Total', 'N1': 'Num_Returns',
}

IRS_WEIGHTS = {
    'AGI_per_return': 0.20, 'Capital_Gains_per_return': 0.20, 'Dividends_per_return': 0.15,
    'Interest_per_return': 0.10, 'Business_Income_per_return': 0.10,
    'Real_Estate_Taxes_per_return': 0.10, 'Charitable_per_return': 0.10, 'Retirement_per_return': 0.05,
}

# City colors
CITY_COLORS = {
    'new_york': '#1f77b4',
    'los_angeles': '#ff7f0e', 
    'san_francisco': '#2ca02c',
    'chicago': '#d62728',
    'dallas': '#9467bd',
    'houston': '#8c564b',
    'miami': '#e377c2'
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================
def haversine_distance(lat1, lon1, lat2, lon2):
    if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lat2):
        return float('inf')
    R = 6371
    dLat, dLon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def normalize(s):
    s = s.replace([np.inf, -np.inf], np.nan).fillna(0)
    if s.max() == s.min():
        return pd.Series(0.5, index=s.index)
    return (s - s.min()) / (s.max() - s.min())

def normalize_global(s, global_min, global_max):
    s = s.replace([np.inf, -np.inf], np.nan).fillna(0)
    if global_max == global_min:
        return pd.Series(0.5, index=s.index)
    return (s - global_min) / (global_max - global_min)

# =============================================================================
# LOAD DATA
# =============================================================================
def load_all_data():
    print("\n" + "="*70)
    print("LOADING DATA")
    print("="*70)
    
    # Geometry
    print("\n--- LOADING GEOMETRY ---")
    gdf = gpd.read_file(CACHE_GEOMETRY)
    zcta_col = [c for c in gdf.columns if 'ZCTA' in c.upper()][0]
    gdf = gdf.rename(columns={zcta_col: 'zipcode'})
    gdf['zipcode'] = gdf['zipcode'].astype(str).str.zfill(5)
    gdf['Area_km2'] = gdf['ALAND20'] / 1e6
    gdf = gdf.to_crs(epsg=4326)
    gdf['centroid_lat'] = gdf.geometry.centroid.y
    gdf['centroid_lon'] = gdf.geometry.centroid.x
    print(f"  Geometry: {len(gdf)} zip codes")
    
    # IRS
    print("\n--- LOADING IRS DATA ---")
    df_irs = pd.read_csv(IRS_FILE)
    df_irs['zipcode'] = df_irs['zipcode'].astype(str).str.zfill(5)
    print(f"  IRS: {len(df_irs)} records")
    
    # Census
    print("\n--- LOADING CENSUS DATA ---")
    df_censo = pd.read_csv(CACHE_CENSUS, dtype={'zipcode': str})
    for col in ['Households_200k', 'Population']:
        df_censo[col] = pd.to_numeric(df_censo[col], errors='coerce')
    df_censo['Households_200k'] = df_censo['Households_200k'].fillna(0)
    print(f"  Census: {len(df_censo)} records")
    
    # Airports
    print("\n--- LOADING AIRPORTS ---")
    try:
        df_airports = pd.read_excel(AIRPORTS_FILE)
        df_airports = df_airports[['Name', 'Facility Type', 'Ownership', 'Use', 'ARP Latitude DD', 'ARP Longitude DD', 'City', 'State Name', 'Loc Id']].dropna(subset=['ARP Latitude DD', 'ARP Longitude DD'])
        df_airports.columns = ['name', 'facility_type', 'ownership', 'use', 'lat', 'lon', 'city', 'state', 'code']
        
        # Map ownership and use labels
        ownership_map = {'PU': 'Public', 'PR': 'Private', 'MR': 'Military', 'MA': 'Air Force', 'MN': 'Navy', 'CG': 'Coast Guard'}
        use_map = {'PU': 'Public', 'PR': 'Private'}
        df_airports['ownership_label'] = df_airports['ownership'].map(ownership_map).fillna('Unknown')
        df_airports['use_label'] = df_airports['use'].map(use_map).fillna('Unknown')
        
        # Count by type
        print(f"  Total: {len(df_airports)} facilities")
        print(f"    Airports: {len(df_airports[df_airports['facility_type'].str.upper() == 'AIRPORT'])}")
        print(f"    Heliports: {len(df_airports[df_airports['facility_type'].str.upper() == 'HELIPORT'])}")
        print(f"    Seaplane: {len(df_airports[df_airports['facility_type'].str.upper() == 'SEAPLANE BASE'])}")
    except Exception as e:
        print(f"  [!] Error loading airports: {e}")
        df_airports = pd.DataFrame()
    
    return gdf, df_irs, df_censo, df_airports

# =============================================================================
# PROCESS ALL CITIES AND CALCULATE SCORES
# =============================================================================
def process_all_cities(gdf, df_irs, df_censo):
    print("\n" + "="*70)
    print("PROCESSING ALL CITIES")
    print("="*70)
    
    all_data = []
    
    for city_key, config in CITIES.items():
        print(f"\n  Processing {config['name']}...", end=" ")
        
        center_lat, center_lon = config['center_lat'], config['center_lon']
        
        # Filter zip codes
        gdf_city = gdf[gdf['zipcode'].str[:3].isin(config['zip_prefixes'])].copy()
        gdf_city['dist_to_center'] = gdf_city.apply(
            lambda r: haversine_distance(r['centroid_lat'], r['centroid_lon'], center_lat, center_lon), axis=1
        )
        gdf_city = gdf_city[gdf_city['dist_to_center'] <= config['radius_km']].copy()
        city_zips = gdf_city['zipcode'].tolist()
        
        if len(city_zips) == 0:
            continue
        
        # IRS data
        df_irs_city = df_irs[df_irs['zipcode'].isin(city_zips)].copy()
        agg_cols = {col: 'sum' for col in IRS_COLS.keys() if col in df_irs_city.columns}
        df_irs_agg = df_irs_city.groupby('zipcode').agg(agg_cols).reset_index()
        df_irs_agg = df_irs_agg.rename(columns=IRS_COLS)
        
        # Per-return metrics
        df_irs_agg['AGI_per_return'] = df_irs_agg['AGI'] / df_irs_agg['Num_Returns'].replace(0, np.nan)
        df_irs_agg['Capital_Gains_per_return'] = df_irs_agg['Capital_Gains'].clip(lower=0) / df_irs_agg['Num_Returns'].replace(0, np.nan)
        df_irs_agg['Dividends_per_return'] = (df_irs_agg['Dividends'] + df_irs_agg['Qualified_Dividends']) / df_irs_agg['Num_Returns'].replace(0, np.nan)
        df_irs_agg['Interest_per_return'] = df_irs_agg['Interest_Income'] / df_irs_agg['Num_Returns'].replace(0, np.nan)
        df_irs_agg['Business_Income_per_return'] = df_irs_agg['Business_Income'].clip(lower=0) / df_irs_agg['Num_Returns'].replace(0, np.nan)
        df_irs_agg['Real_Estate_Taxes_per_return'] = df_irs_agg['Real_Estate_Taxes'] / df_irs_agg['Num_Returns'].replace(0, np.nan)
        df_irs_agg['Charitable_per_return'] = df_irs_agg['Charitable_Total'] / df_irs_agg['Num_Returns'].replace(0, np.nan)
        df_irs_agg['Retirement_per_return'] = (df_irs_agg['IRA_Distributions'] + df_irs_agg['Pensions_Annuities']) / df_irs_agg['Num_Returns'].replace(0, np.nan)
        
        # IRS Wealth Proxy
        for col in IRS_WEIGHTS.keys():
            df_irs_agg[f'Score_{col}'] = normalize(df_irs_agg[col].fillna(0))
        df_irs_agg['IRS_Wealth_Raw'] = sum(df_irs_agg[f'Score_{col}'] * w for col, w in IRS_WEIGHTS.items())
        
        # Census
        df_censo_city = df_censo[df_censo['zipcode'].isin(city_zips)].copy()
        
        # Merge
        df_merged = gdf_city.merge(df_irs_agg[['zipcode', 'IRS_Wealth_Raw', 'AGI_per_return']], on='zipcode', how='left')
        df_merged = df_merged.merge(df_censo_city[['zipcode', 'Households_200k', 'Population']], on='zipcode', how='left')
        df_merged['IRS_Wealth_Raw'] = df_merged['IRS_Wealth_Raw'].fillna(0)
        df_merged['AGI_per_return'] = df_merged['AGI_per_return'].fillna(0)
        df_merged['Households_200k'] = df_merged['Households_200k'].fillna(0)
        df_merged['Population'] = df_merged['Population'].fillna(0)
        
        # Density
        df_merged['HH200k_per_km2'] = df_merged['Households_200k'] / df_merged['Area_km2'].replace(0, np.nan)
        df_merged['HH200k_per_km2'] = df_merged['HH200k_per_km2'].replace([np.inf, -np.inf], np.nan).fillna(0)
        
        # Load cached travel times
        cache_travel = f'../new_folder/cache_travel_times_{city_key}.json'
        if os.path.exists(cache_travel):
            with open(cache_travel, 'r') as f:
                travel_times = json.load(f)
            df_merged['Travel_Time_Min'] = df_merged['zipcode'].map(travel_times).fillna(0)
        else:
            df_merged['Travel_Time_Min'] = 0
        
        df_merged['city_key'] = city_key
        df_merged['city_name'] = config['name']
        df_merged['airport_code'] = config['airport_code']
        
        all_data.append(df_merged)
        print(f"{len(df_merged)} zips")
    
    # Combine all
    df_all = pd.concat(all_data, ignore_index=True)
    print(f"\n  Total zip codes: {len(df_all)}")
    
    return df_all

# =============================================================================
# CALCULATE GLOBAL SCORES WITH MEDIAN-BASED METRICS
# =============================================================================
def calculate_scores(df_all):
    print("\n" + "="*70)
    print("CALCULATING SCORES (MEDIAN-BASED GLOBAL NORMALIZATION)")
    print("="*70)
    
    # Global bounds
    global_bounds = {
        'IRS_Wealth_Raw': (df_all['IRS_Wealth_Raw'].min(), df_all['IRS_Wealth_Raw'].max()),
        'HH200k_per_km2': (df_all['HH200k_per_km2'].min(), df_all['HH200k_per_km2'].max()),
        'Households_200k': (df_all['Households_200k'].min(), df_all['Households_200k'].max()),
        'Travel_Time_Min': (df_all['Travel_Time_Min'].min(), df_all['Travel_Time_Min'].max()),
        'AGI_per_return': (df_all['AGI_per_return'].min(), df_all['AGI_per_return'].max()),
    }
    
    print(f"\n  Global Bounds:")
    print(f"    IRS Wealth:    {global_bounds['IRS_Wealth_Raw'][0]:.3f} - {global_bounds['IRS_Wealth_Raw'][1]:.3f}")
    print(f"    AGI/Return:    ${global_bounds['AGI_per_return'][0]:,.0f} - ${global_bounds['AGI_per_return'][1]:,.0f}")
    print(f"    Density:       {global_bounds['HH200k_per_km2'][0]:.1f} - {global_bounds['HH200k_per_km2'][1]:.1f} /km2")
    print(f"    HH $200k+:     {global_bounds['Households_200k'][0]:.0f} - {global_bounds['Households_200k'][1]:.0f}")
    
    # Normalize globally
    df_all['IRS_Norm'] = normalize_global(df_all['IRS_Wealth_Raw'], *global_bounds['IRS_Wealth_Raw'])
    df_all['Density_Norm'] = normalize_global(df_all['HH200k_per_km2'], *global_bounds['HH200k_per_km2'])
    df_all['Pop200k_Norm'] = normalize_global(df_all['Households_200k'], *global_bounds['Households_200k'])
    df_all['Time_Norm'] = normalize_global(df_all['Travel_Time_Min'], *global_bounds['Travel_Time_Min'])
    df_all['AGI_Norm'] = normalize_global(df_all['AGI_per_return'], *global_bounds['AGI_per_return'])
    
    # Time squared
    df_all['Time_Squared'] = df_all['Time_Norm'] ** 2
    
    # GEOMETRIC SCORE
    epsilon = 1e-10
    df_all['Geometric_Score'] = (
        ((df_all['IRS_Norm'] + epsilon) ** 0.50) *
        ((df_all['Time_Squared'] + epsilon) ** 0.20) *
        ((df_all['Pop200k_Norm'] + epsilon) ** 0.20) *
        ((df_all['Density_Norm'] + epsilon) ** 0.10)
    )
    
    # MEDIAN-based statistics by city
    print(f"\n  Median Scores by City:")
    for city_key in df_all['city_key'].unique():
        city_data = df_all[df_all['city_key'] == city_key]
        print(f"    {city_data['city_name'].iloc[0]}: median={city_data['Geometric_Score'].median()*100:.2f}%, mean={city_data['Geometric_Score'].mean()*100:.2f}%")
    
    return df_all

# =============================================================================
# FILTER TOP 10%
# =============================================================================
def filter_top_10_percent(df_all):
    print("\n" + "="*70)
    print("FILTERING TOP 10% RICHEST ZIP CODES")
    print("="*70)
    
    # Calculate 90th percentile threshold
    threshold_90 = df_all['Geometric_Score'].quantile(0.90)
    print(f"\n  90th Percentile Threshold: {threshold_90*100:.2f}%")
    
    # Filter
    df_top10 = df_all[df_all['Geometric_Score'] >= threshold_90].copy()
    print(f"  Total zip codes in top 10%: {len(df_top10)}")
    
    # Distribution by city
    print(f"\n  Distribution by City:")
    city_counts = df_top10.groupby('city_name').size().sort_values(ascending=False)
    total_by_city = df_all.groupby('city_name').size()
    
    for city_name, count in city_counts.items():
        total = total_by_city.get(city_name, 0)
        pct = count / total * 100 if total > 0 else 0
        print(f"    {city_name}: {count} zips ({pct:.1f}% of city's zips)")
    
    # Statistics
    print(f"\n  Top 10% Statistics:")
    print(f"    Score Range: {df_top10['Geometric_Score'].min()*100:.2f}% - {df_top10['Geometric_Score'].max()*100:.2f}%")
    print(f"    Median Score: {df_top10['Geometric_Score'].median()*100:.2f}%")
    print(f"    Mean Score: {df_top10['Geometric_Score'].mean()*100:.2f}%")
    print(f"    Total HH $200k+: {df_top10['Households_200k'].sum():,.0f}")
    print(f"    Total Population: {df_top10['Population'].sum():,.0f}")
    print(f"    Median AGI/Return: ${df_top10['AGI_per_return'].median():,.0f}")
    
    return df_top10, threshold_90

# =============================================================================
# CREATE NATIONAL MAP
# =============================================================================
def create_national_map(df_top10, df_airports, threshold_90):
    print("\n" + "="*70)
    print("CREATING NATIONAL MAP")
    print("="*70)
    
    # Center on US
    m = folium.Map(location=[39.8283, -98.5795], zoom_start=4, tiles='CartoDB positron')
    
    # Colormap
    colormap = cm.LinearColormap(
        colors=['#fed976', '#feb24c', '#fd8d3c', '#fc4e2a', '#e31a1c', '#bd0026', '#800026'],
        vmin=df_top10['Geometric_Score'].min(),
        vmax=df_top10['Geometric_Score'].max(),
        caption='Geometric Score (Top 10% Richest)'
    )
    
    def style_function(feature):
        value = feature['properties'].get('Geometric_Score', 0)
        return {
            'fillColor': colormap(value) if value else '#808080',
            'color': 'black',
            'weight': 0.5,
            'fillOpacity': 0.8
        }
    
    # Format columns
    df_top10['Score_Fmt'] = (df_top10['Geometric_Score'] * 100).round(2).astype(str) + '%'
    df_top10['IRS_Fmt'] = (df_top10['IRS_Norm'] * 100).round(1).astype(str) + '%'
    df_top10['AGI_Fmt'] = '$' + (df_top10['AGI_per_return'] / 1000).round(0).astype(int).astype(str) + 'k'
    df_top10['HH200k_Fmt'] = df_top10['Households_200k'].astype(int).apply(lambda x: f"{x:,}")
    df_top10['Pop_Fmt'] = df_top10['Population'].astype(int).apply(lambda x: f"{x:,}")
    
    # Add GeoJson
    folium.GeoJson(
        df_top10,
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(
            fields=['zipcode', 'city_name', 'Score_Fmt', 'AGI_Fmt', 'HH200k_Fmt', 'Pop_Fmt'],
            aliases=['Zip Code', 'City', 'Score', 'AGI/Return', 'HH $200k+', 'Population']
        )
    ).add_to(m)
    
    colormap.add_to(m)
    
    # Process and add airports and helipads with full categorization
    if not df_airports.empty:
        # Create feature groups for each category (all start hidden)
        fg_airports_public = folium.FeatureGroup(name='✈️ Airports - Public', show=False)
        fg_airports_private = folium.FeatureGroup(name='✈️ Airports - Private', show=False)
        fg_airports_military = folium.FeatureGroup(name='✈️ Airports - Military', show=False)
        fg_heliports_hospital = folium.FeatureGroup(name='🚁 Heliports - Hospital', show=False)
        fg_heliports_military = folium.FeatureGroup(name='🚁 Heliports - Military', show=False)
        fg_heliports_public = folium.FeatureGroup(name='🚁 Heliports - Public', show=False)
        fg_heliports_private = folium.FeatureGroup(name='🚁 Heliports - Private', show=False)
        fg_seaplane = folium.FeatureGroup(name='🌊 Seaplane Bases', show=False)
        fg_other = folium.FeatureGroup(name='📍 Other (Gliderport, Ultralight)', show=False)
        
        for _, row in df_airports.iterrows():
            fac_type = str(row['facility_type']).upper()
            ownership = str(row['ownership']).upper()
            use = str(row['use']).upper()
            name_upper = str(row['name']).upper()
            
            is_public = (ownership == 'PU' or use == 'PU')
            is_military = ownership in ['MR', 'MA', 'MN', 'CG']
            is_hospital = any(word in name_upper for word in ['HOSPITAL', 'MEDICAL', 'HEALTH', 'CLINIC', 'EMERGENCY', 'TRAUMA'])
            
            popup = f"<b>{row['name']}</b><br>Code: {row['code']}<br>Type: {fac_type}<br>Owner: {row['ownership_label']}<br>Use: {row['use_label']}<br>City: {row['city']}, {row['state']}"
            
            if 'HELIPORT' in fac_type:
                if is_hospital:
                    folium.Marker([row['lat'], row['lon']], popup=popup + "<br><b>🏥 HOSPITAL HELIPAD</b>",
                        icon=folium.Icon(color='green', icon='plus-square', prefix='fa'),
                        tooltip=f"{row['name']} (Hospital)").add_to(fg_heliports_hospital)
                elif is_military:
                    folium.Marker([row['lat'], row['lon']], popup=popup + "<br><b>🎖️ MILITARY HELIPAD</b>",
                        icon=folium.Icon(color='darkblue', icon='shield', prefix='fa'),
                        tooltip=f"{row['name']} (Military)").add_to(fg_heliports_military)
                elif is_public:
                    folium.Marker([row['lat'], row['lon']], popup=popup,
                        icon=folium.Icon(color='lightgreen', icon='helicopter', prefix='fa'),
                        tooltip=f"{row['name']} (Public)").add_to(fg_heliports_public)
                else:
                    folium.Marker([row['lat'], row['lon']], popup=popup,
                        icon=folium.Icon(color='gray', icon='helicopter', prefix='fa'),
                        tooltip=f"{row['name']} (Private)").add_to(fg_heliports_private)
                        
            elif 'AIRPORT' in fac_type:
                if is_military:
                    folium.Marker([row['lat'], row['lon']], popup=popup,
                        icon=folium.Icon(color='darkblue', icon='plane', prefix='fa'),
                        tooltip=f"{row['name']} (Military)").add_to(fg_airports_military)
                elif is_public:
                    folium.Marker([row['lat'], row['lon']], popup=popup,
                        icon=folium.Icon(color='blue', icon='plane', prefix='fa'),
                        tooltip=f"{row['name']} (Public)").add_to(fg_airports_public)
                else:
                    folium.Marker([row['lat'], row['lon']], popup=popup,
                        icon=folium.Icon(color='lightblue', icon='plane', prefix='fa'),
                        tooltip=f"{row['name']} (Private)").add_to(fg_airports_private)
                        
            elif 'SEAPLANE' in fac_type:
                folium.Marker([row['lat'], row['lon']], popup=popup,
                    icon=folium.Icon(color='lightgray', icon='ship', prefix='fa'),
                    tooltip=f"{row['name']} (Seaplane)").add_to(fg_seaplane)
            else:
                folium.Marker([row['lat'], row['lon']], popup=popup,
                    icon=folium.Icon(color='beige', icon='map-marker', prefix='fa'),
                    tooltip=f"{row['name']} ({fac_type})").add_to(fg_other)
        
        # Add all layers to map
        fg_airports_public.add_to(m)
        fg_airports_private.add_to(m)
        fg_airports_military.add_to(m)
        fg_heliports_hospital.add_to(m)
        fg_heliports_military.add_to(m)
        fg_heliports_public.add_to(m)
        fg_heliports_private.add_to(m)
        fg_seaplane.add_to(m)
        fg_other.add_to(m)
    
    # Add main airports (central airports in different color) - ALWAYS VISIBLE
    central_airports_layer = folium.FeatureGroup(name='🔴 Central Airports', show=True)
    for city_key, config in CITIES.items():
        folium.Marker(
            [config['airport_lat'], config['airport_lon']],
            popup=f"<b>{config['airport_code']}</b><br>{config['name']}<br><b>CENTRAL AIRPORT</b>",
            icon=folium.Icon(color='darkred', icon='plane', prefix='fa'),
            tooltip=f"{config['airport_code']} - CENTRAL"
        ).add_to(central_airports_layer)
    central_airports_layer.add_to(m)
    
    # Add layer control
    folium.LayerControl(collapsed=False, position='bottomright').add_to(m)
    
    # Info panel
    city_counts = df_top10.groupby('city_name').size().sort_values(ascending=False)
    city_list_html = "".join([f"<tr><td>{city}</td><td>{count}</td></tr>" for city, count in city_counts.items()])
    
    info_html = f"""
    <div style="position: fixed; top: 10px; right: 10px; width: 320px; background-color: white; z-index:9999; 
                border:2px solid #800026; padding: 12px; font-family: Arial; font-size: 11px; border-radius: 5px; box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">
        <h4 style="margin:0; color: #800026;">TOP 10% RICHEST ZIP CODES</h4>
        <p style="margin:5px 0; font-size: 10px; color: #666;">National Analysis - {len(df_top10)} Zip Codes</p>
        <p style="margin:3px 0; font-size: 9px; color: #bd0026;">Threshold: Score >= {threshold_90*100:.2f}%</p>
        <hr style="margin: 5px 0;">
        <table style="width:100%; font-size:10px;">
            <tr><td><b>Total HH $200k+:</b></td><td>{df_top10['Households_200k'].sum():,.0f}</td></tr>
            <tr><td><b>Total Population:</b></td><td>{df_top10['Population'].sum():,.0f}</td></tr>
            <tr><td><b>Median AGI:</b></td><td>${df_top10['AGI_per_return'].median():,.0f}</td></tr>
            <tr><td><b>Median Score:</b></td><td>{df_top10['Geometric_Score'].median()*100:.2f}%</td></tr>
        </table>
        <hr style="margin: 5px 0;">
        <p style="margin:3px 0;"><b>By City:</b></p>
        <table style="width:100%; font-size:9px;">{city_list_html}</table>
        <hr style="margin: 5px 0;">
        <p style="margin:3px 0; font-size:9px; color:#666;"><b>Legend (Toggle in Layers):</b><br>
        🔴 Central Airports<br>
        ✈️ Airports: 🔵 Public | 🩵 Private | 🔷 Military<br>
        🚁 Heliports: 🟢 Hospital | 🔵 Military | 🟩 Public | ⚫ Private<br>
        🌊 Seaplane | 📍 Other</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(info_html))
    
    m.save('map_top10_national.html')
    print("  [OK] map_top10_national.html")

# =============================================================================
# CREATE CITY-SPECIFIC MAPS
# =============================================================================
def create_city_maps(df_top10, df_all, df_airports):
    print("\n" + "="*70)
    print("CREATING CITY-SPECIFIC MAPS")
    print("="*70)
    
    for city_key, config in CITIES.items():
        city_name = config['name']
        df_city_top = df_top10[df_top10['city_key'] == city_key]
        df_city_all = df_all[df_all['city_key'] == city_key]
        
        if len(df_city_top) == 0:
            print(f"  [SKIP] {city_name}: No top 10% zips")
            continue
        
        m = folium.Map(location=[config['center_lat'], config['center_lon']], zoom_start=10, tiles='CartoDB positron')
        
        # Background layer (all zips in gray)
        folium.GeoJson(
            df_city_all,
            style_function=lambda x: {'fillColor': '#e0e0e0', 'color': '#999', 'weight': 0.3, 'fillOpacity': 0.3}
        ).add_to(m)
        
        # Top 10% layer
        colormap = cm.LinearColormap(
            colors=['#fed976', '#feb24c', '#fd8d3c', '#fc4e2a', '#e31a1c', '#bd0026', '#800026'],
            vmin=df_city_top['Geometric_Score'].min(),
            vmax=df_city_top['Geometric_Score'].max(),
            caption=f'Top 10% Score - {city_name}'
        )
        
        def style_top(feature):
            value = feature['properties'].get('Geometric_Score', 0)
            return {'fillColor': colormap(value), 'color': 'black', 'weight': 1, 'fillOpacity': 0.8}
        
        folium.GeoJson(
            df_city_top,
            style_function=style_top,
            tooltip=folium.GeoJsonTooltip(
                fields=['zipcode', 'Score_Fmt', 'AGI_Fmt', 'HH200k_Fmt'],
                aliases=['Zip', 'Score', 'AGI/Return', 'HH $200k+']
            )
        ).add_to(m)
        
        colormap.add_to(m)
        
        # Filter airports/helipads within city radius
        if not df_airports.empty:
            df_airports_city = df_airports.copy()
            df_airports_city['dist_to_center'] = df_airports_city.apply(
                lambda r: haversine_distance(r['lat'], r['lon'], config['center_lat'], config['center_lon']), axis=1
            )
            df_airports_city = df_airports_city[df_airports_city['dist_to_center'] <= config['radius_km']]
            
            # Create feature groups for each category
            fg_airports_public = folium.FeatureGroup(name='✈️ Airports - Public', show=False)
            fg_airports_private = folium.FeatureGroup(name='✈️ Airports - Private', show=False)
            fg_airports_military = folium.FeatureGroup(name='✈️ Airports - Military', show=False)
            fg_heliports_hospital = folium.FeatureGroup(name='🚁 Heliports - Hospital', show=False)
            fg_heliports_military = folium.FeatureGroup(name='🚁 Heliports - Military', show=False)
            fg_heliports_public = folium.FeatureGroup(name='🚁 Heliports - Public', show=False)
            fg_heliports_private = folium.FeatureGroup(name='🚁 Heliports - Private', show=False)
            fg_seaplane = folium.FeatureGroup(name='🌊 Seaplane Bases', show=False)
            fg_other = folium.FeatureGroup(name='📍 Other', show=False)
            
            for _, row in df_airports_city.iterrows():
                # Exclude central airport from layers (it has its own marker)
                if row['code'] == config['airport_code']:
                    continue
                    
                fac_type = str(row['facility_type']).upper()
                ownership = str(row['ownership']).upper()
                use = str(row['use']).upper()
                name_upper = str(row['name']).upper()
                
                is_public = (ownership == 'PU' or use == 'PU')
                is_military = ownership in ['MR', 'MA', 'MN', 'CG']
                is_hospital = any(word in name_upper for word in ['HOSPITAL', 'MEDICAL', 'HEALTH', 'CLINIC', 'EMERGENCY', 'TRAUMA'])
                
                popup = f"<b>{row['name']}</b><br>Code: {row['code']}<br>Type: {fac_type}<br>Owner: {row['ownership_label']}<br>Use: {row['use_label']}<br>City: {row['city']}, {row['state']}"
                
                if 'HELIPORT' in fac_type:
                    if is_hospital:
                        folium.Marker([row['lat'], row['lon']], popup=popup + "<br><b>🏥 HOSPITAL HELIPAD</b>",
                            icon=folium.Icon(color='green', icon='plus-square', prefix='fa'),
                            tooltip=f"{row['name']} (Hospital)").add_to(fg_heliports_hospital)
                    elif is_military:
                        folium.Marker([row['lat'], row['lon']], popup=popup + "<br><b>🎖️ MILITARY HELIPAD</b>",
                            icon=folium.Icon(color='darkblue', icon='shield', prefix='fa'),
                            tooltip=f"{row['name']} (Military)").add_to(fg_heliports_military)
                    elif is_public:
                        folium.Marker([row['lat'], row['lon']], popup=popup,
                            icon=folium.Icon(color='lightgreen', icon='helicopter', prefix='fa'),
                            tooltip=f"{row['name']} (Public)").add_to(fg_heliports_public)
                    else:
                        folium.Marker([row['lat'], row['lon']], popup=popup,
                            icon=folium.Icon(color='gray', icon='helicopter', prefix='fa'),
                            tooltip=f"{row['name']} (Private)").add_to(fg_heliports_private)
                            
                elif 'AIRPORT' in fac_type:
                    if is_military:
                        folium.Marker([row['lat'], row['lon']], popup=popup,
                            icon=folium.Icon(color='darkblue', icon='plane', prefix='fa'),
                            tooltip=f"{row['name']} (Military)").add_to(fg_airports_military)
                    elif is_public:
                        folium.Marker([row['lat'], row['lon']], popup=popup,
                            icon=folium.Icon(color='blue', icon='plane', prefix='fa'),
                            tooltip=f"{row['name']} (Public)").add_to(fg_airports_public)
                    else:
                        folium.Marker([row['lat'], row['lon']], popup=popup,
                            icon=folium.Icon(color='lightblue', icon='plane', prefix='fa'),
                            tooltip=f"{row['name']} (Private)").add_to(fg_airports_private)
                            
                elif 'SEAPLANE' in fac_type:
                    folium.Marker([row['lat'], row['lon']], popup=popup,
                        icon=folium.Icon(color='lightgray', icon='ship', prefix='fa'),
                        tooltip=f"{row['name']} (Seaplane)").add_to(fg_seaplane)
                else:
                    folium.Marker([row['lat'], row['lon']], popup=popup,
                        icon=folium.Icon(color='beige', icon='map-marker', prefix='fa'),
                        tooltip=f"{row['name']} ({fac_type})").add_to(fg_other)
            
            # Add all layers to map
            fg_airports_public.add_to(m)
            fg_airports_private.add_to(m)
            fg_airports_military.add_to(m)
            fg_heliports_hospital.add_to(m)
            fg_heliports_military.add_to(m)
            fg_heliports_public.add_to(m)
            fg_heliports_private.add_to(m)
            fg_seaplane.add_to(m)
            fg_other.add_to(m)
        
        # Central airport marker (always visible)
        central_airport_layer = folium.FeatureGroup(name='🔴 Central Airport', show=True)
        folium.Marker(
            [config['airport_lat'], config['airport_lon']],
            popup=f"<b>{config['airport_code']}</b><br>{city_name}<br><b>CENTRAL AIRPORT</b>",
            icon=folium.Icon(color='darkred', icon='plane', prefix='fa'),
            tooltip=f"{config['airport_code']} - CENTRAL"
        ).add_to(central_airport_layer)
        central_airport_layer.add_to(m)
        
        # Add layer control
        folium.LayerControl(collapsed=False, position='bottomright').add_to(m)
        
        # Info
        info_html = f"""
        <div style="position: fixed; top: 10px; right: 10px; width: 280px; background-color: white; z-index:9999; 
                    border:2px solid #800026; padding: 10px; font-family: Arial; font-size: 11px; border-radius: 5px;">
            <h4 style="margin:0; color: #800026;">Top 10% - {city_name}</h4>
            <hr style="margin: 5px 0;">
            <p><b>Rich Zips:</b> {len(df_city_top)} / {len(df_city_all)} ({len(df_city_top)/len(df_city_all)*100:.1f}%)</p>
            <p><b>HH $200k+:</b> {df_city_top['Households_200k'].sum():,.0f}</p>
            <p><b>Median AGI:</b> ${df_city_top['AGI_per_return'].median():,.0f}</p>
            <p><b>Score Range:</b> {df_city_top['Geometric_Score'].min()*100:.1f}% - {df_city_top['Geometric_Score'].max()*100:.1f}%</p>
            <hr style="margin: 5px 0;">
            <p style="margin:3px 0; font-size:9px; color:#666;"><b>Legend (Toggle Layers):</b><br>
            🔴 Central Airport<br>
            ✈️ Pub/Priv/Mil Airports<br>
            🚁 Hosp/Mil/Pub/Priv Heliports</p>
        </div>
        """
        m.get_root().html.add_child(folium.Element(info_html))
        
        m.save(f'map_top10_{city_key}.html')
        print(f"  [OK] map_top10_{city_key}.html ({len(df_city_top)} zips)")

# =============================================================================
# CREATE HISTOGRAMS
# =============================================================================
def create_histograms(df_top10, df_all, threshold_90):
    print("\n" + "="*70)
    print("CREATING HISTOGRAMS")
    print("="*70)
    
    # Figure 1: Distribution of top 10% scores
    fig1, ax1 = plt.subplots(figsize=(12, 7))
    
    for city_key in df_top10['city_key'].unique():
        city_data = df_top10[df_top10['city_key'] == city_key]
        city_name = CITIES[city_key]['name']
        ax1.hist(city_data['Geometric_Score'].values, bins=20, alpha=0.6, 
                 label=f"{city_name} (n={len(city_data)})", color=CITY_COLORS.get(city_key, 'gray'))
    
    ax1.axvline(threshold_90, color='red', linestyle='--', linewidth=2, label=f'90th Percentile: {threshold_90*100:.2f}%')
    ax1.set_xlabel('Geometric Score', fontsize=12)
    ax1.set_ylabel('Number of Zip Codes', fontsize=12)
    ax1.set_title('Score Distribution - TOP 10% Richest Zip Codes', fontsize=14, fontweight='bold')
    ax1.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax1.legend(loc='upper right')
    ax1.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    fig1.savefig('histogram_top10_scores.png', dpi=150)
    print("  [OK] histogram_top10_scores.png")
    plt.close(fig1)
    
    # Figure 2: Comparison all vs top 10%
    fig2, (ax2a, ax2b) = plt.subplots(1, 2, figsize=(14, 6))
    
    # All zips
    ax2a.hist(df_all['Geometric_Score'].values, bins=50, color='#0c2c84', alpha=0.7, edgecolor='white')
    ax2a.axvline(threshold_90, color='red', linestyle='--', linewidth=2, label=f'Top 10% Threshold')
    ax2a.axvline(df_all['Geometric_Score'].median(), color='orange', linestyle=':', linewidth=2, label=f'Median: {df_all["Geometric_Score"].median()*100:.2f}%')
    ax2a.set_xlabel('Geometric Score', fontsize=11)
    ax2a.set_ylabel('Zip Codes', fontsize=11)
    ax2a.set_title(f'All Zip Codes (n={len(df_all)})', fontsize=12, fontweight='bold')
    ax2a.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax2a.legend(fontsize=9)
    ax2a.grid(axis='y', alpha=0.3)
    
    # Top 10%
    ax2b.hist(df_top10['Geometric_Score'].values, bins=30, color='#bd0026', alpha=0.7, edgecolor='white')
    ax2b.axvline(df_top10['Geometric_Score'].median(), color='orange', linestyle=':', linewidth=2, label=f'Median: {df_top10["Geometric_Score"].median()*100:.2f}%')
    ax2b.set_xlabel('Geometric Score', fontsize=11)
    ax2b.set_ylabel('Zip Codes', fontsize=11)
    ax2b.set_title(f'Top 10% Richest (n={len(df_top10)})', fontsize=12, fontweight='bold')
    ax2b.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax2b.legend(fontsize=9)
    ax2b.grid(axis='y', alpha=0.3)
    
    fig2.suptitle('Score Distribution: All vs Top 10%', fontsize=14, fontweight='bold')
    plt.tight_layout()
    fig2.savefig('histogram_all_vs_top10.png', dpi=150)
    print("  [OK] histogram_all_vs_top10.png")
    plt.close(fig2)
    
    # Figure 3: Box plot by city (top 10% only)
    fig3, ax3 = plt.subplots(figsize=(12, 7))
    
    city_data = []
    city_labels = []
    city_colors = []
    
    sorted_cities = df_top10.groupby('city_key').apply(lambda x: x['Geometric_Score'].median()).sort_values(ascending=False)
    
    for city_key in sorted_cities.index:
        data = df_top10[df_top10['city_key'] == city_key]['Geometric_Score'].values * 100
        city_data.append(data)
        city_labels.append(CITIES[city_key]['name'])
        city_colors.append(CITY_COLORS.get(city_key, 'gray'))
    
    bp = ax3.boxplot(city_data, tick_labels=city_labels, patch_artist=True)
    for idx, box in enumerate(bp['boxes']):
        box.set_facecolor(city_colors[idx])
        box.set_alpha(0.7)
    
    ax3.set_ylabel('Geometric Score (%)', fontsize=12)
    ax3.set_title('Top 10% Score Distribution by City\n(Sorted by Median)', fontsize=14, fontweight='bold')
    ax3.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    fig3.savefig('histogram_top10_boxplot.png', dpi=150)
    print("  [OK] histogram_top10_boxplot.png")
    plt.close(fig3)
    
    # Figure 4: AGI Distribution
    fig4, ax4 = plt.subplots(figsize=(12, 7))
    
    for city_key in df_top10['city_key'].unique():
        city_data = df_top10[df_top10['city_key'] == city_key]
        city_name = CITIES[city_key]['name']
        ax4.hist(city_data['AGI_per_return'].values / 1000, bins=20, alpha=0.6,
                 label=f"{city_name}", color=CITY_COLORS.get(city_key, 'gray'))
    
    median_agi = df_top10['AGI_per_return'].median() / 1000
    ax4.axvline(median_agi, color='red', linestyle='--', linewidth=2, label=f'Median: ${median_agi:.0f}k')
    ax4.set_xlabel('AGI per Return ($k)', fontsize=12)
    ax4.set_ylabel('Number of Zip Codes', fontsize=12)
    ax4.set_title('AGI Distribution - Top 10% Richest Zip Codes', fontsize=14, fontweight='bold')
    ax4.legend(loc='upper right')
    ax4.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    fig4.savefig('histogram_top10_agi.png', dpi=150)
    print("  [OK] histogram_top10_agi.png")
    plt.close(fig4)
    
    # Figure 5: City count bar chart
    fig5, ax5 = plt.subplots(figsize=(12, 7))
    
    city_counts = df_top10.groupby('city_name').size().sort_values(ascending=True)
    colors = [CITY_COLORS.get(k, 'gray') for k in [c.lower().replace(' ', '_') for c in city_counts.index]]
    
    bars = ax5.barh(city_counts.index, city_counts.values, color=colors, alpha=0.8, edgecolor='black')
    
    # Add value labels
    for bar, val in zip(bars, city_counts.values):
        ax5.text(val + 2, bar.get_y() + bar.get_height()/2, f'{val}', va='center', fontsize=11, fontweight='bold')
    
    ax5.set_xlabel('Number of Zip Codes in Top 10%', fontsize=12)
    ax5.set_title('Top 10% Richest Zip Codes by City', fontsize=14, fontweight='bold')
    ax5.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    fig5.savefig('histogram_top10_by_city.png', dpi=150)
    print("  [OK] histogram_top10_by_city.png")
    plt.close(fig5)

# =============================================================================
# CREATE SUMMARY HTML
# =============================================================================
def create_summary_html(df_top10, df_all, threshold_90):
    print("\n" + "="*70)
    print("CREATING SUMMARY HTML")
    print("="*70)
    
    city_stats = []
    for city_key in df_top10['city_key'].unique():
        city_data = df_top10[df_top10['city_key'] == city_key]
        city_all = df_all[df_all['city_key'] == city_key]
        city_stats.append({
            'city': CITIES[city_key]['name'],
            'city_key': city_key,
            'top10_count': len(city_data),
            'total_count': len(city_all),
            'pct_rich': len(city_data) / len(city_all) * 100,
            'median_score': city_data['Geometric_Score'].median(),
            'median_agi': city_data['AGI_per_return'].median(),
            'total_hh200k': city_data['Households_200k'].sum(),
        })
    
    df_city_stats = pd.DataFrame(city_stats).sort_values('top10_count', ascending=False)
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Top 10% Richest Zip Codes - Analysis</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial; margin: 0; padding: 20px; background: #f0f0f0; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #800026; border-bottom: 3px solid #800026; padding-bottom: 10px; }}
        h2 {{ color: #bd0026; }}
        .highlight {{ background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 5px solid #ffc107; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center; }}
        .stat-card .number {{ font-size: 28px; font-weight: bold; color: #800026; }}
        .stat-card .label {{ font-size: 12px; color: #666; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; background: white; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin: 20px 0; }}
        th {{ background: #800026; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #fff5f5; }}
        .map-link {{ display: inline-block; background: #bd0026; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; margin: 5px; }}
        .map-link:hover {{ background: #800026; }}
        .chart-img {{ max-width: 100%; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>TOP 10% RICHEST ZIP CODES</h1>
        <p>National Analysis across 7 Major Metro Areas</p>
        
        <div class="highlight">
            <strong>Threshold:</strong> Geometric Score >= {threshold_90*100:.2f}% (90th percentile)<br>
            <strong>Formula:</strong> IRS<sup>0.50</sup> x Time²<sup>0.20</sup> x Pop200k<sup>0.20</sup> x Density<sup>0.10</sup>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="number">{len(df_top10)}</div>
                <div class="label">Rich Zip Codes</div>
            </div>
            <div class="stat-card">
                <div class="number">{df_top10['Households_200k'].sum():,.0f}</div>
                <div class="label">HH $200k+</div>
            </div>
            <div class="stat-card">
                <div class="number">${df_top10['AGI_per_return'].median()/1000:.0f}k</div>
                <div class="label">Median AGI/Return</div>
            </div>
            <div class="stat-card">
                <div class="number">{df_top10['Population'].sum()/1e6:.1f}M</div>
                <div class="label">Total Population</div>
            </div>
        </div>
        
        <h2>Maps</h2>
        <p>
            <a href="map_top10_national.html" class="map-link">National Map</a>
    """
    
    for city_key in CITIES.keys():
        city_count = len(df_top10[df_top10['city_key'] == city_key])
        if city_count > 0:
            html += f'<a href="map_top10_{city_key}.html" class="map-link">{CITIES[city_key]["name"]} ({city_count})</a>\n'
    
    html += """
        </p>
        
        <h2>City Breakdown</h2>
        <table>
            <tr>
                <th>City</th>
                <th>Top 10% Zips</th>
                <th>Total Zips</th>
                <th>% Rich</th>
                <th>Median Score</th>
                <th>Median AGI</th>
                <th>HH $200k+</th>
            </tr>
    """
    
    for _, row in df_city_stats.iterrows():
        html += f"""
            <tr>
                <td><strong>{row['city']}</strong></td>
                <td>{row['top10_count']}</td>
                <td>{row['total_count']}</td>
                <td>{row['pct_rich']:.1f}%</td>
                <td>{row['median_score']*100:.2f}%</td>
                <td>${row['median_agi']:,.0f}</td>
                <td>{row['total_hh200k']:,.0f}</td>
            </tr>
        """
    
    html += f"""
        </table>
        
        <h2>Score Distribution</h2>
        <img src="histogram_all_vs_top10.png" class="chart-img" alt="All vs Top 10%">
        <img src="histogram_top10_scores.png" class="chart-img" alt="Score Distribution">
        <img src="histogram_top10_by_city.png" class="chart-img" alt="By City">
        <img src="histogram_top10_boxplot.png" class="chart-img" alt="Box Plot">
        <img src="histogram_top10_agi.png" class="chart-img" alt="AGI Distribution">
        
        <h2>Distance & Radius Analysis</h2>
        <p>Geographic analysis of top 10% zip codes relative to central airports.</p>
        <img src="distance_radius_analysis.png" class="chart-img" alt="Distance & Radius Analysis">
        <p><a href="distance_radius_analysis.csv" class="map-link">📥 Download Distance Data (CSV)</a></p>
        
        <h2>Weighted Averages Analysis</h2>
        <p>Speed weighted by (HH200k+ × AGI) and AGI weighted by HH200k+.</p>
        <img src="weighted_averages_chart.png" class="chart-img" alt="Weighted Averages">
        <p><a href="weighted_averages_analysis.csv" class="map-link">📥 Download Weighted Averages (CSV)</a></p>
        
        <h2>HH $200k+ by Region</h2>
        <p>Distribution of high-income households across metro areas.</p>
        <img src="hh200k_by_region_charts.png" class="chart-img" alt="HH200k by Region">
        <p><a href="hh200k_by_region.csv" class="map-link">📥 Download HH by Region (CSV)</a></p>
        
        <h2>Data Downloads</h2>
        <p>
            <a href="top10_richest_data.csv" class="map-link">📊 Top 10% Data (CSV)</a>
            <a href="distance_radius_analysis.csv" class="map-link">📏 Distance Analysis</a>
            <a href="weighted_averages_analysis.csv" class="map-link">⚖️ Weighted Averages</a>
            <a href="hh200k_by_region.csv" class="map-link">🏠 HH by Region</a>
            <a href="helicopter_market_analysis.tex" class="map-link">📄 LaTeX Paper</a>
        </p>
        
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px;">
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            Data: IRS SOI 2022, Census ACS 5yr 2022, Google Distance Matrix API
        </div>
    </div>
</body>
</html>
    """
    
    with open('summary_top10.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("  [OK] summary_top10.html")
    
    # Export data
    df_export = df_top10.drop(columns=['geometry']).copy()
    df_export.to_csv('top10_richest_data.csv', index=False)
    print("  [OK] top10_richest_data.csv")

# =============================================================================
# CREATE DISTANCE AND RADIUS ANALYSIS TABLE
# =============================================================================
def create_distance_radius_table(df_top10, df_all):
    """
    Create a table with:
    1. Weighted distance by travel time to airport for each zip code
    2. Geodesic radius that encompasses each city's top 10% region
    """
    print("\n" + "="*70)
    print("CREATING DISTANCE & RADIUS ANALYSIS TABLE")
    print("="*70)
    
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
        # This gives more importance to zip codes that are further in time
        total_time = df_city_top['Travel_Time_Min'].sum()
        if total_time > 0:
            df_city_top['Weight'] = df_city_top['Travel_Time_Min'] / total_time
            weighted_distance = (df_city_top['Distance_km'] * df_city_top['Weight']).sum()
        else:
            weighted_distance = df_city_top['Distance_km'].mean()
        
        # Calculate geodesic radius that encompasses all top 10% zip codes
        # This is the max distance from airport to any top 10% zip centroid
        max_distance = df_city_top['Distance_km'].max()
        min_distance = df_city_top['Distance_km'].min()
        mean_distance = df_city_top['Distance_km'].mean()
        median_distance = df_city_top['Distance_km'].median()
        
        # Calculate the centroid of all top 10% zip codes
        centroid_lat = df_city_top['centroid_lat'].mean()
        centroid_lon = df_city_top['centroid_lon'].mean()
        
        # Distance from airport to the centroid of rich region
        centroid_distance = haversine_distance(centroid_lat, centroid_lon, airport_lat, airport_lon)
        
        # Calculate convex hull radius (bounding circle)
        # Find the two most distant points among top 10% zips
        max_spread = 0
        for i, row1 in df_city_top.iterrows():
            for j, row2 in df_city_top.iterrows():
                if i < j:
                    d = haversine_distance(row1['centroid_lat'], row1['centroid_lon'], 
                                          row2['centroid_lat'], row2['centroid_lon'])
                    if d > max_spread:
                        max_spread = d
        
        # Radius of minimum bounding circle (approximately half of max spread)
        bounding_radius = max_spread / 2
        
        # Time-weighted average travel time
        avg_travel_time = df_city_top['Travel_Time_Min'].mean()
        median_travel_time = df_city_top['Travel_Time_Min'].median()
        
        # Speed calculation (distance/time)
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
    
    # Additional analysis
    print("\n--- DETAILED GEODESIC ANALYSIS ---")
    print(f"\n| {'City':<15} | {'Min Dist':<10} | {'Mean Dist':<10} | {'Max Dist':<10} | {'Spread':<10} | {'Avg Speed':<10} |")
    print("-"*80)
    for _, row in df_results.iterrows():
        print(f"| {row['City']:<15} | {row['Min_Distance_km']:>7.1f} km | {row['Mean_Distance_km']:>7.1f} km | {row['Max_Distance_km']:>7.1f} km | {row['Region_Spread_km']:>7.1f} km | {row['Avg_Speed_kmh']:>7.1f} km/h |")
    print("-"*80)
    
    # Centroid locations
    print("\n--- RICH REGION CENTROIDS ---")
    print(f"\n| {'City':<15} | {'Centroid Lat':<12} | {'Centroid Lon':<12} | {'Dist to Airport':<15} |")
    print("-"*65)
    for _, row in df_results.iterrows():
        print(f"| {row['City']:<15} | {row['Centroid_Lat']:>12.4f} | {row['Centroid_Lon']:>12.4f} | {row['Centroid_to_Airport_km']:>12.1f} km |")
    print("-"*65)
    
    # Save to CSV
    df_results.to_csv('distance_radius_analysis.csv', index=False)
    print("\n  [OK] distance_radius_analysis.csv")
    
    # Create visualization
    create_distance_radius_chart(df_results)
    
    return df_results

# =============================================================================
# WEIGHTED AVERAGES ANALYSIS
# =============================================================================
def create_weighted_averages_analysis(df_top10, df_all):
    """
    Create two new weighted averages:
    
    1. Speed Weighted Average (by city):
       Sum(HH200K+ × AGI × Speed) / Sum(HH200K+ × AGI)
       
    2. AGI Weighted by HH200K+ (by city):
       Sum(HH200K+ × AGI) / Sum(HH200K+)
    """
    print("\n" + "="*70)
    print("WEIGHTED AVERAGES ANALYSIS")
    print("="*70)
    
    results = []
    
    # Process each city
    for city_key, config in CITIES.items():
        city_name = config['name']
        airport_lat = config['airport_lat']
        airport_lon = config['airport_lon']
        
        df_city = df_top10[df_top10['city_key'] == city_key].copy()
        
        if len(df_city) == 0:
            continue
        
        # Calculate distance and speed for each zip
        df_city['Distance_km'] = df_city.apply(
            lambda r: haversine_distance(r['centroid_lat'], r['centroid_lon'], airport_lat, airport_lon), 
            axis=1
        )
        df_city['Speed_kmh'] = df_city['Distance_km'] / (df_city['Travel_Time_Min'] / 60)
        df_city['Speed_kmh'] = df_city['Speed_kmh'].replace([np.inf, -np.inf], np.nan).fillna(0)
        
        # Calculate weighted components
        df_city['HH_AGI'] = df_city['Households_200k'] * df_city['AGI_per_return']
        df_city['HH_AGI_Speed'] = df_city['HH_AGI'] * df_city['Speed_kmh']
        
        # Sums
        sum_hh200k = df_city['Households_200k'].sum()
        sum_hh_agi = df_city['HH_AGI'].sum()
        sum_hh_agi_speed = df_city['HH_AGI_Speed'].sum()
        sum_agi = df_city['AGI_per_return'].sum()
        
        # AVERAGE 1: Speed weighted by (HH200K+ × AGI)
        # Sum(HH200K+ × AGI × Speed) / Sum(HH200K+ × AGI)
        if sum_hh_agi > 0:
            weighted_speed_1 = sum_hh_agi_speed / sum_hh_agi
        else:
            weighted_speed_1 = 0
        
        # AVERAGE 2: AGI weighted by HH200K+
        # Sum(HH200K+ × AGI) / Sum(HH200K+)
        if sum_hh200k > 0:
            weighted_agi_2 = sum_hh_agi / sum_hh200k
        else:
            weighted_agi_2 = 0
        
        # Additional metrics
        avg_speed_simple = df_city['Speed_kmh'].mean()
        avg_agi_simple = df_city['AGI_per_return'].mean()
        median_speed = df_city['Speed_kmh'].median()
        median_agi = df_city['AGI_per_return'].median()
        
        results.append({
            'City': city_name,
            'Top10_Zips': len(df_city),
            'Total_HH200k': sum_hh200k,
            'Sum_HH_AGI': sum_hh_agi,
            'Sum_HH_AGI_Speed': sum_hh_agi_speed,
            # Average 1: Speed weighted
            'Weighted_Speed_by_HH_AGI': weighted_speed_1,
            'Simple_Avg_Speed': avg_speed_simple,
            'Median_Speed': median_speed,
            # Average 2: AGI weighted
            'Weighted_AGI_by_HH': weighted_agi_2,
            'Simple_Avg_AGI': avg_agi_simple,
            'Median_AGI': median_agi,
        })
    
    df_results = pd.DataFrame(results)
    
    # Also calculate NATIONAL totals
    print("\n--- NATIONAL TOTALS (All Top 10% Zip Codes) ---")
    
    # Calculate for all zips combined
    df_all_top10 = df_top10.copy()
    
    # Need to calculate speed for all zips - use their respective city's airport
    for city_key, config in CITIES.items():
        mask = df_all_top10['city_key'] == city_key
        df_all_top10.loc[mask, 'Distance_km'] = df_all_top10.loc[mask].apply(
            lambda r: haversine_distance(r['centroid_lat'], r['centroid_lon'], 
                                        config['airport_lat'], config['airport_lon']), axis=1
        )
    
    df_all_top10['Speed_kmh'] = df_all_top10['Distance_km'] / (df_all_top10['Travel_Time_Min'] / 60)
    df_all_top10['Speed_kmh'] = df_all_top10['Speed_kmh'].replace([np.inf, -np.inf], np.nan).fillna(0)
    df_all_top10['HH_AGI'] = df_all_top10['Households_200k'] * df_all_top10['AGI_per_return']
    df_all_top10['HH_AGI_Speed'] = df_all_top10['HH_AGI'] * df_all_top10['Speed_kmh']
    
    national_sum_hh200k = df_all_top10['Households_200k'].sum()
    national_sum_hh_agi = df_all_top10['HH_AGI'].sum()
    national_sum_hh_agi_speed = df_all_top10['HH_AGI_Speed'].sum()
    
    national_weighted_speed = national_sum_hh_agi_speed / national_sum_hh_agi if national_sum_hh_agi > 0 else 0
    national_weighted_agi = national_sum_hh_agi / national_sum_hh200k if national_sum_hh200k > 0 else 0
    
    print(f"\n  Total Top 10% Zip Codes: {len(df_all_top10)}")
    print(f"  Total HH $200k+: {national_sum_hh200k:,.0f}")
    print(f"  Sum(HH × AGI): ${national_sum_hh_agi:,.0f}")
    print(f"  Sum(HH × AGI × Speed): {national_sum_hh_agi_speed:,.0f}")
    
    print(f"\n  AVERAGE 1 - Speed Weighted by (HH×AGI):")
    print(f"    National: {national_weighted_speed:.2f} km/h")
    
    print(f"\n  AVERAGE 2 - AGI Weighted by HH200k+:")
    print(f"    National: ${national_weighted_agi:,.0f}")
    
    # Print city-level table
    print("\n" + "="*70)
    print("AVERAGE 1: SPEED WEIGHTED BY (HH200K+ × AGI)")
    print("Formula: Sum(HH200K+ × AGI × Speed) / Sum(HH200K+ × AGI)")
    print("="*70)
    
    df_sorted1 = df_results.sort_values('Weighted_Speed_by_HH_AGI', ascending=False)
    print("\n" + "-"*95)
    print(f"| {'City':<15} | {'Zips':<5} | {'Weighted Speed':<14} | {'Simple Avg':<12} | {'Median':<10} | {'Difference':<10} |")
    print("-"*95)
    for _, row in df_sorted1.iterrows():
        diff = row['Weighted_Speed_by_HH_AGI'] - row['Simple_Avg_Speed']
        diff_sign = '+' if diff >= 0 else ''
        print(f"| {row['City']:<15} | {row['Top10_Zips']:<5} | {row['Weighted_Speed_by_HH_AGI']:>10.2f} km/h | {row['Simple_Avg_Speed']:>8.2f} km/h | {row['Median_Speed']:>6.2f} km/h | {diff_sign}{diff:>7.2f} km/h |")
    print("-"*95)
    print(f"| {'NATIONAL':<15} | {len(df_all_top10):<5} | {national_weighted_speed:>10.2f} km/h | {df_all_top10['Speed_kmh'].mean():>8.2f} km/h | {df_all_top10['Speed_kmh'].median():>6.2f} km/h | {'':>10} |")
    print("-"*95)
    
    print("\n" + "="*70)
    print("AVERAGE 2: AGI WEIGHTED BY HH200K+")
    print("Formula: Sum(HH200K+ × AGI) / Sum(HH200K+)")
    print("="*70)
    
    df_sorted2 = df_results.sort_values('Weighted_AGI_by_HH', ascending=False)
    print("\n" + "-"*100)
    print(f"| {'City':<15} | {'Total HH200k':<12} | {'Weighted AGI':<14} | {'Simple Avg':<12} | {'Median':<12} | {'Difference':<12} |")
    print("-"*100)
    for _, row in df_sorted2.iterrows():
        diff = row['Weighted_AGI_by_HH'] - row['Simple_Avg_AGI']
        diff_sign = '+' if diff >= 0 else ''
        print(f"| {row['City']:<15} | {row['Total_HH200k']:>10,.0f} | ${row['Weighted_AGI_by_HH']:>11,.0f} | ${row['Simple_Avg_AGI']:>9,.0f} | ${row['Median_AGI']:>9,.0f} | {diff_sign}${diff:>9,.0f} |")
    print("-"*100)
    print(f"| {'NATIONAL':<15} | {national_sum_hh200k:>10,.0f} | ${national_weighted_agi:>11,.0f} | ${df_all_top10['AGI_per_return'].mean():>9,.0f} | ${df_all_top10['AGI_per_return'].median():>9,.0f} | {'':>12} |")
    print("-"*100)
    
    # Save to CSV
    df_results['National_Weighted_Speed'] = national_weighted_speed
    df_results['National_Weighted_AGI'] = national_weighted_agi
    df_results.to_csv('weighted_averages_analysis.csv', index=False)
    print("\n  [OK] weighted_averages_analysis.csv")
    
    # Create visualization
    create_weighted_averages_chart(df_results, national_weighted_speed, national_weighted_agi)
    
    return df_results

# =============================================================================
# HH200K+ BY REGION ANALYSIS
# =============================================================================
def create_hh200k_by_region_analysis(df_top10, df_all):
    """
    Create table and chart with SUM of all HH200k+ by region (city)
    Comparing Top 10% vs All zip codes
    """
    print("\n" + "="*70)
    print("HH200K+ BY REGION ANALYSIS")
    print("="*70)
    
    results = []
    
    for city_key, config in CITIES.items():
        city_name = config['name']
        
        df_city_top = df_top10[df_top10['city_key'] == city_key]
        df_city_all = df_all[df_all['city_key'] == city_key]
        
        if len(df_city_all) == 0:
            continue
        
        # Sums for Top 10%
        top10_hh200k = df_city_top['Households_200k'].sum()
        top10_population = df_city_top['Population'].sum()
        top10_zips = len(df_city_top)
        
        # Sums for ALL zip codes
        all_hh200k = df_city_all['Households_200k'].sum()
        all_population = df_city_all['Population'].sum()
        all_zips = len(df_city_all)
        
        # Percentages
        pct_hh200k_in_top10 = (top10_hh200k / all_hh200k * 100) if all_hh200k > 0 else 0
        pct_pop_in_top10 = (top10_population / all_population * 100) if all_population > 0 else 0
        pct_zips_in_top10 = (top10_zips / all_zips * 100) if all_zips > 0 else 0
        
        # Concentration ratio (HH200k% / Zips%)
        concentration = pct_hh200k_in_top10 / pct_zips_in_top10 if pct_zips_in_top10 > 0 else 0
        
        # HH200k per zip code
        hh200k_per_zip_top10 = top10_hh200k / top10_zips if top10_zips > 0 else 0
        hh200k_per_zip_all = all_hh200k / all_zips if all_zips > 0 else 0
        
        results.append({
            'City': city_name,
            'city_key': city_key,
            'Top10_Zips': top10_zips,
            'Top10_HH200k': top10_hh200k,
            'Top10_Population': top10_population,
            'Top10_HH200k_per_Zip': hh200k_per_zip_top10,
            'All_Zips': all_zips,
            'All_HH200k': all_hh200k,
            'All_Population': all_population,
            'All_HH200k_per_Zip': hh200k_per_zip_all,
            'Pct_HH200k_in_Top10': pct_hh200k_in_top10,
            'Pct_Pop_in_Top10': pct_pop_in_top10,
            'Pct_Zips_in_Top10': pct_zips_in_top10,
            'Concentration_Ratio': concentration,
        })
    
    df_results = pd.DataFrame(results)
    
    # National totals
    national_top10_hh200k = df_top10['Households_200k'].sum()
    national_top10_pop = df_top10['Population'].sum()
    national_all_hh200k = df_all['Households_200k'].sum()
    national_all_pop = df_all['Population'].sum()
    
    print("\n--- NATIONAL SUMMARY ---")
    print(f"\n  ALL ZIP CODES ({len(df_all)} zips):")
    print(f"    Total HH $200k+: {national_all_hh200k:,.0f}")
    print(f"    Total Population: {national_all_pop:,.0f}")
    print(f"\n  TOP 10% ZIP CODES ({len(df_top10)} zips):")
    print(f"    Total HH $200k+: {national_top10_hh200k:,.0f} ({national_top10_hh200k/national_all_hh200k*100:.1f}% of total)")
    print(f"    Total Population: {national_top10_pop:,.0f} ({national_top10_pop/national_all_pop*100:.1f}% of total)")
    
    df_sorted = df_results.sort_values('Top10_HH200k', ascending=False)
    
    print("\n--- TOP 10% ZIP CODES - HH200K+ BY REGION ---")
    print("-"*100)
    print(f"| {'City':<15} | {'Zips':<5} | {'HH $200k+':<12} | {'Population':<12} | {'HH/Zip':<10} | {'% of City HH':<12} |")
    print("-"*100)
    for _, row in df_sorted.iterrows():
        print(f"| {row['City']:<15} | {row['Top10_Zips']:<5} | {row['Top10_HH200k']:>10,.0f} | {row['Top10_Population']:>10,.0f} | {row['Top10_HH200k_per_Zip']:>8,.0f} | {row['Pct_HH200k_in_Top10']:>10.1f}% |")
    print("-"*100)
    print(f"| {'NATIONAL':<15} | {len(df_top10):<5} | {national_top10_hh200k:>10,.0f} | {national_top10_pop:>10,.0f} | {national_top10_hh200k/len(df_top10):>8,.0f} | {national_top10_hh200k/national_all_hh200k*100:>10.1f}% |")
    print("-"*100)
    
    print("\n--- ALL ZIP CODES - HH200K+ BY REGION ---")
    print("-"*90)
    print(f"| {'City':<15} | {'Zips':<5} | {'HH $200k+':<12} | {'Population':<12} | {'HH/Zip':<10} |")
    print("-"*90)
    df_sorted_all = df_results.sort_values('All_HH200k', ascending=False)
    for _, row in df_sorted_all.iterrows():
        print(f"| {row['City']:<15} | {row['All_Zips']:<5} | {row['All_HH200k']:>10,.0f} | {row['All_Population']:>10,.0f} | {row['All_HH200k_per_Zip']:>8,.0f} |")
    print("-"*90)
    print(f"| {'NATIONAL':<15} | {len(df_all):<5} | {national_all_hh200k:>10,.0f} | {national_all_pop:>10,.0f} | {national_all_hh200k/len(df_all):>8,.0f} |")
    print("-"*90)
    
    df_results.to_csv('hh200k_by_region.csv', index=False)
    print("\n  [OK] hh200k_by_region.csv")
    
    create_hh200k_charts(df_results, national_top10_hh200k, national_all_hh200k)
    
    return df_results

def create_hh200k_charts(df_results, national_top10, national_all):
    """Create visualizations for HH200k by region"""
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    
    df_sorted = df_results.sort_values('Top10_HH200k', ascending=True)
    cities = df_sorted['City'].tolist()
    colors = [CITY_COLORS.get(c.lower().replace(' ', '_'), 'gray') for c in cities]
    
    # Chart 1: Top 10% HH200k by City
    ax1 = axes[0, 0]
    bars1 = ax1.barh(cities, df_sorted['Top10_HH200k'] / 1000, color=colors, alpha=0.8, edgecolor='black')
    ax1.set_xlabel('HH $200k+ (thousands)', fontsize=11)
    ax1.set_title('Top 10% Richest Zip Codes\nHH $200k+ by City', fontsize=12, fontweight='bold')
    ax1.grid(axis='x', alpha=0.3)
    for bar, val in zip(bars1, df_sorted['Top10_HH200k']):
        ax1.text(val/1000 + 5, bar.get_y() + bar.get_height()/2, f'{val/1000:.0f}k', va='center', fontsize=10)
    
    # Chart 2: Top 10% vs All
    ax2 = axes[0, 1]
    x = range(len(cities))
    width = 0.35
    bars2a = ax2.bar([i - width/2 for i in x], df_sorted['Top10_HH200k'] / 1000, width, 
                      label='Top 10%', color='#bd0026', alpha=0.8, edgecolor='black')
    bars2b = ax2.bar([i + width/2 for i in x], df_sorted['All_HH200k'] / 1000, width,
                      label='All Zips', color='#0c2c84', alpha=0.5, edgecolor='black')
    ax2.set_xticks(x)
    ax2.set_xticklabels(cities, rotation=45, ha='right')
    ax2.set_ylabel('HH $200k+ (thousands)', fontsize=11)
    ax2.set_title('Top 10% vs All Zip Codes\nHH $200k+ Comparison', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(axis='y', alpha=0.3)
    
    # Chart 3: Percentage in Top 10%
    ax3 = axes[1, 0]
    df_sorted_pct = df_results.sort_values('Pct_HH200k_in_Top10', ascending=True)
    cities_pct = df_sorted_pct['City'].tolist()
    colors_pct = [CITY_COLORS.get(c.lower().replace(' ', '_'), 'gray') for c in cities_pct]
    bars3 = ax3.barh(cities_pct, df_sorted_pct['Pct_HH200k_in_Top10'], color=colors_pct, alpha=0.8, edgecolor='black')
    ax3.axvline(national_top10/national_all*100, color='red', linestyle='--', linewidth=2, 
                label=f'National: {national_top10/national_all*100:.1f}%')
    ax3.set_xlabel('% of City HH $200k+ in Top 10%', fontsize=11)
    ax3.set_title('Concentration of Wealth\n% in Top 10% Zip Codes', fontsize=12, fontweight='bold')
    ax3.legend(loc='lower right', fontsize=10)
    ax3.grid(axis='x', alpha=0.3)
    for bar, val in zip(bars3, df_sorted_pct['Pct_HH200k_in_Top10']):
        ax3.text(val + 1, bar.get_y() + bar.get_height()/2, f'{val:.1f}%', va='center', fontsize=10)
    
    # Chart 4: Pie chart
    ax4 = axes[1, 1]
    df_sorted_pie = df_results.sort_values('Top10_HH200k', ascending=False)
    sizes = df_sorted_pie['Top10_HH200k'].values
    labels = [f"{row['City']}\n{row['Top10_HH200k']/1000:.0f}k" for _, row in df_sorted_pie.iterrows()]
    colors_pie = [CITY_COLORS.get(c.lower().replace(' ', '_'), 'gray') for c in df_sorted_pie['City']]
    wedges, texts, autotexts = ax4.pie(sizes, labels=labels, colors=colors_pie, autopct='%1.1f%%',
                                        startangle=90, pctdistance=0.75)
    ax4.set_title(f'National Distribution\nTotal: {national_top10/1000:.0f}k HH $200k+', fontsize=12, fontweight='bold')
    for text in texts:
        text.set_fontsize(9)
    for autotext in autotexts:
        autotext.set_fontsize(8)
    
    plt.tight_layout()
    fig.savefig('hh200k_by_region_charts.png', dpi=150, bbox_inches='tight')
    print("  [OK] hh200k_by_region_charts.png")
    plt.close(fig)

def create_weighted_averages_chart(df_results, national_speed, national_agi):
    """Create visualization for weighted averages"""
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 7))
    
    # Chart 1: Speed comparison (Weighted vs Simple)
    ax1 = axes[0]
    df_sorted1 = df_results.sort_values('Weighted_Speed_by_HH_AGI', ascending=True)
    cities = df_sorted1['City'].tolist()
    y_pos = range(len(cities))
    
    colors = [CITY_COLORS.get(c.lower().replace(' ', '_'), 'gray') for c in cities]
    
    # Bars
    bars1 = ax1.barh(y_pos, df_sorted1['Weighted_Speed_by_HH_AGI'], height=0.4, 
                     label='Weighted (HH×AGI)', color=colors, alpha=0.8, edgecolor='black')
    bars2 = ax1.barh([y + 0.4 for y in y_pos], df_sorted1['Simple_Avg_Speed'], height=0.4,
                     label='Simple Average', color=colors, alpha=0.4, edgecolor='black', hatch='//')
    
    # National line
    ax1.axvline(national_speed, color='red', linestyle='--', linewidth=2, label=f'National: {national_speed:.1f} km/h')
    
    ax1.set_yticks([y + 0.2 for y in y_pos])
    ax1.set_yticklabels(cities)
    ax1.set_xlabel('Speed (km/h)', fontsize=11)
    ax1.set_title('AVERAGE 1: Speed Weighted by (HH200k+ × AGI)\nFormula: Σ(HH×AGI×Speed) / Σ(HH×AGI)', fontsize=12, fontweight='bold')
    ax1.legend(loc='lower right', fontsize=9)
    ax1.grid(axis='x', alpha=0.3)
    
    # Chart 2: AGI comparison (Weighted vs Simple)
    ax2 = axes[1]
    df_sorted2 = df_results.sort_values('Weighted_AGI_by_HH', ascending=True)
    cities2 = df_sorted2['City'].tolist()
    colors2 = [CITY_COLORS.get(c.lower().replace(' ', '_'), 'gray') for c in cities2]
    
    bars3 = ax2.barh(y_pos, df_sorted2['Weighted_AGI_by_HH'] / 1000, height=0.4,
                     label='Weighted (by HH)', color=colors2, alpha=0.8, edgecolor='black')
    bars4 = ax2.barh([y + 0.4 for y in y_pos], df_sorted2['Simple_Avg_AGI'] / 1000, height=0.4,
                     label='Simple Average', color=colors2, alpha=0.4, edgecolor='black', hatch='//')
    
    # National line
    ax2.axvline(national_agi / 1000, color='red', linestyle='--', linewidth=2, label=f'National: ${national_agi/1000:.0f}k')
    
    ax2.set_yticks([y + 0.2 for y in y_pos])
    ax2.set_yticklabels(cities2)
    ax2.set_xlabel('AGI per Return ($k)', fontsize=11)
    ax2.set_title('AVERAGE 2: AGI Weighted by HH200k+\nFormula: Σ(HH×AGI) / Σ(HH)', fontsize=12, fontweight='bold')
    ax2.legend(loc='lower right', fontsize=9)
    ax2.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    fig.savefig('weighted_averages_chart.png', dpi=150, bbox_inches='tight')
    print("  [OK] weighted_averages_chart.png")
    plt.close(fig)

def create_distance_radius_chart(df_results):
    """Create visualization of distance and radius analysis"""
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    
    # Sort by weighted distance
    df_sorted = df_results.sort_values('Weighted_Distance_km', ascending=True)
    cities = df_sorted['City'].tolist()
    colors = [CITY_COLORS.get(c.lower().replace(' ', '_'), 'gray') for c in cities]
    
    # Chart 1: Weighted Distance by City
    ax1 = axes[0, 0]
    bars1 = ax1.barh(cities, df_sorted['Weighted_Distance_km'], color=colors, alpha=0.8, edgecolor='black')
    ax1.set_xlabel('Weighted Distance to Airport (km)', fontsize=11)
    ax1.set_title('Time-Weighted Distance to Airport\n(Higher travel time = more weight)', fontsize=12, fontweight='bold')
    ax1.grid(axis='x', alpha=0.3)
    for bar, val in zip(bars1, df_sorted['Weighted_Distance_km']):
        ax1.text(val + 0.5, bar.get_y() + bar.get_height()/2, f'{val:.1f}', va='center', fontsize=10)
    
    # Chart 2: Bounding Radius by City
    ax2 = axes[0, 1]
    df_sorted2 = df_results.sort_values('Bounding_Radius_km', ascending=True)
    cities2 = df_sorted2['City'].tolist()
    colors2 = [CITY_COLORS.get(c.lower().replace(' ', '_'), 'gray') for c in cities2]
    bars2 = ax2.barh(cities2, df_sorted2['Bounding_Radius_km'], color=colors2, alpha=0.8, edgecolor='black')
    ax2.set_xlabel('Bounding Radius (km)', fontsize=11)
    ax2.set_title('Geodesic Radius Encompassing Top 10%\n(Half of max spread between zip codes)', fontsize=12, fontweight='bold')
    ax2.grid(axis='x', alpha=0.3)
    for bar, val in zip(bars2, df_sorted2['Bounding_Radius_km']):
        ax2.text(val + 0.5, bar.get_y() + bar.get_height()/2, f'{val:.1f}', va='center', fontsize=10)
    
    # Chart 3: Distance Range (min-max) by City
    ax3 = axes[1, 0]
    df_sorted3 = df_results.sort_values('Median_Distance_km', ascending=True)
    cities3 = df_sorted3['City'].tolist()
    colors3 = [CITY_COLORS.get(c.lower().replace(' ', '_'), 'gray') for c in cities3]
    
    y_pos = range(len(cities3))
    ax3.barh(y_pos, df_sorted3['Max_Distance_km'] - df_sorted3['Min_Distance_km'], 
             left=df_sorted3['Min_Distance_km'], color=colors3, alpha=0.5, edgecolor='black', label='Range')
    ax3.scatter(df_sorted3['Median_Distance_km'], y_pos, color='red', s=100, zorder=5, label='Median')
    ax3.scatter(df_sorted3['Weighted_Distance_km'], y_pos, color='blue', marker='D', s=80, zorder=5, label='Weighted')
    ax3.set_yticks(y_pos)
    ax3.set_yticklabels(cities3)
    ax3.set_xlabel('Distance to Airport (km)', fontsize=11)
    ax3.set_title('Distance Range: Min to Max\n(with Median and Weighted markers)', fontsize=12, fontweight='bold')
    ax3.legend(loc='lower right', fontsize=9)
    ax3.grid(axis='x', alpha=0.3)
    
    # Chart 4: Travel Time vs Distance scatter
    ax4 = axes[1, 1]
    for _, row in df_results.iterrows():
        city_key = row['City'].lower().replace(' ', '_')
        color = CITY_COLORS.get(city_key, 'gray')
        ax4.scatter(row['Median_Distance_km'], row['Median_Travel_Time_min'], 
                   s=row['Top10_Zips']*5, color=color, alpha=0.7, edgecolor='black', label=row['City'])
    
    ax4.set_xlabel('Median Distance to Airport (km)', fontsize=11)
    ax4.set_ylabel('Median Travel Time (min)', fontsize=11)
    ax4.set_title('Distance vs Travel Time\n(Bubble size = number of top 10% zips)', fontsize=12, fontweight='bold')
    ax4.legend(loc='upper left', fontsize=9)
    ax4.grid(alpha=0.3)
    
    # Add trend line
    z = np.polyfit(df_results['Median_Distance_km'], df_results['Median_Travel_Time_min'], 1)
    p = np.poly1d(z)
    x_line = np.linspace(df_results['Median_Distance_km'].min(), df_results['Median_Distance_km'].max(), 100)
    ax4.plot(x_line, p(x_line), 'r--', alpha=0.5, label='Trend')
    
    plt.tight_layout()
    fig.savefig('distance_radius_analysis.png', dpi=150, bbox_inches='tight')
    print("  [OK] distance_radius_analysis.png")
    plt.close(fig)

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
    start_time = time.time()
    
    print("\n" + "="*70)
    print("TOP 10% RICHEST ZIP CODES - NATIONAL ANALYSIS")
    print("Using MEDIAN-based metrics for robust analysis")
    print("="*70)
    
    # Load data
    gdf, df_irs, df_censo, df_airports = load_all_data()
    
    # Process all cities
    df_all = process_all_cities(gdf, df_irs, df_censo)
    
    # Calculate scores
    df_all = calculate_scores(df_all)
    
    # Filter top 10%
    df_top10, threshold_90 = filter_top_10_percent(df_all)
    
    # Create maps
    create_national_map(df_top10, df_airports, threshold_90)
    create_city_maps(df_top10, df_all, df_airports)
    
    # Create histograms
    create_histograms(df_top10, df_all, threshold_90)
    
    # Create summary
    create_summary_html(df_top10, df_all, threshold_90)
    
    # Create distance and radius analysis
    df_distance = create_distance_radius_table(df_top10, df_all)
    
    # Create weighted averages analysis
    df_weighted = create_weighted_averages_analysis(df_top10, df_all)
    
    # Create HH200k by region analysis
    df_hh200k = create_hh200k_by_region_analysis(df_top10, df_all)
    
    elapsed = time.time() - start_time
    print(f"\n{'='*70}")
    print(f"COMPLETED in {elapsed:.1f}s")
    print(f"{'='*70}")

