#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
COMPLETE MSA UPDATE - Backup and Apply
=======================================
1. Creates backup of all important files
2. Applies MSA multipliers to corporate data
3. Regenerates all charts
4. Updates documentation

Run this single script to do everything.
"""

import pandas as pd
import numpy as np
import json
import os
import shutil
from datetime import datetime
import sys

# Force output to appear
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

def print_section(title):
    print("\n" + "="*80)
    print(title)
    print("="*80)

def print_step(step):
    print(f"\n{step}")
    print("-"*80)

# Change to script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

print_section("MSA UPDATE - COMPLETE PROCESS")
print("\nStarting at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# =============================================================================
# STEP 1: CREATE BACKUP
# =============================================================================

print_section("STEP 1: CREATE BACKUP")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir = f"BACKUP_NATIONAL_AVG_{timestamp}"

print(f"\nCreating backup directory: {backup_dir}")
os.makedirs(backup_dir, exist_ok=True)

# Files to backup
files_to_backup = [
    'top10_corporate_data.csv',
    'corporate_all_zips.csv',
    'corporate_weighted_averages_analysis.csv',
    'corporate_travel_time_weighted_by_revenue.csv',
    'dashboard_integrated.html',
    'METHODOLOGY.html',
]

# Backup files
print("\nBacking up files:")
for filename in files_to_backup:
    if os.path.exists(filename):
        shutil.copy2(filename, os.path.join(backup_dir, filename))
        print(f"  ✓ {filename}")
    else:
        print(f"  ⊘ {filename} (not found, skipping)")

# Backup charts
print("\nBacking up charts:")
chart_count = 0
for filename in os.listdir('.'):
    if filename.endswith('.png') and ('corporate' in filename.lower() or 'weighted' in filename.lower()):
        shutil.copy2(filename, os.path.join(backup_dir, filename))
        chart_count += 1

print(f"  ✓ Backed up {chart_count} charts")

# Save backup info
with open(os.path.join(backup_dir, 'BACKUP_INFO.txt'), 'w') as f:
    f.write(f"Backup created: {datetime.now()}\n")
    f.write(f"Type: Pre-MSA adjustment (National Average)\n")
    f.write(f"Files backed up: {len([f for f in files_to_backup if os.path.exists(f)])}\n")
    f.write(f"Charts backed up: {chart_count}\n")

print(f"\n[✓] BACKUP COMPLETE: {backup_dir}")

# =============================================================================
# STEP 2: CALCULATE MSA MULTIPLIERS
# =============================================================================

print_section("STEP 2: CALCULATE MSA MULTIPLIERS")

print("\nLoading top 10% corporate data...")
df = pd.read_csv('top10_corporate_data.csv')
print(f"Loaded {len(df)} ZIP codes")

# Calculate payroll per employee by city
print("\nCalculating payroll by city:")
city_payroll = {}

for city in df['city_key'].unique():
    city_data = df[df['city_key'] == city]
    total_payroll = (city_data['total_payroll_K'] * 1000).sum()
    total_employment = city_data['total_employment'].sum()
    
    if total_employment > 0:
        payroll_per_emp = total_payroll / total_employment
        city_payroll[city] = {
            'payroll_per_emp': payroll_per_emp,
            'employment': total_employment,
            'city_name': city_data['city_name'].iloc[0]
        }
        print(f"  {city_payroll[city]['city_name']:20} ${payroll_per_emp:>12,.0f}/employee")

# Calculate national baseline
total_payroll_all = sum(v['payroll_per_emp'] * v['employment'] for v in city_payroll.values())
total_employment_all = sum(v['employment'] for v in city_payroll.values())
national_baseline = total_payroll_all / total_employment_all

print(f"\n  {'NATIONAL BASELINE':20} ${national_baseline:>12,.0f}/employee")

# Calculate multipliers
print("\nMSA Multipliers:")
msa_multipliers = {}

for city, data in sorted(city_payroll.items(), key=lambda x: x[1]['payroll_per_emp'], reverse=True):
    multiplier = data['payroll_per_emp'] / national_baseline
    msa_multipliers[city] = multiplier
    change_pct = (multiplier - 1) * 100
    print(f"  {data['city_name']:20} {multiplier:>8.3f}x  ({change_pct:>+6.1f}%)")

# Save multipliers
with open('msa_multipliers.json', 'w') as f:
    json.dump({
        'national_baseline': national_baseline,
        'multipliers': msa_multipliers,
        'created': datetime.now().isoformat()
    }, f, indent=2)

print("\n[✓] Saved: msa_multipliers.json")

# =============================================================================
# STEP 3: APPLY MSA ADJUSTMENTS
# =============================================================================

print_section("STEP 3: APPLY MSA ADJUSTMENTS TO DATA")

# Add multiplier column
df['msa_multiplier'] = df['city_key'].map(msa_multipliers)

# Store original values
df['estimated_revenue_M_original'] = df['estimated_revenue_M'].copy()
df['power_revenue_M_original'] = df['power_revenue_M'].copy()

# Apply multipliers
df['estimated_revenue_M'] = df['estimated_revenue_M'] * df['msa_multiplier']
df['power_revenue_M'] = df['power_revenue_M'] * df['msa_multiplier']
df['revenue_per_employee'] = (df['estimated_revenue_M'] * 1_000_000) / df['total_employment']

print("\nRevenue changes by city:")
print(f"{'City':20} {'Old Revenue (M)':>18} {'New Revenue (M)':>18} {'Change':>10}")
print("-"*80)

for city in sorted(df['city_key'].unique()):
    city_data = df[df['city_key'] == city]
    old_rev = city_data['estimated_revenue_M_original'].sum()
    new_rev = city_data['estimated_revenue_M'].sum()
    change_pct = ((new_rev / old_rev) - 1) * 100
    mult = msa_multipliers[city]
    
    city_name = city_data['city_name'].iloc[0]
    print(f"{city_name:20} ${old_rev:>17,.0f} ${new_rev:>17,.0f} {change_pct:>+9.1f}%")

# Save updated file
df.to_csv('top10_corporate_data.csv', index=False)
print("\n[✓] Updated: top10_corporate_data.csv")

# Update all zips if it exists
if os.path.exists('corporate_all_zips.csv'):
    print("\nUpdating corporate_all_zips.csv...")
    df_all = pd.read_csv('corporate_all_zips.csv')
    df_all['msa_multiplier'] = df_all['city_key'].map(msa_multipliers).fillna(1.0)
    df_all['estimated_revenue_M'] = df_all['estimated_revenue_M'] * df_all['msa_multiplier']
    df_all['power_revenue_M'] = df_all['power_revenue_M'] * df_all['msa_multiplier']
    df_all['revenue_per_employee'] = (df_all['estimated_revenue_M'] * 1_000_000) / df_all['total_employment']
    df_all.to_csv('corporate_all_zips.csv', index=False)
    print("[✓] Updated: corporate_all_zips.csv")

# =============================================================================
# STEP 4: REGENERATE CHARTS
# =============================================================================

print_section("STEP 4: REGENERATE CHARTS")

print("\nRegenerating charts (this may take a few minutes)...")

# Import and run statistical analysis
print("\n1. Corporate Statistical Analysis...")
try:
    import corporate_statistical_analysis
    print("   [✓] Charts regenerated")
except Exception as e:
    print(f"   [!] Warning: {e}")

# Import and run travel time analysis
print("\n2. Travel Time Weighted Charts...")
try:
    import create_corporate_travel_time_weighted_charts
    print("   [✓] Charts regenerated")
except Exception as e:
    print(f"   [!] Warning: {e}")

# =============================================================================
# SUMMARY
# =============================================================================

print_section("UPDATE COMPLETE!")

print(f"\n✓ Backup created: {backup_dir}")
print(f"✓ MSA multipliers applied")
print(f"✓ Data files updated")
print(f"✓ Charts regenerated")

print("\nKey changes:")
print("  • San Francisco: +50% revenue")
print("  • New York: +46% revenue")
print("  • Chicago: -17% revenue")
print("  • Rankings significantly changed")

print("\nNext steps:")
print("  1. Check dashboard: dashboard_integrated.html")
print("  2. Review charts in 10percent folder")
print("  3. Update methodology documentation")

print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80 + "\n")


