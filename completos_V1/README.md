# Análise de Viabilidade + Trânsito - USA

## Visão Geral

Este diretório contém scripts Python para gerar mapas interativos de viabilidade e trânsito para 7 regiões metropolitanas dos EUA.

## Estrutura de Arquivos

```
completos_V1/
├── v1_los_angeles.py     # Los Angeles (LAX)
├── v1_new_york.py        # New York (JFK)
├── v1_chicago.py         # Chicago (ORD)
├── v1_dallas.py          # Dallas (DFW)
├── v1_houston.py         # Houston (IAH)
├── v1_miami.py           # Miami (MIA)
├── v1_san_francisco.py   # San Francisco (SFO)
├── v1_usa_master.py      # Mapa Nacional (todas as cidades)
├── run_all.py            # Script para executar todos
└── README.md             # Este arquivo
```

## Score de Viabilidade

O score de viabilidade é calculado com base em 5 fatores:

| Fator | Peso | Fonte |
|-------|------|-------|
| Renda Domiciliar Mediana | 35% | Census B19013_001E |
| Valor do Imóvel | 35% | Zillow ZHVI |
| Total de Households | 15% | Census B11001_001E |
| Households $200k+ | 10% | Census B19001_017E |
| Educação Profissional | 5% | Census B15003_024E |

## Como Executar

### Requisitos

```bash
pip install pandas geopandas folium census requests geopy
```

### Executar uma cidade específica

```bash
cd completos_V1
python v1_los_angeles.py
```

### Executar todas as cidades

```bash
python run_all.py
```

### Mapas Gerados

Cada script gera um arquivo HTML interativo:

- `mapa_la_viabilidade_traffic.html`
- `mapa_ny_viabilidade_traffic.html`
- `mapa_chi_viabilidade_traffic.html`
- `mapa_dfw_viabilidade_traffic.html`
- `mapa_hou_viabilidade_traffic.html`
- `mapa_mia_viabilidade_traffic.html`
- `mapa_sfo_viabilidade_traffic.html`
- `mapa_usa_master_viabilidade_traffic.html`

## Dados de Trânsito

Os dados de trânsito estão na pasta `../traffic_data/` organizados por cidade:

```
traffic_data/
├── Los_Angeles/
├── New_York/ (arquivos na raiz com *JFK*.csv)
├── Chicago/
├── Dallas/
├── Houston/
├── Miami/
└── San_Francisco_Bay_Area/
```

## Aeroportos

| Cidade | Código | Aeroporto |
|--------|--------|-----------|
| Los Angeles | LAX | Los Angeles International |
| New York | JFK | John F. Kennedy International |
| Chicago | ORD | O'Hare International |
| Dallas | DFW | Dallas/Fort Worth International |
| Houston | IAH | George Bush Intercontinental |
| Miami | MIA | Miami International |
| San Francisco | SFO | San Francisco International |

## Cores do Mapa

### Score de Viabilidade (Choropleth)
- Verde escuro → Alto score
- Amarelo → Médio
- Vermelho → Baixo score

### Tempo de Viagem (Marcadores)
- 🟢 Verde: < 25 min
- 🟡 Verde claro: 25-35 min
- 🟠 Laranja: 35-45 min
- 🔴 Vermelho: 45-60 min
- 🟣 Vermelho escuro: > 60 min

