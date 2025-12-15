# Análise V4 - Cenário Pessimista (Pior Caso)

## 📊 Visão Geral

Esta análise compara tempos de viagem de helicóptero vs carro para aeroportos em **New York** e **Los Angeles**, utilizando o **cenário PESSIMISTA** baseado em dados históricos do Google Traffic.

## ⚠️ Características Principais

### Multiplicadores de Tráfego (derivados do Google)
- **Rush Hour**: 1.68x
- **Pior Caso**: 4.68x (quase 5x mais lento que condições normais!)

### Regras de Manhattan
- ZIP codes de Manhattan usam **EXCLUSIVAMENTE** helipontos localizados na ilha:
  - **JRB** - Downtown Manhattan/Wall St Heliport
  - **JRA** - West 30th St Heliport
  - **6N5** - East 34th Street Heliport
  - **3NY2** - Astoria Heliport (Queens, próximo)
- Helipontos de polícia são **EXCLUÍDOS**

## 📈 Resultados

| Métrica | New York | Los Angeles |
|---------|----------|-------------|
| Total ZIP Codes | 70 | 44 |
| Manhattan ZIPs | 27 | - |
| Tempo Carro (worst) | 221 min | 222 min |
| Tempo Heli (worst) | 74 min | 79 min |
| **Economia (worst)** | **147 min** | **143 min** |
| % com vantagem heli | 99% | 98% |
| Velocidade média (worst) | 11.9 km/h | 13.7 km/h |

## 📁 Arquivos

### Dados
- `analysis_v4_pessimistic.csv` - Resultados completos (114 ZIP codes)
- `route_segments_100m.csv` - 62,579 segmentos de 100m com velocidades

### Scripts
- `analysis_v4_pessimistic.py` - Script principal de análise
- `create_map_v4.py` - Gerador de mapas interativos
- `create_charts_v4.py` - Gerador de gráficos (EN/PT)

### Visualizações
- `dashboard_v4.html` - Dashboard interativo completo
- `map_v4_ny_pessimistic.html` - Mapa interativo NY
- `map_v4_la_pessimistic.html` - Mapa interativo LA
- `charts_v4_en/` - Gráficos em inglês
- `charts_v4_pt/` - Gráficos em português

## 🚀 Como Usar

1. Abrir `dashboard_v4.html` no navegador
2. Ou iniciar servidor local:
   ```bash
   python -m http.server 8080
   ```
3. Acessar `http://localhost:8080/dashboard_v4.html`

## 📊 Gráficos Disponíveis

Cada gráfico está disponível em **inglês** (charts_v4_en/) e **português** (charts_v4_pt/):

1. `fig1_comparison_worst.png` - Comparação Carro vs Helicóptero
2. `fig2_savings_boxplot.png` - Box Plot de Economia
3. `fig3_speed_comparison.png` - Velocidade por Cenário
4. `fig4_time_per_100m.png` - Tempo para percorrer 100m
5. `fig5_manhattan_comparison.png` - Manhattan vs Outras Áreas
6. `fig6_summary_table.png` - Tabela Resumo
7. `fig7_savings_distribution.png` - Distribuição de Economia

## 🔍 Metodologia

### Cálculo de Tempo de Helicóptero
1. Tempo de carro até heliponto (com tráfego)
2. + 10 min check-in
3. + Tempo de voo (200 km/h)
4. + 10 min transfer no aeroporto

### Cenários de Tráfego
- **Fast**: Multiplicador 1.0x (baseline OSRM)
- **Normal**: Multiplicador 1.25x
- **Rush**: Multiplicador 1.68x (horário de pico)
- **Worst**: Multiplicador 4.68x (pior cenário histórico)

## 📅 Data de Geração
Dezembro 2025

