# -*- coding: utf-8 -*-
"""
HEATMAPS TEMPORAIS - VOOS PREMIUM (AMOSTRA)
============================================
Versão otimizada que processa uma amostra dos dados
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import pytz
import warnings
warnings.filterwarnings('ignore')

# Sample size
SAMPLE_SIZE = 100000  # Processar 100k voos

# Timezones dos aeroportos
AIRPORT_TIMEZONES = {
    'KJFK': 'America/New_York',
    'KLAX': 'America/Los_Angeles',
    'KORD': 'America/Chicago',
    'KDFW': 'America/Chicago',
    'KSFO': 'America/Los_Angeles',
    'KIAH': 'America/Chicago',
}

AIRPORT_NAMES = {
    'KJFK': 'New York JFK',
    'KLAX': 'Los Angeles',
    'KORD': 'Chicago ORD',
    'KDFW': 'Dallas DFW',
    'KSFO': 'San Francisco',
    'KIAH': 'Houston IAH',
}

print("="*80)
print("ANALISE TEMPORAL - VOOS PREMIUM (AMOSTRA DE 100K VOOS)")
print("="*80)

# 1. Carregar AMOSTRA dos dados
print("\n[1/6] CARREGANDO AMOSTRA DOS DADOS...")
df = pd.read_csv('premium_flights_analysis.csv', nrows=SAMPLE_SIZE)
print(f"  [OK] {len(df):,} voos carregados (amostra)")

# 2. Converter UTC para local
print("\n[2/6] CONVERTENDO PARA HORARIO LOCAL...")
df['first_seen'] = pd.to_datetime(df['first_seen'], utc=True)

# Criar coluna local para cada aeroporto
df['first_seen_local'] = df['first_seen'].copy()

for airport, tz_name in AIRPORT_TIMEZONES.items():
    mask = df['query_airport'] == airport
    if mask.any():
        local_tz = pytz.timezone(tz_name)
        df.loc[mask, 'first_seen_local'] = df.loc[mask, 'first_seen'].dt.tz_convert(local_tz)
        print(f"  [OK] {airport}: {mask.sum():,} voos convertidos")

# 3. Extrair features temporais
print("\n[3/6] EXTRAINDO FEATURES TEMPORAIS...")
df['hour_local'] = df['first_seen_local'].dt.hour
df['day_of_week'] = df['first_seen_local'].dt.dayofweek
df['day_name'] = df['first_seen_local'].dt.day_name()
print("  [OK] Features extraidas")

# 4. Criar heatmaps por aeroporto (Departures e Arrivals)
print("\n[4/6] CRIANDO HEATMAPS POR AEROPORTO (DEP/ARR)...")

day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
airports = sorted(df['query_airport'].unique())

for airport in airports:
    airport_name = AIRPORT_NAMES.get(airport, airport)
    print(f"  Processando {airport_name}...")
    
    airport_data = df[df['query_airport'] == airport].copy()
    
    # Identificar DEPARTURES e ARRIVALS
    if 'direction' in airport_data.columns:
        departures = airport_data[airport_data['direction'].str.upper().str.contains('DEP', na=False)]
        arrivals = airport_data[airport_data['direction'].str.upper().str.contains('ARR', na=False)]
    elif 'orig_icao' in airport_data.columns and 'dest_icao' in airport_data.columns:
        departures = airport_data[airport_data['orig_icao'] == airport]
        arrivals = airport_data[airport_data['dest_icao'] == airport]
    else:
        departures = airport_data
        arrivals = airport_data
    
    # Criar figura com dois subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(24, 8))
    
    # DEPARTURES
    if len(departures) > 0:
        pivot_dep = departures.groupby(['day_of_week', 'hour_local'])['premium_seats'].mean().reset_index()
        pivot_table_dep = pivot_dep.pivot(index='day_of_week', columns='hour_local', values='premium_seats')
    else:
        pivot_table_dep = pd.DataFrame(0, index=range(7), columns=range(24))
    
    # Garantir todas as horas e dias
    for hour in range(24):
        if hour not in pivot_table_dep.columns:
            pivot_table_dep[hour] = 0
    for day in range(7):
        if day not in pivot_table_dep.index:
            pivot_table_dep.loc[day] = 0
    
    pivot_table_dep = pivot_table_dep.sort_index(axis=0).sort_index(axis=1)
    pivot_table_dep.index = [day_names[int(i)] for i in pivot_table_dep.index]
    
    # ARRIVALS
    if len(arrivals) > 0:
        pivot_arr = arrivals.groupby(['day_of_week', 'hour_local'])['premium_seats'].mean().reset_index()
        pivot_table_arr = pivot_arr.pivot(index='day_of_week', columns='hour_local', values='premium_seats')
    else:
        pivot_table_arr = pd.DataFrame(0, index=range(7), columns=range(24))
    
    # Garantir todas as horas e dias
    for hour in range(24):
        if hour not in pivot_table_arr.columns:
            pivot_table_arr[hour] = 0
    for day in range(7):
        if day not in pivot_table_arr.index:
            pivot_table_arr.loc[day] = 0
    
    pivot_table_arr = pivot_table_arr.sort_index(axis=0).sort_index(axis=1)
    pivot_table_arr.index = [day_names[int(i)] for i in pivot_table_arr.index]
    
    # Mesma escala para ambos
    vmax = max(pivot_table_dep.max().max(), pivot_table_arr.max().max())
    if vmax == 0:
        vmax = 1
    
    # Plotar DEPARTURES
    sns.heatmap(pivot_table_dep, annot=False, cmap='YlOrRd',
                cbar_kws={'label': 'Premium Seats'}, ax=ax1,
                vmin=0, vmax=vmax, linewidths=0.5, linecolor='white')
    ax1.set_title(f'DEPARTURES - {airport_name}\nPremium Seats by Day/Hour', 
                  fontsize=14, fontweight='bold', pad=15)
    ax1.set_xlabel('Time of Day', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Day of Week', fontsize=12, fontweight='bold')
    ax1.set_xticklabels([f'{h:02d}h' for h in range(24)], rotation=0)
    ax1.set_yticklabels(day_names, rotation=0)
    
    # Plotar ARRIVALS
    sns.heatmap(pivot_table_arr, annot=False, cmap='YlOrRd',
                cbar_kws={'label': 'Premium Seats'}, ax=ax2,
                vmin=0, vmax=vmax, linewidths=0.5, linecolor='white')
    ax2.set_title(f'ARRIVALS - {airport_name}\nPremium Seats by Day/Hour', 
                  fontsize=14, fontweight='bold', pad=15)
    ax2.set_xlabel('Time of Day', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Day of Week', fontsize=12, fontweight='bold')
    ax2.set_xticklabels([f'{h:02d}h' for h in range(24)], rotation=0)
    ax2.set_yticklabels(day_names, rotation=0)
    
    plt.tight_layout()
    output_filename = f'heatmap_{airport.lower()}_departures_arrivals_sample.png'
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"    [OK] Salvo: {output_filename}")
    plt.close()

print("  [OK] Todos os heatmaps gerados")

# 5. Estatísticas por aeroporto
print("\n[5/6] ESTATISTICAS POR AEROPORTO...")
for airport in airports:
    airport_name = AIRPORT_NAMES.get(airport, airport)
    airport_data = df[df['query_airport'] == airport]
    
    if 'direction' in airport_data.columns:
        n_dep = airport_data['direction'].str.upper().str.contains('DEP', na=False).sum()
        n_arr = airport_data['direction'].str.upper().str.contains('ARR', na=False).sum()
    else:
        n_dep = len(airport_data)
        n_arr = len(airport_data)
    
    print(f"  {airport_name}: {len(airport_data):,} voos (Dep: {n_dep:,}, Arr: {n_arr:,})")

# 6. Sumário de horários de pico
print("\n[6/6] IDENTIFICANDO HORARIOS DE PICO...")
hourly = df.groupby(['query_airport', 'hour_local']).agg({
    'premium_seats': 'sum',
    'fr24_id': 'count'
}).reset_index()
hourly.columns = ['query_airport', 'hour_local', 'total_premium_seats', 'n_flights']

peak_hours = hourly.loc[hourly.groupby('query_airport')['total_premium_seats'].idxmax()]
print("\nAeroporto | Hora de Pico (Local) | Assentos Premium | Voos")
print("-" * 75)
for _, row in peak_hours.iterrows():
    airport_name = AIRPORT_NAMES.get(row['query_airport'], row['query_airport'])
    print(f"{airport_name:20} | {int(row['hour_local']):02d}:00 | "
          f"{row['total_premium_seats']:20,.0f} | {row['n_flights']:5.0f}")

print("\n" + "="*80)
print("PROCESSAMENTO CONCLUIDO!")
print("="*80)
print("\nNOTA: Esta e uma AMOSTRA de 100k voos.")
print("Para processar todos os dados, execute: python create_premium_heatmaps.py")

