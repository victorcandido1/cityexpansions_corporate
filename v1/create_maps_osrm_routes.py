#!/usr/bin/env python3
"""
Create interactive maps with OSRM routes displayed on hover
Routes are pre-fetched and stored in the HTML for immediate display
"""

import pandas as pd
import folium
from folium.plugins import FloatImage
import json
import requests
import os

# City-specific traffic multipliers
CITY_MULTIPLIERS = {
    'NY': {'fast': 1.0, 'normal': 1.35, 'rush': 1.69, 'worst': 5.20},
    'LA': {'fast': 1.0, 'normal': 1.42, 'rush': 1.77, 'worst': 4.15}
}

AIRPORTS = {
    'NY': {'coords': [40.6413, -73.7781], 'name': 'JFK International Airport'},
    'LA': {'coords': [33.9425, -118.4081], 'name': 'LAX International Airport'}
}

OSRM_SERVERS = {
    'NY': 'http://localhost:5000',
    'LA': 'http://localhost:5001'
}

def get_osrm_route(origin, destination, city):
    """Get route geometry from OSRM"""
    try:
        server = OSRM_SERVERS[city]
        url = f"{server}/route/v1/driving/{origin[1]},{origin[0]};{destination[1]},{destination[0]}?overview=full&geometries=geojson"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['code'] == 'Ok' and data['routes']:
                coords = data['routes'][0]['geometry']['coordinates']
                # Convert [lon, lat] to [lat, lon] for Leaflet
                return [[c[1], c[0]] for c in coords]
    except Exception as e:
        print(f"    OSRM error: {e}")
    
    # Fallback: straight line
    return [[origin[0], origin[1]], [destination[0], destination[1]]]

