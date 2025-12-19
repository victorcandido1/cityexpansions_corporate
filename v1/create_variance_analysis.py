#!/usr/bin/env python3
"""
Variance Analysis of Travel Times by ZIP Code
Analyzes the dispersion and variability of travel times across cities and regions
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Create output directories
os.makedirs('variance_charts_en', exist_ok=True)
os.makedirs('variance_charts_pt', exist_ok=True)

# Load data
df = pd.read_csv('analysis_v4_pessimistic.csv')

print(f"Total ZIP codes: {len(df)}")
print(f"NY ZIP codes: {len(df[df['city'] == 'NY'])}")
print(f"LA ZIP codes: {len(df[df['city'] == 'LA'])}")

# Define regions for NY
def assign_ny_region(row):
    if row['city'] != 'NY':
        return None
    if row['is_manhattan']:
        return 'Manhattan'
    lat, lon = row['origin_lat'], row['origin_lon']
    # Brooklyn
    if 40.57 < lat < 40.74 and -74.05 < lon < -73.83:
        return 'Brooklyn'
    # Long Island
    if lon > -73.7:
        return 'Long Island'
    # New Jersey
    if lon < -74.0:
        return 'New Jersey'
    # Queens/Bronx
    if lat > 40.7 and lon > -74.0:
        return 'Queens/Bronx'
    return 'Other NY'

# Define regions for LA
def assign_la_region(row):
    if row['city'] != 'LA':
        return None
    lat, lon = row['origin_lat'], row['origin_lon']
    # Beverly Hills / West LA
    if 34.0 < lat < 34.15 and -118.5 < lon < -118.35:
        return 'Beverly Hills/West LA'
    # Santa Monica / Malibu
    if lon < -118.5:
        return 'Malibu/Santa Monica'
    # Orange County (south of 33.9)
    if lat < 33.9:
        return 'Orange County'
    # Pasadena area
    if lat > 34.1 and lon > -118.3:
        return 'Pasadena'
    return 'Central LA'

df['region'] = df.apply(lambda row: assign_ny_region(row) if row['city'] == 'NY' else assign_la_region(row), axis=1)

# Calculate variance statistics
def calculate_stats(data, column):
    return {
        'mean': data[column].mean(),
        'std': data[column].std(),
        'var': data[column].var(),
        'cv': (data[column].std() / data[column].mean()) * 100 if data[column].mean() != 0 else 0,
        'min': data[column].min(),
        'max': data[column].max(),
        'range': data[column].max() - data[column].min()
    }

# Scenarios to analyze
scenarios = {
    'fast': ('fast_car_direct_min', 'fast_heli_total_min', 'fast_savings_min'),
    'normal': ('normal_car_direct_min', 'normal_heli_total_min', 'normal_savings_min'),
    'rush': ('rush_car_direct_min', 'rush_heli_total_min', 'rush_savings_min'),
    'worst': ('worst_car_direct_min', 'worst_heli_total_min', 'worst_savings_min')
}

# Calculate variance by city and scenario
print("\n" + "="*80)
print("VARIANCE ANALYSIS BY CITY")
print("="*80)

variance_data = []
for city in ['NY', 'LA']:
    city_data = df[df['city'] == city]
    for scenario_name, (car_col, heli_col, savings_col) in scenarios.items():
        car_stats = calculate_stats(city_data, car_col)
        heli_stats = calculate_stats(city_data, heli_col)
        savings_stats = calculate_stats(city_data, savings_col)
        
        variance_data.append({
            'city': city,
            'scenario': scenario_name,
            'car_mean': car_stats['mean'],
            'car_std': car_stats['std'],
            'car_var': car_stats['var'],
            'car_cv': car_stats['cv'],
            'heli_mean': heli_stats['mean'],
            'heli_std': heli_stats['std'],
            'heli_var': heli_stats['var'],
            'heli_cv': heli_stats['cv'],
            'savings_mean': savings_stats['mean'],
            'savings_std': savings_stats['std'],
            'savings_var': savings_stats['var'],
            'savings_cv': savings_stats['cv']
        })
        
        print(f"\n{city} - {scenario_name.upper()}:")
        print(f"  Car:     Mean={car_stats['mean']:.1f} min, Std={car_stats['std']:.1f}, CV={car_stats['cv']:.1f}%")
        print(f"  Heli:    Mean={heli_stats['mean']:.1f} min, Std={heli_stats['std']:.1f}, CV={heli_stats['cv']:.1f}%")
        print(f"  Savings: Mean={savings_stats['mean']:.1f} min, Std={savings_stats['std']:.1f}, CV={savings_stats['cv']:.1f}%")

variance_df = pd.DataFrame(variance_data)
variance_df.to_csv('variance_analysis_summary.csv', index=False)
print("\nSaved: variance_analysis_summary.csv")

# Regional variance analysis
print("\n" + "="*80)
print("VARIANCE ANALYSIS BY REGION (WORST CASE)")
print("="*80)

regional_variance = []
for city in ['NY', 'LA']:
    city_data = df[df['city'] == city]
    regions = city_data['region'].dropna().unique()
    for region in regions:
        region_data = city_data[city_data['region'] == region]
        if len(region_data) >= 2:  # Need at least 2 for variance
            stats = calculate_stats(region_data, 'worst_car_direct_min')
            savings_stats = calculate_stats(region_data, 'worst_savings_min')
            regional_variance.append({
                'city': city,
                'region': region,
                'n': len(region_data),
                'car_mean': stats['mean'],
                'car_std': stats['std'],
                'car_cv': stats['cv'],
                'savings_mean': savings_stats['mean'],
                'savings_std': savings_stats['std'],
                'savings_cv': savings_stats['cv']
            })
            print(f"\n{city} - {region} (n={len(region_data)}):")
            print(f"  Car time:  Mean={stats['mean']:.1f} min, Std={stats['std']:.1f}, CV={stats['cv']:.1f}%")
            print(f"  Savings:   Mean={savings_stats['mean']:.1f} min, Std={savings_stats['std']:.1f}, CV={savings_stats['cv']:.1f}%")

regional_variance_df = pd.DataFrame(regional_variance)
regional_variance_df.to_csv('regional_variance_summary.csv', index=False)

# ============================================================================
# CHARTS - ENGLISH VERSION
# ============================================================================

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10

# Chart 1: Variance comparison by scenario (bar chart)
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

for idx, city in enumerate(['NY', 'LA']):
    ax = axes[idx]
    city_var = variance_df[variance_df['city'] == city]
    
    scenarios_list = ['fast', 'normal', 'rush', 'worst']
    x = np.arange(len(scenarios_list))
    width = 0.35
    
    car_std = city_var.set_index('scenario').loc[scenarios_list, 'car_std'].values
    heli_std = city_var.set_index('scenario').loc[scenarios_list, 'heli_std'].values
    
    bars1 = ax.bar(x - width/2, car_std, width, label='Car', color='#e74c3c', alpha=0.8)
    bars2 = ax.bar(x + width/2, heli_std, width, label='Helicopter', color='#27ae60', alpha=0.8)
    
    ax.set_xlabel('Traffic Scenario')
    ax.set_ylabel('Standard Deviation (minutes)')
    ax.set_title(f'{city}: Travel Time Variability by Scenario')
    ax.set_xticks(x)
    ax.set_xticklabels(['Fast', 'Normal', 'Rush', 'Worst'])
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{bar.get_height():.1f}', ha='center', fontsize=9)
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{bar.get_height():.1f}', ha='center', fontsize=9)

plt.tight_layout()
plt.savefig('variance_charts_en/fig1_std_by_scenario.png', dpi=150, bbox_inches='tight')
plt.close()
print("\n[OK] Created: variance_charts_en/fig1_std_by_scenario.png")

# Chart 2: Coefficient of Variation comparison
fig, ax = plt.subplots(figsize=(12, 6))

scenarios_list = ['fast', 'normal', 'rush', 'worst']
x = np.arange(len(scenarios_list))
width = 0.2

colors = {'NY_car': '#e74c3c', 'NY_heli': '#c0392b', 'LA_car': '#3498db', 'LA_heli': '#2980b9'}

for i, city in enumerate(['NY', 'LA']):
    city_var = variance_df[variance_df['city'] == city].set_index('scenario')
    car_cv = city_var.loc[scenarios_list, 'car_cv'].values
    heli_cv = city_var.loc[scenarios_list, 'heli_cv'].values
    
    offset = i * 2 * width - 1.5 * width
    ax.bar(x + offset, car_cv, width, label=f'{city} Car', color=colors[f'{city}_car'], alpha=0.8)
    ax.bar(x + offset + width, heli_cv, width, label=f'{city} Heli', color=colors[f'{city}_heli'], alpha=0.6)

ax.set_xlabel('Traffic Scenario')
ax.set_ylabel('Coefficient of Variation (%)')
ax.set_title('Travel Time Variability: Coefficient of Variation by City and Mode')
ax.set_xticks(x)
ax.set_xticklabels(['Fast', 'Normal', 'Rush', 'Worst'])
ax.legend()
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('variance_charts_en/fig2_cv_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("[OK] Created: variance_charts_en/fig2_cv_comparison.png")

# Chart 3: Box plots showing distribution with variance
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

for idx, (scenario_name, (car_col, heli_col, _)) in enumerate(scenarios.items()):
    ax = axes[idx // 2, idx % 2]
    
    ny_car = df[df['city'] == 'NY'][car_col]
    la_car = df[df['city'] == 'LA'][car_col]
    ny_heli = df[df['city'] == 'NY'][heli_col]
    la_heli = df[df['city'] == 'LA'][heli_col]
    
    data = [ny_car, ny_heli, la_car, la_heli]
    bp = ax.boxplot(data, patch_artist=True)
    
    colors = ['#e74c3c', '#27ae60', '#3498db', '#2ecc71']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax.set_xticklabels(['NY Car', 'NY Heli', 'LA Car', 'LA Heli'])
    ax.set_ylabel('Travel Time (minutes)')
    ax.set_title(f'{scenario_name.upper()} Scenario: Distribution & Variance')
    ax.grid(axis='y', alpha=0.3)
    
    # Add variance annotation
    for i, d in enumerate(data):
        ax.text(i + 1, d.max() + 5, f'σ={d.std():.1f}', ha='center', fontsize=8)

plt.tight_layout()
plt.savefig('variance_charts_en/fig3_boxplots_variance.png', dpi=150, bbox_inches='tight')
plt.close()
print("[OK] Created: variance_charts_en/fig3_boxplots_variance.png")

# Chart 4: Regional variance heatmap
fig, ax = plt.subplots(figsize=(12, 8))

# Prepare data for heatmap
if len(regional_variance_df) > 0:
    pivot_data = regional_variance_df.pivot_table(
        values='car_cv', index='region', columns='city', aggfunc='mean'
    ).fillna(0)
    
    im = ax.imshow(pivot_data.values, cmap='YlOrRd', aspect='auto')
    
    ax.set_xticks(range(len(pivot_data.columns)))
    ax.set_xticklabels(pivot_data.columns)
    ax.set_yticks(range(len(pivot_data.index)))
    ax.set_yticklabels(pivot_data.index)
    
    # Add value labels
    for i in range(len(pivot_data.index)):
        for j in range(len(pivot_data.columns)):
            val = pivot_data.values[i, j]
            if val > 0:
                ax.text(j, i, f'{val:.1f}%', ha='center', va='center', 
                       color='white' if val > 30 else 'black', fontsize=10)
    
    plt.colorbar(im, ax=ax, label='Coefficient of Variation (%)')
    ax.set_title('Regional Travel Time Variability (CV%) - Worst Case Scenario')

plt.tight_layout()
plt.savefig('variance_charts_en/fig4_regional_cv_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print("[OK] Created: variance_charts_en/fig4_regional_cv_heatmap.png")

# Chart 5: Scatter plot - Mean vs Standard Deviation
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

for idx, city in enumerate(['NY', 'LA']):
    ax = axes[idx]
    city_data = df[df['city'] == city]
    
    ax.scatter(city_data['worst_car_direct_min'], city_data['worst_savings_min'],
               c=city_data['worst_car_direct_min'], cmap='RdYlGn_r', s=100, alpha=0.7)
    
    ax.set_xlabel('Car Travel Time (minutes)')
    ax.set_ylabel('Time Savings (minutes)')
    ax.set_title(f'{city}: Travel Time vs Savings (Worst Case)')
    ax.grid(alpha=0.3)
    
    # Add trend line
    z = np.polyfit(city_data['worst_car_direct_min'], city_data['worst_savings_min'], 1)
    p = np.poly1d(z)
    x_line = np.linspace(city_data['worst_car_direct_min'].min(), city_data['worst_car_direct_min'].max(), 100)
    ax.plot(x_line, p(x_line), 'r--', alpha=0.8, label=f'Trend (R²={np.corrcoef(city_data["worst_car_direct_min"], city_data["worst_savings_min"])[0,1]**2:.2f})')
    ax.legend()

plt.tight_layout()
plt.savefig('variance_charts_en/fig5_scatter_mean_vs_savings.png', dpi=150, bbox_inches='tight')
plt.close()
print("[OK] Created: variance_charts_en/fig5_scatter_mean_vs_savings.png")

# Chart 6: Summary statistics table as image
fig, ax = plt.subplots(figsize=(14, 8))
ax.axis('off')

# Create summary table
table_data = []
for city in ['NY', 'LA']:
    city_data = df[df['city'] == city]
    for scenario in ['fast', 'worst']:
        car_col = f'{scenario}_car_direct_min'
        heli_col = f'{scenario}_heli_total_min'
        savings_col = f'{scenario}_savings_min'
        
        table_data.append([
            city, scenario.upper(),
            f"{city_data[car_col].mean():.1f}", f"{city_data[car_col].std():.1f}", f"{(city_data[car_col].std()/city_data[car_col].mean()*100):.1f}%",
            f"{city_data[heli_col].mean():.1f}", f"{city_data[heli_col].std():.1f}", f"{(city_data[heli_col].std()/city_data[heli_col].mean()*100):.1f}%",
            f"{city_data[savings_col].mean():.1f}", f"{city_data[savings_col].std():.1f}"
        ])

columns = ['City', 'Scenario', 'Car Mean', 'Car Std', 'Car CV', 'Heli Mean', 'Heli Std', 'Heli CV', 'Savings Mean', 'Savings Std']
table = ax.table(cellText=table_data, colLabels=columns, loc='center', cellLoc='center')
table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1.2, 2)

# Color header
for i in range(len(columns)):
    table[(0, i)].set_facecolor('#2c3e50')
    table[(0, i)].set_text_props(color='white', fontweight='bold')

ax.set_title('Variance Analysis Summary: Travel Time Statistics', fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('variance_charts_en/fig6_summary_table.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("[OK] Created: variance_charts_en/fig6_summary_table.png")

# ============================================================================
# CHARTS - PORTUGUESE VERSION
# ============================================================================

# Chart 1 PT
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

for idx, city in enumerate(['NY', 'LA']):
    ax = axes[idx]
    city_var = variance_df[variance_df['city'] == city]
    
    scenarios_list = ['fast', 'normal', 'rush', 'worst']
    x = np.arange(len(scenarios_list))
    width = 0.35
    
    car_std = city_var.set_index('scenario').loc[scenarios_list, 'car_std'].values
    heli_std = city_var.set_index('scenario').loc[scenarios_list, 'heli_std'].values
    
    bars1 = ax.bar(x - width/2, car_std, width, label='Carro', color='#e74c3c', alpha=0.8)
    bars2 = ax.bar(x + width/2, heli_std, width, label='Helicoptero', color='#27ae60', alpha=0.8)
    
    ax.set_xlabel('Cenario de Trafego')
    ax.set_ylabel('Desvio Padrao (minutos)')
    ax.set_title(f'{city}: Variabilidade do Tempo de Viagem por Cenario')
    ax.set_xticks(x)
    ax.set_xticklabels(['Rapido', 'Normal', 'Pico', 'Pior'])
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{bar.get_height():.1f}', ha='center', fontsize=9)
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{bar.get_height():.1f}', ha='center', fontsize=9)

plt.tight_layout()
plt.savefig('variance_charts_pt/fig1_std_by_scenario.png', dpi=150, bbox_inches='tight')
plt.close()
print("[OK] Created: variance_charts_pt/fig1_std_by_scenario.png")

# Chart 2 PT
fig, ax = plt.subplots(figsize=(12, 6))

colors_cv = {'NY_car': '#e74c3c', 'NY_heli': '#c0392b', 'LA_car': '#3498db', 'LA_heli': '#2980b9'}

for i, city in enumerate(['NY', 'LA']):
    city_var = variance_df[variance_df['city'] == city].set_index('scenario')
    car_cv = city_var.loc[scenarios_list, 'car_cv'].values
    heli_cv = city_var.loc[scenarios_list, 'heli_cv'].values
    
    offset = i * 2 * width - 1.5 * width
    ax.bar(x + offset, car_cv, width, label=f'{city} Carro', color=colors_cv[f'{city}_car'], alpha=0.8)
    ax.bar(x + offset + width, heli_cv, width, label=f'{city} Heli', color=colors_cv[f'{city}_heli'], alpha=0.6)

ax.set_xlabel('Cenario de Trafego')
ax.set_ylabel('Coeficiente de Variacao (%)')
ax.set_title('Variabilidade do Tempo de Viagem: Coeficiente de Variacao por Cidade e Modo')
ax.set_xticks(x)
ax.set_xticklabels(['Rapido', 'Normal', 'Pico', 'Pior'])
ax.legend()
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('variance_charts_pt/fig2_cv_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("[OK] Created: variance_charts_pt/fig2_cv_comparison.png")

# Chart 3 PT
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
scenario_names_pt = {'fast': 'RAPIDO', 'normal': 'NORMAL', 'rush': 'PICO', 'worst': 'PIOR CASO'}

for idx, (scenario_name, (car_col, heli_col, _)) in enumerate(scenarios.items()):
    ax = axes[idx // 2, idx % 2]
    
    ny_car = df[df['city'] == 'NY'][car_col]
    la_car = df[df['city'] == 'LA'][car_col]
    ny_heli = df[df['city'] == 'NY'][heli_col]
    la_heli = df[df['city'] == 'LA'][heli_col]
    
    data = [ny_car, ny_heli, la_car, la_heli]
    bp = ax.boxplot(data, patch_artist=True)
    
    colors_box = ['#e74c3c', '#27ae60', '#3498db', '#2ecc71']
    for patch, color in zip(bp['boxes'], colors_box):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax.set_xticklabels(['NY Carro', 'NY Heli', 'LA Carro', 'LA Heli'])
    ax.set_ylabel('Tempo de Viagem (minutos)')
    ax.set_title(f'Cenario {scenario_names_pt[scenario_name]}: Distribuicao & Variancia')
    ax.grid(axis='y', alpha=0.3)
    
    for i, d in enumerate(data):
        ax.text(i + 1, d.max() + 5, f'σ={d.std():.1f}', ha='center', fontsize=8)

plt.tight_layout()
plt.savefig('variance_charts_pt/fig3_boxplots_variance.png', dpi=150, bbox_inches='tight')
plt.close()
print("[OK] Created: variance_charts_pt/fig3_boxplots_variance.png")

# Chart 4 PT
fig, ax = plt.subplots(figsize=(12, 8))

if len(regional_variance_df) > 0:
    pivot_data = regional_variance_df.pivot_table(
        values='car_cv', index='region', columns='city', aggfunc='mean'
    ).fillna(0)
    
    im = ax.imshow(pivot_data.values, cmap='YlOrRd', aspect='auto')
    
    ax.set_xticks(range(len(pivot_data.columns)))
    ax.set_xticklabels(pivot_data.columns)
    ax.set_yticks(range(len(pivot_data.index)))
    ax.set_yticklabels(pivot_data.index)
    
    for i in range(len(pivot_data.index)):
        for j in range(len(pivot_data.columns)):
            val = pivot_data.values[i, j]
            if val > 0:
                ax.text(j, i, f'{val:.1f}%', ha='center', va='center', 
                       color='white' if val > 30 else 'black', fontsize=10)
    
    plt.colorbar(im, ax=ax, label='Coeficiente de Variacao (%)')
    ax.set_title('Variabilidade Regional do Tempo de Viagem (CV%) - Pior Cenario')

plt.tight_layout()
plt.savefig('variance_charts_pt/fig4_regional_cv_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print("[OK] Created: variance_charts_pt/fig4_regional_cv_heatmap.png")

# Chart 5 PT
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

for idx, city in enumerate(['NY', 'LA']):
    ax = axes[idx]
    city_data = df[df['city'] == city]
    
    ax.scatter(city_data['worst_car_direct_min'], city_data['worst_savings_min'],
               c=city_data['worst_car_direct_min'], cmap='RdYlGn_r', s=100, alpha=0.7)
    
    ax.set_xlabel('Tempo de Viagem de Carro (minutos)')
    ax.set_ylabel('Economia de Tempo (minutos)')
    ax.set_title(f'{city}: Tempo de Viagem vs Economia (Pior Caso)')
    ax.grid(alpha=0.3)
    
    z = np.polyfit(city_data['worst_car_direct_min'], city_data['worst_savings_min'], 1)
    p = np.poly1d(z)
    x_line = np.linspace(city_data['worst_car_direct_min'].min(), city_data['worst_car_direct_min'].max(), 100)
    ax.plot(x_line, p(x_line), 'r--', alpha=0.8, label=f'Tendencia (R²={np.corrcoef(city_data["worst_car_direct_min"], city_data["worst_savings_min"])[0,1]**2:.2f})')
    ax.legend()

plt.tight_layout()
plt.savefig('variance_charts_pt/fig5_scatter_mean_vs_savings.png', dpi=150, bbox_inches='tight')
plt.close()
print("[OK] Created: variance_charts_pt/fig5_scatter_mean_vs_savings.png")

# Chart 6 PT
fig, ax = plt.subplots(figsize=(14, 8))
ax.axis('off')

table_data = []
for city in ['NY', 'LA']:
    city_data = df[df['city'] == city]
    for scenario in ['fast', 'worst']:
        car_col = f'{scenario}_car_direct_min'
        heli_col = f'{scenario}_heli_total_min'
        savings_col = f'{scenario}_savings_min'
        scenario_pt = 'RAPIDO' if scenario == 'fast' else 'PIOR'
        
        table_data.append([
            city, scenario_pt,
            f"{city_data[car_col].mean():.1f}", f"{city_data[car_col].std():.1f}", f"{(city_data[car_col].std()/city_data[car_col].mean()*100):.1f}%",
            f"{city_data[heli_col].mean():.1f}", f"{city_data[heli_col].std():.1f}", f"{(city_data[heli_col].std()/city_data[heli_col].mean()*100):.1f}%",
            f"{city_data[savings_col].mean():.1f}", f"{city_data[savings_col].std():.1f}"
        ])

columns = ['Cidade', 'Cenario', 'Carro Med', 'Carro DP', 'Carro CV', 'Heli Med', 'Heli DP', 'Heli CV', 'Econ Med', 'Econ DP']
table = ax.table(cellText=table_data, colLabels=columns, loc='center', cellLoc='center')
table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1.2, 2)

for i in range(len(columns)):
    table[(0, i)].set_facecolor('#2c3e50')
    table[(0, i)].set_text_props(color='white', fontweight='bold')

ax.set_title('Resumo da Analise de Variancia: Estatisticas de Tempo de Viagem', fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('variance_charts_pt/fig6_summary_table.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("[OK] Created: variance_charts_pt/fig6_summary_table.png")

print("\n" + "="*80)
print("KEY FINDINGS")
print("="*80)
print(f"""
1. CAR TRAVEL TIME VARIANCE:
   - NY Worst Case: Mean={df[df['city']=='NY']['worst_car_direct_min'].mean():.1f} min, Std={df[df['city']=='NY']['worst_car_direct_min'].std():.1f} min
   - LA Worst Case: Mean={df[df['city']=='LA']['worst_car_direct_min'].mean():.1f} min, Std={df[df['city']=='LA']['worst_car_direct_min'].std():.1f} min

2. HELICOPTER TIME VARIANCE (MUCH LOWER):
   - NY Worst Case: Mean={df[df['city']=='NY']['worst_heli_total_min'].mean():.1f} min, Std={df[df['city']=='NY']['worst_heli_total_min'].std():.1f} min
   - LA Worst Case: Mean={df[df['city']=='LA']['worst_heli_total_min'].mean():.1f} min, Std={df[df['city']=='LA']['worst_heli_total_min'].std():.1f} min

3. KEY INSIGHT:
   - Car travel has {df['worst_car_direct_min'].std()/df['worst_heli_total_min'].std():.1f}x higher variance than helicopter
   - This means helicopter provides more PREDICTABLE travel times
   - Higher variance in car = higher risk of being late
""")

print("\nAll charts created successfully!")

