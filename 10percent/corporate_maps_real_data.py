# -*- coding: utf-8 -*-
"""
CORPORATE MAPS - REAL CENSUS DATA
==================================
Creates maps using 100% REAL data from U.S. Census Bureau.

Options:
- ALL ZIPs: Complete business data (30,917 ZIPs)
- TOP 10% RICHEST: Only top 10% wealthy ZIPs (272 ZIPs)
"""

import pandas as pd
import numpy as np
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
import branca.colormap as cm
import os
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'new_folder')
AIRPORTS_FILE = os.path.join(BASE_DIR, '..', 'all-airport-data.xlsx')

# City configurations
CITIES = {
    'los_angeles': {
        'name': 'Los Angeles', 'state': 'CA',
        'center_lat': 34.0522, 'center_lon': -118.2437,
        'airport_code': 'LAX', 'airport_lat': 33.9416, 'airport_lon': -118.4085,
        'radius_km': 100, 'zoom': 10,
        'zip_prefixes': ['900', '901', '902', '903', '904', '905', '906', '907', '908', '909', 
                         '910', '911', '912', '913', '914', '915', '916', '917', '918',
                         '920', '921', '922', '923', '924', '925', '926', '927', '928'],
    },
    'new_york': {
        'name': 'New York', 'state': 'NY',
        'center_lat': 40.7128, 'center_lon': -74.0060,
        'airport_code': 'JFK', 'airport_lat': 40.6413, 'airport_lon': -73.7781,
        'radius_km': 180, 'zoom': 9,
        'zip_prefixes': ['100', '101', '102', '103', '104', '105', '106', '107', '108', '109',
                         '110', '111', '112', '113', '114', '115', '116', '117', '118', '119',
                         '070', '071', '072', '073', '074', '075', '076', '077', '078', '079'],
    },
    'chicago': {
        'name': 'Chicago', 'state': 'IL',
        'center_lat': 41.8781, 'center_lon': -87.6298,
        'airport_code': 'ORD', 'airport_lat': 41.9742, 'airport_lon': -87.9073,
        'radius_km': 100, 'zoom': 10,
        'zip_prefixes': ['600', '601', '602', '603', '604', '605', '606', '607', '608', '609'],
    },
    'dallas': {
        'name': 'Dallas', 'state': 'TX',
        'center_lat': 32.7767, 'center_lon': -96.7970,
        'airport_code': 'DFW', 'airport_lat': 32.8998, 'airport_lon': -97.0403,
        'radius_km': 100, 'zoom': 10,
        'zip_prefixes': ['750', '751', '752', '753', '754', '755', '756', '757', '758', '759',
                         '760', '761', '762', '763'],
    },
    'houston': {
        'name': 'Houston', 'state': 'TX',
        'center_lat': 29.7604, 'center_lon': -95.3698,
        'airport_code': 'IAH', 'airport_lat': 29.9902, 'airport_lon': -95.3368,
        'radius_km': 100, 'zoom': 10,
        'zip_prefixes': ['770', '771', '772', '773', '774', '775', '776', '777', '778', '779'],
    },
    'miami': {
        'name': 'Miami', 'state': 'FL',
        'center_lat': 25.7617, 'center_lon': -80.1918,
        'airport_code': 'MIA', 'airport_lat': 25.7959, 'airport_lon': -80.2870,
        'radius_km': 100, 'zoom': 10,
        'zip_prefixes': ['330', '331', '332', '333', '334', '335', '336', '337', '338', '339'],
    },
    'san_francisco': {
        'name': 'San Francisco', 'state': 'CA',
        'center_lat': 37.7749, 'center_lon': -122.4194,
        'airport_code': 'SFO', 'airport_lat': 37.6213, 'airport_lon': -122.3790,
        'radius_km': 100, 'zoom': 10,
        'zip_prefixes': ['940', '941', '942', '943', '944', '945', '946', '947', '948', '949'],
    }
}