def create_map_with_routes(city, df, output_path):
    """Create map with pre-loaded OSRM routes"""
    
    airport = AIRPORTS[city]
    mults = CITY_MULTIPLIERS[city]
    
    # Calculate center
    center_lat = df['origin_lat'].mean()
    center_lon = df['origin_lon'].mean()
    
    print(f"\nCreating {city} map...")
    print(f"  ZIP codes: {len(df)}")
    print(f"  Center: {center_lat:.4f}, {center_lon:.4f}")
    
    # Fetch all routes first
    routes_data = []
    
    for idx, row in df.iterrows():
        zipcode = str(row['zipcode'])
        origin = [row['origin_lat'], row['origin_lon']]
        heli_dest = [row['facility_lat'], row['facility_lon']]
        is_manhattan = row.get('is_manhattan', False)
        
        print(f"  [{idx+1}/{len(df)}] Fetching routes for ZIP {zipcode}...")
        
        # Get routes
        route_to_heli = get_osrm_route(origin, heli_dest, city)
        route_to_airport = get_osrm_route(origin, airport['coords'], city)
        
        # Get savings for color
        savings = row.get('worst_savings_min', 0)
        if savings > 100:
            color = '#1a7f37'
        elif savings > 50:
            color = '#2ea043'
        elif savings > 0:
            color = '#f0883e'
        else:
            color = '#cf222e'
        
        routes_data.append({
            'zipcode': zipcode,
            'origin': origin,
            'heli_route': route_to_heli,
            'airport_route': route_to_airport,
            'color': color,
            'savings': float(savings),
            'is_manhattan': bool(is_manhattan),
            'facility_name': row['facility_name'],
            'facility_code': row['facility_code'],
            'fast_heli': float(row.get('fast_heli_total_min', 0)),
            'rush_heli': float(row.get('rush_heli_total_min', 0)),
            'worst_heli': float(row.get('worst_heli_total_min', 0)),
            'fast_car': float(row.get('fast_car_direct_min', 0)),
            'rush_car': float(row.get('rush_car_direct_min', 0)),
            'worst_car': float(row.get('worst_car_direct_min', 0)),
            'heli_dist': float(row.get('facility_km', 0)),
            'flight_time': float(row.get('flight_time_min', 0))
        })
    
    print(f"\n  Creating HTML map...")
    
    # Create the complete HTML with embedded data and custom JavaScript
    html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>REVO - {city} OSRM Routes Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {{ margin: 0; padding: 0; }}
        #map {{ width: 100%; height: 100vh; }}
        
        .legend {{
            position: fixed;
            bottom: 30px;
            left: 20px;
            z-index: 1000;
            background: white;
            padding: 15px 20px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            font-family: Arial, sans-serif;
            font-size: 13px;
            max-width: 280px;
        }}
        
        .legend h4 {{
            margin: 0 0 12px 0;
            padding-bottom: 8px;
            border-bottom: 2px solid #e94560;
            font-size: 15px;
            color: #1a1a2e;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            margin: 6px 0;
        }}
        
        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 50%;
            margin-right: 10px;
            flex-shrink: 0;
        }}
        
        .legend-line {{
            width: 30px;
            height: 4px;
            margin-right: 10px;
            border-radius: 2px;
        }}
        
        .legend hr {{
            margin: 10px 0;
            border: none;
            border-top: 1px solid #ddd;
        }}
        
        .legend-note {{
            font-size: 11px;
            color: #666;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #eee;
        }}
        
        .info-panel {{
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            background: white;
            padding: 15px 20px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            font-family: Arial, sans-serif;
            max-width: 350px;
            display: none;
        }}
        
        .info-panel h3 {{
            margin: 0 0 10px 0;
            color: #1a1a2e;
            border-bottom: 2px solid;
            padding-bottom: 5px;
        }}
        
        .info-row {{
            display: flex;
            justify-content: space-between;
            padding: 4px 0;
            border-bottom: 1px solid #f0f0f0;
        }}
        
        .info-row:last-child {{
            border-bottom: none;
        }}
        
        .info-label {{
            color: #666;
        }}
        
        .info-value {{
            font-weight: 600;
        }}
        
        .savings-badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            color: white;
            font-weight: bold;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    
    <div class="legend">
        <h4>{"New York" if city == "NY" else "Los Angeles"} - Routes</h4>
        
        <div style="font-weight: 600; margin-bottom: 8px;">ZIP Code Savings (Worst Case)</div>
        <div class="legend-item">
            <div class="legend-color" style="background: #1a7f37;"></div>
            <span>Savings > 100 min</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #2ea043;"></div>
            <span>Savings 50-100 min</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #f0883e;"></div>
            <span>Savings 0-50 min</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #cf222e;"></div>
            <span>No savings</span>
        </div>
        
        <hr>
        
        <div style="font-weight: 600; margin-bottom: 8px;">Routes (on hover)</div>
        <div class="legend-item">
            <div class="legend-line" style="background: #2196F3;"></div>
            <span>Route to Helipad</span>
        </div>
        <div class="legend-item">
            <div class="legend-line" style="background: #f44336;"></div>
            <span>Route to Airport</span>
        </div>
        
        <hr>
        
        <div style="font-weight: 600; margin-bottom: 8px;">Traffic Multipliers ({city})</div>
        <div style="font-size: 12px;">
            Fast: 1.00x | Normal: {mults['normal']}x<br>
            Rush: {mults['rush']}x | <span style="color: #e74c3c; font-weight: bold;">Worst: {mults['worst']}x</span>
        </div>
        
        <div class="legend-note">
            <strong>Tip:</strong> Hover over ZIP codes to see OSRM routes
        </div>
    </div>
    
    <div class="info-panel" id="infoPanel">
        <h3 id="infoTitle">ZIP Code</h3>
        <div id="infoContent"></div>
    </div>
    
    <script>
        // Routes data
        var routesData = {json.dumps(routes_data)};
        
        // Airport location
        var airportCoords = {json.dumps(airport['coords'])};
        var airportName = "{airport['name']}";
        
        // Initialize map
        var map = L.map('map').setView([{center_lat}, {center_lon}], 10);
        
        // Add tile layer
        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            maxZoom: 19
        }}).addTo(map);
        
        // Add airport marker
        var airportIcon = L.divIcon({{
            className: 'custom-div-icon',
            html: '<div style="background: #e74c3c; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 14px; box-shadow: 0 2px 10px rgba(0,0,0,0.3);">✈</div>',
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        }});
        
        L.marker(airportCoords, {{icon: airportIcon}})
            .addTo(map)
            .bindPopup('<b>' + airportName + '</b>');
        
        // Track unique heliports
        var heliports = {{}};
        routesData.forEach(function(r) {{
            var key = r.facility_code;
            if (!heliports[key]) {{
                heliports[key] = {{
                    name: r.facility_name,
                    code: r.facility_code,
                    lat: r.heli_route[r.heli_route.length - 1][0],
                    lon: r.heli_route[r.heli_route.length - 1][1]
                }};
            }}
        }});
        
        // Add heliport markers
        Object.values(heliports).forEach(function(h) {{
            var heliIcon = L.divIcon({{
                className: 'custom-div-icon',
                html: '<div style="background: #f39c12; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">H</div>',
                iconSize: [24, 24],
                iconAnchor: [12, 12]
            }});
            
            L.marker([h.lat, h.lon], {{icon: heliIcon}})
                .addTo(map)
                .bindPopup('<b>' + h.name + '</b><br>Code: ' + h.code);
        }});
        
        // Current route lines
        var currentHeliRoute = null;
        var currentAirportRoute = null;
        
        // Add ZIP code markers and routes
        routesData.forEach(function(data) {{
            // Create ZIP code marker
            var marker = L.circleMarker(data.origin, {{
                radius: 10,
                fillColor: data.color,
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8
            }}).addTo(map);
            
            // Store route data on marker
            marker.routeData = data;
            
            // Mouse events
            marker.on('mouseover', function(e) {{
                var d = this.routeData;
                
                // Clear existing routes
                if (currentHeliRoute) {{
                    map.removeLayer(currentHeliRoute);
                }}
                if (currentAirportRoute) {{
                    map.removeLayer(currentAirportRoute);
                }}
                
                // Draw route to helipad (blue)
                currentHeliRoute = L.polyline(d.heli_route, {{
                    color: '#2196F3',
                    weight: 5,
                    opacity: 0.9,
                    dashArray: '10, 5'
                }}).addTo(map);
                
                // Draw route to airport (red)
                currentAirportRoute = L.polyline(d.airport_route, {{
                    color: '#f44336',
                    weight: 5,
                    opacity: 0.9,
                    dashArray: '10, 5'
                }}).addTo(map);
                
                // Show info panel
                var panel = document.getElementById('infoPanel');
                var title = document.getElementById('infoTitle');
                var content = document.getElementById('infoContent');
                
                title.innerHTML = 'ZIP ' + d.zipcode + (d.is_manhattan ? ' <span style="color: #3498db;">(Manhattan)</span>' : '');
                title.style.borderColor = d.color;
                
                content.innerHTML = `
                    <div class="info-row">
                        <span class="info-label">Helipad:</span>
                        <span class="info-value">${{d.facility_name}}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Distance:</span>
                        <span class="info-value">${{d.heli_dist.toFixed(1)}} km</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Flight Time:</span>
                        <span class="info-value">${{d.flight_time.toFixed(0)}} min</span>
                    </div>
                    <hr style="margin: 10px 0; border: none; border-top: 1px solid #eee;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 5px; text-align: center; font-size: 12px;">
                        <div style="background: #f8f9fa; padding: 5px; border-radius: 5px;">
                            <div style="color: #666;">Fast</div>
                            <div>Car: ${{d.fast_car.toFixed(0)}}m</div>
                            <div>Heli: ${{d.fast_heli.toFixed(0)}}m</div>
                        </div>
                        <div style="background: #f8f9fa; padding: 5px; border-radius: 5px;">
                            <div style="color: #666;">Rush</div>
                            <div>Car: ${{d.rush_car.toFixed(0)}}m</div>
                            <div>Heli: ${{d.rush_heli.toFixed(0)}}m</div>
                        </div>
                        <div style="background: #ffe0e0; padding: 5px; border-radius: 5px;">
                            <div style="color: #e74c3c; font-weight: bold;">Worst</div>
                            <div>Car: ${{d.worst_car.toFixed(0)}}m</div>
                            <div>Heli: ${{d.worst_heli.toFixed(0)}}m</div>
                        </div>
                    </div>
                    <div class="savings-badge" style="background: ${{d.color}}; display: block; text-align: center;">
                        Savings: ${{d.savings.toFixed(0)}} min
                    </div>
                `;
                
                panel.style.display = 'block';
                
                // Highlight marker
                this.setStyle({{
                    weight: 4,
                    fillOpacity: 1
                }});
            }});
            
            marker.on('mouseout', function(e) {{
                // Don't remove routes - keep them visible
                // Just reset marker style
                this.setStyle({{
                    weight: 2,
                    fillOpacity: 0.8
                }});
            }});
            
            marker.on('click', function(e) {{
                // Keep routes visible on click
            }});
        }});
        
        // Click on map to hide routes and info panel
        map.on('click', function(e) {{
            if (currentHeliRoute) {{
                map.removeLayer(currentHeliRoute);
                currentHeliRoute = null;
            }}
            if (currentAirportRoute) {{
                map.removeLayer(currentAirportRoute);
                currentAirportRoute = null;
            }}
            document.getElementById('infoPanel').style.display = 'none';
        }});
    </script>
