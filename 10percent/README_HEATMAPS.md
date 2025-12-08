# Heatmaps de Voos Premium - Atualização

## Mudanças Implementadas

### 1. **Horário Local (não UTC)**
- Todos os heatmaps agora usam **horário local** de cada aeroporto
- Conversão automática de UTC para timezone local:
  - JFK (New York): Eastern Time (UTC-5/-4)
  - LAX (Los Angeles): Pacific Time (UTC-8/-7)
  - ORD (Chicago): Central Time (UTC-6/-5)
  - DFW (Dallas): Central Time (UTC-6/-5)
  - SFO (San Francisco): Pacific Time (UTC-8/-7)
  - IAH (Houston): Central Time (UTC-6/-5)

### 2. **Nova Estrutura dos Heatmaps**
- **Eixo X**: Horas do dia (00h - 23h) - horário local
- **Eixo Y**: Dias da semana (Mon, Tue, Wed, Thu, Fri, Sat, Sun)
- **Valores**: Média de assentos premium por dia/hora
- **Separação**: DEPARTURES e ARRIVALS em gráficos lado a lado

### 3. **Arquivos Gerados**
Para cada aeroporto, são gerados:
- `heatmap_kjfk_departures_arrivals.png` - New York JFK
- `heatmap_klax_departures_arrivals.png` - Los Angeles
- `heatmap_kord_departures_arrivals.png` - Chicago ORD
- `heatmap_kdfw_departures_arrivals.png` - Dallas DFW
- `heatmap_ksfo_departures_arrivals.png` - San Francisco
- `heatmap_kiah_departures_arrivals.png` - Houston IAH

## Como Usar

### Opção 1: Processar Amostra (Rápido - 100k voos)
```bash
cd "G:\Meu Drive\Journey\Modelos\Revo\Strategy\Expansion_v2\GeoEco\v1\10percent"
python create_premium_heatmaps_sample.py
```

**Tempo estimado**: 1-2 minutos
**Arquivos gerados**: `heatmap_*_departures_arrivals_sample.png`

### Opção 2: Processar Todos os Dados (Completo)
```bash
cd "G:\Meu Drive\Journey\Modelos\Revo\Strategy\Expansion_v2\GeoEco\v1\10percent"
python create_premium_heatmaps.py
```

**Tempo estimado**: 5-10 minutos (dependendo do volume de dados)
**Arquivos gerados**: `heatmap_*_departures_arrivals.png`

## Pré-requisitos

1. **Dados de Voos Processados**: 
   - Arquivo `premium_flights_analysis.csv` deve existir
   - Se não existir, execute primeiro: `python process_premium_flights.py`

2. **Bibliotecas Python**:
   ```bash
   pip install pandas numpy matplotlib seaborn pytz
   ```

## Estrutura dos Heatmaps

### DEPARTURES (Partidas)
- Mostra assentos premium em voos que **saem** do aeroporto
- Baseado na coluna `direction` ou `orig_icao`

### ARRIVALS (Chegadas)
- Mostra assentos premium em voos que **chegam** ao aeroporto
- Baseado na coluna `direction` ou `dest_icao`

### Interpretação das Cores
- **Amarelo claro**: Baixa quantidade de assentos premium
- **Laranja**: Quantidade média
- **Vermelho escuro**: Alta quantidade de assentos premium (horários de pico)

## Exemplo de Insights

Os heatmaps revelam:
- **Horários de pico**: Quando há mais voos premium
- **Padrões semanais**: Diferenças entre dias úteis e fins de semana
- **Diferenças dep/arr**: Assimetrias entre partidas e chegadas
- **Concentração temporal**: Janelas de oportunidade para operações

## Troubleshooting

### Erro: "Arquivo não encontrado"
Execute primeiro o processamento de dados:
```bash
python process_premium_flights.py
```

### Gráficos vazios ou zeros
Verifique se:
1. Os dados têm a coluna `direction` ou `orig_icao`/`dest_icao`
2. O aeroporto tem voos no dataset
3. Os voos foram corretamente classificados como premium (widebody + >5h)

### Problemas com timezone
- O código detecta automaticamente o timezone de cada aeroporto
- Se adicionar novos aeroportos, atualizar o dicionário `AIRPORT_TIMEZONES`

## Contato

Para dúvidas ou sugestões sobre os heatmaps, consulte a documentação completa do projeto.

