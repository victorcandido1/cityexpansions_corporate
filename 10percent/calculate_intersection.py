# -*- coding: utf-8 -*-
"""
CALCULATE INTERSECTION: TOP 10% HOUSEHOLDS vs TOP 10% CORPORATE
=================================================================
Analyzes overlap between wealthy households and corporate power ZIPs.
Creates statistics for dashboard integration.
"""

import pandas as pd
import os
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

HOUSEHOLD_FILE = os.path.join(BASE_DIR, 'top10_richest_data.csv')
CORPORATE_FILE = os.path.join(BASE_DIR, 'top10_corporate_data.csv')
OUTPUT_FILE = os.path.join(BASE_DIR, 'intersection_analysis.csv')
CITY_SUMMARY_FILE = os.path.join(BASE_DIR, 'intersection_by_city.csv')

CITIES = {
    'los_angeles': 'Los Angeles',
    'new_york': 'New York',
    'chicago': 'Chicago',
    'dallas': 'Dallas',
    'houston': 'Houston',
    'miami': 'Miami',
    'san_francisco': 'San Francisco',
}

# =============================================================================
# LOAD DATA
# =============================================================================
def load_data():
    """Load household and corporate top 10% data"""
    print("\n" + "="*80)
    print("LOADING TOP 10% DATA")
    print("="*80)
    
    df_household = pd.read_csv(HOUSEHOLD_FILE, dtype={'zipcode': str})
    df_corporate = pd.read_csv(CORPORATE_FILE, dtype={'zipcode': str})
    
    # Filter out 'other' category - only keep 7 metros
    df_household = df_household[df_household['city_key'] != 'other'].copy()
    df_corporate = df_corporate[df_corporate['city_key'] != 'other'].copy()
    
    print(f"  Household Top 10% (7 metros): {len(df_household)} ZIPs")
    print(f"  Corporate Top 10% (7 metros): {len(df_corporate)} ZIPs")
    
    return df_household, df_corporate

# =============================================================================
# CALCULATE INTERSECTION
# =============================================================================
def calculate_intersection(df_household, df_corporate):
    """Calculate intersection between household and corporate top 10%"""
    print("\n" + "="*80)
    print("CALCULATING INTERSECTION")
    print("="*80)
    
    # Get ZIP sets
    hh_zips = set(df_household['zipcode'].unique())
    corp_zips = set(df_corporate['zipcode'].unique())
    
    # Intersection
    intersection_zips = hh_zips & corp_zips
    only_household = hh_zips - corp_zips
    only_corporate = corp_zips - hh_zips
    
    print(f"\n  Household Top 10%: {len(hh_zips):,} ZIPs")
    print(f"  Corporate Top 10%: {len(corp_zips):,} ZIPs")
    print(f"  INTERSECTION: {len(intersection_zips):,} ZIPs ({len(intersection_zips)/len(hh_zips)*100:.1f}% of household top 10%)")
    print(f"  Only Household: {len(only_household):,} ZIPs")
    print(f"  Only Corporate: {len(only_corporate):,} ZIPs")
    
    # Create intersection dataframe
    df_intersection = df_household[df_household['zipcode'].isin(intersection_zips)].copy()
    
    # Merge corporate data
    df_intersection = df_intersection.merge(
        df_corporate[['zipcode', 'Corporate_Power_Index', 'total_employment', 
                     'estimated_revenue_M', 'power_employment', 'power_emp_pct']],
        on='zipcode', how='left', suffixes=('_hh', '_corp')
    )
    
    # Calculate combined metrics
    # Combined_Score = 50% Household Geometric_Score + 50% Corporate_Power_Index
    # NOTE: Uses Corporate_Power_Index (arithmetic, no distance), NOT Corporate_Score (geometric, with distance)
    df_intersection['Combined_Score'] = (
        df_intersection['Geometric_Score'] * 0.5 +  # Household wealth (geometric mean)
        (df_intersection['Corporate_Power_Index'] / 100) * 0.5  # Corporate power (arithmetic mean, no distance)
    )
    
    # Save intersection data
    df_intersection.to_csv(OUTPUT_FILE, index=False)
    print(f"\n  [OK] Saved intersection data: {OUTPUT_FILE}")
    
    return df_intersection, intersection_zips, only_household, only_corporate

