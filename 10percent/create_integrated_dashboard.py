# -*- coding: utf-8 -*-
"""
INTEGRATED DASHBOARD - HOUSEHOLDS + CORPORATE DATA (ENHANCED)
=============================================================
Creates a comprehensive HTML dashboard with:
- Top 10% Richest Households (IRS/Census data)
- Top 10% Corporate Power (Census Bureau 2021)
- INTERSECTION analysis
- Advanced comparative statistics
- Overlay maps

100% REAL DATA - NO SYNTHETIC DATA
"""

import pandas as pd
import os
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Input files
HOUSEHOLD_FILE = os.path.join(BASE_DIR, 'top10_richest_data.csv')
CORPORATE_FILE = os.path.join(BASE_DIR, 'corporate_all_zips.csv')
CORPORATE_TOP10_FILE = os.path.join(BASE_DIR, 'top10_corporate_data.csv')
INTERSECTION_FILE = os.path.join(BASE_DIR, 'intersection_analysis.csv')
INTERSECTION_CITY_FILE = os.path.join(BASE_DIR, 'intersection_by_city.csv')
CORPORATE_CITY_SUMMARY = os.path.join(BASE_DIR, 'corporate_by_city_summary.csv')

# Output file
OUTPUT_FILE = os.path.join(BASE_DIR, 'dashboard_integrated.html')

# City names
CITIES = {
    'los_angeles': 'Los Angeles',
    'new_york': 'New York',
    'chicago': 'Chicago',
    'dallas': 'Dallas',
    'houston': 'Houston',
    'miami': 'Miami',
    'san_francisco': 'San Francisco',
}

# =============================================================================
# LOAD DATA
# =============================================================================
def load_data():
    """Load all data files"""
    print("\n" + "="*80)
    print("LOADING DATA FOR INTEGRATED DASHBOARD")
    print("="*80)
    
    data = {}
    
    # Household top 10%
    if os.path.exists(HOUSEHOLD_FILE):
        data['household'] = pd.read_csv(HOUSEHOLD_FILE, dtype={'zipcode': str})
        print(f"  Household Top 10%: {len(data['household'])} ZIPs")
    else:
        data['household'] = None
        print(f"  [!] Household data not found")
    
    # Corporate all
    if os.path.exists(CORPORATE_FILE):
        data['corporate_all'] = pd.read_csv(CORPORATE_FILE, dtype={'zipcode': str})
        print(f"  Corporate All: {len(data['corporate_all'])} ZIPs")
    else:
        data['corporate_all'] = None
    
    # Corporate top 10%
    if os.path.exists(CORPORATE_TOP10_FILE):
        data['corporate_top10'] = pd.read_csv(CORPORATE_TOP10_FILE, dtype={'zipcode': str})
        print(f"  Corporate Top 10%: {len(data['corporate_top10'])} ZIPs")
    else:
        data['corporate_top10'] = None
        print(f"  [!] Corporate Top 10% not found - run calculate_top10_corporate.py first")
    
    # Intersection
    if os.path.exists(INTERSECTION_FILE):
        data['intersection'] = pd.read_csv(INTERSECTION_FILE, dtype={'zipcode': str})
        print(f"  Intersection: {len(data['intersection'])} ZIPs")
    else:
        data['intersection'] = None
        print(f"  [!] Intersection data not found - run calculate_intersection.py first")
    
    # Intersection by city
    if os.path.exists(INTERSECTION_CITY_FILE):
        data['intersection_city'] = pd.read_csv(INTERSECTION_CITY_FILE, dtype={'city_key': str})
        print(f"  Intersection by city: {len(data['intersection_city'])} cities")
    else:
        data['intersection_city'] = None
    
    # Corporate city summary
    if os.path.exists(CORPORATE_CITY_SUMMARY):
        data['corp_city'] = pd.read_csv(CORPORATE_CITY_SUMMARY, dtype={'city_key': str})
    else:
        data['corp_city'] = None
    
    return data

