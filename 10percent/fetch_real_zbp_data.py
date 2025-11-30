# -*- coding: utf-8 -*-
"""
FETCH REAL ZIP CODE BUSINESS PATTERNS DATA
==========================================
Downloads REAL corporate data from Census Bureau API.
NO SYNTHETIC DATA - only real government statistics.

Data Source: Census Bureau County Business Patterns (CBP)
URL: https://api.census.gov/data/2021/cbp

Variables:
- ESTAB: Number of establishments
- EMP: Number of employees  
- PAYANN: Annual payroll ($1,000)
- NAICS2017: Industry code
"""

import pandas as pd
import requests
import os
import time
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================
CENSUS_API_KEY = "65e82b0208b07695a5ffa13b7b9f805462804467"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'new_folder')
OUTPUT_FILE = os.path.join(BASE_DIR, 'zbp_real_data.csv')

# Industry names
INDUSTRY_NAMES = {
    '00': 'Total All Industries',
    '11': 'Agriculture/Forestry/Fishing',
    '21': 'Mining/Oil/Gas',
    '22': 'Utilities',
    '23': 'Construction',
    '31': 'Manufacturing',
    '32': 'Manufacturing',
    '33': 'Manufacturing',
    '42': 'Wholesale Trade',
    '44': 'Retail Trade',
    '45': 'Retail Trade',
    '48': 'Transportation',
    '49': 'Warehousing',
    '51': 'Information/Media',
    '52': 'Finance/Insurance',
    '53': 'Real Estate',
    '54': 'Professional Services',
    '55': 'Management',
    '56': 'Admin Services',
    '61': 'Education',
    '62': 'Health Care',
    '71': 'Entertainment/Arts',
    '72': 'Accommodation/Food',
    '81': 'Other Services',
    '99': 'Unclassified',
}

POWER_INDUSTRIES = ['51', '52', '53', '54', '55', '71']

# City configurations for labeling
CITY_ZIP_PREFIXES = {
    'los_angeles': ['900', '901', '902', '903', '904', '905', '906', '907', '908', '909', 
                    '910', '911', '912', '913', '914', '915', '916', '917', '918',
                    '920', '921', '922', '923', '924', '925', '926', '927', '928'],
    'new_york': ['100', '101', '102', '103', '104', '105', '106', '107', '108', '109',
                 '110', '111', '112', '113', '114', '115', '116', '117', '118', '119',
                 '070', '071', '072', '073', '074', '075', '076', '077', '078', '079',
                 '068', '069', '088', '089'],
    'chicago': ['600', '601', '602', '603', '604', '605', '606', '607', '608', '609'],
    'dallas': ['750', '751', '752', '753', '754', '755', '756', '757', '758', '759',
               '760', '761', '762', '763'],
    'houston': ['770', '771', '772', '773', '774', '775', '776', '777', '778', '779'],
    'miami': ['330', '331', '332', '333', '334', '335', '336', '337', '338', '339', '340', '341'],
    'san_francisco': ['940', '941', '942', '943', '944', '945', '946', '947', '948', '949', '950', '951'],
}

# =============================================================================
# LOAD ZIP CODES FROM EXISTING DATA
# =============================================================================
def get_target_zipcodes():
    """Get list of ZIP codes from existing wealth analysis data"""
    print("\n  Loading target ZIP codes from existing data...")
    
    target_zips = set()
    
    # Try wealth data file first
    wealth_file = os.path.join(BASE_DIR, 'top10_richest_data.csv')
    if os.path.exists(wealth_file):
        df = pd.read_csv(wealth_file, dtype={'zipcode': str})
        df['zipcode'] = df['zipcode'].str.zfill(5)
        target_zips.update(df['zipcode'].unique())
        print(f"    From top10_richest_data.csv: {len(df['zipcode'].unique())} ZIPs")
    
    # Try all zips file
    all_zips_file = os.path.join(BASE_DIR, 'all_zips_all_cities.csv')
    if os.path.exists(all_zips_file):
        df = pd.read_csv(all_zips_file, dtype={'zipcode': str})
        df['zipcode'] = df['zipcode'].str.zfill(5)
        target_zips.update(df['zipcode'].unique())
        print(f"    From all_zips_all_cities.csv: {len(df['zipcode'].unique())} ZIPs")
    
    # Try geometry file
    geo_file = os.path.join(DATA_DIR, 'cache_geometry.gpkg')
    if os.path.exists(geo_file):
        try:
            import geopandas as gpd
            gdf = gpd.read_file(geo_file)
            gdf['zipcode'] = gdf['ZCTA5CE20'].astype(str).str.zfill(5)
            target_zips.update(gdf['zipcode'].unique())
            print(f"    From cache_geometry.gpkg: {len(gdf['zipcode'].unique())} ZIPs")
        except:
            pass
    
    print(f"    Total unique ZIPs: {len(target_zips)}")
    return sorted(list(target_zips))

