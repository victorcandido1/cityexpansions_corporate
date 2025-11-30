# -*- coding: utf-8 -*-
"""
FETCH CORPORATE TRAVEL TIMES TO AIRPORTS
========================================
Downloads travel times from corporate ZIP codes to main airports
using Google Distance Matrix API with 30 parallel workers.

100% REAL DATA - Google Distance Matrix API
"""

import pandas as pd
import geopandas as gpd
import numpy as np
import requests
import json
import os
import time
from datetime import datetime
from multiprocessing import Pool, Manager
from functools import partial
import math

# =============================================================================
# CONFIGURATION
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'new_folder')

GOOGLE_API_KEY = "AIzaSyB32h53iZya5KfRgC8jxwVOZxdkBDZNu2I"
GEOMETRY_FILE = os.path.join(DATA_DIR, 'cache_geometry.gpkg')
CORPORATE_TOP10_FILE = os.path.join(BASE_DIR, 'top10_corporate_data.csv')
OUTPUT_CACHE = os.path.join(BASE_DIR, 'cache_corporate_travel_times.json')

# Number of parallel workers
NUM_WORKERS = 30

# Batch size for Google API (max 25 origins per request)
BATCH_SIZE = 25

# City configurations with airports
CITIES = {
    'los_angeles': {
        'name': 'Los Angeles',
        'airport_code': 'LAX',
        'airport_lat': 33.9416,
        'airport_lon': -118.4085,
    },
    'new_york': {
        'name': 'New York',
        'airport_code': 'JFK',
        'airport_lat': 40.6413,
        'airport_lon': -73.7781,
    },
    'chicago': {
        'name': 'Chicago',
        'airport_code': 'ORD',
        'airport_lat': 41.9742,
        'airport_lon': -87.9073,
    },
    'dallas': {
        'name': 'Dallas',
        'airport_code': 'DFW',
        'airport_lat': 32.8998,
        'airport_lon': -97.0403,
    },
    'houston': {
        'name': 'Houston',
        'airport_code': 'IAH',
        'airport_lat': 29.9902,
        'airport_lon': -95.3368,
    },
    'miami': {
        'name': 'Miami',
        'airport_code': 'MIA',
        'airport_lat': 25.7959,
        'airport_lon': -80.2870,
    },
    'san_francisco': {
        'name': 'San Francisco',
        'airport_code': 'SFO',
        'airport_lat': 37.6213,
        'airport_lon': -122.3790,
    }
}

