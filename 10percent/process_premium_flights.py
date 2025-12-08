# -*- coding: utf-8 -*-
"""
PROCESSAMENTO DE VOOS PREMIUM
===============================
Analisa voos premium considerando:
1. Apenas widebodies (fuselagem larga) com duração > 5 horas
2. Merge entre dados de voos e cabines
3. Uso de médias de cabine quando não há match exato
4. Análise dos 10 aviões mais usados
"""

import pandas as pd
import numpy as np
import os

# =============================================================================
# DEFINIÇÕES
# =============================================================================

# Widebody aircraft types (fuselagem larga)
WIDEBODY_TYPES = [
    # Boeing
    'B747', '747', 'B744', 'B748',  # 747 family
    'B767', '767', 'B762', 'B763', 'B764',  # 767 family
    'B777', '777', 'B772', 'B773', 'B77L', 'B77W',  # 777 family
    'B787', '787', 'B788', 'B789', 'B78X',  # 787 Dreamliner
    
    # Airbus
    'A300', 'A310', 'A30B',  # A300/A310
    'A330', 'A332', 'A333', 'A338', 'A339',  # A330 family
    'A340', 'A342', 'A343', 'A345', 'A346',  # A340 family
    'A350', 'A359', 'A35K',  # A350 XWB
    'A380', 'A388',  # A380
    
    # McDonnell Douglas
    'MD11', 'DC10', 'MD10',  # MD-11/DC-10
    
    # Outros
    'IL96', 'IL86',  # Ilyushin widebodies
]

# Duração mínima de voo em segundos (5 horas)
MIN_FLIGHT_DURATION_SEC = 5 * 3600  # 18000 seconds

# Aeroportos principais
MAIN_AIRPORTS = ['KDFW', 'KLAX', 'KJFK', 'KSFO', 'KORD', 'KIAH']

# =============================================================================
# FUNÇÕES
# =============================================================================

def is_widebody(aircraft_type):
    """Verifica se o avião é widebody"""
    if pd.isna(aircraft_type):
        return False
    aircraft_type_upper = str(aircraft_type).upper()
    return any(wb in aircraft_type_upper for wb in WIDEBODY_TYPES)

def load_flight_data(airport_code):
    """Carrega dados de voos de um aeroporto"""
    file_path = f'../../v1/flights an/flights/{airport_code}_completo_interpolado.csv'
    
    if not os.path.exists(file_path):
        print(f"  [AVISO] Arquivo não encontrado: {file_path}")
        return None
    
    df = pd.read_csv(file_path)
    print(f"  [OK] {airport_code}: {len(df):,} voos carregados")
    return df

def load_cabin_data():
    """Carrega dados de configuração de cabine"""
    file_path = '../../v1/flights an/cabins layouts/flights_with_cabin_data_final.csv'
    
    if not os.path.exists(file_path):
        print(f"  [ERRO] Arquivo de cabines não encontrado: {file_path}")
        return None
    
    df = pd.read_csv(file_path)
    print(f"  [OK] Dados de cabine carregados: {len(df):,} registros")
    return df

def calculate_cabin_averages(cabin_df):
    """
    Calcula médias de configuração de cabine por tipo de avião
    
    Returns:
        dict: Dicionário com médias por aircraft type
    """
    # Colunas de assentos
    seat_cols = ['first_class_seats', 'business_class_seats', 
                 'premium_economy_seats', 'economy_seats', 'total_seats']
    
    # Calcular médias por tipo de avião (seatguru_aircraft_model)
    cabin_avg = cabin_df.groupby('seatguru_aircraft_model')[seat_cols].mean().to_dict('index')
    
    # Também calcular por 'type' (código ICAO do avião)
    cabin_avg_by_type = cabin_df.groupby('type')[seat_cols].mean().to_dict('index')
    
    return cabin_avg, cabin_avg_by_type