# Power industries (NAICS codes)
POWER_INDUSTRIES = ['51', '52', '53', '54', '55', '71']
ENTERTAINMENT_INDUSTRIES = ['51', '71']
FINANCE_INDUSTRIES = ['52']

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
# LOAD DATA
# =============================================================================
def load_data(filter_top10=False):
    """Load geometry, corporate data, and airports"""
    print("\n" + "="*70)
    print("LOADING DATA")
    print("="*70)
    
    # Load geometry
    cache_file = os.path.join(DATA_DIR, 'cache_geometry.gpkg')
    gdf = gpd.read_file(cache_file)
    gdf['zipcode'] = gdf['ZCTA5CE20'].astype(str).str.zfill(5)
    gdf['centroid_lat'] = gdf.geometry.centroid.y
    gdf['centroid_lon'] = gdf.geometry.centroid.x
    gdf['Area_km2'] = gdf['ALAND20'] / 1e6
    print(f"  Geometry: {len(gdf)} ZIP codes")
    
    # Load corporate data (REAL CENSUS DATA)
    corp_file = os.path.join(BASE_DIR, 'industry_by_zip_all.csv')
    if os.path.exists(corp_file):
        df_corp = pd.read_csv(corp_file, dtype={'zipcode': str, 'naics_code': str})
        print(f"  Corporate data (REAL): {len(df_corp):,} records")
        print(f"  Unique ZIPs: {df_corp['zipcode'].nunique():,}")
    else:
        print("  [!] Corporate data not found!")
        return None, None, None
    
    # Filter to top 10% richest if requested
    if filter_top10:
        top10_file = os.path.join(BASE_DIR, 'top10_richest_data.csv')
        if os.path.exists(top10_file):
            df_top10 = pd.read_csv(top10_file, dtype={'zipcode': str})
            top10_zips = set(df_top10['zipcode'].unique())
            df_corp = df_corp[df_corp['zipcode'].isin(top10_zips)]
            gdf = gdf[gdf['zipcode'].isin(top10_zips)]
            print(f"  Filtered to TOP 10% RICHEST: {len(top10_zips)} ZIPs")
        else:
            print("  [!] Top 10% data not found, using all ZIPs")
    
    # Load airports
    try:
        df_airports = pd.read_excel(AIRPORTS_FILE)
        df_airports = df_airports[['Name', 'Facility Type', 'Ownership', 'Use', 
                                   'ARP Latitude DD', 'ARP Longitude DD', 'City', 'State Name', 'Loc Id']]
        df_airports = df_airports.dropna(subset=['ARP Latitude DD', 'ARP Longitude DD'])
        df_airports.columns = ['name', 'facility_type', 'ownership', 'use', 'lat', 'lon', 'city', 'state', 'code']
        
        ownership_map = {'PU': 'Public', 'PR': 'Private', 'MR': 'Military', 'MA': 'Air Force', 'MN': 'Navy', 'CG': 'Coast Guard'}
        use_map = {'PU': 'Public', 'PR': 'Private'}
        df_airports['ownership_label'] = df_airports['ownership'].map(ownership_map).fillna('Unknown')
        df_airports['use_label'] = df_airports['use'].map(use_map).fillna('Unknown')
        
        print(f"  Airports: {len(df_airports)} facilities")
    except Exception as e:
        print(f"  [!] Error loading airports: {e}")
        df_airports = pd.DataFrame()
    
    return gdf, df_corp, df_airports

# =============================================================================
# AGGREGATE CORPORATE DATA BY ZIP
# =============================================================================
def aggregate_corporate_data(df_corp, gdf, city_key, config):
    """Aggregate corporate data for a specific city using REAL Census data"""
    
    # Filter geometry for city
    gdf_city = gdf[gdf['zipcode'].str[:3].isin(config['zip_prefixes'])].copy()
    gdf_city['dist_to_center'] = gdf_city.apply(
        lambda r: haversine_distance(r['centroid_lat'], r['centroid_lon'],
                                    config['center_lat'], config['center_lon']), axis=1
    )
    gdf_city = gdf_city[gdf_city['dist_to_center'] <= config['radius_km']].copy()
    
    if df_corp is not None:
        # Filter corporate data for this city
        df_city_corp = df_corp[df_corp['city_key'] == city_key].copy()
        
        # Total metrics by ZIP
        df_agg = df_city_corp.groupby('zipcode').agg({
            'establishments': 'sum',
            'employment': 'sum',
            'revenue_M': 'sum'
        }).reset_index()
        df_agg.columns = ['zipcode', 'Total_Establishments', 'Total_Employment', 'Total_Revenue_M']
        
        # Power industries
        df_power = df_city_corp[df_city_corp['is_power_industry']].groupby('zipcode').agg({
            'employment': 'sum',
            'revenue_M': 'sum'
        }).reset_index()
        df_power.columns = ['zipcode', 'Power_Employment', 'Power_Revenue_M']
        
        # Entertainment/Media
        df_ent = df_city_corp[df_city_corp['naics_code'].isin(ENTERTAINMENT_INDUSTRIES)].groupby('zipcode').agg({
            'employment': 'sum',
            'revenue_M': 'sum'
        }).reset_index()
        df_ent.columns = ['zipcode', 'Entertainment_Employment', 'Entertainment_Revenue_M']
        
        # Finance
        df_fin = df_city_corp[df_city_corp['naics_code'].isin(FINANCE_INDUSTRIES)].groupby('zipcode').agg({
            'employment': 'sum',
            'revenue_M': 'sum'
        }).reset_index()
        df_fin.columns = ['zipcode', 'Finance_Employment', 'Finance_Revenue_M']
        
        # Merge all
        df_agg = df_agg.merge(df_power, on='zipcode', how='left')
        df_agg = df_agg.merge(df_ent, on='zipcode', how='left')
        df_agg = df_agg.merge(df_fin, on='zipcode', how='left')
        df_agg = df_agg.fillna(0)
        
        # Calculate shares
        df_agg['Power_Share'] = (df_agg['Power_Employment'] / df_agg['Total_Employment'].replace(0, 1)) * 100
        df_agg['Entertainment_Share'] = (df_agg['Entertainment_Employment'] / df_agg['Total_Employment'].replace(0, 1)) * 100
        df_agg['Finance_Share'] = (df_agg['Finance_Employment'] / df_agg['Total_Employment'].replace(0, 1)) * 100
        
        # Corporate Power Index
        for col in ['Total_Revenue_M', 'Total_Employment', 'Power_Share']:
            min_val, max_val = df_agg[col].min(), df_agg[col].max()
            if max_val > min_val:
                df_agg[f'{col}_Norm'] = (df_agg[col] - min_val) / (max_val - min_val)
            else:
                df_agg[f'{col}_Norm'] = 0.5
        
        df_agg['Corp_Power_Index'] = (
            0.4 * df_agg['Total_Revenue_M_Norm'] +
            0.3 * df_agg['Total_Employment_Norm'] +
            0.3 * df_agg['Power_Share_Norm']
        ) * 100
        
        # Merge with geometry
        gdf_city = gdf_city.merge(df_agg, on='zipcode', how='left')
        gdf_city = gdf_city.fillna(0)
    else:
        print(f"  [!] No corporate data for {city_key}")
        gdf_city['Total_Employment'] = 0
        gdf_city['Total_Revenue_M'] = 0
        gdf_city['Power_Share'] = 0
        gdf_city['Entertainment_Share'] = 0
        gdf_city['Finance_Share'] = 0
        gdf_city['Corp_Power_Index'] = 0
    
    return gdf_city

