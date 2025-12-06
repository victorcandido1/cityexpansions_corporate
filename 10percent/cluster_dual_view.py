# -*- coding: utf-8 -*-
"""
DUAL CLUSTER VISUALIZATION - AIRPORTS vs HELIPORTS
===================================================
Shows TWO separate cluster analyses side-by-side:
1. Clusters based on AIRPORT access
2. Clusters based on HELIPORT access
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLUSTER_RESULTS_FILE = os.path.join(BASE_DIR, 'cluster_results_by_city.csv')
AIRPORTS_FILE = os.path.join(BASE_DIR, '..', 'all-airport-data.xlsx')

CLUSTER_COLORS = [
    '#667eea', '#f093fb', '#4facfe', '#43e97b', '#fa709a',
    '#feca57', '#48dbfb', '#ff9ff3', '#54a0ff', '#5f27cd'
]

# =============================================================================
# DATA LOADING
# =============================================================================
def load_data():
    """Load data"""
    df_clusters = pd.read_csv(CLUSTER_RESULTS_FILE, dtype={'zipcode': str})
    
    df_airports = pd.read_excel(AIRPORTS_FILE)
    df_airports = df_airports.rename(columns={
        'Loc Id': 'code', 'Name': 'name', 'Facility Type': 'facility_type',
        'ARP Latitude DD': 'lat', 'ARP Longitude DD': 'lon', 'Use': 'use'
    })
    df_airports = df_airports.dropna(subset=['lat', 'lon', 'code'])
    df_airports['is_airport'] = df_airports['facility_type'].str.contains('AIRPORT', case=False, na=False)
    df_airports['is_heliport'] = df_airports['facility_type'].str.contains('HELIPORT|HELISTOP', case=False, na=False)
    df_airports['is_hospital'] = df_airports['name'].str.contains('HOSPITAL|MEDICAL|HEALTH', case=False, na=False)
    
    return df_clusters, df_airports

def create_dual_view(df_city, df_airports_all, city_name):
    """Create side-by-side comparison: Airport Clusters vs Heliport Clusters"""
    print(f"\n  Creating dual view for {city_name}...")
    
    # Create subplots
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Airport-Based Clusters', 'Heliport-Based Clusters'),
        specs=[[{'type': 'scattergeo'}, {'type': 'scattergeo'}]],
        horizontal_spacing=0.01
    )
    
    # =============================================================================
    # LEFT SIDE: AIRPORT CLUSTERS
    # =============================================================================
    
    # Get airport cluster info
    airport_clusters = sorted(df_city['kmeans_cluster'].unique())
    
    for i, cluster_id in enumerate(airport_clusters):
        cluster_data = df_city[df_city['kmeans_cluster'] == cluster_id]
        color = CLUSTER_COLORS[i % len(CLUSTER_COLORS)]
        
        # Add ZIP markers
        fig.add_trace(go.Scattergeo(
            lon=cluster_data['centroid_lon'],
            lat=cluster_data['centroid_lat'],
            mode='markers+text',
            marker=dict(
                size=cluster_data['Combined_Score'] * 100,
                color=color,
                line=dict(width=2.5, color='white'),
                opacity=0.85
            ),
            text=cluster_data['zipcode'],
            textfont=dict(size=9, color='white', family='Helvetica', weight='bold'),
            hovertext=[f"<b>ZIP {row['zipcode']}</b><br>"
                      f"Airport Cluster {cluster_id}<br>"
                      f"Score: {row['Combined_Score']:.3f}<br>"
                      f"Airport: {row.get('nearest_airport_code', 'N/A')}<br>"
                      f"⏱️ {row['nearest_airport_time']:.0f} min"
                      for _, row in cluster_data.iterrows()],
            hoverinfo='text',
            name=f'AC{cluster_id}',
            legendgroup='airport',
            showlegend=True
        ), row=1, col=1)
        
        # Add airport for this cluster
        airport_code = cluster_data['nearest_airport_code'].mode()[0] if len(cluster_data) > 0 else None
        if pd.notna(airport_code):
            airport = df_airports_all[df_airports_all['code'] == airport_code]
            if len(airport) > 0:
                airport = airport.iloc[0]
                fig.add_trace(go.Scattergeo(
                    lon=[airport['lon']],
                    lat=[airport['lat']],
                    mode='markers+text',
                    marker=dict(size=28, color='#ee5a6f', symbol='square',
                               line=dict(width=3, color='white'), opacity=0.95),
                    text=airport['code'],
                    textfont=dict(size=10, color='white', family='Arial', weight='bold'),
                    hovertext=f"<b>✈️ {airport['code']}</b><br>{airport['name']}",
                    hoverinfo='text',
                    showlegend=False
                ), row=1, col=1)
    
    # =============================================================================
    # RIGHT SIDE: HELIPORT CLUSTERS
    # =============================================================================
    
    # Get heliport cluster info
    heliport_clusters = sorted(df_city['heliport_cluster'].unique())
    
    for i, cluster_id in enumerate(heliport_clusters):
        cluster_data = df_city[df_city['heliport_cluster'] == cluster_id]
        color = CLUSTER_COLORS[i % len(CLUSTER_COLORS)]
        
        # Add ZIP markers
        fig.add_trace(go.Scattergeo(
            lon=cluster_data['centroid_lon'],
            lat=cluster_data['centroid_lat'],
            mode='markers+text',
            marker=dict(
                size=cluster_data['Combined_Score'] * 100,
                color=color,
                line=dict(width=2.5, color='white'),
                opacity=0.85
            ),
            text=cluster_data['zipcode'],
            textfont=dict(size=9, color='white', family='Helvetica', weight='bold'),
            hovertext=[f"<b>ZIP {row['zipcode']}</b><br>"
                      f"Heliport Cluster {cluster_id}<br>"
                      f"Score: {row['Combined_Score']:.3f}<br>"
                      f"Heliport: {row.get('fastest_heliport_code', 'N/A')}<br>"
                      f"⏱️ {row.get('fastest_heliport_time', 0):.0f} min"
                      for _, row in cluster_data.iterrows()],
            hoverinfo='text',
            name=f'HC{cluster_id}',
            legendgroup='heliport',
            showlegend=True
        ), row=1, col=2)
        
        # Add top heliport for this cluster
        heliport_code = cluster_data['fastest_heliport_code'].mode()[0] if len(cluster_data) > 0 else None
        if pd.notna(heliport_code):
            heliport = df_airports_all[df_airports_all['code'] == heliport_code]
            if len(heliport) > 0:
                heliport = heliport.iloc[0]
                
                # Color by type
                if heliport.get('is_hospital', False):
                    h_color = '#74b9ff'
                    h_symbol = 'cross'
                elif heliport.get('use') == 'PU':
                    h_color = '#43e97b'
                    h_symbol = 'diamond'
                else:
                    h_color = '#a29bfe'
                    h_symbol = 'diamond'
                
                fig.add_trace(go.Scattergeo(
                    lon=[heliport['lon']],
                    lat=[heliport['lat']],
                    mode='markers+text',
                    marker=dict(size=24, color=h_color, symbol=h_symbol,
                               line=dict(width=3, color='white'), opacity=0.95),
                    text=heliport['code'][:4],
                    textfont=dict(size=8, color='white', family='Arial', weight='bold'),
                    hovertext=f"<b>🚁 {heliport['code']}</b><br>{heliport['name']}",
                    hoverinfo='text',
                    showlegend=False
                ), row=1, col=2)
    
    # Update geo properties for both subplots
    lat_center = df_city['centroid_lat'].mean()
    lon_center = df_city['centroid_lon'].mean()
    
    geo_settings = dict(
        scope='usa',
        center=dict(lat=lat_center, lon=lon_center),
        projection_scale=100,
        showland=True,
        landcolor='#f8f9fa',
        coastlinecolor='#dee2e6',
        showlakes=True,
        lakecolor='#e3f2fd',
        showsubunits=True,
        subunitcolor='#e9ecef'
    )
    
    fig.update_geos(geo_settings, row=1, col=1)
    fig.update_geos(geo_settings, row=1, col=2)
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f'<b style="font-size:24px; color:#2c3e50">{city_name}</b><br>'
                 f'<span style="font-size:16px; color:#7f8c8d">Dual Cluster Analysis: Airports vs Heliports</span><br>'
                 f'<span style="font-size:12px; color:#95a5a6">Left: Airport-based clusters | Right: Heliport-based clusters</span>',
            x=0.5,
            xanchor='center',
            font=dict(family='Helvetica')
        ),
        height=800,
        width=1800,
        showlegend=True,
        legend=dict(
            x=0.01,
            y=0.99,
            bgcolor='rgba(255, 255, 255, 0.97)',
            bordercolor='#dee2e6',
            borderwidth=1,
            font=dict(size=10, family='Helvetica')
        ),
        margin=dict(l=0, r=0, t=140, b=0),
        paper_bgcolor='#ffffff'
    )
    
    return fig

# =============================================================================
# MAIN EXECUTION
# =============================================================================
def main():
    """Main execution function"""
    print("="*80)
    print("DUAL CLUSTER VISUALIZATION - AIRPORTS vs HELIPORTS")
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
        
        df_city = df_clusters[df_clusters['city_name'] == city_name].copy()
        
        # Create dual view
        fig = create_dual_view(df_city, df_airports, city_name)
        
        # Save
        city_slug = city_name.lower().replace(' ', '_')
        output_file = os.path.join(BASE_DIR, f'cluster_dual_{city_slug}.html')
        fig.write_html(output_file)
        print(f"  [✓] Saved: {output_file}")
    
    print(f"\n{'='*80}")
    print("DUAL CLUSTER VISUALIZATIONS COMPLETE")
    print(f"{'='*80}")
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nGenerated files:")
    print("  - cluster_dual_{city}.html (7 files)")
    print("\nFeatures:")
    print("  ✓ Side-by-side comparison")
    print("  ✓ Left: Airport-based clusters")
    print("  ✓ Right: Heliport-based clusters")
    print("  ✓ Same ZIPs, different clustering logic")
    print("  ✓ Clean, clear visualization")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()



