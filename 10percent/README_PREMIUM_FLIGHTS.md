# 📊 Análise de Voos Premium - Documentação

## 📁 Visão Geral

Esta análise identifica e quantifica o mercado de passageiros premium em voos widebody de longa duração (>5 horas) para avaliar o potencial de serviços de transporte terrestre por helicóptero da REVO.

---

## 🎯 Objetivo

Responder às seguintes questões estratégicas:

1. **Quantos passageiros premium** chegam diariamente em cada aeroporto principal dos EUA?
2. **Quais tipos de aeronaves** dominam os voos premium de longa distância?
3. **Qual o potencial de mercado** para conversão desses passageiros em clientes REVO?
4. **Quais aeroportos** devem ser priorizados para expansão?

---

## 📋 Critérios de Análise

### ✈️ Aeronaves Incluídas
**Apenas widebodies (fuselagem larga):**

- **Boeing:** 747, 767, 777, 787
- **Airbus:** A300, A310, A330, A340, A350, A380
- **McDonnell Douglas:** MD-11, DC-10
- **Outros:** IL-96, IL-86

### ⏱️ Duração de Voo
- **Mínimo:** 5 horas (18.000 segundos)
- **Razão:** Voos longos têm maior probabilidade de passageiros premium dispostos a pagar por transporte rápido ao destino final

### 💺 Classes Premium
- First Class
- Business Class
- Premium Economy

### 🛫 Aeroportos Analisados
- **KJFK** - New York JFK
- **KLAX** - Los Angeles International
- **KORD** - Chicago O'Hare
- **KDFW** - Dallas/Fort Worth
- **KSFO** - San Francisco International
- **KIAH** - Houston George Bush

---

## 🔧 Metodologia

### 1. Merge de Dados Voos × Cabines

O processo de merge foi implementado com fallback inteligente:

```
1. Match Direto (98.9%)
   ↓
   Por aircraft registration + type
   ↓
   Dados exatos de configuração de cabine

2. Média do Avião (1.1%)
   ↓
   Quando não há match exato
   ↓
   Usa média de configuração do tipo de avião na amostra
   ↓
   Exemplo: Se não há dados para um B789 específico,
            usa a média de todos os B789 na amostra

3. Cobertura Total
   ↓
   100% dos voos têm dados de cabine
   (direto ou estimado)
```

### 2. Filtros Aplicados

```python
# Pseudocódigo do processo de filtragem
for each flight in all_flights:
    if is_widebody(flight.aircraft_type):
        if flight.duration > 5_hours:
            if has_premium_seats(flight):
                add_to_premium_flights(flight)
```

### 3. Cálculo de Médias

Para cada tipo de avião, calculamos:

```
Média de Assentos = Σ(assentos_do_tipo) / N(voos_do_tipo)

Aplicado para:
- First Class
- Business Class
- Premium Economy
- Economy
- Total
```

---

## 📊 Resultados Principais

### Estatísticas Gerais

| Métrica | Valor | % |
|---------|-------|---|
| Total de voos analisados | 80.8 milhões | 100% |
| Voos widebody | 4.2 milhões | 5.2% |
| Voos > 5 horas | 4.8 milhões | 6.0% |
| **Voos premium (widebody + >5h)** | **3.1 milhões** | **3.9%** |
| Total de assentos premium | 197.6 milhões | - |

### Top 3 Aeroportos

| Rank | Aeroporto | Assentos Premium/Dia | Market Share |
|------|-----------|----------------------|--------------|
| 🥇 | **KJFK** - New York | 136,402 | 25.2% |
| 🥈 | **KLAX** - Los Angeles | 117,080 | 21.6% |
| 🥉 | **KORD** - Chicago | 101,301 | 18.7% |

### Top 3 Aviões

| Rank | Tipo | Nome | Voos | Média Premium |
|------|------|------|------|---------------|
| 🥇 | **B789** | Boeing 787-9 | 760,923 | 55.5 |
| 🥈 | **B77W** | Boeing 777-300ER | 479,043 | 66.2 |
| 🥉 | **B763** | Boeing 767-300ER | 465,052 | 33.3 |

---

## 📁 Arquivos Gerados

### Dados Processados

| Arquivo | Tamanho | Descrição |
|---------|---------|-----------|
| `premium_flights_analysis.csv` | ~870 MB | Dataset completo com 3.1M voos premium filtrados |
| `premium_top10_aircraft.csv` | 1 KB | Análise dos 10 aviões mais usados com médias de cabine |
| `premium_summary_by_airport.csv` | <1 KB | Sumário estatístico agregado por aeroporto |

### Relatórios

| Arquivo | Formato | Descrição |
|---------|---------|-----------|
| `premium_flights_report.html` | HTML | 📊 **Relatório visual interativo** (RECOMENDADO) |
| `PREMIUM_FLIGHTS_EXECUTIVE_SUMMARY.md` | Markdown | 📄 Sumário executivo com insights e recomendações |
| `README_PREMIUM_FLIGHTS.md` | Markdown | 📖 Esta documentação |

### Scripts

| Arquivo | Linguagem | Descrição |
|---------|-----------|-----------|
| `process_premium_flights.py` | Python | Script principal de processamento |

---

## 🚀 Como Usar

### Pré-requisitos

