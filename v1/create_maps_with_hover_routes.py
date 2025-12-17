#!/usr/bin/env python3
"""
Create interactive maps with routes that appear on hover
- Routes from ZIP codes to helipads
- Routes from ZIP codes to airports
- Routes appear only when mouse hovers over ZIP code
"""

import pandas as pd
import folium
from folium import plugins
import json
import requests
import os

# City-specific traffic multipliers
CITY_MULTIPLIERS = {
    'NY': {'fast': 1.0, 'normal': 1.35, 'rush': 1.69, 'worst': 5.20},
    'LA': {'fast': 1.0, 'normal': 1.42, 'rush': 1.77, 'worst': 4.15}
}

AIRPORTS = {
    'NY': {'coords': (40.6413, -73.7781), 'name': 'JFK International Airport'},
    'LA': {'coords': (33.9425, -118.4081), 'name': 'LAX International Airport'}
}

OSRM_SERVERS = {
    'NY': 'http://localhost:5000',
    'LA': 'http://localhost:5001'
}

def get_osrm_route(origin, destination, city):
    """Get route from OSRM"""
    try:
        server = OSRM_SERVERS[city]
        url = f"{server}/route/v1/driving/{origin[1]},{origin[0]};{destination[1]},{destination[0]}?overview=full&geometries=geojson"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['code'] == 'Ok' and data['routes']:
                return data['routes'][0]['geometry']['coordinates']
    except:
        pass
    return None

