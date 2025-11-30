# -*- coding: utf-8 -*-
"""Quick check of real census data"""
import pandas as pd

df = pd.read_csv('zbp_real_data.csv', dtype={'zipcode': str, 'NAICS2': str})

print("="*80)
print("DADOS REAIS DO CENSUS BUREAU - ZIP CODE BUSINESS PATTERNS 2021")
print("="*80)
print(f"\nTotal records: {len(df):,}")
print(f"Unique ZIPs: {df['zipcode'].nunique():,}")

# Get totals (NAICS2 = '00' for total all industries)
totals = df[df['NAICS2'] == '00'].copy()
print(f"\nZIPs with total data: {len(totals):,}")

print("\n" + "="*80)
print("TOTAIS POR CIDADE")
print("="*80)

city_totals = totals.groupby('city_key').agg({
    'establishments': 'sum',
    'employment': 'sum',
    'annual_payroll': 'sum',
    'zipcode': 'nunique'
}).sort_values('employment', ascending=False)

print(f"\n{'Cidade':<15} | {'ZIPs':>6} | {'Estabelec.':>12} | {'Emprego':>14} | {'Payroll ($B)':>14}")
print("-"*80)

for city in city_totals.index:
    zips = int(city_totals.loc[city, 'zipcode'])
    estab = int(city_totals.loc[city, 'establishments'])
    emp = int(city_totals.loc[city, 'employment'])
    pay = city_totals.loc[city, 'annual_payroll'] / 1e6  # Convert to billions
    print(f"{city:<15} | {zips:>6,} | {estab:>12,} | {emp:>14,} | ${pay:>13,.1f}")

print("-"*80)
total_zips = int(city_totals['zipcode'].sum())
total_estab = int(city_totals['establishments'].sum())
total_emp = int(city_totals['employment'].sum())
total_pay = city_totals['annual_payroll'].sum() / 1e9
print(f"{'TOTAL':<15} | {total_zips:>6,} | {total_estab:>12,} | {total_emp:>14,} | ${total_pay:>13,.2f}T")

# Top 20 ZIPs by employment
print("\n" + "="*80)
print("TOP 20 ZIPs POR EMPREGO")
print("="*80)

top_zips = totals.nlargest(20, 'employment')[['zipcode', 'city_key', 'establishments', 'employment', 'annual_payroll']]
top_zips['payroll_B'] = top_zips['annual_payroll'] / 1e6

print(f"\n{'Rank':>4} | {'ZIP':>6} | {'Cidade':<15} | {'Estab.':>10} | {'Emprego':>12} | {'Payroll ($B)':>12}")
print("-"*80)

for i, (_, row) in enumerate(top_zips.iterrows(), 1):
    print(f"{i:>4} | {row['zipcode']:>6} | {row['city_key']:<15} | {int(row['establishments']):>10,} | {int(row['employment']):>12,} | ${row['payroll_B']:>11,.2f}")

print("\n" + "="*80)
print("DADOS 100% REAIS - FONTE: U.S. CENSUS BUREAU")
print("="*80)