</body>
</html>'''
    
    # Save the HTML
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"  [OK] Saved: {output_path}")
    return len(routes_data)


def main():
    print("="*60)
    print("CREATING MAPS WITH OSRM ROUTES")
    print("="*60)
    
    # Load data
    df = pd.read_csv('analysis_v4_pessimistic.csv')
    print(f"\nLoaded {len(df)} records")
    
    # Create output directory
    os.makedirs('analysis_v4_pessimistic', exist_ok=True)
    
    # Split by city
    ny_df = df[df['city'] == 'NY'].copy()
    la_df = df[df['city'] == 'LA'].copy()
    
    print(f"\nNY: {len(ny_df)} ZIP codes")
    print(f"LA: {len(la_df)} ZIP codes")
    
    # Create maps
    ny_count = create_map_with_routes('NY', ny_df, 'analysis_v4_pessimistic/map_ny_osrm.html')
    la_count = create_map_with_routes('LA', la_df, 'analysis_v4_pessimistic/map_la_osrm.html')
    
    # Copy to root
    import shutil
    shutil.copy('analysis_v4_pessimistic/map_ny_osrm.html', 'map_ny_osrm.html')
    shutil.copy('analysis_v4_pessimistic/map_la_osrm.html', 'map_la_osrm.html')
    
    print("\n" + "="*60)
    print("MAPS CREATED SUCCESSFULLY!")
    print("="*60)
    print(f"""
Output files:
  - map_ny_osrm.html ({ny_count} ZIP codes with OSRM routes)
  - map_la_osrm.html ({la_count} ZIP codes with OSRM routes)

Features:
  [OK] Real OSRM routes pre-fetched
  [OK] Blue dashed line: Route to helipad
  [OK] Red dashed line: Route to airport  
  [OK] Info panel with travel times
  [OK] City-specific multipliers displayed
""")


if __name__ == '__main__':
    main()

