"""
Cria gráficos V4 com cenário PESSIMISTA
Inclui análise de velocidade por 100m
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Configuração
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 11

# Cores
COLORS = {
    'car': '#e74c3c',
    'heli': '#3498db',
    'ny': '#2c3e50',
    'la': '#e67e22',
    'savings': '#27ae60'
}

# Carregar dados
df = pd.read_csv('analysis_v4_pessimistic.csv')
segments = pd.read_csv('route_segments_100m.csv')

# Criar diretórios
Path('charts_v4_en').mkdir(exist_ok=True)
Path('charts_v4_pt').mkdir(exist_ok=True)

# ============================================================================
# FIGURA 1: Comparação Carro vs Helicóptero (Worst Case)
# ============================================================================
def fig1_comparison(lang='en'):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    for idx, city in enumerate(['NY', 'LA']):
        ax = axes[idx]
        city_df = df[df['city'] == city]
        
        x = np.arange(len(city_df))
        width = 0.35
        
        car_times = city_df['worst_car_direct_min'].values
        heli_times = city_df['worst_heli_total_min'].values
        
        ax.bar(x - width/2, car_times, width, label='Carro' if lang=='pt' else 'Car', color=COLORS['car'], alpha=0.8)
        ax.bar(x + width/2, heli_times, width, label='Helicóptero' if lang=='pt' else 'Helicopter', color=COLORS['heli'], alpha=0.8)
        
        ax.set_xlabel('ZIP Code', fontsize=12)
        ax.set_ylabel('Tempo (min)' if lang=='pt' else 'Time (min)', fontsize=12)
        title_city = 'Nova York' if lang=='pt' and city=='NY' else 'Los Angeles' if city=='LA' else 'New York'
        ax.set_title(f'{title_city} - Pior Cenário (4.68x)' if lang=='pt' else f'{city} - Worst Case (4.68x)', fontsize=14, fontweight='bold')
        ax.legend()
        ax.set_xticks([])
        ax.axhline(y=60, color='gray', linestyle='--', alpha=0.5, label='1h')
        ax.axhline(y=120, color='gray', linestyle='--', alpha=0.5, label='2h')
    
    plt.tight_layout()
    folder = 'charts_v4_pt' if lang=='pt' else 'charts_v4_en'
    plt.savefig(f'{folder}/fig1_comparison_worst.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  -> {folder}/fig1_comparison_worst.png")

# ============================================================================
# FIGURA 2: Box Plot de Economia de Tempo
# ============================================================================
def fig2_savings_boxplot(lang='en'):
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ny_df = df[df['city'] == 'NY']['worst_savings_min'].dropna()
    la_df = df[df['city'] == 'LA']['worst_savings_min'].dropna()
    
    bp = ax.boxplot([ny_df, la_df], labels=['New York', 'Los Angeles'], patch_artist=True)
    bp['boxes'][0].set_facecolor(COLORS['ny'])
    bp['boxes'][1].set_facecolor(COLORS['la'])
    
    for box in bp['boxes']:
        box.set_alpha(0.7)
    
    ax.axhline(y=0, color='red', linestyle='--', alpha=0.7)
    ax.set_ylabel('Economia de Tempo (min)' if lang=='pt' else 'Time Savings (min)', fontsize=12)
    ax.set_title('Economia Helicóptero vs Carro - Pior Cenário' if lang=='pt' else 'Helicopter vs Car Savings - Worst Case', fontsize=14, fontweight='bold')
    
    # Anotações
    ax.annotate(f'Média: {ny_df.mean():.0f} min', xy=(1, ny_df.mean()), fontsize=10)
    ax.annotate(f'Média: {la_df.mean():.0f} min', xy=(2, la_df.mean()), fontsize=10)
    
    plt.tight_layout()
    folder = 'charts_v4_pt' if lang=='pt' else 'charts_v4_en'
    plt.savefig(f'{folder}/fig2_savings_boxplot.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  -> {folder}/fig2_savings_boxplot.png")

# ============================================================================
# FIGURA 3: Velocidade Média por Cenário
# ============================================================================
def fig3_speed_comparison(lang='en'):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    scenarios = ['normal', 'rush', 'worst']
    scenario_labels = {
        'en': ['Normal', 'Rush Hour (1.68x)', 'Worst (4.68x)'],
        'pt': ['Normal', 'Horário de Pico (1.68x)', 'Pior Caso (4.68x)']
    }
    
    for idx, city in enumerate(['NY', 'LA']):
        ax = axes[idx]
        city_df = df[df['city'] == city]
        
        speeds = [
            city_df['speed_to_airport_normal_kmh'].mean(),
            city_df['speed_to_airport_rush_kmh'].mean(),
            city_df['speed_to_airport_worst_kmh'].mean()
        ]
        
        colors = ['#27ae60', '#f39c12', '#e74c3c']
        bars = ax.bar(scenario_labels[lang], speeds, color=colors, alpha=0.8)
        
        for bar, speed in zip(bars, speeds):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                   f'{speed:.1f} km/h', ha='center', fontsize=10)
        
        ax.set_ylabel('Velocidade Média (km/h)' if lang=='pt' else 'Average Speed (km/h)', fontsize=12)
        title_city = 'Nova York' if lang=='pt' and city=='NY' else 'Los Angeles' if city=='LA' else 'New York'
        ax.set_title(f'{title_city}', fontsize=14, fontweight='bold')
        ax.set_ylim(0, max(speeds) * 1.3)
    
    fig.suptitle('Velocidade Média por Cenário de Tráfego' if lang=='pt' else 'Average Speed by Traffic Scenario', 
                fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    folder = 'charts_v4_pt' if lang=='pt' else 'charts_v4_en'
    plt.savefig(f'{folder}/fig3_speed_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  -> {folder}/fig3_speed_comparison.png")

# ============================================================================
# FIGURA 4: Tempo por 100m
# ============================================================================
def fig4_time_per_100m(lang='en'):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    for idx, city in enumerate(['NY', 'LA']):
        ax = axes[idx]
        city_segments = segments[segments['city'] == city]
        
        # Média de tempo por 100m
        normal_time = city_segments['time_100m_normal_sec'].mean()
        rush_time = city_segments['time_100m_rush_sec'].mean()
        worst_time = city_segments['time_100m_worst_sec'].mean()
        
        scenarios = ['Normal', 'Rush (1.68x)', 'Worst (4.68x)']
        times = [normal_time, rush_time, worst_time]
        colors = ['#27ae60', '#f39c12', '#e74c3c']
        
        bars = ax.bar(scenarios, times, color=colors, alpha=0.8)
        
        for bar, time in zip(bars, times):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                   f'{time:.1f}s', ha='center', fontsize=11, fontweight='bold')
        
        ax.set_ylabel('Tempo para 100m (seg)' if lang=='pt' else 'Time per 100m (sec)', fontsize=12)
        title_city = 'Nova York' if lang=='pt' and city=='NY' else 'Los Angeles' if city=='LA' else 'New York'
        ax.set_title(f'{title_city}', fontsize=14, fontweight='bold')
        ax.set_ylim(0, max(times) * 1.2)
    
    fig.suptitle('Tempo Médio para Percorrer 100m' if lang=='pt' else 'Average Time to Travel 100m', 
                fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    folder = 'charts_v4_pt' if lang=='pt' else 'charts_v4_en'
    plt.savefig(f'{folder}/fig4_time_per_100m.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  -> {folder}/fig4_time_per_100m.png")

# ============================================================================
# FIGURA 5: Manhattan vs Outros
# ============================================================================
def fig5_manhattan_comparison(lang='en'):
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ny_df = df[df['city'] == 'NY']
    manhattan = ny_df[ny_df['is_manhattan'] == True]
    others = ny_df[ny_df['is_manhattan'] == False]
    
    categories = ['Manhattan', 'Outros' if lang=='pt' else 'Other NYC Areas']
    car_times = [manhattan['worst_car_direct_min'].mean(), others['worst_car_direct_min'].mean()]
    heli_times = [manhattan['worst_heli_total_min'].mean(), others['worst_heli_total_min'].mean()]
    
    x = np.arange(len(categories))
    width = 0.35
    
    ax.bar(x - width/2, car_times, width, label='Carro' if lang=='pt' else 'Car', color=COLORS['car'], alpha=0.8)
    ax.bar(x + width/2, heli_times, width, label='Helicóptero' if lang=='pt' else 'Helicopter', color=COLORS['heli'], alpha=0.8)
    
    ax.set_ylabel('Tempo (min)' if lang=='pt' else 'Time (min)', fontsize=12)
    ax.set_title('Manhattan vs Outras Áreas de NYC - Pior Cenário' if lang=='pt' else 'Manhattan vs Other NYC Areas - Worst Case', 
                fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend()
    
    # Economia
    for i, (car, heli) in enumerate(zip(car_times, heli_times)):
        savings = car - heli
        ax.annotate(f'Economia: {savings:.0f} min' if lang=='pt' else f'Savings: {savings:.0f} min', 
                   xy=(i, max(car, heli) + 5), ha='center', fontsize=10, color='green')
    
    plt.tight_layout()
    folder = 'charts_v4_pt' if lang=='pt' else 'charts_v4_en'
    plt.savefig(f'{folder}/fig5_manhattan_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  -> {folder}/fig5_manhattan_comparison.png")

# ============================================================================
# FIGURA 6: Resumo Estatístico
# ============================================================================
def fig6_summary_table(lang='en'):
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.axis('off')
    
    # Dados
    ny_df = df[df['city'] == 'NY']
    la_df = df[df['city'] == 'LA']
    
    if lang == 'pt':
        headers = ['Métrica', 'NY', 'LA']
        data = [
            ['Total ZIP Codes', str(len(ny_df)), str(len(la_df))],
            ['Manhattan ZIPs', str(ny_df['is_manhattan'].sum()), '-'],
            ['Tempo Carro (worst)', f"{ny_df['worst_car_direct_min'].mean():.0f} min", f"{la_df['worst_car_direct_min'].mean():.0f} min"],
            ['Tempo Heli (worst)', f"{ny_df['worst_heli_total_min'].mean():.0f} min", f"{la_df['worst_heli_total_min'].mean():.0f} min"],
            ['Economia (worst)', f"{ny_df['worst_savings_min'].mean():.0f} min", f"{la_df['worst_savings_min'].mean():.0f} min"],
            ['% com Vantagem Heli', f"{100*(ny_df['worst_savings_min'] > 0).mean():.0f}%", f"{100*(la_df['worst_savings_min'] > 0).mean():.0f}%"],
            ['Velocidade (worst)', f"{ny_df['speed_to_airport_worst_kmh'].mean():.1f} km/h", f"{la_df['speed_to_airport_worst_kmh'].mean():.1f} km/h"],
            ['Tempo/100m (worst)', f"{100/(ny_df['speed_to_airport_worst_kmh'].mean()*1000/3600):.1f}s", f"{100/(la_df['speed_to_airport_worst_kmh'].mean()*1000/3600):.1f}s"],
            ['Multiplicador Rush', '1.68x', '1.68x'],
            ['Multiplicador Worst', '4.68x', '4.68x'],
        ]
    else:
        headers = ['Metric', 'NY', 'LA']
        data = [
            ['Total ZIP Codes', str(len(ny_df)), str(len(la_df))],
            ['Manhattan ZIPs', str(ny_df['is_manhattan'].sum()), '-'],
            ['Car Time (worst)', f"{ny_df['worst_car_direct_min'].mean():.0f} min", f"{la_df['worst_car_direct_min'].mean():.0f} min"],
            ['Heli Time (worst)', f"{ny_df['worst_heli_total_min'].mean():.0f} min", f"{la_df['worst_heli_total_min'].mean():.0f} min"],
            ['Savings (worst)', f"{ny_df['worst_savings_min'].mean():.0f} min", f"{la_df['worst_savings_min'].mean():.0f} min"],
            ['% with Heli Advantage', f"{100*(ny_df['worst_savings_min'] > 0).mean():.0f}%", f"{100*(la_df['worst_savings_min'] > 0).mean():.0f}%"],
            ['Speed (worst)', f"{ny_df['speed_to_airport_worst_kmh'].mean():.1f} km/h", f"{la_df['speed_to_airport_worst_kmh'].mean():.1f} km/h"],
            ['Time/100m (worst)', f"{100/(ny_df['speed_to_airport_worst_kmh'].mean()*1000/3600):.1f}s", f"{100/(la_df['speed_to_airport_worst_kmh'].mean()*1000/3600):.1f}s"],
            ['Rush Multiplier', '1.68x', '1.68x'],
            ['Worst Multiplier', '4.68x', '4.68x'],
        ]
    
    table = ax.table(cellText=data, colLabels=headers, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1.2, 2)
    
    # Estilização
    for i in range(len(headers)):
        table[(0, i)].set_facecolor('#3498db')
        table[(0, i)].set_text_props(color='white', fontweight='bold')
    
    for i in range(1, len(data) + 1):
        for j in range(len(headers)):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#f8f9fa')
    
    title = 'Resumo Estatístico - Cenário Pessimista' if lang=='pt' else 'Statistical Summary - Pessimistic Scenario'
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    
    plt.tight_layout()
    folder = 'charts_v4_pt' if lang=='pt' else 'charts_v4_en'
    plt.savefig(f'{folder}/fig6_summary_table.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  -> {folder}/fig6_summary_table.png")

# ============================================================================
# FIGURA 7: Distribuição de Economia
# ============================================================================
def fig7_savings_distribution(lang='en'):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    for idx, city in enumerate(['NY', 'LA']):
        ax = axes[idx]
        city_df = df[df['city'] == city]
        savings = city_df['worst_savings_min'].dropna()
        
        ax.hist(savings, bins=20, color=COLORS['savings'], alpha=0.7, edgecolor='black')
        ax.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Zero')
        ax.axvline(x=savings.mean(), color='blue', linestyle='-', linewidth=2, label=f'Média: {savings.mean():.0f} min')
        
        ax.set_xlabel('Economia (min)' if lang=='pt' else 'Savings (min)', fontsize=12)
        ax.set_ylabel('Frequência' if lang=='pt' else 'Frequency', fontsize=12)
        title_city = 'Nova York' if lang=='pt' and city=='NY' else 'Los Angeles' if city=='LA' else 'New York'
        ax.set_title(f'{title_city}', fontsize=14, fontweight='bold')
        ax.legend()
    
    fig.suptitle('Distribuição de Economia de Tempo - Pior Cenário' if lang=='pt' else 'Time Savings Distribution - Worst Case', 
                fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    folder = 'charts_v4_pt' if lang=='pt' else 'charts_v4_en'
    plt.savefig(f'{folder}/fig7_savings_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  -> {folder}/fig7_savings_distribution.png")

# ============================================================================
# EXECUTAR
# ============================================================================
if __name__ == "__main__":
    print("Gerando gráficos V4 - Cenário Pessimista...")
    
    for lang in ['en', 'pt']:
        print(f"\n[{lang.upper()}]")
        fig1_comparison(lang)
        fig2_savings_boxplot(lang)
        fig3_speed_comparison(lang)
        fig4_time_per_100m(lang)
        fig5_manhattan_comparison(lang)
        fig6_summary_table(lang)
        fig7_savings_distribution(lang)
    
    print("\n✓ Todos os gráficos gerados!")

