# -*- coding: utf-8 -*-
"""
CLEAN CLUSTER VISUALIZATION - SIMPLIFIED & CLEAR
=================================================
Focus on visual clarity: show clusters without dense connection lines.
Show only the MOST IMPORTANT heliports per cluster.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
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

# Elegant color palette for clusters
CLUSTER_COLORS = [
    '#667eea', '#f093fb', '#4facfe', '#43e97b', '#fa709a',
    '#feca57', '#48dbfb', '#ff9ff3', '#54a0ff', '#5f27cd'
]

# =============================================================================
# DATA LOADING
# =============================================================================
def load_data():
    """Load clustering results and airport data"""
    print("="*80)
    print("CLEAN CLUSTER VISUALIZATION")
    print("="*80)
    
    df_clusters = pd.read_csv(CLUSTER_RESULTS_FILE, dtype={'zipcode': str})
    print(f"  Cluster results: {len(df_clusters)} ZIPs")
    
    df_airports = pd.read_excel(AIRPORTS_FILE)
    df_airports = df_airports.rename(columns={
        'Loc Id': 'code', 'Name': 'name', 'Facility Type': 'facility_type',
        'ARP Latitude DD': 'lat', 'ARP Longitude DD': 'lon',
        'Use': 'use', 'Ownership': 'ownership'
    })
    df_airports = df_airports.dropna(subset=['lat', 'lon', 'code'])
    df_airports['is_heliport'] = df_airports['facility_type'].str.contains('HELIPORT|HELISTOP', case=False, na=False)
    df_airports['is_hospital'] = df_airports['name'].str.contains('HOSPITAL|MEDICAL|HEALTH', case=False, na=False)
    
    return df_clusters, df_airports

def get_top_heliports_per_cluster(df_city, df_airports, top_n=1):
    """Get only the TOP heliport(s) for each cluster - reduces visual clutter"""
    
    # For each cluster, find the heliport(s) serving the most ZIPs or central to cluster
    cluster_heliports = []
    
    for cluster_id in df_city['kmeans_cluster'].unique():
        cluster_zips = df_city[df_city['kmeans_cluster'] == cluster_id]
        
        # Find heliport codes used by this cluster
        heliport_codes = cluster_zips['fastest_heliport_code'].dropna().value_counts()
        
        # Get top N most-used heliports for this cluster
        top_codes = heliport_codes.head(top_n).index.tolist()
        
        for code in top_codes:
            heliport = df_airports[df_airports['code'] == code]
            if len(heliport) > 0:
                heliport = heliport.iloc[0]
                cluster_heliports.append({
                    'cluster_id': cluster_id,
                    'code': code,
                    'name': heliport['name'],
                    'lat': heliport['lat'],
                    'lon': heliport['lon'],
                    'use': heliport.get('use', 'Unknown'),
                    'is_hospital': heliport.get('is_hospital', False),
                    'num_zips_served': heliport_codes[code]
                })
    
    return pd.DataFrame(cluster_heliports)

def create_clean_cluster_viz(df_city, df_heliports_filtered, city_name):
    """Create CLEAN visualization - clusters + key heliports only"""
    print(f"\n  Creating clean visualization for {city_name}...")
    
    fig = go.Figure()
    
    # Get cluster info
    unique_clusters = sorted(df_city['kmeans_cluster'].unique())
    
    # 1. Add cluster areas (convex hull or just points)
    for i, cluster_id in enumerate(unique_clusters):
        cluster_data = df_city[df_city['kmeans_cluster'] == cluster_id]
        color = CLUSTER_COLORS[i % len(CLUSTER_COLORS)]
        
        # Add ZIP markers for this cluster
        fig.add_trace(go.Scattergeo(
            lon=cluster_data['centroid_lon'],
            lat=cluster_data['centroid_lat'],
            mode='markers+text',
            marker=dict(
                size=cluster_data['Combined_Score'] * 120,  # VERY LARGE
                color=color,
                line=dict(width=3, color='white'),
                opacity=0.85
            ),
            text=cluster_data['zipcode'],
            textposition='middle center',
            textfont=dict(size=10, color='white', family='Helvetica', weight='bold'),
            hovertext=[f"<b>📍 ZIP {row['zipcode']}</b><br>"
                      f"<b>Cluster {cluster_id}</b><br>"
                      f"Score: {row['Combined_Score']:.3f}<br>"
                      f"Employment: {row['total_employment']:,}<br>"
                      f"Revenue: ${row['estimated_revenue_M']:.1f}M<br>"
                      f"<br><b>Heliport Access:</b><br>"
                      f"⏱️ Time: {row.get('fastest_heliport_time', 'N/A')} min<br>"
                      f"🚗 Speed: {row.get('fastest_heliport_speed', 'N/A'):.0f} km/h"
                      for _, row in cluster_data.iterrows()],
            hoverinfo='text',
            name=f'Cluster {cluster_id} ({len(cluster_data)} ZIPs)',
            legendgroup=f'cluster{cluster_id}',
            hoverlabel=dict(bgcolor=color, font_size=12, font_family="Helvetica")
        ))
        
        # Add ONLY the key heliport(s) for this cluster
        cluster_heliports = df_heliports_filtered[df_heliports_filtered['cluster_id'] == cluster_id]
        
        for _, heliport in cluster_heliports.iterrows():
            # Determine symbol and color by type
            if heliport['is_hospital']:
                h_color = '#74b9ff'
                h_symbol = 'cross'
                h_name = '🏥 Hospital'
            elif heliport['use'] == 'PU':
                h_color = '#43e97b'
                h_symbol = 'diamond'
                h_name = '🟢 Public'
            else:
                h_color = '#a29bfe'
                h_symbol = 'diamond'
                h_name = '🟣 Private'
            
            # Add heliport marker (LARGER)
            fig.add_trace(go.Scattergeo(
                lon=[heliport['lon']],
                lat=[heliport['lat']],
                mode='markers+text',
                marker=dict(
                    size=26,  # Larger
                    color=h_color,
                    symbol=h_symbol,
                    line=dict(width=3, color='white'),
                    opacity=0.95
                ),
                text=heliport['code'][:4],  # Short code
                textposition='bottom center',
                textfont=dict(size=8, color=h_color, family='Helvetica', weight='bold'),
                hovertext=f"<b>{h_name} Heliport</b><br>"
                         f"{heliport['code']}<br>"
                         f"<i>{heliport['name']}</i><br>"
                         f"<br>Serves {heliport['num_zips_served']} ZIPs in Cluster {cluster_id}",
                hoverinfo='text',
                name=f"Heliport (C{cluster_id})",
                legendgroup=f'cluster{cluster_id}',
                showlegend=False,
                hoverlabel=dict(bgcolor=h_color, font_size=12)
            ))
            
            # Add CLEAR connection lines from EACH ZIP in cluster to this heliport
            zips_using_this = cluster_data[cluster_data['fastest_heliport_code'] == heliport['code']]
            
            for _, zip_row in zips_using_this.iterrows():
                # Calculate speed for color
                travel_time = zip_row.get('fastest_heliport_time', 10)
                speed = zip_row.get('fastest_heliport_speed', 40)
                
                # Determine line color and style by speed
                if speed > 60:
                    line_color = color  # Use cluster color but bright
                    line_width = 3
                    line_opacity = 0.7
                elif speed > 45:
                    line_color = color
                    line_width = 2.5
                    line_opacity = 0.6
                else:
                    line_color = '#e74c3c'  # Red for slow
                    line_width = 2
                    line_opacity = 0.5
                
                fig.add_trace(go.Scattergeo(
                    lon=[zip_row['centroid_lon'], heliport['lon']],
                    lat=[zip_row['centroid_lat'], heliport['lat']],
                    mode='lines',
                    line=dict(width=line_width, color=line_color),
                    opacity=line_opacity,
                    hovertext=f"ZIP {zip_row['zipcode']} → {heliport['code']}<br>"
                             f"Time: {travel_time:.1f} min | Speed: {speed:.0f} km/h",
                    hoverinfo='text',
                    showlegend=False
                ))
    
    # Update layout - CLEAN & FOCUSED
    lat_center = df_city['centroid_lat'].mean()
    lon_center = df_city['centroid_lon'].mean()
    
    fig.update_geos(
        scope='usa',
        center=dict(lat=lat_center, lon=lon_center),
        projection_scale=100,  # Close zoom
        showland=True,
        landcolor='#f8f9fa',
        coastlinecolor='#dee2e6',
        showlakes=True,
        lakecolor='#e3f2fd',
        showsubunits=True,
        subunitcolor='#e9ecef',
        showrivers=False
    )
    
    # Calculate statistics
    total_zips = len(df_city)
    total_heliports = len(df_heliports_filtered)
    avg_time = df_city['fastest_heliport_time'].mean() if 'fastest_heliport_time' in df_city.columns else 0
    
    fig.update_layout(
        title=dict(
            text=f'<b style="font-size:24px; color:#2c3e50">{city_name}</b><br>'
                 f'<span style="font-size:16px; color:#7f8c8d">Heliport Network Analysis</span><br>'
                 f'<span style="font-size:13px; color:#95a5a6">'
                 f'{total_zips} Premium ZIPs • {total_heliports} Key Heliports • '
                 f'⏱️ Avg {avg_time:.0f} min access</span><br>'
                 f'<span style="font-size:11px; color:#bdc3c7">'
                 f'🟢 Public | 🟣 Private | 🏥 Hospital | Line thickness = Speed</span>',
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
            font=dict(size=12, family='Helvetica'),
            title=dict(text='<b>ZIP Clusters</b>', font=dict(size=13))
        ),
        hovermode='closest',
        margin=dict(l=0, r=0, t=140, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='#ffffff'
    )
    
    print(f"    ZIPs: {total_zips}")
    print(f"    Key heliports shown: {total_heliports}")
    print(f"    Avg access time: {avg_time:.1f} min")
    
    return fig

# =============================================================================
# MAIN EXECUTION
# =============================================================================
def main():
    """Main execution function"""
    print("="*80)
    print("CLEAN CLUSTER VISUALIZATION - HELIPORTS ONLY")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Load data
    df_clusters, df_airports = load_data()
    
    # Filter to only heliports
    df_heliports = df_airports[df_airports['is_heliport']].copy()
    
    # Filter by type: Public, Private, Hospital
    df_heliports['is_hospital'] = df_heliports['name'].str.contains(
        'HOSPITAL|MEDICAL|HEALTH|HOSP', case=False, na=False
    )
    df_heliports = df_heliports[
        (df_heliports['use'] == 'PU') |
        (df_heliports['use'] == 'PR') |
        df_heliports['is_hospital']
    ].copy()
    
    print(f"  Filtered heliports: {len(df_heliports)}")
    
    # Process each city
    cities = df_clusters['city_name'].unique()
    
    for city_name in sorted(cities):
        print(f"\n{'='*80}")
        print(f"PROCESSING: {city_name.upper()}")
        print(f"{'='*80}")
        
        df_city = df_clusters[df_clusters['city_name'] == city_name].copy()
        
        # Get top heliports per cluster (2-3 per cluster for better coverage)
        top_n = 3 if len(df_city) > 30 else 2  # More heliports for larger cities
        df_heliports_filtered = get_top_heliports_per_cluster(df_city, df_heliports, top_n=top_n)
        
        # Create clean visualization
        fig = create_clean_cluster_viz(df_city, df_heliports_filtered, city_name)
        
        # Save
        city_slug = city_name.lower().replace(' ', '_')
        output_file = os.path.join(BASE_DIR, f'cluster_clean_{city_slug}.html')
        fig.write_html(output_file)
        print(f"    [✓] Saved: {output_file}")
    
    print(f"\n{'='*80}")
    print("CLEAN VISUALIZATIONS COMPLETE")
    print(f"{'='*80}")
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nGenerated CLEAN HTML files:")
    print("  - cluster_clean_{city}.html (7 files)")
    print("\nKey improvements:")
    print("  ✓ Top 2-3 heliports per cluster (key hubs)")
    print("  ✓ Clear, visible connection lines (thicker = faster)")
    print("  ✓ Very large ZIP markers with codes visible")
    print("  ✓ Heliports color-coded: Green=Public, Purple=Private, Cyan=Hospital")
    print("  ✓ Direct connections (each ZIP → its heliport)")
    print("  ✓ Clean, professional design")
    print("  ✓ Fully interactive: zoom, pan, hover, click legend")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()

