# -*- coding: utf-8 -*-
"""
CLUSTER ANALYSIS: INTERSECTION ZIPs × AIRPORT INFRASTRUCTURE
=============================================================
Analyzes clusters connecting top 10% intersection ZIPs with airports and heliports.

Uses K-means, DBSCAN, and Hierarchical clustering to group ZIPs by airport accessibility.
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INTERSECTION_FILE = os.path.join(BASE_DIR, '..', 'ANALYSIS_INTERSECTION', 'intersection_analysis.csv')
AIRPORTS_FILE = os.path.join(BASE_DIR, '..', 'all-airport-data.xlsx')

# City configurations
CITIES = {
    'los_angeles': {
        'name': 'Los Angeles',
        'center_lat': 34.0522, 'center_lon': -118.2437,
        'main_airport': 'LAX',
        'radius_km': 100,
    },
    'new_york': {
        'name': 'New York',
        'center_lat': 40.7128, 'center_lon': -74.0060,
        'main_airport': 'JFK',
        'radius_km': 150,
    },
    'chicago': {
        'name': 'Chicago',
        'center_lat': 41.8781, 'center_lon': -87.6298,
        'main_airport': 'ORD',
        'radius_km': 100,
    },
    'dallas': {
        'name': 'Dallas',
        'center_lat': 32.7767, 'center_lon': -96.7970,
        'main_airport': 'DFW',
        'radius_km': 100,
    },
    'houston': {
        'name': 'Houston',
        'center_lat': 29.7604, 'center_lon': -95.3698,
        'main_airport': 'IAH',
        'radius_km': 100,
    },
    'miami': {
        'name': 'Miami',
        'center_lat': 25.7617, 'center_lon': -80.1918,
        'main_airport': 'MIA',
        'radius_km': 100,
    },
    'san_francisco': {
        'name': 'San Francisco',
        'center_lat': 37.7749, 'center_lon': -122.4194,
        'main_airport': 'SFO',
        'radius_km': 100,
    }
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate haversine distance between two points in km"""
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(title)
    print("="*80)

# =============================================================================
# DATA LOADING
# =============================================================================
def load_intersection_data():
    """Load intersection ZIPs data (197 ZIPs)"""
    print_section("LOADING INTERSECTION DATA")
    
    df = pd.read_csv(INTERSECTION_FILE, dtype={'zipcode': str})
    
    # Ensure we have required columns
    required_cols = ['zipcode', 'centroid_lat', 'centroid_lon', 'city_key', 'city_name',
                     'Combined_Score', 'total_employment', 'estimated_revenue_M']
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"  [!] Warning: Missing columns: {missing_cols}")
    
    print(f"  Loaded {len(df)} intersection ZIPs")
    print(f"  Cities: {df['city_name'].unique().tolist()}")
    print(f"  ZIPs by city:")
    for city in sorted(df['city_name'].unique()):
        count = len(df[df['city_name'] == city])
        print(f"    {city:20} {count:3} ZIPs")
    
    return df

def load_airports_data():
    """Load airports and heliports data"""
    print_section("LOADING AIRPORTS & HELIPORTS DATA")
    
    try:
        df = pd.read_excel(AIRPORTS_FILE)
        
        # Standardize column names
        df = df.rename(columns={
            'Name': 'name',
            'Facility Type': 'facility_type',
            'Ownership': 'ownership',
            'Use': 'use',
            'ARP Latitude DD': 'lat',
            'ARP Longitude DD': 'lon',
            'City': 'city',
            'State Name': 'state',
            'Loc Id': 'code'
        })
        
        # Filter out entries with missing coordinates
        df = df.dropna(subset=['lat', 'lon'])
        
        # Categorize facilities
        df['is_airport'] = df['facility_type'].str.contains('AIRPORT', case=False, na=False)
        df['is_heliport'] = df['facility_type'].str.contains('HELIPORT|HELISTOP', case=False, na=False)
        
        print(f"  Total facilities: {len(df):,}")
        print(f"  Airports: {df['is_airport'].sum():,}")
        print(f"  Heliports: {df['is_heliport'].sum():,}")
        print(f"  Public use: {(df['use'] == 'PU').sum():,}")
        print(f"  Private use: {(df['use'] == 'PR').sum():,}")
        
        return df
    
    except Exception as e:
        print(f"  [!] Error loading airports: {e}")
        return None

