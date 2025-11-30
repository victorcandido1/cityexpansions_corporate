# -*- coding: utf-8 -*-
"""
TOP 20 ZIP CODES COM MAIOR RECEITA - TOP 10 NEGÓCIOS
=====================================================
Gera tabela com os 10 maiores negócios dos 20 zip codes
com a maior receita estimada.
"""

import pandas as pd
import numpy as np

# Carregar dados
df = pd.read_csv('corporate_power_by_zip.csv', dtype={'zipcode': str})

print("\n" + "="*100)
print("ANÁLISE: TOP 20 ZIP CODES COM MAIOR RECEITA")
print("="*100)

# Ordenar por receita e pegar top 20
top20 = df.nlargest(20, 'Estimated_Revenue')

print(f"\nTop 20 Zip Codes por Receita Estimada:")
print("-"*120)
print(f"| {'Rank':<4} | {'Zip':<8} | {'Cidade':<15} | {'Receita ($B)':<12} | {'Emprego':<10} | {'Estabelecimentos':<15} | {'Power %':<8} | {'HH200k':<8} |")
print("-"*120)

for idx, (_, row) in enumerate(top20.iterrows(), 1):
    print(f"| {idx:<4} | {row['zipcode']:<8} | {row['city_name']:<15} | ${row['Estimated_Revenue']/1e9:>10.2f} | {row['Total_Employment']:>9,} | {row['Total_Establishments']:>14,} | {row['Power_Employment_Share']*100:>6.1f}% | {row['Households_200k']:>7,.0f} |")

print("-"*120)

# Total do Top 20
print(f"\n  TOTAIS TOP 20:")
print(f"    Receita Total: ${top20['Estimated_Revenue'].sum()/1e9:.2f}B")
print(f"    Emprego Total: {top20['Total_Employment'].sum():,.0f}")
print(f"    HH200k+ Total: {top20['Households_200k'].sum():,.0f}")

# Agora, os 10 maiores negócios (ordenar por receita por zip)
print("\n\n" + "="*100)
print("TOP 10 MAIORES NEGÓCIOS (Zip Codes por Receita)")
print("="*100)

# Criar score de "tamanho do negócio" = Receita + Emprego ponderado
top20['Business_Size_Score'] = (
    top20['Estimated_Revenue'] / 1e9 +  # Receita em bilhões
    top20['Total_Employment'] * 0.0001 +  # Emprego (menor peso)
    top20['Power_Revenue_Share'] * top20['Estimated_Revenue'] / 1e9  # Receita de indústrias "power"
)

top10_businesses = top20.nlargest(10, 'Estimated_Revenue')

print(f"\nTop 10 Zip Codes - Maiores Concentrações de Negócios:")
print("-"*140)
print(f"| {'Rank':<4} | {'Zip':<8} | {'Cidade':<15} | {'Receita Total ($B)':<18} | {'Power Revenue ($B)':<18} | {'Emprego':<10} | {'Salário Médio ($)':<15} | {'AGI/Return ($k)':<15} |")
print("-"*140)

for idx, (_, row) in enumerate(top10_businesses.iterrows(), 1):
    power_rev = row['Power_Revenue_Share'] * row['Estimated_Revenue'] if pd.notna(row['Power_Revenue_Share']) else 0
    payroll_per_emp = row['Total_Payroll'] / row['Total_Employment'] if row['Total_Employment'] > 0 else 0
    print(f"| {idx:<4} | {row['zipcode']:<8} | {row['city_name']:<15} | ${row['Estimated_Revenue']/1e9:>16.2f} | ${power_rev/1e9:>16.2f} | {row['Total_Employment']:>9,} | ${payroll_per_emp:>13,.0f} | ${row['AGI_per_return']:>13,.0f} |")

print("-"*140)

# Exportar para CSV
export_df = top20[['zipcode', 'city_name', 'Estimated_Revenue', 'Power_Revenue', 'Total_Employment', 
                    'Total_Payroll', 'Total_Establishments', 'Power_Employment_Share', 
                    'Households_200k', 'AGI_per_return', 'Population']].copy()
export_df.columns = ['Zipcode', 'City', 'Revenue_USD', 'Power_Revenue_USD', 'Employment', 
                     'Payroll_USD', 'Establishments', 'Power_Emp_Share', 'HH_200k', 'AGI_per_Return', 'Population']
export_df['Revenue_Billions'] = export_df['Revenue_USD'] / 1e9
export_df['Rank'] = range(1, 21)
export_df = export_df[['Rank', 'Zipcode', 'City', 'Revenue_Billions', 'Revenue_USD', 'Power_Revenue_USD', 
                       'Employment', 'Establishments', 'Power_Emp_Share', 'HH_200k', 'AGI_per_Return', 'Population']]
export_df.to_csv('top20_revenue_analysis.csv', index=False)
print("\n  [OK] top20_revenue_analysis.csv exportado")

# Tabela formatada para LaTeX/Paper
print("\n\n" + "="*100)
print("TABELA FORMATADA (Top 10)")
print("="*100)

print("\n\\begin{table}[htbp]")
print("\\centering")
print("\\caption{Top 10 Zip Codes com Maior Receita Estimada}")
print("\\label{tab:top10_revenue}")
print("\\begin{tabular}{clrrrrr}")
print("\\hline")
print("Rank & Zip Code & Cidade & Receita (\\$B) & Emprego & Estab. & HH \\$200k+ \\\\")
print("\\hline")

for idx, (_, row) in enumerate(top10_businesses.iterrows(), 1):
    print(f"{idx} & {row['zipcode']} & {row['city_name']} & {row['Estimated_Revenue']/1e9:.2f} & {row['Total_Employment']:,} & {row['Total_Establishments']:,} & {row['Households_200k']:,.0f} \\\\")

print("\\hline")
print("\\end{tabular}")
print("\\end{table}")

print("\n\n  CONCLUÍDO!")

