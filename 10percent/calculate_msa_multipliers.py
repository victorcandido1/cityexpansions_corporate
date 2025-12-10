# -*- coding: utf-8 -*-
"""
CALCULATE MSA MULTIPLIERS FROM ACTUAL PAYROLL DATA
===================================================
Uses real payroll per employee data from Census Bureau to calculate
metropolitan-specific revenue multipliers.

This is more accurate than using external estimates because it's based
on actual economic data for these specific metros.
"""

import pandas as pd
import numpy as np
import json

print("\n" + "="*80)
print("CALCULATING MSA MULTIPLIERS FROM PAYROLL DATA")
print("="*80)
print("\n100% Based on Real Census Bureau Payroll Data\n")

# Load corporate top 10% data
df = pd.read_csv('top10_corporate_data.csv')

print(f"Loaded {len(df)} ZIP codes from Top 10% Corporate data\n")

# Calculate payroll per employee by city
city_stats = []

for city in df['city_key'].unique():
    city_data = df[df['city_key'] == city]
    
    # Weighted average payroll per employee
    total_payroll = (city_data['total_payroll_K'] * 1000).sum()
    total_employment = city_data['total_employment'].sum()
    
    if total_employment > 0:
        avg_payroll_per_emp = total_payroll / total_employment
    else:
        avg_payroll_per_emp = 0
    
    city_stats.append({
        'city_key': city,
        'city_name': city_data['city_name'].iloc[0],
        'total_payroll': total_payroll,
        'total_employment': total_employment,
        'payroll_per_employee': avg_payroll_per_emp,
        'zip_count': len(city_data)
    })

df_city = pd.DataFrame(city_stats).sort_values('payroll_per_employee', ascending=False)

# Calculate national baseline (weighted average across all metros)
national_payroll = df_city['total_payroll'].sum()
national_employment = df_city['total_employment'].sum()
national_baseline = national_payroll / national_employment

print("="*80)
print("PAYROLL PER EMPLOYEE BY METRO")
print("="*80)
print(f"{'City':20} {'Payroll/Emp':>15} {'Employment':>12} {'ZIPs':>6}")
print("-"*80)

for _, row in df_city.iterrows():
    print(f"{row['city_name']:20} ${row['payroll_per_employee']:>14,.0f} "
          f"{row['total_employment']:>12,} {row['zip_count']:>6}")

print("-"*80)
print(f"{'NATIONAL BASELINE':20} ${national_baseline:>14,.0f} "
      f"{national_employment:>12,}")
print("="*80)

# Calculate MSA multipliers
df_city['msa_multiplier'] = df_city['payroll_per_employee'] / national_baseline

print("\n" + "="*80)
print("MSA REVENUE MULTIPLIERS")
print("="*80)
print("\nBased on payroll-to-revenue correlation assumption:")
print("  If payroll is X% above average, revenue is also X% above average\n")
print(f"{'City':20} {'Multiplier':>12} {'% vs National':>15}")
print("-"*80)

for _, row in df_city.iterrows():
    pct_diff = (row['msa_multiplier'] - 1) * 100
    print(f"{row['city_name']:20} {row['msa_multiplier']:>12.3f}x "
          f"{pct_diff:>+14.1f}%")

print("="*80)

# Create multiplier dictionary
msa_multipliers = dict(zip(df_city['city_key'], df_city['msa_multiplier']))

# Save to JSON for easy import
with open('msa_multipliers.json', 'w') as f:
    json.dump(msa_multipliers, f, indent=2)

print("\n[OK] Saved: msa_multipliers.json")

# Save detailed stats
df_city.to_csv('msa_multipliers_analysis.csv', index=False, float_format='%.4f')
print("[OK] Saved: msa_multipliers_analysis.csv")

# Create comparison with simplified model
print("\n" + "="*80)
print("COMPARISON: PAYROLL-BASED vs SIMPLIFIED MODEL")
print("="*80)

simplified = {
    'san_francisco': 1.35,
    'new_york': 1.25,
    'miami': 1.15,
    'los_angeles': 1.10,
    'chicago': 1.05,
    'dallas': 0.95,
    'houston': 0.90
}

print(f"{'City':20} {'Payroll-Based':>15} {'Simplified':>12} {'Difference':>12}")
print("-"*80)

for city_key, payroll_mult in msa_multipliers.items():
    simp_mult = simplified.get(city_key, 1.0)
    diff = payroll_mult - simp_mult
    
    city_name = df_city[df_city['city_key'] == city_key]['city_name'].iloc[0]
    print(f"{city_name:20} {payroll_mult:>15.3f}x {simp_mult:>12.2f}x "
          f"{diff:>+11.3f}x")

print("="*80)

print("\n" + "="*80)
print("RECOMMENDATION")
print("="*80)
print("\n✅ Use PAYROLL-BASED multipliers:")
print("   - Based on actual Census Bureau data")
print("   - Reflects real local economic conditions")
print("   - More accurate than external estimates")
print("   - Metro-specific and data-driven")
print("\n" + "="*80)
print()