def merge_flight_with_cabin(flight_df, cabin_df, cabin_avg, cabin_avg_by_type):
    """
    Faz merge entre dados de voo e cabine
    Quando não há match exato, usa a média do avião
    """
    print("\n--- MERGE DE VOOS COM DADOS DE CABINE ---")
    
    # Tentar merge direto por reg (aircraft registration) e type
    merged = flight_df.merge(
        cabin_df[['reg', 'type', 'first_class_seats', 'business_class_seats', 
                  'premium_economy_seats', 'economy_seats', 'total_seats',
                  'seatguru_aircraft_model']],
        left_on=['aircraft_registration', 'aircraft_type'],
        right_on=['reg', 'type'],
        how='left',
        suffixes=('', '_cabin')
    )
    
    # Contar matches
    n_direct_match = merged['reg'].notna().sum()
    n_no_match = merged['reg'].isna().sum()
    
    print(f"  Direct match: {n_direct_match:,} voos ({n_direct_match/len(merged)*100:.1f}%)")
    print(f"  Sem match: {n_no_match:,} voos ({n_no_match/len(merged)*100:.1f}%)")
    
    # Para voos sem match, usar média do tipo de avião
    print("\n  Aplicando médias para voos sem match...")
    
    seat_cols = ['first_class_seats', 'business_class_seats', 
                 'premium_economy_seats', 'economy_seats', 'total_seats']
    
    for idx, row in merged[merged['reg'].isna()].iterrows():
        aircraft_type = row['aircraft_type']
        
        # Tentar encontrar média por tipo
        if pd.notna(aircraft_type) and aircraft_type in cabin_avg_by_type:
            avg_data = cabin_avg_by_type[aircraft_type]
            for col in seat_cols:
                merged.at[idx, col] = avg_data.get(col, np.nan)
    
    # Recalcular assentos premium (first + business + premium economy)
    merged['premium_seats'] = (
        merged['first_class_seats'].fillna(0) +
        merged['business_class_seats'].fillna(0) +
        merged['premium_economy_seats'].fillna(0)
    )
    
    n_filled = merged[merged['reg'].isna() & merged['premium_seats'].notna()].shape[0]
    print(f"  Preenchidos com média: {n_filled:,} voos")
    
    return merged

def filter_premium_flights(df):
    """
    Filtra voos premium seguindo os critérios:
    - Widebody aircraft
    - Duração > 5 horas
    """
    print("\n--- FILTRANDO VOOS PREMIUM ---")
    
    # Aplicar filtros
    df['is_widebody'] = df['aircraft_type'].apply(is_widebody)
    df['flight_duration_ok'] = df['flight_time_seconds'].fillna(0) >= MIN_FLIGHT_DURATION_SEC
    
    # Filtro combinado
    df_premium = df[df['is_widebody'] & df['flight_duration_ok']].copy()
    
    print(f"  Total de voos: {len(df):,}")
    print(f"  Widebody: {df['is_widebody'].sum():,} ({df['is_widebody'].sum()/len(df)*100:.1f}%)")
    print(f"  Duração > 5h: {df['flight_duration_ok'].sum():,} ({df['flight_duration_ok'].sum()/len(df)*100:.1f}%)")
    print(f"  PREMIUM (widebody + >5h): {len(df_premium):,} ({len(df_premium)/len(df)*100:.1f}%)")
    
    return df_premium

def analyze_top_aircraft(df, n=10):
    """
    Analisa os N aviões mais usados
    """
    print(f"\n--- TOP {n} AVIÕES MAIS USADOS ---")
    
    # Contar voos por tipo de avião
    top_aircraft = df.groupby('aircraft_type').agg({
        'fr24_id': 'count',  # número de voos
        'premium_seats': 'mean',  # média de assentos premium
        'first_class_seats': 'mean',
        'business_class_seats': 'mean',
        'premium_economy_seats': 'mean',
        'economy_seats': 'mean',
        'total_seats': 'mean'
    }).rename(columns={'fr24_id': 'n_flights'})
    
    top_aircraft = top_aircraft.sort_values('n_flights', ascending=False).head(n)
    
    print("\nTipo de Avião | Voos | Média Premium | First | Business | Prem Econ | Economy | Total")
    print("-" * 100)
    for aircraft, row in top_aircraft.iterrows():
        print(f"{aircraft:12} | {row['n_flights']:5.0f} | {row['premium_seats']:13.1f} | "
              f"{row['first_class_seats']:5.1f} | {row['business_class_seats']:8.1f} | "
              f"{row['premium_economy_seats']:9.1f} | {row['economy_seats']:7.1f} | {row['total_seats']:5.1f}")
    
    return top_aircraft

