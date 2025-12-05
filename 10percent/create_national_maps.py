# -*- coding: utf-8 -*-
"""
CREATE NATIONAL MAPS - CORPORATE & INTERSECTION
================================================
Creates national maps showing:
1. Corporate Top 10% across all 7 metros
2. Intersection (Household + Corporate Top 10%) across all 7 metros
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

# City configurations for airport markers
CITIES = {
    'los_angeles': {
        'name': 'Los Angeles', 'state': 'CA',
        'airport_code': 'LAX', 'airport_lat': 33.9416, 'airport_lon': -118.4085,
    },
    'new_york': {
        'name': 'New York', 'state': 'NY',
        'airport_code': 'JFK', 'airport_lat': 40.6413, 'airport_lon': -73.7781,
    },
    'chicago': {
        'name': 'Chicago', 'state': 'IL',
        'airport_code': 'ORD', 'airport_lat': 41.9742, 'airport_lon': -87.9073,
    },
    'dallas': {
        'name': 'Dallas', 'state': 'TX',
        'airport_code': 'DFW', 'airport_lat': 32.8998, 'airport_lon': -97.0403,
    },
    'houston': {
        'name': 'Houston', 'state': 'TX',
        'airport_code': 'IAH', 'airport_lat': 29.9902, 'airport_lon': -95.3368,
    },
    'miami': {
        'name': 'Miami', 'state': 'FL',
        'airport_code': 'MIA', 'airport_lat': 25.7959, 'airport_lon': -80.2870,
    },
    'san_francisco': {
        'name': 'San Francisco', 'state': 'CA',
        'airport_code': 'SFO', 'airport_lat': 37.6213, 'airport_lon': -122.3790,
    }
}

# =============================================================================
# LOAD DATA
# =============================================================================
def load_data():
    """Load all necessary data for national maps"""
    print("\n" + "="*70)
    print("LOADING DATA FOR NATIONAL MAPS")
    print("="*70)
    
    # Geometry - load all ZIP codes
    cache_file = os.path.join(DATA_DIR, 'cache_geometry.gpkg')
    gdf = gpd.read_file(cache_file)
    gdf['zipcode'] = gdf['ZCTA5CE20'].astype(str).str.zfill(5)
    gdf['centroid_lat'] = gdf.geometry.centroid.y
    gdf['centroid_lon'] = gdf.geometry.centroid.x
    print(f"  Geometry: {len(gdf)} ZIP codes")
    
    # Corporate Top 10% - filter only 7 metros
    corp_file = os.path.join(BASE_DIR, 'top10_corporate_data.csv')
    df_corporate = pd.read_csv(corp_file, dtype={'zipcode': str})
    df_corporate = df_corporate[df_corporate['city_key'] != 'other'].copy()
    print(f"  Corporate Top 10% (7 metros): {len(df_corporate)} ZIPs")
    
    # Household Top 10% - filter only 7 metros
    hh_file = os.path.join(BASE_DIR, 'top10_richest_data.csv')
    df_household = pd.read_csv(hh_file, dtype={'zipcode': str})
    df_household = df_household[df_household['city_key'] != 'other'].copy()
    print(f"  Household Top 10% (7 metros): {len(df_household)} ZIPs")
    
    # Intersection
    int_file = os.path.join(BASE_DIR, 'intersection_analysis.csv')
    if os.path.exists(int_file):
        df_intersection = pd.read_csv(int_file, dtype={'zipcode': str})
        df_intersection = df_intersection[df_intersection['city_key'] != 'other'].copy()
        print(f"  Intersection (7 metros): {len(df_intersection)} ZIPs")
    else:
        print("  [!] Intersection file not found, will calculate from data")
        df_intersection = None
    
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
    
    return gdf, df_corporate, df_household, df_intersection, df_airports

# =============================================================================
# CREATE NATIONAL CORPORATE MAP
# =============================================================================
def create_national_corporate_map(gdf, df_corporate, df_airports):
    """Create national map showing Corporate Top 10% across all 7 metros"""
    
    print("\n" + "="*70)
    print("CREATING NATIONAL CORPORATE MAP")
    print("="*70)
    
    # Filter geometry to only ZIPs in corporate top 10%
    corp_zips = set(df_corporate['zipcode'].unique())
    gdf_corp = gdf[gdf['zipcode'].isin(corp_zips)].copy()
    
    # Merge corporate data (including travel time if available)
    corp_cols = ['zipcode', 'city_key', 'city_name', 'Corporate_Score', 
                 'total_employment', 'estimated_revenue_M', 
                 'power_emp_pct', 'power_employment']
    # Check if Travel_Time_Min exists in corporate data
    if 'Travel_Time_Min' in df_corporate.columns:
        corp_cols.append('Travel_Time_Min')
    gdf_corp = gdf_corp.merge(
        df_corporate[corp_cols],
        on='zipcode', how='left'
    )
    
    # Use Corporate_Score
    score_col = 'Corporate_Score'
    score_name = 'Corporate Score'
    
    print(f"  ZIPs to map: {len(gdf_corp)}")
    print(f"  Score column: {score_col}")
    
    # Create map centered on USA
    m = folium.Map(
        location=[39.8283, -98.5795],  # Geographic center of USA
        zoom_start=5,
        tiles='CartoDB positron'
    )
    
    # Create separate FeatureGroups for Score and Travel Time layers
    score_layer = folium.FeatureGroup(name='Corporate Score', show=True).add_to(m)
    travel_time_layer = folium.FeatureGroup(name='Travel Time', show=False).add_to(m)
    
    # Colormap for Corporate Score
    if len(gdf_corp) > 0 and gdf_corp[score_col].max() > gdf_corp[score_col].min():
        colormap = cm.LinearColormap(
            colors=['#fee5d9', '#fcae91', '#fb6a4a', '#de2d26', '#a50f15'],
            vmin=gdf_corp[score_col].min(),
            vmax=gdf_corp[score_col].max(),
            caption=score_name
        )
        
        # Colormap for Travel Time (if available)
        travel_time_colormap = None
        if 'Travel_Time_Min' in gdf_corp.columns:
            travel_times = gdf_corp[gdf_corp['Travel_Time_Min'] > 0]['Travel_Time_Min']
            if len(travel_times) > 0:
                travel_time_colormap = cm.LinearColormap(
                    colors=['#2ecc71', '#f39c12', '#e74c3c'],  # Green to Orange to Red
                    vmin=travel_times.min(),
                    vmax=travel_times.max(),
                    caption='Travel Time (minutes)'
                )
        
        # Add ZIP code polygons - SCORE LAYER
        for idx, row in gdf_corp.iterrows():
            if pd.notna(row.geometry) and pd.notna(row[score_col]):
                # Get travel time and format
                travel_time = row.get('Travel_Time_Min', 0)
                if pd.notna(travel_time) and travel_time > 0:
                    travel_time_str = f"{travel_time:.1f} min"
                    # Color code travel time
                    if travel_time < 30:
                        time_color = '#2ecc71'  # Green - fast
                    elif travel_time < 60:
                        time_color = '#f39c12'  # Orange - medium
                    else:
                        time_color = '#e74c3c'  # Red - slow
                else:
                    travel_time_str = "N/A"
                    time_color = '#95a5a6'  # Gray
                
                popup_html = f"""
                <div style="font-family: Arial; width: 300px;">
                    <h4 style="margin: 5px 0;">ZIP Code: {row['zipcode']}</h4>
                    <p style="margin: 3px 0; color: #666;"><b>{row.get('city_name', 'Unknown')}</b></p>
                    <hr style="margin: 5px 0;">
                    <div style="background-color: #f8f9fa; padding: 8px; border-left: 4px solid {time_color}; margin: 5px 0;">
                        <p style="margin: 0; font-weight: bold; color: #333;">⏱️ Travel Time to Airport</p>
                        <p style="margin: 3px 0; font-size: 18px; font-weight: bold; color: {time_color};">{travel_time_str}</p>
                    </div>
                    <hr style="margin: 5px 0;">
                    <p style="margin: 3px 0;"><b>Corporate Power:</b></p>
                    <p style="margin: 3px 0; padding-left: 10px;">{score_name}: {row[score_col]:.2f}</p>
                    <p style="margin: 3px 0; padding-left: 10px;">Employment: {int(row.get('total_employment', 0)):,}</p>
                    <p style="margin: 3px 0; padding-left: 10px;">Revenue: ${row.get('estimated_revenue_M', 0):,.0f}M</p>
                    <p style="margin: 3px 0; padding-left: 10px;">Power Industries: {row.get('power_emp_pct', 0):.1f}%</p>
                    <hr style="margin: 5px 0;">
                    <p style="margin: 3px 0; font-size: 10px; color: #666;">Data: U.S. Census Bureau 2021</p>
                </div>
                """
                
                # Score-based visualization
                folium.GeoJson(
                    row.geometry,
                    style_function=lambda feature, r=row, sc=score_col: {
                        'fillColor': colormap(r[sc]),
                        'color': 'black',
                        'weight': 1,
                        'fillOpacity': 0.7
                    },
                    popup=folium.Popup(popup_html, max_width=320),
                    tooltip=f"ZIP {row['zipcode']}: {score_name} {row[score_col]:.2f} | Travel: {travel_time_str}"
                ).add_to(score_layer)
        
        colormap.add_to(m)
        
        # Add ZIP code polygons - TRAVEL TIME LAYER (if travel time data available)
        if 'Travel_Time_Min' in gdf_corp.columns and travel_time_colormap is not None:
            for idx, row in gdf_corp.iterrows():
                if pd.notna(row.geometry):
                    travel_time = row.get('Travel_Time_Min', 0)
                    if pd.notna(travel_time) and travel_time > 0:
                        # Determine color based on travel time
                        if travel_time < 30:
                            fill_color = '#2ecc71'  # Green - fast
                        elif travel_time < 60:
                            fill_color = '#f39c12'  # Orange - medium
                        else:
                            fill_color = '#e74c3c'  # Red - slow
                        
                        travel_time_str = f"{travel_time:.1f} min"
                        
                        popup_html = f"""
                        <div style="font-family: Arial; width: 300px;">
                            <h4 style="margin: 5px 0;">ZIP Code: {row['zipcode']}</h4>
                            <p style="margin: 3px 0; color: #666;"><b>{row.get('city_name', 'Unknown')}</b></p>
                            <hr style="margin: 5px 0;">
                            <div style="background-color: #f8f9fa; padding: 8px; border-left: 4px solid {fill_color}; margin: 5px 0;">
                                <p style="margin: 0; font-weight: bold; color: #333;">⏱️ Travel Time to Airport</p>
                                <p style="margin: 3px 0; font-size: 24px; font-weight: bold; color: {fill_color};">{travel_time_str}</p>
                            </div>
                            <hr style="margin: 5px 0;">
                            <p style="margin: 3px 0;"><b>Corporate Power:</b></p>
                            <p style="margin: 3px 0; padding-left: 10px;">{score_name}: {row.get(score_col, 0):.2f}</p>
                            <p style="margin: 3px 0; padding-left: 10px;">Employment: {int(row.get('total_employment', 0)):,}</p>
                            <p style="margin: 3px 0; padding-left: 10px;">Revenue: ${row.get('estimated_revenue_M', 0):,.0f}M</p>
                            <hr style="margin: 5px 0;">
                            <p style="margin: 3px 0; font-size: 10px; color: #666;">Data: Google Maps API</p>
                        </div>
                        """
                        
                        folium.GeoJson(
                            row.geometry,
                            style_function=lambda feature, fc=fill_color: {
                                'fillColor': fc,
                                'color': 'black',
                                'weight': 2,
                                'fillOpacity': 0.8
                            },
                            popup=folium.Popup(popup_html, max_width=320),
                            tooltip=f"ZIP {row['zipcode']}: Travel Time {travel_time_str}"
                        ).add_to(travel_time_layer)
            
            travel_time_colormap.add_to(m)
            print(f"  Added travel time visualization layer")
    
    # Add travel time lines from ZIP centroids to airports (if travel time data available)
    if 'Travel_Time_Min' in gdf_corp.columns:
        travel_time_lines = folium.FeatureGroup(name='Travel Time Routes').add_to(m)
        
        for idx, row in gdf_corp.iterrows():
            if pd.notna(row.geometry) and pd.notna(row[score_col]):
                travel_time = row.get('Travel_Time_Min', 0)
                if pd.notna(travel_time) and travel_time > 0:
                    city_key = row.get('city_key')
                    if city_key and city_key in CITIES:
                        airport = CITIES[city_key]
                        centroid_lat = row.get('centroid_lat')
                        centroid_lon = row.get('centroid_lon')
                        
                        if pd.notna(centroid_lat) and pd.notna(centroid_lon):
                            # Color code by travel time
                            if travel_time < 30:
                                line_color = '#2ecc71'  # Green
                                line_weight = 2
                            elif travel_time < 60:
                                line_color = '#f39c12'  # Orange
                                line_weight = 3
                            else:
                                line_color = '#e74c3c'  # Red
                                line_weight = 4
                            
                            # Draw line from ZIP centroid to airport
                            folium.PolyLine(
                                [[centroid_lat, centroid_lon], 
                                 [airport['airport_lat'], airport['airport_lon']]],
                                color=line_color,
                                weight=line_weight,
                                opacity=0.6,
                                popup=f"Travel Time: {travel_time:.1f} min",
                                tooltip=f"{row['zipcode']} → {airport['airport_code']}: {travel_time:.1f} min"
                            ).add_to(travel_time_lines)
        
        print(f"  Added travel time routes layer")
    
    # Add main airport markers for each metro
    for city_key, config in CITIES.items():
        folium.Marker(
            [config['airport_lat'], config['airport_lon']],
            popup=f"<b>{config['airport_code']}</b><br>{config['name']}",
            tooltip=f"{config['airport_code']} - {config['name']}",
            icon=folium.Icon(color='darkred', icon='plane', prefix='fa')
        ).add_to(m)
    
    # Add travel time legend (if travel time data available)
    if 'Travel_Time_Min' in gdf_corp.columns:
        travel_legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 240px; height: 180px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:12px; padding: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.3);">
            <h4 style="margin: 0 0 8px 0; font-size: 14px;">⏱️ Travel Time to Airport</h4>
            <p style="margin: 3px 0;"><span style="color: #2ecc71; font-weight: bold; font-size: 16px;">━━</span> &lt; 30 min (Fast)</p>
            <p style="margin: 3px 0;"><span style="color: #f39c12; font-weight: bold; font-size: 16px;">━━</span> 30-60 min (Medium)</p>
            <p style="margin: 3px 0;"><span style="color: #e74c3c; font-weight: bold; font-size: 16px;">━━</span> &gt; 60 min (Slow)</p>
            <hr style="margin: 8px 0;">
            <p style="margin: 0; font-size: 10px; color: #666; font-weight: bold;">Toggle Layers:</p>
            <p style="margin: 2px 0; font-size: 10px; color: #666;">• "Corporate Score" = Score colors</p>
            <p style="margin: 2px 0; font-size: 10px; color: #666;">• "Travel Time" = Traffic colors</p>
            <p style="margin: 2px 0; font-size: 10px; color: #666;">• "Travel Time Routes" = Lines</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(travel_legend_html))
    
    # Add title
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 500px; height: 120px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
        <h4 style="margin: 0;">National Corporate Power Map</h4>
        <p style="margin: 5px 0;"><b>Top 10% Corporate ZIPs - 7 Major Metro Areas</b></p>
        <p style="margin: 5px 0;">Total ZIPs: {len(gdf_corp):,}</p>
        <p style="margin: 5px 0;">Data: U.S. Census Bureau 2021 | Travel Times: Google Maps API</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    return m

# =============================================================================
# CREATE NATIONAL INTERSECTION MAP
# =============================================================================
def create_national_intersection_map(gdf, df_household, df_corporate, df_intersection, df_airports):
    """Create national map showing intersection (Household + Corporate Top 10%)"""
    
    print("\n" + "="*70)
    print("CREATING NATIONAL INTERSECTION MAP")
    print("="*70)
    
    # Get all relevant ZIPs
    hh_zips = set(df_household['zipcode'].unique())
    corp_zips = set(df_corporate['zipcode'].unique())
    
    if df_intersection is not None:
        int_zips = set(df_intersection['zipcode'].unique())
    else:
        int_zips = hh_zips & corp_zips
    
    only_hh = hh_zips - int_zips
    only_corp = corp_zips - int_zips
    
    all_relevant_zips = hh_zips | corp_zips
    
    # Filter geometry
    gdf_map = gdf[gdf['zipcode'].isin(all_relevant_zips)].copy()
    
    # Merge household data (including travel time)
    hh_cols = ['zipcode', 'city_key', 'city_name', 'Geometric_Score', 
               'Households_200k', 'AGI_per_return']
    if 'Travel_Time_Min' in df_household.columns:
        hh_cols.append('Travel_Time_Min')
    gdf_map = gdf_map.merge(
        df_household[hh_cols],
        on='zipcode', how='left'
    )
    gdf_map['is_household_top10'] = gdf_map['Geometric_Score'].notna()
    
    # Merge corporate data (including travel time if available)
    corp_cols = ['zipcode', 'Corporate_Score',
                 'total_employment', 'estimated_revenue_M', 'power_emp_pct']
    if 'Travel_Time_Min' in df_corporate.columns:
        corp_cols.append('Travel_Time_Min')
    gdf_map = gdf_map.merge(
        df_corporate[corp_cols],
        on='zipcode', how='left'
    )
    gdf_map['is_corporate_top10'] = gdf_map['Corporate_Score'].notna()
    
    # Use household travel time if available, otherwise corporate
    if 'Travel_Time_Min_x' in gdf_map.columns and 'Travel_Time_Min_y' in gdf_map.columns:
        gdf_map['Travel_Time_Min'] = gdf_map['Travel_Time_Min_x'].fillna(gdf_map['Travel_Time_Min_y'])
        gdf_map = gdf_map.drop(columns=['Travel_Time_Min_x', 'Travel_Time_Min_y'])
    elif 'Travel_Time_Min_x' in gdf_map.columns:
        gdf_map['Travel_Time_Min'] = gdf_map['Travel_Time_Min_x']
        gdf_map = gdf_map.drop(columns=['Travel_Time_Min_x'])
    elif 'Travel_Time_Min_y' in gdf_map.columns:
        gdf_map['Travel_Time_Min'] = gdf_map['Travel_Time_Min_y']
        gdf_map = gdf_map.drop(columns=['Travel_Time_Min_y'])
    
    # Mark intersection
    gdf_map['is_intersection'] = gdf_map['zipcode'].isin(int_zips)
    
    # Fill NAs
    gdf_map = gdf_map.fillna(0)
    
    print(f"  Total ZIPs to map: {len(gdf_map)}")
    print(f"  Intersection: {len(int_zips)} ZIPs")
    print(f"  Only Household: {len(only_hh)} ZIPs")
    print(f"  Only Corporate: {len(only_corp)} ZIPs")
    
    # Create map centered on USA
    m = folium.Map(
        location=[39.8283, -98.5795],  # Geographic center of USA
        zoom_start=5,
        tiles='CartoDB positron'
    )
    
    # Create separate FeatureGroups for Score and Travel Time layers
    score_layer = folium.FeatureGroup(name='Score Visualization', show=True).add_to(m)
    travel_time_layer = folium.FeatureGroup(name='Travel Time Visualization', show=False).add_to(m)
    
    # Prepare travel time colormap if available
    travel_time_colormap = None
    if 'Travel_Time_Min' in gdf_map.columns:
        travel_times = gdf_map[gdf_map['Travel_Time_Min'] > 0]['Travel_Time_Min']
        if len(travel_times) > 0:
            travel_time_colormap = cm.LinearColormap(
                colors=['#2ecc71', '#f39c12', '#e74c3c'],  # Green to Orange to Red
                vmin=travel_times.min(),
                vmax=travel_times.max(),
                caption='Travel Time (minutes)'
            )
    
    # Add ZIP polygons with different colors based on category - SCORE LAYER
    for idx, row in gdf_map.iterrows():
        if pd.notna(row.geometry):
            # Determine category and color
            if row['is_intersection']:
                color = '#8B008B'  # Purple - both
                category = 'INTERSECTION'
                opacity = 0.8
                weight = 2
            elif row['is_household_top10']:
                color = '#800026'  # Red - household only
                category = 'Household Top 10%'
                opacity = 0.6
                weight = 1
            elif row['is_corporate_top10']:
                color = '#0066cc'  # Blue - corporate only
                category = 'Corporate Top 10%'
                opacity = 0.6
                weight = 1
            else:
                continue  # Skip if not in either top 10%
            
            # Get travel time and format
            travel_time = row.get('Travel_Time_Min', 0)
            if pd.notna(travel_time) and travel_time > 0:
                travel_time_str = f"{travel_time:.1f} min"
                # Color code travel time
                if travel_time < 30:
                    time_color = '#2ecc71'  # Green - fast
                elif travel_time < 60:
                    time_color = '#f39c12'  # Orange - medium
                else:
                    time_color = '#e74c3c'  # Red - slow
            else:
                travel_time_str = "N/A"
                time_color = '#95a5a6'  # Gray
            
            # Popup content
            popup_html = f"""
            <div style="font-family: Arial; width: 320px;">
                <h4 style="margin: 5px 0; color: {color};">ZIP Code: {row['zipcode']}</h4>
                <p style="margin: 3px 0; font-weight: bold; color: {color};">{category}</p>
                <p style="margin: 3px 0; color: #666;"><b>{row.get('city_name', 'Unknown')}</b></p>
                <hr style="margin: 5px 0;">
                <div style="background-color: #f8f9fa; padding: 8px; border-left: 4px solid {time_color}; margin: 5px 0;">
                    <p style="margin: 0; font-weight: bold; color: #333;">⏱️ Travel Time to Airport</p>
                    <p style="margin: 3px 0; font-size: 18px; font-weight: bold; color: {time_color};">{travel_time_str}</p>
                </div>
                <hr style="margin: 5px 0;">