def create_hover_map(city: str, df: pd.DataFrame, output_path: str):
    """Create interactive map with hover routes"""
    
    airport = AIRPORTS[city]
    mults = CITY_MULTIPLIERS[city]
    center = [airport['coords'][0], airport['coords'][1]]
    
    # Create base map
    m = folium.Map(
        location=center, 
        zoom_start=10, 
        tiles='CartoDB positron',
        prefer_canvas=True
    )
    
    # Add airport marker
    folium.Marker(
        location=airport['coords'],
        popup=f"<b>✈️ {airport['name']}</b>",
        icon=folium.Icon(color='red', icon='plane', prefix='fa'),
        tooltip="Main Airport"
    ).add_to(m)
    
    # Add heliports
    heliports = df[['facility_code', 'facility_name', 'facility_lat', 'facility_lon']].drop_duplicates()
    heli_group = folium.FeatureGroup(name='🚁 Heliports')
    for _, h in heliports.iterrows():
        folium.Marker(
            location=[h['facility_lat'], h['facility_lon']],
            popup=f"<b>🚁 {h['facility_name']}</b><br>Code: {h['facility_code']}",
            icon=folium.Icon(color='orange', icon='helicopter', prefix='fa'),
            tooltip=h['facility_name']
        ).add_to(heli_group)
    heli_group.add_to(m)
    
    # Create route groups (initially hidden)
    routes_data = []
    
    print(f"Processing {len(df)} ZIP codes for {city}...")
    
    for idx, row in df.iterrows():
        zipcode = str(row['zipcode'])
        origin = (row['origin_lat'], row['origin_lon'])
        heli_dest = (row['facility_lat'], row['facility_lon'])
        airport_dest = airport['coords']
        is_manhattan = row.get('is_manhattan', False)
        
        # Get savings
        savings = row.get('worst_savings_min', 0)
        if savings > 100:
            color = '#1a7f37'  # dark green
        elif savings > 50:
            color = '#2ea043'  # green
        elif savings > 0:
            color = '#f0883e'  # orange
        else:
            color = '#cf222e'  # red
        
        # Get routes from OSRM (or use straight line as fallback)
        route_to_heli = get_osrm_route(origin, heli_dest, city)
        route_to_airport = get_osrm_route(origin, airport_dest, city)
        
        # Convert to lat/lon format for Leaflet
        if route_to_heli:
            route_to_heli_latlon = [[c[1], c[0]] for c in route_to_heli]
        else:
            route_to_heli_latlon = [[origin[0], origin[1]], [heli_dest[0], heli_dest[1]]]
            
        if route_to_airport:
            route_to_airport_latlon = [[c[1], c[0]] for c in route_to_airport]
        else:
            route_to_airport_latlon = [[origin[0], origin[1]], [airport_dest[0], airport_dest[1]]]
        
        # Store route data for JavaScript
        routes_data.append({
            'zipcode': zipcode,
            'origin': [origin[0], origin[1]],
            'heli_route': route_to_heli_latlon,
            'airport_route': route_to_airport_latlon,
            'heli_name': row['facility_name'],
            'heli_code': row['facility_code'],
            'color': color,
            'savings': savings,
            'is_manhattan': is_manhattan,
            'fast_heli': row.get('fast_heli_total_min', 0),
            'rush_heli': row.get('rush_heli_total_min', 0),
            'worst_heli': row.get('worst_heli_total_min', 0),
            'fast_car': row.get('fast_car_direct_min', 0),
            'rush_car': row.get('rush_car_direct_min', 0),
            'worst_car': row.get('worst_car_direct_min', 0),
            'flight_time': row.get('flight_time_min', 0),
            'heli_dist_km': row.get('facility_km', 0),
            'airport_dist_km': row.get('car_to_airport_dist_km', 0)
        })
        
        # Create popup HTML
        popup_html = f"""
        <div style="width:380px; font-family: Arial, sans-serif; font-size: 12px;">
            <h4 style="margin:0; color: #333; border-bottom: 2px solid {color}; padding-bottom: 5px;">
                ZIP {zipcode} {'🏙️ MANHATTAN' if is_manhattan else ''}
            </h4>
            
            <div style="display: flex; margin-top: 8px;">
                <div style="flex: 1; padding-right: 10px;">
                    <h5 style="margin: 0 0 5px 0; color: #666;">🚁 To Helipad</h5>
                    <b>{row['facility_name']}</b><br>
                    Distance: {row['facility_km']:.1f} km<br>
                    Flight: {row['flight_time_min']:.0f} min
                </div>
                <div style="flex: 1; padding-left: 10px; border-left: 1px solid #ddd;">
                    <h5 style="margin: 0 0 5px 0; color: #666;">✈️ To Airport</h5>
                    <b>{airport['name']}</b><br>
                    Distance: {row['car_to_airport_dist_km']:.1f} km
                </div>
            </div>
            
            <h5 style="margin: 10px 0 5px 0; color: #666;">
                ⏱️ Travel Times (Multipliers: Fast 1.0x | Rush {mults['rush']}x | Worst {mults['worst']}x)
            </h5>
            <table style="width:100%; border-collapse: collapse; font-size: 11px;">
                <tr style="background:#f5f5f5;">
                    <th style="padding:4px; text-align:left;">Mode</th>
                    <th style="padding:4px;">Fast</th>
                    <th style="padding:4px;">Rush</th>
                    <th style="padding:4px; background:#ffe0e0;">WORST</th>
                </tr>
                <tr>
                    <td style="padding:4px;">🚁 Helicopter</td>
                    <td style="padding:4px; text-align:center;">{row.get('fast_heli_total_min', 0):.0f} min</td>
                    <td style="padding:4px; text-align:center;">{row.get('rush_heli_total_min', 0):.0f} min</td>
                    <td style="padding:4px; text-align:center; background:#ffe0e0;"><b>{row.get('worst_heli_total_min', 0):.0f} min</b></td>
                </tr>
                <tr style="background:#f9f9f9;">
                    <td style="padding:4px;">🚗 Car Direct</td>
                    <td style="padding:4px; text-align:center;">{row.get('fast_car_direct_min', 0):.0f} min</td>
                    <td style="padding:4px; text-align:center;">{row.get('rush_car_direct_min', 0):.0f} min</td>
                    <td style="padding:4px; text-align:center; background:#ffe0e0;"><b>{row.get('worst_car_direct_min', 0):.0f} min</b></td>
                </tr>
            </table>
            
            <div style="margin-top: 8px; padding: 8px; background: {color}20; border-left: 4px solid {color}; border-radius: 4px;">
                <b style="color: {color};">💰 SAVINGS (Worst Case): {savings:.0f} min</b>
            </div>
        </div>
        """
        
        # Add ZIP code marker with custom ID
        marker = folium.CircleMarker(
            location=[origin[0], origin[1]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=400),
            tooltip=f"ZIP {zipcode} - Savings: {savings:.0f} min"
        )
        marker._name = f"zip_{zipcode}"
        marker.add_to(m)
        
        if (idx + 1) % 10 == 0:
            print(f"  Processed {idx + 1}/{len(df)} ZIP codes...")
    
    # Add custom JavaScript for hover routes
    routes_json = json.dumps(routes_data)
    
    hover_js = f"""
    <script>
    // Store route data
    var routesData = {routes_json};
    
    // Global variables to store current routes
    var currentHeliRoute = null;
    var currentAirportRoute = null;
    var map = null;
    
    // Wait for map to be ready
    document.addEventListener('DOMContentLoaded', function() {{
        // Find the map object
        var mapContainer = document.querySelector('.folium-map');
        if (mapContainer) {{
            var mapId = mapContainer.id;
            map = window[mapId];
            
            // Add event listeners to all circle markers
            map.eachLayer(function(layer) {{
                if (layer instanceof L.CircleMarker) {{
                    var latlng = layer.getLatLng();
                    
                    // Find matching route data
                    var routeInfo = routesData.find(function(r) {{
                        return Math.abs(r.origin[0] - latlng.lat) < 0.001 && 
                               Math.abs(r.origin[1] - latlng.lng) < 0.001;
                    }});
                    
                    if (routeInfo) {{
                        layer.on('mouseover', function(e) {{
                            showRoutes(routeInfo);
                        }});
                        
                        layer.on('mouseout', function(e) {{
                            hideRoutes();
                        }});
                    }}
                }}
            }});
        }}
    }});
    
    function showRoutes(routeInfo) {{
        hideRoutes();  // Clear any existing routes
        
        // Draw route to helipad (blue dashed)
        if (routeInfo.heli_route && routeInfo.heli_route.length > 0) {{
            currentHeliRoute = L.polyline(routeInfo.heli_route, {{
                color: '#2196F3',
                weight: 4,
                opacity: 0.8,
                dashArray: '10, 5'
            }}).addTo(map);
            
            // Add animated arrow
            var decorator = L.polylineDecorator(currentHeliRoute, {{
                patterns: [
                    {{offset: '50%', repeat: 0, symbol: L.Symbol.arrowHead({{
                        pixelSize: 12,
                        polygon: false,
                        pathOptions: {{stroke: true, color: '#2196F3', weight: 3}}
                    }})}}
                ]
            }}).addTo(map);
            currentHeliRoute.decorator = decorator;
        }}
        
        // Draw route to airport (red dashed)
        if (routeInfo.airport_route && routeInfo.airport_route.length > 0) {{
            currentAirportRoute = L.polyline(routeInfo.airport_route, {{
                color: '#f44336',
                weight: 4,
                opacity: 0.8,
                dashArray: '10, 5'
            }}).addTo(map);
            
            // Add animated arrow
            var decorator2 = L.polylineDecorator(currentAirportRoute, {{
                patterns: [
                    {{offset: '50%', repeat: 0, symbol: L.Symbol.arrowHead({{
                        pixelSize: 12,
                        polygon: false,
                        pathOptions: {{stroke: true, color: '#f44336', weight: 3}}
                    }})}}
                ]
            }}).addTo(map);
            currentAirportRoute.decorator = decorator2;
        }}
    }}
    
    function hideRoutes() {{
        if (currentHeliRoute) {{
            if (currentHeliRoute.decorator) {{
                map.removeLayer(currentHeliRoute.decorator);
            }}
            map.removeLayer(currentHeliRoute);
            currentHeliRoute = null;
        }}
        if (currentAirportRoute) {{
            if (currentAirportRoute.decorator) {{
                map.removeLayer(currentAirportRoute.decorator);
            }}
            map.removeLayer(currentAirportRoute);
            currentAirportRoute = null;
        }}
    }}
    </script>
    
    <!-- Include Leaflet Polyline Decorator for arrows -->
    <script src="https://cdn.jsdelivr.net/npm/leaflet-polylinedecorator@1.6.0/dist/leaflet.polylineDecorator.min.js"></script>
    """
    
    # Add legend
    legend_html = f"""
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; 
                background: white; padding: 15px; border-radius: 8px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.2); font-family: Arial, sans-serif;">
        <h4 style="margin: 0 0 10px 0; border-bottom: 1px solid #ddd; padding-bottom: 5px;">
            {city} - Interactive Routes
        </h4>
        <div style="font-size: 12px;">
            <div style="margin: 5px 0;">
                <span style="display: inline-block; width: 12px; height: 12px; 
                             background: #1a7f37; border-radius: 50%; margin-right: 8px;"></span>
                Savings > 100 min
            </div>
            <div style="margin: 5px 0;">
                <span style="display: inline-block; width: 12px; height: 12px; 
                             background: #2ea043; border-radius: 50%; margin-right: 8px;"></span>
                Savings 50-100 min
            </div>
            <div style="margin: 5px 0;">
                <span style="display: inline-block; width: 12px; height: 12px; 
                             background: #f0883e; border-radius: 50%; margin-right: 8px;"></span>
                Savings 0-50 min
            </div>
            <div style="margin: 5px 0;">
                <span style="display: inline-block; width: 12px; height: 12px; 
                             background: #cf222e; border-radius: 50%; margin-right: 8px;"></span>
                No savings
            </div>
            <hr style="margin: 10px 0;">
            <div style="margin: 5px 0;">
                <span style="display: inline-block; width: 20px; height: 3px; 
                             background: #2196F3; margin-right: 8px; border-style: dashed;"></span>
                Route to Helipad
            </div>
            <div style="margin: 5px 0;">
                <span style="display: inline-block; width: 20px; height: 3px; 
                             background: #f44336; margin-right: 8px; border-style: dashed;"></span>
                Route to Airport
            </div>
            <hr style="margin: 10px 0;">
            <div style="font-size: 11px; color: #666;">
                <b>Multipliers ({city}):</b><br>
                Normal: {mults['normal']}x | Rush: {mults['rush']}x<br>
                <span style="color: #cf222e;"><b>Worst: {mults['worst']}x</b></span>
            </div>
            <hr style="margin: 10px 0;">
            <div style="font-size: 11px; color: #888;">
                🖱️ Hover over ZIP code to see routes
            </div>
        </div>
    </div>
    """
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Get the HTML and inject our custom code
    html = m._repr_html_()
    
    # Inject custom JS and legend before closing body tag
    html = html.replace('</body>', hover_js + legend_html + '</body>')
    
    # Save the map
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"[OK] Created: {output_path}")
    return len(routes_data)


