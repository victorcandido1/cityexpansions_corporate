# -*- coding: utf-8 -*-
"""
TIPOS DE NEGÓCIOS POR CIDADE - TOP 20 ZIP CODES COM MAIOR RECEITA
=================================================================
Gera tabelas detalhadas por cidade mostrando os tipos de indústrias
"""

import pandas as pd
import numpy as np

# Nomes das industrias por codigo NAICS
INDUSTRY_NAMES = {
    '11': 'Agricultura/Pesca',
    '21': 'Mineracao/Petroleo/Gas',
    '22': 'Utilities (Energia/Agua)',
    '23': 'Construcao',
    '31': 'Manufatura (Alimentos)',
    '32': 'Manufatura (Quimica)',
    '33': 'Manufatura (Metal/Equip)',
    '42': 'Comercio Atacado',
    '44': 'Varejo (Lojas)',
    '45': 'Varejo (Eletronicos)',
    '48': 'Transporte',
    '49': 'Armazenagem/Logistica',
    '51': '** Midia/Informacao/Tech',
    '52': '** Financas/Bancos/Seguros',
    '53': '** Imobiliario',
    '54': '** Serv. Profissionais',
    '55': '** Gestao Empresarial',
    '56': 'Serv. Administrativos',
    '61': 'Educacao',
    '62': 'Saude',
    '71': '** Entretenimento/Artes',
    '72': 'Hoteis/Restaurantes',
    '81': 'Outros Servicos',
    '99': 'Nao Classificado'
}

POWER_INDUSTRIES = ['51', '52', '53', '54', '55', '71']

# Revenue per employee by industry ($1000s)
REVENUE_PER_EMPLOYEE = {
    '11': 150, '21': 800, '22': 600, '23': 200, '31': 350, '32': 350, '33': 350,
    '42': 500, '44': 250, '45': 250, '48': 200, '49': 200,
    '51': 500, '52': 600, '53': 300, '54': 180, '55': 500,
    '56': 100, '61': 80, '62': 100, '71': 150, '72': 50, '81': 80, '99': 100,
}

# Carregar dados
print("\n" + "="*100)
print("TIPOS DE NEGÓCIOS POR CIDADE - TOP 20 ZIP CODES COM MAIOR RECEITA")
print("="*100)

# Carregar dados de zip codes com receita
df_zips = pd.read_csv('corporate_power_by_zip.csv', dtype={'zipcode': str})
df_industry = pd.read_csv('industry_by_zip_all.csv', dtype={'zipcode': str, 'NAICS2': str})

# Top 20 zip codes por receita
top20_df = df_zips.nlargest(20, 'Estimated_Revenue').copy()
top20_zips = top20_df['zipcode'].tolist()

print(f"\nTop 20 Zip Codes por Receita:")
for i, (_, row) in enumerate(top20_df.iterrows(), 1):
    print(f"  {i}. {row['zipcode']} ({row['city_name']}): ${row['Estimated_Revenue']/1e9:.2f}B")

# Filtrar indústrias para os top 20 zips
df_top_industries = df_industry[df_industry['zipcode'].isin(top20_zips)].copy()

# Se city_name não existir, fazer merge
if 'city_name' not in df_top_industries.columns or df_top_industries['city_name'].isna().all():
    df_top_industries = df_top_industries.merge(
        df_zips[['zipcode', 'city_name']], on='zipcode', how='left'
    )

# Cidades nos top 20
cities_in_top20 = df_top_industries['city_name'].dropna().unique()

if len(cities_in_top20) == 0:
    # Se ainda não tiver cidades, usar diretamente de top20_df
    cities_in_top20 = top20_df['city_name'].unique()

print(f"\nCidades representadas nos Top 20 Zip Codes: {list(cities_in_top20)}")

# Criar tabelas por cidade
all_city_tables = []

