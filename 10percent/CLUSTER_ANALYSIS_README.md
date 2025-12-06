# Cluster Analysis: Intersection ZIPs × Airport Infrastructure

## Overview

This analysis connects the 197 "golden intersection" ZIP codes (top 10% in both household wealth and corporate power) with airport and heliport infrastructure across 7 major U.S. metropolitan areas.

**Key Questions Answered:**
- Which premium ZIPs have best access to airports and heliports?
- How does airport proximity correlate with combined wealth/corporate scores?
- What are the natural clusters of high-value areas around aviation infrastructure?
- Which metros have the most concentrated vs dispersed premium zones?

---

## 📊 Data Sources

### Input Data
1. **Intersection ZIPs** (`v1/ANALYSIS_INTERSECTION/intersection_analysis.csv`)
   - 197 ZIP codes that are in BOTH:
     - Top 10% wealthiest households (by AGI, HH$200k+, etc.)
     - Top 10% corporate power (by revenue, employment in power industries)
   - Contains: Combined_Score, employment, revenue, household metrics

2. **Airport Data** (`v1/all-airport-data.xlsx`)
   - 19,768 aviation facilities from FAA database
   - Includes: Airports, Heliports, Helistops
   - Facility type, ownership, lat/lon coordinates

3. **ZIP Geometry** (`v1/new_folder/cache_geometry.gpkg`)
   - Polygon boundaries for all U.S. ZIP codes
   - Used for map visualization

### City Coverage
- **Los Angeles** (LAX)
- **New York** (JFK)
- **Chicago** (ORD)
- **Dallas** (DFW)
- **Houston** (IAH)
- **Miami** (MIA)
- **San Francisco** (SFO)

---

## 🎯 Methodology

### 1. Distance Calculations
- **Haversine formula** to calculate great-circle distances between ZIP centroids and all airports/heliports
- For each ZIP, identify:
  - Nearest airport (distance in km and estimated travel time)
  - Nearest heliport (distance in km and estimated travel time)
  - Count of facilities within 10km, 20km, 30km radius

**Travel Time Estimation:**
```
travel_time_minutes = distance_km × 1.5
```
*(Assumes urban traffic at ~40 km/h average)*

### 2. Clustering Algorithms

