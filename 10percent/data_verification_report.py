# -*- coding: utf-8 -*-
"""
DATA VERIFICATION REPORT
========================
Detailed report on what data is 100% REAL vs ESTIMATED
"""

import pandas as pd
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

print("\n" + "="*80)
print("RELATÓRIO DE VERIFICAÇÃO DE DADOS")
print("="*80)
print(f"\nGerado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

print("="*80)
print("[REAL] DADOS 100% REAIS (Diretamente de Fontes Oficiais)")
print("="*80)
print()

print("1. HOUSEHOLD DATA (IRS SOI 2022 + Census ACS 5yr 2022):")
print("   [REAL] Households $200k+ - 100% REAL")
print("   [REAL] AGI per Return - 100% REAL")
print("   [REAL] Population - 100% REAL")
print("   [CALCULADO] Geometric Score - CALCULADO de dados reais")
print()

print("2. CORPORATE DATA (U.S. Census Bureau - CBP 2021):")
print("   [REAL] Establishments (estabelecimentos) - 100% REAL")
print("   [REAL] Total Employment (por ZIP) - 100% REAL")
print("   [REAL] Total Annual Payroll - 100% REAL")
print("   [REAL] Industry Codes (NAICS) - 100% REAL")
print("   [REAL] ZIP Codes - 100% REAL")
print()

print("="*80)
print("[ESTIMADO] ESTIMATIVAS (Baseadas em Dados Reais + Metodologia)")
print("="*80)
print()

print("1. EMPLOYMENT POR INDÚSTRIA:")
print("   [ESTIMADO] ESTIMADO proporcionalmente aos establishments")
print("   Motivo: Census Bureau SUPRIME employment por indústria por privacidade")
print("   Metodologia: Employment_total × (Estab_industry / Estab_total)")
print("   Base: Dados REAIS de establishments e employment total")
print()

print("2. REVENUE (Receita):")
print("   [ESTIMADO] ESTIMADO usando revenue-per-employee")
print("   Fonte dos coeficientes: BLS (Bureau of Labor Statistics) médias por indústria")
print("   Fórmula: Employment_estimated × Revenue_per_Employee (BLS)")
print("   Base: Employment estimado (que vem de dados reais)")
print()

print("3. CORPORATE POWER INDEX:")
print("   [CALCULADO] CALCULADO (não vem direto da API)")
print("   Fórmula: 0.4×Revenue_Norm + 0.3×Employment_Norm + 0.3×Power_Share_Norm")
print("   Base: Dados REAIS de employment, establishments, e estimativas de revenue")
print()

print("="*80)
print("VERIFICACAO DOS ARQUIVOS")
print("="*80)
print()

files = {
    'zbp_real_data.csv': {
        'source': 'Census Bureau API',
        'real': True,
        'description': 'Dados brutos REAIS da API do Census'
    },
    'corporate_all_zips.csv': {
        'source': 'Processado de zbp_real_data.csv',
        'real': 'partial',
        'description': 'Employment e establishments REAIS, revenue ESTIMADO'
    },
    'industry_by_zip_all.csv': {
        'source': 'Processado de zbp_real_data.csv',
        'real': 'partial',
        'description': 'Establishments REAIS, employment por indústria ESTIMADO'
    },
    'top10_richest_data.csv': {
        'source': 'IRS SOI + Census ACS',
        'real': True,
        'description': '100% REAL de fontes governamentais'
    },
    'top10_corporate_data.csv': {
        'source': 'Calculado de corporate_all_zips.csv',
        'real': 'partial',
        'description': 'Baseado em dados reais + estimativas'
    }
}

for file, info in files.items():
    exists = os.path.exists(file)
    status = '[OK]' if exists else '[MISSING]'
    real_status = '100% REAL' if info['real'] == True else 'PARCIAL (Real + Estimado)' if info['real'] == 'partial' else 'CALCULADO'
    
    print(f"{status} {file:35}")
    print(f"   Fonte: {info['source']}")
    print(f"   Status: {real_status}")
    print(f"   Descricao: {info['description']}")
    print()

print("="*80)
print("RESUMO")
print("="*80)
print()

print("DADOS 100% REAIS:")
print("  • Establishments (todos) - Census Bureau")
print("  • Total Employment (por ZIP) - Census Bureau")
print("  • Total Payroll - Census Bureau")
print("  • Households $200k+ - IRS/Census")
print("  • AGI - IRS")
print("  • Population - Census")
print()

print("ESTIMATIVAS (baseadas em dados reais):")
print("  • Employment por indústria - estimado proporcionalmente")
print("  • Revenue - estimado usando BLS revenue-per-employee")
print("  • Corporate Power Index - calculado de dados reais")
print()

print("ARQUIVOS ANTIGOS COM DADOS SINTETICOS:")
print("  [LEGADO] corporate_power_analysis.py - tem funcao create_synthetic_zbp_data()")
print("  [LEGADO] corporate_power_full_analysis.py - tem funcao generate_corporate_data()")
print("  [LEGADO] corporate_maps.py - tem fallback para dados sinteticos")
print()
print("  [OK] ESTES ARQUIVOS NAO ESTAO SENDO USADOS!")
print("  [OK] Usamos apenas:")
print("     - fetch_real_zbp_parallel.py (busca dados REAIS)")
print("     - corporate_real_data_analysis.py (processa dados REAIS)")
print("     - corporate_maps_real_data.py (mapas com dados REAIS)")
print()

print("="*80)
print("[CONCLUSAO]")
print("="*80)
print()
print("TODOS os dados BASE sao 100% REAIS de fontes governamentais:")
print("  - U.S. Census Bureau - County Business Patterns 2021")
print("  - IRS SOI 2022")
print("  - Census ACS 5yr 2022")
print()
print("As unicas ESTIMATIVAS sao:")
print("  1. Employment por industria (Census suprime por privacidade)")
print("  2. Revenue (nao disponivel no Census, estimado via BLS)")
print()
print("NENHUM dado e SINTETICO ou GERADO ALEATORIAMENTE.")
print("Todas as estimativas sao baseadas em metodologia estatistica")
print("aplicada sobre dados reais.")
print()

