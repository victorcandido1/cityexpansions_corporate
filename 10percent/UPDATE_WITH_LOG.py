#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MSA UPDATE WITH LOG FILE
========================
Runs the update and writes all output to a log file.
Double-click this file to run it!
"""

import pandas as pd
import numpy as np
import json
import os
import shutil
import sys
from datetime import datetime

# Redirect output to file
log_file = open('MSA_UPDATE_LOG.txt', 'w', encoding='utf-8')
sys.stdout = log_file
sys.stderr = log_file

try:
    print("="*80)
    print("MSA UPDATE - STARTING")
    print(f"Time: {datetime.now()}")
    print("="*80)
    
    # Change directory
    os.chdir(r'G:\Meu Drive\Journey\Modelos\Revo\Strategy\Expansion_v2\GeoEco\v1\10percent')
    print(f"\nWorking directory: {os.getcwd()}")
    
    # CREATE BACKUP
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"BACKUP_NATIONAL_AVG_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    shutil.copy2('top10_corporate_data.csv', f'{backup_dir}/top10_corporate_data.csv')
    print(f"\n✓ BACKUP CREATED: {backup_dir}")
    
    # LOAD DATA
    df = pd.read_csv('top10_corporate_data.csv')
    print(f"✓ LOADED: {len(df)} ZIP codes")
    print(f"  Columns: {len(df.columns)}")
    
    # CALCULATE MULTIPLIERS
    print("\n" + "="*80)
    print("CALCULATING MSA MULTIPLIERS")
    print("="*80)
    
    city_data = df.groupby('city_key').agg({
        'total_payroll_K': lambda x: (x * 1000).sum(),
        'total_employment': 'sum',
        'city_name': 'first'
    }).reset_index()
    
    city_data['payroll_per_emp'] = city_data['total_payroll_K'] * 1000 / city_data['total_employment']
    national_baseline = (city_data['payroll_per_emp'] * city_data['total_employment']).sum() / city_data['total_employment'].sum()
    city_data['msa_multiplier'] = city_data['payroll_per_emp'] / national_baseline
    
    print(f"\nNATIONAL BASELINE: ${national_baseline:,.0f}/employee\n")
    print("MSA MULTIPLIERS:")
    print(city_data[['city_name', 'payroll_per_emp', 'msa_multiplier']].to_string(index=False))
    
    # SAVE MULTIPLIERS
    multipliers = dict(zip(city_data['city_key'], city_data['msa_multiplier']))
    with open('msa_multipliers.json', 'w') as f:
        json.dump({'national_baseline': national_baseline, 'multipliers': multipliers}, f, indent=2)
    print("\n✓ SAVED: msa_multipliers.json")
    
    # APPLY TO DATA
    print("\n" + "="*80)
    print("APPLYING MSA ADJUSTMENTS")
    print("="*80)
    
    df['msa_multiplier'] = df['city_key'].map(multipliers)
    df['estimated_revenue_M_original'] = df['estimated_revenue_M'].copy()
    df['estimated_revenue_M'] = df['estimated_revenue_M'] * df['msa_multiplier']
    df['power_revenue_M'] = df['power_revenue_M'] * df['msa_multiplier']
    df['revenue_per_employee'] = (df['estimated_revenue_M'] * 1_000_000) / df['total_employment']
    
    print("\nREVENUE CHANGES BY CITY:")
    print("="*80)
    for city in sorted(df['city_key'].unique()):
        city_df = df[df['city_key'] == city]
        old_rev = city_df['estimated_revenue_M_original'].sum()
        new_rev = city_df['estimated_revenue_M'].sum()
        change_pct = ((new_rev / old_rev) - 1) * 100
        city_name = city_df['city_name'].iloc[0]
        mult = multipliers[city]
        print(f"{city_name:20} ${old_rev:>10,.0f}M → ${new_rev:>10,.0f}M ({mult:.3f}x, {change_pct:+.1f}%)")
    
    # SAVE
    df.to_csv('top10_corporate_data.csv', index=False)
    print("\n✓ SAVED: top10_corporate_data.csv")
    print(f"  New columns: {len(df.columns)} (added msa_multiplier)")
    
    print("\n" + "="*80)
    print("✅ UPDATE COMPLETE!")
    print("="*80)
    print(f"\nBackup folder: {backup_dir}")
    print(f"Log file: MSA_UPDATE_LOG.txt")
    print("\nNext steps:")
    print("  1. Regenerate charts: python corporate_statistical_analysis.py")
    print("  2. Update travel time: python create_corporate_travel_time_weighted_charts.py")
    print("  3. Regenerate maps: python corporate_maps_real_data.py")
    
    print(f"\nCompleted at: {datetime.now()}")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

finally:
    log_file.close()
    
    # Also create a SUCCESS flag file
    with open('UPDATE_SUCCESS.txt', 'w') as f:
        f.write(f"Update completed at {datetime.now()}\n")
        f.write(f"Check MSA_UPDATE_LOG.txt for details\n")

print("\n✓ Done! Check MSA_UPDATE_LOG.txt for output")


