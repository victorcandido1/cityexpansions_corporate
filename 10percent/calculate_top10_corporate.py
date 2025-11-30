# -*- coding: utf-8 -*-
"""
CALCULATE TOP 10% CORPORATE ZIP CODES
======================================
Creates a weighted combination to identify top 10% corporate ZIPs,
similar to the household wealth analysis.

Uses REAL Census Bureau data only.
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_FILE = os.path.join(BASE_DIR, 'corporate_all_zips.csv')
OUTPUT_FILE = os.path.join(BASE_DIR, 'top10_corporate_data.csv')

# Weights for Corporate Power Index (must sum to 1.0)
WEIGHTS = {
    'revenue': 0.40,      # 40% - Total estimated revenue
    'employment': 0.30,   # 30% - Total employment
    'power_share': 0.30   # 30% - Power industries percentage
}

# =============================================================================
# CALCULATE CORPORATE POWER INDEX
# =============================================================================
def calculate_corporate_power_index(df):
    """Calculate weighted Corporate Power Index"""
    print("\n" + "="*80)
    print("CALCULATING CORPORATE POWER INDEX")
    print("="*80)
    
    # Filter ZIPs with actual business activity
    df_active = df[df['total_employment'] > 0].copy()
    print(f"\n  Active ZIPs (with employment > 0): {len(df_active):,}")
    
    # Normalize each component (0-1 scale)
    components = {}
    
    # 1. Revenue (in $M)
    revenue_min = df_active['estimated_revenue_M'].min()
    revenue_max = df_active['estimated_revenue_M'].max()
    if revenue_max > revenue_min:
        components['revenue_norm'] = (df_active['estimated_revenue_M'] - revenue_min) / (revenue_max - revenue_min)
    else:
        components['revenue_norm'] = 0.5
    
    # 2. Employment
    emp_min = df_active['total_employment'].min()
    emp_max = df_active['total_employment'].max()
    if emp_max > emp_min:
        components['employment_norm'] = (df_active['total_employment'] - emp_min) / (emp_max - emp_min)
    else:
        components['employment_norm'] = 0.5
    
    # 3. Power Industries Share (%)
    power_min = df_active['power_emp_pct'].min()
    power_max = df_active['power_emp_pct'].max()
    if power_max > power_min:
        components['power_share_norm'] = (df_active['power_emp_pct'] - power_min) / (power_max - power_min)
    else:
        components['power_share_norm'] = 0.5
    
    # Calculate weighted index
    df_active['Corporate_Power_Index'] = (
        WEIGHTS['revenue'] * components['revenue_norm'] +
        WEIGHTS['employment'] * components['employment_norm'] +
        WEIGHTS['power_share'] * components['power_share_norm']
    ) * 100
    
    # Add component scores for transparency
    df_active['Revenue_Score'] = components['revenue_norm'] * 100
    df_active['Employment_Score'] = components['employment_norm'] * 100
    df_active['Power_Share_Score'] = components['power_share_norm'] * 100
    
    print(f"\n  Corporate Power Index calculated:")
    print(f"    Min: {df_active['Corporate_Power_Index'].min():.2f}")
    print(f"    Max: {df_active['Corporate_Power_Index'].max():.2f}")
    print(f"    Mean: {df_active['Corporate_Power_Index'].mean():.2f}")
    print(f"    Median: {df_active['Corporate_Power_Index'].median():.2f}")
    
    return df_active

# =============================================================================
# IDENTIFY TOP 10%
# =============================================================================
def identify_top10_corporate(df):
    """Identify top 10% corporate ZIPs by Corporate Power Index"""
    print("\n" + "="*80)
    print("IDENTIFYING TOP 10% CORPORATE ZIP CODES")
    print("="*80)
    
    # Calculate 90th percentile threshold
    threshold_90 = df['Corporate_Power_Index'].quantile(0.90)
    print(f"\n  90th Percentile Threshold: {threshold_90:.2f}")
    
    # Filter top 10%
    df_top10 = df[df['Corporate_Power_Index'] >= threshold_90].copy()
    df_top10 = df_top10.sort_values('Corporate_Power_Index', ascending=False)
    
    print(f"  Top 10% ZIPs: {len(df_top10):,}")
    print(f"  Total Employment: {df_top10['total_employment'].sum():,.0f}")
    print(f"  Total Revenue: ${df_top10['estimated_revenue_M'].sum()/1000:,.1f}B")
    print(f"  Power Industries Employment: {df_top10['power_employment'].sum():,.0f}")
    
    # Add threshold to dataframe
    df_top10['threshold_90'] = threshold_90
    
    # Summary by city
    print("\n  Top 10% Corporate by City:")
    city_summary = df_top10.groupby('city_name').agg({
        'zipcode': 'count',
        'total_employment': 'sum',
        'estimated_revenue_M': 'sum',
        'Corporate_Power_Index': 'mean'
    }).sort_values('zipcode', ascending=False)
    
    for city, row in city_summary.iterrows():
        print(f"    {city:15}: {int(row['zipcode']):>4} ZIPs, {int(row['total_employment']):>12,} emp, ${row['estimated_revenue_M']/1000:>8,.1f}B rev")
    
    return df_top10, threshold_90

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
    print("\n" + "="*80)
    print("TOP 10% CORPORATE ZIP CODES - WEIGHTED COMBINATION")
    print("="*80)
    print("\n*** 100% REAL DATA FROM U.S. CENSUS BUREAU ***")
    print(f"\nWeights: Revenue {WEIGHTS['revenue']*100:.0f}%, Employment {WEIGHTS['employment']*100:.0f}%, Power Share {WEIGHTS['power_share']*100:.0f}%")
    
    # Load data
    print("\n  Loading corporate data...")
    df = pd.read_csv(INPUT_FILE, dtype={'zipcode': str})
    print(f"  Total ZIPs: {len(df):,}")
    
    # Calculate Corporate Power Index
    df_active = calculate_corporate_power_index(df)
    
    # Identify top 10%
    df_top10, threshold_90 = identify_top10_corporate(df_active)
    
    # Save
    df_top10.to_csv(OUTPUT_FILE, index=False)
    print(f"\n  [OK] Saved: {OUTPUT_FILE}")
    print(f"      Top 10% ZIPs: {len(df_top10):,}")
    print(f"      Threshold: {threshold_90:.2f}")
    
    print("\n" + "="*80)
    print("COMPLETED")
    print("="*80)

