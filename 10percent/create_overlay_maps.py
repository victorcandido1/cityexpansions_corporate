# -*- coding: utf-8 -*-
"""
CREATE OVERLAY MAPS - HOUSEHOLDS + CORPORATE
=============================================
Creates maps showing BOTH household wealth and corporate power
on the same visualization (overlay).
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

CITIES = {
    'los_angeles': {
        'name': 'Los Angeles', 'state': 'CA',
        'center_lat': 34.0522, 'center_lon': -118.2437,
        'airport_code': 'LAX', 'airport_lat': 33.9416, 'airport_lon': -118.4085,
        'radius_km': 100, 'zoom': 10,
    },
    'new_york': {
        'name': 'New York', 'state': 'NY',
        'center_lat': 40.7128, 'center_lon': -74.0060,
        'airport_code': 'JFK', 'airport_lat': 40.6413, 'airport_lon': -73.7781,
        'radius_km': 180, 'zoom': 9,
    },
    'chicago': {
        'name': 'Chicago', 'state': 'IL',
        'center_lat': 41.8781, 'center_lon': -87.6298,
        'airport_code': 'ORD', 'airport_lat': 41.9742, 'airport_lon': -87.9073,
        'radius_km': 100, 'zoom': 10,
    },
    'dallas': {
        'name': 'Dallas', 'state': 'TX',
        'center_lat': 32.7767, 'center_lon': -96.7970,
        'airport_code': 'DFW', 'airport_lat': 32.8998, 'airport_lon': -97.0403,
        'radius_km': 100, 'zoom': 10,
    },
    'houston': {
        'name': 'Houston', 'state': 'TX',
        'center_lat': 29.7604, 'center_lon': -95.3698,
        'airport_code': 'IAH', 'airport_lat': 29.9902, 'airport_lon': -95.3368,
        'radius_km': 100, 'zoom': 10,
    },
    'miami': {
        'name': 'Miami', 'state': 'FL',
        'center_lat': 25.7617, 'center_lon': -80.1918,
        'airport_code': 'MIA', 'airport_lat': 25.7959, 'airport_lon': -80.2870,
        'radius_km': 100, 'zoom': 10,
    },
    'san_francisco': {
        'name': 'San Francisco', 'state': 'CA',
        'center_lat': 37.7749, 'center_lon': -122.4194,
        'airport_code': 'SFO', 'airport_lat': 37.6213, 'airport_lon': -122.3790,
        'radius_km': 100, 'zoom': 10,
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
    """Load all necessary data"""
    print("\n" + "="*70)
    print("LOADING DATA")
    print("="*70)
    
    # Geometry
    cache_file = os.path.join(DATA_DIR, 'cache_geometry.gpkg')
    gdf = gpd.read_file(cache_file)
    gdf['zipcode'] = gdf['ZCTA5CE20'].astype(str).str.zfill(5)
    gdf['centroid_lat'] = gdf.geometry.centroid.y
    gdf['centroid_lon'] = gdf.geometry.centroid.x
    print(f"  Geometry: {len(gdf)} ZIP codes")
    
    # Household top 10%
    hh_file = os.path.join(BASE_DIR, 'top10_richest_data.csv')
    df_household = pd.read_csv(hh_file, dtype={'zipcode': str})
    print(f"  Household Top 10%: {len(df_household)} ZIPs")
    
    # Corporate top 10%
    corp_file = os.path.join(BASE_DIR, 'top10_corporate_data.csv')
    df_corporate = pd.read_csv(corp_file, dtype={'zipcode': str})
    print(f"  Corporate Top 10%: {len(df_corporate)} ZIPs")
    
    # Intersection
    int_file = os.path.join(BASE_DIR, 'intersection_analysis.csv')
    df_intersection = pd.read_csv(int_file, dtype={'zipcode': str})
    print(f"  Intersection: {len(df_intersection)} ZIPs")
    
    # Airports
    try:
        df_airports = pd.read_excel(AIRPORTS_FILE)
        df_airports = df_airports[['Name', 'Facility Type', 'Ownership', 'Use', 
                                   'ARP Latitude DD', 'ARP Longitude DD', 'City', 'State Name', 'Loc Id']]
        df_airports = df_airports.dropna(subset=['ARP Latitude DD', 'ARP Longitude DD'])
        df_airports.columns = ['name', 'facility_type', 'ownership', 'use', 'lat', 'lon', 'city', 'state', 'code']
        print(f"  Airports: {len(df_airports)} facilities")
    except Exception as e:
        print(f"  [!] Error loading airports: {e}")
        df_airports = pd.DataFrame()
    
    return gdf, df_household, df_corporate, df_intersection, df_airports

# =============================================================================
# CREATE OVERLAY MAP
# =============================================================================
def create_overlay_map(gdf, df_household, df_corporate, df_intersection, df_airports, city_key, config):
    """Create overlay map showing both household and corporate data"""
    
    city_name = config['name']
    
    # Filter geometry for city
    zip_prefixes = {
        'los_angeles': ['900', '901', '902', '903', '904', '905', '906', '907', '908', '909', 
                        '910', '911', '912', '913', '914', '915', '916', '917', '918',
                        '920', '921', '922', '923', '924', '925', '926', '927', '928'],
        'new_york': ['100', '101', '102', '103', '104', '105', '106', '107', '108', '109',
                     '110', '111', '112', '113', '114', '115', '116', '117', '118', '119',
                     '070', '071', '072', '073', '074', '075', '076', '077', '078', '079'],
        'chicago': ['600', '601', '602', '603', '604', '605', '606', '607', '608', '609'],
        'dallas': ['750', '751', '752', '753', '754', '755', '756', '757', '758', '759',
                   '760', '761', '762', '763'],
        'houston': ['770', '771', '772', '773', '774', '775', '776', '777', '778', '779'],
        'miami': ['330', '331', '332', '333', '334', '335', '336', '337', '338', '339'],
        'san_francisco': ['940', '941', '942', '943', '944', '945', '946', '947', '948', '949'],
    }
    
    gdf_city = gdf[gdf['zipcode'].str[:3].isin(zip_prefixes.get(city_key, []))].copy()
    gdf_city['dist_to_center'] = gdf_city.apply(
        lambda r: haversine_distance(r['centroid_lat'], r['centroid_lon'],
                                    config['center_lat'], config['center_lon']), axis=1
    )
    gdf_city = gdf_city[gdf_city['dist_to_center'] <= config['radius_km']].copy()
    
    # Merge household data
    hh_city = df_household[df_household['city_key'] == city_key]
    gdf_city = gdf_city.merge(
        hh_city[['zipcode', 'Geometric_Score', 'Households_200k', 'AGI_per_return']],
        on='zipcode', how='left'
    )
    gdf_city['is_household_top10'] = gdf_city['Geometric_Score'].notna()
    
    # Merge corporate data
    corp_city = df_corporate[df_corporate['city_key'] == city_key]
    gdf_city = gdf_city.merge(
        corp_city[['zipcode', 'Corporate_Power_Index', 'total_employment', 'estimated_revenue_M', 'power_emp_pct']],
        on='zipcode', how='left'
    )
    gdf_city['is_corporate_top10'] = gdf_city['Corporate_Power_Index'].notna()
    
    # Mark intersection
    int_city = df_intersection[df_intersection['city_key'] == city_key]
    gdf_city['is_intersection'] = gdf_city['zipcode'].isin(int_city['zipcode'].unique())
    
    # Fill NAs
    gdf_city = gdf_city.fillna(0)
    
    # Create map
    m = folium.Map(
        location=[config['center_lat'], config['center_lon']],
        zoom_start=config['zoom'],
        tiles='CartoDB positron'
    )
    
    # Add ZIP polygons with different colors based on category
    for idx, row in gdf_city.iterrows():
        if pd.notna(row.geometry):
            # Determine category and color
            if row['is_intersection']:
                color = '#8B008B'  # Purple - both
                category = 'INTERSECTION'
                opacity = 0.7
            elif row['is_household_top10']:
                color = '#800026'  # Red - household only
                category = 'Household Top 10%'
                opacity = 0.5
            elif row['is_corporate_top10']:
                color = '#0066cc'  # Blue - corporate only
                category = 'Corporate Top 10%'
                opacity = 0.5
            else:
                continue  # Skip if not in either top 10%
            
            # Popup content
            popup_html = f"""
            <div style="font-family: Arial; width: 280px;">
                <h4 style="margin: 5px 0; color: {color};">ZIP Code: {row['zipcode']}</h4>
                <p style="margin: 3px 0; font-weight: bold; color: {color};">{category}</p>
                <hr style="margin: 5px 0;">