def filter_airports_by_city(df_airports, city_config):
    """Filter airports/heliports within city radius"""
    center_lat = city_config['center_lat']
    center_lon = city_config['center_lon']
    radius_km = city_config['radius_km']
    
    df_airports['dist_to_center'] = df_airports.apply(
        lambda row: haversine_distance(row['lat'], row['lon'], center_lat, center_lon),
        axis=1
    )
    
    df_city = df_airports[df_airports['dist_to_center'] <= radius_km].copy()
    
    return df_city

# =============================================================================
# DISTANCE CALCULATIONS
# =============================================================================
def calculate_zip_airport_distances(df_zips, df_airports):
    """Calculate distance matrix between ZIPs and airports/heliports"""
    print_section("CALCULATING ZIP-AIRPORT DISTANCES")
    
    results = []
    
    for _, zip_row in df_zips.iterrows():
        zip_code = zip_row['zipcode']
        zip_lat = zip_row['centroid_lat']
        zip_lon = zip_row['centroid_lon']
        city_key = zip_row['city_key']
        
        for _, airport_row in df_airports.iterrows():
            dist_km = haversine_distance(
                zip_lat, zip_lon,
                airport_row['lat'], airport_row['lon']
            )
            
            results.append({
                'zipcode': zip_code,
                'city_key': city_key,
                'airport_code': airport_row['code'],
                'airport_name': airport_row['name'],
                'facility_type': airport_row['facility_type'],
                'is_airport': airport_row['is_airport'],
                'is_heliport': airport_row['is_heliport'],
                'distance_km': dist_km,
                'travel_time_min': dist_km * 1.5,  # Estimated: 1.5 min per km in urban areas
            })
    
    df_distances = pd.DataFrame(results)
    
    print(f"  Calculated {len(df_distances):,} ZIP-Airport distance pairs")
    print(f"  Average distance: {df_distances['distance_km'].mean():.1f} km")
    print(f"  Min distance: {df_distances['distance_km'].min():.1f} km")
    print(f"  Max distance: {df_distances['distance_km'].max():.1f} km")
    
    return df_distances

def find_nearest_facilities(df_distances):
    """Find FASTEST (not just nearest) airport and heliport for each ZIP"""
    print_section("FINDING FASTEST/MOST ACCESSIBLE FACILITIES")
    
    # Fastest airport (by TRAVEL TIME, not distance)
    airports_only = df_distances[df_distances['is_airport']].copy()
    nearest_airport = airports_only.loc[airports_only.groupby('zipcode')['travel_time_min'].idxmin()]
    nearest_airport = nearest_airport.rename(columns={
        'airport_code': 'nearest_airport_code',
        'airport_name': 'nearest_airport_name',
        'distance_km': 'nearest_airport_km',
        'travel_time_min': 'nearest_airport_time'
    })
    nearest_airport = nearest_airport[['zipcode', 'nearest_airport_code', 'nearest_airport_name',
                                       'nearest_airport_km', 'nearest_airport_time']]
    
    # Fastest heliport (by TRAVEL TIME, not distance)
    heliports_only = df_distances[df_distances['is_heliport']].copy()
    if len(heliports_only) > 0:
        nearest_heliport = heliports_only.loc[heliports_only.groupby('zipcode')['travel_time_min'].idxmin()]
        nearest_heliport = nearest_heliport.rename(columns={
            'airport_code': 'fastest_heliport_code',
            'airport_name': 'fastest_heliport_name',
            'distance_km': 'fastest_heliport_km',
            'travel_time_min': 'fastest_heliport_time'
        })
        nearest_heliport = nearest_heliport[['zipcode', 'fastest_heliport_code', 'fastest_heliport_name',
                                            'fastest_heliport_km', 'fastest_heliport_time']]
        
        # Calculate speed for fastest heliport
        nearest_heliport['fastest_heliport_speed'] = (
            nearest_heliport['fastest_heliport_km'] / (nearest_heliport['fastest_heliport_time'] / 60.0)
        )
    else:
        nearest_heliport = pd.DataFrame()
    
    print(f"  Found fastest airport for {len(nearest_airport)} ZIPs (by travel time)")
    if len(nearest_heliport) > 0:
        print(f"  Found fastest heliport for {len(nearest_heliport)} ZIPs (by travel time)")
        print(f"  Avg speed to fastest heliport: {nearest_heliport['fastest_heliport_speed'].mean():.1f} km/h")
    
    return nearest_airport, nearest_heliport