```bash
# Bibliotecas necessárias
pip install pandas numpy
```

### Executar Análise

```bash
# Navegar para o diretório
cd V3/new_folder

# Executar script
python process_premium_flights.py
```

### Visualizar Resultados

1. **Relatório HTML (Recomendado):**
   - Abrir `premium_flights_report.html` no navegador
   - Visualização interativa com gráficos e tabelas

2. **Sumário Executivo:**
   - Ler `PREMIUM_FLIGHTS_EXECUTIVE_SUMMARY.md`
   - Insights estratégicos e recomendações

3. **Dados Brutos:**
   - Abrir CSVs no Excel/Python/R para análises customizadas

---

## 💡 Insights Principais

### 🏆 Dominância do Boeing 787
- Variantes do 787 (789, 788, 78X) representam **1.25 milhões** de voos premium
- B789 sozinho: **760,923 voos** (24% do total)
- Boeing 787-10 (B78X) tem a maior média de assentos premium: **141.8**

### 🗽 New York JFK é o Maior Mercado
- **136,402 assentos premium/dia**
- 25.2% do mercado total
- 20 tipos diferentes de widebodies operando

### 📈 Potencial de Conversão
Mesmo com taxa conservadora de **0.1%**:
- JFK: 136 passageiros/dia = **$14.9M/ano** (@ $300/trajeto)
- LAX: 117 passageiros/dia = **$12.8M/ano**
- ORD: 101 passageiros/dia = **$11.1M/ano**

---

## 🎯 Recomendações Estratégicas

### Prioridade de Expansão

#### 🥇 Prioridade 1: New York JFK
- ✅ Maior mercado (136k assentos/dia)
- ✅ Infraestrutura de heliporto estabelecida
- ✅ Base corporativa consolidada
- ✅ Tráfego terrestre severo

#### 🥈 Prioridade 2: Los Angeles LAX
- ✅ Segundo maior mercado (117k assentos/dia)
- ✅ Cultura de helicóptero estabelecida
- ✅ Geografia dispersa favorece aéreo
- ✅ Mix entretenimento + negócios

#### 🥉 Prioridade 3: Chicago ORD
- ✅ Terceiro maior mercado (101k assentos/dia)
- ✅ Maior média de assentos/voo (90.8)
- ✅ Hub central dos EUA
- ✅ Forte presença corporativa

---

## 📊 Estrutura dos Dados

### premium_flights_analysis.csv

Colunas principais:

```
- query_airport: Aeroporto de origem/destino
- aircraft_type: Tipo ICAO da aeronave (ex: B789, B77W)
- aircraft_registration: Matrícula do avião
- flight_time_seconds: Duração do voo em segundos
- is_widebody: Boolean - é widebody?
- flight_duration_ok: Boolean - duração > 5h?
- first_class_seats: Número de assentos first class
- business_class_seats: Número de assentos business
- premium_economy_seats: Número de assentos premium economy
- economy_seats: Número de assentos economy
- total_seats: Total de assentos
- premium_seats: Total premium (first + business + premium economy)
```

### premium_top10_aircraft.csv

Colunas:

```
- aircraft_type: Tipo ICAO
- n_flights: Número de voos
- premium_seats: Média de assentos premium
- first_class_seats: Média first class
- business_class_seats: Média business
- premium_economy_seats: Média premium economy
- economy_seats: Média economy
- total_seats: Média total
```

### premium_summary_by_airport.csv

Colunas:

```
- query_airport: Código ICAO do aeroporto
- n_flights: Número total de voos premium
- total_premium_seats: Total de assentos premium
- avg_premium_seats: Média de assentos premium por voo
- n_aircraft_types: Número de tipos diferentes de aeronaves
```

---

## 🔄 Próximos Passos

### Análises Sugeridas

1. **Análise Temporal:**
   - Distribuição por hora do dia
   - Sazonalidade (mês/trimestre)
   - Dias da semana vs. fins de semana

2. **Análise de Rotas:**
   - Top rotas internacionais por aeroporto
   - Concentração por região de origem
   - Identificar rotas premium específicas

3. **Perfil de Passageiro:**
   - Cruzamento com dados demográficos
   - Identificar empresas com maior volume
   - Padrões de viagem corporativa

4. **Análise Competitiva:**
   - Mapeamento de serviços existentes
   - Tempos de viagem terrestres
   - Cálculo de time savings

5. **Modelagem Financeira:**
   - Estrutura de preços por mercado
   - Custos operacionais detalhados
   - Análise de breakeven

---

## 📞 Suporte

Para dúvidas ou sugestões sobre esta análise:

- **Email:** strategy@revo.com
- **Slack:** #data-analytics
- **Documentação:** Este arquivo

---

## 📝 Changelog

### v1.0 - Dezembro 2025
- ✅ Implementação inicial
- ✅ Filtros de widebody + duração > 5h
- ✅ Merge inteligente com fallback para médias
- ✅ Análise dos top 10 aviões
- ✅ Sumário por aeroporto
- ✅ Relatório HTML interativo
- ✅ Documentação completa

---

## 📄 Licença

© 2025 REVO Helicopter Services  
Uso interno apenas - Confidencial

---

*Última atualização: Dezembro 2025*  
*Dados baseados em: 80.8 milhões de voos reais*

