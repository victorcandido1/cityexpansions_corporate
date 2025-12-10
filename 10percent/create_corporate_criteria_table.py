# -*- coding: utf-8 -*-
"""
CORPORATE CRITERIA BREAKDOWN TABLE BY CITY
===========================================
Cria tabela detalhada mostrando os componentes do Corporate Score por cidade.
Similar à tabela de households, mas para corporate data.
"""

import pandas as pd
import numpy as np

print("\n" + "="*80)
print("CORPORATE CRITERIA BREAKDOWN BY CITY")
print("="*80)

# Load data
df_corp = pd.read_csv('top10_corporate_data.csv')

print(f"\nLoaded {len(df_corp)} Corporate Top 10% ZIPs")

# Calculate statistics by city
city_stats = []

for city in sorted(df_corp['city_name'].unique()):
    city_data = df_corp[df_corp['city_name'] == city]
    
    stats = {
        'City': city,
        'Top10_ZIPs': len(city_data),
        'Total_Employment': city_data['total_employment'].sum(),
        'Total_Revenue_M': city_data['estimated_revenue_M'].sum(),
        'Total_Establishments': city_data['total_establishments'].sum(),
        'Power_Employment': city_data['power_employment'].sum(),
        'Power_Employment_Pct': (city_data['power_employment'].sum() / city_data['total_employment'].sum() * 100) if city_data['total_employment'].sum() > 0 else 0,
        'Median_Revenue_M': city_data['estimated_revenue_M'].median(),
        'Median_Employment': city_data['total_employment'].median(),
        'Median_RevPerEmp': city_data['revenue_per_employee'].median(),
        'Median_Corporate_Score': city_data['Corporate_Score'].median(),
        'Mean_Corporate_Score': city_data['Corporate_Score'].mean(),
        'Median_Distance_km': city_data['distance_km'].median(),
        'Mean_Travel_Time_min': city_data['Travel_Time_Min'].mean() if 'Travel_Time_Min' in city_data.columns else np.nan,
        'Median_Payroll_per_Emp': city_data['payroll_per_employee'].median(),
    }
    
    city_stats.append(stats)

df_stats = pd.DataFrame(city_stats)

# Sort by total employment (descending)
df_stats = df_stats.sort_values('Total_Employment', ascending=False)

# Save to CSV
df_stats.to_csv('corporate_criteria_by_city.csv', index=False, float_format='%.2f')
print("\n✓ Saved: corporate_criteria_by_city.csv")

# Print table
print("\n" + "="*80)
print("CORPORATE CRITERIA BREAKDOWN")
print("="*80)
print(f"\n{'City':15} {'ZIPs':>6} {'Employment':>12} {'Revenue ($M)':>15} {'Power %':>8} {'Med Score':>10}")
print("-"*80)

for _, row in df_stats.iterrows():
    print(f"{row['City']:15} {row['Top10_ZIPs']:>6} {row['Total_Employment']:>12,.0f} "
          f"${row['Total_Revenue_M']:>14,.0f} {row['Power_Employment_Pct']:>7.1f}% "
          f"{row['Median_Corporate_Score']:>10.2f}")

print("="*80)

# Create detailed HTML table
html_table = """
<div class="section corporate">
    <h3>📊 Corporate Criteria Breakdown by City</h3>
    <p style="margin-bottom: 15px; color: #666;">
        <strong>Corporate Score Formula:</strong> Revenue (35%) × Employment (30%) × Power Share (15%) × Distance² (20%)<br>
        <strong>Threshold:</strong> Corporate Score ≥ 90º percentil (14.05)
    </p>
    <table>
        <thead>
            <tr>
                <th class="corporate">City</th>
                <th class="corporate">Top 10%<br>ZIPs</th>
                <th class="corporate">Total<br>Employment</th>
                <th class="corporate">Total Revenue<br>($M)</th>
                <th class="corporate">Power<br>Industries %</th>
                <th class="corporate">Median<br>Rev/Employee</th>
                <th class="corporate">Median<br>Corp Score</th>
                <th class="corporate">Median<br>Distance (km)</th>
            </tr>
        </thead>
        <tbody>
"""

for _, row in df_stats.iterrows():
    html_table += f"""
            <tr>
                <td><strong>{row['City']}</strong></td>
                <td>{row['Top10_ZIPs']:,.0f}</td>
                <td>{row['Total_Employment']:,.0f}</td>
                <td>${row['Total_Revenue_M']:,.0f}</td>
                <td>{row['Power_Employment_Pct']:.1f}%</td>
                <td>${row['Median_RevPerEmp']:,.0f}</td>
                <td>{row['Median_Corporate_Score']:.2f}</td>
                <td>{row['Median_Distance_km']:.1f}</td>
            </tr>
"""

html_table += """
        </tbody>
    </table>
    <p><a href="corporate_criteria_by_city.csv" class="map-link corporate">📥 Download Corporate Criteria by City (CSV)</a></p>
    
    <div style="background: #e7f3ff; padding: 15px; border-radius: 8px; margin-top: 20px;">
        <h4 style="margin-top: 0; color: #0066cc;">📋 Componentes do Corporate Score:</h4>
        <ul style="margin: 10px 0; padding-left: 20px;">
            <li><strong>Revenue (35%):</strong> Total estimated revenue (normalizado 0-1)</li>
            <li><strong>Employment (30%):</strong> Total employment count (normalizado 0-1)</li>
            <li><strong>Power Share (15%):</strong> % de employment em Power Industries (Finance, Tech, Professional Services)</li>
            <li><strong>Distance² (20%):</strong> Distância ao aeroporto ao quadrado (normalizado 0-1)</li>
        </ul>
        <p style="margin: 10px 0; font-size: 13px; color: #666;">
            <strong>Nota:</strong> O Corporate Score usa média geométrica dos componentes normalizados. 
            ZIPs com score ≥ 14.05 (90º percentil) são classificados como Top 10%.
        </p>
    </div>
</div>
"""

# Save HTML snippet
with open('corporate_criteria_table_snippet.html', 'w', encoding='utf-8') as f:
    f.write(html_table)

print("\n✓ Saved: corporate_criteria_table_snippet.html")
print("\nHTML table snippet created. Add this to dashboard_tabbed.html in the Corporate tab.")
print("="*80)