for city in sorted(cities_in_top20):
    print(f"\n\n{'='*100}")
    print(f">>> {city.upper()}")
    print("="*100)
    
    # Filtrar para esta cidade
    df_city = df_top_industries[df_top_industries['city_name'] == city].copy()
    
    # Zip codes desta cidade nos top 20
    city_zips = df_city['zipcode'].unique()
    print(f"\nZip Codes nos Top 20: {list(city_zips)} ({len(city_zips)} zips)")
    
    # Agregar por indústria
    df_agg = df_city.groupby(['NAICS2', 'industry_name']).agg({
        'establishments': 'sum',
        'employment': 'sum',
        'payroll': 'sum',
        'revenue': 'sum',
        'is_power': 'first'
    }).reset_index()
    
    # Calcular porcentagens
    total_emp = df_agg['employment'].sum()
    total_rev = df_agg['revenue'].sum()
    df_agg['emp_share'] = df_agg['employment'] / total_emp * 100
    df_agg['rev_share'] = df_agg['revenue'] / total_rev * 100
    
    # Ordenar por receita
    df_agg = df_agg.sort_values('revenue', ascending=False)
    
    # Imprimir tabela
    print(f"\n{'Indústria':<35} | {'Estab.':<8} | {'Emprego':<10} | {'Receita ($M)':<12} | {'% Emp':<7} | {'% Rev':<7} | {'Power?':<6}")
    print("-"*100)
    
    for _, row in df_agg.iterrows():
        industry_name = INDUSTRY_NAMES.get(row['NAICS2'], row['industry_name'])
        is_power = 'YES' if row['is_power'] else ''
        print(f"{industry_name:<35} | {row['establishments']:>7,} | {row['employment']:>9,} | ${row['revenue']/1e6:>10.1f} | {row['emp_share']:>5.1f}% | {row['rev_share']:>5.1f}% | {is_power:^6}")
    
    print("-"*100)
    
    # Totais
    print(f"{'TOTAL':<35} | {df_agg['establishments'].sum():>7,} | {total_emp:>9,} | ${total_rev/1e6:>10.1f} | {100:>5.1f}% | {100:>5.1f}% |")
    
    # Power industries summary
    power_emp = df_agg[df_agg['is_power']]['employment'].sum()
    power_rev = df_agg[df_agg['is_power']]['revenue'].sum()
    print(f"\n  [POWER INDUSTRIES] (Midia, Financas, Imobiliario, Serv. Prof., Gestao, Entretenimento):")
    print(f"     Emprego: {power_emp:,} ({power_emp/total_emp*100:.1f}%)")
    print(f"     Receita: ${power_rev/1e6:,.1f}M ({power_rev/total_rev*100:.1f}%)")
    
    # Top 5 industrias
    print(f"\n  [TOP 5 INDUSTRIAS POR RECEITA]:")
    for idx, (_, row) in enumerate(df_agg.head(5).iterrows(), 1):
        industry_name = INDUSTRY_NAMES.get(row['NAICS2'], row['industry_name'])
        print(f"     {idx}. {industry_name}: ${row['revenue']/1e6:,.1f}M ({row['rev_share']:.1f}%)")
    
    # Guardar para export
    df_agg['city'] = city
    all_city_tables.append(df_agg)

# Criar tabela detalhada por zip code
print(f"\n\n{'='*100}")
print("[DETALHAMENTO POR ZIP CODE - TOP 10]")
print("="*100)

# Top 10 zips por receita
top10_zips = df_zips.nlargest(10, 'Estimated_Revenue')

for _, zip_row in top10_zips.iterrows():
    zipcode = zip_row['zipcode']
    city = zip_row['city_name']
    
    print(f"\n\n--- ZIP {zipcode} ({city}) ---")
    print(f"Receita Total: ${zip_row['Estimated_Revenue']/1e9:.2f}B | Emprego: {zip_row['Total_Employment']:,} | HH$200k+: {zip_row['Households_200k']:,.0f}")
    
    # Indústrias deste zip
    df_zip_ind = df_industry[df_industry['zipcode'] == zipcode].copy()
    df_zip_ind = df_zip_ind.sort_values('revenue', ascending=False)
    
    print(f"\n{'Indústria':<30} | {'Emp.':<8} | {'Receita ($M)':<12} | {'% Total':<8}")
    print("-"*70)
    
    total_zip_rev = df_zip_ind['revenue'].sum()
    for _, row in df_zip_ind.head(8).iterrows():
        industry_name = INDUSTRY_NAMES.get(str(row['NAICS2']), row['industry_name'])[:28]
        pct = row['revenue'] / total_zip_rev * 100 if total_zip_rev > 0 else 0
        print(f"{industry_name:<30} | {row['employment']:>7,} | ${row['revenue']/1e6:>10.1f} | {pct:>6.1f}%")

# Exportar dados combinados
df_all = pd.concat(all_city_tables, ignore_index=True)
df_all.to_csv('business_types_top20_by_city.csv', index=False)
print(f"\n\n[OK] business_types_top20_by_city.csv exportado")

# Criar tabela LaTeX resumida
print("\n\n" + "="*100)
print("TABELA LATEX - RESUMO POR CIDADE")
print("="*100)

print("\n\\begin{table}[htbp]")
print("\\centering")
print("\\caption{Tipos de Negócio por Cidade - Top 20 Zip Codes}")
print("\\label{tab:business_types}")
print("\\begin{tabular}{llrrr}")
print("\\hline")
print("Cidade & Indústria Principal & Receita (\\$M) & Emprego & \\% Revenue \\\\")
print("\\hline")

for city in sorted(cities_in_top20):
    df_city = df_all[df_all['city'] == city]
    top_industry = df_city.nlargest(1, 'revenue').iloc[0]
    industry_name = INDUSTRY_NAMES.get(top_industry['NAICS2'], top_industry['industry_name'])
    print(f"{city} & {industry_name[:25]} & {top_industry['revenue']/1e6:,.0f} & {top_industry['employment']:,} & {top_industry['rev_share']:.1f}\\% \\\\")

print("\\hline")
print("\\end{tabular}")
print("\\end{table}")

print("\n\nCONCLUÍDO!")

