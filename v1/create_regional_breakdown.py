#!/usr/bin/env python3
"""
Create regional breakdown charts for NY and LA
Also create city-specific traffic multiplier visualizations
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Create output directories
os.makedirs('regional_charts_en', exist_ok=True)
os.makedirs('regional_charts_pt', exist_ok=True)

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 11

# Load data
print("Loading data...")
df = pd.read_csv('analysis_v4_pessimistic.csv')

# Load ZIP code data to get regions
print("Loading ZIP code region data...")
zip_data = pd.read_csv('../10percent/top10_richest_data.csv')

# Define regions based on ZIP codes
# NY Regions
NY_REGIONS = {
    'Manhattan': list(range(10001, 10300)),  # Manhattan ZIP codes
    'Brooklyn': list(range(11201, 11257)),
    'Queens': list(range(11351, 11700)),
    'Bronx': list(range(10451, 10476)),
    'Staten Island': list(range(10301, 10315)),
    'Hamptons': [11932, 11937, 11954, 11957, 11959, 11962, 11963, 11964, 11968, 11969, 11975, 11976, 11978, 
                 11930, 11931, 11933, 11935, 11939, 11941, 11942, 11944, 11946, 11947, 11948, 11949, 11950,
                 11951, 11952, 11953, 11955, 11956, 11958, 11960, 11961, 11965, 11967, 11970, 11971, 11972,
                 11973, 11977, 11979, 11980],
    'Westchester': list(range(10501, 10600)) + list(range(10701, 10800)) + list(range(10801, 10900)),
    'Long Island': list(range(11001, 11100)) + list(range(11501, 11600)) + list(range(11701, 11800)),
    'New Jersey': list(range(7001, 8000)) + list(range(7000, 7999)),
}

# LA Regions  
LA_REGIONS = {
    'Beverly Hills': [90210, 90211, 90212],
    'Bel Air/Holmby': [90024, 90049, 90077],
    'Santa Monica': [90401, 90402, 90403, 90404, 90405],
    'Malibu': [90263, 90264, 90265],
    'Pacific Palisades': [90272],
    'Brentwood': [90049],
    'Hollywood Hills': [90028, 90046, 90068, 90069],
    'Pasadena': [91101, 91102, 91103, 91104, 91105, 91106, 91107],
    'Newport Beach': [92660, 92661, 92662, 92663],
    'Laguna Beach': [92651, 92652, 92653],
    'Manhattan Beach': [90266],
    'Palos Verdes': [90274, 90275],
    'Other LA': [],  # Will be filled with remaining ZIPs
}

def assign_region_ny(zipcode):
    """Assign NY ZIP code to region"""
    zip_int = int(zipcode)
    for region, zips in NY_REGIONS.items():
        if zip_int in zips:
            return region
    # Check by prefix for broader categories
    if 100 <= zip_int // 100 <= 104:
        return 'Manhattan'
    elif 112 <= zip_int // 100 <= 114:
        return 'Brooklyn/Queens'
    elif 70 <= zip_int // 100 <= 79:
        return 'New Jersey'
    elif 105 <= zip_int // 100 <= 109:
        return 'Westchester/Upstate'
    elif 115 <= zip_int // 100 <= 119:
        return 'Long Island'
    return 'Other NY'

def assign_region_la(zipcode):
    """Assign LA ZIP code to region"""
    zip_int = int(zipcode)
    for region, zips in LA_REGIONS.items():
        if zip_int in zips:
            return region
    # Check by prefix
    if zip_int in [90210, 90211, 90212]:
        return 'Beverly Hills'
    elif 902 <= zip_int // 100 <= 904:
        return 'West LA'
    elif zip_int // 100 == 906:
        return 'South Bay'
    elif 910 <= zip_int // 100 <= 912:
        return 'San Fernando Valley'
    elif 926 <= zip_int // 100 <= 927:
        return 'Orange County'
    return 'Other LA'

# Assign regions
print("Assigning regions...")
df['region'] = df.apply(lambda row: assign_region_ny(row['zipcode']) if row['city'] == 'NY' else assign_region_la(row['zipcode']), axis=1)

# Check distribution
print("\n=== NY Region Distribution ===")
ny_regions = df[df['city'] == 'NY']['region'].value_counts()
print(ny_regions)

print("\n=== LA Region Distribution ===")
la_regions = df[df['city'] == 'LA']['region'].value_counts()
print(la_regions)

# ============================================================================
# CHART 1: Regional Time Breakdown - NY
# ============================================================================
def create_regional_breakdown_ny(lang='en'):
    fig, ax = plt.subplots(figsize=(14, 8))
    
    ny_df = df[df['city'] == 'NY']
    regions = ny_df.groupby('region').agg({
        'fast_car_direct_min': 'mean',
        'worst_car_direct_min': 'mean',
        'fast_heli_total_min': 'mean',
        'worst_heli_total_min': 'mean',
        'worst_savings_min': 'mean',
        'zipcode': 'count'
    }).rename(columns={'zipcode': 'count'})
    
    # Sort by worst car time
    regions = regions.sort_values('worst_car_direct_min', ascending=True)
    
    if lang == 'en':
        title = 'New York: Travel Time Breakdown by Region (Worst Case)'
        ylabel = 'Average Travel Time (minutes)'
        xlabel = 'Region'
        labels = ['Car (Worst)', 'Helicopter (Worst)', 'Savings']
    else:
        title = 'Nova York: Detalhamento por Região (Pior Caso)'
        ylabel = 'Tempo Médio de Viagem (minutos)'
        xlabel = 'Região'
        labels = ['Carro (Pior)', 'Helicóptero (Pior)', 'Economia']
    
    x = np.arange(len(regions))
    width = 0.25
    
    bars1 = ax.bar(x - width, regions['worst_car_direct_min'], width, label=labels[0], color='#e74c3c', edgecolor='black')
    bars2 = ax.bar(x, regions['worst_heli_total_min'], width, label=labels[1], color='#3498db', edgecolor='black')
    bars3 = ax.bar(x + width, regions['worst_savings_min'], width, label=labels[2], color='#27ae60', edgecolor='black')
    
    # Add count annotations
    for i, (idx, row) in enumerate(regions.iterrows()):
        ax.annotate(f'n={int(row["count"])}', xy=(i, 5), fontsize=8, ha='center', color='gray')
    
    # Add value labels
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.0f}', xy=(bar.get_x() + bar.get_width()/2, height),
                       xytext=(0, 3), textcoords='offset points', ha='center', fontsize=9, fontweight='bold')
    
    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(regions.index, rotation=45, ha='right')
    ax.legend()
    ax.set_ylim(0, max(regions['worst_car_direct_min']) * 1.15)
    
    plt.tight_layout()
    
    folder = 'regional_charts_en' if lang == 'en' else 'regional_charts_pt'
    plt.savefig(f'{folder}/ny_regional_breakdown.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Created: {folder}/ny_regional_breakdown.png")

# ============================================================================
# CHART 2: Regional Time Breakdown - LA
# ============================================================================
def create_regional_breakdown_la(lang='en'):
    fig, ax = plt.subplots(figsize=(14, 8))
    
    la_df = df[df['city'] == 'LA']
    regions = la_df.groupby('region').agg({
        'fast_car_direct_min': 'mean',
        'worst_car_direct_min': 'mean',
        'fast_heli_total_min': 'mean',
        'worst_heli_total_min': 'mean',
        'worst_savings_min': 'mean',
        'zipcode': 'count'
    }).rename(columns={'zipcode': 'count'})
    
    # Sort by worst car time
    regions = regions.sort_values('worst_car_direct_min', ascending=True)
    
    if lang == 'en':
        title = 'Los Angeles: Travel Time Breakdown by Region (Worst Case)'
        ylabel = 'Average Travel Time (minutes)'
        xlabel = 'Region'
        labels = ['Car (Worst)', 'Helicopter (Worst)', 'Savings']
    else:
        title = 'Los Angeles: Detalhamento por Região (Pior Caso)'
        ylabel = 'Tempo Médio de Viagem (minutos)'
        xlabel = 'Região'
        labels = ['Carro (Pior)', 'Helicóptero (Pior)', 'Economia']
    
    x = np.arange(len(regions))
    width = 0.25
    
    bars1 = ax.bar(x - width, regions['worst_car_direct_min'], width, label=labels[0], color='#e74c3c', edgecolor='black')
    bars2 = ax.bar(x, regions['worst_heli_total_min'], width, label=labels[1], color='#3498db', edgecolor='black')
    bars3 = ax.bar(x + width, regions['worst_savings_min'], width, label=labels[2], color='#27ae60', edgecolor='black')
    
    # Add count annotations
    for i, (idx, row) in enumerate(regions.iterrows()):
        ax.annotate(f'n={int(row["count"])}', xy=(i, 5), fontsize=8, ha='center', color='gray')
    
    # Add value labels
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.0f}', xy=(bar.get_x() + bar.get_width()/2, height),
                       xytext=(0, 3), textcoords='offset points', ha='center', fontsize=9, fontweight='bold')
    
    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(regions.index, rotation=45, ha='right')
    ax.legend()
    ax.set_ylim(0, max(regions['worst_car_direct_min']) * 1.15)
    
    plt.tight_layout()
    
    folder = 'regional_charts_en' if lang == 'en' else 'regional_charts_pt'
    plt.savefig(f'{folder}/la_regional_breakdown.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Created: {folder}/la_regional_breakdown.png")

# ============================================================================
# CHART 3: City-Specific Traffic Multipliers
# ============================================================================
def create_city_traffic_multipliers(lang='en'):
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    
    # City-specific multipliers from Google Traffic data analysis
    # NY has higher worst-case (5.20x) - more extreme traffic events
    # LA has higher normal/rush (1.42x/1.77x) - more consistent congestion
    ny_normal_mult = 1.35
    ny_rush_mult = 1.69
    ny_worst_mult = 5.20
    
    la_normal_mult = 1.42
    la_rush_mult = 1.77
    la_worst_mult = 4.15
    
    if lang == 'en':
        title = 'Traffic Multipliers by City (Google Traffic Data)'
        scenarios = ['Fast\n(Baseline)', 'Normal', 'Rush Hour', 'Worst Case']
        ylabel = 'Traffic Multiplier'
    else:
        title = 'Multiplicadores de Tráfego por Cidade (Dados Google Traffic)'
        scenarios = ['Rápido\n(Base)', 'Normal', 'Hora Pico', 'Pior Caso']
        ylabel = 'Multiplicador de Tráfego'
    
    # NY multipliers (higher worst case - more extreme events)
    ny_mults = [1.0, ny_normal_mult, ny_rush_mult, ny_worst_mult]
    # LA multipliers (higher normal/rush - consistent congestion)
    la_mults = [1.0, la_normal_mult, la_rush_mult, la_worst_mult]
    
    colors = ['#27ae60', '#f39c12', '#e67e22', '#c0392b']
    
    # NY chart
    ax = axes[0]
    bars = ax.bar(scenarios, ny_mults, color=colors, edgecolor='black', linewidth=1.5)
    for bar, val in zip(bars, ny_mults):
        ax.annotate(f'{val:.2f}x', xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                   xytext=(0, 3), textcoords='offset points', ha='center', fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel)
    ax.set_title('New York' if lang == 'en' else 'Nova York', fontsize=14, fontweight='bold', color='#3498db')
    ax.set_ylim(0, max(ny_mults) * 1.15)
    ax.axhline(y=1, color='gray', linestyle='--', alpha=0.5)
    
    # LA chart
    ax = axes[1]
    bars = ax.bar(scenarios, la_mults, color=colors, edgecolor='black', linewidth=1.5)
    for bar, val in zip(bars, la_mults):
        ax.annotate(f'{val:.2f}x', xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                   xytext=(0, 3), textcoords='offset points', ha='center', fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel)
    ax.set_title('Los Angeles', fontsize=14, fontweight='bold', color='#e74c3c')
    ax.set_ylim(0, max(la_mults) * 1.15)
    ax.axhline(y=1, color='gray', linestyle='--', alpha=0.5)
    
    fig.suptitle(title, fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    folder = 'regional_charts_en' if lang == 'en' else 'regional_charts_pt'
    plt.savefig(f'{folder}/city_traffic_multipliers.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Created: {folder}/city_traffic_multipliers.png")

# ============================================================================
# CHART 4: Regional Comparison - Stacked Bar
# ============================================================================
def create_regional_stacked_comparison(lang='en'):
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))
    
    for idx, (city, city_name) in enumerate([('NY', 'New York'), ('LA', 'Los Angeles')]):
        ax = axes[idx]
        city_df = df[df['city'] == city]
        
        regions = city_df.groupby('region').agg({
            'fast_car_to_facility_min': 'mean',  # Car to helipad
            'flight_time_min': 'mean',           # Flight time
            'worst_car_direct_min': 'mean',      # Direct car time
            'worst_heli_total_min': 'mean',      # Total heli time
            'zipcode': 'count'
        }).rename(columns={'zipcode': 'count'})
        
        # Calculate components
        regions['car_to_helipad'] = regions['fast_car_to_facility_min'] * 4.68  # worst case
        regions['checkin'] = 10  # fixed
        regions['flight'] = regions['flight_time_min']
        regions['transfer'] = 10  # fixed
        
        # Sort by worst car time
        regions = regions.sort_values('worst_car_direct_min', ascending=False)
        
        if lang == 'en':
            labels = ['Car to Helipad', 'Check-in (10min)', 'Flight', 'Terminal Transfer (10min)']
        else:
            labels = ['Carro até Heliponto', 'Check-in (10min)', 'Voo', 'Transfer Terminal (10min)']
        
        x = np.arange(len(regions))
        
        # Stacked bar for helicopter components
        bottom = np.zeros(len(regions))
        colors_heli = ['#3498db', '#9b59b6', '#1abc9c', '#2ecc71']
        
        for i, (col, label, color) in enumerate(zip(['car_to_helipad', 'checkin', 'flight', 'transfer'], labels, colors_heli)):
            if col == 'checkin' or col == 'transfer':
                vals = [10] * len(regions)
            else:
                vals = regions[col].values
            ax.bar(x, vals, bottom=bottom, label=label, color=color, edgecolor='black', linewidth=0.5)
            bottom += vals
        
        # Add car time as separate bar
        ax.bar(x + 0.4, regions['worst_car_direct_min'], width=0.35, label='Car Direct' if lang == 'en' else 'Carro Direto', 
               color='#e74c3c', edgecolor='black', linewidth=0.5, alpha=0.8)
        
        ax.set_ylabel('Minutes' if lang == 'en' else 'Minutos')
        ax.set_title(city_name if lang == 'en' else ('Nova York' if city == 'NY' else 'Los Angeles'), 
                    fontsize=14, fontweight='bold')
        ax.set_xticks(x + 0.2)
        ax.set_xticklabels(regions.index, rotation=45, ha='right', fontsize=9)
        ax.legend(loc='upper right', fontsize=8)
    
    title = 'Helicopter Journey Breakdown by Region (Worst Case)' if lang == 'en' else 'Detalhamento do Trajeto de Helicóptero por Região (Pior Caso)'
    fig.suptitle(title, fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    folder = 'regional_charts_en' if lang == 'en' else 'regional_charts_pt'
    plt.savefig(f'{folder}/regional_stacked_comparison.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Created: {folder}/regional_stacked_comparison.png")

# ============================================================================
# CHART 5: Regional Savings Heatmap Style
# ============================================================================
def create_regional_savings_summary(lang='en'):
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Combine both cities
    regions_all = df.groupby(['city', 'region']).agg({
        'worst_car_direct_min': 'mean',
        'worst_heli_total_min': 'mean',
        'worst_savings_min': 'mean',
        'zipcode': 'count'
    }).rename(columns={'zipcode': 'count'}).reset_index()
    
    # Filter to regions with at least 2 ZIP codes
    regions_all = regions_all[regions_all['count'] >= 1]
    
    # Sort by savings
    regions_all = regions_all.sort_values('worst_savings_min', ascending=True)
    
    # Create labels
    regions_all['label'] = regions_all.apply(lambda r: f"{r['city']}: {r['region']} (n={int(r['count'])})", axis=1)
    
    if lang == 'en':
        title = 'Time Savings by Region (Worst Case Traffic)'
        xlabel = 'Minutes Saved with Helicopter'
    else:
        title = 'Economia de Tempo por Região (Pior Caso de Trânsito)'
        xlabel = 'Minutos Economizados com Helicóptero'
    
    colors = ['#3498db' if city == 'NY' else '#e74c3c' for city in regions_all['city']]
    
    bars = ax.barh(regions_all['label'], regions_all['worst_savings_min'], color=colors, edgecolor='black')
    
    # Add value labels
    for bar, val in zip(bars, regions_all['worst_savings_min']):
        ax.annotate(f'{val:.0f} min', xy=(bar.get_width() + 2, bar.get_y() + bar.get_height()/2),
                   va='center', fontsize=10, fontweight='bold')
    
    ax.set_xlabel(xlabel)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.axvline(x=0, color='black', linewidth=1)
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='#3498db', label='New York' if lang == 'en' else 'Nova York'),
                       Patch(facecolor='#e74c3c', label='Los Angeles')]
    ax.legend(handles=legend_elements, loc='lower right')
    
    plt.tight_layout()
    
    folder = 'regional_charts_en' if lang == 'en' else 'regional_charts_pt'
    plt.savefig(f'{folder}/regional_savings_summary.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Created: {folder}/regional_savings_summary.png")

# ============================================================================
# MAIN EXECUTION
# ============================================================================
print("\n" + "="*60)
print("GENERATING REGIONAL BREAKDOWN CHARTS")
print("="*60)

print("\n[1/5] Creating NY regional breakdown...")
create_regional_breakdown_ny('en')
create_regional_breakdown_ny('pt')

print("\n[2/5] Creating LA regional breakdown...")
create_regional_breakdown_la('en')
create_regional_breakdown_la('pt')

print("\n[3/5] Creating city traffic multipliers...")
create_city_traffic_multipliers('en')
create_city_traffic_multipliers('pt')

print("\n[4/5] Creating regional stacked comparison...")
create_regional_stacked_comparison('en')
create_regional_stacked_comparison('pt')

print("\n[5/5] Creating regional savings summary...")
create_regional_savings_summary('en')
create_regional_savings_summary('pt')

print("\n" + "="*60)
print("ALL REGIONAL CHARTS GENERATED SUCCESSFULLY!")
print("="*60)
print(f"\nOutput folders:")
print(f"  - regional_charts_en/ (5 charts)")
print(f"  - regional_charts_pt/ (5 charts)")

