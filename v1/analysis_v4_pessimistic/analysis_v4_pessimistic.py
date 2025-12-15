"""
Análise V4 - PESSIMISTIC (Pior Cenário)
- Usa dados PESSIMISTAS do Google Traffic
- ZIP codes de Manhattan usam APENAS helipontos de Manhattan
- Calcula velocidade por segmento de 100m
- Usa servidores OSRM locais
"""

import pandas as pd
import numpy as np
import requests
import math
import folium
from folium import plugins
from pathlib import Path
import sys
import io
import warnings
import json
from typing import Dict, List, Tuple, Optional

warnings.filterwarnings('ignore')

if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except:
        pass

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

OSRM_SERVERS = {
    'NY': 'http://localhost:5000/route/v1/driving',
    'LA': 'http://localhost:5001/route/v1/driving'
}

AIRPORTS = {
    'NY': {'coords': (40.6413, -73.7781), 'name': 'JFK International', 'code': 'JFK'},
    'LA': {'coords': (33.9425, -118.4081), 'name': 'LAX International', 'code': 'LAX'}
}

# Manhattan bounding box (mais preciso - exclui NJ)
MANHATTAN_BOUNDS = {
    'lat_min': 40.70,
    'lat_max': 40.88,
    'lon_min': -74.02,
    'lon_max': -73.90
}

# Helipontos APROVADOS em Manhattan (verificados manualmente)
MANHATTAN_HELIPORTS_APPROVED = [
    'JRB',   # Downtown Manhattan/Wall St Heliport
    '6N5',   # East 34th Street Heliport
    'JRA',   # West 30th St Heliport
    '3NY2',  # Astoria (Queens, próximo)
]

# Helipontos de polícia PROIBIDOS
POLICE_KEYWORDS = ['POLICE', 'SHERIFF', 'STATE PATROL', 'HIGHWAY PATROL']

# Multiplicadores de tráfego baseados nos dados do Google
# Derivados da análise dos dados históricos PESSIMISTAS
TRAFFIC_MULTIPLIERS = {
    'fast': 1.0,        # Sem tráfego (baseline OSRM)
    'normal': 1.25,     # Tráfego normal
    'rush': 2.0,        # Rush hour PESSIMISTA (baseado em duration_pessimistic_min)
    'worst': 2.5        # Pior cenário possível
}

# Constantes helicóptero
CHECK_IN_MIN = 10
TRANSFER_MIN = 10
HELI_SPEED_KMH = 200

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def is_police_heliport(name: str) -> bool:
    """Verifica se é heliponto de polícia"""
    if not name:
        return False
    name_upper = str(name).upper()
    for keyword in POLICE_KEYWORDS:
        if keyword in name_upper:
            return True
    return False

