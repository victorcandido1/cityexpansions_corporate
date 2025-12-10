# -*- coding: utf-8 -*-
"""
CLUSTER MAPS WITH LAYERS - CLEAR CONNECTIONS
=============================================
Create maps with toggleable layers - one layer per cluster.
Shows CLEAR connections: which ZIPs connect to which heliports/airports.
User can enable/disable each cluster to see connections clearly.
"""

import pandas as pd
import numpy as np
import geopandas as gpd
import folium
from folium import plugins
import os
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLUSTER_RESULTS_FILE = os.path.join(BASE_DIR, 'cluster_results_by_city.csv')
GEOMETRY_FILE = os.path.join(BASE_DIR, '..', 'new_folder', 'cache_geometry.gpkg')
AIRPORTS_FILE = os.path.join(BASE_DIR, '..', 'all-airport-data.xlsx')
GATED_COMMUNITIES_FILE = os.path.join(BASE_DIR, 'gated_communities.csv')

# Cluster colors - vibrant and distinct
CLUSTER_COLORS = [
    '#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6',
    '#1abc9c', '#e67e22', '#34495e', '#16a085', '#c0392b'
]

# =============================================================================
# DATA LOADING
# =============================================================================
def load_all_data():
    """Load cluster results, geometry, and airports"""
    print("="*80)
    print("CLUSTER MAPS WITH TOGGLE LAYERS")
    print("="*80)
    
    df_clusters = pd.read_csv(CLUSTER_RESULTS_FILE, dtype={'zipcode': str})
    print(f"  Cluster results: {len(df_clusters)} ZIPs")
    
    try:
        gdf = gpd.read_file(GEOMETRY_FILE)
        gdf['zipcode'] = gdf['ZCTA5CE20'].astype(str).str.zfill(5)
        print(f"  Geometry: {len(gdf)} ZIP codes")
    except:
        gdf = None
        print("  [!] Geometry not loaded")
    
    df_airports = pd.read_excel(AIRPORTS_FILE)
    df_airports = df_airports.rename(columns={
        'Loc Id': 'code', 'Name': 'name', 'Facility Type': 'facility_type',
        'ARP Latitude DD': 'lat', 'ARP Longitude DD': 'lon', 'Use': 'use'
    })
    df_airports = df_airports.dropna(subset=['lat', 'lon', 'code'])
    df_airports['is_airport'] = df_airports['facility_type'].str.contains('AIRPORT', case=False, na=False)
    df_airports['is_heliport'] = df_airports['facility_type'].str.contains('HELIPORT|HELISTOP', case=False, na=False)
    df_airports['is_hospital'] = df_airports['name'].str.contains('HOSPITAL|MEDICAL|HEALTH', case=False, na=False)
    
    # Filter heliports
    df_heliports = df_airports[
        df_airports['is_heliport'] &
        ((df_airports['use'] == 'PU') | (df_airports['use'] == 'PR') | df_airports['is_hospital'])
    ].copy()
    
    print(f"  Airports: {df_airports['is_airport'].sum()}")
    print(f"  Heliports (filtered): {len(df_heliports)}")
    
    # Load gated communities
    df_gated = pd.read_csv(GATED_COMMUNITIES_FILE)
    print(f"  Gated Communities: {len(df_gated)}")
    
    return df_clusters, gdf, df_airports, df_heliports, df_gated

