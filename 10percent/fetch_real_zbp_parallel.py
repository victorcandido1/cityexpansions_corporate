# -*- coding: utf-8 -*-
"""
FETCH REAL ZIP CODE BUSINESS PATTERNS DATA - PARALLEL VERSION
==============================================================
Downloads REAL corporate data from Census Bureau API using 20 parallel workers.
Uses cache to avoid re-downloading already fetched data.

NO SYNTHETIC DATA - only real government statistics.

Data Source: Census Bureau County Business Patterns (CBP) 2021
"""

import pandas as pd
import requests
import os
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# =============================================================================
# CONFIGURATION
# =============================================================================
CENSUS_API_KEY = "65e82b0208b07695a5ffa13b7b9f805462804467"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'new_folder')

# Output files
OUTPUT_FILE = os.path.join(BASE_DIR, 'zbp_real_data.csv')
CACHE_FILE = os.path.join(BASE_DIR, 'cache_zbp_raw.json')

# Parallel settings
NUM_WORKERS = 20
BATCH_SIZE = 30  # ZIPs per API call

# Thread-safe counter
progress_lock = threading.Lock()
progress = {'done': 0, 'total': 0, 'failed': []}

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
# CACHE MANAGEMENT
# =============================================================================
def load_cache():
    """Load cached ZIP data"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_cache(cache):
    """Save cache to file"""
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)

cache_lock = threading.Lock()
CACHE = load_cache()

def update_cache(zipcode, data):
    """Thread-safe cache update"""
    with cache_lock:
        CACHE[zipcode] = data

def save_cache_periodic():
    """Save cache periodically"""
    with cache_lock:
        save_cache(CACHE)

# =============================================================================
# GET TARGET ZIP CODES
# =============================================================================
def get_target_zipcodes():
    """Get list of ZIP codes from existing data"""
    target_zips = set()
    
    # From wealth data
    wealth_file = os.path.join(BASE_DIR, 'top10_richest_data.csv')
    if os.path.exists(wealth_file):
        df = pd.read_csv(wealth_file, dtype={'zipcode': str})
        df['zipcode'] = df['zipcode'].str.zfill(5)
        target_zips.update(df['zipcode'].unique())
    
    # From all zips
    all_zips_file = os.path.join(BASE_DIR, 'all_zips_all_cities.csv')
    if os.path.exists(all_zips_file):
        df = pd.read_csv(all_zips_file, dtype={'zipcode': str})
        df['zipcode'] = df['zipcode'].str.zfill(5)
        target_zips.update(df['zipcode'].unique())
    
    # From geometry
    geo_file = os.path.join(DATA_DIR, 'cache_geometry.gpkg')
    if os.path.exists(geo_file):
        try:
            import geopandas as gpd
            gdf = gpd.read_file(geo_file)
            gdf['zipcode'] = gdf['ZCTA5CE20'].astype(str).str.zfill(5)
            target_zips.update(gdf['zipcode'].unique())
        except:
            pass
    
    return sorted(list(target_zips))

# =============================================================================
# FETCH DATA FROM CENSUS API
# =============================================================================
def fetch_batch(batch_zips, batch_id):
    """Fetch a batch of ZIP codes from Census API"""
    global progress
    
    # Check cache first
    cached_zips = []
    to_fetch = []
    
    for z in batch_zips:
        if z in CACHE:
            cached_zips.append(z)
        else:
            to_fetch.append(z)
    
    results = []
    
    # Get cached data
    for z in cached_zips:
        for row in CACHE[z]:
            results.append(row)
    
    # Fetch remaining from API
    if to_fetch:
        url = "https://api.census.gov/data/2021/cbp"
        zip_list = ','.join(to_fetch)
        
        params = {
            'get': 'ZIPCODE,NAICS2017,ESTAB,EMP,PAYANN',
            'for': f'zipcode:{zip_list}',
            'key': CENSUS_API_KEY
        }
        
        try:
            response = requests.get(url, params=params, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                if len(data) > 1:
                    headers = data[0]
                    rows = data[1:]
                    
                    # Group by ZIP and cache
                    zip_data = {}
                    for row in rows:
                        z = row[0]
                        if z not in zip_data:
                            zip_data[z] = []
                        zip_data[z].append(row)
                        results.append(row)
                    
                    # Update cache
                    for z, zdata in zip_data.items():
                        update_cache(z, zdata)
                    
        except Exception as e:
            with progress_lock:
                progress['failed'].extend(to_fetch)
    
    # Update progress
    with progress_lock:
        progress['done'] += 1
        done = progress['done']
        total = progress['total']
        pct = (done / total) * 100 if total > 0 else 0
        print(f"\r  Progress: {done}/{total} batches ({pct:.1f}%) - {len(results)} rows", end="", flush=True)
    
    return results

def fetch_all_parallel():
    """Fetch all ZIP codes using parallel workers"""
    global progress
    
    print("\n" + "="*80)
    print("FETCHING REAL CENSUS DATA - PARALLEL MODE")
    print("="*80)
    print(f"\nWorkers: {NUM_WORKERS}")
    print(f"Batch size: {BATCH_SIZE} ZIPs per request")
    print(f"Cache file: {CACHE_FILE}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get target ZIPs
    print("\n  Loading target ZIP codes...")
    all_zips = get_target_zipcodes()
    print(f"  Total ZIPs to process: {len(all_zips)}")
    print(f"  Already cached: {len([z for z in all_zips if z in CACHE])}")
    
    # Create batches
    batches = []
    for i in range(0, len(all_zips), BATCH_SIZE):
        batches.append(all_zips[i:i+BATCH_SIZE])
    
    progress['total'] = len(batches)
    progress['done'] = 0
    progress['failed'] = []
    
    print(f"  Batches: {len(batches)}")
    print()
    
    # Parallel fetch
    all_results = []
    
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {executor.submit(fetch_batch, batch, i): i for i, batch in enumerate(batches)}
        
        for future in as_completed(futures):
            try:
                results = future.result()
                all_results.extend(results)
            except Exception as e:
                pass
        
        # Save cache periodically
        save_cache_periodic()
    
    print()
    print(f"\n  Total rows fetched: {len(all_results):,}")
    print(f"  Failed ZIPs: {len(progress['failed'])}")
    
    # Save final cache
    save_cache(CACHE)
    print(f"  Cache saved: {len(CACHE)} ZIPs")
    
    if not all_results:
        return None
    
    # Create DataFrame (API returns 6 columns: ZIPCODE, NAICS2017, ESTAB, EMP, PAYANN, zipcode)
    headers = ['ZIPCODE', 'NAICS2017', 'ESTAB', 'EMP', 'PAYANN', 'zip_code_dup']
    df = pd.DataFrame(all_results, columns=headers)
    df = df.drop(columns=['zip_code_dup'], errors='ignore')
    
    # Clean columns
    df = df.rename(columns={
        'ZIPCODE': 'zipcode',
        'NAICS2017': 'NAICS2',
        'ESTAB': 'establishments',
        'EMP': 'employment',
        'PAYANN': 'annual_payroll'
    })
    
    df['zipcode'] = df['zipcode'].astype(str).str.zfill(5)
    
    for col in ['establishments', 'employment', 'annual_payroll']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    
    df['NAICS2'] = df['NAICS2'].astype(str).str[:2]
    df['industry_name'] = df['NAICS2'].map(INDUSTRY_NAMES).fillna('Unknown')
    df['is_power'] = df['NAICS2'].isin(POWER_INDUSTRIES)
    
    def get_city(zipcode):
        prefix = zipcode[:3]
        for city, prefixes in CITY_ZIP_PREFIXES.items():
            if prefix in prefixes:
                return city
        return 'other'
    
    df['city_key'] = df['zipcode'].apply(get_city)
    
    return df

def print_summary(df):
    """Print data summary"""
    if df is None or len(df) == 0:
        return
    
    print("\n" + "="*80)
    print("DATA SUMMARY - REAL CENSUS DATA (2021)")
    print("="*80)
    
    df_detail = df[df['NAICS2'] != '00']
    
    print("\nBy City:")
    city_summary = df_detail.groupby('city_key').agg({
        'zipcode': 'nunique',
        'establishments': 'sum',
        'employment': 'sum',
        'annual_payroll': 'sum'
    }).reset_index().sort_values('employment', ascending=False)
    
    for _, row in city_summary.iterrows():
        print(f"  {row['city_key']:<15}: {row['zipcode']:>5} zips, {row['establishments']:>10,} estab, {row['employment']:>12,} emp")
    
    print("\nTop 10 Industries by Employment:")
    ind_summary = df_detail.groupby(['NAICS2', 'industry_name']).agg({
        'establishments': 'sum',
        'employment': 'sum'
    }).reset_index().sort_values('employment', ascending=False).head(10)
    
    for _, row in ind_summary.iterrows():
        power = '**' if row['NAICS2'] in POWER_INDUSTRIES else '  '
        print(f"  {power}{row['industry_name']:<25}: {row['employment']:>12,} emp, {row['establishments']:>10,} estab")
    
    print("\nPower Industries Total:")
    power_df = df_detail[df_detail['is_power']]
    print(f"  Establishments: {power_df['establishments'].sum():,}")
    print(f"  Employment: {power_df['employment'].sum():,}")
    print(f"  Payroll: ${power_df['annual_payroll'].sum()/1000:,.0f}M")

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
    print("\n" + "="*80)
    print("CENSUS BUSINESS PATTERNS - REAL DATA (PARALLEL FETCH)")
    print("="*80)
    print("\n*** NO SYNTHETIC DATA - ONLY REAL CENSUS STATISTICS ***")
    
    start_time = time.time()
    
    # Fetch
    df = fetch_all_parallel()
    
    elapsed = time.time() - start_time
    
    if df is not None and len(df) > 0:
        # Save
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"\n[OK] Saved to: {OUTPUT_FILE}")
        print(f"     Records: {len(df):,}")
        print(f"     Unique ZIPs: {df['zipcode'].nunique():,}")
        
        # Summary
        print_summary(df)
        
        print("\n" + "="*80)
        print(f"COMPLETED in {elapsed:.1f} seconds")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("FAILED - NO DATA RETRIEVED")
        print("="*80)

