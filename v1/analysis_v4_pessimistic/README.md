# Análise V4 - Cenário Pessimista (Pior Caso)

## 📊 Visão Geral

Esta análise compara tempos de viagem de helicóptero vs carro para aeroportos em **New York** e **Los Angeles**, utilizando o **cenário PESSIMISTA** baseado em dados históricos do Google Traffic.

## ⚠️ Características Principais

### Multiplicadores de Tráfego (derivados do Google)
| Cenário | Multiplicador | Descrição |
|---------|---------------|-----------|
| Fast | 1.0x | Fluxo livre |
| Normal | 1.25x | Condições típicas |
| Rush Hour | 1.68x | Horário de pico |
| **Worst Case** | **4.68x** | Congestionamento severo |

### Regras de Manhattan
- ZIP codes de Manhattan usam **EXCLUSIVAMENTE** helipontos localizados na ilha
- Helipontos de polícia são **EXCLUÍDOS**

## 📈 Resultados Principais

| Métrica | New York | Los Angeles |
|---------|----------|-------------|
| Total ZIP Codes | 70 | 44 |
| Manhattan ZIPs | 27 | - |
| Tempo Carro (worst) | 221 min | 222 min |
| Tempo Heli (worst) | 74 min | 79 min |
| **Economia (worst)** | **147 min** | **143 min** |
| % com vantagem heli | 99% | 98% |
| Velocidade média (worst) | 12 km/h | 14 km/h |

## 📁 Estrutura de Arquivos

```
analysis_v4_pessimistic/
├── 📊 DADOS
│   ├── analysis_v4_pessimistic.csv    # Resultados (114 ZIP codes)
│   └── route_segments_100m.csv        # 62,579 segmentos de 100m
│
├── 🐍 SCRIPTS
│   ├── analysis_v4_pessimistic.py     # Script principal
│   ├── create_map_v4.py               # Gerador de mapas
│   └── create_charts_v4.py            # Gerador de gráficos
│
├── 🗺️ MAPAS INTERATIVOS
│   ├── dashboard_v4.html              # Dashboard completo
│   ├── map_v4_ny_pessimistic.html     # Mapa NY
│   └── map_v4_la_pessimistic.html     # Mapa LA
│
├── 📊 GRÁFICOS BÁSICOS
│   ├── charts_v4_en/                  # Gráficos V4 (inglês)
│   └── charts_v4_pt/                  # Gráficos V4 (português)
│
├── 📊 GRÁFICOS COMPARATIVOS (NOVO!)
│   ├── comparison_charts_en/          # Comparação Normal vs Worst (inglês)
│   │   ├── fig1_scenario_comparison.png
│   │   ├── fig2_speed_comparison.png
│   │   ├── fig3_time_100m.png
│   │   ├── fig4_savings_boxplot.png
│   │   ├── fig5_multiplier_effect.png
│   │   ├── fig6_normal_vs_worst.png
│   │   ├── fig7_summary_table.png
│   │   └── fig8_savings_histogram.png
│   └── comparison_charts_pt/          # Comparação Normal vs Worst (português)
│       └── (mesmos arquivos acima)
│
├── 📐 DIAGRAMAS (NOVO!)
│   ├── journey_diagram_en.png         # Fluxo de trajeto (inglês)
│   ├── journey_diagram_pt.png         # Fluxo de trajeto (português)
│   ├── traffic_multiplier_en.png      # Multiplicadores (inglês)
│   ├── traffic_multiplier_pt.png      # Multiplicadores (português)
│   ├── time_breakdown_en.png          # Detalhamento (inglês)
│   └── time_breakdown_pt.png          # Detalhamento (português)
│
├── 📄 PAPERS LaTeX (NOVO!)
│   ├── paper_comparison_en.tex        # Paper completo (inglês)
│   └── paper_comparison_pt.tex        # Paper completo (português)
│
└── 🎬 APRESENTAÇÕES Beamer (NOVO!)
    ├── presentation_en.tex            # Slides (inglês)
    ├── presentation_en.pdf            # PDF compilado (inglês)
    └── presentation_pt.tex            # Slides (português)
```

## 📊 Descrição dos Gráficos Comparativos

1. **fig1_scenario_comparison** - Carro vs Helicóptero em todos os cenários
2. **fig2_speed_comparison** - Velocidade média por cenário
3. **fig3_time_100m** - Tempo para percorrer 100 metros
4. **fig4_savings_boxplot** - Box plot de economia por cenário
5. **fig5_multiplier_effect** - Efeito do multiplicador no tempo
6. **fig6_normal_vs_worst** - Comparação direta Normal vs Pior Caso
7. **fig7_summary_table** - Tabela resumo completa
8. **fig8_savings_histogram** - Distribuição de economia

## 📐 Descrição dos Diagramas

1. **journey_diagram** - Comparação visual dos trajetos (carro vs helicóptero)
2. **traffic_multiplier** - Visualização dos multiplicadores de tráfego
3. **time_breakdown** - Detalhamento dos componentes de tempo

## 🚀 Como Usar

### Dashboard
```bash
python -m http.server 8080
# Acesse http://localhost:8080/dashboard_v4.html
```

### Compilar Papers LaTeX
```bash
pdflatex paper_comparison_en.tex
pdflatex paper_comparison_pt.tex
```

### Compilar Apresentações Beamer
```bash
pdflatex presentation_en.tex
pdflatex presentation_pt.tex
```

## 🔍 Metodologia

### Cálculo de Tempo de Helicóptero
```
Tempo Total = Carro→Heliponto + Check-in(10min) + Voo + Transfer(10min)
```

### Cenários de Tráfego (baseado em Google Traffic)
- **Fast**: Multiplicador 1.0x (baseline OSRM)
- **Normal**: Multiplicador 1.25x
- **Rush**: Multiplicador 1.68x (horário de pico)
- **Worst**: Multiplicador 4.68x (pior cenário histórico - PESSIMISTA)

## 📅 Data de Geração
Dezembro 2025

## 📝 Changelog
- **v4.0**: Análise completa com cenário pessimista
- **v4.1**: Adicionados gráficos comparativos, diagramas, papers e apresentações
