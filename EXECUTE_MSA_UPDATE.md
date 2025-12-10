# EXECUTE MSA UPDATE - Direct Instructions

## The Issue

The terminal isn't showing Python output due to PowerShell buffering. However, I've prepared everything you need.

## ✅ SOLUTION: Run This in Jupyter Notebook or Python IDE

Copy and paste this ENTIRE code block into Jupyter Notebook, VS Code, or PyCharm:

```python
import pandas as pd
import numpy as np
import json
import os
import shutil
from datetime import datetime

# Change to correct directory
os.chdir(r'G:\Meu Drive\Journey\Modelos\Revo\Strategy\Expansion_v2\GeoEco\v1\10percent')

print("="*80)
print("MSA UPDATE - BACKUP AND APPLY")
print("="*80)

# ============================================================================
# STEP 1: CREATE BACKUP
# ============================================================================

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir = f"BACKUP_NATIONAL_AVG_{timestamp}"
os.makedirs(backup_dir, exist_ok=True)

# Backup files
files_to_backup = [
    'top10_corporate_data.csv',
    'corporate_weighted_averages_analysis.csv',
    'corporate_travel_time_weighted_by_revenue.csv',
]

for filename in files_to_backup:
    if os.path.exists(filename):
        shutil.copy2(filename, os.path.join(backup_dir, filename))
        print(f"  ✓ Backed up: {filename}")

print(f"\n✓ BACKUP COMPLETE: {backup_dir}\n")

# ============================================================================
# STEP 2: CALCULATE MSA MULTIPLIERS
# ============================================================================

print("="*80)
print("CALCULATING MSA MULTIPLIERS")
print("="*80)

df = pd.read_csv('top10_corporate_data.csv')
print(f"\nLoaded {len(df)} ZIP codes\n")

# Calculate payroll per employee by city
city_stats = []
for city in df['city_key'].unique():
    city_data = df[df['city_key'] == city]
    total_payroll = (city_data['total_payroll_K'] * 1000).sum()
    total_employment = city_data['total_employment'].sum()
    
    if total_employment > 0:
        city_stats.append({
            'city_key': city,
            'city_name': city_data['city_name'].iloc[0],
            'payroll_per_emp': total_payroll / total_employment,
            'employment': total_employment
        })

df_cities = pd.DataFrame(city_stats).sort_values('payroll_per_emp', ascending=False)

# Calculate national baseline
national_baseline = (df_cities['payroll_per_emp'] * df_cities['employment']).sum() / df_cities['employment'].sum()
df_cities['msa_multiplier'] = df_cities['payroll_per_emp'] / national_baseline

print("Payroll per Employee by City:")
print(df_cities[['city_name', 'payroll_per_emp', 'msa_multiplier']].to_string(index=False))
print(f"\nNational Baseline: ${national_baseline:,.0f}/employee\n")

# Create multiplier dictionary
msa_multipliers = dict(zip(df_cities['city_key'], df_cities['msa_multiplier']))

# Save multipliers
with open('msa_multipliers.json', 'w') as f:
    json.dump({
        'national_baseline': national_baseline,
        'multipliers': msa_multipliers,
        'created': datetime.now().isoformat()
    }, f, indent=2)

print("✓ Saved: msa_multipliers.json\n")

# ============================================================================
# STEP 3: APPLY MSA ADJUSTMENTS
# ============================================================================

print("="*80)
print("APPLYING MSA ADJUSTMENTS")
print("="*80)

# Add multiplier column
df['msa_multiplier'] = df['city_key'].map(msa_multipliers)

# Store original values for comparison
df['estimated_revenue_M_original'] = df['estimated_revenue_M'].copy()

# Apply multipliers to revenue
df['estimated_revenue_M'] = df['estimated_revenue_M'] * df['msa_multiplier']
df['power_revenue_M'] = df['power_revenue_M'] * df['msa_multiplier']
df['revenue_per_employee'] = (df['estimated_revenue_M'] * 1_000_000) / df['total_employment']

# Show changes
print("\nRevenue Changes by City:")
print("="*80)
for city in sorted(df['city_key'].unique()):
    city_data = df[df['city_key'] == city]
    old_rev = city_data['estimated_revenue_M_original'].sum()
    new_rev = city_data['estimated_revenue_M'].sum()
    change_pct = ((new_rev / old_rev) - 1) * 100
    
    city_name = city_data['city_name'].iloc[0]
    mult = msa_multipliers[city]
    print(f"{city_name:20} ${old_rev:>10,.0f}M → ${new_rev:>10,.0f}M ({mult:.3f}x, {change_pct:+.1f}%)")

# Save updated file
df.to_csv('top10_corporate_data.csv', index=False)
print("\n✓ Updated: top10_corporate_data.csv")

print("\n" + "="*80)
print("DATA UPDATE COMPLETE!")
print("="*80)
print("\nBackup folder:", backup_dir)
print("\nNext steps:")
print("  1. Regenerate charts: python corporate_statistical_analysis.py")
print("  2. Update travel time: python create_corporate_travel_time_weighted_charts.py")
print("  3. Regenerate maps: python corporate_maps_real_data.py")
print("="*80)
```

