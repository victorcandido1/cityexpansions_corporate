# -*- coding: utf-8 -*-
"""
CLUSTER NETWORK GRAPHS - INTERACTIVE VERSION
=============================================
Generate INTERACTIVE network graph visualizations using Plotly.
Shows only airports/heliports that have actual connections to intersection ZIPs.
"""

import pandas as pd
import numpy as np
import networkx as nx
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLUSTER_RESULTS_FILE = os.path.join(BASE_DIR, 'cluster_results_by_city.csv')
AIRPORTS_FILE = os.path.join(BASE_DIR, '..', 'all-airport-data.xlsx')

MAIN_AIRPORTS = ['LAX', 'JFK', 'ORD', 'DFW', 'IAH', 'MIA', 'SFO']

CITY_COLORS = {
    'Los Angeles': '#FF6B6B',
    'New York': '#4ECDC4',
    'Chicago': '#45B7D1',
    'Dallas': '#F7B731',
    'Houston': '#5F27CD',
    'Miami': '#FF9FF3',
    'San Francisco': '#54A0FF'
}

# =============================================================================
# DATA LOADING
# =============================================================================
def load_data():
    """Load clustering results and airport data"""
    print("="*80)
    print("LOADING DATA FOR INTERACTIVE NETWORK GRAPHS")
    print("="*80)
    
    # Load cluster results
    df_clusters = pd.read_csv(CLUSTER_RESULTS_FILE, dtype={'zipcode': str})
    print(f"  Cluster results: {len(df_clusters)} ZIPs")
    
    # Load airports
    df_airports = pd.read_excel(AIRPORTS_FILE)
    df_airports = df_airports.rename(columns={
        'Loc Id': 'code',
        'Name': 'name',
        'Facility Type': 'facility_type',
        'ARP Latitude DD': 'lat',
        'ARP Longitude DD': 'lon',
        'Use': 'use',
        'Ownership': 'ownership'
    })
    df_airports = df_airports.dropna(subset=['lat', 'lon', 'code'])
    df_airports['is_airport'] = df_airports['facility_type'].str.contains('AIRPORT', case=False, na=False)
    df_airports['is_heliport'] = df_airports['facility_type'].str.contains('HELIPORT|HELISTOP', case=False, na=False)
    
    print(f"  Airports/Heliports: {len(df_airports)}")
    
    return df_clusters, df_airports

def get_connected_facilities(df_city, df_airports):
    """Get only airports/heliports that are actually connected to ZIPs"""
    connected_codes = set()
    
    # Get nearest airport codes
    airport_codes = df_city['nearest_airport_code'].dropna().unique()
    connected_codes.update(airport_codes)
    
    # Get fastest heliport codes
    heliport_codes = df_city['fastest_heliport_code'].dropna().unique()
    connected_codes.update(heliport_codes)
    
    # Filter airports to only connected ones
    df_connected = df_airports[df_airports['code'].isin(connected_codes)].copy()
    
    # Filter heliports: only Public, Private, and Hospital
    # Check facility_type and name for hospital keywords
    if len(df_connected) > 0:
        df_connected['is_hospital'] = (
            df_connected['name'].str.contains('HOSPITAL|MEDICAL|HEALTH|HOSP', case=False, na=False) |
            df_connected['facility_type'].str.contains('HOSPITAL|MEDICAL', case=False, na=False)
        )
        
        # For heliports, keep only: Public use (PU), Private (PR), or Hospital
        heliport_mask = df_connected['is_heliport']
        public_private_hospital = (
            (df_connected['use'] == 'PU') |  # Public
            (df_connected['use'] == 'PR') |  # Private
            df_connected['is_hospital']       # Hospital
        )
        
        # Keep all airports, but filter heliports
        df_connected = df_connected[
            df_connected['is_airport'] | (heliport_mask & public_private_hospital)
        ].copy()
    
    return df_connected

