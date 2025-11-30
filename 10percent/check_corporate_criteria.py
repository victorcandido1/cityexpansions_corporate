# -*- coding: utf-8 -*-
"""Check corporate wealth criteria"""
import pandas as pd

corp = pd.read_csv('corporate_all_zips.csv', dtype={'zipcode': str})

print('='*80)
print('CRITERIO DE RIQUEZA CORPORATIVA ATUAL')
print('='*80)
print()

print('Métricas disponíveis no dataset:')
print(f'  - Total Employment: {corp["total_employment"].sum():,.0f}')
print(f'  - Total Revenue: ${corp["estimated_revenue_M"].sum()/1000:,.1f}B')
print(f'  - Power Employment: {corp["power_employment"].sum():,.0f}')
print()

print('Top 10 ZIPs por Revenue:')
top_rev = corp.nlargest(10, 'estimated_revenue_M')[['zipcode', 'city_name', 'estimated_revenue_M', 'total_employment', 'power_emp_pct']]
for _, row in top_rev.iterrows():
    print(f'  {row["zipcode"]:6} {row["city_name"]:15} ${row["estimated_revenue_M"]:>12,.0f}M  {row["total_employment"]:>10,} emp  Power: {row["power_emp_pct"]:>5.1f}%')
print()

print('Top 10 ZIPs por Employment:')
top_emp = corp.nlargest(10, 'total_employment')[['zipcode', 'city_name', 'estimated_revenue_M', 'total_employment', 'power_emp_pct']]
for _, row in top_emp.iterrows():
    print(f'  {row["zipcode"]:6} {row["city_name"]:15} ${row["estimated_revenue_M"]:>12,.0f}M  {row["total_employment"]:>10,} emp  Power: {row["power_emp_pct"]:>5.1f}%')
print()

print('Colunas disponíveis:', list(corp.columns))
print()

# Verificar se temos Corporate Power Index calculado
if 'power_emp_pct' in corp.columns:
    print('Power Industries % disponível')
    print(f'  Média: {corp["power_emp_pct"].mean():.1f}%')
    print(f'  Mediana: {corp["power_emp_pct"].median():.1f}%')
    print(f'  Máximo: {corp["power_emp_pct"].max():.1f}%')
print()

print('='*80)
print('CORPORATE POWER INDEX (usado nos mapas):')
print('='*80)
print('Fórmula: 0.4 × Revenue_Norm + 0.3 × Employment_Norm + 0.3 × Power_Share_Norm')
print()
print('Onde:')
print('  - Revenue_Norm: Receita total normalizada (0-1)')
print('  - Employment_Norm: Emprego total normalizado (0-1)')
print('  - Power_Share_Norm: % Power Industries normalizado (0-1)')
print()
print('Power Industries: Information, Finance, Real Estate, Professional Services,')
print('                  Management, Entertainment/Arts')