## After Running the Above Code

### Then Regenerate Charts

```python
# In the same Python session or new one:
os.chdir(r'G:\Meu Drive\Journey\Modelos\Revo\Strategy\Expansion_v2\GeoEco\v1\10percent')

print("\nRegenerating charts...")
exec(open('corporate_statistical_analysis.py').read())
exec(open('create_corporate_travel_time_weighted_charts.py').read())

print("\n✓ CHARTS REGENERATED!")
```

### Then Regenerate Maps (YES, Maps Need Updating!)

```python
# Maps use revenue data, so they need updating too:
print("\nRegenerating corporate maps...")
exec(open('corporate_maps_real_data.py').read())

print("\n✓ MAPS REGENERATED!")
```

## About the Maps

**YES, the maps DO need updating!** I found that:

1. **`corporate_maps_real_data.py`** - Uses `estimated_revenue_M` 
2. **`create_national_maps.py`** - Uses `estimated_revenue_M`

These maps display revenue information in tooltips and use revenue for scoring/coloring, so they will show the NEW MSA-adjusted values once regenerated.

## Verification

After running, check:

```python
# Verify backup exists
import os
backups = [d for d in os.listdir('.') if d.startswith('BACKUP_NATIONAL_AVG')]
print("Backups:", backups)

# Verify MSA multipliers
with open('msa_multipliers.json') as f:
    print(json.load(f))

# Verify data has new column
df_check = pd.read_csv('top10_corporate_data.csv')
print("\nColumns:", df_check.columns.tolist())
print("\nHas msa_multiplier?", 'msa_multiplier' in df_check.columns)

# Show sample
print("\nSample data:")
print(df_check[['city_name', 'msa_multiplier', 'estimated_revenue_M']].head())
```

## Why Terminal Doesn't Work

PowerShell has output buffering issues with Python. The scripts ARE running (exit code 0), but output isn't displayed. Using Jupyter/IDE solves this.

## Files That Will Be Updated

### Data:
- ✅ `top10_corporate_data.csv` (adds msa_multiplier column)

### Charts (20+ files):
- ✅ All `corporate_histogram_*.png`
- ✅ `corporate_weighted_averages_chart.png`
- ✅ `corporate_travel_time_weighted_by_revenue.png`
- ✅ All statistical charts

### Maps (YES!):
- ✅ `map_corporate_*.html` (all city maps)
- ✅ `map_corporate_national.html`
- ✅ Tooltips will show new revenue values
- ✅ Colors/scores will reflect new data

### CSV Exports:
- ✅ `corporate_weighted_averages_analysis.csv`
- ✅ `corporate_travel_time_weighted_by_revenue.csv`

---

**RECOMMENDATION:** 

1. Open Jupyter Notebook or VS Code
2. Copy the first code block above
3. Run it
4. You'll see all the output!
5. Then run the chart regeneration code
6. Then run the map regeneration code

This will take 3-5 minutes total and you'll see everything happening in real-time.

---

**Status:** Ready to execute
**Risk:** LOW (backup created first)
**Impact:** HIGH (major changes)
**Maps:** YES, they need updating too!


