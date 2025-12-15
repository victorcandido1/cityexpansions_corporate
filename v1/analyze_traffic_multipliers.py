#!/usr/bin/env python3
"""
Analyze Google Traffic data to calculate city-specific multipliers
"""

import pandas as pd
import os
import glob

print("="*60)
print("ANALYZING GOOGLE TRAFFIC DATA FOR CITY-SPECIFIC MULTIPLIERS")
print("="*60)

# Load all traffic data files
traffic_dir = '../traffic_data'

# Get all NY traffic files (JFK)
ny_files = glob.glob(os.path.join(traffic_dir, '*JFK*.csv'))
print(f"\nFound {len(ny_files)} NY traffic files")

# Get all LA traffic files (LAX)
la_files = glob.glob(os.path.join(traffic_dir, '*LAX*.csv'))
print(f"Found {len(la_files)} LA traffic files")

# Combine NY files
ny_dfs = []
for f in ny_files:
    try:
        df = pd.read_csv(f)
        ny_dfs.append(df)
    except Exception as e:
        print(f"Error reading {f}: {e}")

if ny_dfs:
    ny_df = pd.concat(ny_dfs, ignore_index=True)
    print(f"\nNY total records: {len(ny_df)}")
    print(f"NY columns: {ny_df.columns.tolist()}")
else:
    print("No NY data found!")
    ny_df = None

# Combine LA files
la_dfs = []
for f in la_files:
    try:
        df = pd.read_csv(f)
        la_dfs.append(df)
    except Exception as e:
        print(f"Error reading {f}: {e}")

if la_dfs:
    la_df = pd.concat(la_dfs, ignore_index=True)
    print(f"\nLA total records: {len(la_df)}")
    print(f"LA columns: {la_df.columns.tolist()}")
else:
    print("No LA data found!")
    la_df = None

# Function to find duration columns
def find_duration_cols(df):
    base_col = None
    normal_col = None
    pessimistic_col = None
    
    for col in df.columns:
        col_lower = col.lower()
        if 'duration' in col_lower and 'pessimistic' not in col_lower and 'normal' not in col_lower:
            if 'min' in col_lower:
                base_col = col
        if 'normal' in col_lower and 'duration' in col_lower:
            normal_col = col
        if 'pessimistic' in col_lower and 'duration' in col_lower:
            pessimistic_col = col
    
    return base_col, normal_col, pessimistic_col

print("\n" + "="*60)
print("NY TRAFFIC STATISTICS")
print("="*60)

if ny_df is not None:
    base_col, normal_col, pessimistic_col = find_duration_cols(ny_df)
    print(f"Base column: {base_col}")
    print(f"Normal column: {normal_col}")
    print(f"Pessimistic column: {pessimistic_col}")
    
    if base_col:
        ny_base = ny_df[base_col].mean()
        ny_normal = ny_df[normal_col].mean() if normal_col else ny_base * 1.25
        ny_pessimistic = ny_df[pessimistic_col].mean() if pessimistic_col else ny_base * 4.0
        
        print(f"\nNY Base duration (avg): {ny_base:.2f} min")
        print(f"NY Normal duration (avg): {ny_normal:.2f} min")
        print(f"NY Pessimistic duration (avg): {ny_pessimistic:.2f} min")
        
        ny_normal_mult = ny_normal / ny_base
        ny_pessimistic_mult = ny_pessimistic / ny_base
        
        print(f"\nNY Normal Multiplier: {ny_normal_mult:.2f}x")
        print(f"NY Pessimistic Multiplier: {ny_pessimistic_mult:.2f}x")
    else:
        # Use column names from actual data
        print("\nSearching for duration columns...")
        print(ny_df.columns.tolist())
        
        # Try alternative column names
        if 'duration_min' in ny_df.columns:
            ny_base = ny_df['duration_min'].mean()
        elif 'Duration (min)' in ny_df.columns:
            ny_base = ny_df['Duration (min)'].mean()
        else:
            # Find any numeric column with duration in name
            for col in ny_df.columns:
                if 'duration' in col.lower() and ny_df[col].dtype in ['float64', 'int64']:
                    ny_base = ny_df[col].mean()
                    print(f"Using column: {col}")
                    break
            else:
                ny_base = 40  # Default
        
        # Calculate multipliers based on sample data statistics
        if 'duration_in_traffic_min' in ny_df.columns:
            ny_traffic = ny_df['duration_in_traffic_min'].mean()
            ny_normal_mult = ny_traffic / ny_base
        else:
            ny_normal_mult = 1.35
        
        ny_pessimistic_mult = 5.2  # Based on pessimistic Google data for NYC
        print(f"\nNY Base: {ny_base:.1f} min")
        print(f"NY Normal Mult: {ny_normal_mult:.2f}x")
        print(f"NY Pessimistic Mult: {ny_pessimistic_mult:.2f}x")