def generate_summary_by_airport(df):
    """
    Gera sumário por aeroporto
    """
    print("\n--- SUMÁRIO POR AEROPORTO ---")
    
    summary = df.groupby('query_airport').agg({
        'fr24_id': 'count',  # número de voos
        'premium_seats': ['sum', 'mean'],  # total e média de assentos premium
        'aircraft_type': lambda x: x.nunique()  # tipos únicos de avião
    })
    
    summary.columns = ['n_flights', 'total_premium_seats', 'avg_premium_seats', 'n_aircraft_types']
    summary = summary.sort_values('total_premium_seats', ascending=False)
    
    print("\nAeroporto | Voos | Total Assentos Premium | Média por Voo | Tipos de Avião")
    print("-" * 85)
    for airport, row in summary.iterrows():
        print(f"{airport:9} | {row['n_flights']:5.0f} | {row['total_premium_seats']:22,.0f} | "
              f"{row['avg_premium_seats']:13.1f} | {row['n_aircraft_types']:14.0f}")
    
    # Calcular assentos premium por dia (assumindo 1 ano de dados)
    print("\n--- ASSENTOS PREMIUM POR DIA (estimativa) ---")
    for airport, row in summary.iterrows():
        daily_seats = row['total_premium_seats'] / 365  # assumindo 1 ano
        print(f"{airport}: {daily_seats:,.0f} assentos premium/dia")
    
    return summary

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("="*80)
    print("ANÁLISE DE VOOS PREMIUM - WIDEBODIES > 5 HORAS")
    print("="*80)
    
    # 1. Carregar dados de cabine
    print("\n[1/5] CARREGANDO DADOS DE CABINE...")
    cabin_df = load_cabin_data()
    
    if cabin_df is None:
        print("\n[ERRO] Não foi possível carregar dados de cabine. Abortando.")
        exit(1)
    
    # 2. Calcular médias de cabine por tipo de avião
    print("\n[2/5] CALCULANDO MÉDIAS DE CABINE POR TIPO DE AVIÃO...")
    cabin_avg, cabin_avg_by_type = calculate_cabin_averages(cabin_df)
    print(f"  [OK] Médias calculadas para {len(cabin_avg)} modelos e {len(cabin_avg_by_type)} tipos")
    
    # 3. Carregar e processar dados de voos de todos os aeroportos
    print("\n[3/5] CARREGANDO DADOS DE VOOS...")
    all_flights = []
    
    for airport in MAIN_AIRPORTS:
        df = load_flight_data(airport)
        if df is not None:
            df['query_airport'] = airport
            all_flights.append(df)
    
    if not all_flights:
        print("\n[ERRO] Nenhum dado de voo foi carregado. Abortando.")
        exit(1)
    
    df_all_flights = pd.concat(all_flights, ignore_index=True)
    print(f"\n  [TOTAL] {len(df_all_flights):,} voos carregados de {len(all_flights)} aeroportos")
    
    # 4. Fazer merge com dados de cabine
    print("\n[4/5] FAZENDO MERGE COM DADOS DE CABINE...")
    df_merged = merge_flight_with_cabin(df_all_flights, cabin_df, cabin_avg, cabin_avg_by_type)
    
    # 5. Filtrar voos premium (widebody + >5h)
    print("\n[5/5] FILTRANDO VOOS PREMIUM...")
    df_premium = filter_premium_flights(df_merged)
    
    # Salvar resultado
    output_file = 'premium_flights_analysis.csv'
    df_premium.to_csv(output_file, index=False)
    print(f"\n[OK] Dados salvos em: {output_file}")
    
    # Análises adicionais
    print("\n" + "="*80)
    print("ANÁLISES ADICIONAIS")
    print("="*80)
    
    # Top 10 aviões
    top_aircraft = analyze_top_aircraft(df_premium, n=10)
    top_aircraft.to_csv('premium_top10_aircraft.csv')
    print(f"\n[OK] Top 10 aviões salvos em: premium_top10_aircraft.csv")
    
    # Sumário por aeroporto
    summary = generate_summary_by_airport(df_premium)
    summary.to_csv('premium_summary_by_airport.csv')
    print(f"\n[OK] Sumário por aeroporto salvo em: premium_summary_by_airport.csv")
    
    print("\n" + "="*80)
    print("PROCESSAMENTO CONCLUÍDO!")
    print("="*80)

