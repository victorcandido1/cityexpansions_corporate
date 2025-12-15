"""
Cria mapa interativo V4 com:
- Cenário PESSIMISTA
- Velocidade por 100m
- Helipontos de Manhattan verificados
"""

import pandas as pd
import folium
from folium import plugins
import json
from pathlib import Path

# Carregar dados
df = pd.read_csv('analysis_v4_pessimistic.csv')
segments_df = pd.read_csv('route_segments_100m.csv')

AIRPORTS = {
    'NY': {'coords': (40.6413, -73.7781), 'name': 'JFK International'},
    'LA': {'coords': (33.9425, -118.4081), 'name': 'LAX International'}
}

def create_map(city: str, city_df: pd.DataFrame, city_segments: pd.DataFrame):
    """Cria mapa para uma cidade"""
    airport = AIRPORTS[city]
    center = [airport['coords'][0], airport['coords'][1]]
    
    m = folium.Map(location=center, zoom_start=10, tiles='CartoDB positron')
    
    # Grupos de camadas
    zip_group = folium.FeatureGroup(name='ZIP Codes')
    heli_group = folium.FeatureGroup(name='Helipontos')
    route_group = folium.FeatureGroup(name='Rotas de Carro')
    flight_group = folium.FeatureGroup(name='Rotas de Voo')
    
    # Aeroporto
    folium.Marker(
        location=airport['coords'],
        popup=f"<b>{airport['name']}</b>",
        icon=folium.Icon(color='red', icon='plane', prefix='fa')
    ).add_to(m)
    
    # Helipontos únicos
    heliports = city_df[['facility_code', 'facility_name', 'facility_lat', 'facility_lon']].drop_duplicates()
    for _, h in heliports.iterrows():
        folium.Marker(
            location=[h['facility_lat'], h['facility_lon']],
            popup=f"<b>{h['facility_name']}</b><br>Código: {h['facility_code']}",
            icon=folium.Icon(color='orange', icon='helicopter', prefix='fa')
        ).add_to(heli_group)
    
    # ZIP codes e rotas
    for _, row in city_df.iterrows():
        zipcode = str(row['zipcode'])
        is_manhattan = row.get('is_manhattan', False)
        
        # Cor baseada na economia
        savings = row.get('worst_savings_min', 0)
        if savings > 100:
            color = 'darkgreen'
        elif savings > 50:
            color = 'green'
        elif savings > 0:
            color = 'orange'
        else:
            color = 'red'
        
        # Popup detalhado
        popup_html = f"""
        <div style="width:350px; font-family: Arial, sans-serif;">
            <h4 style="margin:0; color: #333;">ZIP {zipcode} {'🏙️ MANHATTAN' if is_manhattan else ''}</h4>
            <hr style="margin:5px 0;">
            
            <h5 style="margin:5px 0;">📍 Heliponto Mais Próximo</h5>
            <table style="font-size:12px; width:100%;">
                <tr><td><b>Nome:</b></td><td>{row['facility_name']} ({row['facility_code']})</td></tr>
                <tr><td><b>Distância:</b></td><td>{row['facility_km']:.1f} km</td></tr>
            </table>
            
            <h5 style="margin:10px 0 5px 0;">⏱️ Tempos (PIOR CENÁRIO - 4.68x tráfego)</h5>
            <table style="font-size:12px; width:100%; border-collapse:collapse;">
                <tr style="background:#f0f0f0;">
                    <td><b>Modo</b></td>
                    <td><b>Fast</b></td>
                    <td><b>Rush</b></td>
                    <td><b>WORST</b></td>
                </tr>
                <tr>
                    <td>🚁 Helicóptero</td>
                    <td>{row.get('fast_heli_total_min', 'N/A'):.0f} min</td>
                    <td>{row.get('rush_heli_total_min', 'N/A'):.0f} min</td>
                    <td><b>{row.get('worst_heli_total_min', 'N/A'):.0f} min</b></td>
                </tr>
                <tr>
                    <td>🚗 Carro Direto</td>
                    <td>{row.get('fast_car_direct_min', 'N/A'):.0f} min</td>
                    <td>{row.get('rush_car_direct_min', 'N/A'):.0f} min</td>
                    <td><b>{row.get('worst_car_direct_min', 'N/A'):.0f} min</b></td>
                </tr>
            </table>
            
            <h5 style="margin:10px 0 5px 0; color: {'green' if savings > 0 else 'red'};">
                💰 Economia (WORST): {savings:.0f} min ({savings/60:.1f}h)
            </h5>
            
            <h5 style="margin:10px 0 5px 0;">🚙 Velocidade Média (WORST)</h5>
            <table style="font-size:12px; width:100%;">
                <tr><td>Para Aeroporto:</td><td><b>{row.get('speed_to_airport_worst_kmh', 'N/A'):.1f} km/h</b></td></tr>
                <tr><td>Para Heliponto:</td><td><b>{row.get('speed_to_facility_worst_kmh', 'N/A'):.1f} km/h</b></td></tr>
                <tr><td>Tempo/100m (worst):</td><td><b>{100/(row.get('speed_to_airport_worst_kmh', 30)*1000/3600):.1f} seg</b></td></tr>
            </table>
        </div>
        """
        
        # Marker
        folium.CircleMarker(
            location=[row['origin_lat'], row['origin_lon']],
            radius=8,
            popup=folium.Popup(popup_html, max_width=400),
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7
        ).add_to(zip_group)
        
        # Linhas de rota (simplificadas)
        # ZIP -> Heliponto
        folium.PolyLine(
            [[row['origin_lat'], row['origin_lon']], 
             [row['facility_lat'], row['facility_lon']]],
            color='blue',
            weight=2,
            opacity=0.5,
            dash_array='5,5'
        ).add_to(route_group)
        
        # Heliponto -> Aeroporto (voo)
        folium.PolyLine(
            [[row['facility_lat'], row['facility_lon']], 
             list(airport['coords'])],
            color='green',
            weight=2,
            opacity=0.7,
            dash_array='10,5'
        ).add_to(flight_group)
    
    # Adicionar grupos ao mapa
    zip_group.add_to(m)
    heli_group.add_to(m)
    route_group.add_to(m)
    flight_group.add_to(m)
    
    # Controle de camadas
    folium.LayerControl().add_to(m)
    
    # Legenda
    legend_html = '''
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background: white; 
                padding: 10px; border-radius: 5px; border: 2px solid grey; font-family: Arial;">
        <h4 style="margin:0 0 5px 0;">Legenda</h4>
        <p style="margin:2px;"><span style="color:darkgreen;">●</span> Economia > 100 min</p>
        <p style="margin:2px;"><span style="color:green;">●</span> Economia 50-100 min</p>
        <p style="margin:2px;"><span style="color:orange;">●</span> Economia 0-50 min</p>
        <p style="margin:2px;"><span style="color:red;">●</span> Sem vantagem</p>
        <hr style="margin:5px 0;">
        <p style="margin:2px; font-size:11px;">CENÁRIO: <b>PESSIMISTA (4.68x)</b></p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

# Criar mapas
for city in ['NY', 'LA']:
    city_df = df[df['city'] == city]
    city_segments = segments_df[segments_df['city'] == city]
    
    print(f"Criando mapa para {city}...")
    m = create_map(city, city_df, city_segments)
    
    filename = f'map_v4_{city.lower()}_pessimistic.html'
    m.save(filename)
    print(f"  -> {filename}")

print("\nMapas criados com sucesso!")

