# -*- coding: utf-8 -*-
import pandas as pd
import sys

# Zip code a consultar
zipcode = sys.argv[1] if len(sys.argv) > 1 else '92301'

# Carregar dados
df_ind = pd.read_csv('industry_by_zip_all.csv', dtype={'zipcode': str, 'NAICS2': str})
df_zips = pd.read_csv('corporate_power_by_zip.csv', dtype={'zipcode': str})

# Nomes das industrias
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
    '51': 'Midia/Informacao/Tech',
    '52': 'Financas/Bancos/Seguros',
    '53': 'Imobiliario',
    '54': 'Serv. Profissionais',
    '55': 'Gestao Empresarial',
    '56': 'Serv. Administrativos',
    '61': 'Educacao',
    '62': 'Saude',
    '71': 'Entretenimento/Artes',
    '72': 'Hoteis/Restaurantes',
    '81': 'Outros Servicos',
    '99': 'Nao Classificado'
}

print(f"\n{'='*80}")
print(f"ANALISE DO ZIP CODE: {zipcode}")
print('='*80)

# Info geral do zip
zip_info = df_zips[df_zips['zipcode'] == zipcode]
if len(zip_info) > 0:
    row = zip_info.iloc[0]
    print(f"\nINFORMACOES GERAIS:")
    print(f"  Cidade: {row['city_name']}")
    print(f"  Receita Total Estimada: ${row['Estimated_Revenue']/1e9:.2f}B")
    print(f"  Emprego Total: {row['Total_Employment']:,}")
    print(f"  Estabelecimentos: {row['Total_Establishments']:,}")
    print(f"  HH $200k+: {row['Households_200k']:,.0f}")
    print(f"  Populacao: {row['Population']:,.0f}")
    print(f"  AGI por Return: ${row['AGI_per_return']:,.0f}")
    print(f"  Corp Power Index: {row['Corp_Power_Index']:.1f}")
    print(f"  Power Employment Share: {row['Power_Employment_Share']*100:.1f}%")
else:
    print(f"\n[!] Zip code {zipcode} nao encontrado nos dados corporativos")
    print("    Este zip pode estar fora das areas metropolitanas analisadas.")

# Industrias
df_zip = df_ind[df_ind['zipcode'] == zipcode]
if len(df_zip) > 0:
    df_zip = df_zip.sort_values('revenue', ascending=False)
    total_rev = df_zip['revenue'].sum()
    total_emp = df_zip['employment'].sum()
    
    print(f"\n{'='*80}")
    print(f"INDUSTRIAS/NEGOCIOS NO ZIP {zipcode}")
    print('='*80)
    
    header = f"{'Industria':<35} | {'Estab.':<7} | {'Emprego':<8} | {'Receita ($M)':<12} | {'% Rev':<7} | {'Power?':<6}"
    print(header)
    print('-'*80)
    
    for _, r in df_zip.iterrows():
        pct = r['revenue'] / total_rev * 100 if total_rev > 0 else 0
        power = 'SIM' if r['is_power'] else ''
        ind_name = INDUSTRY_NAMES.get(str(r['NAICS2']), r['industry_name'])
        print(f"{ind_name:<35} | {r['establishments']:>6,} | {r['employment']:>7,} | ${r['revenue']/1e6:>10.1f} | {pct:>5.1f}% | {power:^6}")
    
    print('-'*80)
    print(f"{'TOTAL':<35} | {df_zip['establishments'].sum():>6,} | {total_emp:>7,} | ${total_rev/1e6:>10.1f} | 100.0% |")
    
    # Top 5 industrias
    print(f"\nTOP 5 INDUSTRIAS POR RECEITA:")
    for i, (_, r) in enumerate(df_zip.head(5).iterrows(), 1):
        ind_name = INDUSTRY_NAMES.get(str(r['NAICS2']), r['industry_name'])
        pct = r['revenue'] / total_rev * 100 if total_rev > 0 else 0
        print(f"  {i}. {ind_name}: ${r['revenue']/1e6:.1f}M ({pct:.1f}%)")
    
    # Power industries
    power_rev = df_zip[df_zip['is_power']]['revenue'].sum()
    power_emp = df_zip[df_zip['is_power']]['employment'].sum()
    print(f"\nPOWER INDUSTRIES (Midia, Financas, Imobiliario, Serv.Prof, Gestao, Entretenimento):")
    print(f"  Receita: ${power_rev/1e6:.1f}M ({power_rev/total_rev*100:.1f}% do total)")
    print(f"  Emprego: {power_emp:,} ({power_emp/total_emp*100:.1f}% do total)")
    
else:
    print(f"\n[!] Nenhuma industria encontrada para zip {zipcode}")
    print("    Verificando se o zip existe nos dados de riqueza...")
    
    # Tentar encontrar nos dados de top10
    df_wealth = pd.read_csv('top10_richest_data.csv', dtype={'zipcode': str})
    wealth_info = df_wealth[df_wealth['zipcode'] == zipcode]
    if len(wealth_info) > 0:
        w = wealth_info.iloc[0]
        print(f"\n    Encontrado nos dados de riqueza:")
        print(f"    Cidade: {w['city_name']}")
        print(f"    HH $200k+: {w['Households_200k']:,.0f}")
        print(f"    Populacao: {w['Population']:,.0f}")
    else:
        print(f"    Zip {zipcode} nao encontrado em nenhum dataset.")

print("\n" + "="*80)