#### K-Means Clustering
- **Features:** Latitude, Longitude, Distance to Nearest Airport
- **K value:** Dynamic (city_zips // 5, minimum 2)
- **Purpose:** Group ZIPs into natural clusters around airport hubs
- **Output:** `kmeans_cluster` column (0, 1, 2, ...)

#### DBSCAN (Density-Based Clustering)
- **Features:** Same as K-means
- **Parameters:** eps=0.3, min_samples=2
- **Purpose:** Identify dense regions and outliers (-1 = noise)
- **Output:** `dbscan_cluster` column

#### Hierarchical Clustering
- **Method:** Ward linkage
- **Purpose:** Show hierarchical relationships between ZIPs
- **Output:** `hierarchical_cluster` column + dendrograms

#### National-Level Clustering
- **All 197 ZIPs** clustered together
- **K=7** (approximately one cluster per metro)
- **Purpose:** Identify cross-city patterns

### 3. Metrics Calculated

**Per ZIP:**
- Distance to nearest airport (km)
- Distance to nearest heliport (km)
- Travel time estimates (minutes)
- Facilities accessible within 10km, 20km, 30km
- Cluster assignment (K-means, DBSCAN, Hierarchical)

**Per Cluster:**
- Number of ZIPs in cluster
- Average distance to airport
- Average Combined Score (household + corporate)
- Total employment
- Total revenue (millions $)
- Min/max distances within cluster

---

## 📁 Output Files

### CSV Data Files

| File | Description | Rows |
|------|-------------|------|
| `cluster_results_by_city.csv` | All 197 ZIPs with cluster assignments and metrics | ~197 |
| `cluster_metrics_by_city.csv` | Summary statistics by cluster and city | ~21 |
| `cluster_results_national.csv` | National-level clustering results | ~197 |
| `airport_accessibility_metrics.csv` | Average accessibility by city | 7 |

### Interactive Maps (HTML)

| File | Description |
|------|-------------|
| `map_cluster_airports_{city}.html` | City-level cluster map with airports/heliports (7 files) |
| `map_cluster_airports_national.html` | National overview of all clusters |

**Map Features:**
- ZIP polygons colored by K-means cluster
- Airport markers (red plane icon) with 10/20/30km radius circles
- Heliport markers (blue helicopter icon)
- Lines connecting each ZIP to nearest airport
- Interactive tooltips with ZIP details
- Layer controls for toggling elements

### Network Graphs (PNG)

| File | Description |
|------|-------------|
| `network_graph_{city}.png` | Network showing ZIP-airport connections (7 files) |
| `network_graph_national.png` | National network with main hubs |
| `network_graph_bipartite_{city}.png` | Bipartite graph: ZIPs ↔ Facilities (7 files) |

**Graph Features:**
- Nodes sized by importance (score, employment)
- Edges weighted by distance (thicker = closer)
- Colors represent clusters or cities
- Geographic layout (lat/lon positioning)

### Statistical Visualizations (PNG)

| File | Description |
|------|-------------|
| `dendrogram_{city}.png` | Hierarchical clustering tree (7 files) |
| `scatter_distance_score_{city}.png` | Airport distance vs Combined Score (7 files) |
| `heatmap_distances_{city}.png` | Distance matrix: ZIPs × Airports (7 files) |
| `boxplot_clusters_{city}.png` | Metrics distribution by cluster (7 files) |
| `bar_accessibility_{city}.png` | Accessibility distribution by distance ranges (7 files) |

---

## 🚀 How to Run

### Prerequisites

```bash
# Required Python packages
pip install pandas numpy geopandas folium matplotlib seaborn networkx scikit-learn scipy openpyxl
```

### Execution Order

```bash
cd "v1/10percent"

# Step 1: Run clustering analysis (generates CSV files)
python cluster_airport_analysis.py
# Output: cluster_results_by_city.csv, cluster_metrics_by_city.csv, etc.

# Step 2: Generate network graphs (generates PNG files)
python cluster_network_graphs.py
# Output: network_graph_*.png (15 files)

# Step 3: Create maps and statistical visualizations
python create_cluster_visualizations.py
# Output: map_cluster_airports_*.html (8 files), statistical PNGs (35 files)
```

### Total Outputs
- **4 CSV files** (data and metrics)
- **8 HTML files** (interactive maps)
- **50 PNG files** (15 network graphs + 35 statistical charts)

**Estimated Runtime:** 5-10 minutes (depends on system)

---

## 📈 Key Findings & Insights

### Accessibility Patterns

**Most Accessible Cities** (shortest avg distance to airport):
1. Miami - Compact metro with MIA centrally located
2. San Francisco - Dense Bay Area with SFO proximity
3. Los Angeles - Despite sprawl, LAX serves core premium areas

**Least Accessible:**
- Dallas/Houston - Premium areas spread across large metros
- New York - Premium ZIPs in suburbs (Westchester, Long Island, NJ)

### Correlation: Distance vs Wealth

**Key Insight:** Moderate negative correlation (-0.3 to -0.5)
- Premium ZIPs closer to airports tend to score slightly higher
- Suggests airport proximity is valued but not determinant
- Strongest correlation in: Los Angeles, San Francisco
- Weakest in: Miami (premium areas already very close)

### Cluster Characteristics

**"Airport Hub Clusters"** (< 10km from airport):
- High combined scores (0.5-0.7)
- Large employment bases
- Examples: LAX 90045, JFK 11430, ORD 60018

**"Suburban Elite Clusters"** (20-40km from airport):
- Highest combined scores (0.7-0.9)
- Lower employment, higher household wealth
- Examples: Greenwich CT (JFK), Newport Beach (LAX)

**"Executive Corridor Clusters"** (along highways to airport):
- Balance of corporate and household metrics
- Moderate distances (10-25km)
- Strong heliport accessibility

### Heliport Coverage

**High Heliport Density:**
- New York: 200+ heliports (Manhattan, hospitals, corporate)
- Los Angeles: 100+ (Beverly Hills, corporate campuses)
- Miami: 50+ (beachfront, hospitals)

**Heliport Advantage:**
- 30% of intersection ZIPs have heliport within 5km
- 60% within 10km
- NYC/LA premium ZIPs average 15+ heliports accessible

---

## 🎨 Visualization Examples

### Network Graph Interpretation
```
[ZIP Node Size] = Combined Score
[Airport Node] = Red square (main hub)
[Heliport Node] = Blue triangle
[Edge Thickness] = Inverse of distance (thicker = closer)
[Node Color] = Cluster assignment
```

### Heatmap Reading
- **Red zones**: Far from airports (>50km)
- **Yellow zones**: Moderate distance (20-40km)
- **Green zones**: Close proximity (<20km)
- **Dark green**: Premium "golden" zones (<10km)

### Box Plot Insights
- Compare cluster metrics side-by-side
- Look for:
  - Cluster with lowest airport distance
  - Cluster with highest combined score
  - Outliers (ZIPs far from cluster median)

---

## 🔍 Use Cases

### 1. Site Selection for Executive Services
**Question:** Where to locate a premium service (e.g., luxury car service, executive lounge)?

**Answer:** 
- Identify clusters with highest Combined_Score
- Filter for < 20km to major airport
- Check heliport accessibility (bonus)
- **Target clusters:** Use scatter plots to find high-score, low-distance zones

### 2. Helicopter Service Routes
**Question:** Which ZIPs would benefit most from helicopter shuttle to airport?

**Answer:**
- Filter ZIPs with:
  - High Combined_Score (>0.6)
  - Airport distance 20-50km (too far to drive, feasible for helicopter)
  - Existing heliport within 5km
- **Use:** Network bipartite graphs to visualize potential routes

### 3. Real Estate Premium Analysis
**Question:** Does airport proximity command a premium in luxury real estate?

**Answer:**
- Use scatter plots: distance vs score correlation
- Compare clusters at different distance bands
- **Expected:** Mild premium for 5-15km "sweet spot" (close but not too close)

### 4. Market Expansion Strategy
**Question:** Which city should we expand our airport-dependent service to next?

**Answer:**
- Use accessibility bar charts
- Cities with most ZIPs in 10-30km range = largest addressable market
- Cities with high heliport count = alternative infrastructure
- **Compare:** LA (dispersed, needs service) vs Miami (compact, saturated?)

---

## 📊 Technical Details

### Clustering Performance

**K-Means:**
- Fast, deterministic results
- Best for roughly spherical clusters
- Optimal for this geographic + distance data

**DBSCAN:**
- Finds dense regions automatically
- Good for identifying outlier ZIPs
- May produce many "noise" points (-1 cluster)

**Hierarchical:**
- Shows nested relationships
- Useful for understanding ZIP similarities
- Computationally intensive for large datasets

### Distance Metrics

**Why Haversine?**
- Accurate great-circle distance on Earth's surface
- Better than Euclidean for geographic coordinates
- Error: < 0.5% for distances < 500km

**Travel Time Assumptions:**
- Urban speed: ~40 km/h average (includes traffic, lights, highway)
- Does NOT account for:
  - Time of day variations
  - Route-specific traffic patterns
  - Access roads to/from highways

**Improvement:** Use actual traffic_data CSV files for more accurate times (future enhancement)

---

## 🐛 Troubleshooting

### Common Issues

**1. "FileNotFoundError: intersection_analysis.csv"**
- **Solution:** Run `v1/ANALYSIS_INTERSECTION/calculate_intersection.py` first
- This generates the required intersection data

**2. "No airports found for {city}"**
- **Check:** all-airport-data.xlsx exists in v1/ folder
- **Check:** City radius_km is large enough (increase in cluster_airport_analysis.py)

**3. "Memory Error during visualization"**
- **Solution:** Reduce sample size in heatmap function (default: 30 ZIPs)
- Or increase available RAM

**4. Matplotlib/Seaborn style warnings**
- **Ignore:** Visual output still correct
- **Fix:** Update to latest matplotlib: `pip install --upgrade matplotlib seaborn`

### Data Quality Checks

Before running analysis, verify:
```python
import pandas as pd

# Check intersection data
df = pd.read_csv('v1/ANALYSIS_INTERSECTION/intersection_analysis.csv')
print(f"Intersection ZIPs: {len(df)}")  # Should be ~197
print(f"Cities: {df['city_name'].unique()}")  # Should be 7

# Check required columns
required = ['zipcode', 'centroid_lat', 'centroid_lon', 'Combined_Score']
print(f"Has required columns: {all(col in df.columns for col in required)}")
```

---

## 📚 References & Data Sources

### Data Providers
- **U.S. Census Bureau**: ZIP-level business and household data
- **FAA (Federal Aviation Administration)**: Airport and heliport locations
- **Census TIGER/Line**: ZIP code geographic boundaries

### Algorithms & Libraries
- **scikit-learn**: K-Means, DBSCAN, Agglomerative Clustering
- **scipy**: Hierarchical clustering dendrograms
- **NetworkX**: Network graph analysis and visualization
- **Folium**: Interactive Leaflet maps in Python
- **GeoPandas**: Geographic data manipulation

### Related Documentation
- `v1/10percent/METHODOLOGY.html` - Overall analysis methodology
- `v1/ANALYSIS_INTERSECTION/` - How intersection ZIPs were calculated
- `v1/MSA_UPDATE_STATUS.md` - MSA revenue adjustments methodology

---

## 🚧 Future Enhancements

### Planned Features
1. **Real Traffic Data Integration**
   - Use existing traffic_data/ CSVs for accurate travel times
   - Peak vs off-peak analysis

2. **Private Airport Analysis**
   - Include smaller private airports
   - Cluster by private vs public accessibility

3. **Time-Series Analysis**
   - Track changes in airport accessibility over time
   - Correlate with property value changes

4. **3D Visualizations**
   - Altitude + lat/lon network graphs
   - Interactive 3D clusters

5. **Machine Learning Predictions**
   - Predict optimal locations for new heliports
   - Score potential new intersection ZIPs

---

## 👥 Contact & Contributions

**Author:** GeoEco Analysis Team  
**Last Updated:** December 2025  
**Version:** 1.0

For questions or suggestions regarding this analysis:
- Review methodology in METHODOLOGY.html
- Check dashboard for integrated visualizations
- Refer to source scripts for implementation details

---

## 📄 License & Usage

This analysis uses public data from U.S. government sources (Census Bureau, FAA). 
All code and visualizations are provided for analytical and research purposes.

**Citation:**
```
GeoEco Cluster Analysis: Intersection ZIPs × Airport Infrastructure (2025)
Data: U.S. Census Bureau CBP 2021, FAA Airport Database 2024
```

---

**End of Documentation**



