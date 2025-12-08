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

# 4. Criar heatmap por hora
print("\n[4/6] CRIANDO HEATMAP POR HORA...")
pivot_data = df.groupby(['query_airport', 'hour_local'])['premium_seats'].sum().reset_index()
pivot_table = pivot_data.pivot(index='query_airport', columns='hour_local', values='premium_seats')
pivot_table.index = pivot_table.index.map(lambda x: AIRPORT_NAMES.get(x, x))

plt.figure(figsize=(20, 8))
sns.heatmap(pivot_table, annot=True, fmt='.0f', cmap='YlOrRd',
            cbar_kws={'label': 'Assentos Premium'}, linewidths=0.5)
plt.title('Assentos Premium por Hora do Dia (Horario Local)', fontsize=16, fontweight='bold')
plt.xlabel('Hora do Dia (Horario Local)', fontsize=12)
plt.ylabel('Aeroporto', fontsize=12)
plt.tight_layout()
plt.savefig('heatmap_hour_local_sample.png', dpi=300, bbox_inches='tight')
print("  [OK] Salvo: heatmap_hour_local_sample.png")
plt.close()

# 5. Criar heatmap por dia da semana
print("\n[5/6] CRIANDO HEATMAP POR DIA DA SEMANA...")
day_names = ['Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo']
pivot_day = df.groupby(['query_airport', 'day_of_week'])['premium_seats'].sum().reset_index()
pivot_day_table = pivot_day.pivot(index='query_airport', columns='day_of_week', values='premium_seats')
pivot_day_table.columns = day_names
pivot_day_table.index = pivot_day_table.index.map(lambda x: AIRPORT_NAMES.get(x, x))

plt.figure(figsize=(14, 8))
sns.heatmap(pivot_day_table, annot=True, fmt='.0f', cmap='viridis',
            cbar_kws={'label': 'Assentos Premium'}, linewidths=0.5)
plt.title('Assentos Premium por Dia da Semana (Horario Local)', fontsize=16, fontweight='bold')
plt.xlabel('Dia da Semana', fontsize=12)
plt.ylabel('Aeroporto', fontsize=12)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('heatmap_day_local_sample.png', dpi=300, bbox_inches='tight')
print("  [OK] Salvo: heatmap_day_local_sample.png")
plt.close()

# 6. Grafico de padrao horario
print("\n[6/6] CRIANDO GRAFICO DE PADRAO HORARIO...")
hourly = df.groupby(['query_airport', 'hour_local']).agg({
    'premium_seats': 'sum',
    'fr24_id': 'count'
}).reset_index()
hourly.columns = ['query_airport', 'hour_local', 'total_premium_seats', 'n_flights']

fig, axes = plt.subplots(2, 1, figsize=(16, 10))

for airport in sorted(df['query_airport'].unique()):
    data = hourly[hourly['query_airport'] == airport]
    axes[0].plot(data['hour_local'], data['total_premium_seats'],
                 marker='o', linewidth=2, label=AIRPORT_NAMES.get(airport, airport))

axes[0].set_title('Total de Assentos Premium por Hora (Horario Local)', fontsize=14, fontweight='bold')
axes[0].set_xlabel('Hora do Dia', fontsize=12)
axes[0].set_ylabel('Total de Assentos Premium', fontsize=12)
axes[0].legend(loc='best')
axes[0].grid(True, alpha=0.3)
axes[0].set_xticks(range(0, 24))

for airport in sorted(df['query_airport'].unique()):
    data = hourly[hourly['query_airport'] == airport]
    axes[1].plot(data['hour_local'], data['n_flights'],
                 marker='s', linewidth=2, label=AIRPORT_NAMES.get(airport, airport))

axes[1].set_title('Numero de Voos Premium por Hora (Horario Local)', fontsize=14, fontweight='bold')
axes[1].set_xlabel('Hora do Dia', fontsize=12)
axes[1].set_ylabel('Numero de Voos', fontsize=12)
axes[1].legend(loc='best')
axes[1].grid(True, alpha=0.3)
axes[1].set_xticks(range(0, 24))

plt.tight_layout()
plt.savefig('hourly_pattern_sample.png', dpi=300, bbox_inches='tight')
print("  [OK] Salvo: hourly_pattern_sample.png")
plt.close()

# Identificar horarios de pico
print("\n--- HORARIOS DE PICO POR AEROPORTO ---")
peak_hours = hourly.loc[hourly.groupby('query_airport')['total_premium_seats'].idxmax()]
print("Aeroporto | Hora de Pico (Local) | Assentos Premium | Voos")
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

