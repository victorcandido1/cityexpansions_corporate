#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UPDATE ALL DATA WITH MSA MULTIPLIERS
=====================================
Direct implementation of MSA adjustments.
"""

import pandas as pd
import numpy as np
import json
import os

os.chdir(r'G:\Meu Drive\Journey\Modelos\Revo\Strategy\Expansion_v2\GeoEco\v1\10percent')

print("\n" + "="*80)
print("MSA ADJUSTMENT - COMPLETE UPDATE")
print("="*80)

# Load data
print("\nLoading data...")
df = pd.read_csv('top10_corporate_data.csv')
print(f"Loaded {len(df)} ZIP codes")

# Calculate MSA multipliers from payroll
print("\nCalculating MSA multipliers from payroll data...")

city_stats = []
for city in df['city_key'].unique():
    city_data = df[df['city_key'] == city]
    total_payroll = (city_data['total_payroll_K'] * 1000).sum()
    total_emp = city_data['total_employment'].sum()
    
    city_stats.append({
        'city_key': city,
        'city_name': city_data['city_name'].iloc[0],
        'payroll_per_emp': total_payroll / total_emp if total_emp > 0 else 0,
        'total_emp': total_emp
    })

df_cities = pd.DataFrame(city_stats)

# National baseline
national_baseline = (df_cities['payroll_per_emp'] * df_cities['total_emp']).sum() / df_cities['total_emp'].sum()
df_cities['msa_multiplier'] = df_cities['payroll_per_emp'] / national_baseline

print(f"\nNational baseline: ${national_baseline:,.0f}/employee")
print("\nMSA Multipliers:")
print(df_cities[['city_name', 'payroll_per_emp', 'msa_multiplier']].to_string(index=False))

# Save multipliers
multipliers = dict(zip(df_cities['city_key'], df_cities['msa_multiplier']))
with open('msa_multipliers.json', 'w') as f:
    json.dump(multipliers, f, indent=2)
print("\n✓ Saved: msa_multipliers.json")

# Apply to data
print("\nApplying MSA multipliers...")
df['msa_multiplier'] = df['city_key'].map(multipliers)
df['estimated_revenue_M_original'] = df['estimated_revenue_M']
df['estimated_revenue_M'] = df['estimated_revenue_M'] * df['msa_multiplier']
df['power_revenue_M'] = df['power_revenue_M'] * df['msa_multiplier']
df['revenue_per_employee'] = (df['estimated_revenue_M'] * 1_000_000) / df['total_employment']

# Backup and save
import shutil
shutil.copy2('top10_corporate_data.csv', 'top10_corporate_data_BACKUP.csv')
df.to_csv('top10_corporate_data.csv', index=False)
print("✓ Updated: top10_corporate_data.csv")
print("✓ Backup: top10_corporate_data_BACKUP.csv")

# Summary
print("\n" + "="*80)
print("REVENUE CHANGES BY CITY")
print("="*80)
for city in df['city_key'].unique():
    city_data = df[df['city_key'] == city]
    old_rev = city_data['estimated_revenue_M_original'].sum()
    new_rev = city_data['estimated_revenue_M'].sum()
    change = ((new_rev/old_rev) - 1) * 100
    mult = multipliers[city]
    print(f"{city_data['city_name'].iloc[0]:20} ${old_rev:>10,.0f}M → ${new_rev:>10,.0f}M ({mult:.3f}x, {change:+.1f}%)")

print("\n" + "="*80)
print("SUCCESS! Now run:")
print("  python corporate_statistical_analysis.py")
print("  python create_corporate_travel_time_weighted_charts.py")
print("="*80 + "\n")