def is_manhattan_location(lat: float, lon: float) -> bool:
    """Verifica se coordenadas estão em Manhattan"""
    return (MANHATTAN_BOUNDS['lat_min'] <= lat <= MANHATTAN_BOUNDS['lat_max'] and
            MANHATTAN_BOUNDS['lon_min'] <= lon <= MANHATTAN_BOUNDS['lon_max'])

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula distância em km entre dois pontos"""
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def get_osrm_route_with_steps(origin_lat: float, origin_lon: float, 
                               dest_lat: float, dest_lon: float, city: str) -> Optional[Dict]:
    """
    Obtém rota detalhada do OSRM com geometria completa e passos
    """
    url = f"{OSRM_SERVERS[city]}/{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
    params = {
        'overview': 'full',
        'geometries': 'geojson',
        'steps': 'true',
        'annotations': 'true'
    }
    
    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        if data.get('code') == 'Ok' and data.get('routes'):
            route = data['routes'][0]
            return {
                'distance_km': route['distance'] / 1000,
                'duration_min': route['duration'] / 60,
                'geometry': route['geometry'],
                'legs': route.get('legs', [])
            }
    except Exception as e:
        print(f"  [WARN] OSRM error: {e}")
    return None

def segment_route(geometry: Dict, total_distance_km: float, 
                  total_duration_min: float, segment_length_m: float = 100) -> List[Dict]:
    """
    Divide a rota em segmentos de 100m e calcula velocidade média para cada
    """
    if not geometry or 'coordinates' not in geometry:
        return []
    
    coords = geometry['coordinates']
    if len(coords) < 2:
        return []
    
    segments = []
    cumulative_distance_m = 0
    segment_id = 0
    
    # Velocidade média geral (km/h)
    avg_speed_kmh = (total_distance_km / (total_duration_min / 60)) if total_duration_min > 0 else 30
    
    for i in range(1, len(coords)):
        lon1, lat1 = coords[i-1]
        lon2, lat2 = coords[i]
        
        seg_dist_km = haversine_distance(lat1, lon1, lat2, lon2)
        seg_dist_m = seg_dist_km * 1000
        
        cumulative_distance_m += seg_dist_m
        
        # Criar segmento a cada 100m
        while cumulative_distance_m >= segment_length_m:
            segment_id += 1
            cumulative_distance_m -= segment_length_m
            
            # Tempo para percorrer 100m (em segundos)
            time_100m_normal_sec = (0.1 / avg_speed_kmh) * 3600
            time_100m_rush_sec = (0.1 / (avg_speed_kmh / TRAFFIC_MULTIPLIERS['rush'])) * 3600
            time_100m_worst_sec = (0.1 / (avg_speed_kmh / TRAFFIC_MULTIPLIERS['worst'])) * 3600
            
            # Velocidade em diferentes cenários
            speed_normal_kmh = avg_speed_kmh
            speed_rush_kmh = avg_speed_kmh / TRAFFIC_MULTIPLIERS['rush']
            speed_worst_kmh = avg_speed_kmh / TRAFFIC_MULTIPLIERS['worst']
            
            segments.append({
                'segment_id': segment_id,
                'lat': lat2,
                'lon': lon2,
                'distance_from_start_m': segment_id * segment_length_m,
                'time_100m_normal_sec': round(time_100m_normal_sec, 2),
                'time_100m_rush_sec': round(time_100m_rush_sec, 2),
                'time_100m_worst_sec': round(time_100m_worst_sec, 2),
                'speed_normal_kmh': round(speed_normal_kmh, 1),
                'speed_rush_kmh': round(speed_rush_kmh, 1),
                'speed_worst_kmh': round(speed_worst_kmh, 1)
            })
    
    return segments

# ============================================================================
# CARREGAMENTO DE DADOS
# ============================================================================

def load_google_traffic_data() -> pd.DataFrame:
    """
    Carrega dados de tráfego do Google e extrai multiplicadores PESSIMISTAS
    """
    traffic_dir = Path('../traffic_data/New_York')
    la_dir = Path('../traffic_data/Los_Angeles')
    
    all_data = []
    
    for csv_file in list(traffic_dir.glob('*.csv')) + list(la_dir.glob('*.csv')):
        try:
            df = pd.read_csv(csv_file)
            if 'duration_pessimistic_min' in df.columns and 'duration_normal_min' in df.columns:
                all_data.append(df)
        except:
            pass
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()

def analyze_google_multipliers(df: pd.DataFrame) -> Dict:
    """
    Analisa os dados do Google para extrair multiplicadores PESSIMISTAS reais
    """
    if df.empty:
        return {'rush': 2.0, 'worst': 2.5}
    
    # Calcular multiplicador pessimista vs normal
    df['multiplier'] = df['duration_pessimistic_min'] / df['duration_normal_min']
    
    # Agrupar por hora
    hourly = df.groupby('hour')['multiplier'].agg(['mean', 'max']).reset_index()
    
    # Rush hours (7-9 AM e 5-8 PM)
    rush_hours = [7, 8, 9, 17, 18, 19, 20]
    rush_multipliers = hourly[hourly['hour'].isin(rush_hours)]
    
    avg_rush = rush_multipliers['mean'].mean() if not rush_multipliers.empty else 1.6
    max_rush = rush_multipliers['max'].max() if not rush_multipliers.empty else 2.3
    
    return {
        'rush': round(avg_rush, 2),
        'worst': round(max_rush, 2)
    }

def load_cluster_data() -> pd.DataFrame:
    """Carrega dados do cluster"""
    df = pd.read_csv('../10percent/cluster_results_by_city.csv', dtype={'zipcode': str})
    return df

def load_faa_data() -> pd.DataFrame:
    """Carrega coordenadas de helipontos e aeroportos da FAA"""
    faa_df = pd.read_excel('../all-airport-data.xlsx', usecols=[
        'Facility Type', 'Loc Id', 'Name', 'City', 'State Name',
        'ARP Latitude DD', 'ARP Longitude DD'
    ])
    faa_df.columns = ['facility_type', 'code', 'name', 'city_name', 'state', 'lat', 'lon']
    faa_df = faa_df.dropna(subset=['lat', 'lon'])
    return faa_df

def load_top10_data() -> pd.DataFrame:
    """Carrega dados dos ZIP codes top 10%"""
    df = pd.read_csv('../10percent/top10_richest_data.csv', dtype={'zipcode': str})
    return df

# ============================================================================
# SELEÇÃO DE HELIPONTOS
# ============================================================================

def get_manhattan_heliports(faa_df: pd.DataFrame) -> pd.DataFrame:
    """
    Retorna apenas helipontos localizados em Manhattan
    """
    manhattan_heliports = faa_df[
        (faa_df['facility_type'].str.contains('HELIPORT|HELISTOP', case=False, na=False)) &
        (faa_df['lat'].apply(lambda x: MANHATTAN_BOUNDS['lat_min'] <= x <= MANHATTAN_BOUNDS['lat_max'])) &
        (faa_df['lon'].apply(lambda x: MANHATTAN_BOUNDS['lon_min'] <= x <= MANHATTAN_BOUNDS['lon_max'])) &
        (~faa_df['name'].apply(is_police_heliport))
    ].copy()
    
    return manhattan_heliports

def find_best_heliport_for_zip(origin_lat: float, origin_lon: float, 
                                 faa_df: pd.DataFrame, city: str,
                                 is_manhattan_zip: bool = False) -> Optional[Dict]:
    """
    Encontra o melhor heliponto para um ZIP code
    Se for Manhattan, usa APENAS helipontos APROVADOS de Manhattan
    """
    if is_manhattan_zip:
        # Usar APENAS helipontos aprovados de Manhattan (lista manual verificada)
        candidates = faa_df[
            (faa_df['code'].isin(MANHATTAN_HELIPORTS_APPROVED))
        ].copy()
    else:
        # Para outros locais, usar qualquer heliponto/aeroporto não-policial
        candidates = faa_df[
            (faa_df['facility_type'].str.contains('HELIPORT|HELISTOP|AIRPORT', case=False, na=False)) &
            (~faa_df['name'].apply(is_police_heliport))
        ].copy()
    
    if candidates.empty:
        return None
    
    # Calcular distância para cada candidato
    candidates['distance_km'] = candidates.apply(
        lambda row: haversine_distance(origin_lat, origin_lon, row['lat'], row['lon']),
        axis=1
    )
    
    # Ordenar por distância
    candidates = candidates.sort_values('distance_km')
    
    # Retornar o mais próximo
    best = candidates.iloc[0]
    return {
        'code': best['code'],
        'name': best['name'],
        'lat': float(best['lat']),
        'lon': float(best['lon']),
        'km': float(best['distance_km']),
        'type': 'HELIPORT' if 'HELI' in str(best['facility_type']).upper() else 'AIRPORT'
    }

# ============================================================================
# CÁLCULO DE TEMPOS COM CENÁRIOS PESSIMISTAS
# ============================================================================

def calculate_pessimistic_times(origin_lat: float, origin_lon: float,
                                 facility: Dict, airport_coords: Tuple[float, float],
                                 city: str, traffic_multipliers: Dict) -> Dict:
    """
    Calcula todos os tempos usando cenários PESSIMISTAS
    """
    results = {}
    
    # Distância de voo (não muda com tráfego)
    flight_dist_km = haversine_distance(facility['lat'], facility['lon'], 
                                        airport_coords[0], airport_coords[1])
    flight_time_min = (flight_dist_km / HELI_SPEED_KMH) * 60
    
    results['flight_dist_km'] = flight_dist_km
    results['flight_time_min'] = flight_time_min
    
    # Rota de carro até a instalação (heliponto/aeroporto local)
    car_to_facility = get_osrm_route_with_steps(origin_lat, origin_lon, 
                                                 facility['lat'], facility['lon'], city)
    
    # Rota de carro direto até aeroporto principal
    car_to_airport = get_osrm_route_with_steps(origin_lat, origin_lon,
                                                airport_coords[0], airport_coords[1], city)
    
    # Segmentar rotas
    if car_to_facility:
        results['car_to_facility_base_min'] = car_to_facility['duration_min']
        results['car_to_facility_dist_km'] = car_to_facility['distance_km']
        results['car_to_facility_geometry'] = car_to_facility['geometry']
        results['car_to_facility_segments'] = segment_route(
            car_to_facility['geometry'],
            car_to_facility['distance_km'],
            car_to_facility['duration_min']
        )
    else:
        # Fallback: estimar baseado na distância
        results['car_to_facility_base_min'] = (facility['km'] / 30) * 60  # 30 km/h média
        results['car_to_facility_dist_km'] = facility['km']
        results['car_to_facility_geometry'] = None
        results['car_to_facility_segments'] = []
    
    if car_to_airport:
        results['car_to_airport_base_min'] = car_to_airport['duration_min']
        results['car_to_airport_dist_km'] = car_to_airport['distance_km']
        results['car_to_airport_geometry'] = car_to_airport['geometry']
        results['car_to_airport_segments'] = segment_route(
            car_to_airport['geometry'],
            car_to_airport['distance_km'],
            car_to_airport['duration_min']
        )
    else:
        results['car_to_airport_base_min'] = None
        results['car_to_airport_dist_km'] = None
        results['car_to_airport_geometry'] = None
        results['car_to_airport_segments'] = []
    
    # Calcular velocidades médias
    if results.get('car_to_facility_dist_km') and results['car_to_facility_base_min'] > 0:
        base_speed = (results['car_to_facility_dist_km'] / results['car_to_facility_base_min']) * 60
        results['speed_to_facility_normal_kmh'] = round(base_speed, 1)
        results['speed_to_facility_rush_kmh'] = round(base_speed / traffic_multipliers['rush'], 1)
        results['speed_to_facility_worst_kmh'] = round(base_speed / traffic_multipliers['worst'], 1)
    
    if results.get('car_to_airport_dist_km') and results.get('car_to_airport_base_min') and results['car_to_airport_base_min'] > 0:
        base_speed = (results['car_to_airport_dist_km'] / results['car_to_airport_base_min']) * 60
        results['speed_to_airport_normal_kmh'] = round(base_speed, 1)
        results['speed_to_airport_rush_kmh'] = round(base_speed / traffic_multipliers['rush'], 1)
        results['speed_to_airport_worst_kmh'] = round(base_speed / traffic_multipliers['worst'], 1)
    
    # Calcular para cada cenário de tráfego
    for scenario, multiplier in traffic_multipliers.items():
        # Tempo de carro até instalação (heliponto)
        car_fac = results['car_to_facility_base_min'] * multiplier
        
        # Tempo total helicóptero
        heli_total = car_fac + CHECK_IN_MIN + flight_time_min + TRANSFER_MIN
        
        # Tempo de carro direto
        if results['car_to_airport_base_min']:
            car_direct = results['car_to_airport_base_min'] * multiplier
        else:
            car_direct = None
        
        # Economia
        if car_direct:
            savings = car_direct - heli_total
        else:
            savings = None
        
        results[f'{scenario}_car_to_facility_min'] = round(car_fac, 1)
        results[f'{scenario}_heli_total_min'] = round(heli_total, 1)
        results[f'{scenario}_car_direct_min'] = round(car_direct, 1) if car_direct else None
        results[f'{scenario}_savings_min'] = round(savings, 1) if savings else None
    
    return results

# ============================================================================
# PROCESSAMENTO PRINCIPAL
# ============================================================================

def process_all_zipcodes():
    """Processa todos os ZIP codes com cenários PESSIMISTAS"""
    print("=" * 80)
    print("ANÁLISE V4 - CENÁRIO PESSIMISTA (PIOR CASO)")
    print("=" * 80)
    
    # Carrega dados de tráfego do Google para derivar multiplicadores
    print("\n[1] Analisando dados de tráfego do Google...")
    google_df = load_google_traffic_data()
    
    if not google_df.empty:
        real_multipliers = analyze_google_multipliers(google_df)
        print(f"   Multiplicadores PESSIMISTAS derivados do Google:")
        print(f"   - Rush Hour: {real_multipliers['rush']}x")
        print(f"   - Pior Caso: {real_multipliers['worst']}x")
        TRAFFIC_MULTIPLIERS['rush'] = real_multipliers['rush']
        TRAFFIC_MULTIPLIERS['worst'] = real_multipliers['worst']
    else:
        print("   [WARN] Dados do Google não encontrados, usando multipliers padrão")
    
    # Carrega dados
    print("\n[2] Carregando dados...")
    cluster_df = load_cluster_data()
    faa_df = load_faa_data()
    top10_df = load_top10_data()
    
    # Merge para obter coordenadas dos ZIPs
    merged_df = cluster_df.merge(
        top10_df[['zipcode', 'centroid_lat', 'centroid_lon']].rename(
            columns={'centroid_lat': 'lat', 'centroid_lon': 'lon'}
        ),
        on='zipcode',
        how='left'
    )
    
    # Filtra por NY e LA
    merged_df = merged_df[merged_df['city_key'].isin(['new_york', 'los_angeles'])]
    print(f"   {len(merged_df)} ZIP codes carregados")
    
    # Identifica helipontos de Manhattan
    manhattan_heliports = get_manhattan_heliports(faa_df)
    print(f"   {len(manhattan_heliports)} helipontos em Manhattan disponíveis:")
    for _, h in manhattan_heliports.iterrows():
        print(f"      - {h['name']} ({h['code']})")
    
    results = []
    segments_data = []
    
    print("\n[3] Processando ZIP codes...")
    for idx, row in merged_df.iterrows():
        zipcode = str(row['zipcode'])
        city_key = row['city_key']
        city = 'NY' if city_key == 'new_york' else 'LA'
        
        origin_lat = row.get('lat')
        origin_lon = row.get('lon')
        
        if pd.isna(origin_lat) or pd.isna(origin_lon):
            print(f"   [SKIP] {zipcode} ({city}) - Sem coordenadas")
            continue
        
        # Verificar se é Manhattan
        is_manhattan = city == 'NY' and is_manhattan_location(origin_lat, origin_lon)
        
        if is_manhattan:
            print(f"   [{zipcode}] MANHATTAN - buscando helipontos em Manhattan apenas")
        
        # Encontrar melhor heliponto
        facility = find_best_heliport_for_zip(origin_lat, origin_lon, faa_df, city, is_manhattan)
        
        if not facility:
            print(f"   [SKIP] {zipcode} ({city}) - Sem heliponto disponível")
            continue
        
        # Calcular tempos PESSIMISTAS
        airport_coords = AIRPORTS[city]['coords']
        times = calculate_pessimistic_times(origin_lat, origin_lon, facility, 
                                            airport_coords, city, TRAFFIC_MULTIPLIERS)
        
        # Montar resultado
        result = {
            'zipcode': zipcode,
            'city': city,
            'is_manhattan': is_manhattan,
            'origin_lat': origin_lat,
            'origin_lon': origin_lon,
            'facility_code': facility['code'],
            'facility_name': facility['name'],
            'facility_type': facility['type'],
            'facility_lat': facility['lat'],
            'facility_lon': facility['lon'],
            'facility_km': facility['km'],
            **{k: v for k, v in times.items() if not k.endswith('_geometry') and not k.endswith('_segments')}
        }
        results.append(result)
        
        # Salvar segmentos
        for seg in times.get('car_to_airport_segments', []):
            seg['zipcode'] = zipcode
            seg['city'] = city
            seg['route_type'] = 'to_airport'
            segments_data.append(seg)
        
        for seg in times.get('car_to_facility_segments', []):
            seg['zipcode'] = zipcode
            seg['city'] = city
            seg['route_type'] = 'to_helipad'
            segments_data.append(seg)
        
        # Log
        worst_savings = times.get('worst_savings_min', 0)
        symbol = "+" if worst_savings and worst_savings > 0 else "-"
        print(f"   [{zipcode}] {city}{'*' if is_manhattan else ''} -> {facility['name'][:30]} | "
              f"Worst: Carro {times.get('worst_car_direct_min', 0):.0f}min vs Heli {times.get('worst_heli_total_min', 0):.0f}min | "
              f"Economia: {symbol}{abs(worst_savings) if worst_savings else 0:.0f}min")
    
    # Salvar resultados
    print("\n[4] Salvando resultados...")
    results_df = pd.DataFrame(results)
    results_df.to_csv('analysis_v4_pessimistic.csv', index=False)
    print(f"   -> analysis_v4_pessimistic.csv ({len(results_df)} registros)")
    
    if segments_data:
        segments_df = pd.DataFrame(segments_data)
        segments_df.to_csv('route_segments_100m.csv', index=False)
        print(f"   -> route_segments_100m.csv ({len(segments_df)} segmentos)")
    
    # Estatísticas
    print("\n" + "=" * 80)
    print("ESTATÍSTICAS - CENÁRIO PESSIMISTA (PIOR CASO)")
    print("=" * 80)
    
    for city in ['NY', 'LA']:
        city_df = results_df[results_df['city'] == city]
        if city_df.empty:
            continue
        
        manhattan_count = city_df['is_manhattan'].sum() if 'is_manhattan' in city_df.columns else 0
        
        print(f"\n{city}:")
        print(f"  Total ZIPs: {len(city_df)} (Manhattan: {manhattan_count})")
        print(f"  Tempo Carro (worst): {city_df['worst_car_direct_min'].mean():.0f} min (média)")
        print(f"  Tempo Heli (worst): {city_df['worst_heli_total_min'].mean():.0f} min (média)")
        print(f"  Economia (worst): {city_df['worst_savings_min'].mean():.0f} min (média)")
        print(f"  % com vantagem heli: {100*(city_df['worst_savings_min'] > 0).mean():.0f}%")
        
        if 'speed_to_airport_worst_kmh' in city_df.columns:
            print(f"  Velocidade média (worst): {city_df['speed_to_airport_worst_kmh'].mean():.1f} km/h")

if __name__ == "__main__":
    process_all_zipcodes()