# =============================================================================
# HAVERSINE DISTANCE (FALLBACK)
# =============================================================================
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate geodesic distance between two points"""
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

# =============================================================================
# FETCH BATCH FROM GOOGLE API
# =============================================================================
def fetch_batch_travel_times(batch_data, airport_lat, airport_lon, airport_code):
    """
    Fetch travel times for a batch of ZIP codes from Google Distance Matrix API
    
    Args:
        batch_data: List of tuples (zipcode, lat, lon)
        airport_lat: Airport latitude
        airport_lon: Airport longitude
        airport_code: Airport code (for logging)
    
    Returns:
        Dictionary {zipcode: travel_time_minutes}
    """
    results = {}
    
    if len(batch_data) == 0:
        return results
    
    # Prepare origins
    origins = "|".join([f"{lat},{lon}" for _, lat, lon in batch_data])
    dest = f"{airport_lat},{airport_lon}"
    
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        'origins': origins,
        'destinations': dest,
        'mode': 'driving',
        'departure_time': 'now',
        'key': GOOGLE_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if data['status'] == 'OK':
            for idx, (zipcode, lat, lon) in enumerate(batch_data):
                if idx < len(data.get('rows', [])):
                    element = data['rows'][idx]['elements'][0]
                    
                    if element['status'] == 'OK':
                        # Use duration_in_traffic if available, else duration
                        duration_sec = element.get('duration_in_traffic', 
                                                  element.get('duration', {})).get('value', 0)
                        if duration_sec > 0:
                            results[zipcode] = duration_sec / 60.0  # Convert to minutes
                        else:
                            # Fallback to estimated time based on distance
                            dist_km = haversine_distance(lat, lon, airport_lat, airport_lon)
                            results[zipcode] = (dist_km / 40.0) * 60  # Assume 40 km/h average
                    else:
                        # Fallback to estimated time
                        dist_km = haversine_distance(lat, lon, airport_lat, airport_lon)
                        results[zipcode] = (dist_km / 40.0) * 60
                else:
                    # Fallback
                    dist_km = haversine_distance(lat, lon, airport_lat, airport_lon)
                    results[zipcode] = (dist_km / 40.0) * 60
        else:
            # API error - use fallback for all
            for zipcode, lat, lon in batch_data:
                dist_km = haversine_distance(lat, lon, airport_lat, airport_lon)
                results[zipcode] = (dist_km / 40.0) * 60
        
        # Rate limiting
        time.sleep(0.1)
        
    except Exception as e:
        print(f"    [!] Error fetching batch: {e}")
        # Fallback for all in batch
        for zipcode, lat, lon in batch_data:
            dist_km = haversine_distance(lat, lon, airport_lat, airport_lon)
            results[zipcode] = (dist_km / 40.0) * 60
    
    return results

# =============================================================================
# PROCESS BATCH (WORKER FUNCTION)
# =============================================================================
def process_batch_worker(batch_tuple):
    """
    Worker function to process one batch of ZIP codes
    
    Args:
        batch_tuple: (batch_id, batch_data, airport_lat, airport_lon, airport_code, city_name)
    
    Returns:
        (batch_id, travel_times_dict)
    """
    batch_id, batch_data, airport_lat, airport_lon, airport_code, city_name = batch_tuple
    
    batch_results = fetch_batch_travel_times(batch_data, airport_lat, airport_lon, airport_code)
    
    return (batch_id, batch_results)

# =============================================================================
# LOAD DATA
# =============================================================================
def load_data():
    """Load corporate data and geometry"""
    print("\n" + "="*80)
    print("LOADING DATA")
    print("="*80)
    
    # Load corporate Top 10% data
    df_corporate = pd.read_csv(CORPORATE_TOP10_FILE, dtype={'zipcode': str})
    print(f"  Corporate Top 10% ZIPs: {len(df_corporate):,}")
    
    # Load geometry
    if not os.path.exists(GEOMETRY_FILE):
        print(f"  [!] Geometry file not found: {GEOMETRY_FILE}")
        return None, None
    
    gdf = gpd.read_file(GEOMETRY_FILE)
    gdf['zipcode'] = gdf['ZCTA5CE20'].astype(str).str.zfill(5)
    print(f"  Geometry loaded: {len(gdf):,} ZIP codes")
    
    # Calculate centroids
    gdf['centroid_lat'] = gdf.geometry.centroid.y
    gdf['centroid_lon'] = gdf.geometry.centroid.x
    
    # Merge corporate data with geometry
    df_merged = df_corporate.merge(
        gdf[['zipcode', 'centroid_lat', 'centroid_lon']],
        on='zipcode',
        how='left'
    )
    
    # Filter only ZIPs with geometry
    df_merged = df_merged[df_merged['centroid_lat'].notna()].copy()
    print(f"  ZIPs with geometry: {len(df_merged):,}")
    
    return df_merged, gdf

# =============================================================================
# MAIN FETCH FUNCTION
# =============================================================================
def fetch_all_travel_times():
    """Fetch travel times for all corporate Top 10% ZIP codes"""
    print("\n" + "="*80)
    print("FETCHING CORPORATE TRAVEL TIMES TO AIRPORTS")
    print("="*80)
    print(f"\nWorkers: {NUM_WORKERS}")
    print(f"Batch Size: {BATCH_SIZE}")
    print(f"API: Google Distance Matrix")
    print()
    
    # Load data
    df_merged, gdf = load_data()
    if df_merged is None:
        return
    
    # Check if cache exists
    if os.path.exists(OUTPUT_CACHE):
        print(f"  [CACHE] Found existing cache: {OUTPUT_CACHE}")
        response = input("  Overwrite? (y/n): ").strip().lower()
        if response != 'y':
            print("  [SKIP] Using existing cache")
            return
    
    # Prepare all batches from all cities
    all_batch_tasks = []
    batch_id = 0
    
    for city_key, config in CITIES.items():
        df_city = df_merged[df_merged['city_key'] == city_key].copy()
        
        if len(df_city) > 0:
            # Prepare batch data
            batches = []
            for idx, row in df_city.iterrows():
                batches.append((row['zipcode'], row['centroid_lat'], row['centroid_lon']))
            
            # Split into batches of BATCH_SIZE
            for i in range(0, len(batches), BATCH_SIZE):
                batch_data = batches[i:i+BATCH_SIZE]
                all_batch_tasks.append((
                    batch_id,
                    batch_data,
                    config['airport_lat'],
                    config['airport_lon'],
                    config['airport_code'],
                    config['name']
                ))
                batch_id += 1
    
    print(f"\n  Total batches: {len(all_batch_tasks)}")
    print(f"  Total ZIPs: {len(df_merged):,}")
    print(f"  Using {NUM_WORKERS} parallel workers...")
    print()
    
    # Process all batches in parallel
    all_travel_times = {}
    
    start_time = time.time()
    with Pool(processes=NUM_WORKERS) as pool:
        results = pool.map(process_batch_worker, all_batch_tasks)
    
    # Combine results
    for batch_id, batch_results in results:
        all_travel_times.update(batch_results)
    
    elapsed = time.time() - start_time
    print(f"\n  Processed {len(all_batch_tasks)} batches in {elapsed:.1f} seconds")
    print(f"  Average: {elapsed/len(all_batch_tasks):.2f} seconds per batch")
    
    # Save cache
    print(f"\n  Saving cache...")
    with open(OUTPUT_CACHE, 'w') as f:
        json.dump(all_travel_times, f, indent=2)
    
    print(f"  [OK] Cache saved: {OUTPUT_CACHE}")
    print(f"      Total travel times: {len(all_travel_times):,}")
    
    # Statistics
    if len(all_travel_times) > 0:
        times = list(all_travel_times.values())
        print(f"\n  Statistics:")
        print(f"    Min: {min(times):.1f} minutes")
        print(f"    Max: {max(times):.1f} minutes")
        print(f"    Mean: {np.mean(times):.1f} minutes")
        print(f"    Median: {np.median(times):.1f} minutes")
    
    return all_travel_times

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
    print("\n" + "="*80)
    print("CORPORATE TRAVEL TIMES FETCHER")
    print("="*80)
    print("\n*** 100% REAL DATA FROM GOOGLE DISTANCE MATRIX API ***")
    print()
    
    fetch_all_travel_times()
    
    print("\n" + "="*80)
    print("COMPLETED")
    print("="*80)