def main():
    print("="*60)
    print("CREATING INTERACTIVE MAPS WITH HOVER ROUTES")
    print("="*60)
    
    # Load data
    df = pd.read_csv('analysis_v4_pessimistic.csv')
    
    # Create output directories
    os.makedirs('analysis_v4_pessimistic', exist_ok=True)
    
    # Split by city
    ny_df = df[df['city'] == 'NY'].copy()
    la_df = df[df['city'] == 'LA'].copy()
    
    print(f"\nNY ZIP codes: {len(ny_df)}")
    print(f"LA ZIP codes: {len(la_df)}")
    
    # Create maps
    print("\n" + "-"*40)
    print("Creating NY map...")
    print("-"*40)
    ny_count = create_hover_map('NY', ny_df, 'analysis_v4_pessimistic/map_ny_hover_routes.html')
    
    print("\n" + "-"*40)
    print("Creating LA map...")
    print("-"*40)
    la_count = create_hover_map('LA', la_df, 'analysis_v4_pessimistic/map_la_hover_routes.html')
    
    # Also create copies in root for easy access
    import shutil
    shutil.copy('analysis_v4_pessimistic/map_ny_hover_routes.html', 'map_ny_hover_routes.html')
    shutil.copy('analysis_v4_pessimistic/map_la_hover_routes.html', 'map_la_hover_routes.html')
    
    print("\n" + "="*60)
    print("MAPS CREATED SUCCESSFULLY!")
    print("="*60)
    print(f"""
Output files:
  - map_ny_hover_routes.html ({ny_count} ZIP codes)
  - map_la_hover_routes.html ({la_count} ZIP codes)
  - analysis_v4_pessimistic/map_ny_hover_routes.html
  - analysis_v4_pessimistic/map_la_hover_routes.html

Features:
  [OK] Routes appear on hover over ZIP codes
  [OK] Blue dashed line: Route to nearest helipad
  [OK] Red dashed line: Route to main airport
  [OK] City-specific traffic multipliers
  [OK] Detailed popup with all travel times
""")


if __name__ == '__main__':
    main()