def calculate_accessibility_metrics(df_distances):
    """Calculate accessibility metrics (facilities within radius thresholds)"""
    print_section("CALCULATING ACCESSIBILITY METRICS")
    
    thresholds = [10, 20, 30]  # km
    results = []
    
    for zipcode in df_distances['zipcode'].unique():
        zip_data = df_distances[df_distances['zipcode'] == zipcode]
        
        metrics = {'zipcode': zipcode}
        
        for threshold in thresholds:
            within_threshold = zip_data[zip_data['distance_km'] <= threshold]
            metrics[f'airports_within_{threshold}km'] = within_threshold['is_airport'].sum()
            metrics[f'heliports_within_{threshold}km'] = within_threshold['is_heliport'].sum()
            metrics[f'total_facilities_within_{threshold}km'] = len(within_threshold)
        
        results.append(metrics)
    
    df_accessibility = pd.DataFrame(results)
    
    print(f"  Calculated accessibility for {len(df_accessibility)} ZIPs")
    for threshold in thresholds:
        avg_airports = df_accessibility[f'airports_within_{threshold}km'].mean()
        avg_heliports = df_accessibility[f'heliports_within_{threshold}km'].mean()
        print(f"    Avg within {threshold}km: {avg_airports:.1f} airports, {avg_heliports:.1f} heliports")
    
    return df_accessibility

