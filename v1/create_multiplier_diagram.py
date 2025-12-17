#!/usr/bin/env python3
"""
Create diagrams explaining traffic multiplier calculation methodology
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# Set style
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10

def create_methodology_diagram_en():
    """Create methodology flow diagram in English"""
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Title
    ax.text(7, 9.5, 'Traffic Multiplier Calculation Methodology', 
            fontsize=16, fontweight='bold', ha='center', color='#2c3e50')
    
    # Step 1: Google Traffic Data
    box1 = FancyBboxPatch((0.5, 7), 4, 1.8, boxstyle="round,pad=0.05",
                          facecolor='#3498db', edgecolor='#2980b9', linewidth=2)
    ax.add_patch(box1)
    ax.text(2.5, 8.1, 'Step 1: Google Traffic API', fontsize=11, fontweight='bold', 
            ha='center', color='white')
    ax.text(2.5, 7.6, 'Historical data (pessimistic)', fontsize=9, ha='center', color='white')
    ax.text(2.5, 7.25, 'Multiple routes per city', fontsize=9, ha='center', color='white')
    
    # Step 2: Data Collection
    box2 = FancyBboxPatch((5.5, 7), 4, 1.8, boxstyle="round,pad=0.05",
                          facecolor='#9b59b6', edgecolor='#8e44ad', linewidth=2)
    ax.add_patch(box2)
    ax.text(7.5, 8.1, 'Step 2: Data Collected', fontsize=11, fontweight='bold', 
            ha='center', color='white')
    ax.text(7.5, 7.6, 'duration_min (baseline)', fontsize=9, ha='center', color='white')
    ax.text(7.5, 7.25, 'duration_pessimistic_min', fontsize=9, ha='center', color='white')
    
    # Step 3: Calculate Multipliers
    box3 = FancyBboxPatch((10.5, 7), 3, 1.8, boxstyle="round,pad=0.05",
                          facecolor='#e74c3c', edgecolor='#c0392b', linewidth=2)
    ax.add_patch(box3)
    ax.text(12, 8.1, 'Step 3: Calculate', fontsize=11, fontweight='bold', 
            ha='center', color='white')
    ax.text(12, 7.5, 'Multiplier =', fontsize=9, ha='center', color='white')
    ax.text(12, 7.15, 'Pessimistic / Baseline', fontsize=9, ha='center', color='white')
    
    # Arrows between steps
    ax.annotate('', xy=(5.4, 7.9), xytext=(4.6, 7.9),
                arrowprops=dict(arrowstyle='->', color='#34495e', lw=2))
    ax.annotate('', xy=(10.4, 7.9), xytext=(9.6, 7.9),
                arrowprops=dict(arrowstyle='->', color='#34495e', lw=2))
    
    # Example Box - NY
    box_ny = FancyBboxPatch((0.5, 3.5), 6, 3, boxstyle="round,pad=0.05",
                            facecolor='#ecf0f1', edgecolor='#1a5276', linewidth=2)
    ax.add_patch(box_ny)
    ax.text(3.5, 6.1, 'NEW YORK Example', fontsize=12, fontweight='bold', 
            ha='center', color='#1a5276')
    
    # NY calculation steps
    ax.text(1, 5.5, 'Sample route: Manhattan to JFK', fontsize=9, color='#2c3e50')
    ax.text(1, 5.1, 'Baseline time: 47 min', fontsize=9, color='#2c3e50')
    ax.text(1, 4.7, 'Pessimistic time: 245 min', fontsize=9, color='#2c3e50')
    ax.text(1, 4.2, 'Multiplier = 245 / 47 = 5.21x', fontsize=10, fontweight='bold', color='#e74c3c')
    ax.text(1, 3.8, 'Average across all routes: 5.20x', fontsize=9, color='#27ae60', fontweight='bold')
    
    # Example Box - LA
    box_la = FancyBboxPatch((7.5, 3.5), 6, 3, boxstyle="round,pad=0.05",
                            facecolor='#ecf0f1', edgecolor='#e67e22', linewidth=2)
    ax.add_patch(box_la)
    ax.text(10.5, 6.1, 'LOS ANGELES Example', fontsize=12, fontweight='bold', 
            ha='center', color='#e67e22')
    
    # LA calculation steps
    ax.text(8, 5.5, 'Sample route: Beverly Hills to LAX', fontsize=9, color='#2c3e50')
    ax.text(8, 5.1, 'Baseline time: 36 min', fontsize=9, color='#2c3e50')
    ax.text(8, 4.7, 'Pessimistic time: 149 min', fontsize=9, color='#2c3e50')
    ax.text(8, 4.2, 'Multiplier = 149 / 36 = 4.14x', fontsize=10, fontweight='bold', color='#e74c3c')
    ax.text(8, 3.8, 'Average across all routes: 4.15x', fontsize=9, color='#27ae60', fontweight='bold')
    
    # Final Results Box
    box_results = FancyBboxPatch((2, 0.5), 10, 2.5, boxstyle="round,pad=0.05",
                                 facecolor='#27ae60', edgecolor='#1e8449', linewidth=3)
    ax.add_patch(box_results)
    ax.text(7, 2.6, 'FINAL CITY-SPECIFIC MULTIPLIERS', fontsize=13, fontweight='bold', 
            ha='center', color='white')
    
    # Results table
    ax.text(4.5, 2, 'New York', fontsize=11, fontweight='bold', ha='center', color='white')
    ax.text(4.5, 1.5, 'Fast: 1.00x', fontsize=9, ha='center', color='white')
    ax.text(4.5, 1.15, 'Normal: 1.35x', fontsize=9, ha='center', color='white')
    ax.text(4.5, 0.8, 'Worst: 5.20x', fontsize=10, ha='center', color='white', fontweight='bold')
    
    ax.text(9.5, 2, 'Los Angeles', fontsize=11, fontweight='bold', ha='center', color='white')
    ax.text(9.5, 1.5, 'Fast: 1.00x', fontsize=9, ha='center', color='white')
    ax.text(9.5, 1.15, 'Normal: 1.42x', fontsize=9, ha='center', color='white')
    ax.text(9.5, 0.8, 'Worst: 4.15x', fontsize=10, ha='center', color='white', fontweight='bold')
    
    # Divider
    ax.axvline(x=7, ymin=0.08, ymax=0.27, color='white', linewidth=2, linestyle='--')
    
    plt.tight_layout()
    plt.savefig('diagrams/multiplier_methodology_en.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("[OK] Created: diagrams/multiplier_methodology_en.png")


def create_methodology_diagram_pt():
    """Create methodology flow diagram in Portuguese"""
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Title
    ax.text(7, 9.5, 'Metodologia de Calculo dos Multiplicadores de Trafego', 
            fontsize=16, fontweight='bold', ha='center', color='#2c3e50')
    
    # Step 1: Google Traffic Data
    box1 = FancyBboxPatch((0.5, 7), 4, 1.8, boxstyle="round,pad=0.05",
                          facecolor='#3498db', edgecolor='#2980b9', linewidth=2)
    ax.add_patch(box1)
    ax.text(2.5, 8.1, 'Passo 1: Google Traffic API', fontsize=11, fontweight='bold', 
            ha='center', color='white')
    ax.text(2.5, 7.6, 'Dados historicos (pessimista)', fontsize=9, ha='center', color='white')
    ax.text(2.5, 7.25, 'Multiplas rotas por cidade', fontsize=9, ha='center', color='white')
    
    # Step 2: Data Collection
    box2 = FancyBboxPatch((5.5, 7), 4, 1.8, boxstyle="round,pad=0.05",
                          facecolor='#9b59b6', edgecolor='#8e44ad', linewidth=2)
    ax.add_patch(box2)
    ax.text(7.5, 8.1, 'Passo 2: Dados Coletados', fontsize=11, fontweight='bold', 
            ha='center', color='white')
    ax.text(7.5, 7.6, 'duracao_min (base)', fontsize=9, ha='center', color='white')
    ax.text(7.5, 7.25, 'duracao_pessimista_min', fontsize=9, ha='center', color='white')
    
    # Step 3: Calculate Multipliers
    box3 = FancyBboxPatch((10.5, 7), 3, 1.8, boxstyle="round,pad=0.05",
                          facecolor='#e74c3c', edgecolor='#c0392b', linewidth=2)
    ax.add_patch(box3)
    ax.text(12, 8.1, 'Passo 3: Calcular', fontsize=11, fontweight='bold', 
            ha='center', color='white')
    ax.text(12, 7.5, 'Multiplicador =', fontsize=9, ha='center', color='white')
    ax.text(12, 7.15, 'Pessimista / Base', fontsize=9, ha='center', color='white')
    
    # Arrows between steps
    ax.annotate('', xy=(5.4, 7.9), xytext=(4.6, 7.9),
                arrowprops=dict(arrowstyle='->', color='#34495e', lw=2))
    ax.annotate('', xy=(10.4, 7.9), xytext=(9.6, 7.9),
                arrowprops=dict(arrowstyle='->', color='#34495e', lw=2))
    
    # Example Box - NY
    box_ny = FancyBboxPatch((0.5, 3.5), 6, 3, boxstyle="round,pad=0.05",
                            facecolor='#ecf0f1', edgecolor='#1a5276', linewidth=2)
    ax.add_patch(box_ny)
    ax.text(3.5, 6.1, 'Exemplo NOVA YORK', fontsize=12, fontweight='bold', 
            ha='center', color='#1a5276')
    
    # NY calculation steps
    ax.text(1, 5.5, 'Rota exemplo: Manhattan para JFK', fontsize=9, color='#2c3e50')
    ax.text(1, 5.1, 'Tempo base: 47 min', fontsize=9, color='#2c3e50')
    ax.text(1, 4.7, 'Tempo pessimista: 245 min', fontsize=9, color='#2c3e50')
    ax.text(1, 4.2, 'Multiplicador = 245 / 47 = 5.21x', fontsize=10, fontweight='bold', color='#e74c3c')
    ax.text(1, 3.8, 'Media de todas as rotas: 5.20x', fontsize=9, color='#27ae60', fontweight='bold')
    
    # Example Box - LA
    box_la = FancyBboxPatch((7.5, 3.5), 6, 3, boxstyle="round,pad=0.05",
                            facecolor='#ecf0f1', edgecolor='#e67e22', linewidth=2)
    ax.add_patch(box_la)
    ax.text(10.5, 6.1, 'Exemplo LOS ANGELES', fontsize=12, fontweight='bold', 
            ha='center', color='#e67e22')
    
    # LA calculation steps
    ax.text(8, 5.5, 'Rota exemplo: Beverly Hills para LAX', fontsize=9, color='#2c3e50')
    ax.text(8, 5.1, 'Tempo base: 36 min', fontsize=9, color='#2c3e50')
    ax.text(8, 4.7, 'Tempo pessimista: 149 min', fontsize=9, color='#2c3e50')
    ax.text(8, 4.2, 'Multiplicador = 149 / 36 = 4.14x', fontsize=10, fontweight='bold', color='#e74c3c')
    ax.text(8, 3.8, 'Media de todas as rotas: 4.15x', fontsize=9, color='#27ae60', fontweight='bold')
    
    # Final Results Box
    box_results = FancyBboxPatch((2, 0.5), 10, 2.5, boxstyle="round,pad=0.05",
                                 facecolor='#27ae60', edgecolor='#1e8449', linewidth=3)
    ax.add_patch(box_results)
    ax.text(7, 2.6, 'MULTIPLICADORES FINAIS POR CIDADE', fontsize=13, fontweight='bold', 
            ha='center', color='white')
    
    # Results table
    ax.text(4.5, 2, 'Nova York', fontsize=11, fontweight='bold', ha='center', color='white')
    ax.text(4.5, 1.5, 'Rapido: 1.00x', fontsize=9, ha='center', color='white')
    ax.text(4.5, 1.15, 'Normal: 1.35x', fontsize=9, ha='center', color='white')
    ax.text(4.5, 0.8, 'Pior: 5.20x', fontsize=10, ha='center', color='white', fontweight='bold')
    
    ax.text(9.5, 2, 'Los Angeles', fontsize=11, fontweight='bold', ha='center', color='white')
    ax.text(9.5, 1.5, 'Rapido: 1.00x', fontsize=9, ha='center', color='white')
    ax.text(9.5, 1.15, 'Normal: 1.42x', fontsize=9, ha='center', color='white')
    ax.text(9.5, 0.8, 'Pior: 4.15x', fontsize=10, ha='center', color='white', fontweight='bold')
    
    # Divider
    ax.axvline(x=7, ymin=0.08, ymax=0.27, color='white', linewidth=2, linestyle='--')
    
    plt.tight_layout()
    plt.savefig('diagrams/multiplier_methodology_pt.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("[OK] Created: diagrams/multiplier_methodology_pt.png")


def create_google_api_diagram_en():
    """Create diagram showing Google API data flow"""
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis('off')
    
    ax.text(6, 7.5, 'Google Distance Matrix API - Data Collection', 
            fontsize=14, fontweight='bold', ha='center', color='#2c3e50')
    
    # API Request Box
    box_req = FancyBboxPatch((0.5, 5), 5, 2, boxstyle="round,pad=0.05",
                             facecolor='#3498db', edgecolor='#2980b9', linewidth=2)
    ax.add_patch(box_req)
    ax.text(3, 6.5, 'API Request Parameters', fontsize=11, fontweight='bold', 
            ha='center', color='white')
    ax.text(3, 6, 'origin: ZIP code centroid', fontsize=9, ha='center', color='white')
    ax.text(3, 5.6, 'destination: JFK/LAX Airport', fontsize=9, ha='center', color='white')
    ax.text(3, 5.2, 'traffic_model: pessimistic', fontsize=9, ha='center', color='white')
    
    # API Response Box
    box_resp = FancyBboxPatch((6.5, 5), 5, 2, boxstyle="round,pad=0.05",
                              facecolor='#27ae60', edgecolor='#1e8449', linewidth=2)
    ax.add_patch(box_resp)
    ax.text(9, 6.5, 'API Response Data', fontsize=11, fontweight='bold', 
            ha='center', color='white')
    ax.text(9, 6, 'duration: baseline time', fontsize=9, ha='center', color='white')
    ax.text(9, 5.6, 'duration_in_traffic: with traffic', fontsize=9, ha='center', color='white')
    ax.text(9, 5.2, 'distance: route distance', fontsize=9, ha='center', color='white')
    
    # Arrow
    ax.annotate('', xy=(6.4, 6), xytext=(5.6, 6),
                arrowprops=dict(arrowstyle='->', color='#34495e', lw=2))
    
    # Data Processing Box
    box_proc = FancyBboxPatch((2, 2.5), 8, 2), 
    ax.add_patch(FancyBboxPatch((2, 2.5), 8, 2, boxstyle="round,pad=0.05",
                                facecolor='#9b59b6', edgecolor='#8e44ad', linewidth=2))
    ax.text(6, 4, 'Data Processing (52 NY routes + 44 LA routes)', fontsize=11, 
            fontweight='bold', ha='center', color='white')
    ax.text(6, 3.4, 'For each route: Multiplier = duration_in_traffic / duration', 
            fontsize=10, ha='center', color='white')
    ax.text(6, 2.9, 'City average = mean(all route multipliers)', 
            fontsize=10, ha='center', color='white')
    
    # Arrow down
    ax.annotate('', xy=(6, 2.4), xytext=(6, 4.9),
                arrowprops=dict(arrowstyle='->', color='#34495e', lw=2))
    
    # Results
    box_ny = FancyBboxPatch((1, 0.5), 4.5, 1.5, boxstyle="round,pad=0.05",
                            facecolor='#1a5276', edgecolor='#154360', linewidth=2)
    ax.add_patch(box_ny)
    ax.text(3.25, 1.5, 'NY Result', fontsize=11, fontweight='bold', ha='center', color='white')
    ax.text(3.25, 1, '52 routes analyzed', fontsize=9, ha='center', color='white')
    ax.text(3.25, 0.7, 'Worst multiplier: 5.20x', fontsize=10, ha='center', color='#f1c40f', fontweight='bold')
    
    box_la = FancyBboxPatch((6.5, 0.5), 4.5, 1.5, boxstyle="round,pad=0.05",
                            facecolor='#e67e22', edgecolor='#d35400', linewidth=2)
    ax.add_patch(box_la)
    ax.text(8.75, 1.5, 'LA Result', fontsize=11, fontweight='bold', ha='center', color='white')
    ax.text(8.75, 1, '44 routes analyzed', fontsize=9, ha='center', color='white')
    ax.text(8.75, 0.7, 'Worst multiplier: 4.15x', fontsize=10, ha='center', color='#f1c40f', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('diagrams/google_api_flow_en.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("[OK] Created: diagrams/google_api_flow_en.png")


def create_google_api_diagram_pt():
    """Create diagram showing Google API data flow in Portuguese"""
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis('off')
    
    ax.text(6, 7.5, 'Google Distance Matrix API - Coleta de Dados', 
            fontsize=14, fontweight='bold', ha='center', color='#2c3e50')
    
    # API Request Box
    box_req = FancyBboxPatch((0.5, 5), 5, 2, boxstyle="round,pad=0.05",
                             facecolor='#3498db', edgecolor='#2980b9', linewidth=2)
    ax.add_patch(box_req)
    ax.text(3, 6.5, 'Parametros da Requisicao', fontsize=11, fontweight='bold', 
            ha='center', color='white')
    ax.text(3, 6, 'origem: centroide do CEP', fontsize=9, ha='center', color='white')
    ax.text(3, 5.6, 'destino: Aeroporto JFK/LAX', fontsize=9, ha='center', color='white')
    ax.text(3, 5.2, 'modelo_trafego: pessimista', fontsize=9, ha='center', color='white')
    
    # API Response Box
    box_resp = FancyBboxPatch((6.5, 5), 5, 2, boxstyle="round,pad=0.05",
                              facecolor='#27ae60', edgecolor='#1e8449', linewidth=2)
    ax.add_patch(box_resp)
    ax.text(9, 6.5, 'Resposta da API', fontsize=11, fontweight='bold', 
            ha='center', color='white')
    ax.text(9, 6, 'duracao: tempo base', fontsize=9, ha='center', color='white')
    ax.text(9, 5.6, 'duracao_com_trafego: com trafego', fontsize=9, ha='center', color='white')
    ax.text(9, 5.2, 'distancia: distancia da rota', fontsize=9, ha='center', color='white')
    
    # Arrow
    ax.annotate('', xy=(6.4, 6), xytext=(5.6, 6),
                arrowprops=dict(arrowstyle='->', color='#34495e', lw=2))
    
    # Data Processing Box
    ax.add_patch(FancyBboxPatch((2, 2.5), 8, 2, boxstyle="round,pad=0.05",
                                facecolor='#9b59b6', edgecolor='#8e44ad', linewidth=2))
    ax.text(6, 4, 'Processamento (52 rotas NY + 44 rotas LA)', fontsize=11, 
            fontweight='bold', ha='center', color='white')
    ax.text(6, 3.4, 'Para cada rota: Multiplicador = duracao_trafego / duracao', 
            fontsize=10, ha='center', color='white')
    ax.text(6, 2.9, 'Media cidade = media(multiplicadores de todas rotas)', 
            fontsize=10, ha='center', color='white')
    
    # Arrow down
    ax.annotate('', xy=(6, 2.4), xytext=(6, 4.9),
                arrowprops=dict(arrowstyle='->', color='#34495e', lw=2))
    
    # Results
    box_ny = FancyBboxPatch((1, 0.5), 4.5, 1.5, boxstyle="round,pad=0.05",
                            facecolor='#1a5276', edgecolor='#154360', linewidth=2)
    ax.add_patch(box_ny)
    ax.text(3.25, 1.5, 'Resultado NY', fontsize=11, fontweight='bold', ha='center', color='white')
    ax.text(3.25, 1, '52 rotas analisadas', fontsize=9, ha='center', color='white')
    ax.text(3.25, 0.7, 'Multiplicador pior: 5.20x', fontsize=10, ha='center', color='#f1c40f', fontweight='bold')
    
    box_la = FancyBboxPatch((6.5, 0.5), 4.5, 1.5, boxstyle="round,pad=0.05",
                            facecolor='#e67e22', edgecolor='#d35400', linewidth=2)
    ax.add_patch(box_la)
    ax.text(8.75, 1.5, 'Resultado LA', fontsize=11, fontweight='bold', ha='center', color='white')
    ax.text(8.75, 1, '44 rotas analisadas', fontsize=9, ha='center', color='white')
    ax.text(8.75, 0.7, 'Multiplicador pior: 4.15x', fontsize=10, ha='center', color='#f1c40f', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('diagrams/google_api_flow_pt.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("[OK] Created: diagrams/google_api_flow_pt.png")


if __name__ == '__main__':
    import os
    os.makedirs('diagrams', exist_ok=True)
    
    print("Creating multiplier methodology diagrams...")
    create_methodology_diagram_en()
    create_methodology_diagram_pt()
    create_google_api_diagram_en()
    create_google_api_diagram_pt()
    print("\nAll diagrams created successfully!")

