# -*- coding: utf-8 -*-
"""
INTEGRATE STRATEGIC ANALYSIS WITH QUANTITATIVE DATA
====================================================
Cross-references strategic market analysis (competitors, partners, terminals)
with quantitative Top 10% ZIP code analysis for LA and NYC.
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Strategic locations from analysis
STRATEGIC_LOCATIONS = {
    'los_angeles': {
        'competitor_routes': [
            {'route': 'Santa Monica – LAX', 'type': 'BLADE Crowdsource'},
            {'route': 'Santa Monica – LAX', 'type': 'BLADE Charter'},
        ],
        'partner_locations': [
            {'name': 'Helinet Base', 'type': 'Partner'},
            {'name': 'Maverick Base', 'type': 'Partner'},
            {'name': 'LAX', 'type': 'Terminal'},
        ],
        'terminal': 'P/S LAX',
        'zip_prefixes': ['900', '901', '902', '903', '904', '905', '906', '907', '908', '909', 
                         '910', '911', '912', '913', '914', '915', '916', '917', '918',
                         '920', '921', '922', '923', '924', '925', '926', '927', '928'],
    },
    'new_york': {
        'competitor_routes': [
            {'route': 'Manhattan – JFK', 'type': 'BLADE Airport Shuttle'},
            {'route': 'Manhattan – JFK', 'type': 'BLADE Charter'},
            {'route': 'Manhattan – EWR', 'type': 'BLADE'},
            {'route': 'Manhattan – East Hampton', 'type': 'BLADE'},
            {'route': 'Manhattan – Westchester', 'type': 'BLADE'},
            {'route': 'Manhattan – Atlantic City', 'type': 'BLADE'},
        ],
        'partner_locations': [
            {'name': 'Heliflite Base (Kearny, NJ)', 'type': 'Partner'},
            {'name': 'FlexJet Terminal (White Plains)', 'type': 'Partner Terminal'},
            {'name': 'FlexJet Terminal (Teterboro)', 'type': 'Partner Terminal'},
            {'name': 'JFK', 'type': 'Airport'},
            {'name': 'EWR', 'type': 'Airport'},
        ],
        'terminal': 'Kind Of (Not BTG Standard)',
        'zip_prefixes': ['100', '101', '102', '103', '104', '105', '106', '107', '108', '109',
                         '110', '111', '112', '113', '114', '115', '116', '117', '118', '119',
                         '070', '071', '072', '073', '074', '075', '076', '077', '078', '079'],
    }
}

# =============================================================================
# LOAD DATA
# =============================================================================
def load_quantitative_data():
    """Load Top 10% quantitative data"""
    print("\n" + "="*80)
    print("LOADING QUANTITATIVE DATA")
    print("="*80)
    
    # Household Top 10%
    hh_file = os.path.join(BASE_DIR, 'top10_richest_data.csv')
    df_household = pd.read_csv(hh_file, dtype={'zipcode': str})
    df_household = df_household[df_household['city_key'].isin(['los_angeles', 'new_york'])].copy()
    print(f"  Household Top 10% (LA + NYC): {len(df_household)} ZIPs")
    
    # Corporate Top 10%
    corp_file = os.path.join(BASE_DIR, 'top10_corporate_data.csv')
    df_corporate = pd.read_csv(corp_file, dtype={'zipcode': str})
    df_corporate = df_corporate[df_corporate['city_key'].isin(['los_angeles', 'new_york'])].copy()
    print(f"  Corporate Top 10% (LA + NYC): {len(df_corporate)} ZIPs")
    
    # Intersection
    int_file = os.path.join(BASE_DIR, 'intersection_analysis.csv')
    df_intersection = pd.read_csv(int_file, dtype={'zipcode': str})
    df_intersection = df_intersection[df_intersection['city_key'].isin(['los_angeles', 'new_york'])].copy()
    print(f"  Intersection (LA + NYC): {len(df_intersection)} ZIPs")
    
    return df_household, df_corporate, df_intersection

# =============================================================================
# ANALYZE STRATEGIC OVERLAP
# =============================================================================
def analyze_strategic_overlap(df_household, df_corporate, df_intersection):
    """Analyze overlap between strategic locations and Top 10% ZIPs"""
    print("\n" + "="*80)
    print("ANALYZING STRATEGIC OVERLAP")
    print("="*80)
    
    results = {}
    
    for city_key, city_name in [('los_angeles', 'Los Angeles'), ('new_york', 'New York')]:
        print(f"\n  {city_name}:")
        
        # Filter data for this city
        hh_city = df_household[df_household['city_key'] == city_key].copy()
        corp_city = df_corporate[df_corporate['city_key'] == city_key].copy()
        int_city = df_intersection[df_intersection['city_key'] == city_key].copy()
        
        # Get strategic info
        strategic = STRATEGIC_LOCATIONS[city_key]
        
        # Summary statistics
        results[city_key] = {
            'city_name': city_name,
            'household_top10_count': len(hh_city),
            'corporate_top10_count': len(corp_city),
            'intersection_count': len(int_city),
            'competitor_routes': len(strategic['competitor_routes']),
            'partner_locations': len(strategic['partner_locations']),
            'terminal': strategic['terminal'],
            'terminal_status': strategic['terminal'],
            'household_stats': {
                'mean_geometric_score': hh_city['Geometric_Score'].mean() if len(hh_city) > 0 else 0,
                'mean_households_200k': hh_city['Households_200k'].mean() if len(hh_city) > 0 else 0,
                'mean_agi': hh_city['AGI_per_return'].mean() if len(hh_city) > 0 else 0,
            },
            'corporate_stats': {
                'mean_corporate_score': corp_city['Corporate_Score'].mean() if len(corp_city) > 0 else 0,
                'mean_employment': corp_city['total_employment'].mean() if len(corp_city) > 0 else 0,
                'mean_revenue_M': corp_city['estimated_revenue_M'].mean() if len(corp_city) > 0 else 0,
                'mean_power_pct': corp_city['power_emp_pct'].mean() if len(corp_city) > 0 else 0,
            },
            'intersection_stats': {
                'mean_combined_score': int_city['Combined_Score'].mean() if len(int_city) > 0 else 0,
                'total_employment': int_city['total_employment'].sum() if len(int_city) > 0 else 0,
                'total_revenue_M': int_city['estimated_revenue_M'].sum() if len(int_city) > 0 else 0,
            }
        }
        
        print(f"    Household Top 10%: {len(hh_city)} ZIPs")
        print(f"    Corporate Top 10%: {len(corp_city)} ZIPs")
        print(f"    Intersection: {len(int_city)} ZIPs")
        print(f"    Competitor Routes: {len(strategic['competitor_routes'])}")
        print(f"    Partner Locations: {len(strategic['partner_locations'])}")
        print(f"    Terminal: {strategic['terminal']}")
    
    return results

# =============================================================================
# CREATE SUMMARY REPORT
# =============================================================================
def create_summary_report(results):
    """Create summary report integrating strategic and quantitative data"""
    print("\n" + "="*80)
    print("CREATING SUMMARY REPORT")
    print("="*80)
    
    report_lines = []
    report_lines.append("# Strategic Market Analysis - LA & NYC Integration Report")
    report_lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report_lines.append("="*80)
    
    for city_key in ['los_angeles', 'new_york']:
        r = results[city_key]
        report_lines.append(f"\n## {r['city_name']}")
        report_lines.append("-"*80)
        
        report_lines.append(f"\n### Top 10% Quantitative Analysis")
        report_lines.append(f"- **Household Top 10%:** {r['household_top10_count']} ZIPs")
        report_lines.append(f"- **Corporate Top 10%:** {r['corporate_top10_count']} ZIPs")
        report_lines.append(f"- **Intersection:** {r['intersection_count']} ZIPs")
        
        report_lines.append(f"\n### Household Wealth Metrics (Top 10%)")
        report_lines.append(f"- Mean Geometric Score: {r['household_stats']['mean_geometric_score']:.4f}")
        report_lines.append(f"- Mean Households $200k+: {r['household_stats']['mean_households_200k']:,.0f}")
        report_lines.append(f"- Mean AGI per Return: ${r['household_stats']['mean_agi']:,.0f}")
        
        report_lines.append(f"\n### Corporate Power Metrics (Top 10%)")
        report_lines.append(f"- Mean Corporate Score: {r['corporate_stats']['mean_corporate_score']:.4f}")
        report_lines.append(f"- Mean Employment: {r['corporate_stats']['mean_employment']:,.0f}")
        report_lines.append(f"- Mean Revenue: ${r['corporate_stats']['mean_revenue_M']:,.0f}M")
        report_lines.append(f"- Mean Power Industries %: {r['corporate_stats']['mean_power_pct']:.1f}%")
        
        report_lines.append(f"\n### Intersection Analysis")
        report_lines.append(f"- Mean Combined Score: {r['intersection_stats']['mean_combined_score']:.4f}")
        report_lines.append(f"- Total Employment: {r['intersection_stats']['total_employment']:,.0f}")
        report_lines.append(f"- Total Revenue: ${r['intersection_stats']['total_revenue_M']:,.0f}M")
        
        report_lines.append(f"\n### Strategic Market Context")
        report_lines.append(f"- **Competitor Routes:** {r['competitor_routes']} active routes")
        report_lines.append(f"- **Partner Locations:** {r['partner_locations']} potential partner locations")
        report_lines.append(f"- **Terminal Infrastructure:** {r['terminal']}")
        
        report_lines.append(f"\n### Strategic Insights")
        if city_key == 'los_angeles':
            report_lines.append("- LA has superior terminal infrastructure (P/S LAX) providing competitive advantage")
            report_lines.append("- BLADE operates charter-only in LA, creating opportunity for scheduled services")
            report_lines.append("- Multiple potential partners (Helinet, Maverick) with established infrastructure")
        else:
            report_lines.append("- NYC has multiple competitor routes, indicating high market demand")
            report_lines.append("- Terminal infrastructure not at BTG standard, creating opportunity")
            report_lines.append("- Strong partner ecosystem (Heliflite, FlexJet) with private terminals")
        
        report_lines.append("")
    
    # Save report
    report_file = os.path.join(BASE_DIR, 'STRATEGIC_INTEGRATION_REPORT.md')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    print(f"\n  [OK] Saved: {report_file}")
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    for city_key in ['los_angeles', 'new_york']:
        r = results[city_key]
        print(f"\n{r['city_name']}:")
        print(f"  Top 10% ZIPs: {r['household_top10_count']} (HH) + {r['corporate_top10_count']} (Corp) = {r['intersection_count']} intersection")
        print(f"  Strategic Context: {r['competitor_routes']} competitor routes, {r['partner_locations']} partner locations")
        print(f"  Terminal: {r['terminal']}")

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
    print("\n" + "="*80)
    print("INTEGRATE STRATEGIC ANALYSIS WITH QUANTITATIVE DATA")
    print("="*80)
    
    # Load data
    df_household, df_corporate, df_intersection = load_quantitative_data()
    
    # Analyze overlap
    results = analyze_strategic_overlap(df_household, df_corporate, df_intersection)
    
    # Create report
    create_summary_report(results)
    
    print("\n" + "="*80)
    print("COMPLETED")
    print("="*80)

