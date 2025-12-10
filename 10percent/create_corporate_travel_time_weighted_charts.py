# -*- coding: utf-8 -*-
"""
CORPORATE TRAVEL TIME WEIGHTED BY REVENUE ANALYSIS
===================================================
Creates charts that weight corporate travel time to airports by:
1. Revenue per Employee
2. Total Revenue

This provides insights into which cities have the most economically significant
corporate presence relative to airport accessibility.

100% REAL DATA - U.S. Census Bureau 2021
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import os
import json

# =============================================================================
# CONFIGURATION
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Input files
CORPORATE_TOP10_FILE = os.path.join(BASE_DIR, 'top10_corporate_data.csv')
TRAVEL_TIMES_FILE = os.path.join(BASE_DIR, 'cache_corporate_travel_times.json')

# Output files
OUTPUT_CHART = os.path.join(BASE_DIR, 'corporate_travel_time_weighted_by_revenue.png')
OUTPUT_CSV = os.path.join(BASE_DIR, 'corporate_travel_time_weighted_by_revenue.csv')

# City configurations
CITIES = {
    'los_angeles': {'name': 'Los Angeles', 'color': '#ff7f0e'},
    'new_york': {'name': 'New York', 'color': '#1f77b4'},
    'chicago': {'name': 'Chicago', 'color': '#2ca02c'},
    'dallas': {'name': 'Dallas', 'color': '#d62728'},
    'houston': {'name': 'Houston', 'color': '#9467bd'},
    'miami': {'name': 'Miami', 'color': '#8c564b'},
    'san_francisco': {'name': 'San Francisco', 'color': '#e377c2'},
}

CITY_COLORS = {k: v['color'] for k, v in CITIES.items()}

# =============================================================================
# MAIN ANALYSIS
# =============================================================================
def main():
    print("\n" + "="*80)
    print("CORPORATE TRAVEL TIME WEIGHTED BY REVENUE ANALYSIS")
    print("="*80)
    print("\n100% REAL DATA - U.S. Census Bureau CBP 2021\n")
    
    # Load corporate data
    print("Loading data...")
    df_corporate = pd.read_csv(CORPORATE_TOP10_FILE)
    print(f"  Corporate Top 10%: {len(df_corporate)} ZIP codes")
    
    # Load travel times
    with open(TRAVEL_TIMES_FILE, 'r') as f:
        travel_times = json.load(f)
    print(f"  Travel times: {len(travel_times)} ZIP codes\n")
    
    # Add travel times to corporate data
    df_corporate['travel_time_min'] = df_corporate['zipcode'].apply(
        lambda z: travel_times.get(str(z), np.nan)
    )
    
    # Calculate revenue per employee
    df_corporate['revenue_per_employee'] = (
        df_corporate['estimated_revenue_M'] * 1_000_000 / df_corporate['total_employment']
    ).replace([np.inf, -np.inf], np.nan)
    
    # Filter data with valid travel times
    df_valid = df_corporate[
        df_corporate['travel_time_min'].notna() &
        (df_corporate['travel_time_min'] > 0) &
        (df_corporate['total_employment'] > 0)
    ].copy()
    
    print(f"Valid data points: {len(df_valid)} ZIP codes\n")
    
    # Calculate weighted metrics by city
    city_stats = []
    
    for city_key, city_config in CITIES.items():
        city_name = city_config['name']
        city_data = df_valid[df_valid['city_key'] == city_key]
        
        if len(city_data) == 0:
            continue
        
        # Total metrics
        total_revenue_M = city_data['estimated_revenue_M'].sum()
        total_employment = city_data['total_employment'].sum()
        zip_count = len(city_data)
        
        # Simple averages
        mean_travel_time = city_data['travel_time_min'].mean()
        median_travel_time = city_data['travel_time_min'].median()
        mean_revenue_per_emp = city_data['revenue_per_employee'].mean()
        median_revenue_per_emp = city_data['revenue_per_employee'].median()
        
        # Weighted by Revenue per Employee
        # Give more weight to ZIPs with higher revenue per employee
        rev_per_emp_weights = city_data['revenue_per_employee']
        if rev_per_emp_weights.sum() > 0:
            weighted_time_by_rev_per_emp = (
                (city_data['travel_time_min'] * rev_per_emp_weights).sum() / 
                rev_per_emp_weights.sum()
            )
        else:
            weighted_time_by_rev_per_emp = np.nan
        
        # Weighted by Total Revenue
        # Give more weight to ZIPs with higher total revenue
        revenue_weights = city_data['estimated_revenue_M']
        if revenue_weights.sum() > 0:
            weighted_time_by_revenue = (
                (city_data['travel_time_min'] * revenue_weights).sum() / 
                revenue_weights.sum()
            )
        else:
            weighted_time_by_revenue = np.nan
        
        # Weighted by Employment
        # Give more weight to ZIPs with more employees
        employment_weights = city_data['total_employment']
        if employment_weights.sum() > 0:
            weighted_time_by_employment = (
                (city_data['travel_time_min'] * employment_weights).sum() / 
                employment_weights.sum()
            )
        else:
            weighted_time_by_employment = np.nan
        
        city_stats.append({
            'City': city_name,
            'city_key': city_key,
            'Top10_Zips': zip_count,
            'Total_Revenue_M': total_revenue_M,
            'Total_Employment': total_employment,
            'Revenue_per_Employee': total_revenue_M * 1_000_000 / total_employment if total_employment > 0 else np.nan,
            'Mean_Travel_Time_min': mean_travel_time,
            'Median_Travel_Time_min': median_travel_time,
            'Weighted_Time_by_RevPerEmp_min': weighted_time_by_rev_per_emp,
            'Weighted_Time_by_Revenue_min': weighted_time_by_revenue,
            'Weighted_Time_by_Employment_min': weighted_time_by_employment,
            'Mean_RevPerEmp': mean_revenue_per_emp,
            'Median_RevPerEmp': median_revenue_per_emp,
        })
    
    df_stats = pd.DataFrame(city_stats)
    df_stats = df_stats.sort_values('Total_Employment', ascending=False)
    
    # Save CSV
    df_stats.to_csv(OUTPUT_CSV, index=False, float_format='%.2f')
    print(f"[OK] Saved: {OUTPUT_CSV}\n")
    
    # Print summary
    print("="*80)
    print("SUMMARY BY CITY")
    print("="*80)
    for _, row in df_stats.iterrows():
        print(f"\n{row['City']}:")
        print(f"  ZIPs: {row['Top10_Zips']}")
        print(f"  Total Revenue: ${row['Total_Revenue_M']:,.0f}M")
        print(f"  Total Employment: {row['Total_Employment']:,.0f}")
        print(f"  Revenue per Employee: ${row['Revenue_per_Employee']:,.0f}")
        print(f"  Mean Travel Time: {row['Mean_Travel_Time_min']:.1f} min")
        print(f"  Weighted by Revenue/Employee: {row['Weighted_Time_by_RevPerEmp_min']:.1f} min")
        print(f"  Weighted by Total Revenue: {row['Weighted_Time_by_Revenue_min']:.1f} min")
        print(f"  Weighted by Employment: {row['Weighted_Time_by_Employment_min']:.1f} min")
    
    # Create visualization
    create_visualization(df_stats)
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print(f"\nGenerated files:")
    print(f"  - {OUTPUT_CSV}")
    print(f"  - {OUTPUT_CHART}")
    print()

# =============================================================================
# VISUALIZATION
# =============================================================================
def create_visualization(df_stats):
    """Create comprehensive visualization of weighted travel times."""
    
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
    
    cities = df_stats['City'].values
    colors = [CITY_COLORS.get(k, '#666666') for k in df_stats['city_key'].values]
    x_pos = np.arange(len(cities))
    
    # Chart 1: Travel Time Weighted by Revenue per Employee
    ax1 = fig.add_subplot(gs[0, 0])
    width = 0.35
    
    ax1.bar(x_pos - width/2, df_stats['Mean_Travel_Time_min'], width,
           label='Simple Mean', color='#cccccc', alpha=0.7)
    ax1.bar(x_pos + width/2, df_stats['Weighted_Time_by_RevPerEmp_min'], width,
           label='Weighted by Rev/Employee', color='#e74c3c', alpha=0.8)
    
    ax1.set_ylabel('Travel Time (minutes)', fontsize=11, fontweight='bold')
    ax1.set_title('Travel Time Weighted by Revenue per Employee', 
                 fontsize=12, fontweight='bold')
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(cities, rotation=45, ha='right')
    ax1.legend(fontsize=9)
    ax1.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for i, (mean_val, weighted_val) in enumerate(zip(
        df_stats['Mean_Travel_Time_min'], 
        df_stats['Weighted_Time_by_RevPerEmp_min']
    )):
        ax1.text(i - width/2, mean_val + 2, f'{mean_val:.0f}', 
                ha='center', va='bottom', fontsize=8)
        ax1.text(i + width/2, weighted_val + 2, f'{weighted_val:.0f}', 
                ha='center', va='bottom', fontsize=8, fontweight='bold')
    
    # Chart 2: Travel Time Weighted by Total Revenue
    ax2 = fig.add_subplot(gs[0, 1])
    
    ax2.bar(x_pos - width/2, df_stats['Mean_Travel_Time_min'], width,
           label='Simple Mean', color='#cccccc', alpha=0.7)
    ax2.bar(x_pos + width/2, df_stats['Weighted_Time_by_Revenue_min'], width,
           label='Weighted by Total Revenue', color='#3498db', alpha=0.8)
    
    ax2.set_ylabel('Travel Time (minutes)', fontsize=11, fontweight='bold')
    ax2.set_title('Travel Time Weighted by Total Revenue', 
                 fontsize=12, fontweight='bold')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(cities, rotation=45, ha='right')
    ax2.legend(fontsize=9)
    ax2.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for i, (mean_val, weighted_val) in enumerate(zip(
        df_stats['Mean_Travel_Time_min'], 
        df_stats['Weighted_Time_by_Revenue_min']
    )):
        ax2.text(i - width/2, mean_val + 2, f'{mean_val:.0f}', 
                ha='center', va='bottom', fontsize=8)
        ax2.text(i + width/2, weighted_val + 2, f'{weighted_val:.0f}', 
                ha='center', va='bottom', fontsize=8, fontweight='bold')
    
    # Chart 3: Comparison of All Weighting Methods
    ax3 = fig.add_subplot(gs[1, :])
    width = 0.2
    
    ax3.bar(x_pos - 1.5*width, df_stats['Mean_Travel_Time_min'], width,
           label='Simple Mean', color='#cccccc', alpha=0.7)
    ax3.bar(x_pos - 0.5*width, df_stats['Weighted_Time_by_RevPerEmp_min'], width,
           label='Weighted by Revenue/Employee', color='#e74c3c', alpha=0.8)
    ax3.bar(x_pos + 0.5*width, df_stats['Weighted_Time_by_Revenue_min'], width,
           label='Weighted by Total Revenue', color='#3498db', alpha=0.8)
    ax3.bar(x_pos + 1.5*width, df_stats['Weighted_Time_by_Employment_min'], width,
           label='Weighted by Employment', color='#2ecc71', alpha=0.8)
    
    ax3.set_ylabel('Travel Time (minutes)', fontsize=11, fontweight='bold')
    ax3.set_title('Comparison: All Weighting Methods', 
                 fontsize=13, fontweight='bold')
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(cities, rotation=45, ha='right')
    ax3.legend(fontsize=10, loc='upper left')
    ax3.grid(axis='y', alpha=0.3)
    
    # Chart 4: Revenue per Employee by City
    ax4 = fig.add_subplot(gs[2, 0])
    
    bars = ax4.barh(cities, df_stats['Revenue_per_Employee'] / 1000, 
                    color=colors, alpha=0.8)
    ax4.set_xlabel('Revenue per Employee ($1000s)', fontsize=11, fontweight='bold')
    ax4.set_title('Revenue per Employee by City', 
                 fontsize=12, fontweight='bold')
    ax4.grid(axis='x', alpha=0.3)
    
    # Add value labels
    for i, (city, val) in enumerate(zip(cities, df_stats['Revenue_per_Employee'])):
        ax4.text(val / 1000 + 5, i, f'${val/1000:.0f}k', 
                va='center', fontsize=9)
    
    # Chart 5: Total Revenue by City
    ax5 = fig.add_subplot(gs[2, 1])
    
    bars = ax5.barh(cities, df_stats['Total_Revenue_M'] / 1000, 
                    color=colors, alpha=0.8)
    ax5.set_xlabel('Total Revenue ($B)', fontsize=11, fontweight='bold')
    ax5.set_title('Total Revenue by City (Top 10% ZIPs)', 
                 fontsize=12, fontweight='bold')
    ax5.grid(axis='x', alpha=0.3)
    
    # Add value labels
    for i, (city, val) in enumerate(zip(cities, df_stats['Total_Revenue_M'])):
        ax5.text(val / 1000 + 10, i, f'${val/1000:.0f}B', 
                va='center', fontsize=9)
    
    # Main title
    fig.suptitle('Corporate Travel Time to Airport - Weighted by Revenue Metrics\n' +
                'Top 10% Corporate ZIP Codes - U.S. Census Bureau CBP 2021', 
                fontsize=14, fontweight='bold', y=0.995)
    
    # Add explanation text
    explanation = (
        'Revenue per Employee weighting: Higher weight to ZIPs with more productive companies\n'
        'Total Revenue weighting: Higher weight to ZIPs with larger total economic output\n'
        'Employment weighting: Higher weight to ZIPs with more employees'
    )
    fig.text(0.5, 0.01, explanation, ha='center', fontsize=9, 
            style='italic', color='#666666')
    
    plt.savefig(OUTPUT_CHART, dpi=150, bbox_inches='tight')
    print(f"[OK] Saved: {OUTPUT_CHART}")
    plt.close(fig)

# =============================================================================
# RUN
# =============================================================================
if __name__ == '__main__':
    main()

