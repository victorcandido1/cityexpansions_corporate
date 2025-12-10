# -*- coding: utf-8 -*-
"""
ADD GATED COMMUNITIES TO CLUSTER MAPS
======================================
Adds gated communities markers to existing cluster analysis maps.

This script loads the gated communities data and adds markers to the 
cluster maps showing where these premium communities are located,
categorized by distance from city center.
"""

import pandas as pd
import numpy as np
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
import branca.colormap as cm
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLUSTER_RESULTS_FILE = os.path.join(BASE_DIR, 'cluster_results_by_city.csv')
GEOMETRY_FILE = os.path.join(BASE_DIR, '..', 'new_folder', 'cache_geometry.gpkg')
AIRPORTS_FILE = os.path.join(BASE_DIR, '..', 'all-airport-data.xlsx')
GATED_COMMUNITIES_FILE = os.path.join(BASE_DIR, 'gated_communities.csv')

# =============================================================================
# DATA LOADING
# =============================================================================
def load_all_data():
    """Load cluster results, geometry, airports, and gated communities"""
    print("="*80)
    print("LOADING DATA FOR VISUALIZATIONS")
    print("="*80)
    
    # Cluster results
    df_clusters = pd.read_csv(CLUSTER_RESULTS_FILE, dtype={'zipcode': str})
    print(f"  Cluster results: {len(df_clusters)} ZIPs")
    
    # Geometry
    try:
        gdf = gpd.read_file(GEOMETRY_FILE)
        gdf['zipcode'] = gdf['ZCTA5CE20'].astype(str).str.zfill(5)
        print(f"  Geometry: {len(gdf)} ZIP codes")
    except Exception as e:
        print(f"  [!] Error loading geometry: {e}")
        gdf = None
    
    # Airports
    df_airports = pd.read_excel(AIRPORTS_FILE)
    df_airports = df_airports.rename(columns={
        'Loc Id': 'code', 'Name': 'name', 'Facility Type': 'facility_type',
        'ARP Latitude DD': 'lat', 'ARP Longitude DD': 'lon'
    })
    df_airports = df_airports.dropna(subset=['lat', 'lon'])
    df_airports['is_airport'] = df_airports['facility_type'].str.contains('AIRPORT', case=False, na=False)
    df_airports['is_heliport'] = df_airports['facility_type'].str.contains('HELIPORT|HELISTOP', case=False, na=False)
    print(f"  Airports/Heliports: {len(df_airports)}")
    
    # Gated Communities
    df_gated = pd.read_csv(GATED_COMMUNITIES_FILE)
    print(f"  Gated Communities: {len(df_gated)}")
    
    return df_clusters, gdf, df_airports, df_gated