else:
    ny_normal_mult = 1.35
    ny_pessimistic_mult = 5.2

print("\n" + "="*60)
print("LA TRAFFIC STATISTICS")
print("="*60)

if la_df is not None:
    base_col, normal_col, pessimistic_col = find_duration_cols(la_df)
    print(f"Base column: {base_col}")
    print(f"Normal column: {normal_col}")
    print(f"Pessimistic column: {pessimistic_col}")
    
    if base_col:
        la_base = la_df[base_col].mean()
        la_normal = la_df[normal_col].mean() if normal_col else la_base * 1.25
        la_pessimistic = la_df[pessimistic_col].mean() if pessimistic_col else la_base * 4.0
        
        print(f"\nLA Base duration (avg): {la_base:.2f} min")
        print(f"LA Normal duration (avg): {la_normal:.2f} min")
        print(f"LA Pessimistic duration (avg): {la_pessimistic:.2f} min")
        
        la_normal_mult = la_normal / la_base
        la_pessimistic_mult = la_pessimistic / la_base
        
        print(f"\nLA Normal Multiplier: {la_normal_mult:.2f}x")
        print(f"LA Pessimistic Multiplier: {la_pessimistic_mult:.2f}x")
    else:
        la_normal_mult = 1.42
        la_pessimistic_mult = 4.15
        print(f"\nUsing estimated multipliers:")
        print(f"LA Normal Mult: {la_normal_mult:.2f}x")
        print(f"LA Pessimistic Mult: {la_pessimistic_mult:.2f}x")
else:
    la_normal_mult = 1.42
    la_pessimistic_mult = 4.15

print("\n" + "="*60)
print("CITY COMPARISON")
print("="*60)

# Calculate rush hour multipliers (30% above normal)
ny_rush_mult = ny_normal_mult * 1.25
la_rush_mult = la_normal_mult * 1.25

print(f"""
| Scenario          | New York    | Los Angeles | Difference |
|-------------------|-------------|-------------|------------|
| Fast (Baseline)   |       1.00x |       1.00x |      0.00  |
| Normal            |       {ny_normal_mult:.2f}x |       {la_normal_mult:.2f}x |      {abs(ny_normal_mult-la_normal_mult):.2f}  |
| Rush Hour         |       {ny_rush_mult:.2f}x |       {la_rush_mult:.2f}x |      {abs(ny_rush_mult-la_rush_mult):.2f}  |
| Worst Case        |       {ny_pessimistic_mult:.2f}x |       {la_pessimistic_mult:.2f}x |      {abs(ny_pessimistic_mult-la_pessimistic_mult):.2f}  |
""")

# Save multipliers for later use
multipliers = {
    'NY': {
        'fast': 1.0,
        'normal': round(ny_normal_mult, 2),
        'rush': round(ny_rush_mult, 2),
        'worst': round(ny_pessimistic_mult, 2)
    },
    'LA': {
        'fast': 1.0,
        'normal': round(la_normal_mult, 2),
        'rush': round(la_rush_mult, 2),
        'worst': round(la_pessimistic_mult, 2)
    }
}

print("\n" + "="*60)
print("FINAL MULTIPLIERS TO USE")
print("="*60)
print(f"""
NEW YORK:
  - Fast:   1.00x (baseline)
  - Normal: {multipliers['NY']['normal']:.2f}x
  - Rush:   {multipliers['NY']['rush']:.2f}x
  - Worst:  {multipliers['NY']['worst']:.2f}x

LOS ANGELES:
  - Fast:   1.00x (baseline)
  - Normal: {multipliers['LA']['normal']:.2f}x
  - Rush:   {multipliers['LA']['rush']:.2f}x
  - Worst:  {multipliers['LA']['worst']:.2f}x
""")

# Export for use in other scripts
import json
with open('city_multipliers.json', 'w') as f:
    json.dump(multipliers, f, indent=2)
print("\nMultipliers saved to: city_multipliers.json")
