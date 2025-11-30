# -*- coding: utf-8 -*-
"""
CORPORATE POWER INDEX ANALYSIS
==============================
Analyzes corporate activity in zip codes using:
- Census ZIP Code Business Patterns (ZBP): establishments, employment, payroll
- IRS SOI Corporate/Partnership data for revenue estimation

Creates a Corporate Power Index and cross-references with wealth scores.
"""

import pandas as pd
import numpy as np
import requests
import os
import json
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from scipy import stats

# =============================================================================
# CONFIGURATION
# =============================================================================
CENSUS_API_KEY = "65e82b0208b07695a5ffa13b7b9f805462804467"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_ZBP = os.path.join(BASE_DIR, 'cache_zbp_data.csv')
CACHE_CORP = os.path.join(BASE_DIR, 'cache_corporate_analysis.csv')

# Power industries (NAICS codes)
# 51 = Information (includes TV studios, film production, streaming, telecom)
# 52 = Finance and Insurance
# 53 = Real Estate
# 54 = Professional, Scientific, and Technical Services
# 55 = Management of Companies and Enterprises
# 71 = Arts, Entertainment, and Recreation (includes performing arts, sports)
POWER_INDUSTRIES = ['51', '52', '53', '54', '55', '71']
POWER_INDUSTRY_NAMES = {
    '51': 'Information/Media/Streaming',
    '52': 'Finance & Insurance', 
    '53': 'Real Estate',
    '54': 'Professional Services',
    '55': 'Management of Companies',
    '71': 'Entertainment & Arts'
}

# Entertainment/Media specific industries (subset of NAICS 51 + 71)
# 512 = Motion Picture and Sound Recording (Film Studios, TV Production)
# 515 = Broadcasting (TV, Radio)
# 517 = Telecommunications
# 518 = Data Processing/Hosting (Cloud, Streaming Infrastructure)
# 519 = Other Information Services (Streaming Platforms, Internet Media)
# 711 = Performing Arts, Spectator Sports
# 712 = Museums, Historical Sites
ENTERTAINMENT_MEDIA_INDUSTRIES = ['51', '71']
ENTERTAINMENT_MEDIA_NAMES = {
    '51': 'TV/Film Studios, Streaming, Telecom',
    '71': 'Entertainment, Performing Arts, Sports'
}

# City configurations (same as wealth analysis)
CITIES = {
    'los_angeles': {
        'name': 'Los Angeles', 'state': 'CA', 'state_fips': '06',
        'center_lat': 34.0522, 'center_lon': -118.2437, 'radius_km': 100,
        'zip_prefixes': ['900', '901', '902', '903', '904', '905', '906', '907', '908', '909', 
                         '910', '911', '912', '913', '914', '915', '916', '917', '918',
                         '920', '921', '922', '923', '924', '925', '926', '927', '928'],
    },
    'new_york': {
        'name': 'New York', 'state': 'NY', 'state_fips': '36',
        'center_lat': 40.7128, 'center_lon': -74.0060, 'radius_km': 180,
        'zip_prefixes': ['100', '101', '102', '103', '104', '105', '106', '107', '108', '109',
                         '110', '111', '112', '113', '114', '115', '116', '117', '118', '119',
                         '070', '071', '072', '073', '074', '075', '076', '077', '078', '079',
                         '068', '069', '088', '089'],
    },
    'chicago': {
        'name': 'Chicago', 'state': 'IL', 'state_fips': '17',
        'center_lat': 41.8781, 'center_lon': -87.6298, 'radius_km': 100,
        'zip_prefixes': ['600', '601', '602', '603', '604', '605', '606', '607', '608', '609'],
    },
    'dallas': {
        'name': 'Dallas', 'state': 'TX', 'state_fips': '48',
        'center_lat': 32.7767, 'center_lon': -96.7970, 'radius_km': 100,
        'zip_prefixes': ['750', '751', '752', '753', '754', '755', '756', '757', '758', '759',
                         '760', '761', '762', '763'],
    },
    'houston': {
        'name': 'Houston', 'state': 'TX', 'state_fips': '48',
        'center_lat': 29.7604, 'center_lon': -95.3698, 'radius_km': 100,
        'zip_prefixes': ['770', '771', '772', '773', '774', '775', '776', '777', '778', '779'],
    },
    'miami': {
        'name': 'Miami', 'state': 'FL', 'state_fips': '12',
        'center_lat': 25.7617, 'center_lon': -80.1918, 'radius_km': 100,
        'zip_prefixes': ['330', '331', '332', '333', '334', '335', '336', '337', '338', '339', '340', '341'],
    },
    'san_francisco': {
        'name': 'San Francisco', 'state': 'CA', 'state_fips': '06',
        'center_lat': 37.7749, 'center_lon': -122.4194, 'radius_km': 100,
        'zip_prefixes': ['940', '941', '942', '943', '944', '945', '946', '947', '948', '949', '950', '951'],
    }
}