# =============================================================================
# FETCH DATA FROM CENSUS API
# =============================================================================
def fetch_zbp_data_batch(zipcodes, year=2021):
    """
    Fetch ZIP Code Business Patterns data for a batch of ZIP codes.
    Returns REAL data only - no synthetic fallback.
    """
    # CBP endpoint
    url = f"https://api.census.gov/data/{year}/cbp"
    
    # Join ZIP codes with comma
    zip_list = ','.join(zipcodes)
    
    params = {
        'get': 'ZIPCODE,NAICS2017,ESTAB,EMP,PAYANN',
        'for': f'zipcode:{zip_list}',
        'key': CENSUS_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            if len(data) > 1:
                return data
        
    except Exception as e:
        pass
    
    return None

def fetch_all_zbp_data():
    """
    Fetch ZBP data for all target ZIP codes.
    Returns DataFrame with REAL data only.
    """
    print("\n" + "="*80)
    print("FETCHING REAL ZIP CODE BUSINESS PATTERNS DATA FROM CENSUS API")
    print("="*80)
    print(f"\nSource: U.S. Census Bureau - County Business Patterns (CBP) 2021")
    print(f"API Key: {CENSUS_API_KEY[:10]}...")
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get target ZIP codes
    all_zipcodes = get_target_zipcodes()
    
    if not all_zipcodes:
        print("\n[ERROR] No target ZIP codes found!")
        return None
    
    print(f"\n  Total ZIP codes to fetch: {len(all_zipcodes)}")
    
    # Fetch in batches of 50 ZIPs
    BATCH_SIZE = 50
    all_data = []
    successful_batches = 0
    failed_batches = 0
    total_batches = (len(all_zipcodes) + BATCH_SIZE - 1) // BATCH_SIZE
    
    print(f"  Batches of {BATCH_SIZE}: {total_batches} batches")
    print()
    
    for i in range(0, len(all_zipcodes), BATCH_SIZE):
        batch = all_zipcodes[i:i+BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        
        print(f"\r  Fetching batch {batch_num}/{total_batches} ({len(batch)} ZIPs)...", end="", flush=True)
        
        data = fetch_zbp_data_batch(batch)
        
        if data and len(data) > 1:
            headers = data[0]
            rows = data[1:]
            
            df_batch = pd.DataFrame(rows, columns=headers)
            df_batch['data_year'] = 2021
            
            all_data.append(df_batch)
            successful_batches += 1
        else:
            failed_batches += 1
            # Try individual ZIPs for failed batch
            for z in batch:
                single_data = fetch_zbp_data_batch([z])
                if single_data and len(single_data) > 1:
                    headers = single_data[0]
                    rows = single_data[1:]
                    df_single = pd.DataFrame(rows, columns=headers)
                    df_single['data_year'] = 2021
                    all_data.append(df_single)
        
        time.sleep(0.3)  # Rate limiting
    
    print()
    print(f"\n  Successful batches: {successful_batches}")
    print(f"  Failed batches: {failed_batches}")
    
    if not all_data:
        print("\n[ERROR] No data retrieved from API!")
        print("\nNO SYNTHETIC DATA WILL BE GENERATED.")
        return None
    
    # Combine all data
    df = pd.concat(all_data, ignore_index=True)
    
    # Clean up columns (API returns both 'ZIPCODE' and 'zip code')
    if 'zip code' in df.columns:
        df = df.drop(columns=['zip code'])
    
    # Rename columns
    df = df.rename(columns={
        'ZIPCODE': 'zipcode',
        'NAICS2017': 'NAICS2',
        'ESTAB': 'establishments',
        'EMP': 'employment',
        'PAYANN': 'annual_payroll'
    })
    
    # Ensure zipcode is string with leading zeros
    df['zipcode'] = df['zipcode'].astype(str).str.zfill(5)
    
    # Convert to numeric
    for col in ['establishments', 'employment', 'annual_payroll']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    
    # Get 2-digit NAICS
    df['NAICS2'] = df['NAICS2'].astype(str).str[:2]
    
    # Add industry names
    df['industry_name'] = df['NAICS2'].map(INDUSTRY_NAMES).fillna('Unknown')
    
    # Mark power industries
    df['is_power'] = df['NAICS2'].isin(POWER_INDUSTRIES)
    
    # Assign city
    def get_city(zipcode):
        prefix = zipcode[:3]
        for city, prefixes in CITY_ZIP_PREFIXES.items():
            if prefix in prefixes:
                return city
        return 'other'
    
    df['city_key'] = df['zipcode'].apply(get_city)
    
    print(f"\n  Total records: {len(df):,}")
    print(f"  Unique ZIP codes: {df['zipcode'].nunique():,}")
    print(f"  Industries covered: {df['NAICS2'].nunique()}")
    
    return df

def save_data(df):
    """Save data to CSV"""
    if df is None or len(df) == 0:
        print("\n[ERROR] No data to save!")
        return
    
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n[OK] Saved to: {OUTPUT_FILE}")
    print(f"     Records: {len(df):,}")
    print(f"     File size: {os.path.getsize(OUTPUT_FILE)/1024:.1f} KB")

def print_summary(df):
    """Print data summary"""
    if df is None or len(df) == 0:
        return
    
    print("\n" + "="*80)
    print("DATA SUMMARY - REAL CENSUS DATA")
    print("="*80)
    
    # Filter out "Total All Industries" (NAICS 00) for detailed stats
    df_detail = df[df['NAICS2'] != '00']
    
    # By city
    print("\nBy City:")
    city_summary = df_detail.groupby('city_key').agg({
        'zipcode': 'nunique',
        'establishments': 'sum',
        'employment': 'sum',
        'annual_payroll': 'sum'
    }).reset_index()
    city_summary.columns = ['City', 'ZIP Codes', 'Establishments', 'Employment', 'Payroll ($K)']
    city_summary = city_summary.sort_values('Employment', ascending=False)
    
    for _, row in city_summary.iterrows():
        print(f"  {row['City']:<15}: {row['ZIP Codes']:>5} zips, {row['Establishments']:>10,} estab, {row['Employment']:>12,} emp, ${row['Payroll ($K)']/1000:>12,.0f}M payroll")
    
    # By industry (top 10)
    print("\nTop 10 Industries by Employment:")
    ind_summary = df_detail.groupby(['NAICS2', 'industry_name']).agg({
        'establishments': 'sum',
        'employment': 'sum'
    }).reset_index().sort_values('employment', ascending=False).head(10)
    
    for _, row in ind_summary.iterrows():
        power = '**' if row['NAICS2'] in POWER_INDUSTRIES else '  '
        print(f"  {power}{row['industry_name']:<25}: {row['employment']:>12,} employees, {row['establishments']:>10,} establishments")
    
    # Power industries summary
    print("\nPower Industries (Total):")
    power_df = df_detail[df_detail['is_power']]
    print(f"  Total Establishments: {power_df['establishments'].sum():,}")
    print(f"  Total Employment: {power_df['employment'].sum():,}")
    print(f"  Total Payroll: ${power_df['annual_payroll'].sum()/1000:,.0f}M")

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
    print("\n" + "="*80)
    print("CENSUS ZIP CODE BUSINESS PATTERNS - REAL DATA FETCHER")
    print("="*80)
    print("\n*** NO SYNTHETIC DATA - ONLY REAL CENSUS STATISTICS ***\n")
    
    # Fetch data
    df = fetch_all_zbp_data()
    
    if df is not None and len(df) > 0:
        # Save
        save_data(df)
        
        # Summary
        print_summary(df)
        
        print("\n" + "="*80)
        print("COMPLETED SUCCESSFULLY")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("FAILED - NO DATA RETRIEVED")
        print("="*80)
        print("\nPlease check:")
        print("  1. Internet connectivity")
        print("  2. Census API key validity")
        print("  3. Census API status: https://api.census.gov/")
