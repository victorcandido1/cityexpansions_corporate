# 🌍 Conversão de Timezone - UTC para Horário Local

## ❓ Questão Original

**"No heatmap estamos usando o horário UTC ou o horário local de cada aeroporto?"**

---

## ✅ Resposta: HORÁRIO LOCAL

Os heatmaps foram **convertidos de UTC para horário local de cada aeroporto**.

---

## 🔄 Conversão Implementada

### Timezones dos Aeroportos

| Aeroporto | Código IATA | Timezone | UTC Offset |
|-----------|-------------|----------|------------|
| **New York JFK** | KJFK | America/New_York (EST/EDT) | UTC-5/-4 |
| **Los Angeles** | KLAX | America/Los_Angeles (PST/PDT) | UTC-8/-7 |
| **Chicago O'Hare** | KORD | America/Chicago (CST/CDT) | UTC-6/-5 |
| **Dallas/Fort Worth** | KDFW | America/Chicago (CST/CDT) | UTC-6/-5 |
| **San Francisco** | KSFO | America/Los_Angeles (PST/PDT) | UTC-8/-7 |
| **Houston** | KIAH | America/Chicago (CST/CDT) | UTC-6/-5 |

**Nota:** Os offsets variam entre horário padrão (Standard Time) e horário de verão (Daylight Time).

---

## 📊 Heatmaps Gerados

### 1. Por Hora do Dia (Local)
**Arquivo:** `heatmap_hour_local_sample.png`

- **Eixo X:** Hora do dia (0-23h) em horário LOCAL
- **Eixo Y:** Aeroporto
- **Cor:** Total de assentos premium
- **Interpretação:** Mostra os horários de PICO de chegadas/partidas de voos premium em cada aeroporto

### 2. Por Dia da Semana (Local)
**Arquivo:** `heatmap_day_local_sample.png`

- **Eixo X:** Dia da semana (Segunda a Domingo)
- **Eixo Y:** Aeroporto
- **Cor:** Total de assentos premium
- **Interpretação:** Identifica padrões semanais de voos premium

### 3. Padrão Horário
**Arquivo:** `hourly_pattern_sample.png`

- **Gráfico 1:** Total de assentos premium por hora
- **Gráfico 2:** Número de voos por hora
- **Interpretação:** Permite ver a curva de demanda ao longo do dia

---

## 💡 Por Que Horário Local é Importante?

### Razões Operacionais

1. **Planejamento de Frota:**
   - Helicópteros precisam estar disponíveis nos horários de pico LOCAL
   - Não faz sentido usar UTC para operações terrestres

2. **Turnos de Tripulação:**
   - Pilotos e equipe trabalham em horário local
   - Picos operacionais devem ser identificados em hora local

3. **Padrões de Demanda:**
   - Passageiros agem baseados em horário local
   - Um voo que chega às 18:00 LOCAL é "final do dia" independente do UTC

4. **Análise Comparativa:**
   - Permite comparar padrões entre aeroportos
   - Ex: Pico às 09:00 em todos os aeroportos significa algo similar em cada localidade

### Exemplo Prático

Um voo chegando às `22:00 UTC`:

| Aeroporto | Horário Local | Contexto |
|-----------|---------------|----------|
| **KJFK** (New York) | 17:00 EST | Final de tarde - rush hour |
| **KLAX** (Los Angeles) | 14:00 PST | Meio da tarde |
| **KDFW** (Dallas) | 16:00 CST | Tarde |

**Conclusão:** O mesmo horário UTC representa momentos MUITO diferentes do dia em cada aeroporto!

---

## 🔧 Método de Conversão

### Técnico

```python
# Para cada aeroporto
for airport, tz_name in AIRPORT_TIMEZONES.items():
    mask = df['query_airport'] == airport
    if mask.any():
        local_tz = pytz.timezone(tz_name)
        df.loc[mask, 'first_seen_local'] = df.loc[mask, 'first_seen'].dt.tz_convert(local_tz)
```

### Características

- ✅ **Automaticamente ajusta para DST** (Daylight Saving Time)
- ✅ **Preserva precisão temporal**
- ✅ **Operação vetorizada** (eficiente para grandes datasets)
- ✅ **Usa biblioteca pytz** (padrão da indústria)

---

## 📈 Insights dos Heatmaps (Amostra)

### Dallas/Fort Worth (KDFW)

**Horário de Pico:** 09:00 (hora local)

- **641,079 assentos premium**
- **10,796 voos**

**Interpretação:**
- Manhã é o período de maior movimentação
- Oportunidade para serviços de helicóptero matinais
- Helicópteros devem estar posicionados antes das 08:00

---

## 📁 Arquivos Disponíveis

### Heatmaps Completos (Todos os Dados)
- `heatmap_premium_seats_by_hour_local.png` - Todos os 3.1M voos

### Heatmaps de Amostra (100k voos)
- `heatmap_hour_local_sample.png` - Por hora do dia
- `heatmap_day_local_sample.png` - Por dia da semana
- `hourly_pattern_sample.png` - Padrão horário

### Scripts
- `create_premium_heatmaps.py` - Versão completa (3.1M voos)
- `create_premium_heatmaps_sample.py` - Versão rápida (100k voos)

---

## 🎯 Recomendações de Uso

### Para Análise Operacional
✅ **Use horário LOCAL** (o que fizemos)

- Planejamento de frota
- Turnos de tripulação
- Posicionamento de helicópteros
- Análise de demanda

### Para Análise Técnica/Log
❌ **Use UTC** somente para:

- Logs de sistema
- Sincronização entre sistemas
- Debugging técnico
- Compliance regulatório

---

## 🚀 Como Executar

### Versão Rápida (Recomendada para teste)
```bash
python create_premium_heatmaps_sample.py
# Processa 100k voos em ~30 segundos
```

### Versão Completa
```bash
python create_premium_heatmaps.py
# Processa 3.1M voos em ~10-15 minutos
```

---

## 📊 Próximas Análises Sugeridas

1. **Heatmap Hora × Dia da Semana**
   - Matriz 2D para cada aeroporto
   - Identificar padrões específicos (ex: sexta-feira à noite)

2. **Análise Sazonal**
   - Variação por mês
   - Impacto de feriados

3. **Rotas Específicas**
   - Horários de pico por rota internacional
   - Ex: Voos Europa → JFK vs. Ásia → LAX

4. **Correlação com Eventos**
   - Conferências/eventos em cada cidade
   - Impacto em padrões de voo

---

## ✅ Conclusão

**Os heatmaps estão em HORÁRIO LOCAL de cada aeroporto** ✨

Isso permite:
- ✅ Análise operacional precisa
- ✅ Planejamento de recursos
- ✅ Identificação de horários de pico reais
- ✅ Comparação significativa entre aeroportos

---

*Última atualização: Dezembro 2025*  
*Dados baseados em: 3.1 milhões de voos premium*

