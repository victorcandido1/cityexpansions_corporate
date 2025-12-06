# Quick Start: Cluster Analysis Execution Guide

## 🚀 How to Run the Complete Cluster Analysis

### Step 1: Navigate to Directory
```bash
cd "G:\Meu Drive\Journey\Modelos\Revo\Strategy\Expansion_v2\GeoEco\v1\10percent"
```

### Step 2: Run Analysis Scripts (in order)

```bash
# 1. Generate clustering data and metrics (2-3 minutes)
python cluster_airport_analysis.py

# 2. Create network graphs (3-4 minutes)
python cluster_network_graphs.py

# 3. Generate maps and statistical visualizations (4-5 minutes)
python create_cluster_visualizations.py
```

### Total Time: ~10 minutes

---

## 📁 What Gets Created

### CSV Data Files (4 files)
- `cluster_results_by_city.csv` - 197 ZIPs with cluster assignments
- `cluster_metrics_by_city.csv` - Summary statistics per cluster
- `cluster_results_national.csv` - National-level clustering
- `airport_accessibility_metrics.csv` - Accessibility by city

### Interactive Maps (8 HTML files)
- `map_cluster_airports_los_angeles.html`
- `map_cluster_airports_new_york.html`
- `map_cluster_airports_chicago.html`
- `map_cluster_airports_dallas.html`
- `map_cluster_airports_houston.html`
- `map_cluster_airports_miami.html`
- `map_cluster_airports_san_francisco.html`
- `map_cluster_airports_national.html`

### Network Graphs (15 PNG files)
- `network_graph_{city}.png` (7 files)
- `network_graph_bipartite_{city}.png` (7 files)
- `network_graph_national.png`

### Statistical Charts (35 PNG files)
- `dendrogram_{city}.png` (7 files)
- `scatter_distance_score_{city}.png` (7 files)
- `heatmap_distances_{city}.png` (7 files)
- `boxplot_clusters_{city}.png` (7 files)
- `bar_accessibility_{city}.png` (7 files)

**Total: 62 output files**

---

## 📊 View Results

### Option 1: Dashboard (Recommended)
Open `dashboard_integrated.html` in your browser and scroll to:
**"✈️ Cluster Analysis: Intersection ZIPs × Airport Infrastructure"**

### Option 2: Individual Files
- **Interactive exploration:** Open any `map_cluster_airports_*.html`
- **Data analysis:** Open CSV files in Excel/Python
- **Visualizations:** View PNG charts

### Option 3: Documentation
Read `CLUSTER_ANALYSIS_README.md` for complete methodology and insights

---

## ✅ Verification Checklist

After running, verify:

```bash
# Check CSV files exist
ls cluster_*.csv airport_*.csv

# Check maps created
ls map_cluster_airports_*.html

# Check network graphs
ls network_graph_*.png

# Check statistical charts
ls dendrogram_*.png scatter_*.png heatmap_*.png boxplot_*.png bar_*.png
```

Expected output:
- 4 CSV files
- 8 HTML files  
- 50 PNG files

---

## 🐛 Troubleshooting

**Problem:** "FileNotFoundError: intersection_analysis.csv"  
**Solution:** First run `python ../ANALYSIS_INTERSECTION/calculate_intersection.py`

**Problem:** "Memory Error"  
**Solution:** Close other applications, increase available RAM

**Problem:** Missing visualizations  
**Solution:** Install missing packages:
```bash
pip install matplotlib seaborn networkx scipy
```

---

## 📚 Additional Resources

- **Complete Documentation:** `CLUSTER_ANALYSIS_README.md`
- **Methodology:** `METHODOLOGY.html` (main project docs)
- **Intersection Analysis:** `../ANALYSIS_INTERSECTION/`

---

**Ready to explore clusters of premium ZIPs around airport infrastructure!** ✈️🏠💼