# =============================================================================
# CALCULATE STATISTICS
# =============================================================================
def calculate_statistics(data):
    """Calculate all statistics for dashboard"""
    stats = {}
    
    # Household statistics
    if data['household'] is not None:
        df_hh = data['household']
        stats['hh_zips'] = len(df_hh)
        stats['hh_hh200k'] = df_hh['Households_200k'].sum()
        stats['hh_median_agi'] = df_hh['AGI_per_return'].median()
        stats['hh_total_pop'] = df_hh['Population'].sum()
        stats['hh_threshold'] = df_hh['Geometric_Score'].min()
    else:
        stats['hh_zips'] = 0
        stats['hh_hh200k'] = 0
        stats['hh_median_agi'] = 0
        stats['hh_total_pop'] = 0
        stats['hh_threshold'] = 0
    
    # Corporate top 10% statistics
    if data['corporate_top10'] is not None:
        df_corp10 = data['corporate_top10']
        stats['corp10_zips'] = len(df_corp10)
        stats['corp10_employment'] = df_corp10['total_employment'].sum()
        stats['corp10_revenue'] = df_corp10['estimated_revenue_M'].sum()
        stats['corp10_power_emp'] = df_corp10['power_employment'].sum()
        stats['corp10_threshold'] = df_corp10['Corporate_Power_Index'].min() if len(df_corp10) > 0 else 0
    else:
        stats['corp10_zips'] = 0
        stats['corp10_employment'] = 0
        stats['corp10_revenue'] = 0
        stats['corp10_power_emp'] = 0
        stats['corp10_threshold'] = 0
    
    # Corporate all statistics
    if data['corporate_all'] is not None:
        df_corp = data['corporate_all']
        stats['corp_all_zips'] = len(df_corp[df_corp['total_employment'] > 0])
        stats['corp_all_employment'] = df_corp['total_employment'].sum()
        stats['corp_all_revenue'] = df_corp['estimated_revenue_M'].sum()
    else:
        stats['corp_all_zips'] = 0
        stats['corp_all_employment'] = 0
        stats['corp_all_revenue'] = 0
    
    # Intersection statistics
    if data['intersection'] is not None:
        df_int = data['intersection']
        stats['intersection_zips'] = len(df_int)
        stats['intersection_hh200k'] = df_int['Households_200k'].sum()
        stats['intersection_employment'] = df_int['total_employment'].sum()
        stats['intersection_revenue'] = df_int['estimated_revenue_M'].sum()
        stats['intersection_median_agi'] = df_int['AGI_per_return'].median()
        stats['intersection_median_corp_index'] = df_int['Corporate_Power_Index'].median()
        
        # Calculate intersection percentage
        if stats['hh_zips'] > 0:
            stats['intersection_pct_of_hh'] = stats['intersection_zips'] / stats['hh_zips'] * 100
        else:
            stats['intersection_pct_of_hh'] = 0
        
        if stats['corp10_zips'] > 0:
            stats['intersection_pct_of_corp'] = stats['intersection_zips'] / stats['corp10_zips'] * 100
        else:
            stats['intersection_pct_of_corp'] = 0
    else:
        stats['intersection_zips'] = 0
        stats['intersection_hh200k'] = 0
        stats['intersection_employment'] = 0
        stats['intersection_revenue'] = 0
        stats['intersection_median_agi'] = 0
        stats['intersection_median_corp_index'] = 0
        stats['intersection_pct_of_hh'] = 0
        stats['intersection_pct_of_corp'] = 0
    
    # Correlation
    if data['household'] is not None and data['corporate_top10'] is not None:
        merged = data['household'].merge(
            data['corporate_top10'][['zipcode', 'Corporate_Power_Index']],
            on='zipcode', how='inner'
        )
        if len(merged) > 0:
            stats['correlation'] = merged['Geometric_Score'].corr(merged['Corporate_Power_Index'])
        else:
            stats['correlation'] = 0
    else:
        stats['correlation'] = 0
    
    return stats