"""
            
            if row['is_household_top10']:
                popup_html += f"""
                <p style="margin: 3px 0;"><b>Household Wealth:</b></p>
                <p style="margin: 3px 0; padding-left: 10px;">Score: {row['Geometric_Score']*100:.2f}%</p>
                <p style="margin: 3px 0; padding-left: 10px;">HH $200k+: {int(row['Households_200k']):,}</p>
                <p style="margin: 3px 0; padding-left: 10px;">AGI: ${row['AGI_per_return']:,.0f}</p>
"""
            
            if row['is_corporate_top10']:
                popup_html += f"""
                <p style="margin: 3px 0;"><b>Corporate Power:</b></p>
                <p style="margin: 3px 0; padding-left: 10px;">Power Index: {row['Corporate_Power_Index']:.2f}</p>
                <p style="margin: 3px 0; padding-left: 10px;">Employment: {int(row['total_employment']):,}</p>
                <p style="margin: 3px 0; padding-left: 10px;">Revenue: ${row['estimated_revenue_M']:,.0f}M</p>
                <p style="margin: 3px 0; padding-left: 10px;">Power %: {row['power_emp_pct']:.1f}%</p>
"""
            
            popup_html += """
                <hr style="margin: 5px 0;">
                <p style="margin: 3px 0; font-size: 10px; color: #666;">Data: U.S. Census Bureau 2021</p>
            </div>
            """
            
            folium.GeoJson(
                row.geometry,
                style_function=lambda feature, c=color, o=opacity: {
                    'fillColor': c,
                    'color': 'black',
                    'weight': 2 if o == 0.7 else 1,
                    'fillOpacity': o
                },
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"ZIP {row['zipcode']}: {category}"
            ).add_to(m)
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 200px; height: 150px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
        <h4 style="margin: 0 0 10px 0;">Legend</h4>
        <p style="margin: 5px 0;"><span style="color: #8B008B; font-weight: bold;">■</span> Intersection (Both)</p>
        <p style="margin: 5px 0;"><span style="color: #800026; font-weight: bold;">■</span> Household Top 10%</p>
        <p style="margin: 5px 0;"><span style="color: #0066cc; font-weight: bold;">■</span> Corporate Top 10%</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add title
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 500px; height: 100px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
        <h4 style="margin: 0;">{city_name} - Overlay Map</h4>
        <p style="margin: 5px 0;"><b>Household Wealth + Corporate Power</b></p>
        <p style="margin: 5px 0;">Data: U.S. Census Bureau 2021</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
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
                
                folium.Marker(
                    [apt['lat'], apt['lon']],
                    tooltip=f"{apt['name']} ({apt['code']})",
                    icon=folium.Icon(color=icon_color, icon=icon, prefix='fa')
                ).add_to(airport_cluster)
    
    # Add main airport
    folium.Marker(
        [config['airport_lat'], config['airport_lon']],
        popup=f"<b>{config['airport_code']}</b><br>Main Airport",
        tooltip=config['airport_code'],
        icon=folium.Icon(color='darkred', icon='plane', prefix='fa')
    ).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    return m

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
    print("\n" + "="*80)
    print("OVERLAY MAPS - HOUSEHOLDS + CORPORATE")
    print("="*80)
    print("\n*** 100% REAL DATA ***")
    
    # Load data
    gdf, df_household, df_corporate, df_intersection, df_airports = load_data()
    
    # Create overlay map for each city
    for city_key, config in CITIES.items():
        print(f"\n  Creating overlay map for {config['name']}...")
        
        m = create_overlay_map(gdf, df_household, df_corporate, df_intersection, 
                              df_airports, city_key, config)
        
        # Save
        output_file = os.path.join(BASE_DIR, f'map_overlay_{city_key}.html')
        m.save(output_file)
        print(f"    Saved: {output_file}")
        
        # Count categories
        hh_city = df_household[df_household['city_key'] == city_key]
        corp_city = df_corporate[df_corporate['city_key'] == city_key]
        int_city = df_intersection[df_intersection['city_key'] == city_key]
        
        print(f"    Household Top 10%: {len(hh_city)} ZIPs")
        print(f"    Corporate Top 10%: {len(corp_city)} ZIPs")
        print(f"    Intersection: {len(int_city)} ZIPs")
    
    print("\n" + "="*80)
    print("COMPLETED")
    print("="*80)

