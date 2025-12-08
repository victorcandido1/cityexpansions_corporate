# -*- coding: utf-8 -*-
"""
HEATMAPS TEMPORAIS - VOOS PREMIUM
===================================
Converte UTC para horário local e cria heatmaps de distribuição temporal
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import pytz
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# DEFINIÇÕES
# =============================================================================

# Timezones dos aeroportos
AIRPORT_TIMEZONES = {
    'KJFK': 'America/New_York',      # Eastern Time (UTC-5/-4)
    'KLAX': 'America/Los_Angeles',   # Pacific Time (UTC-8/-7)
    'KORD': 'America/Chicago',        # Central Time (UTC-6/-5)
    'KDFW': 'America/Chicago',        # Central Time (UTC-6/-5)
    'KSFO': 'America/Los_Angeles',   # Pacific Time (UTC-8/-7)
    'KIAH': 'America/Chicago',        # Central Time (UTC-6/-5)
}

# Nomes amigáveis
AIRPORT_NAMES = {
    'KJFK': 'New York JFK',
    'KLAX': 'Los Angeles',
    'KORD': 'Chicago ORD',
    'KDFW': 'Dallas DFW',
    'KSFO': 'San Francisco',
    'KIAH': 'Houston IAH',
}

# =============================================================================
# FUNÇÕES
# =============================================================================

def convert_utc_to_local(df, airport_col='query_airport', datetime_col='first_seen'):
    """
    Converte timestamps UTC para horário local do aeroporto
    Usando operações vetorizadas para melhor performance
    """
    print(f"\n--- CONVERTENDO {datetime_col} DE UTC PARA HORÁRIO LOCAL ---")
    
    # Converter string para datetime se necessário
    if df[datetime_col].dtype == 'object':
        print(f"  Convertendo para datetime...")
        df[datetime_col] = pd.to_datetime(df[datetime_col], utc=True, errors='coerce')
    
    # Garantir que está em UTC
    if df[datetime_col].dt.tz is None:
        print(f"  Localizando para UTC...")
        df[datetime_col] = df[datetime_col].dt.tz_localize('UTC')
    
    # Criar coluna de horário local para cada aeroporto
    print(f"  Convertendo para horário local por aeroporto...")
    
    # Inicializar com cópia do original
    df[f'{datetime_col}_local'] = df[datetime_col].copy()
    
    for airport, tz_name in AIRPORT_TIMEZONES.items():
        print(f"    Processando {airport} ({tz_name})...")
        mask = df[airport_col] == airport
        if mask.any():
            # Converter para timezone local
            local_tz = pytz.timezone(tz_name)
            df.loc[mask, f'{datetime_col}_local'] = df.loc[mask, datetime_col].dt.tz_convert(local_tz)
    
    print(f"  [OK] Conversão concluída")
    return df

def extract_temporal_features(df, datetime_col='first_seen_local'):
    """
    Extrai features temporais (hora, dia da semana, etc.)
    """
    print(f"\n--- EXTRAINDO FEATURES TEMPORAIS ---")
    
    df['hour_local'] = df[datetime_col].dt.hour
    df['day_of_week'] = df[datetime_col].dt.dayofweek  # 0=Monday, 6=Sunday
    df['day_name'] = df[datetime_col].dt.day_name()
    df['month'] = df[datetime_col].dt.month
    df['date'] = df[datetime_col].dt.date
    
    print(f"  [OK] Features extraídas:")
    print(f"       - hour_local (0-23)")
    print(f"       - day_of_week (0-6)")
    print(f"       - day_name")
    print(f"       - month")
    
    return df

def create_heatmap_by_hour(df, value_col='premium_seats', 
                           title='Assentos Premium por Hora do Dia (Horário Local)',
                           output_file='heatmap_premium_by_hour.png'):
    """
    Cria heatmap de distribuição por hora do dia e aeroporto
    """
    print(f"\n--- CRIANDO HEATMAP: {title} ---")
    
    # Agregar por aeroporto e hora
    pivot_data = df.groupby(['query_airport', 'hour_local'])[value_col].sum().reset_index()
    pivot_table = pivot_data.pivot(index='query_airport', columns='hour_local', values=value_col)
    
    # Reordenar por nome amigável
    pivot_table.index = pivot_table.index.map(lambda x: AIRPORT_NAMES.get(x, x))
    
    # Criar figura
    plt.figure(figsize=(20, 8))
    
    # Criar heatmap
    sns.heatmap(pivot_table, 
                annot=True, 
                fmt='.0f', 
                cmap='YlOrRd', 
                cbar_kws={'label': value_col.replace('_', ' ').title()},
                linewidths=0.5,
                linecolor='white')
    
    plt.title(title, fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Hora do Dia (Horário Local)', fontsize=12, fontweight='bold')
    plt.ylabel('Aeroporto', fontsize=12, fontweight='bold')
    plt.xticks(rotation=0)
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    # Salvar
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  [OK] Heatmap salvo: {output_file}")
    plt.close()

def create_heatmap_by_day_of_week(df, value_col='premium_seats',
                                   title='Assentos Premium por Dia da Semana',
                                   output_file='heatmap_premium_by_day.png'):
    """
    Cria heatmap de distribuição por dia da semana e aeroporto
    """
    print(f"\n--- CRIANDO HEATMAP: {title} ---")
    
    # Nomes dos dias
    day_names = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    
    # Agregar por aeroporto e dia
    pivot_data = df.groupby(['query_airport', 'day_of_week'])[value_col].sum().reset_index()
    pivot_table = pivot_data.pivot(index='query_airport', columns='day_of_week', values=value_col)
    
    # Renomear colunas
    pivot_table.columns = day_names
    
    # Reordenar por nome amigável
    pivot_table.index = pivot_table.index.map(lambda x: AIRPORT_NAMES.get(x, x))
    
    # Criar figura
    plt.figure(figsize=(14, 8))
    
    # Criar heatmap
    sns.heatmap(pivot_table, 
                annot=True, 
                fmt='.0f', 
                cmap='viridis', 
                cbar_kws={'label': value_col.replace('_', ' ').title()},
                linewidths=0.5,
                linecolor='white')
    
    plt.title(title, fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Dia da Semana', fontsize=12, fontweight='bold')
    plt.ylabel('Aeroporto', fontsize=12, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    # Salvar
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  [OK] Heatmap salvo: {output_file}")
    plt.close()

def create_hourly_pattern_chart(df, output_file='hourly_pattern_by_airport.png'):
    """
    Cria gráfico de linha mostrando padrão horário por aeroporto
    """
    print(f"\n--- CRIANDO GRÁFICO DE PADRÃO HORÁRIO ---")
    
    # Agregar por aeroporto e hora
    hourly_data = df.groupby(['query_airport', 'hour_local']).agg({
        'premium_seats': 'sum',
        'fr24_id': 'count'
    }).reset_index()
    
    hourly_data.columns = ['query_airport', 'hour_local', 'total_premium_seats', 'n_flights']
    
    # Calcular média por voo
    hourly_data['avg_premium_per_flight'] = hourly_data['total_premium_seats'] / hourly_data['n_flights']
    
    # Criar figura com subplots
    fig, axes = plt.subplots(2, 1, figsize=(16, 10))
    
    # Plot 1: Total de assentos premium por hora
    for airport in sorted(df['query_airport'].unique()):
        data = hourly_data[hourly_data['query_airport'] == airport]
        axes[0].plot(data['hour_local'], data['total_premium_seats'], 
                     marker='o', linewidth=2, label=AIRPORT_NAMES.get(airport, airport))
    
    axes[0].set_title('Total de Assentos Premium por Hora do Dia (Horário Local)', 
                      fontsize=14, fontweight='bold')
    axes[0].set_xlabel('Hora do Dia', fontsize=12)
    axes[0].set_ylabel('Total de Assentos Premium', fontsize=12)
    axes[0].legend(loc='best', frameon=True, shadow=True)
    axes[0].grid(True, alpha=0.3)
    axes[0].set_xticks(range(0, 24))
    
    # Plot 2: Número de voos por hora
    for airport in sorted(df['query_airport'].unique()):
        data = hourly_data[hourly_data['query_airport'] == airport]
        axes[1].plot(data['hour_local'], data['n_flights'], 
                     marker='s', linewidth=2, label=AIRPORT_NAMES.get(airport, airport))
    
    axes[1].set_title('Número de Voos Premium por Hora do Dia (Horário Local)', 
                      fontsize=14, fontweight='bold')
    axes[1].set_xlabel('Hora do Dia', fontsize=12)
    axes[1].set_ylabel('Número de Voos', fontsize=12)
    axes[1].legend(loc='best', frameon=True, shadow=True)
    axes[1].grid(True, alpha=0.3)
    axes[1].set_xticks(range(0, 24))
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  [OK] Gráfico salvo: {output_file}")
    plt.close()

def create_combined_heatmap(df, output_file='heatmap_hour_day_combined.png'):
    """
    Cria heatmap combinado: hora x dia da semana para cada aeroporto
    """
    print(f"\n--- CRIANDO HEATMAP COMBINADO (HORA X DIA) ---")
    
    airports = sorted(df['query_airport'].unique())
    n_airports = len(airports)
    
    # Criar figura com subplots
    fig, axes = plt.subplots(2, 3, figsize=(24, 12))
    axes = axes.flatten()
    
    day_names = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
    
    for idx, airport in enumerate(airports):
        airport_data = df[df['query_airport'] == airport]
        
        # Agregar por hora e dia
        pivot_data = airport_data.groupby(['hour_local', 'day_of_week'])['premium_seats'].sum().reset_index()
        pivot_table = pivot_data.pivot(index='day_of_week', columns='hour_local', values='premium_seats')
        
        # Renomear índice
        pivot_table.index = [day_names[i] for i in pivot_table.index]
        
        # Criar heatmap
        sns.heatmap(pivot_table, 
                    annot=False, 
                    cmap='RdYlGn', 
                    cbar_kws={'label': 'Assentos Premium'},
                    ax=axes[idx],
                    linewidths=0.1)
        
        axes[idx].set_title(AIRPORT_NAMES.get(airport, airport), 
                           fontsize=12, fontweight='bold')
        axes[idx].set_xlabel('Hora do Dia (Local)', fontsize=10)
        axes[idx].set_ylabel('Dia da Semana', fontsize=10)
    
    plt.suptitle('Distribuição de Assentos Premium por Hora e Dia da Semana\n(Horário Local de Cada Aeroporto)', 
                 fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  [OK] Heatmap combinado salvo: {output_file}")
    plt.close()

def generate_temporal_summary(df, output_file='temporal_summary.csv'):
    """
    Gera sumário estatístico temporal
    """
    print(f"\n--- GERANDO SUMÁRIO TEMPORAL ---")
    
    # Por hora
    hourly_summary = df.groupby(['query_airport', 'hour_local']).agg({
        'premium_seats': ['sum', 'mean', 'count'],
        'fr24_id': 'count'
    }).reset_index()
    
    hourly_summary.columns = ['query_airport', 'hour_local', 
                              'total_premium_seats', 'avg_premium_seats', 
                              'flights_with_premium', 'total_flights']
    
    # Identificar horários de pico
    peak_hours = hourly_summary.loc[hourly_summary.groupby('query_airport')['total_premium_seats'].idxmax()]
    
    print("\n--- HORÁRIOS DE PICO POR AEROPORTO ---")
    print("Aeroporto | Hora de Pico (Local) | Assentos Premium | Voos")
    print("-" * 75)
    for _, row in peak_hours.iterrows():
        airport_name = AIRPORT_NAMES.get(row['query_airport'], row['query_airport'])
        print(f"{airport_name:20} | {int(row['hour_local']):02d}:00 | "
              f"{row['total_premium_seats']:20,.0f} | {row['total_flights']:5.0f}")
    
    # Salvar sumário completo
    hourly_summary.to_csv(output_file, index=False)
    print(f"\n[OK] Sumário temporal salvo: {output_file}")
    
    return hourly_summary, peak_hours

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("="*80)
    print("ANALISE TEMPORAL DE VOOS PREMIUM - CONVERSAO UTC PARA LOCAL + HEATMAPS")
    print("="*80)
    
    # 1. Carregar dados
    print("\n[1/7] CARREGANDO DADOS DE VOOS PREMIUM...")
    
    try:
        df = pd.read_csv('premium_flights_analysis.csv')
        print(f"  [OK] {len(df):,} voos premium carregados")
    except FileNotFoundError:
        print("\n[ERRO] Arquivo 'premium_flights_analysis.csv' não encontrado!")
        print("Execute primeiro: python process_premium_flights.py")
        exit(1)
    
    # 2. Converter UTC para horário local
    print("\n[2/7] CONVERTENDO UTC PARA HORÁRIO LOCAL...")
    df = convert_utc_to_local(df, datetime_col='first_seen')
    
    # 3. Extrair features temporais
    print("\n[3/7] EXTRAINDO FEATURES TEMPORAIS...")
    df = extract_temporal_features(df, datetime_col='first_seen_local')
    
    # 4. Salvar dataset com timestamps locais
    print("\n[4/7] SALVANDO DATASET COM HORÁRIOS LOCAIS...")
    output_file = 'premium_flights_with_local_time.csv'
    
    # Selecionar apenas colunas essenciais para reduzir tamanho
    cols_to_save = ['query_airport', 'aircraft_type', 'flight_time_seconds',
                    'premium_seats', 'first_class_seats', 'business_class_seats',
                    'premium_economy_seats', 'first_seen', 'first_seen_local',
                    'hour_local', 'day_of_week', 'day_name', 'month']
    
    df[cols_to_save].to_csv(output_file, index=False)
    print(f"  [OK] Salvo: {output_file}")
    
    # 5. Criar heatmaps
    print("\n[5/7] CRIANDO HEATMAPS...")
    
    # Heatmap por hora do dia
    create_heatmap_by_hour(df, 
                           value_col='premium_seats',
                           title='Distribuição de Assentos Premium por Hora do Dia\n(Horário Local de Cada Aeroporto)',
                           output_file='heatmap_premium_seats_by_hour_local.png')
    
    create_heatmap_by_hour(df, 
                           value_col='fr24_id',
                           title='Número de Voos Premium por Hora do Dia\n(Horário Local de Cada Aeroporto)',
                           output_file='heatmap_flights_by_hour_local.png')
    
    # Heatmap por dia da semana
    create_heatmap_by_day_of_week(df,
                                   value_col='premium_seats',
                                   title='Distribuição de Assentos Premium por Dia da Semana\n(Horário Local de Cada Aeroporto)',
                                   output_file='heatmap_premium_seats_by_day_local.png')
    
    # 6. Criar gráficos de padrão horário
    print("\n[6/7] CRIANDO GRÁFICOS DE PADRÃO HORÁRIO...")
    create_hourly_pattern_chart(df, output_file='hourly_pattern_by_airport_local.png')
    
    # Heatmap combinado
    create_combined_heatmap(df, output_file='heatmap_hour_day_combined_local.png')
    
    # 7. Gerar sumário temporal
    print("\n[7/7] GERANDO SUMÁRIO TEMPORAL...")
    hourly_summary, peak_hours = generate_temporal_summary(df, 
                                                            output_file='temporal_summary_local.csv')
    
    print("\n" + "="*80)
    print("PROCESSAMENTO CONCLUÍDO!")
    print("="*80)
    
    print("\n📁 ARQUIVOS GERADOS:")
    print("  Dados:")
    print("    - premium_flights_with_local_time.csv (dataset com horários locais)")
    print("    - temporal_summary_local.csv (sumário temporal)")
    print("\n  Heatmaps:")
    print("    - heatmap_premium_seats_by_hour_local.png")
    print("    - heatmap_flights_by_hour_local.png")
    print("    - heatmap_premium_seats_by_day_local.png")
    print("    - heatmap_hour_day_combined_local.png")
    print("\n  Gráficos:")
    print("    - hourly_pattern_by_airport_local.png")
    
    print("\n💡 TODOS OS HORÁRIOS FORAM CONVERTIDOS PARA HORÁRIO LOCAL DE CADA AEROPORTO")
    print("   - JFK: Eastern Time (UTC-5/-4)")
    print("   - LAX: Pacific Time (UTC-8/-7)")
    print("   - ORD/DFW/IAH: Central Time (UTC-6/-5)")
    print("   - SFO: Pacific Time (UTC-8/-7)")