# =============================================================================
# INTERACTIVE NETWORK GRAPH WITH PLOTLY
# =============================================================================
def create_interactive_network_plotly(df_city, df_airports_connected, city_name):
    """Create interactive network graph using Plotly"""
    print(f"\n  Creating interactive network graph for {city_name}...")
    
    # Prepare data for visualization
    zip_data = []
    airport_data = []
    heliport_data = []
    edges_data = []
    
    # Collect ZIP data with ELEGANT cluster colors (softer palette)
    unique_clusters = sorted(df_city['kmeans_cluster'].unique())
    
    # Professional color palette - softer, more elegant
    elegant_colors = [
        '#667eea',  # Soft purple
        '#f093fb',  # Soft pink
        '#4facfe',  # Sky blue
        '#43e97b',  # Mint green
        '#fa709a',  # Rose
        '#feca57',  # Warm yellow
        '#48dbfb',  # Cyan
        '#ff9ff3',  # Light magenta
        '#54a0ff',  # Ocean blue
        '#5f27cd',  # Deep purple
    ]
    
    cluster_colors_map = {
        cluster: elegant_colors[i % len(elegant_colors)]
        for i, cluster in enumerate(unique_clusters)
    }
    
    for _, row in df_city.iterrows():
        zip_data.append({
            'lon': row['centroid_lon'],
            'lat': row['centroid_lat'],
            'zipcode': row['zipcode'],
            'cluster': row['kmeans_cluster'],
            'score': row['Combined_Score'],
            'employment': row['total_employment'],
            'revenue': row['estimated_revenue_M'],
            'travel_time': row['nearest_airport_time'],
            'speed': row.get('avg_speed_kmh', 40),
            'color': cluster_colors_map[row['kmeans_cluster']]
        })
        
        # ONLY connect to FASTEST heliport (NO AIRPORTS)
        if pd.notna(row.get('fastest_heliport_code')):
            heliport_match = df_airports_connected[df_airports_connected['code'] == row['fastest_heliport_code']]
            if len(heliport_match) > 0:
                heliport = heliport_match.iloc[0]
                travel_time = row.get('fastest_heliport_time', 30)
                heliport_dist = row.get('fastest_heliport_km', 10)
                speed = row.get('fastest_heliport_speed', 40)
                
                # Color by speed for heliport connections
                if speed > 60:
                    edge_color = 'rgba(67, 233, 123, 0.5)'  # Soft green - fast
                elif speed > 45:
                    edge_color = 'rgba(254, 202, 87, 0.5)'  # Soft yellow - medium
                else:
                    edge_color = 'rgba(250, 112, 154, 0.5)'  # Soft pink - slow
                
                edges_data.append({
                    'zip_lon': row['centroid_lon'],
                    'zip_lat': row['centroid_lat'],
                    'facility_lon': heliport['lon'],
                    'facility_lat': heliport['lat'],
                    'type': 'Heliport',
                    'code': heliport['code'],
                    'name': heliport['name'],
                    'travel_time': travel_time,
                    'speed': speed,
                    'color': edge_color,
                    'width': max(1.0, 3 * (100.0 / (1.0 + travel_time)))
                })
    
    # Collect heliport data (only connected) - separated by type
    # NOTE: NOT collecting airport data anymore - HELIPORTS ONLY
    heliport_public = []
    heliport_private = []
    heliport_hospital = []
    
    for _, row in df_airports_connected[df_airports_connected['is_heliport']].iterrows():
        heliport_info = {
            'lon': row['lon'],
            'lat': row['lat'],
            'code': row['code'],
            'name': row['name'],
            'use': row.get('use', 'Unknown')
        }
        
        # Categorize
        if row.get('is_hospital', False):
            heliport_hospital.append(heliport_info)
        elif row.get('use') == 'PU':
            heliport_public.append(heliport_info)
        elif row.get('use') == 'PR':
            heliport_private.append(heliport_info)
    
    heliport_data = {
        'public': heliport_public,
        'private': heliport_private,
        'hospital': heliport_hospital
    }
    
    total_heliports = (len(heliport_data['public']) + len(heliport_data['private']) + 
                       len(heliport_data['hospital']))
    
    print(f"    ZIPs: {len(zip_data)}")
    print(f"    Heliports: {total_heliports} (Public: {len(heliport_data['public'])}, "
          f"Private: {len(heliport_data['private'])}, Hospital: {len(heliport_data['hospital'])})")
    print(f"    Edges: {len(edges_data)}")
    
    # Create Plotly figure
    fig = go.Figure()
    
    # Add edges first (so they appear behind nodes)
    for edge in edges_data:
        fig.add_trace(go.Scattergeo(
            lon=[edge['zip_lon'], edge['facility_lon']],
            lat=[edge['zip_lat'], edge['facility_lat']],
            mode='lines',
            line=dict(width=edge['width'], color=edge['color']),
            hoverinfo='text',
            text=f"{edge['type']}: {edge['code']}<br>Time: {edge['travel_time']:.1f} min<br>Speed: {edge['speed']:.0f} km/h",
            showlegend=False
        ))
    
    # Add ZIP nodes by cluster - ELEGANT & LARGER
    for cluster_id in unique_clusters:
        cluster_zips = [z for z in zip_data if z['cluster'] == cluster_id]
        
        fig.add_trace(go.Scattergeo(
            lon=[z['lon'] for z in cluster_zips],
            lat=[z['lat'] for z in cluster_zips],
            mode='markers+text',
            marker=dict(
                size=[max(18, z['score'] * 100) for z in cluster_zips],  # LARGER & clearer
                color=cluster_zips[0]['color'] if cluster_zips else 'gray',
                line=dict(width=2.5, color='white'),
                opacity=0.85,
                symbol='circle'
            ),
            text=[z['zipcode'] for z in cluster_zips],  # Show ZIP code
            textposition='middle center',
            textfont=dict(size=9, color='white', family='Helvetica', weight='bold'),
            hovertext=[f"<b>📍 ZIP {z['zipcode']}</b><br>"
                      f"<b>Cluster {z['cluster']}</b><br>"
                      f"Combined Score: {z['score']:.3f}<br>"
                      f"Employment: {z['employment']:,}<br>"
                      f"Revenue: ${z['revenue']:.1f}M<br>"
                      f"<br><b>Airport Access:</b><br>"
                      f"⏱️ Travel Time: {z['travel_time']:.1f} min<br>"
                      f"🚗 Avg Speed: {z['speed']:.0f} km/h"
                      for z in cluster_zips],
            hoverinfo='text',
            name=f'Cluster {cluster_id}',
            hoverlabel=dict(
                bgcolor=cluster_zips[0]['color'] if cluster_zips else 'gray',
                font_size=12,
                font_family="Helvetica"
            )
        ))
    
    # AIRPORTS REMOVED - SHOWING ONLY HELIPORTS
    
    # Add heliport nodes - PUBLIC (elegant green)
    if heliport_data['public']:
        fig.add_trace(go.Scattergeo(
            lon=[h['lon'] for h in heliport_data['public']],
            lat=[h['lat'] for h in heliport_data['public']],
            mode='markers',
            marker=dict(
                size=16, 
                color='#43e97b',  # Soft green
                symbol='diamond', 
                line=dict(width=2, color='white'), 
                opacity=0.85
            ),
            hovertext=[f"<b>🚁 Public</b><br>{h['code']}<br><i>{h['name']}</i>" 
                      for h in heliport_data['public']],
            hoverinfo='text',
            name='🚁 Public'
        ))
    
    # Add heliport nodes - PRIVATE (elegant purple)
    if heliport_data['private']:
        fig.add_trace(go.Scattergeo(
            lon=[h['lon'] for h in heliport_data['private']],
            lat=[h['lat'] for h in heliport_data['private']],
            mode='markers',
            marker=dict(
                size=14, 
                color='#a29bfe',  # Soft purple
                symbol='diamond',
                line=dict(width=2, color='white'), 
                opacity=0.80
            ),
            hovertext=[f"<b>🚁 Private</b><br>{h['code']}<br><i>{h['name']}</i>" 
                      for h in heliport_data['private']],
            hoverinfo='text',
            name='🚁 Private'
        ))
    
    # Add heliport nodes - HOSPITAL (elegant cyan)
    if heliport_data['hospital']:
        fig.add_trace(go.Scattergeo(
            lon=[h['lon'] for h in heliport_data['hospital']],
            lat=[h['lat'] for h in heliport_data['hospital']],
            mode='markers',
            marker=dict(
                size=16, 
                color='#74b9ff',  # Medical blue
                symbol='diamond',
                line=dict(width=2, color='white'), 
                opacity=0.90
            ),
            hovertext=[f"<b>🏥 Hospital</b><br>{h['code']}<br><i>{h['name']}</i>" 
                      for h in heliport_data['hospital']],
            hoverinfo='text',
            name='🏥 Hospital'
        ))
    
    # Calculate bounds for better zoom
    lat_min, lat_max = df_city['centroid_lat'].min(), df_city['centroid_lat'].max()
    lon_min, lon_max = df_city['centroid_lon'].min(), df_city['centroid_lon'].max()
    lat_range = lat_max - lat_min
    lon_range = lon_max - lon_min
    
    # Add 10% padding
    lat_center = (lat_min + lat_max) / 2
    lon_center = (lon_min + lon_max) / 2
    
    # Update layout - CLEAN & MODERN DESIGN
    fig.update_geos(
        scope='usa',
        center=dict(lat=lat_center, lon=lon_center),
        projection_scale=80,
        showland=True,
        landcolor='#f8f9fa',  # Very light gray background
        coastlinecolor='#dee2e6',
        showlakes=True,
        lakecolor='#e3f2fd',  # Light blue
        showcountries=False,
        showsubunits=True,
        subunitcolor='#e9ecef',
        showrivers=False
    )
    
    fig.update_layout(
        title=dict(
            text=f'<b style="font-size:20px; color:#2c3e50">{city_name}</b><br>'
                 f'<span style="font-size:14px; color:#7f8c8d">Network: Intersection ZIPs × Heliports</span><br>'
                 f'<span style="font-size:11px; color:#95a5a6">Speed: '
                 f'<span style="color:#43e97b">●</span> Fast (>60km/h) | '
                 f'<span style="color:#feca57">●</span> Medium | '
                 f'<span style="color:#fa709a">●</span> Slow | '
                 f'🟢 Public | 🟣 Private | 🏥 Hospital</span>',
            x=0.5,
            xanchor='center',
            font=dict(family='Helvetica')
        ),
        height=1000,
        showlegend=True,
        legend=dict(
            x=0.01,
            y=0.99,
            bgcolor='rgba(255, 255, 255, 0.97)',
            bordercolor='#dee2e6',
            borderwidth=1,
            font=dict(size=11, family='Helvetica')
        ),
        hovermode='closest',
        margin=dict(l=0, r=0, t=100, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='#ffffff'
    )
    
    return fig

def create_national_network_plotly(df_all, df_airports):
    """Create interactive national network graph"""
    print(f"\n  Creating interactive national network graph...")
    
    # Get only main airports that are connected
    connected_airport_codes = df_all['nearest_airport_code'].dropna().unique()
    main_connected = [code for code in MAIN_AIRPORTS if code in connected_airport_codes]
    df_main_airports = df_airports[df_airports['code'].isin(main_connected)].copy()
    
    print(f"    Main airports shown: {len(df_main_airports)} (out of {len(MAIN_AIRPORTS)})")
    
    # Create figure
    fig = go.Figure()
    
    # Add edges - SOFTER, MORE ELEGANT
    for _, row in df_all.iterrows():
        if pd.notna(row.get('nearest_airport_code')) and row['nearest_airport_code'] in main_connected:
            airport = df_main_airports[df_main_airports['code'] == row['nearest_airport_code']]
            if len(airport) > 0:
                airport = airport.iloc[0]
                speed = row.get('avg_speed_kmh', 40)
                travel_time = row.get('nearest_airport_time', 30)
                
                # Color by speed - SOFTER palette
                if speed > 60:
                    color = 'rgba(67, 233, 123, 0.25)'  # Soft green
                elif speed > 45:
                    color = 'rgba(254, 202, 87, 0.25)'  # Soft yellow
                else:
                    color = 'rgba(250, 112, 154, 0.25)'  # Soft pink
                
                width = max(0.5, 2 * (100.0 / (1.0 + travel_time)))
                
                fig.add_trace(go.Scattergeo(
                    lon=[row['centroid_lon'], airport['lon']],
                    lat=[row['centroid_lat'], airport['lat']],
                    mode='lines',
                    line=dict(width=width, color=color),
                    hoverinfo='skip',
                    showlegend=False
                ))
    
    # Add ZIP nodes by city - ELEGANT & CONSISTENT
    for city_name, color in CITY_COLORS.items():
        city_data = df_all[df_all['city_name'] == city_name]
        
        if len(city_data) == 0:
            continue
        
        fig.add_trace(go.Scattergeo(
            lon=city_data['centroid_lon'],
            lat=city_data['centroid_lat'],
            mode='markers',
            marker=dict(
                size=city_data['Combined_Score'] * 50,  # LARGER & more visible
                color=color,
                line=dict(width=2, color='white'),
                opacity=0.85,
                symbol='circle'
            ),
            hovertext=[f"<b>📍 ZIP {row['zipcode']}</b><br>"
                      f"<b>{row['city_name']}</b><br>"
                      f"Score: {row['Combined_Score']:.3f}<br>"
                      f"⏱️ Time: {row['nearest_airport_time']:.1f} min<br>"
                      f"🚗 Speed: {row.get('avg_speed_kmh', 40):.0f} km/h"
                      for _, row in city_data.iterrows()],
            hoverinfo='text',
            name=city_name,
            hoverlabel=dict(
                bgcolor=color,
                font_size=12,
                font_family="Helvetica"
            )
        ))
    
    # Add main airport nodes - ELEGANT & PROMINENT
    fig.add_trace(go.Scattergeo(
        lon=df_main_airports['lon'],
        lat=df_main_airports['lat'],
        mode='markers+text',
        marker=dict(
            size=35, 
            color='#ee5a6f',  # Elegant red
            symbol='square', 
            line=dict(width=3, color='white'), 
            opacity=0.95
        ),
        text=df_main_airports['code'],
        textposition='middle center',
        textfont=dict(size=11, color='white', family='Helvetica', weight='bold'),
        hovertext=[f"<b>✈️ {row['code']}</b><br><i>{row['name']}</i>" 
                  for _, row in df_main_airports.iterrows()],
        hoverinfo='text',
        name='✈️ Major Airports',
        hoverlabel=dict(
            bgcolor='#ee5a6f',
            font_size=13,
            font_family="Helvetica"
        )
    ))
    
    # Update layout - PROFESSIONAL DESIGN
    fig.update_geos(
        scope='usa',
        projection_type='albers usa',
        showland=True,
        landcolor='#f8f9fa',
        coastlinecolor='#dee2e6',
        showlakes=True,
        lakecolor='#e3f2fd',
        showsubunits=True,
        subunitcolor='#e9ecef'
    )
    
    fig.update_layout(
        title=dict(
            text='<b style="font-size:22px; color:#2c3e50">National Network Overview</b><br>'
                 f'<span style="font-size:15px; color:#7f8c8d">197 Premium ZIPs across 7 Metropolitan Areas</span><br>'
                 '<span style="font-size:11px; color:#95a5a6">🔍 Interactive: Zoom, Pan & Explore | Click legend to filter</span>',
            x=0.5,
            xanchor='center',
            font=dict(family='Helvetica')
        ),
        height=1000,
        showlegend=True,
        legend=dict(
            x=0.01,
            y=0.99,
            bgcolor='rgba(255, 255, 255, 0.97)',
            bordercolor='#dee2e6',
            borderwidth=1,
            font=dict(size=11, family='Helvetica'),
            title=dict(text='<b>Legend</b>', font=dict(size=12))
        ),
        hovermode='closest',
        margin=dict(l=0, r=0, t=120, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='#ffffff'
    )
    
    return fig

# =============================================================================
# MAIN EXECUTION
# =============================================================================
def main():
    """Main execution function"""
    print("="*80)
    print("INTERACTIVE CLUSTER NETWORK GRAPHS GENERATION")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Load data
    df_clusters, df_airports = load_data()
    
    # Process each city
    cities = df_clusters['city_name'].unique()
    
    for city_name in sorted(cities):
        print(f"\n{'='*80}")
        print(f"PROCESSING: {city_name.upper()}")
        print(f"{'='*80}")
        
        # Filter data for city
        df_city = df_clusters[df_clusters['city_name'] == city_name].copy()
        
        # Get only connected facilities (not all thousands)
        df_airports_connected = get_connected_facilities(df_city, df_airports)
        
        print(f"  Total ZIPs: {len(df_city)}")
        print(f"  Connected airports: {df_airports_connected['is_airport'].sum()}")
        print(f"  Connected heliports: {df_airports_connected['is_heliport'].sum()}")
        
        # Create interactive Plotly network graph
        fig = create_interactive_network_plotly(df_city, df_airports_connected, city_name)
        
        # Save as HTML
        city_slug = city_name.lower().replace(' ', '_')
        output_file = os.path.join(BASE_DIR, f'network_interactive_{city_slug}.html')
        fig.write_html(output_file)
        print(f"    [✓] Saved: {output_file}")
    
    # Create national network graph
    print(f"\n{'='*80}")
    print("CREATING NATIONAL INTERACTIVE NETWORK GRAPH")
    print(f"{'='*80}")
    
    fig_national = create_national_network_plotly(df_clusters, df_airports)
    output_file_national = os.path.join(BASE_DIR, 'network_interactive_national.html')
    fig_national.write_html(output_file_national)
    print(f"  [✓] Saved: {output_file_national}")
    
    print(f"\n{'='*80}")
    print("INTERACTIVE NETWORK GRAPHS COMPLETE")
    print(f"{'='*80}")
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nGenerated INTERACTIVE HTML files (with zoom, pan, hover):")
    print("  - network_interactive_{city}.html (7 files)")
    print("  - network_interactive_national.html")
    print("\nFeatures:")
    print("  ✓ Zoom in/out with mouse wheel")
    print("  ✓ Pan by dragging")
    print("  ✓ Hover for detailed information")
    print("  ✓ Click legend to show/hide clusters")
    print("  ✓ Edge colors show speed: Green=Fast, Orange=Medium, Red=Slow")
    print("  ✓ Only shows connected airports/heliports (not all 19,768!)")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