"""
            
            if row['is_household_top10']:
                popup_html += f"""
                <p style="margin: 3px 0;"><b>Household Wealth:</b></p>
                <p style="margin: 3px 0; padding-left: 10px;">Geometric Score: {row['Geometric_Score']*100:.2f}%</p>
                <p style="margin: 3px 0; padding-left: 10px;">HH $200k+: {int(row['Households_200k']):,}</p>
                <p style="margin: 3px 0; padding-left: 10px;">AGI: ${row['AGI_per_return']:,.0f}</p>
"""
            
            if row['is_corporate_top10']:
                popup_html += f"""
                <p style="margin: 3px 0;"><b>Corporate Power:</b></p>
                <p style="margin: 3px 0; padding-left: 10px;">Corporate Score: {row['Corporate_Score']:.4f}</p>
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
                style_function=lambda feature, c=color, o=opacity, w=weight: {
                    'fillColor': c,
                    'color': 'black',
                    'weight': w,
                    'fillOpacity': o
                },
                popup=folium.Popup(popup_html, max_width=340),
                tooltip=f"ZIP {row['zipcode']}: {category} | Travel: {travel_time_str}"
            ).add_to(score_layer)
    
    # Add ZIP polygons colored by travel time - TRAVEL TIME LAYER
    if 'Travel_Time_Min' in gdf_map.columns and travel_time_colormap is not None:
        for idx, row in gdf_map.iterrows():
            if pd.notna(row.geometry):
                travel_time = row.get('Travel_Time_Min', 0)
                if pd.notna(travel_time) and travel_time > 0:
                    # Determine category and base color
                    if row['is_intersection']:
                        category = 'INTERSECTION'
                        base_opacity = 0.8
                        weight = 2
                    elif row['is_household_top10']:
                        category = 'Household Top 10%'
                        base_opacity = 0.6
                        weight = 1
                    elif row['is_corporate_top10']:
                        category = 'Corporate Top 10%'
                        base_opacity = 0.6
                        weight = 1
                    else:
                        continue
                    
                    # Color by travel time
                    if travel_time < 30:
                        fill_color = '#2ecc71'  # Green - fast
                    elif travel_time < 60:
                        fill_color = '#f39c12'  # Orange - medium
                    else:
                        fill_color = '#e74c3c'  # Red - slow
                    
                    travel_time_str = f"{travel_time:.1f} min"
                    
                    popup_html = f"""
                    <div style="font-family: Arial; width: 320px;">
                        <h4 style="margin: 5px 0; color: {fill_color};">ZIP Code: {row['zipcode']}</h4>
                        <p style="margin: 3px 0; font-weight: bold; color: {fill_color};">{category}</p>
                        <p style="margin: 3px 0; color: #666;"><b>{row.get('city_name', 'Unknown')}</b></p>
                        <hr style="margin: 5px 0;">
                        <div style="background-color: #f8f9fa; padding: 10px; border-left: 5px solid {fill_color}; margin: 5px 0;">
                            <p style="margin: 0; font-weight: bold; color: #333; font-size: 14px;">⏱️ Travel Time to Airport</p>
                            <p style="margin: 3px 0; font-size: 28px; font-weight: bold; color: {fill_color};">{travel_time_str}</p>
                        </div>
                        <hr style="margin: 5px 0;">
"""
                    
                    if row['is_household_top10']:
                        popup_html += f"""
                        <p style="margin: 3px 0;"><b>Household Wealth:</b></p>
                        <p style="margin: 3px 0; padding-left: 10px;">Geometric Score: {row['Geometric_Score']*100:.2f}%</p>
                        <p style="margin: 3px 0; padding-left: 10px;">HH $200k+: {int(row['Households_200k']):,}</p>
"""
                    
                    if row['is_corporate_top10']:
                        popup_html += f"""
                        <p style="margin: 3px 0;"><b>Corporate Power:</b></p>
                        <p style="margin: 3px 0; padding-left: 10px;">Corporate Score: {row['Corporate_Score']:.4f}</p>
                        <p style="margin: 3px 0; padding-left: 10px;">Employment: {int(row['total_employment']):,}</p>
"""
                    
                    popup_html += """
                        <hr style="margin: 5px 0;">
                        <p style="margin: 3px 0; font-size: 10px; color: #666;">Data: Google Maps API</p>
                    </div>
                    """
                    
                    folium.GeoJson(
                        row.geometry,
                        style_function=lambda feature, fc=fill_color, op=base_opacity, w=weight: {
                            'fillColor': fc,
                            'color': 'black',
                            'weight': w,
                            'fillOpacity': op
                        },
                        popup=folium.Popup(popup_html, max_width=340),
                        tooltip=f"ZIP {row['zipcode']}: {category} | Travel: {travel_time_str}"
                    ).add_to(travel_time_layer)
        
        travel_time_colormap.add_to(m)
        print(f"  Added travel time visualization layer")
    
    # Add travel time lines from ZIP centroids to airports (if travel time data available)
    if 'Travel_Time_Min' in gdf_map.columns:
        travel_time_lines = folium.FeatureGroup(name='Travel Time Routes').add_to(m)
        
        for idx, row in gdf_map.iterrows():
            if pd.notna(row.geometry):
                travel_time = row.get('Travel_Time_Min', 0)
                if pd.notna(travel_time) and travel_time > 0:
                    city_key = row.get('city_key')
                    if city_key and city_key in CITIES:
                        airport = CITIES[city_key]
                        centroid_lat = row.get('centroid_lat')
                        centroid_lon = row.get('centroid_lon')
                        
                        if pd.notna(centroid_lat) and pd.notna(centroid_lon):
                            # Color code by travel time
                            if travel_time < 30:
                                line_color = '#2ecc71'  # Green
                                line_weight = 2
                            elif travel_time < 60:
                                line_color = '#f39c12'  # Orange
                                line_weight = 3
                            else:
                                line_color = '#e74c3c'  # Red
                                line_weight = 4
                            
                            # Draw line from ZIP centroid to airport
                            folium.PolyLine(
                                [[centroid_lat, centroid_lon], 
                                 [airport['airport_lat'], airport['airport_lon']]],
                                color=line_color,
                                weight=line_weight,
                                opacity=0.5,
                                popup=f"Travel Time: {travel_time:.1f} min",
                                tooltip=f"{row['zipcode']} → {airport['airport_code']}: {travel_time:.1f} min"
                            ).add_to(travel_time_lines)
        
        print(f"  Added travel time routes layer")
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 240px; height: 240px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.3);">
        <h4 style="margin: 0 0 10px 0;">Legend</h4>
        <p style="margin: 5px 0;"><span style="color: #8B008B; font-weight: bold; font-size: 18px;">■</span> Intersection (Both)</p>
        <p style="margin: 5px 0;"><span style="color: #800026; font-weight: bold; font-size: 18px;">■</span> Household Top 10%</p>
        <p style="margin: 5px 0;"><span style="color: #0066cc; font-weight: bold; font-size: 18px;">■</span> Corporate Top 10%</p>
        <hr style="margin: 10px 0;">
        <h5 style="margin: 5px 0 5px 0; font-size: 12px;">⏱️ Travel Time</h5>
        <p style="margin: 3px 0; font-size: 11px;"><span style="color: #2ecc71; font-weight: bold;">━━</span> &lt; 30 min</p>
        <p style="margin: 3px 0; font-size: 11px;"><span style="color: #f39c12; font-weight: bold;">━━</span> 30-60 min</p>
        <p style="margin: 3px 0; font-size: 11px;"><span style="color: #e74c3c; font-weight: bold;">━━</span> &gt; 60 min</p>
        <hr style="margin: 8px 0;">
        <p style="margin: 0; font-size: 10px; color: #666; font-weight: bold;">Toggle Layers:</p>
        <p style="margin: 2px 0; font-size: 10px; color: #666;">• "Score Visualization" = Categories</p>
        <p style="margin: 2px 0; font-size: 10px; color: #666;">• "Travel Time Visualization" = Traffic</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add title
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 550px; height: 140px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
        <h4 style="margin: 0;">National Overlay Map</h4>
        <p style="margin: 5px 0;"><b>Household Wealth + Corporate Power - Top 10%</b></p>
        <p style="margin: 5px 0;">Intersection: {len(int_zips):,} ZIPs | Household Only: {len(only_hh):,} | Corporate Only: {len(only_corp):,}</p>
        <p style="margin: 5px 0;">Data: U.S. Census Bureau 2021</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add all airports and heliports near the 7 metros using MarkerCluster
    if len(df_airports) > 0:
        # Create bounds for all 7 metros (expand around each city center)
        airport_cluster = MarkerCluster(name='Airports & Heliports').add_to(m)
        
        # Add airports near each metro area
        for city_key, config in CITIES.items():
            # Filter airports within reasonable distance of each metro (lat/lon ± 2 degrees)
            airports_nearby = df_airports[
                (df_airports['lat'].between(config['airport_lat'] - 2, config['airport_lat'] + 2)) &
                (df_airports['lon'].between(config['airport_lon'] - 2, config['airport_lon'] + 2))
            ]
            
            for _, apt in airports_nearby.iterrows():
                icon_color = 'blue' if 'heliport' in str(apt['facility_type']).lower() else 'red'
                icon = 'helicopter' if 'heliport' in str(apt['facility_type']).lower() else 'plane'
                
                popup_html = f"""
                <div style="font-family: Arial;">
                    <h4>{apt['name']}</h4>
                    <p><b>Type:</b> {apt['facility_type']}</p>
                    <p><b>Code:</b> {apt['code']}</p>
                    <p><b>City:</b> {apt.get('city', 'N/A')}, {apt.get('state', 'N/A')}</p>
                </div>
                """
                
                folium.Marker(
                    [apt['lat'], apt['lon']],
                    popup=folium.Popup(popup_html, max_width=250),
                    tooltip=f"{apt['name']} ({apt['code']})",
                    icon=folium.Icon(color=icon_color, icon=icon, prefix='fa')
                ).add_to(airport_cluster)
        
        print(f"  Added airports/heliports to map")
    
    # Add main airport markers for each metro (highlighted)
    for city_key, config in CITIES.items():
        folium.Marker(
            [config['airport_lat'], config['airport_lon']],
            popup=f"<b>{config['airport_code']}</b><br>{config['name']}<br><i>Main Airport</i>",
            tooltip=f"{config['airport_code']} - {config['name']} (Main)",
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
    print("CREATE NATIONAL MAPS - CORPORATE & INTERSECTION")
    print("="*80)
    print("\n*** 100% REAL DATA FROM U.S. CENSUS BUREAU ***")
    print("\nCreating maps for:")
    print("  1. Corporate Top 10% (National)")
    print("  2. Intersection Total (National)")
    print()
    
    # Load data
    gdf, df_corporate, df_household, df_intersection, df_airports = load_data()
    
    if gdf is None or len(df_corporate) == 0:
        print("[ERROR] Cannot create maps without data!")
        exit(1)
    
    # 1. Create National Corporate Map
    print("\n" + "="*80)
    print("1. NATIONAL CORPORATE MAP")
    print("="*80)
    m_corp = create_national_corporate_map(gdf, df_corporate, df_airports)
    output_corp = os.path.join(BASE_DIR, 'map_corporate_national.html')
    m_corp.save(output_corp)
    print(f"\n  [OK] Saved: {output_corp}")
    
    # 2. Create National Intersection Map
    print("\n" + "="*80)
    print("2. NATIONAL INTERSECTION MAP")
    print("="*80)
    m_int = create_national_intersection_map(gdf, df_household, df_corporate, df_intersection, df_airports)
    output_int = os.path.join(BASE_DIR, 'map_intersection_national.html')
    m_int.save(output_int)
    print(f"\n  [OK] Saved: {output_int}")
    
    print("\n" + "="*80)
    print("ALL NATIONAL MAPS CREATED")
    print("="*80)