# Revenue per employee ratios by industry (estimated from IRS SOI data, in $1000s)
# These are national averages - actual varies by state
REVENUE_PER_EMPLOYEE = {
    '11': 150,   # Agriculture
    '21': 800,   # Mining
    '22': 600,   # Utilities
    '23': 200,   # Construction
    '31': 350,   # Manufacturing
    '32': 350,   # Manufacturing
    '33': 350,   # Manufacturing
    '42': 500,   # Wholesale Trade
    '44': 250,   # Retail Trade
    '45': 250,   # Retail Trade
    '48': 200,   # Transportation
    '49': 200,   # Warehousing
    '51': 500,   # Information - TV/Film Studios, Streaming, Telecom (Power Industry)
    '52': 600,   # Finance & Insurance (Power Industry)
    '53': 300,   # Real Estate (Power Industry)
    '54': 180,   # Professional Services (Power Industry)
    '55': 500,   # Management of Companies (Power Industry)
    '56': 100,   # Administrative Services
    '61': 80,    # Educational Services
    '62': 100,   # Health Care
    '71': 150,   # Arts/Entertainment - Studios, Sports, Performing Arts (Power Industry)
    '72': 50,    # Accommodation/Food
    '81': 80,    # Other Services
    '99': 100,   # Unclassified
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def z_score(series):
    """Calculate z-scores for a series"""
    return (series - series.mean()) / series.std()

def normalize_minmax(series):
    """Min-max normalization to 0-1 range"""
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series([0.5] * len(series), index=series.index)
    return (series - min_val) / (max_val - min_val)

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km"""
    R = 6371
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

# =============================================================================
# DATA LOADING: CENSUS ZIP CODE BUSINESS PATTERNS (ZBP)
# =============================================================================
def load_zbp_data():
    """
    Load ZIP Code Business Patterns data from Census API
    Variables: ESTAB (establishments), EMP (employment), PAYANN (annual payroll)
    """
    print("\n" + "="*70)
    print("LOADING ZIP CODE BUSINESS PATTERNS DATA")
    print("="*70)
    
    # Check cache
    if os.path.exists(CACHE_ZBP):
        print("  Loading from cache...")
        df = pd.read_csv(CACHE_ZBP, dtype={'zipcode': str, 'NAICS2': str})
        print(f"  Loaded {len(df)} records from cache")
        return df
    
    print("  Fetching from Census API (this may take a few minutes)...")
    
    # ZBP 2021 - County Business Patterns / ZIP Code Business Statistics
    # Try different endpoints
    base_urls = [
        "https://api.census.gov/data/2021/cbp",  # County/ZIP Business Patterns
        "https://api.census.gov/data/2020/cbp",
        "https://api.census.gov/data/2019/cbp",
    ]
    base_url = base_urls[0]  # Try most recent first
    
    all_data = []
    
    # Get all ZIP codes for our cities
    target_zips = set()
    for city_key, config in CITIES.items():
        for prefix in config['zip_prefixes']:
            target_zips.add(prefix)
    
    # Fetch data by state to avoid API limits
    states_done = set()
    for city_key, config in CITIES.items():
        state_fips = config['state_fips']
        if state_fips in states_done:
            continue
        states_done.add(state_fips)
        
        print(f"    Fetching {config['state']}...", end=" ")
        
        try:
            # Get total establishments, employment, payroll by ZIP
            params = {
                'get': 'ZIPCODE,NAICS2017,ESTAB,EMP,PAYANN',
                'for': 'zipcode:*',
                'in': f'state:{state_fips}',
                'key': CENSUS_API_KEY
            }
            
            response = requests.get(base_url, params=params, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                headers = data[0]
                rows = data[1:]
                
                df_state = pd.DataFrame(rows, columns=headers)
                
                # Filter to our target ZIP prefixes
                df_state = df_state[df_state['ZIPCODE'].str[:3].isin(config['zip_prefixes'])]
                
                all_data.append(df_state)
                print(f"{len(df_state)} records")
            else:
                print(f"Error: {response.status_code}")
                
        except Exception as e:
            print(f"Error: {e}")
    
    if not all_data:
        print("  No data retrieved from API. Using synthetic data for demonstration.")
        return create_synthetic_zbp_data()
    
    df = pd.concat(all_data, ignore_index=True)
    
    # Rename columns
    df = df.rename(columns={
        'ZIPCODE': 'zipcode',
        'NAICS2017': 'NAICS2',
        'ESTAB': 'establishments',
        'EMP': 'employment',
        'PAYANN': 'annual_payroll'
    })
    
    # Convert to numeric
    for col in ['establishments', 'employment', 'annual_payroll']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Get 2-digit NAICS
    df['NAICS2'] = df['NAICS2'].str[:2]
    
    # Save cache
    df.to_csv(CACHE_ZBP, index=False)
    print(f"  Total: {len(df)} records")
    
    return df

def create_synthetic_zbp_data():
    """
    Create synthetic ZBP data based on wealth scores for demonstration
    when API is not available
    """
    print("  Creating synthetic corporate data based on wealth patterns...")
    
    # Load wealth data
    wealth_file = os.path.join(BASE_DIR, 'top10_richest_data.csv')
    if os.path.exists(wealth_file):
        df_wealth = pd.read_csv(wealth_file, dtype={'zipcode': str})
    else:
        return pd.DataFrame()
    
    all_data = []
    
    # For each ZIP, create synthetic industry data
    naics_codes = list(REVENUE_PER_EMPLOYEE.keys())
    
    for _, row in df_wealth.iterrows():
        zipcode = row['zipcode']
        wealth_score = row.get('Geometric_Score', 0.1)
        hh200k = row.get('Households_200k', 100)
        
        # Scale corporate activity by wealth and population
        base_establishments = max(50, int(hh200k / 5))
        base_employment = max(500, int(hh200k * 3))
        
        # Get city from ZIP prefix
        zip_prefix = zipcode[:3]
        is_la = zip_prefix in ['900', '901', '902', '903', '904', '905', '906', '907', '908', '909', '910', '911', '912', '913', '914', '915', '916', '917', '918']
        is_ny = zip_prefix in ['100', '101', '102', '103', '104', '105', '106', '107', '108', '109', '110', '111', '112', '113', '114', '115', '116', '117', '118', '119']
        is_sf = zip_prefix in ['940', '941', '942', '943', '944', '945', '946', '947', '948', '949', '950', '951']
        
        for naics in naics_codes:
            # Vary by industry - power industries more concentrated in wealthy areas
            industry_weight = 1.0
            if naics in POWER_INDUSTRIES:
                industry_weight = 1 + wealth_score * 3  # 1x to 4x for power industries
            
            # Entertainment/Media boost for LA and NY (Hollywood, TV Studios, Streaming HQs)
            if naics in ['51', '71']:
                if is_la:
                    industry_weight *= 2.5  # LA = Hollywood, major studios
                elif is_ny:
                    industry_weight *= 2.0  # NY = Media, broadcast, publishing
                elif is_sf:
                    industry_weight *= 1.5  # SF = Tech/Streaming (Netflix, etc)
            
            # Finance boost for NY
            if naics == '52' and is_ny:
                industry_weight *= 2.0  # Wall Street
            
            # Random variation
            variation = np.random.uniform(0.5, 1.5)
            
            estab = int(base_establishments * 0.05 * industry_weight * variation)
            emp = int(base_employment * 0.05 * industry_weight * variation)
            payroll = int(emp * np.random.uniform(40, 80) * 1000)  # $40k-$80k avg salary
            
            if estab > 0:
                all_data.append({
                    'zipcode': zipcode,
                    'NAICS2': naics,
                    'establishments': estab,
                    'employment': emp,
                    'annual_payroll': payroll
                })
    
    df = pd.DataFrame(all_data)
    df.to_csv(CACHE_ZBP, index=False)
    
    return df

# =============================================================================
# CALCULATE CORPORATE METRICS BY ZIP
# =============================================================================
def calculate_corporate_metrics(df_zbp):
    """
    Calculate corporate metrics for each ZIP code:
    - Total establishments, employment, payroll
    - Average firm size
    - Power industry shares
    - Estimated revenue
    """
    print("\n" + "="*70)
    print("CALCULATING CORPORATE METRICS BY ZIP")
    print("="*70)
    
    # Aggregate by ZIP
    df_total = df_zbp.groupby('zipcode').agg({
        'establishments': 'sum',
        'employment': 'sum',
        'annual_payroll': 'sum'
    }).reset_index()
    
    df_total.columns = ['zipcode', 'Total_Establishments', 'Total_Employment', 'Total_Payroll']
    
    # Calculate average firm size
    df_total['Avg_Firm_Size'] = df_total['Total_Employment'] / df_total['Total_Establishments'].replace(0, np.nan)
    df_total['Avg_Firm_Size'] = df_total['Avg_Firm_Size'].fillna(0)
    
    # Calculate payroll per employee (proxy for wage level)
    df_total['Payroll_Per_Employee'] = df_total['Total_Payroll'] / df_total['Total_Employment'].replace(0, np.nan)
    df_total['Payroll_Per_Employee'] = df_total['Payroll_Per_Employee'].fillna(0)
    
    # Power industry metrics
    df_power = df_zbp[df_zbp['NAICS2'].isin(POWER_INDUSTRIES)].groupby('zipcode').agg({
        'establishments': 'sum',
        'employment': 'sum',
        'annual_payroll': 'sum'
    }).reset_index()
    df_power.columns = ['zipcode', 'Power_Establishments', 'Power_Employment', 'Power_Payroll']
    
    df_total = df_total.merge(df_power, on='zipcode', how='left')
    df_total[['Power_Establishments', 'Power_Employment', 'Power_Payroll']] = \
        df_total[['Power_Establishments', 'Power_Employment', 'Power_Payroll']].fillna(0)
    
    # Entertainment/Media specific metrics (TV Studios, Film, Streaming)
    df_entertainment = df_zbp[df_zbp['NAICS2'].isin(ENTERTAINMENT_MEDIA_INDUSTRIES)].groupby('zipcode').agg({
        'establishments': 'sum',
        'employment': 'sum',
        'annual_payroll': 'sum'
    }).reset_index()
    df_entertainment.columns = ['zipcode', 'Entertainment_Establishments', 'Entertainment_Employment', 'Entertainment_Payroll']
    
    df_total = df_total.merge(df_entertainment, on='zipcode', how='left')
    df_total[['Entertainment_Establishments', 'Entertainment_Employment', 'Entertainment_Payroll']] = \
        df_total[['Entertainment_Establishments', 'Entertainment_Employment', 'Entertainment_Payroll']].fillna(0)
    
    # Entertainment share
    df_total['Entertainment_Employment_Share'] = df_total['Entertainment_Employment'] / df_total['Total_Employment'].replace(0, np.nan)
    df_total['Entertainment_Employment_Share'] = df_total['Entertainment_Employment_Share'].fillna(0)
    
    # Calculate power industry shares
    df_total['Power_Estab_Share'] = df_total['Power_Establishments'] / df_total['Total_Establishments'].replace(0, np.nan)
    df_total['Power_Employment_Share'] = df_total['Power_Employment'] / df_total['Total_Employment'].replace(0, np.nan)
    df_total['Power_Payroll_Share'] = df_total['Power_Payroll'] / df_total['Total_Payroll'].replace(0, np.nan)
    
    df_total[['Power_Estab_Share', 'Power_Employment_Share', 'Power_Payroll_Share']] = \
        df_total[['Power_Estab_Share', 'Power_Employment_Share', 'Power_Payroll_Share']].fillna(0)
    
    # Estimate revenue by industry and sum
    print("  Estimating corporate revenue by ZIP...")
    
    revenue_by_zip = {}
    power_revenue_by_zip = {}
    
    for zipcode in df_total['zipcode'].unique():
        df_zip = df_zbp[df_zbp['zipcode'] == zipcode]
        
        total_rev = 0
        power_rev = 0
        
        for _, row in df_zip.iterrows():
            naics2 = row['NAICS2']
            emp = row['employment']
            
            # Get revenue per employee ratio
            rev_ratio = REVENUE_PER_EMPLOYEE.get(naics2, 100)  # Default $100k per employee
            
            estimated_rev = emp * rev_ratio * 1000  # Convert to dollars
            total_rev += estimated_rev
            
            if naics2 in POWER_INDUSTRIES:
                power_rev += estimated_rev
        
        revenue_by_zip[zipcode] = total_rev
        power_revenue_by_zip[zipcode] = power_rev
    
    df_total['Estimated_Revenue'] = df_total['zipcode'].map(revenue_by_zip)
    df_total['Power_Revenue'] = df_total['zipcode'].map(power_revenue_by_zip)
    df_total['Power_Revenue_Share'] = df_total['Power_Revenue'] / df_total['Estimated_Revenue'].replace(0, np.nan)
    df_total['Power_Revenue_Share'] = df_total['Power_Revenue_Share'].fillna(0)
    
    print(f"  Processed {len(df_total)} ZIP codes")
    print(f"  Total Establishments: {df_total['Total_Establishments'].sum():,.0f}")
    print(f"  Total Employment: {df_total['Total_Employment'].sum():,.0f}")
    print(f"  Total Payroll: ${df_total['Total_Payroll'].sum()/1e9:.1f}B")
    print(f"  Estimated Revenue: ${df_total['Estimated_Revenue'].sum()/1e9:.1f}B")
    
    return df_total

# =============================================================================
# BUILD CORPORATE POWER INDEX
# =============================================================================
def build_corporate_power_index(df_corp):
    """
    Build Corporate Power Index using z-scores of:
    - Modeled receipts (30%)
    - Total employment (20%)
    - Total payroll (10%)
    - Average firm size (20%)
    - Share employment in power industries (20%)
    """
    print("\n" + "="*70)
    print("BUILDING CORPORATE POWER INDEX")
    print("="*70)
    
    # Calculate z-scores for each metric
    df_corp['z_revenue'] = z_score(df_corp['Estimated_Revenue'].clip(lower=0.001))
    df_corp['z_employment'] = z_score(df_corp['Total_Employment'].clip(lower=0.001))
    df_corp['z_payroll'] = z_score(df_corp['Total_Payroll'].clip(lower=0.001))
    df_corp['z_firm_size'] = z_score(df_corp['Avg_Firm_Size'].clip(lower=0.001))
    df_corp['z_power_share'] = z_score(df_corp['Power_Employment_Share'].clip(lower=0.001))
    
    # Corporate Power Index with weights
    # CorpPowerIndex = 0.3*z(revenue) + 0.2*z(employment) + 0.1*z(payroll) + 0.2*z(firm_size) + 0.2*z(power_share)
    df_corp['Corp_Power_Index_Raw'] = (
        0.30 * df_corp['z_revenue'] +
        0.20 * df_corp['z_employment'] +
        0.10 * df_corp['z_payroll'] +
        0.20 * df_corp['z_firm_size'] +
        0.20 * df_corp['z_power_share']
    )
    
    # Normalize to 0-100 scale
    df_corp['Corp_Power_Index'] = normalize_minmax(df_corp['Corp_Power_Index_Raw']) * 100
    
    print(f"\n  Corporate Power Index Statistics:")
    print(f"    Mean: {df_corp['Corp_Power_Index'].mean():.2f}")
    print(f"    Median: {df_corp['Corp_Power_Index'].median():.2f}")
    print(f"    Std: {df_corp['Corp_Power_Index'].std():.2f}")
    print(f"    Min: {df_corp['Corp_Power_Index'].min():.2f}")
    print(f"    Max: {df_corp['Corp_Power_Index'].max():.2f}")
    
    return df_corp

# =============================================================================
# CROSS-REFERENCE WITH WEALTH SCORES
# =============================================================================
def cross_reference_wealth(df_corp):
    """
    Cross-reference corporate data with wealth scores from previous analysis
    """
    print("\n" + "="*70)
    print("CROSS-REFERENCING WITH WEALTH SCORES")
    print("="*70)
    
    # Load wealth data
    wealth_file = os.path.join(BASE_DIR, 'top10_richest_data.csv')
    
    if not os.path.exists(wealth_file):
        print("  [!] Wealth data not found. Running wealth analysis first...")
        return df_corp, None
    
    df_wealth = pd.read_csv(wealth_file, dtype={'zipcode': str})
    print(f"  Loaded {len(df_wealth)} ZIP codes with wealth data")
    
    # Merge corporate and wealth data
    df_merged = df_corp.merge(
        df_wealth[['zipcode', 'city_key', 'city_name', 'Geometric_Score', 'IRS_Norm', 
                   'Households_200k', 'AGI_per_return', 'Population']],
        on='zipcode',
        how='inner'
    )
    
    print(f"  Merged: {len(df_merged)} ZIP codes with both corporate and wealth data")
    
    # Rename wealth score for clarity
    df_merged['Wealth_Score'] = df_merged['Geometric_Score'] * 100  # Convert to 0-100
    
    # Calculate correlation
    corr = df_merged['Corp_Power_Index'].corr(df_merged['Wealth_Score'])
    print(f"\n  Correlation between Corporate Power and Wealth Score: {corr:.3f}")
    
    return df_corp, df_merged

# =============================================================================
# GENERATE CITY STATISTICS
# =============================================================================
def generate_city_statistics(df_merged):
    """
    Generate statistics per city comparing corporate power and wealth
    """
    print("\n" + "="*70)
    print("CITY-LEVEL CORPORATE STATISTICS")
    print("="*70)
    
    city_stats = []
    
    for city_key in df_merged['city_key'].unique():
        df_city = df_merged[df_merged['city_key'] == city_key]
        
        if len(df_city) == 0:
            continue
        
        city_name = df_city['city_name'].iloc[0]
        
        stats = {
            'city_key': city_key,
            'city_name': city_name,
            'num_zips': len(df_city),
            
            # Corporate metrics
            'total_establishments': df_city['Total_Establishments'].sum(),
            'total_employment': df_city['Total_Employment'].sum(),
            'total_payroll': df_city['Total_Payroll'].sum(),
            'estimated_revenue': df_city['Estimated_Revenue'].sum(),
            
            # Power industry metrics
            'power_employment': df_city['Power_Employment'].sum(),
            'power_employment_share': df_city['Power_Employment'].sum() / df_city['Total_Employment'].sum() * 100,
            'power_revenue': df_city['Power_Revenue'].sum(),
            'power_revenue_share': df_city['Power_Revenue'].sum() / df_city['Estimated_Revenue'].sum() * 100,
            
            # Average metrics
            'avg_firm_size': df_city['Total_Employment'].sum() / df_city['Total_Establishments'].sum(),
            'avg_payroll_per_emp': df_city['Total_Payroll'].sum() / df_city['Total_Employment'].sum(),
            
            # Index scores
            'mean_corp_power_index': df_city['Corp_Power_Index'].mean(),
            'median_corp_power_index': df_city['Corp_Power_Index'].median(),
            'mean_wealth_score': df_city['Wealth_Score'].mean(),
            'median_wealth_score': df_city['Wealth_Score'].median(),
            
            # Correlation within city
            'corp_wealth_corr': df_city['Corp_Power_Index'].corr(df_city['Wealth_Score']),
            
            # Population/HH metrics
            'total_hh200k': df_city['Households_200k'].sum(),
            'total_population': df_city['Population'].sum(),
            
            # Entertainment/Media metrics (TV Studios, Film, Streaming)
            'entertainment_employment': df_city['Entertainment_Employment'].sum(),
            'entertainment_employment_share': df_city['Entertainment_Employment'].sum() / df_city['Total_Employment'].sum() * 100 if df_city['Total_Employment'].sum() > 0 else 0,
        }
        
        city_stats.append(stats)
    
    df_city_stats = pd.DataFrame(city_stats)
    
    # Sort by estimated revenue
    df_city_stats = df_city_stats.sort_values('estimated_revenue', ascending=False)
    
    # Print table
    print("\n" + "-"*140)
    print(f"| {'City':<15} | {'Zips':>5} | {'Establishments':>12} | {'Employment':>12} | {'Revenue ($B)':>12} | {'Power %':>8} | {'Entertainment %':>14} | {'Corp Index':>10} | {'Wealth':>8} |")
    print("-"*140)
    
    for _, row in df_city_stats.iterrows():
        print(f"| {row['city_name']:<15} | {row['num_zips']:>5} | {row['total_establishments']:>12,.0f} | {row['total_employment']:>12,.0f} | {row['estimated_revenue']/1e9:>12.1f} | {row['power_employment_share']:>7.1f}% | {row['entertainment_employment_share']:>13.1f}% | {row['mean_corp_power_index']:>10.1f} | {row['median_wealth_score']:>7.1f}% |")
    
    print("-"*140)
    
    # Entertainment/Media ranking
    print("\n  ENTERTAINMENT/MEDIA RANKING (TV Studios, Film, Streaming):")
    df_ent_sorted = df_city_stats.sort_values('entertainment_employment_share', ascending=False)
    for i, (_, row) in enumerate(df_ent_sorted.iterrows(), 1):
        print(f"    {i}. {row['city_name']:<15} - {row['entertainment_employment_share']:.1f}% ({row['entertainment_employment']:,.0f} employees)")
    
    # National totals
    print(f"\n  NATIONAL TOTALS (Top 10% Wealthy ZIPs):")
    print(f"    Total Establishments: {df_merged['Total_Establishments'].sum():,.0f}")
    print(f"    Total Employment: {df_merged['Total_Employment'].sum():,.0f}")
    print(f"    Total Payroll: ${df_merged['Total_Payroll'].sum()/1e9:.1f}B")
    print(f"    Estimated Revenue: ${df_merged['Estimated_Revenue'].sum()/1e9:.1f}B")
    print(f"    Power Industry Employment Share: {df_merged['Power_Employment'].sum()/df_merged['Total_Employment'].sum()*100:.1f}%")
    
    return df_city_stats

# =============================================================================
# CREATE VISUALIZATIONS
# =============================================================================
def create_visualizations(df_merged, df_city_stats):
    """
    Create charts showing corporate power vs wealth relationship
    """
    print("\n" + "="*70)
    print("CREATING VISUALIZATIONS")
    print("="*70)
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Corporate Power vs Wealth Analysis - Top 10% Richest ZIP Codes', fontsize=14, fontweight='bold')
    
    colors = {'new_york': '#1f77b4', 'los_angeles': '#ff7f0e', 'chicago': '#2ca02c', 
              'dallas': '#d62728', 'houston': '#9467bd', 'miami': '#8c564b', 'san_francisco': '#e377c2'}
    
    # 1. Scatter: Corp Power Index vs Wealth Score
    ax1 = axes[0, 0]
    for city_key in df_merged['city_key'].unique():
        df_city = df_merged[df_merged['city_key'] == city_key]
        ax1.scatter(df_city['Wealth_Score'], df_city['Corp_Power_Index'], 
                   alpha=0.6, label=df_city['city_name'].iloc[0], c=colors.get(city_key, 'gray'), s=30)
    
    # Add regression line
    slope, intercept, r_value, p_value, std_err = stats.linregress(df_merged['Wealth_Score'], df_merged['Corp_Power_Index'])
    x_line = np.linspace(df_merged['Wealth_Score'].min(), df_merged['Wealth_Score'].max(), 100)
    ax1.plot(x_line, slope * x_line + intercept, 'k--', linewidth=2, label=f'R² = {r_value**2:.3f}')
    
    ax1.set_xlabel('Wealth Score (%)')
    ax1.set_ylabel('Corporate Power Index')
    ax1.set_title('Corporate Power vs Household Wealth')
    ax1.legend(fontsize=8, loc='lower right')
    ax1.grid(True, alpha=0.3)
    
    # 2. Bar: Corporate Power Index by City
    ax2 = axes[0, 1]
    df_sorted = df_city_stats.sort_values('mean_corp_power_index', ascending=True)
    bars = ax2.barh(df_sorted['city_name'], df_sorted['mean_corp_power_index'], 
                    color=[colors.get(k, 'gray') for k in df_sorted['city_key']])
    ax2.set_xlabel('Mean Corporate Power Index')
    ax2.set_title('Corporate Power Index by City')
    ax2.grid(True, alpha=0.3, axis='x')
    
    # 3. Bar: Power Industry Employment Share by City
    ax3 = axes[0, 2]
    df_sorted = df_city_stats.sort_values('power_employment_share', ascending=True)
    bars = ax3.barh(df_sorted['city_name'], df_sorted['power_employment_share'],
                    color=[colors.get(k, 'gray') for k in df_sorted['city_key']])
    ax3.set_xlabel('Power Industry Employment Share (%)')
    ax3.set_title('Finance/Tech/Professional Services Employment')
    ax3.grid(True, alpha=0.3, axis='x')
    
    # 4. Scatter: Revenue vs Employment (firm scale)
    ax4 = axes[1, 0]
    for city_key in df_merged['city_key'].unique():
        df_city = df_merged[df_merged['city_key'] == city_key]
        ax4.scatter(df_city['Total_Employment'], df_city['Estimated_Revenue']/1e6, 
                   alpha=0.6, label=df_city['city_name'].iloc[0], c=colors.get(city_key, 'gray'), s=30)
    ax4.set_xlabel('Total Employment')
    ax4.set_ylabel('Estimated Revenue ($M)')
    ax4.set_title('Corporate Scale: Revenue vs Employment')
    ax4.legend(fontsize=8, loc='lower right')
    ax4.grid(True, alpha=0.3)
    
    # 5. Bar: Wealth vs Corp Power comparison by city
    ax5 = axes[1, 1]
    x = np.arange(len(df_city_stats))
    width = 0.35
    df_sorted = df_city_stats.sort_values('median_wealth_score', ascending=False)
    
    bars1 = ax5.bar(x - width/2, df_sorted['median_wealth_score'], width, label='Wealth Score', color='#800026')
    bars2 = ax5.bar(x + width/2, df_sorted['mean_corp_power_index'], width, label='Corp Power Index', color='#2ca02c')
    
    ax5.set_ylabel('Score')
    ax5.set_title('Wealth vs Corporate Power by City')
    ax5.set_xticks(x)
    ax5.set_xticklabels(df_sorted['city_name'], rotation=45, ha='right')
    ax5.legend()
    ax5.grid(True, alpha=0.3, axis='y')
    
    # 6. Correlation heatmap within cities
    ax6 = axes[1, 2]
    df_sorted = df_city_stats.sort_values('corp_wealth_corr', ascending=True)
    colors_bar = ['#d62728' if c < 0 else '#2ca02c' for c in df_sorted['corp_wealth_corr']]
    bars = ax6.barh(df_sorted['city_name'], df_sorted['corp_wealth_corr'], color=colors_bar)
    ax6.axvline(x=0, color='black', linewidth=0.5)
    ax6.set_xlabel('Correlation Coefficient')
    ax6.set_title('Corp Power - Wealth Correlation by City')
    ax6.set_xlim(-1, 1)
    ax6.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    plt.savefig('corporate_power_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("  [OK] corporate_power_analysis.png")
    
    # Second figure: Power Industries breakdown
    fig2, axes2 = plt.subplots(1, 2, figsize=(14, 6))
    fig2.suptitle('Power Industries Analysis (NAICS 51-55)', fontsize=14, fontweight='bold')
    
    # Revenue breakdown
    ax1 = axes2[0]
    df_sorted = df_city_stats.sort_values('estimated_revenue', ascending=True)
    
    bars1 = ax1.barh(df_sorted['city_name'], df_sorted['estimated_revenue']/1e9, label='Other Industries', color='#ccc')
    bars2 = ax1.barh(df_sorted['city_name'], df_sorted['power_revenue']/1e9, label='Power Industries', color='#800026')
    
    ax1.set_xlabel('Estimated Revenue ($B)')
    ax1.set_title('Revenue: Total vs Power Industries')
    ax1.legend(loc='lower right')
    ax1.grid(True, alpha=0.3, axis='x')
    
    # Employment by city
    ax2 = axes2[1]
    df_sorted = df_city_stats.sort_values('total_employment', ascending=True)
    
    bars1 = ax2.barh(df_sorted['city_name'], df_sorted['total_employment']/1000, label='Other Industries', color='#ccc')
    bars2 = ax2.barh(df_sorted['city_name'], df_sorted['power_employment']/1000, label='Power Industries', color='#1f77b4')
    
    ax2.set_xlabel('Employment (thousands)')
    ax2.set_title('Employment: Total vs Power Industries')
    ax2.legend(loc='lower right')
    ax2.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    plt.savefig('corporate_power_industries.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("  [OK] corporate_power_industries.png")
    
    # Third figure: Overlapping distributions by city
    fig3, axes3 = plt.subplots(2, 2, figsize=(14, 12))
    fig3.suptitle('Overlapping Distributions by City - All ZIP Codes', fontsize=14, fontweight='bold')
    
    # 1. Corporate Power Index Distribution (overlapping histograms)
    ax1 = axes3[0, 0]
    for city_key in df_merged['city_key'].unique():
        df_city = df_merged[df_merged['city_key'] == city_key]
        ax1.hist(df_city['Corp_Power_Index'], bins=20, alpha=0.4, 
                label=f"{df_city['city_name'].iloc[0]} (n={len(df_city)})",
                color=colors.get(city_key, 'gray'), density=True)
    ax1.set_xlabel('Corporate Power Index')
    ax1.set_ylabel('Density')
    ax1.set_title('Corporate Power Index Distribution')
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)
    
    # 2. Entertainment Employment Share Distribution
    ax2 = axes3[0, 1]
    for city_key in df_merged['city_key'].unique():
        df_city = df_merged[df_merged['city_key'] == city_key]
        ax2.hist(df_city['Entertainment_Employment_Share'] * 100, bins=15, alpha=0.4,
                label=f"{df_city['city_name'].iloc[0]}",
                color=colors.get(city_key, 'gray'), density=True)
    ax2.set_xlabel('Entertainment/Media Employment Share (%)')
    ax2.set_ylabel('Density')
    ax2.set_title('Entertainment/Media Distribution (TV, Film, Streaming)')
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)
    
    # 3. Power Industry Share Distribution
    ax3 = axes3[1, 0]
    for city_key in df_merged['city_key'].unique():
        df_city = df_merged[df_merged['city_key'] == city_key]
        ax3.hist(df_city['Power_Employment_Share'] * 100, bins=15, alpha=0.4,
                label=f"{df_city['city_name'].iloc[0]}",
                color=colors.get(city_key, 'gray'), density=True)
    ax3.set_xlabel('Power Industries Employment Share (%)')
    ax3.set_ylabel('Density')
    ax3.set_title('Power Industries Distribution (Finance, Tech, Professional)')
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.3)
    
    # 4. Wealth Score Distribution
    ax4 = axes3[1, 1]
    for city_key in df_merged['city_key'].unique():
        df_city = df_merged[df_merged['city_key'] == city_key]
        ax4.hist(df_city['Wealth_Score'], bins=15, alpha=0.4,
                label=f"{df_city['city_name'].iloc[0]}",
                color=colors.get(city_key, 'gray'), density=True)
    ax4.set_xlabel('Wealth Score (%)')
    ax4.set_ylabel('Density')
    ax4.set_title('Wealth Score Distribution')
    ax4.legend(fontsize=8)
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('corporate_distributions_overlay.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("  [OK] corporate_distributions_overlay.png")
    
    # Fourth figure: KDE (Kernel Density Estimation) smooth curves
    fig4, axes4 = plt.subplots(2, 2, figsize=(14, 12))
    fig4.suptitle('Smooth Density Distributions by City (KDE)', fontsize=14, fontweight='bold')
    
    from scipy.stats import gaussian_kde
    
    # 1. Corporate Power Index KDE
    ax1 = axes4[0, 0]
    for city_key in df_merged['city_key'].unique():
        df_city = df_merged[df_merged['city_key'] == city_key]
        if len(df_city) > 5:
            data = df_city['Corp_Power_Index'].dropna()
            if len(data) > 5:
                kde = gaussian_kde(data)
                x_range = np.linspace(data.min(), data.max(), 100)
                ax1.plot(x_range, kde(x_range), label=df_city['city_name'].iloc[0],
                        color=colors.get(city_key, 'gray'), linewidth=2)
                ax1.fill_between(x_range, kde(x_range), alpha=0.2, color=colors.get(city_key, 'gray'))
    ax1.set_xlabel('Corporate Power Index')
    ax1.set_ylabel('Density')
    ax1.set_title('Corporate Power Index (Smooth)')
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)
    
    # 2. Entertainment Share KDE
    ax2 = axes4[0, 1]
    for city_key in df_merged['city_key'].unique():
        df_city = df_merged[df_merged['city_key'] == city_key]
        if len(df_city) > 5:
            data = (df_city['Entertainment_Employment_Share'] * 100).dropna()
            if len(data) > 5 and data.std() > 0:
                kde = gaussian_kde(data)
                x_range = np.linspace(max(0, data.min()), data.max(), 100)
                ax2.plot(x_range, kde(x_range), label=df_city['city_name'].iloc[0],
                        color=colors.get(city_key, 'gray'), linewidth=2)
                ax2.fill_between(x_range, kde(x_range), alpha=0.2, color=colors.get(city_key, 'gray'))
    ax2.set_xlabel('Entertainment/Media Share (%)')
    ax2.set_ylabel('Density')
    ax2.set_title('Entertainment/Media (TV, Film, Streaming)')
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)
    
    # 3. Total Employment KDE (log scale)
    ax3 = axes4[1, 0]
    for city_key in df_merged['city_key'].unique():
        df_city = df_merged[df_merged['city_key'] == city_key]
        if len(df_city) > 5:
            data = np.log10(df_city['Total_Employment'].replace(0, 1)).dropna()
            if len(data) > 5 and data.std() > 0:
                kde = gaussian_kde(data)
                x_range = np.linspace(data.min(), data.max(), 100)
                ax3.plot(x_range, kde(x_range), label=df_city['city_name'].iloc[0],
                        color=colors.get(city_key, 'gray'), linewidth=2)
                ax3.fill_between(x_range, kde(x_range), alpha=0.2, color=colors.get(city_key, 'gray'))
    ax3.set_xlabel('Log10(Total Employment)')
    ax3.set_ylabel('Density')
    ax3.set_title('Total Employment per ZIP (Log Scale)')
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.3)
    
    # 4. Estimated Revenue KDE (log scale)
    ax4 = axes4[1, 1]
    for city_key in df_merged['city_key'].unique():
        df_city = df_merged[df_merged['city_key'] == city_key]
        if len(df_city) > 5:
            data = np.log10(df_city['Estimated_Revenue'].replace(0, 1) / 1e6).dropna()  # in millions
            if len(data) > 5 and data.std() > 0:
                kde = gaussian_kde(data)
                x_range = np.linspace(data.min(), data.max(), 100)
                ax4.plot(x_range, kde(x_range), label=df_city['city_name'].iloc[0],
                        color=colors.get(city_key, 'gray'), linewidth=2)
                ax4.fill_between(x_range, kde(x_range), alpha=0.2, color=colors.get(city_key, 'gray'))
    ax4.set_xlabel('Log10(Revenue in $M)')
    ax4.set_ylabel('Density')
    ax4.set_title('Estimated Revenue per ZIP (Log Scale)')
    ax4.legend(fontsize=8)
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('corporate_distributions_kde.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("  [OK] corporate_distributions_kde.png")
    
    # Fifth figure: Box plots comparison
    fig5, axes5 = plt.subplots(2, 2, figsize=(14, 10))
    fig5.suptitle('Box Plot Comparison by City', fontsize=14, fontweight='bold')
    
    city_order = df_city_stats.sort_values('mean_corp_power_index', ascending=False)['city_name'].tolist()
    
    # 1. Corporate Power Index Box Plot
    ax1 = axes5[0, 0]
    data_corp = [df_merged[df_merged['city_name'] == city]['Corp_Power_Index'].values for city in city_order]
    bp1 = ax1.boxplot(data_corp, labels=city_order, patch_artist=True)
    for i, patch in enumerate(bp1['boxes']):
        city_key = df_city_stats[df_city_stats['city_name'] == city_order[i]]['city_key'].iloc[0]
        patch.set_facecolor(colors.get(city_key, 'gray'))
        patch.set_alpha(0.6)
    ax1.set_ylabel('Corporate Power Index')
    ax1.set_title('Corporate Power Index by City')
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, alpha=0.3, axis='y')
    
    # 2. Entertainment Share Box Plot
    ax2 = axes5[0, 1]
    data_ent = [df_merged[df_merged['city_name'] == city]['Entertainment_Employment_Share'].values * 100 for city in city_order]
    bp2 = ax2.boxplot(data_ent, labels=city_order, patch_artist=True)
    for i, patch in enumerate(bp2['boxes']):
        city_key = df_city_stats[df_city_stats['city_name'] == city_order[i]]['city_key'].iloc[0]
        patch.set_facecolor(colors.get(city_key, 'gray'))
        patch.set_alpha(0.6)
    ax2.set_ylabel('Entertainment/Media Share (%)')
    ax2.set_title('Entertainment/Media by City')
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 3. Power Industry Share Box Plot
    ax3 = axes5[1, 0]
    data_power = [df_merged[df_merged['city_name'] == city]['Power_Employment_Share'].values * 100 for city in city_order]
    bp3 = ax3.boxplot(data_power, labels=city_order, patch_artist=True)
    for i, patch in enumerate(bp3['boxes']):
        city_key = df_city_stats[df_city_stats['city_name'] == city_order[i]]['city_key'].iloc[0]
        patch.set_facecolor(colors.get(city_key, 'gray'))
        patch.set_alpha(0.6)
    ax3.set_ylabel('Power Industries Share (%)')
    ax3.set_title('Power Industries by City')
    ax3.tick_params(axis='x', rotation=45)
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 4. Wealth Score Box Plot
    ax4 = axes5[1, 1]
    data_wealth = [df_merged[df_merged['city_name'] == city]['Wealth_Score'].values for city in city_order]
    bp4 = ax4.boxplot(data_wealth, labels=city_order, patch_artist=True)
    for i, patch in enumerate(bp4['boxes']):
        city_key = df_city_stats[df_city_stats['city_name'] == city_order[i]]['city_key'].iloc[0]
        patch.set_facecolor(colors.get(city_key, 'gray'))
        patch.set_alpha(0.6)
    ax4.set_ylabel('Wealth Score (%)')
    ax4.set_title('Wealth Score by City')
    ax4.tick_params(axis='x', rotation=45)
    ax4.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('corporate_boxplots.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("  [OK] corporate_boxplots.png")

# =============================================================================
# EXPORT DATA
# =============================================================================
def export_data(df_merged, df_city_stats):
    """Export analysis results to CSV"""
    print("\n" + "="*70)
    print("EXPORTING DATA")
    print("="*70)
    
    # ZIP-level data
    export_cols = ['zipcode', 'city_key', 'city_name', 
                   'Total_Establishments', 'Total_Employment', 'Total_Payroll', 'Estimated_Revenue',
                   'Avg_Firm_Size', 'Payroll_Per_Employee',
                   'Power_Employment', 'Power_Employment_Share', 'Power_Revenue', 'Power_Revenue_Share',
                   'Corp_Power_Index', 'Wealth_Score', 'Households_200k', 'AGI_per_return', 'Population']
    
    df_export = df_merged[export_cols].copy()
    df_export.to_csv('corporate_power_by_zip.csv', index=False)
    print("  [OK] corporate_power_by_zip.csv")
    
    # City-level data
    df_city_stats.to_csv('corporate_power_by_city.csv', index=False)
    print("  [OK] corporate_power_by_city.csv")
    
    # Summary statistics
    summary = {
        'metric': [
            'Total ZIP Codes',
            'Total Establishments',
            'Total Employment',
            'Total Payroll ($B)',
            'Estimated Revenue ($B)',
            'Power Industry Employment Share (%)',
            'Power Industry Revenue Share (%)',
            'Mean Corporate Power Index',
            'Mean Wealth Score',
            'Corp-Wealth Correlation'
        ],
        'value': [
            len(df_merged),
            df_merged['Total_Establishments'].sum(),
            df_merged['Total_Employment'].sum(),
            df_merged['Total_Payroll'].sum() / 1e9,
            df_merged['Estimated_Revenue'].sum() / 1e9,
            df_merged['Power_Employment'].sum() / df_merged['Total_Employment'].sum() * 100,
            df_merged['Power_Revenue'].sum() / df_merged['Estimated_Revenue'].sum() * 100,
            df_merged['Corp_Power_Index'].mean(),
            df_merged['Wealth_Score'].mean(),
            df_merged['Corp_Power_Index'].corr(df_merged['Wealth_Score'])
        ]
    }
    df_summary = pd.DataFrame(summary)
    df_summary.to_csv('corporate_power_summary.csv', index=False)
    print("  [OK] corporate_power_summary.csv")

# =============================================================================
# MAIN
# =============================================================================
def main():
    print("\n" + "="*70)
    print("CORPORATE POWER INDEX ANALYSIS")
    print("Analyzing corporate activity in top 10% wealthiest ZIP codes")
    print("="*70)
    
    start_time = datetime.now()
    
    # Load ZBP data
    df_zbp = load_zbp_data()
    
    if df_zbp.empty:
        print("\n[ERROR] No ZBP data available. Cannot proceed.")
        return
    
    # Calculate corporate metrics
    df_corp = calculate_corporate_metrics(df_zbp)
    
    # Build corporate power index
    df_corp = build_corporate_power_index(df_corp)
    
    # Cross-reference with wealth data
    df_corp, df_merged = cross_reference_wealth(df_corp)
    
    if df_merged is None or df_merged.empty:
        print("\n[ERROR] Could not merge corporate and wealth data.")
        return
    
    # Generate city statistics
    df_city_stats = generate_city_statistics(df_merged)
    
    # Create visualizations
    create_visualizations(df_merged, df_city_stats)
    
    # Export data
    export_data(df_merged, df_city_stats)
    
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n" + "="*70)
    print(f"COMPLETED in {elapsed:.1f}s")
    print("="*70)

if __name__ == '__main__':
    main()