# =============================================================================
# CREATE MAP WITH LAYERS
# =============================================================================
def create_layered_cluster_map(df_city, gdf, df_airports, df_heliports, df_gated_city, city_name):
    """Create map with one layer per cluster - can toggle on/off"""
    print(f"\n  Creating layered map for {city_name}...")
    
    # Center map
    center_lat = df_city['centroid_lat'].mean()
    center_lon = df_city['centroid_lon'].mean()
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles='CartoDB positron'  # Clean, light background
    )
    
    # Get unique clusters
    clusters = sorted(df_city['kmeans_cluster'].unique())
    
    # Create feature group for each cluster
    for cluster_id in clusters:
        cluster_data = df_city[df_city['kmeans_cluster'] == cluster_id]
        color = CLUSTER_COLORS[cluster_id % len(CLUSTER_COLORS)]
        
        # Create feature group (can be toggled)
        cluster_group = folium.FeatureGroup(
            name=f'<b>Cluster {cluster_id}</b> ({len(cluster_data)} ZIPs)',
            show=True
        )
        
        # Add ZIP polygons for this cluster
        if gdf is not None:
            gdf_cluster = gdf[gdf['zipcode'].isin(cluster_data['zipcode'])].copy()
            
            for _, row in gdf_cluster.iterrows():
                folium.GeoJson(
                    row['geometry'],
                    style_function=lambda x, c=color: {
                        'fillColor': c,
                        'color': 'white',
                        'weight': 2,
                        'fillOpacity': 0.6
                    }
                ).add_to(cluster_group)
        
        # Add ZIP markers with large, visible labels
        for _, row in cluster_data.iterrows():
            folium.CircleMarker(
                location=[row['centroid_lat'], row['centroid_lon']],
                radius=12,
                popup=folium.Popup(
                    f"<b style='font-size:14px'>ZIP {row['zipcode']}</b><br>"
                    f"<b>Cluster {cluster_id}</b><br>"
                    f"Score: {row['Combined_Score']:.3f}<br>"
                    f"Employment: {row['total_employment']:,}<br>"
                    f"Revenue: ${row['estimated_revenue_M']:.1f}M<br>"
                    f"<hr>"
                    f"<b>Airport:</b> {row.get('nearest_airport_code', 'N/A')}<br>"
                    f"⏱️ {row['nearest_airport_time']:.0f} min<br>"
                    f"<b>Heliport:</b> {row.get('fastest_heliport_code', 'N/A')}<br>"
                    f"⏱️ {row.get('fastest_heliport_time', 0):.0f} min",
                    max_width=300
                ),
                tooltip=f"ZIP {row['zipcode']} (Cluster {cluster_id})",
                color='white',
                fillColor=color,
                fillOpacity=0.9,
                weight=3
            ).add_to(cluster_group)
            
            # Add label on top
            folium.Marker(
                location=[row['centroid_lat'], row['centroid_lon']],
                icon=folium.DivIcon(
                    html=f'<div style="font-size: 11px; font-weight: bold; '
                         f'color: white; text-shadow: 1px 1px 2px black;">{row["zipcode"]}</div>'
                )
            ).add_to(cluster_group)
        
        # Find airport used by this cluster
        most_used_airport = cluster_data['nearest_airport_code'].mode()
        if len(most_used_airport) > 0:
            airport_code = most_used_airport[0]
            airport = df_airports[df_airports['code'] == airport_code]
            
            if len(airport) > 0:
                airport = airport.iloc[0]
                
                # Add airport marker
                folium.Marker(
                    location=[airport['lat'], airport['lon']],
                    popup=f"<b>✈️ {airport['code']}</b><br>{airport['name']}<br>"
                          f"<i>Serves Cluster {cluster_id}</i>",
                    tooltip=f"✈️ {airport['code']}",
                    icon=folium.Icon(color='red', icon='plane', prefix='fa')
                ).add_to(cluster_group)
                
                # Add connection lines from EACH ZIP to airport
                for _, zip_row in cluster_data.iterrows():
                    # Line thickness based on speed
                    speed = zip_row.get('avg_speed_kmh', 40)
                    if speed > 60:
                        line_weight = 3
                        line_color = '#2ecc71'  # Green
                    elif speed > 45:
                        line_weight = 2.5
                        line_color = '#f39c12'  # Orange
                    else:
                        line_weight = 2
                        line_color = '#e74c3c'  # Red
                    
                    folium.PolyLine(
                        locations=[
                            [zip_row['centroid_lat'], zip_row['centroid_lon']],
                            [airport['lat'], airport['lon']]
                        ],
                        color=line_color,
                        weight=line_weight,
                        opacity=0.7,
                        popup=f"ZIP {zip_row['zipcode']} → {airport['code']}<br>"
                              f"⏱️ {zip_row['nearest_airport_time']:.0f} min<br>"
                              f"🚗 {speed:.0f} km/h"
                    ).add_to(cluster_group)
        
        # Find heliports used by this cluster (top 5 to ensure coverage)
        heliport_codes = cluster_data['fastest_heliport_code'].dropna().value_counts().head(5)
        
        for heliport_code in heliport_codes.index:
            heliport = df_heliports[df_heliports['code'] == heliport_code]
            
            if len(heliport) > 0:
                heliport = heliport.iloc[0]
                
                # Determine heliport type
                if heliport.get('is_hospital', False):
                    h_color = 'lightblue'
                    h_icon = 'plus'
                    h_type = 'Hospital'
                elif heliport.get('use') == 'PU':
                    h_color = 'green'
                    h_icon = 'helicopter'
                    h_type = 'Public'
                else:
                    h_color = 'purple'
                    h_icon = 'helicopter'
                    h_type = 'Private'
                
                # Add heliport marker
                folium.Marker(
                    location=[heliport['lat'], heliport['lon']],
                    popup=f"<b>🚁 {h_type}</b><br>{heliport['code']}<br>{heliport['name']}<br>"
                          f"<i>Serves {heliport_codes[heliport_code]} ZIPs in Cluster {cluster_id}</i>",
                    tooltip=f"🚁 {heliport['code']} ({h_type})",
                    icon=folium.Icon(color=h_color, icon=h_icon, prefix='fa')
                ).add_to(cluster_group)
                
                # Add connection lines from ZIPs that use THIS heliport
                zips_using = cluster_data[cluster_data['fastest_heliport_code'] == heliport_code]
                
                for _, zip_row in zips_using.iterrows():
                    folium.PolyLine(
                        locations=[
                            [zip_row['centroid_lat'], zip_row['centroid_lon']],
                            [heliport['lat'], heliport['lon']]
                        ],
                        color=color,  # Use cluster color
                        weight=2,
                        opacity=0.6,
                        dash_array='5, 5',  # Dashed line for heliports
                        popup=f"ZIP {zip_row['zipcode']} → 🚁 {heliport['code']}<br>"
                              f"⏱️ {zip_row.get('fastest_heliport_time', 0):.0f} min"
                    ).add_to(cluster_group)
        
        # Add this cluster group to map
        cluster_group.add_to(m)
    
    # =============================================================================
    # ADD ALL KEY HELIPORTS LAYER
    # =============================================================================
    # Create a separate layer for ALL key heliports in the city area
    heliports_layer = folium.FeatureGroup(name='🚁 All Heliports', show=False)
    
    # Filter heliports roughly within the city bounds
    min_lat, max_lat = df_city['centroid_lat'].min() - 0.1, df_city['centroid_lat'].max() + 0.1
    min_lon, max_lon = df_city['centroid_lon'].min() - 0.1, df_city['centroid_lon'].max() + 0.1
    
    city_heliports = df_heliports[
        (df_heliports['lat'].between(min_lat, max_lat)) &
        (df_heliports['lon'].between(min_lon, max_lon))
    ]
    
    for _, heliport in city_heliports.iterrows():
        # Determine heliport type/color
        if heliport.get('is_hospital', False):
            h_color = 'lightblue'
            h_icon = 'plus'
            h_type = 'Hospital'
        elif heliport.get('use') == 'PU':
            h_color = 'green'
            h_icon = 'helicopter'
            h_type = 'Public'
        else:
            h_color = 'purple'
            h_icon = 'helicopter'
            h_type = 'Private'
            
        folium.Marker(
            location=[heliport['lat'], heliport['lon']],
            popup=f"<b>🚁 {h_type}</b><br>{heliport['code']}<br>{heliport['name']}<br>Use: {heliport['use']}",
            tooltip=f"🚁 {heliport['name']} ({heliport['code']})",
            icon=folium.Icon(color=h_color, icon=h_icon, prefix='fa')
        ).add_to(heliports_layer)
        
    heliports_layer.add_to(m)
    
    # =============================================================================
    # ADD WORLD CUP STADIUMS LAYER WITH CONNECTIONS
    # =============================================================================
    # Load stadium data and add to map if applicable for this city
    stadium_file = os.path.join(BASE_DIR, 'world_cup_stadiums.csv')
    stadium_analysis_file = os.path.join(BASE_DIR, 'world_cup_stadiums_analysis.csv')
    
    if os.path.exists(stadium_file) and os.path.exists(stadium_analysis_file):
        df_stadiums = pd.read_csv(stadium_file)
        df_stadium_analysis = pd.read_csv(stadium_analysis_file)
        city_stadium = df_stadiums[df_stadiums['city_name'] == city_name]
        
        if len(city_stadium) > 0:
            stadium = city_stadium.iloc[0]
            stadium_lat = stadium['latitude']
            stadium_lon = stadium['longitude']
            
            # Get analysis data for this stadium
            analysis = df_stadium_analysis[df_stadium_analysis['stadium_name'] == stadium['stadium_name']]
            if len(analysis) > 0:
                analysis = analysis.iloc[0]
                
                # Draw line to closest airport (solid blue line)
                closest_airport_code = analysis['closest_airport_code']
                airport_match = df_airports[df_airports['code'] == closest_airport_code]
                if len(airport_match) > 0:
                    airport = airport_match.iloc[0]
                    
                    # Add PROMINENT marker for stadium's airport
                    folium.Marker(
                        location=[airport['lat'], airport['lon']],
                        popup=f"<b>✈️ {airport['code']}</b><br>"
                              f"<b style='color: #2980b9;'>Stadium Airport</b><br>"
                              f"{airport['name']}<br>"
                              f"<hr>"
                              f"<b>Serves:</b> ⚽ {stadium['stadium_name']}<br>"
                              f"<b>Distance:</b> {analysis['airport_distance_km']:.1f} km",
                        tooltip=f"✈️ {airport['code']} - Stadium Airport",
                        icon=folium.Icon(
                            color='blue',
                            icon='plane',
                            prefix='fa',
                            icon_color='white'
                        )
                    ).add_to(m)
                    
                    # Draw connection line
                    folium.PolyLine(
                        locations=[[stadium_lat, stadium_lon], [airport['lat'], airport['lon']]],
                        color='#2980b9',  # Blue for airport
                        weight=5,
                        opacity=0.9,
                        popup=f"⚽ → ✈️ {closest_airport_code}<br>Distance: {analysis['airport_distance_km']:.1f} km",
                        tooltip=f"Stadium → Airport {closest_airport_code} ({analysis['airport_distance_km']:.1f} km)"
                    ).add_to(m)
                
                # Draw line to closest heliport (dashed green line)
                if pd.notna(analysis['closest_heliport_code']):
                    closest_heliport_code = analysis['closest_heliport_code']
                    heliport_match = df_heliports[df_heliports['code'] == closest_heliport_code]
                    if len(heliport_match) > 0:
                        heliport = heliport_match.iloc[0]
                        
                        # Add PROMINENT marker for stadium's heliport
                        folium.Marker(
                            location=[heliport['lat'], heliport['lon']],
                            popup=f"<b>🚁 {heliport['code']}</b><br>"
                                  f"<b style='color: #27ae60;'>Stadium Heliport</b><br>"
                                  f"{heliport['name']}<br>"
                                  f"<hr>"
                                  f"<b>Serves:</b> ⚽ {stadium['stadium_name']}<br>"
                                  f"<b>Distance:</b> {analysis['heliport_distance_km']:.1f} km",
                            tooltip=f"🚁 {heliport['code']} - Stadium Heliport",
                            icon=folium.Icon(
                                color='lightgreen',
                                icon='helicopter',
                                prefix='fa',
                                icon_color='white'
                            )
                        ).add_to(m)
                        
                        # Draw connection line
                        folium.PolyLine(
                            locations=[[stadium_lat, stadium_lon], [heliport['lat'], heliport['lon']]],
                            color='#27ae60',  # Green for heliport
                            weight=5,
                            opacity=0.9,
                            dash_array='10, 5',  # Dashed line
                            popup=f"⚽ → 🚁 {closest_heliport_code}<br>Distance: {analysis['heliport_distance_km']:.1f} km",
                            tooltip=f"Stadium → Heliport {closest_heliport_code} ({analysis['heliport_distance_km']:.1f} km)"
                        ).add_to(m)
            
            # Add stadium marker with special icon
            folium.Marker(
                location=[stadium_lat, stadium_lon],
                popup=f"<b>⚽ {stadium['stadium_name']}</b><br>"
                      f"<b>World Cup 2026 Venue</b><br>"
                      f"{stadium['address']}<br>"
                      f"<hr>"
                      f"<b>Closest Airport:</b> {analysis['closest_airport_code']} ({analysis['airport_distance_km']:.1f} km)<br>"
                      f"<b>Closest Heliport:</b> {analysis['closest_heliport_code']} ({analysis['heliport_distance_km']:.1f} km)",
                tooltip=f"⚽ {stadium['stadium_name']} (World Cup 2026)",
                icon=folium.Icon(
                    color='darkgreen',
                    icon='futbol-o',
                    prefix='fa',
                    icon_color='white'
                )
            ).add_to(m)
            
            print(f"  Added World Cup stadium: {stadium['stadium_name']} with connections")
    
    # =============================================================================
    # ADD GATED COMMUNITIES LAYER
    # =============================================================================
    if len(df_gated_city) > 0:
        print(f"  Adding {len(df_gated_city)} gated communities...")
        
        # Create separate layers by radius category
        gated_50km = folium.FeatureGroup(name='🏘️ Gated Communities (0-50km)', show=True)
        gated_100km = folium.FeatureGroup(name='🏘️ Gated Communities (50-100km)', show=True)
        gated_200km = folium.FeatureGroup(name='🏘️ Gated Communities (100-200km)', show=True)
        
        for _, community in df_gated_city.iterrows():
            if pd.notna(community['lat']) and pd.notna(community['lon']):
                # Determine which group to add to
                if community['radius_km'] <= 50:
                    feature_group = gated_50km
                    color = 'lightgreen'
                    category = '0-50km (Standard)'
                elif community['radius_km'] <= 100:
                    feature_group = gated_100km
                    color = 'orange'
                    category = '50-100km (Shuttle)'
                else:
                    feature_group = gated_200km
                    color = 'darkred'
                    category = '100-200km (Charter)'
                
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
                            <td>{category}</td>
                        </tr>
                    </table>
                </div>
                """
                
                # Add marker
                folium.Marker(
                    location=[community['lat'], community['lon']],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"<b>{community['community_name']}</b><br>({category})",
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
    folium.LayerControl(
        position='topright',
        collapsed=False  # Keep expanded so user can see all options
    ).add_to(m)
    
    # Add title
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50%; transform: translateX(-50%);
                width: 600px; 
                background-color: white; 
                border: 3px solid #2c3e50;
                border-radius: 10px;
                z-index: 9999; 
                padding: 15px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                text-align: center;">
        <h3 style="margin: 0; color: #2c3e50;">{city_name}</h3>
        <p style="margin: 5px 0; color: #7f8c8d; font-size: 14px;">
            Cluster Analysis: ZIPs × Airport/Heliport Infrastructure
        </p>
        <p style="margin: 5px 0; font-size: 12px; color: #95a5a6;">
            <b>Toggle clusters on/off →</b> (top right)<br>
            Solid lines = Airports | Dashed lines = Heliports
        </p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add legend
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; 
                width: 220px;
                background-color: white; 
                border: 2px solid #dee2e6;
                border-radius: 8px;
                z-index: 9999; 
                padding: 12px;
                font-size: 12px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <b style="font-size: 13px;">Connection Speed:</b><br>
        <span style="color: #2ecc71;">●</span> <b>Green</b> = Fast (>60 km/h)<br>
        <span style="color: #f39c12;">●</span> <b>Orange</b> = Medium (45-60 km/h)<br>
        <span style="color: #e74c3c;">●</span> <b>Red</b> = Slow (<45 km/h)<br>
        <hr style="margin: 8px 0;">
        <b style="font-size: 13px;">Facilities:</b><br>
        ✈️ <b style="color: #e74c3c;">Airports</b> (solid lines)<br>
        🚁 <b style="color: #2ecc71;">Public</b> Heliports (dashed)<br>
        🚁 <b style="color: #9b59b6;">Private</b> Heliports (dashed)<br>
        🏥 <b style="color: #3498db;">Hospital</b> Heliports (dashed)<br>
        <hr style="margin: 8px 0;">
        <b style="font-size: 13px;">Gated Communities:</b><br>
        🏠 <b style="color: lightgreen;">0-50km</b> Standard service<br>
        🏠 <b style="color: orange;">50-100km</b> Shuttle/Full Cabin<br>
        🏠 <b style="color: darkred;">100-200km</b> Charter<br>
        <hr style="margin: 8px 0;">
        ⚽ <b style="color: #196F3D;">World Cup 2026</b> Stadium<br>
        <span style="color: #2980b9; font-weight: bold;">━━</span> Stadium → Airport<br>
        <span style="color: #27ae60; font-weight: bold;">╌╌</span> Stadium → Heliport
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
    print("CLUSTER MAPS WITH TOGGLE LAYERS GENERATION")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Load data
    df_clusters, gdf, df_airports, df_heliports, df_gated = load_all_data()
    
    # Process each city
    cities = df_clusters['city_name'].unique()
    
    for city_name in sorted(cities):
        print(f"\n{'='*80}")
        print(f"PROCESSING: {city_name.upper()}")
        print(f"{'='*80}")
        
        df_city = df_clusters[df_clusters['city_name'] == city_name].copy()
        
        # Filter gated communities for this city
        df_gated_city = df_gated[df_gated['city'] == city_name].copy()
        print(f"  Gated Communities in {city_name}: {len(df_gated_city)}")
        
        # Create map with layers
        m = create_layered_cluster_map(df_city, gdf, df_airports, df_heliports, df_gated_city, city_name)
        
        # Save
        city_slug = city_name.lower().replace(' ', '_')
        output_file = os.path.join(BASE_DIR, f'cluster_layers_{city_slug}.html')
        m.save(output_file)
        
        n_clusters = df_city['kmeans_cluster'].nunique()
        print(f"  Created {n_clusters} toggleable layers")
        print(f"  [✓] Saved: {output_file}")
    
    print(f"\n{'='*80}")
    print("LAYERED CLUSTER MAPS COMPLETE")
    print(f"{'='*80}")
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nGenerated files:")
    print("  - cluster_layers_{city}.html (7 files)")
    print("\nKey features:")
    print("  ✓ One layer per cluster (toggle on/off)")
    print("  ✓ CLEAR connection lines: each ZIP → its airport/heliport")
    print("  ✓ Solid lines = Airports")
    print("  ✓ Dashed lines = Heliports")
    print("  ✓ Line colors = Connection speed (green/orange/red)")
    print("  ✓ Large ZIP markers with codes")
    print("  ✓ Clean, professional design")
    print("\nHow to use:")
    print("  1. Open any cluster_layers_{city}.html file")
    print("  2. Use layer control (top right) to toggle clusters")
    print("  3. Enable just 1-2 clusters to see connections clearly")
    print("  4. Compare how different clusters connect to infrastructure")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()