# =============================================================================
# CLUSTERING ALGORITHMS
# =============================================================================
def apply_kmeans_clustering(df_zips_enriched, city_key, n_clusters=3):
    """Apply K-means clustering based on travel time (speed) and combined score"""
    city_data = df_zips_enriched[df_zips_enriched['city_key'] == city_key].copy()
    
    if len(city_data) < n_clusters:
        n_clusters = max(2, len(city_data) // 3)
    
    # Calculate average speed (km/h) - lower speed = more traffic/urban congestion
    city_data['avg_speed_kmh'] = (city_data['nearest_airport_km'] / 
                                   (city_data['nearest_airport_time'] / 60.0))
    
    # Features: lat, lon, travel TIME (not distance), and speed
    features = city_data[['centroid_lat', 'centroid_lon', 
                          'nearest_airport_time', 'avg_speed_kmh']].values
    
    # Standardize features
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    # Apply K-means
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    city_data['kmeans_cluster'] = kmeans.fit_predict(features_scaled)
    
    return city_data

def apply_dbscan_clustering(df_zips_enriched, city_key, eps=0.3, min_samples=2):
    """Apply DBSCAN clustering based on travel time and speed"""
    city_data = df_zips_enriched[df_zips_enriched['city_key'] == city_key].copy()
    
    # Features: lat, lon, travel TIME, speed
    features = city_data[['centroid_lat', 'centroid_lon', 
                          'nearest_airport_time', 'avg_speed_kmh']].values
    
    # Standardize features
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    # Apply DBSCAN
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    city_data['dbscan_cluster'] = dbscan.fit_predict(features_scaled)
    
    return city_data

def apply_hierarchical_clustering(df_zips_enriched, city_key, n_clusters=3):
    """Apply Hierarchical (Agglomerative) clustering based on travel time and speed"""
    city_data = df_zips_enriched[df_zips_enriched['city_key'] == city_key].copy()
    
    if len(city_data) < n_clusters:
        n_clusters = max(2, len(city_data) // 3)
    
    # Features: lat, lon, travel TIME, speed
    features = city_data[['centroid_lat', 'centroid_lon', 
                          'nearest_airport_time', 'avg_speed_kmh']].values
    
    # Standardize features
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    # Apply Hierarchical clustering
    hierarchical = AgglomerativeClustering(n_clusters=n_clusters, linkage='ward')
    city_data['hierarchical_cluster'] = hierarchical.fit_predict(features_scaled)
    
    return city_data

def apply_heliport_clustering(df_zips, n_clusters=3):
    """Apply K-means clustering based ONLY on heliport access"""
    
    if len(df_zips) < n_clusters:
        n_clusters = max(2, len(df_zips) // 3)
    
    # Features: lat, lon, heliport TIME, heliport speed
    features = df_zips[['centroid_lat', 'centroid_lon', 
                        'fastest_heliport_time', 'fastest_heliport_speed']].values
    
    # Standardize features
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    # Apply K-means
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    heliport_clusters = kmeans.fit_predict(features_scaled)
    
    return heliport_clusters

def calculate_cluster_metrics(df_clustered, cluster_col='kmeans_cluster'):
    """Calculate metrics for each cluster including speed"""
    cluster_metrics = []
    
    for cluster_id in sorted(df_clustered[cluster_col].unique()):
        if cluster_id == -1:  # DBSCAN noise
            continue
        
        cluster_data = df_clustered[df_clustered[cluster_col] == cluster_id]
        
        metrics = {
            'cluster_id': cluster_id,
            'num_zips': len(cluster_data),
            'avg_distance_airport_km': cluster_data['nearest_airport_km'].mean(),
            'avg_travel_time_min': cluster_data['nearest_airport_time'].mean(),
            'avg_speed_kmh': cluster_data.get('avg_speed_kmh', pd.Series([np.nan])).mean(),
            'avg_distance_heliport_km': cluster_data.get('nearest_heliport_km', pd.Series([np.nan])).mean(),
            'avg_combined_score': cluster_data['Combined_Score'].mean(),
            'total_employment': cluster_data['total_employment'].sum(),
            'total_revenue_M': cluster_data['estimated_revenue_M'].sum(),
            'min_distance_airport': cluster_data['nearest_airport_km'].min(),
            'max_distance_airport': cluster_data['nearest_airport_km'].max(),
            'min_travel_time': cluster_data['nearest_airport_time'].min(),
            'max_travel_time': cluster_data['nearest_airport_time'].max(),
        }
        
        cluster_metrics.append(metrics)
    
    return pd.DataFrame(cluster_metrics)

# =============================================================================
# MAIN EXECUTION
# =============================================================================
def main():
    """Main execution function"""
    print_section("CLUSTER ANALYSIS: INTERSECTION × AIRPORTS")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Load data
    df_intersection = load_intersection_data()
    df_airports = load_airports_data()
    
    if df_airports is None:
        print("[!] Cannot proceed without airport data")
        return
    
    # Process each city
    all_city_results = []
    all_cluster_metrics = []
    
    for city_key, city_config in CITIES.items():
        city_name = city_config['name']
        print_section(f"PROCESSING: {city_name.upper()}")
        
        # Filter data for city
        df_city_zips = df_intersection[df_intersection['city_key'] == city_key].copy()
        
        if len(df_city_zips) == 0:
            print(f"  [!] No intersection ZIPs found for {city_name}")
            continue
        
        print(f"  Intersection ZIPs: {len(df_city_zips)}")
        
        # Filter airports for city
        df_city_airports = filter_airports_by_city(df_airports, city_config)
        print(f"  Airports in radius: {df_city_airports['is_airport'].sum()}")
        print(f"  Heliports in radius: {df_city_airports['is_heliport'].sum()}")
        
        if len(df_city_airports) == 0:
            print(f"  [!] No airports/heliports found for {city_name}")
            continue
        
        # Calculate distances
        df_distances = calculate_zip_airport_distances(df_city_zips, df_city_airports)
        
        # Find nearest facilities
        df_nearest_airport, df_nearest_heliport = find_nearest_facilities(df_distances)
        
        # Calculate accessibility metrics
        df_accessibility = calculate_accessibility_metrics(df_distances)
        
        # Merge all data
        df_enriched = df_city_zips.copy()
        df_enriched = df_enriched.merge(df_nearest_airport, on='zipcode', how='left')
        if len(df_nearest_heliport) > 0:
            df_enriched = df_enriched.merge(df_nearest_heliport, on='zipcode', how='left')
        df_enriched = df_enriched.merge(df_accessibility, on='zipcode', how='left')
        
        # Apply clustering algorithms - TWO SEPARATE ANALYSES
        n_clusters = max(2, len(df_city_zips) // 5)  # Dynamic number of clusters
        
        print(f"\n  Applying clustering for AIRPORTS (k={n_clusters})...")
        df_enriched = apply_kmeans_clustering(df_enriched, city_key, n_clusters)
        df_enriched = apply_dbscan_clustering(df_enriched, city_key)
        df_enriched = apply_hierarchical_clustering(df_enriched, city_key, n_clusters)
        
        # Create SEPARATE clustering for HELIPORTS
        print(f"\n  Applying clustering for HELIPORTS (k={n_clusters})...")
        df_enriched['heliport_cluster'] = apply_heliport_clustering(df_enriched, n_clusters)
        
        # Calculate cluster metrics
        kmeans_metrics = calculate_cluster_metrics(df_enriched, 'kmeans_cluster')
        kmeans_metrics['city_key'] = city_key
        kmeans_metrics['city_name'] = city_name
        kmeans_metrics['algorithm'] = 'K-Means'
        
        print(f"\n  K-Means Clusters (based on travel time & speed):")
        for _, row in kmeans_metrics.iterrows():
            print(f"    Cluster {row['cluster_id']}: {row['num_zips']} ZIPs, "
                  f"avg {row['avg_travel_time_min']:.1f}min ({row['avg_speed_kmh']:.1f}km/h) to airport, "
                  f"score {row['avg_combined_score']:.3f}")
        
        all_city_results.append(df_enriched)
        all_cluster_metrics.append(kmeans_metrics)
    
    # Combine results
    df_all_results = pd.concat(all_city_results, ignore_index=True)
    df_all_metrics = pd.concat(all_cluster_metrics, ignore_index=True)
    
    # Save outputs
    print_section("SAVING RESULTS")
    
    output_file_city = os.path.join(BASE_DIR, 'cluster_results_by_city.csv')
    df_all_results.to_csv(output_file_city, index=False)
    print(f"  [✓] Saved: {output_file_city}")
    
    output_file_metrics = os.path.join(BASE_DIR, 'cluster_metrics_by_city.csv')
    df_all_metrics.to_csv(output_file_metrics, index=False)
    print(f"  [✓] Saved: {output_file_metrics}")
    
    # National-level clustering
    print_section("NATIONAL-LEVEL CLUSTERING (based on travel time & speed)")
    
    features = df_all_results[['centroid_lat', 'centroid_lon', 
                               'nearest_airport_time', 'avg_speed_kmh']].values
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    n_national_clusters = 7  # One per city approximately
    kmeans_national = KMeans(n_clusters=n_national_clusters, random_state=42, n_init=10)
    df_all_results['national_cluster'] = kmeans_national.fit_predict(features_scaled)
    
    output_file_national = os.path.join(BASE_DIR, 'cluster_results_national.csv')
    df_all_results.to_csv(output_file_national, index=False)
    print(f"  [✓] Saved: {output_file_national}")
    
    # Accessibility summary
    accessibility_cols = [col for col in df_all_results.columns if 'within_' in col]
    df_accessibility_summary = df_all_results.groupby('city_name')[accessibility_cols].mean().round(2)
    
    output_file_access = os.path.join(BASE_DIR, 'airport_accessibility_metrics.csv')
    df_accessibility_summary.to_csv(output_file_access)
    print(f"  [✓] Saved: {output_file_access}")
    
    print_section("CLUSTER ANALYSIS COMPLETE")
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nSummary:")
    print(f"  Total ZIPs analyzed: {len(df_all_results)}")
    print(f"  Cities: {len(CITIES)}")
    print(f"  K-Means clusters per city: ~{n_clusters}")
    print(f"  National clusters: {n_national_clusters}")
    print("\nOutput files:")
    print(f"  - cluster_results_by_city.csv")
    print(f"  - cluster_metrics_by_city.csv")
    print(f"  - cluster_results_national.csv")
    print(f"  - airport_accessibility_metrics.csv")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()