# =============================================================================
# CREATE DASHBOARD
# =============================================================================
def create_dashboard(data, stats):
    """Create enhanced integrated HTML dashboard"""
    print("\n" + "="*80)
    print("CREATING ENHANCED INTEGRATED DASHBOARD")
    print("="*80)
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Integrated Dashboard - Households & Corporate Data</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: #f0f0f0; 
        }}
        .container {{ 
            max-width: 1600px; 
            margin: 0 auto; 
        }}
        .methodology-link {{
            display: inline-block;
            background: #0066cc;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            margin: 20px 0;
            font-size: 16px;
        }}
        .methodology-link:hover {{
            background: #0052a3;
        }}
        h1 {{ 
            color: #800026; 
            border-bottom: 3px solid #800026; 
            padding-bottom: 10px; 
            margin-bottom: 20px;
        }}
        h2 {{ 
            color: #bd0026; 
            margin-top: 30px;
            border-left: 4px solid #bd0026;
            padding-left: 10px;
        }}
        h3 {{
            color: #0066cc;
            margin-top: 20px;
            border-left: 3px solid #0066cc;
            padding-left: 8px;
        }}
        .highlight {{ 
            background: #fff3cd; 
            padding: 15px; 
            border-radius: 8px; 
            margin: 20px 0; 
            border-left: 5px solid #ffc107; 
        }}
        .highlight.intersection {{
            background: #d1ecf1;
            border-left: 5px solid #17a2b8;
        }}
        .stats-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 15px; 
            margin: 20px 0; 
        }}
        .stat-card {{ 
            background: white; 
            padding: 20px; 
            border-radius: 8px; 
            box-shadow: 0 2px 5px rgba(0,0,0,0.1); 
            text-align: center; 
        }}
        .stat-card.household {{ border-top: 4px solid #800026; }}
        .stat-card.corporate {{ border-top: 4px solid #0066cc; }}
        .stat-card.intersection {{ border-top: 4px solid #17a2b8; }}
        .stat-card .number {{ 
            font-size: 32px; 
            font-weight: bold; 
            color: #800026; 
        }}
        .stat-card.corporate .number {{ color: #0066cc; }}
        .stat-card.intersection .number {{ color: #17a2b8; }}
        .stat-card .label {{ 
            font-size: 12px; 
            color: #666; 
            margin-top: 5px; 
        }}
        .section {{ 
            background: white; 
            padding: 20px; 
            border-radius: 8px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
            margin: 20px 0; 
        }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            background: white; 
            margin: 20px 0; 
        }}
        th {{ 
            background: #800026; 
            color: white; 
            padding: 12px; 
            text-align: left; 
            font-size: 14px;
        }}
        th.corporate {{ background: #0066cc; }}
        th.intersection {{ background: #17a2b8; }}
        td {{ 
            padding: 10px; 
            border-bottom: 1px solid #ddd; 
            font-size: 13px;
        }}
        tr:hover {{ background: #fff5f5; }}
        .map-link {{ 
            display: inline-block; 
            background: #bd0026; 
            color: white; 
            padding: 8px 16px; 
            text-decoration: none; 
            border-radius: 4px; 
            margin: 5px; 
            font-size: 13px;
        }}
        .map-link:hover {{ background: #800026; }}
        .map-link.corporate {{ 
            background: #0066cc; 
        }}
        .map-link.corporate:hover {{ 
            background: #0052a3; 
        }}
        .map-link.intersection {{ 
            background: #17a2b8; 
        }}
        .map-link.intersection:hover {{ 
            background: #138496; 
        }}
        .chart-img {{ 
            max-width: 100%; 
            border-radius: 8px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
            margin: 10px 0; 
        }}
        .data-badge {{
            display: inline-block;
            background: #28a745;
            color: white;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
            margin-left: 5px;
        }}
        .comparison-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }}
        .comparison-box {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border: 2px solid #dee2e6;
        }}
        .comparison-box.household {{
            border-color: #800026;
        }}
        .comparison-box.corporate {{
            border-color: #0066cc;
        }}
    </style>
</head>
<body>
    <div class="container">
        <a href="METHODOLOGY.html" class="methodology-link">📚 METHODOLOGY - Complete Documentation</a>
        <h1>🏠💼 INTEGRATED DASHBOARD: HOUSEHOLDS & CORPORATE DATA</h1>
        <p style="font-size: 16px; color: #666;">
            Comprehensive analysis combining Top 10% Richest Households and Top 10% Corporate Power
            <span class="data-badge">100% REAL DATA</span>
        </p>
        
        <div class="highlight">
            <strong>Household Data:</strong> IRS SOI 2022, Census ACS 5yr 2022<br>
            <strong>Corporate Data:</strong> U.S. Census Bureau - County Business Patterns 2021<br>
            <strong>Geographic Coverage:</strong> 7 Major Metro Areas
        </div>
        
        <!-- Key Statistics -->
        <div class="section">
            <h2>📊 Key Statistics</h2>
            <div class="stats-grid">
                <div class="stat-card household">
                    <div class="number">{stats['hh_zips']:,}</div>
                    <div class="label">Household Top 10% ZIPs</div>
                </div>
                <div class="stat-card household">
                    <div class="number">{stats['hh_hh200k']:,.0f}</div>
                    <div class="label">HH $200k+</div>
                </div>
                <div class="stat-card household">
                    <div class="number">${stats['hh_median_agi']/1000:.0f}k</div>
                    <div class="label">Median AGI/Return</div>
                </div>
                <div class="stat-card corporate">
                    <div class="number">{stats['corp10_zips']:,}</div>
                    <div class="label">Corporate Top 10% ZIPs</div>
                </div>
                <div class="stat-card corporate">
                    <div class="number">{stats['corp10_employment']:,.0f}</div>
                    <div class="label">Total Employment</div>
                </div>
                <div class="stat-card corporate">
                    <div class="number">${stats['corp10_revenue']/1000:.1f}B</div>
                    <div class="label">Est. Total Revenue</div>
                </div>
                <div class="stat-card intersection">
                    <div class="number">{stats['intersection_zips']:,}</div>
                    <div class="label">INTERSECTION ZIPs</div>
                </div>
                <div class="stat-card intersection">
                    <div class="number">{stats['intersection_pct_of_hh']:.1f}%</div>
                    <div class="label">% of Household Top 10%</div>
                </div>
            </div>
        </div>
        
        <!-- INTERSECTION HIGHLIGHT -->
        <div class="section">
            <div class="highlight intersection">
                <h2 style="margin-top: 0; color: #17a2b8;">🎯 INTERSECTION: Where Wealth Meets Corporate Power</h2>
                <p style="font-size: 16px; margin: 10px 0;">
                    <strong>{stats['intersection_zips']:,} ZIP codes</strong> are in BOTH Top 10% Household Wealth AND Top 10% Corporate Power
                </p>
                <p>
                    This represents <strong>{stats['intersection_pct_of_hh']:.1f}%</strong> of wealthy household ZIPs and 
                    <strong>{stats['intersection_pct_of_corp']:.1f}%</strong> of corporate power ZIPs.
                </p>
                <p>
                    <strong>Intersection Statistics:</strong><br>
                    • {stats['intersection_hh200k']:,.0f} Households $200k+<br>
                    • {stats['intersection_employment']:,.0f} Total Employment<br>
                    • ${stats['intersection_revenue']/1000:,.1f}B Estimated Revenue<br>
                    • ${stats['intersection_median_agi']:,.0f} Median AGI<br>
                    • {stats['intersection_median_corp_index']:.2f} Median Corporate Power Index
                </p>
            </div>
        </div>
        
        <!-- Advanced Statistics -->
        <div class="section">
            <h2>📈 Advanced Statistics: Household vs Corporate Wealth</h2>
            
            <div class="comparison-grid">
                <div class="comparison-box household">
                    <h3>Household Wealth (Top 10%)</h3>
                    <p><strong>Threshold:</strong> Geometric Score >= {stats['hh_threshold']*100:.2f}%</p>
                    <p><strong>ZIPs:</strong> {stats['hh_zips']:,}</p>
                    <p><strong>Total HH $200k+:</strong> {stats['hh_hh200k']:,.0f}</p>
                    <p><strong>Median AGI:</strong> ${stats['hh_median_agi']:,.0f}</p>
                    <p><strong>Total Population:</strong> {stats['hh_total_pop']/1e6:.1f}M</p>
                </div>
                
                <div class="comparison-box corporate">
                    <h3>Corporate Power (Top 10%)</h3>
                    <p><strong>Threshold:</strong> Corporate Power Index >= {stats['corp10_threshold']:.2f}</p>
                    <p><strong>ZIPs:</strong> {stats['corp10_zips']:,}</p>
                    <p><strong>Total Employment:</strong> {stats['corp10_employment']:,.0f}</p>
                    <p><strong>Total Revenue:</strong> ${stats['corp10_revenue']/1000:,.1f}B</p>
                    <p><strong>Power Industries Emp:</strong> {stats['corp10_power_emp']:,.0f}</p>
                </div>
            </div>
            
            <div style="background: #e7f3ff; padding: 15px; border-radius: 8px; margin-top: 20px;">
                <h3 style="margin-top: 0;">Correlation Analysis</h3>
                <p>
                    <strong>Correlation Coefficient:</strong> {stats['correlation']:.3f}
                </p>
                <p style="font-size: 13px; color: #666;">
                    Measures the relationship between Household Geometric Score and Corporate Power Index.
                    Values range from -1 (perfect negative) to +1 (perfect positive).
                    A value of {stats['correlation']:.3f} indicates a {'positive' if stats['correlation'] > 0 else 'negative'} correlation.
                </p>
            </div>
        </div>
        
        <!-- Maps Section -->
        <div class="section">
            <h2>🗺️ Interactive Maps</h2>
            
            <h3>Household Maps (Top 10% Richest)</h3>
            <p>
                <a href="map_top10_national.html" class="map-link">National Map</a>
"""
    
    # Add household maps
    if data['household'] is not None:
        for city_key, city_name in CITIES.items():
            city_count = len(data['household'][data['household']['city_key'] == city_key])
            if city_count > 0:
                html += f'                <a href="map_top10_{city_key}.html" class="map-link">{city_name} ({city_count})</a>\n'
    
    html += """            </p>
            
            <h3>Corporate Maps</h3>
            <p>
                <strong>All ZIPs:</strong><br>
"""
    
    # Add corporate maps (all)
    for city_key, city_name in CITIES.items():
        html += f'                <a href="map_corporate_{city_key}_all.html" class="map-link corporate">All - {city_name}</a>\n'
    
    html += """            </p>
            <p>
                <strong>Top 10% Corporate Power ZIPs:</strong><br>
"""
    
    # Add corporate maps (top10)
    for city_key, city_name in CITIES.items():
        html += f'                <a href="map_corporate_{city_key}_top10.html" class="map-link corporate">Top 10% - {city_name}</a>\n'
    
    html += """            </p>
            <p>
                <strong>🎯 Overlay Maps (Household + Corporate Combined):</strong><br>
"""
    
    # Add overlay maps
    for city_key, city_name in CITIES.items():
        html += f'                <a href="map_overlay_{city_key}.html" class="map-link intersection">Overlay - {city_name}</a>\n'
    
    html += """            </p>
            <p style="font-size: 12px; color: #666;">
                <strong>Legend:</strong> 
                <span style="color: #8B008B;">■ Purple</span> = Intersection (Both Top 10%), 
                <span style="color: #800026;">■ Red</span> = Household Top 10% Only, 
                <span style="color: #0066cc;">■ Blue</span> = Corporate Top 10% Only
            </p>
        </div>
        
        <!-- Intersection by City -->
        <div class="section">
            <h2>🏙️ Intersection by City</h2>
            <table>
                <thead>
                    <tr>
                        <th>City</th>
                        <th class="household">HH Top 10%</th>
                        <th class="corporate">Corp Top 10%</th>
                        <th class="intersection">INTERSECTION</th>
                        <th class="intersection">% of HH</th>
                        <th class="intersection">% of Corp</th>
                        <th class="intersection">HH $200k+</th>
                        <th class="intersection">Employment</th>
                        <th class="intersection">Revenue ($M)</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    # Add intersection city data
    if data['intersection_city'] is not None:
        for _, row in data['intersection_city'].iterrows():
            html += f"""
                    <tr>
                        <td><strong>{row['city']}</strong></td>
                        <td>{int(row['household_top10'])}</td>
                        <td>{int(row['corporate_top10'])}</td>
                        <td><strong>{int(row['intersection'])}</strong></td>
                        <td>{row['intersection_pct_of_household']:.1f}%</td>
                        <td>{row['intersection_pct_of_corporate']:.1f}%</td>
                        <td>{row.get('intersection_hh200k', 0):,.0f}</td>
                        <td>{row.get('intersection_employment', 0):,.0f}</td>
                        <td>${row.get('intersection_revenue_M', 0):,.0f}</td>
                    </tr>
"""
    
    html += """                </tbody>
            </table>
        </div>
        
        <!-- City Breakdown -->
        <div class="section">
            <h2>🏙️ City Breakdown - Integrated View</h2>
            <table>
                <thead>
                    <tr>
                        <th>City</th>
                        <th colspan="4" style="text-align: center; background: #800026;">HOUSEHOLDS (Top 10%)</th>
                        <th colspan="4" style="text-align: center; background: #0066cc;">CORPORATE (Top 10%)</th>
                    </tr>
                    <tr>
                        <th></th>
                        <th style="background: #800026;">ZIPs</th>
                        <th style="background: #800026;">HH $200k+</th>
                        <th style="background: #800026;">Med AGI</th>
                        <th style="background: #800026;">Med Score</th>
                        <th style="background: #0066cc;">ZIPs</th>
                        <th style="background: #0066cc;">Employment</th>
                        <th style="background: #0066cc;">Revenue ($M)</th>
                        <th style="background: #0066cc;">Power %</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    # Add city statistics
    if data['household'] is not None and data['corporate_top10'] is not None:
        for city_key, city_name in CITIES.items():
            hh_city = data['household'][data['household']['city_key'] == city_key]
            corp_city = data['corporate_top10'][data['corporate_top10']['city_key'] == city_key]
            
            if len(hh_city) > 0 or len(corp_city) > 0:
                hh_zips = len(hh_city)
                hh_hh200k = hh_city['Households_200k'].sum() if len(hh_city) > 0 else 0
                hh_agi = hh_city['AGI_per_return'].median() if len(hh_city) > 0 else 0
                hh_score = hh_city['Geometric_Score'].median() if len(hh_city) > 0 else 0
                
                corp_zips = len(corp_city)
                corp_emp = corp_city['total_employment'].sum() if len(corp_city) > 0 else 0
                corp_rev = corp_city['estimated_revenue_M'].sum() if len(corp_city) > 0 else 0
                corp_power = corp_city['power_emp_pct'].mean() if len(corp_city) > 0 else 0
                
                html += f"""
                    <tr>
                        <td><strong>{city_name}</strong></td>
                        <td>{hh_zips}</td>
                        <td>{hh_hh200k:,.0f}</td>
                        <td>${hh_agi:,.0f}</td>
                        <td>{hh_score*100:.2f}%</td>
                        <td>{corp_zips}</td>
                        <td>{corp_emp:,.0f}</td>
                        <td>${corp_rev:,.0f}</td>
                        <td>{corp_power:.1f}%</td>
                    </tr>
"""
    
    html += """                </tbody>
            </table>
        </div>
        
        <!-- Household Analysis -->
        <div class="section">
            <h2>🏠 Household Analysis (Top 10% Richest)</h2>
            <img src="histogram_all_vs_top10.png" class="chart-img" alt="All vs Top 10%">
            <img src="histogram_top10_scores.png" class="chart-img" alt="Score Distribution">
            <img src="histogram_top10_by_city.png" class="chart-img" alt="By City">
            <img src="histogram_top10_boxplot.png" class="chart-img" alt="Box Plot">
            <img src="histogram_top10_agi.png" class="chart-img" alt="AGI Distribution">
            
            <h3>Geographic Analysis</h3>
            <img src="distance_radius_analysis.png" class="chart-img" alt="Distance & Radius Analysis">
            <p><a href="distance_radius_analysis.csv" class="map-link">📥 Download Distance Data (CSV)</a></p>
            
            <h3>Weighted Averages</h3>
            <img src="weighted_averages_chart.png" class="chart-img" alt="Weighted Averages">
            <p><a href="weighted_averages_analysis.csv" class="map-link">📥 Download Weighted Averages (CSV)</a></p>
            
            <h3>HH $200k+ by Region</h3>
            <img src="hh200k_by_region_charts.png" class="chart-img" alt="HH200k by Region">
            <p><a href="hh200k_by_region.csv" class="map-link">📥 Download HH by Region (CSV)</a></p>
        </div>
        
        <!-- Corporate Statistical Analysis -->
        <div class="section">
            <h2>🏢 Corporate Statistical Analysis (Top 10% Corporate Power)</h2>
            <p style="background: #e7f3ff; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                <strong>Data Source:</strong> U.S. Census Bureau - County Business Patterns 2021<br>
                <strong>100% Real Data:</strong> Establishments, Employment, Payroll from Census API<br>
                <strong>Estimates:</strong> Revenue estimated using BLS revenue-per-employee ratios
            </p>
            
            <h3>Distribution Analysis</h3>
            <img src="corporate_histogram_all_vs_top10.png" class="chart-img" alt="All vs Top 10% Corporate">
            <img src="corporate_histogram_top10_power_index.png" class="chart-img" alt="Power Index Distribution">
            <img src="corporate_histogram_top10_by_city.png" class="chart-img" alt="Corporate by City">
            <img src="corporate_histogram_top10_boxplot.png" class="chart-img" alt="Box Plot by City">
            
            <h3>Revenue & Employment</h3>
            <img src="corporate_histogram_top10_revenue.png" class="chart-img" alt="Revenue Distribution">
            <img src="corporate_histogram_top10_employment.png" class="chart-img" alt="Employment Distribution">
            
            <h3>Power Industries</h3>
            <img src="corporate_histogram_top10_power_share.png" class="chart-img" alt="Power Industries Share">
            <img src="corporate_power_industries_by_region.png" class="chart-img" alt="Power Industries by Region">
            <p><a href="corporate_power_industries_by_region.csv" class="map-link corporate">📥 Download Power Industries by Region (CSV)</a></p>
            
            <h3>Geographic Analysis</h3>
            <img src="corporate_distance_radius_analysis.png" class="chart-img" alt="Distance & Radius Analysis">
            <p><a href="corporate_distance_analysis.csv" class="map-link corporate">📥 Download Distance Data (CSV)</a></p>
            
            <h3>Weighted Averages</h3>
            <img src="corporate_weighted_averages_chart.png" class="chart-img" alt="Weighted Averages">
            <p><a href="corporate_weighted_averages_analysis.csv" class="map-link corporate">📥 Download Weighted Averages (CSV)</a></p>
            
            <h3>Comparative Analysis</h3>
            <img src="corporate_comparative_analysis.png" class="chart-img" alt="Comparative Analysis">
            <p style="font-size: 13px; color: #666; margin-top: 10px;">
                <strong>Top Left:</strong> Revenue vs Employment correlation<br>
                <strong>Top Right:</strong> Power Index vs Power Share relationship<br>
                <strong>Bottom Left:</strong> Employment vs Establishments density<br>
                <strong>Bottom Right:</strong> Revenue per Employee by city
            </p>
        </div>
        
        <!-- Data Downloads -->
        <div class="section">
            <h2>📥 Data Downloads</h2>
            <h3>Household Data</h3>
            <p>
                <a href="top10_richest_data.csv" class="map-link">📊 Top 10% Household Data (CSV)</a>
                <a href="distance_radius_analysis.csv" class="map-link">📏 Distance Analysis</a>
                <a href="weighted_averages_analysis.csv" class="map-link">⚖️ Weighted Averages</a>
                <a href="hh200k_by_region.csv" class="map-link">🏠 HH by Region</a>
            </p>
            
            <h3>Corporate Data</h3>
            <p>
                <a href="corporate_all_zips.csv" class="map-link corporate">📊 All Corporate ZIPs (CSV)</a>
                <a href="top10_corporate_data.csv" class="map-link corporate">⭐ Top 10% Corporate ZIPs (CSV)</a>
                <a href="industry_by_zip_all.csv" class="map-link corporate">🏭 Industry by ZIP (CSV)</a>
                <a href="corporate_power_by_zip.csv" class="map-link corporate">⚡ Power Industries by ZIP</a>
                <a href="corporate_by_city_summary.csv" class="map-link corporate">🏙️ City Summary</a>
                <a href="corporate_weighted_averages_analysis.csv" class="map-link corporate">⚖️ Weighted Averages</a>
                <a href="corporate_power_industries_by_region.csv" class="map-link corporate">🏭 Power Industries by Region</a>
                <a href="corporate_distance_analysis.csv" class="map-link corporate">📏 Distance Analysis</a>
            </p>
            
            <h3>Intersection Data</h3>
            <p>
                <a href="intersection_analysis.csv" class="map-link intersection">🎯 Intersection ZIPs (CSV)</a>
                <a href="intersection_by_city.csv" class="map-link intersection">🏙️ Intersection by City (CSV)</a>
            </p>
            
            <h3>Documentation</h3>
            <p>
                <a href="helicopter_market_analysis.tex" class="map-link">📄 LaTeX Paper</a>
                <a href="CORPORATE_STATISTICS_EXPLANATION.md" class="map-link corporate">📊 Corporate Statistics Explanation</a>
            </p>
        </div>
        
        <!-- Footer -->
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px;">
            <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            <strong>Data Sources:</strong><br>
            • Households: IRS SOI 2022, Census ACS 5yr 2022, Google Distance Matrix API<br>
            • Corporate: U.S. Census Bureau - County Business Patterns 2021<br>
            <strong>Note:</strong> All data is 100% real from official government sources. No synthetic data used.
        </div>
    </div>
</body>
</html>
"""
    
    # Save
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n  [OK] Dashboard saved: {OUTPUT_FILE}")
    print(f"      Household Top 10%: {stats['hh_zips']}")
    print(f"      Corporate Top 10%: {stats['corp10_zips']}")
    print(f"      Intersection: {stats['intersection_zips']} ({stats['intersection_pct_of_hh']:.1f}% of HH)")

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
    print("\n" + "="*80)
    print("INTEGRATED DASHBOARD GENERATOR (ENHANCED)")
    print("="*80)
    print("\n*** 100% REAL DATA - NO SYNTHETIC DATA ***\n")
    
    # Load data
    data = load_data()
    
    # Calculate statistics
    stats = calculate_statistics(data)
    
    # Create dashboard
    create_dashboard(data, stats)
    
    print("\n" + "="*80)
    print("COMPLETED")
    print("="*80)
