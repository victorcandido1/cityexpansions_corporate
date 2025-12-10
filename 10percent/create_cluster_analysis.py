# -*- coding: utf-8 -*-
"""
ANÁLISE DE CLUSTERS - HOUSEHOLDS E CORPORATE
=============================================
Cria análise de clusters para identificar padrões geográficos e econômicos.

Clusters baseados em:
- Riqueza (AGI, Revenue)
- Densidade (HH200k, Employment)
- Distância ao aeroporto
- Características econômicas
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import json

print("\n" + "="*80)
print("ANÁLISE DE CLUSTERS - HOUSEHOLDS & CORPORATE")
print("="*80)

# =============================================================================
# LOAD DATA
# =============================================================================

print("\nCarregando dados...")
df_hh = pd.read_csv('top10_richest_data.csv')
df_corp = pd.read_csv('top10_corporate_data.csv')

print(f"  Households Top 10%: {len(df_hh)} ZIPs")
print(f"  Corporate Top 10%: {len(df_corp)} ZIPs")

# =============================================================================
# HOUSEHOLD CLUSTERS
# =============================================================================

print("\n" + "="*80)
print("HOUSEHOLD CLUSTERS (K-Means)")
print("="*80)

# Prepare features
hh_features = df_hh[['Households_200k', 'AGI_per_return', 'Travel_Time_Min']].copy()
hh_features = hh_features.fillna(hh_features.median())

# Standardize
scaler = StandardScaler()
hh_scaled = scaler.fit_transform(hh_features)

# K-Means clustering (4 clusters)
kmeans_hh = KMeans(n_clusters=4, random_state=42, n_init=10)
df_hh['cluster'] = kmeans_hh.fit_predict(hh_scaled)

# Analyze clusters
print("\nHousehold Clusters:")
for cluster_id in range(4):
    cluster_data = df_hh[df_hh['cluster'] == cluster_id]
    print(f"\n  Cluster {cluster_id + 1}: {len(cluster_data)} ZIPs")
    print(f"    Avg HH200k+: {cluster_data['Households_200k'].mean():,.0f}")
    print(f"    Avg AGI: ${cluster_data['AGI_per_return'].mean():,.0f}")
    print(f"    Avg Travel Time: {cluster_data['Travel_Time_Min'].mean():.1f} min")
    cities = cluster_data['city_name'].value_counts().head(3)
    print(f"    Top cities: {', '.join([f'{c} ({n})' for c, n in cities.items()])}")

# Label clusters
cluster_labels_hh = {
    0: "Ultra-Rich / Próximo",
    1: "Alta Renda / Distante",
    2: "Moderado / Central",
    3: "Elite / Subúrbio"
}

df_hh['cluster_name'] = df_hh['cluster'].map(cluster_labels_hh)

# Save
df_hh.to_csv('household_clusters.csv', index=False)
print("\n✓ Saved: household_clusters.csv")

# =============================================================================
# CORPORATE CLUSTERS
# =============================================================================

print("\n" + "="*80)
print("CORPORATE CLUSTERS (K-Means)")
print("="*80)

# Prepare features
corp_features = df_corp[['total_employment', 'estimated_revenue_M', 'distance_km']].copy()
corp_features = corp_features.fillna(corp_features.median())

# Standardize
scaler_corp = StandardScaler()
corp_scaled = scaler_corp.fit_transform(corp_features)

# K-Means clustering (4 clusters)
kmeans_corp = KMeans(n_clusters=4, random_state=42, n_init=10)
df_corp['cluster'] = kmeans_corp.fit_predict(corp_scaled)

# Analyze clusters
print("\nCorporate Clusters:")
for cluster_id in range(4):
    cluster_data = df_corp[df_corp['cluster'] == cluster_id]
    print(f"\n  Cluster {cluster_id + 1}: {len(cluster_data)} ZIPs")
    print(f"    Avg Employment: {cluster_data['total_employment'].mean():,.0f}")
    print(f"    Avg Revenue: ${cluster_data['estimated_revenue_M'].mean():,.0f}M")
    print(f"    Avg Distance: {cluster_data['distance_km'].mean():.1f} km")
    cities = cluster_data['city_key'].value_counts().head(3)
    print(f"    Top cities: {', '.join([f'{c} ({n})' for c, n in cities.items()])}")

# Label clusters
cluster_labels_corp = {
    0: "Mega Corporações",
    1: "Corporate Hub",
    2: "Empresas Médias",
    3: "Periferia Empresarial"
}

df_corp['cluster_name'] = df_corp['cluster'].map(cluster_labels_corp)

# Save
df_corp.to_csv('corporate_clusters.csv', index=False)
print("\n✓ Saved: corporate_clusters.csv")

# =============================================================================
# VISUALIZATION
# =============================================================================

print("\n" + "="*80)
print("CRIANDO VISUALIZAÇÕES")
print("="*80)

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Household clusters
ax1 = axes[0, 0]
for cluster_id in range(4):
    cluster_data = df_hh[df_hh['cluster'] == cluster_id]
    ax1.scatter(cluster_data['Travel_Time_Min'], cluster_data['AGI_per_return'], 
               s=cluster_data['Households_200k']/50, alpha=0.6, 
               label=cluster_labels_hh[cluster_id])
ax1.set_xlabel('Travel Time to Airport (min)', fontweight='bold')
ax1.set_ylabel('AGI per Return ($)', fontweight='bold')
ax1.set_title('Household Clusters', fontsize=14, fontweight='bold')
ax1.legend()
ax1.grid(alpha=0.3)

# Corporate clusters
ax2 = axes[0, 1]
for cluster_id in range(4):
    cluster_data = df_corp[df_corp['cluster'] == cluster_id]
    ax2.scatter(cluster_data['distance_km'], cluster_data['revenue_per_employee'], 
               s=cluster_data['total_employment']/100, alpha=0.6,
               label=cluster_labels_corp[cluster_id])
ax2.set_xlabel('Distance to Airport (km)', fontweight='bold')
ax2.set_ylabel('Revenue per Employee ($)', fontweight='bold')
ax2.set_title('Corporate Clusters', fontsize=14, fontweight='bold')
ax2.legend()
ax2.grid(alpha=0.3)

# Household cluster distribution by city
ax3 = axes[1, 0]
cluster_city = df_hh.groupby(['city_name', 'cluster_name']).size().unstack(fill_value=0)
cluster_city.plot(kind='bar', stacked=True, ax=ax3, colormap='Set3')
ax3.set_xlabel('City', fontweight='bold')
ax3.set_ylabel('Number of ZIPs', fontweight='bold')
ax3.set_title('Household Clusters by City', fontsize=14, fontweight='bold')
ax3.legend(title='Cluster', bbox_to_anchor=(1.05, 1))
ax3.grid(axis='y', alpha=0.3)
plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')

# Corporate cluster distribution by city
ax4 = axes[1, 1]
cluster_city_corp = df_corp.groupby(['city_name', 'cluster_name']).size().unstack(fill_value=0)
cluster_city_corp.plot(kind='bar', stacked=True, ax=ax4, colormap='Set2')
ax4.set_xlabel('City', fontweight='bold')
ax4.set_ylabel('Number of ZIPs', fontweight='bold')
ax4.set_title('Corporate Clusters by City', fontsize=14, fontweight='bold')
ax4.legend(title='Cluster', bbox_to_anchor=(1.05, 1))
ax4.grid(axis='y', alpha=0.3)
plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha='right')

plt.tight_layout()
plt.savefig('cluster_analysis.png', dpi=150, bbox_inches='tight')
print("✓ Saved: cluster_analysis.png")

print("\n" + "="*80)
print("ANÁLISE DE CLUSTERS COMPLETA!")
print("="*80)
print("\nArquivos gerados:")
print("  - household_clusters.csv")
print("  - corporate_clusters.csv")
print("  - cluster_analysis.png")
print()

