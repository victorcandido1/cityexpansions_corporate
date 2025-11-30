# -*- coding: utf-8 -*-
"""
CORPORATE MAPS - Separate Maps for Corporate Analysis
======================================================
Creates individual maps for each city showing:
- Corporate Power Index by ZIP code
- Power Industries concentration
- Airports and Heliports with layer controls
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
def load_data():
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
    
    # Load corporate data
    corp_file = os.path.join(BASE_DIR, 'industry_by_zip_all.csv')
    if os.path.exists(corp_file):
        df_corp = pd.read_csv(corp_file, dtype={'zipcode': str})
        print(f"  Corporate data: {len(df_corp)} records")
    else:
        df_corp = None
        print("  [!] Corporate data not found - will generate")
    
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
    """Aggregate corporate data for a specific city"""
    
    # Filter geometry for city
    gdf_city = gdf[gdf['zipcode'].str[:3].isin(config['zip_prefixes'])].copy()
    gdf_city['dist_to_center'] = gdf_city.apply(
        lambda r: haversine_distance(r['centroid_lat'], r['centroid_lon'],
                                    config['center_lat'], config['center_lon']), axis=1
    )
    gdf_city = gdf_city[gdf_city['dist_to_center'] <= config['radius_km']].copy()
    
    if df_corp is not None:
        # Aggregate by ZIP
        df_city_corp = df_corp[df_corp['city_key'] == city_key].copy()
        
        # Total metrics
        df_agg = df_city_corp.groupby('zipcode').agg({
            'establishments': 'sum',
            'employment': 'sum',
            'payroll': 'sum',
            'revenue': 'sum'
        }).reset_index()
        df_agg.columns = ['zipcode', 'Total_Establishments', 'Total_Employment', 'Total_Payroll', 'Total_Revenue']
        
        # Power industries
        power_industries = ['51', '52', '53', '54', '55', '71']
        df_power = df_city_corp[df_city_corp['NAICS2'].isin(power_industries)].groupby('zipcode').agg({
            'employment': 'sum',
            'revenue': 'sum'
        }).reset_index()
        df_power.columns = ['zipcode', 'Power_Employment', 'Power_Revenue']
        
        # Entertainment/Media
        ent_industries = ['51', '71']
        df_ent = df_city_corp[df_city_corp['NAICS2'].isin(ent_industries)].groupby('zipcode').agg({
            'employment': 'sum',
            'revenue': 'sum'
        }).reset_index()
        df_ent.columns = ['zipcode', 'Entertainment_Employment', 'Entertainment_Revenue']
        
        # Finance
        df_fin = df_city_corp[df_city_corp['NAICS2'] == '52'].groupby('zipcode').agg({
            'employment': 'sum',
            'revenue': 'sum'
        }).reset_index()
        df_fin.columns = ['zipcode', 'Finance_Employment', 'Finance_Revenue']
        
        # Merge all
        df_agg = df_agg.merge(df_power, on='zipcode', how='left')
        df_agg = df_agg.merge(df_ent, on='zipcode', how='left')
        df_agg = df_agg.merge(df_fin, on='zipcode', how='left')
        df_agg = df_agg.fillna(0)
        
        # Calculate shares
        df_agg['Power_Share'] = df_agg['Power_Employment'] / df_agg['Total_Employment'].replace(0, np.nan) * 100
        df_agg['Entertainment_Share'] = df_agg['Entertainment_Employment'] / df_agg['Total_Employment'].replace(0, np.nan) * 100
        df_agg['Finance_Share'] = df_agg['Finance_Employment'] / df_agg['Total_Employment'].replace(0, np.nan) * 100
        df_agg = df_agg.fillna(0)
        
        # Corporate Power Index
        for col in ['Total_Revenue', 'Total_Employment', 'Power_Share']:
            min_val, max_val = df_agg[col].min(), df_agg[col].max()
            if max_val > min_val:
                df_agg[f'{col}_Norm'] = (df_agg[col] - min_val) / (max_val - min_val)
            else:
                df_agg[f'{col}_Norm'] = 0.5
        
        df_agg['Corp_Power_Index'] = (
            0.4 * df_agg['Total_Revenue_Norm'] +
            0.3 * df_agg['Total_Employment_Norm'] +
            0.3 * df_agg['Power_Share_Norm']
        ) * 100
        
        # Merge with geometry
        gdf_city = gdf_city.merge(df_agg, on='zipcode', how='left')
        gdf_city = gdf_city.fillna(0)
    else:
        # Generate synthetic data
        gdf_city['Total_Employment'] = np.random.randint(100, 50000, len(gdf_city))
        gdf_city['Total_Revenue'] = gdf_city['Total_Employment'] * np.random.uniform(100, 500, len(gdf_city)) * 1000
        gdf_city['Power_Share'] = np.random.uniform(20, 50, len(gdf_city))
        gdf_city['Entertainment_Share'] = np.random.uniform(5, 30, len(gdf_city))
        gdf_city['Finance_Share'] = np.random.uniform(10, 40, len(gdf_city))
        gdf_city['Corp_Power_Index'] = np.random.uniform(20, 80, len(gdf_city))
    
    return gdf_city

# =============================================================================
# CREATE CITY MAP
# =============================================================================
def create_city_map(gdf_city, df_airports, city_key, config):
    """Create corporate map for a specific city"""
    
    city_name = config['name']
    
    # Create map
    m = folium.Map(
        location=[config['center_lat'], config['center_lon']],
        zoom_start=config['zoom'],
        tiles='CartoDB positron'
    )
    
    # Colormap for Corporate Power Index
    if len(gdf_city) > 0 and gdf_city['Corp_Power_Index'].max() > 0:
        colormap = cm.LinearColormap(
            colors=['#ffffcc', '#c7e9b4', '#7fcdbb', '#41b6c4', '#2c7fb8', '#253494'],
            vmin=gdf_city['Corp_Power_Index'].min(),
            vmax=gdf_city['Corp_Power_Index'].max(),
            caption='Corporate Power Index'
        )
        
        def style_function(feature):
            value = feature['properties'].get('Corp_Power_Index', 0)
            return {
                'fillColor': colormap(value) if value > 0 else '#e0e0e0',
                'color': 'black',
                'weight': 0.5,
                'fillOpacity': 0.7
            }
        
        # Format columns for tooltip
        gdf_city['Revenue_Fmt'] = '$' + (gdf_city['Total_Revenue'] / 1e6).round(1).astype(str) + 'M'
        gdf_city['Employment_Fmt'] = gdf_city['Total_Employment'].astype(int).apply(lambda x: f"{x:,}")
        gdf_city['Power_Fmt'] = gdf_city['Power_Share'].round(1).astype(str) + '%'
        gdf_city['Entertainment_Fmt'] = gdf_city['Entertainment_Share'].round(1).astype(str) + '%'
        gdf_city['Finance_Fmt'] = gdf_city['Finance_Share'].round(1).astype(str) + '%'
        gdf_city['Index_Fmt'] = gdf_city['Corp_Power_Index'].round(1).astype(str)
        
        # Add GeoJSON layer
        fg_corporate = folium.FeatureGroup(name='Corporate Power Index', show=True)
        folium.GeoJson(
            gdf_city,
            style_function=style_function,
            tooltip=folium.GeoJsonTooltip(
                fields=['zipcode', 'Index_Fmt', 'Revenue_Fmt', 'Employment_Fmt', 'Power_Fmt', 'Entertainment_Fmt', 'Finance_Fmt'],
                aliases=['ZIP Code', 'Corp Index', 'Revenue', 'Employment', 'Power Ind %', 'Entertainment %', 'Finance %']
            )
        ).add_to(fg_corporate)
        fg_corporate.add_to(m)
        colormap.add_to(m)
    
    # Add airports and heliports
    if not df_airports.empty:
        # Filter airports for this city
        df_airports_city = df_airports.copy()
        df_airports_city['dist'] = df_airports_city.apply(
            lambda r: haversine_distance(r['lat'], r['lon'], config['center_lat'], config['center_lon']), axis=1
        )
        df_airports_city = df_airports_city[df_airports_city['dist'] <= config['radius_km']]
        
        # Create layer groups
        fg_airports_public = folium.FeatureGroup(name='Airports - Public', show=False)
        fg_airports_private = folium.FeatureGroup(name='Airports - Private', show=False)
        fg_airports_military = folium.FeatureGroup(name='Airports - Military', show=False)
        fg_heliports_hospital = folium.FeatureGroup(name='Heliports - Hospital', show=False)
        fg_heliports_military = folium.FeatureGroup(name='Heliports - Military', show=False)
        fg_heliports_public = folium.FeatureGroup(name='Heliports - Public', show=False)
        fg_heliports_private = folium.FeatureGroup(name='Heliports - Private', show=True)
        fg_seaplane = folium.FeatureGroup(name='Seaplane Bases', show=False)
        fg_other = folium.FeatureGroup(name='Other Facilities', show=False)
        
        for _, row in df_airports_city.iterrows():
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
                    folium.Marker([row['lat'], row['lon']], popup=popup,
                        icon=folium.Icon(color='green', icon='plus-square', prefix='fa'),
                        tooltip=f"{row['name']} (Hospital)").add_to(fg_heliports_hospital)
                elif is_military:
                    folium.Marker([row['lat'], row['lon']], popup=popup,
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
                    tooltip=f"{row['name']}").add_to(fg_other)
        
        # Add all layers
        fg_airports_public.add_to(m)
        fg_airports_private.add_to(m)
        fg_airports_military.add_to(m)
        fg_heliports_hospital.add_to(m)
        fg_heliports_military.add_to(m)
        fg_heliports_public.add_to(m)
        fg_heliports_private.add_to(m)
        fg_seaplane.add_to(m)
        fg_other.add_to(m)
    
    # Central airport marker
    fg_central = folium.FeatureGroup(name='Central Airport', show=True)
    folium.Marker(
        [config['airport_lat'], config['airport_lon']],
        popup=f"<b>{config['airport_code']}</b><br>{city_name}<br>CENTRAL AIRPORT",
        icon=folium.Icon(color='darkred', icon='plane', prefix='fa'),
        tooltip=f"{config['airport_code']} - CENTRAL"
    ).add_to(fg_central)
    fg_central.add_to(m)
    
    # Layer control
    folium.LayerControl(collapsed=False, position='bottomright').add_to(m)
    
    # Info panel
    if len(gdf_city) > 0:
        total_emp = gdf_city['Total_Employment'].sum()
        total_rev = gdf_city['Total_Revenue'].sum()
        avg_power = gdf_city['Power_Share'].mean()
        avg_ent = gdf_city['Entertainment_Share'].mean()
        avg_fin = gdf_city['Finance_Share'].mean()
        
        info_html = f"""
        <div style="position: fixed; top: 10px; right: 10px; width: 300px; background-color: white; z-index:9999; 
                    border:2px solid #253494; padding: 12px; font-family: Arial; font-size: 11px; border-radius: 5px; box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">
            <h4 style="margin:0; color: #253494;">CORPORATE ANALYSIS - {city_name.upper()}</h4>
            <p style="margin:5px 0; font-size: 10px; color: #666;">All ZIP Codes - {len(gdf_city)} areas</p>
            <hr style="margin: 5px 0;">
            <table style="width:100%; font-size:10px;">
                <tr><td><b>Total Employment:</b></td><td>{total_emp:,.0f}</td></tr>
                <tr><td><b>Total Revenue:</b></td><td>${total_rev/1e9:.1f}B</td></tr>
                <tr><td><b>Avg Power Ind %:</b></td><td>{avg_power:.1f}%</td></tr>
                <tr><td><b>Avg Entertainment %:</b></td><td>{avg_ent:.1f}%</td></tr>
                <tr><td><b>Avg Finance %:</b></td><td>{avg_fin:.1f}%</td></tr>
            </table>
            <hr style="margin: 5px 0;">
            <p style="margin:3px 0; font-size:9px; color:#666;"><b>Legend (Toggle Layers):</b><br>
            Central Airport | Airports: Pub/Priv/Mil<br>
            Heliports: Hosp/Mil/Pub/Priv</p>
        </div>
        """
        m.get_root().html.add_child(folium.Element(info_html))
    
    return m

# =============================================================================
# CREATE NATIONAL CORPORATE MAP
# =============================================================================
def create_national_map(all_city_data, df_airports):
    """Create national corporate map showing all cities"""
    print("\n  Creating national corporate map...")
    
    m = folium.Map(location=[39.8283, -98.5795], zoom_start=4, tiles='CartoDB positron')
    
    # Combine all city data
    gdf_all = pd.concat(all_city_data.values(), ignore_index=True)
    
    # Colormap
    colormap = cm.LinearColormap(
        colors=['#ffffcc', '#c7e9b4', '#7fcdbb', '#41b6c4', '#2c7fb8', '#253494'],
        vmin=gdf_all['Corp_Power_Index'].min(),
        vmax=gdf_all['Corp_Power_Index'].max(),
        caption='Corporate Power Index'
    )
    
    def style_function(feature):
        value = feature['properties'].get('Corp_Power_Index', 0)
        return {
            'fillColor': colormap(value) if value > 0 else '#e0e0e0',
            'color': 'black',
            'weight': 0.3,
            'fillOpacity': 0.7
        }
    
    # Add GeoJSON
    folium.GeoJson(
        gdf_all,
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(
            fields=['zipcode', 'Index_Fmt', 'Revenue_Fmt', 'Employment_Fmt'],
            aliases=['ZIP', 'Corp Index', 'Revenue', 'Employment']
        )
    ).add_to(m)
    
    colormap.add_to(m)
    
    # Add central airports
    fg_central = folium.FeatureGroup(name='Central Airports', show=True)
    for city_key, config in CITIES.items():
        folium.Marker(
            [config['airport_lat'], config['airport_lon']],
            popup=f"<b>{config['airport_code']}</b><br>{config['name']}",
            icon=folium.Icon(color='darkred', icon='plane', prefix='fa'),
            tooltip=f"{config['airport_code']}"
        ).add_to(fg_central)
    fg_central.add_to(m)
    
    folium.LayerControl().add_to(m)
    
    # Info panel
    total_emp = gdf_all['Total_Employment'].sum()
    total_rev = gdf_all['Total_Revenue'].sum()
    
    info_html = f"""
    <div style="position: fixed; top: 10px; right: 10px; width: 280px; background-color: white; z-index:9999; 
                border:2px solid #253494; padding: 12px; font-family: Arial; font-size: 11px; border-radius: 5px;">
        <h4 style="margin:0; color: #253494;">NATIONAL CORPORATE MAP</h4>
        <p style="margin:5px 0; font-size: 10px;">7 Metro Areas - {len(gdf_all)} ZIP codes</p>
        <hr style="margin: 5px 0;">
        <p><b>Total Employment:</b> {total_emp:,.0f}</p>
        <p><b>Total Revenue:</b> ${total_rev/1e9:.1f}B</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(info_html))
    
    m.save('map_corporate_national.html')
    print("  [OK] map_corporate_national.html")

