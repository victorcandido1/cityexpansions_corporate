# -*- coding: utf-8 -*-
"""
Verificar dados reais do ZIP 92301
"""
import pandas as pd
import os

zipcode = '92301'

print('='*80)
print(f'INVESTIGACAO DETALHADA DO ZIP CODE {zipcode}')
print('='*80)

# 1. Verificar nos dados de riqueza (Top 10%)
print('\n[1] DADOS DE RIQUEZA (Top 10%)')
print('-'*40)
df_wealth = pd.read_csv('top10_richest_data.csv', dtype={'zipcode': str})
w = df_wealth[df_wealth['zipcode'] == zipcode]

if len(w) > 0:
    row = w.iloc[0]
    print(f'  STATUS: ENCONTRADO nos Top 10% mais ricos!')
    print(f'  Cidade: {row["city_name"]}')
    print(f'  HH $200k+: {row["Households_200k"]:,.0f}')
    print(f'  Populacao: {row["Population"]:,.0f}')
    print(f'  AGI per Return: ${row["AGI_per_return"]:,.0f}')
    print(f'  Geometric Score: {row["Geometric_Score"]*100:.2f}%')
    print(f'  IRS Wealth Raw: {row["IRS_Wealth_Raw"]:.4f}')
    print(f'  Dist to Center: {row["dist_to_center"]:.1f} km')
else:
    print(f'  STATUS: NAO encontrado nos Top 10% mais ricos')

# 2. Verificar dados IRS brutos
print('\n[2] DADOS IRS BRUTOS')
print('-'*40)
irs_file = '../22zpallagi.csv'
if os.path.exists(irs_file):
    df_irs = pd.read_csv(irs_file, dtype={'zipcode': str})
    irs_data = df_irs[df_irs['zipcode'] == zipcode]
    
    if len(irs_data) > 0:
        print(f'  Registros IRS encontrados: {len(irs_data)}')
        
        # Colunas importantes
        cols_to_check = ['N1', 'A00100', 'A00300', 'A00600', 'A01000', 'A00900']
        col_names = ['Num_Returns', 'AGI_Total', 'Interest', 'Dividends', 'Capital_Gains', 'Business_Income']
        
        for col, name in zip(cols_to_check, col_names):
            if col in irs_data.columns:
                val = irs_data[col].sum()
                print(f'  {name}: {val:,.0f}')
        
        # Calcular AGI medio
        if 'N1' in irs_data.columns and 'A00100' in irs_data.columns:
            total_returns = irs_data['N1'].sum()
            total_agi = irs_data['A00100'].sum()
            if total_returns > 0:
                avg_agi = total_agi / total_returns
                print(f'\n  AGI MEDIO POR RETURN: ${avg_agi:,.0f}')
                print(f'  (Este e o indicador real de riqueza media)')
    else:
        print(f'  Nenhum dado IRS para {zipcode}')
else:
    print(f'  Arquivo IRS nao encontrado')

# 3. Verificar Census
print('\n[3] DADOS CENSUS')
print('-'*40)
census_file = '../new_folder/cache_census_all.csv'
if os.path.exists(census_file):
    df_census = pd.read_csv(census_file, dtype={'zipcode': str})
    census_data = df_census[df_census['zipcode'] == zipcode]
    
    if len(census_data) > 0:
        row = census_data.iloc[0]
        print(f'  Households $200k+: {row.get("Households_200k", "N/A")}')
        print(f'  Population: {row.get("Population", "N/A")}')
    else:
        print(f'  Nenhum dado Census para {zipcode}')
else:
    print(f'  Arquivo Census nao encontrado')

# 4. Verificar geometria
print('\n[4] DADOS GEOGRAFICOS')
print('-'*40)
try:
    import geopandas as gpd
    geom_file = '../new_folder/cache_geometry.gpkg'
    if os.path.exists(geom_file):
        gdf = gpd.read_file(geom_file)
        gdf['zipcode'] = gdf['zipcode'].astype(str).str.zfill(5)
        geom_data = gdf[gdf['zipcode'] == zipcode]
        
        if len(geom_data) > 0:
            row = geom_data.iloc[0]
            area_km2 = row['ALAND20'] / 1e6 if 'ALAND20' in row else 0
            print(f'  Area: {area_km2:.1f} km2')
            print(f'  Centroid Lat: {row.geometry.centroid.y:.4f}')
            print(f'  Centroid Lon: {row.geometry.centroid.x:.4f}')
        else:
            print(f'  Geometria nao encontrada para {zipcode}')
except Exception as e:
    print(f'  Erro ao carregar geometria: {e}')

# 5. Comparar com zip codes vizinhos
print('\n[5] COMPARACAO COM ZIPS VIZINHOS (923xx)')
print('-'*40)
nearby_zips = df_wealth[df_wealth['zipcode'].str.startswith('923')]
if len(nearby_zips) > 0:
    print(f'  Zips 923xx nos Top 10%: {len(nearby_zips)}')
    for _, r in nearby_zips.head(10).iterrows():
        print(f'    {r["zipcode"]}: AGI=${r["AGI_per_return"]:,.0f}, HH200k={r["Households_200k"]:,.0f}, Score={r["Geometric_Score"]*100:.1f}%')
else:
    print('  Nenhum zip 923xx nos top 10%')

# 6. Conclusao
print('\n' + '='*80)
print('CONCLUSAO')
print('='*80)

# Verificar se o zip esta realmente nos dados ou se e um erro
if len(w) == 0:
    print(f'\nO ZIP {zipcode} NAO esta nos Top 10% mais ricos.')
    print('Os dados de industria mostrados anteriormente sao SINTETICOS/ESTIMADOS,')
    print('nao representam negocios reais nessa localizacao.')
else:
    if w.iloc[0]['AGI_per_return'] < 100:
        print(f'\nALERTA: AGI muito baixo (${w.iloc[0]["AGI_per_return"]:,.0f})')
        print('Isso indica que a regiao provavelmente NAO e rica.')
        print('Pode haver um erro na classificacao ou nos dados.')

print('\n' + '='*80)

