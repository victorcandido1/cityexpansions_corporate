# Gated Communities - Adição aos Mapas de Cluster

## Resumo

Foram adicionadas **30 comunidades privadas (gated communities)** aos mapas de análise de clusters para Nova York e Los Angeles, categorizadas por distância do centro da cidade e tipo de serviço requerido.

---

## 📊 Dados Incluídos

### Arquivo de Dados: `gated_communities.csv`

Contém 30 comunidades premium com as seguintes informações:
- Nome da comunidade
- Cidade
- Estado
- Coordenadas (latitude/longitude)
- Categoria de raio (0-50km, 50-100km, 100-200km)

---

## 🗽 Nova York (11 comunidades)

### 0-50km de Raio do Centro da Cidade
**Serviço:** Standard (helicóptero/carro de luxo)

1. **Manhasset Crest, Long Island**
   - Coordenadas: 40.7831°N, 73.6995°W
   - Icone: 🟢 Verde

2. **The Greens at Cherry Lawn, New Rochelle**
   - Coordenadas: 40.9217°N, 73.7826°W
   - Icone: 🟢 Verde

3. **Cobblefield Community, White Plains**
   - Coordenadas: 41.0340°N, 73.7629°W
   - Icone: 🟢 Verde

### 50-100km de Raio do Centro da Cidade
**Serviço:** Shuttle/Full Cabin

4. **Stonebridge Country Club, Suffolk Country, Long Island**
   - Coordenadas: 40.8700°N, 73.0500°W
   - Icone: 🟠 Laranja

5. **Tuxedo Park**
   - Coordenadas: 41.1967°N, 74.1982°W
   - Icone: 🟠 Laranja

### 100-200km de Raio do Centro da Cidade
**Serviço:** Charter (voo fretado completo)

6. **Meadow Lane, Southampton, NY**
   - Coordenadas: 40.8838°N, 72.3915°W
   - Icone: 🔴 Vermelho Escuro

7. **Sagaponack South, NY**
   - Coordenadas: 40.9331°N, 72.2825°W
   - Icone: 🔴 Vermelho Escuro

8. **Shelter Island**
   - Coordenadas: 41.0642°N, 72.3398°W
   - Icone: 🔴 Vermelho Escuro

9. **Sag Harbor, NY**
   - Coordenadas: 41.0001°N, 72.2926°W
   - Icone: 🔴 Vermelho Escuro

10. **Fishers Island, NY**
    - Coordenadas: 41.2631°N, 71.9623°W
    - Icone: 🔴 Vermelho Escuro

11. **Indian Neck, NY**
    - Coordenadas: 40.9517°N, 72.5198°W
    - Icone: 🔴 Vermelho Escuro

---

## 🌴 Los Angeles (19 comunidades)

### 0-50km de Raio do Centro da Cidade
**Serviço:** Standard (helicóptero/carro de luxo)

1. **Palos Verdes Peninsula**
   - Coordenadas: 33.7446°N, 118.3874°W
   - Icone: 🟢 Verde

2. **Laughlin Park**
   - Coordenadas: 34.1069°N, 118.2978°W
   - Icone: 🟢 Verde

3. **Brentwood Park**
   - Coordenadas: 34.0607°N, 118.4734°W
   - Icone: 🟢 Verde

4. **Moraga Estates**
   - Coordenadas: 34.0522°N, 118.3437°W
   - Icone: 🟢 Verde

5. **South Beverly Park**
   - Coordenadas: 34.0599°N, 118.4123°W
   - Icone: 🟢 Verde

6. **North Beverly Park**
   - Coordenadas: 34.0876°N, 118.4123°W
   - Icone: 🟢 Verde

7. **Mulholland Estates**
   - Coordenadas: 34.1008°N, 118.3815°W
   - Icone: 🟢 Verde

8. **The Summit, Beverly Hills**
   - Coordenadas: 34.0736°N, 118.4000°W
   - Icone: 🟢 Verde

9. **Malibu Colony**
   - Coordenadas: 34.0345°N, 118.6787°W
   - Icone: 🟢 Verde

10. **The Oaks of Calabasas**
    - Coordenadas: 34.1394°N, 118.6395°W
    - Icone: 🟢 Verde

11. **Hidden Hills**
    - Coordenadas: 34.1625°N, 118.6557°W
    - Icone: 🟢 Verde

12. **Bell Canyon**
    - Coordenadas: 34.2267°N, 118.6492°W
    - Icone: 🟢 Verde

13. **Porter Ranch**
    - Coordenadas: 34.2728°N, 118.5370°W
    - Icone: 🟢 Verde

### 50-100km de Raio do Centro da Cidade
**Serviço:** Shuttle/Full Cabin

14. **Sherwood Country Club**
    - Coordenadas: 34.1738°N, 118.9634°W
    - Icone: 🟠 Laranja

15. **Laguna Beach**
    - Coordenadas: 33.5427°N, 117.7854°W
    - Icone: 🟠 Laranja

### 100-200km de Raio do Centro da Cidade
**Serviço:** Charter (voo fretado completo)

16. **Santa Barbara**
    - Coordenadas: 34.4208°N, 119.6982°W
    - Icone: 🔴 Vermelho Escuro

17. **Solvang**
    - Coordenadas: 34.5958°N, 120.1379°W
    - Icone: 🔴 Vermelho Escuro

18. **Palm Springs**
    - Coordenadas: 33.8303°N, 116.5453°W
    - Icone: 🔴 Vermelho Escuro