# =============================================================================
# CITY-LEVEL ANALYSIS
# =============================================================================
def analyze_by_city(df_household, df_corporate, intersection_zips):
    """Analyze intersection by city"""
    print("\n" + "="*80)
    print("CITY-LEVEL INTERSECTION ANALYSIS")
    print("="*80)
    
    city_stats = []
    
    for city_key, city_name in CITIES.items():
        # Household top 10%
        hh_city = df_household[df_household['city_key'] == city_key]
        hh_zips = set(hh_city['zipcode'].unique())
        
        # Corporate top 10%
        corp_city = df_corporate[df_corporate['city_key'] == city_key]
        corp_zips = set(corp_city['zipcode'].unique())
        
        # Intersection
        city_intersection = hh_zips & corp_zips
        
        # Statistics
        stats = {
            'city': city_name,
            'city_key': city_key,
            'household_top10': len(hh_zips),
            'corporate_top10': len(corp_zips),
            'intersection': len(city_intersection),
            'intersection_pct_of_household': len(city_intersection) / len(hh_zips) * 100 if len(hh_zips) > 0 else 0,
            'intersection_pct_of_corporate': len(city_intersection) / len(corp_zips) * 100 if len(corp_zips) > 0 else 0,
        }
        
        # Household metrics (top 10%)
        if len(hh_city) > 0:
            stats['hh_total_hh200k'] = hh_city['Households_200k'].sum()
            stats['hh_median_agi'] = hh_city['AGI_per_return'].median()
            stats['hh_median_score'] = hh_city['Geometric_Score'].median()
        
        # Corporate metrics (top 10%)
        if len(corp_city) > 0:
            stats['corp_total_employment'] = corp_city['total_employment'].sum()
            stats['corp_total_revenue_M'] = corp_city['estimated_revenue_M'].sum()
            stats['corp_median_power_index'] = corp_city['Corporate_Power_Index'].median()
            stats['corp_power_employment'] = corp_city['power_employment'].sum()
        
        # Intersection metrics
        if len(city_intersection) > 0:
            intersection_data = df_household[df_household['zipcode'].isin(city_intersection)]
            stats['intersection_hh200k'] = intersection_data['Households_200k'].sum()
            stats['intersection_median_agi'] = intersection_data['AGI_per_return'].median()
            
            intersection_corp = df_corporate[df_corporate['zipcode'].isin(city_intersection)]
            stats['intersection_employment'] = intersection_corp['total_employment'].sum()
            stats['intersection_revenue_M'] = intersection_corp['estimated_revenue_M'].sum()
        
        city_stats.append(stats)
        
        print(f"\n  {city_name}:")
        print(f"    Household Top 10%: {stats['household_top10']} ZIPs")
        print(f"    Corporate Top 10%: {stats['corporate_top10']} ZIPs")
        print(f"    INTERSECTION: {stats['intersection']} ZIPs ({stats['intersection_pct_of_household']:.1f}% of HH, {stats['intersection_pct_of_corporate']:.1f}% of Corp)")
    
    # Create dataframe
    df_city_stats = pd.DataFrame(city_stats)
    df_city_stats = df_city_stats.fillna(0)
    
    # Save
    df_city_stats.to_csv(CITY_SUMMARY_FILE, index=False)
    print(f"\n  [OK] Saved city summary: {CITY_SUMMARY_FILE}")
    
    return df_city_stats

# =============================================================================
# ADVANCED STATISTICS
# =============================================================================
def calculate_advanced_stats(df_household, df_corporate, df_intersection):
    """Calculate advanced statistics comparing household and corporate wealth"""
    print("\n" + "="*80)
    print("ADVANCED STATISTICS")
    print("="*80)
    
    stats = {}
    
    # Overall intersection
    hh_zips = set(df_household['zipcode'].unique())
    corp_zips = set(df_corporate['zipcode'].unique())
    intersection_zips = hh_zips & corp_zips
    
    stats['total_household_top10'] = len(hh_zips)
    stats['total_corporate_top10'] = len(corp_zips)
    stats['total_intersection'] = len(intersection_zips)
    stats['intersection_pct'] = len(intersection_zips) / len(hh_zips) * 100 if len(hh_zips) > 0 else 0
    
    # Correlation between household wealth and corporate power
    merged = df_household.merge(
        df_corporate[['zipcode', 'Corporate_Power_Index']],
        on='zipcode', how='inner'
    )
    
    if len(merged) > 0:
        correlation = merged['Geometric_Score'].corr(merged['Corporate_Power_Index'])
        stats['correlation'] = correlation
        print(f"\n  Correlation (Household Score vs Corporate Power Index): {correlation:.3f}")
    
    # Intersection statistics
    if len(df_intersection) > 0:
        stats['intersection_hh200k'] = df_intersection['Households_200k'].sum()
        stats['intersection_employment'] = df_intersection['total_employment'].sum()
        stats['intersection_revenue_M'] = df_intersection['estimated_revenue_M'].sum()
        stats['intersection_median_agi'] = df_intersection['AGI_per_return'].median()
        stats['intersection_median_corp_index'] = df_intersection['Corporate_Power_Index'].median()
        
        print(f"\n  Intersection ZIPs:")
        print(f"    Total HH $200k+: {stats['intersection_hh200k']:,.0f}")
        print(f"    Total Employment: {stats['intersection_employment']:,.0f}")
        print(f"    Total Revenue: ${stats['intersection_revenue_M']/1000:,.1f}B")
        print(f"    Median AGI: ${stats['intersection_median_agi']:,.0f}")
        print(f"    Median Corporate Power Index: {stats['intersection_median_corp_index']:.2f}")
    
    return stats

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
    print("\n" + "="*80)
    print("INTERSECTION ANALYSIS: HOUSEHOLDS vs CORPORATE")
    print("="*80)
    print("\n*** 100% REAL DATA ***")
    
    # Load data
    df_household, df_corporate = load_data()
    
    # Calculate intersection
    df_intersection, intersection_zips, only_household, only_corporate = calculate_intersection(df_household, df_corporate)
    
    # City-level analysis
    df_city_stats = analyze_by_city(df_household, df_corporate, intersection_zips)
    
    # Advanced statistics
    advanced_stats = calculate_advanced_stats(df_household, df_corporate, df_intersection)
    
    print("\n" + "="*80)
    print("COMPLETED")
    print("="*80)