# =============================================================================
# MAIN
# =============================================================================
def main():
    print("\n" + "="*70)
    print("CORPORATE MAPS GENERATOR")
    print("Creating separate maps for corporate analysis")
    print("="*70)
    
    start_time = datetime.now()
    
    # Load data
    gdf, df_corp, df_airports = load_data()
    
    # Create maps for each city
    print("\n" + "="*70)
    print("CREATING CITY MAPS")
    print("="*70)
    
    all_city_data = {}
    
    for city_key, config in CITIES.items():
        print(f"\n  {config['name']}...", end=" ")
        
        # Aggregate data
        gdf_city = aggregate_corporate_data(df_corp, gdf, city_key, config)
        all_city_data[city_key] = gdf_city
        
        # Create map
        m = create_city_map(gdf_city, df_airports, city_key, config)
        
        # Save
        filename = f'map_corporate_{city_key}.html'
        m.save(filename)
        print(f"[OK] {filename} ({len(gdf_city)} ZIPs)")
    
    # Create national map
    create_national_map(all_city_data, df_airports)
    
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n" + "="*70)
    print(f"COMPLETED in {elapsed:.1f}s")
    print("="*70)
    print("\nGenerated maps:")
    print("  - map_corporate_national.html")
    for city_key in CITIES.keys():
        print(f"  - map_corporate_{city_key}.html")

if __name__ == '__main__':
    main()