# =============================================================================
# CREATE CITY MAP
# =============================================================================
def create_city_map(gdf_city, df_airports, city_key, config, filter_top10=False):
    """Create corporate map for a specific city using REAL Census data"""
    
    city_name = config['name']
    map_type = "TOP 10% RICHEST" if filter_top10 else "ALL ZIPs"
    
    # Create map
    m = folium.Map(
        location=[config['center_lat'], config['center_lon']],
        zoom_start=config['zoom'],
        tiles='CartoDB positron'
    )
    
    # Colormap for Corporate Score (use Corporate_Score if available, else Corp_Power_Index)
    score_col = 'Corporate_Score' if 'Corporate_Score' in gdf_city.columns else 'Corp_Power_Index'
    score_name = 'Corporate Score' if score_col == 'Corporate_Score' else 'Corporate Power Index'
    
    if len(gdf_city) > 0 and gdf_city[score_col].max() > 0:
        colormap = cm.LinearColormap(
            colors=['#fee5d9', '#fcae91', '#fb6a4a', '#de2d26', '#a50f15'],
            vmin=gdf_city[score_col].min(),
            vmax=gdf_city[score_col].max(),
            caption=score_name
        )
        
        # Add ZIP code polygons
        for idx, row in gdf_city.iterrows():
            if pd.notna(row.geometry) and row['Total_Employment'] > 0:
                popup_html = f"""
                <div style="font-family: Arial; width: 250px;">
                    <h4 style="margin: 5px 0;">ZIP Code: {row['zipcode']}</h4>
                    <hr style="margin: 5px 0;">
                    <p style="margin: 3px 0;"><b>Total Employment:</b> {int(row['Total_Employment']):,}</p>
                    <p style="margin: 3px 0;"><b>Total Revenue:</b> ${row['Total_Revenue_M']:,.0f}M</p>
                    <p style="margin: 3px 0;"><b>Establishments:</b> {int(row['Total_Establishments']):,}</p>
                    <hr style="margin: 5px 0;">
                    <p style="margin: 3px 0;"><b>Power Industries:</b> {row['Power_Share']:.1f}%</p>
                    <p style="margin: 3px 0;"><b>Entertainment:</b> {row['Entertainment_Share']:.1f}%</p>
                    <p style="margin: 3px 0;"><b>Finance:</b> {row['Finance_Share']:.1f}%</p>
                    <hr style="margin: 5px 0;">
                    <p style="margin: 3px 0;"><b>Corporate Score:</b> {row.get('Corporate_Score', row.get('Corp_Power_Index', 0)):.4f}</p>
                    <p style="margin: 3px 0;"><b>Power Index:</b> {row.get('Corp_Power_Index', 0):.1f}</p>
                    <p style="margin: 3px 0; font-size: 10px; color: #666;">Data: U.S. Census Bureau 2021</p>
                </div>
                """
                
                folium.GeoJson(
                    row.geometry,
                    style_function=lambda feature, r=row, sc=score_col: {
                        'fillColor': colormap(r[sc]),
                        'color': 'black',
                        'weight': 1,
                        'fillOpacity': 0.6
                    },
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"ZIP {row['zipcode']}: {score_name} {row[score_col]:.4f}"
                ).add_to(m)
        
        colormap.add_to(m)
    
    # Add airports
    if len(df_airports) > 0:
        airports_nearby = df_airports[
            (df_airports['lat'].between(config['center_lat'] - 2, config['center_lat'] + 2)) &
            (df_airports['lon'].between(config['center_lon'] - 2, config['center_lon'] + 2))
        ]
        
        if len(airports_nearby) > 0:
            airport_cluster = MarkerCluster(name='Airports & Heliports').add_to(m)
            
            for _, apt in airports_nearby.iterrows():
                icon_color = 'blue' if 'heliport' in apt['facility_type'].lower() else 'red'
                icon = 'helicopter' if 'heliport' in apt['facility_type'].lower() else 'plane'
                
                popup_html = f"""
                <div style="font-family: Arial;">
                    <h4>{apt['name']}</h4>
                    <p><b>Type:</b> {apt['facility_type']}</p>
                    <p><b>Code:</b> {apt['code']}</p>
                    <p><b>Ownership:</b> {apt['ownership_label']}</p>
                    <p><b>Use:</b> {apt['use_label']}</p>
                </div>
                """
                
                folium.Marker(
                    [apt['lat'], apt['lon']],
                    popup=folium.Popup(popup_html, max_width=250),
                    tooltip=f"{apt['name']} ({apt['code']})",
                    icon=folium.Icon(color=icon_color, icon=icon, prefix='fa')
                ).add_to(airport_cluster)
    
    # Add main airport marker
    folium.Marker(
        [config['airport_lat'], config['airport_lon']],
        popup=f"<b>{config['airport_code']}</b><br>Main Airport",
        tooltip=config['airport_code'],
        icon=folium.Icon(color='darkred', icon='plane', prefix='fa')
    ).add_to(m)
    
    # Add title
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 400px; height: 90px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
        <h4 style="margin: 0;">{city_name} - Corporate Power Map</h4>
        <p style="margin: 5px 0;"><b>Data:</b> {map_type} - U.S. Census Bureau 2021</p>
        <p style="margin: 5px 0;"><b>ZIPs:</b> {len(gdf_city[gdf_city['Total_Employment'] > 0])}</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    return m

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
    print("\n" + "="*80)
    print("CORPORATE MAPS - REAL CENSUS DATA")
    print("="*80)
    print("\n*** 100% REAL DATA FROM U.S. CENSUS BUREAU ***")
    print("\nOptions:")
    print("  1. ALL ZIPs (30,917 ZIPs) - Complete business data")
    print("  2. TOP 10% RICHEST (272 ZIPs) - Focus on wealthy areas")
    print()
    
    # Create maps for both options
    for filter_top10 in [False, True]:
        map_type = "top10" if filter_top10 else "all"
        print(f"\n{'='*80}")
        print(f"CREATING MAPS: {map_type.upper()}")
        print("="*80)
        
        # Load data
        gdf, df_corp, df_airports = load_data(filter_top10=filter_top10)
        
        if gdf is None or df_corp is None:
            print("[ERROR] Cannot create maps without data!")
            continue
        
        # Create map for each city
        for city_key, config in CITIES.items():
            print(f"\n  Processing {config['name']}...")
            
            # Aggregate data
            gdf_city = aggregate_corporate_data(df_corp, gdf, city_key, config)
            
            if len(gdf_city) == 0:
                print(f"    No data for {config['name']}")
                continue
            
            # Create map
            m = create_city_map(gdf_city, df_airports, city_key, config, filter_top10=filter_top10)
            
            # Save
            output_file = os.path.join(BASE_DIR, f'map_corporate_{city_key}_{map_type}.html')
            m.save(output_file)
            print(f"    Saved: {output_file}")
            print(f"    ZIPs: {len(gdf_city[gdf_city['Total_Employment'] > 0])}")
            print(f"    Total Employment: {int(gdf_city['Total_Employment'].sum()):,}")
            print(f"    Total Revenue: ${gdf_city['Total_Revenue_M'].sum():,.0f}M")
        
        print(f"\n{'='*80}")
        print(f"COMPLETED: {map_type.upper()} MAPS")
        print("="*80)
    
    print("\n" + "="*80)
    print("ALL MAPS CREATED - 100% REAL CENSUS DATA")
    print("="*80)