# =============================================================================
# FOLIUM MAP WITH GATED COMMUNITIES
# =============================================================================
def create_cluster_map_with_gated(df_city, gdf, df_airports_city, df_gated_city, city_name, city_center):
    """Create interactive Folium map for a city with gated communities"""
    print(f"\n  Creating map for {city_name}...")
    
    # Create base map
    m = folium.Map(
        location=[city_center['lat'], city_center['lon']],
        zoom_start=10,
        tiles='OpenStreetMap'
    )
    
    # Merge with geometry
    if gdf is not None:
        gdf_city = gdf[gdf['zipcode'].isin(df_city['zipcode'])].copy()
        gdf_city = gdf_city.merge(df_city[['zipcode', 'kmeans_cluster', 'Combined_Score',
                                           'nearest_airport_km', 'nearest_airport_name']],
                                 on='zipcode', how='left')
        
        # Create colormap for clusters
        n_clusters = df_city['kmeans_cluster'].nunique()
        cluster_colors = cm.LinearColormap(['#FFF7BC', '#FEC44F', '#D95F0E', '#993404'],
                                          vmin=0, vmax=n_clusters-1,
                                          caption='K-Means Cluster')
        
        # Add ZIP polygons
        folium.GeoJson(
            gdf_city,
            name='ZIP Clusters',
            style_function=lambda x: {
                'fillColor': cluster_colors(x['properties']['kmeans_cluster'])
                            if pd.notna(x['properties'].get('kmeans_cluster')) else 'gray',
                'color': 'black',
                'weight': 0.5,
                'fillOpacity': 0.6
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['zipcode', 'kmeans_cluster', 'Combined_Score', 'nearest_airport_km', 'nearest_airport_name'],
                aliases=['ZIP:', 'Cluster:', 'Combined Score:', 'Distance to Airport (km):', 'Nearest Airport:'],
                localize=True
            )
        ).add_to(m)
        
        cluster_colors.add_to(m)
    
    # Add airport markers
    for _, row in df_airports_city[df_airports_city['is_airport']].iterrows():
        if pd.notna(row['lat']) and pd.notna(row['lon']):
            folium.Marker(
                location=[row['lat'], row['lon']],
                popup=f"<b>{row['name']}</b><br>Code: {row['code']}",
                tooltip=f"{row['code']} - {row['name']}",
                icon=folium.Icon(color='red', icon='plane', prefix='fa')
            ).add_to(m)
            
            # Add radius circles
            for radius_km in [10, 20, 30]:
                folium.Circle(
                    location=[row['lat'], row['lon']],
                    radius=radius_km * 1000,  # Convert to meters
                    color='red' if radius_km == 10 else 'orange' if radius_km == 20 else 'yellow',
                    fill=False,
                    weight=1,
                    opacity=0.3,
                    popup=f'{radius_km}km radius'
                ).add_to(m)
    
    # Add heliport markers
    for _, row in df_airports_city[df_airports_city['is_heliport']].head(50).iterrows():
        if pd.notna(row['lat']) and pd.notna(row['lon']):
            folium.Marker(
                location=[row['lat'], row['lon']],
                popup=f"<b>{row['name']}</b><br>Code: {row['code']}",
                tooltip=f"{row['code']}",
                icon=folium.Icon(color='blue', icon='helicopter', prefix='fa')
            ).add_to(m)
    
    # Add lines connecting ZIPs to nearest airport
    for _, row in df_city.iterrows():
        if pd.notna(row.get('nearest_airport_code')):
            airport_row = df_airports_city[df_airports_city['code'] == row['nearest_airport_code']]
            if len(airport_row) > 0:
                airport_row = airport_row.iloc[0]
                folium.PolyLine(
                    locations=[
                        [row['centroid_lat'], row['centroid_lon']],
                        [airport_row['lat'], airport_row['lon']]
                    ],
                    color='gray',
                    weight=1,
                    opacity=0.3
                ).add_to(m)
    
    # =============================================================================
    # ADD GATED COMMUNITIES MARKERS
    # =============================================================================
    
    # Color coding by radius category
    radius_colors = {
        50: '#FFD700',    # Gold for 0-50km
        100: '#FF8C00',   # Dark Orange for 50-100km
        200: '#FF4500'    # Orange Red for 100-200km
    }
    
    radius_icons = {
        50: 'home',
        100: 'home',
        200: 'home'
    }
    
    # Create feature groups for each category
    gated_50km = folium.FeatureGroup(name='🏘️ Gated Communities (0-50km)', show=True)
    gated_100km = folium.FeatureGroup(name='🏘️ Gated Communities (50-100km)', show=True)
    gated_200km = folium.FeatureGroup(name='🏘️ Gated Communities (100-200km)', show=True)
    
    for _, community in df_gated_city.iterrows():
        if pd.notna(community['lat']) and pd.notna(community['lon']):
            # Determine which group to add to
            if community['radius_km'] <= 50:
                feature_group = gated_50km
                color = 'lightgreen'
            elif community['radius_km'] <= 100:
                feature_group = gated_100km
                color = 'orange'
            else:
                feature_group = gated_200km
                color = 'darkred'
            
            # Create popup with community details
            popup_html = f"""
            <div style="font-family: Arial; min-width: 200px;">
                <h4 style="margin-bottom: 10px; color: #2c3e50;">
                    <i class="fa fa-home"></i> {community['community_name']}
                </h4>
                <hr style="margin: 5px 0;">
                <table style="width: 100%; font-size: 12px;">
                    <tr>
                        <td><b>City:</b></td>
                        <td>{community['city']}</td>
                    </tr>
                    <tr>
                        <td><b>State:</b></td>
                        <td>{community['state']}</td>
                    </tr>
                    <tr>
                        <td><b>Category:</b></td>
                        <td>{'0-50km' if community['radius_km'] <= 50 else '50-100km' if community['radius_km'] <= 100 else '100-200km'}</td>
                    </tr>
                    <tr>
                        <td><b>Coordinates:</b></td>
                        <td>{community['lat']:.4f}, {community['lon']:.4f}</td>
                    </tr>
                </table>
            </div>
            """
            
            # Add marker
            folium.Marker(
                location=[community['lat'], community['lon']],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"<b>{community['community_name']}</b><br>({community['radius_km']}km category)",
                icon=folium.Icon(
                    color=color,
                    icon='home',
                    prefix='fa'
                )
            ).add_to(feature_group)
    
    # Add feature groups to map
    gated_50km.add_to(m)
    gated_100km.add_to(m)
    gated_200km.add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add title
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 500px; height: 80px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:16px; padding: 10px">
    <b>Cluster Analysis: {city_name}</b><br>
    Intersection ZIPs × Airport Infrastructure<br>
    <span style="font-size: 12px; color: #666;">
        + Gated Communities (Premium Residential Areas)
    </span>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add legend for gated communities
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 250px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px">
    <h4 style="margin-top: 0;">Gated Communities Legend</h4>
    <p style="margin: 5px 0;">
        <i class="fa fa-home" style="color: lightgreen;"></i> 0-50km from center
    </p>
    <p style="margin: 5px 0;">
        <i class="fa fa-home" style="color: orange;"></i> 50-100km (Shuttle/Full Cabin)
    </p>
    <p style="margin: 5px 0;">
        <i class="fa fa-home" style="color: darkred;"></i> 100-200km (Charter)
    </p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