19. **Temecula**
    - Coordenadas: 33.4936°N, 117.1484°W
    - Icone: 🔴 Vermelho Escuro

---

## 🗺️ Mapas Gerados

### Novos Arquivos HTML Interativos

1. **`map_cluster_airports_new_york_with_gated.html`**
   - Mapa de Nova York com 11 comunidades privadas
   - Camadas separadas por categoria de distância
   - Tooltips interativos com detalhes de cada comunidade

2. **`map_cluster_airports_los_angeles_with_gated.html`**
   - Mapa de Los Angeles com 19 comunidades privadas
   - Camadas separadas por categoria de distância
   - Tooltips interativos com detalhes de cada comunidade

### Recursos dos Mapas

✅ **Camadas Controláveis:**
- ZIP Clusters (análise de clusters existente)
- Aeroportos (ícone de avião vermelho)
- Heliportos (ícone de helicóptero azul)
- **🆕 Gated Communities 0-50km** (ícone casa verde)
- **🆕 Gated Communities 50-100km** (ícone casa laranja)
- **🆕 Gated Communities 100-200km** (ícone casa vermelha)

✅ **Popups Informativos:**
Cada marcador de comunidade mostra:
- Nome da comunidade
- Cidade e Estado
- Categoria de serviço
- Coordenadas exatas

✅ **Legendas:**
- Legenda explicativa dos tipos de serviço por distância
- Cores codificadas para fácil identificação

---

## 🚀 Como Executar

### Gerar/Atualizar Mapas com Gated Communities

```bash
cd "v1/10percent"
python add_gated_communities_to_maps.py
```

### Saída Esperada:
```
================================================================================
ADDING GATED COMMUNITIES TO CLUSTER MAPS
================================================================================

PROCESSING: NEW YORK
  ZIPs in New York: 70
  Gated Communities in New York: 11
  [✓] Saved map: map_cluster_airports_new_york_with_gated.html

PROCESSING: LOS ANGELES
  ZIPs in Los Angeles: 44
  Gated Communities in Los Angeles: 19
  [✓] Saved map: map_cluster_airports_los_angeles_with_gated.html
```

---

## 📈 Insights Estratégicos

### Nova York - Padrões Observados

**Alta Concentração em Hamptons (100-200km):**
- 6 das 11 comunidades estão na região de Hamptons
- Distância ideal para serviços charter
- Mercado de fim de semana e verão
- Alto poder aquisitivo, demanda sazonal

**Oportunidades:**
- Shuttle regular para Hamptons durante alta temporada (Memorial Day - Labor Day)
- Parcerias com heliportos locais (East Hampton, Southampton)
- Rotas charter sob demanda para residentes permanentes

### Los Angeles - Padrões Observados

**Cluster Denso em Beverly Hills/Brentwood (0-50km):**
- 13 das 19 comunidades dentro de 50km
- Concentração em Beverly Hills, Brentwood, Hidden Hills
- Proximidade com múltiplos heliportos
- Demanda year-round para LAX

**Oportunidades:**
- Serviço de shuttle compartilhado para múltiplas comunidades
- Hub operacional em Van Nuys Airport (heliporto próximo)
- Rotas premium para Palm Springs e Santa Barbara (fim de semana)

---

## 🎯 Aplicações de Negócio

### 1. Planejamento de Rotas
- Identificar rotas de alta demanda baseadas em densidade de comunidades
- Otimizar localização de heliportos/pontos de embarque
- Calcular frequência ideal de serviços por zona

### 2. Análise de Mercado Addressable
- **NY:** 6 comunidades charter + 2 shuttle + 3 standard = mercado estratificado
- **LA:** 13 comunidades standard + 2 shuttle + 4 charter = foco em proximidade

### 3. Precificação Dinâmica
- Diferentes modelos por categoria de distância
- Ajustes sazonais (Hamptons verão, Palm Springs inverno)
- Pacotes compartilhados vs. exclusivos

### 4. Marketing e Parcerias
- Parcerias com associações de residentes
- Programas de fidelidade por comunidade
- Marketing geolocalizado

---

## 📝 Próximos Passos

### Expansão Sugerida

1. **Adicionar outras cidades:**
   - Chicago: North Shore communities, Lake Forest
   - Miami: Fisher Island, Star Island, Palm Beach
   - San Francisco: Atherton, Woodside, Ross
   - Dallas: Highland Park, University Park
   - Houston: River Oaks, Memorial

2. **Dados Adicionais:**
   - Número estimado de residências por comunidade
   - Faixa de valor médio das propriedades
   - População estimada
   - Heliportos privados dentro das comunidades

3. **Análise Avançada:**
   - Heatmaps de densidade de comunidades
   - Análise de acessibilidade a aeroportos privados (FBOs)
   - Correlação com tráfego aéreo executivo existente
   - Análise de concorrência (serviços existentes)

---

## 📚 Referências

### Arquivos Relacionados

- **Dados:** `gated_communities.csv`
- **Script:** `add_gated_communities_to_maps.py`
- **Mapas:** `map_cluster_airports_{city}_with_gated.html`
- **Documentação Principal:** `CLUSTER_ANALYSIS_README.md`

### Metodologia

As coordenadas das comunidades foram obtidas através de:
- Endereços oficiais das comunidades
- Google Maps API / Geocoding
- Verificação manual de precisão

---

**Última Atualização:** Dezembro 10, 2025  
**Versão:** 1.0  
**Status:** ✅ Implementado para NY e LA