# =============================================================================
# MAIN EXECUTION
# =============================================================================
def main():
    """Main execution function"""
    print("="*80)
    print("ADDING GATED COMMUNITIES TO CLUSTER MAPS")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Load data
    df_clusters, gdf, df_airports, df_gated = load_all_data()
    
    # Process each city
    cities = df_clusters['city_name'].unique()
    
    for city_name in sorted(cities):
        print(f"\n{'='*80}")
        print(f"PROCESSING: {city_name.upper()}")
        print(f"{'='*80}")
        
        # Filter data
        df_city = df_clusters[df_clusters['city_name'] == city_name].copy()
        
        # Match city names (handle variations)
        city_matches = {
            'New York': 'New York',
            'Los Angeles': 'Los Angeles', 
            'Chicago': 'Chicago',
            'Dallas': 'Dallas',
            'Houston': 'Houston',
            'Miami': 'Miami',
            'San Francisco': 'San Francisco'
        }
        
        gated_city_name = city_matches.get(city_name, city_name)
        df_gated_city = df_gated[df_gated['city'] == gated_city_name].copy()
        
        print(f"  ZIPs in {city_name}: {len(df_city)}")
        print(f"  Gated Communities in {city_name}: {len(df_gated_city)}")
        
        if len(df_gated_city) == 0:
            print(f"  [!] No gated communities found for {city_name}, skipping...")
            continue
        
        city_center = {
            'lat': df_city['centroid_lat'].mean(),
            'lon': df_city['centroid_lon'].mean()
        }
        
        # Filter airports
        def calc_dist(row):
            R = 6371
            lat1, lon1 = np.radians([city_center['lat'], city_center['lon']])
            lat2, lon2 = np.radians([row['lat'], row['lon']])
            dlat, dlon = lat2 - lat1, lon2 - lon1
            a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
            return R * 2 * np.arcsin(np.sqrt(a))
        
        df_airports['dist_to_city'] = df_airports.apply(calc_dist, axis=1)
        df_airports_city = df_airports[df_airports['dist_to_city'] <= 150].copy()
        
        city_slug = city_name.lower().replace(' ', '_')
        
        # Create Folium map with gated communities
        print("\n  Creating interactive map with gated communities...")
        m = create_cluster_map_with_gated(df_city, gdf, df_airports_city, df_gated_city, 
                                         city_name, city_center)
        map_file = os.path.join(BASE_DIR, f'map_cluster_airports_{city_slug}_with_gated.html')
        m.save(map_file)
        print(f"  [✓] Saved map: {map_file}")
    
    print(f"\n{'='*80}")
    print("GATED COMMUNITIES MAPS COMPLETE")
    print(f"{'='*80}")
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nGenerated files:")
    print("  Maps with Gated Communities:")
    for city_name in sorted(cities):
        city_slug = city_name.lower().replace(' ', '_')
        print(f"    - map_cluster_airports_{city_slug}_with_gated.html")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()

