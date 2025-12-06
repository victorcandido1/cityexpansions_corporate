# Update Maps After MSA Adjustment

## YES - Maps Need Updating!

The corporate maps **DO use revenue data** and will need to be regenerated after the MSA update.

### Maps That Use Revenue Data:

1. **`corporate_maps_real_data.py`**
   - Uses: `estimated_revenue_M`
   - Displays revenue in tooltips
   - Uses revenue for scoring/ranking

2. **`create_national_maps.py`**
   - Uses: `estimated_revenue_M`
   - Shows revenue in popup information
   - Colors ZIPs by corporate power (which includes revenue)

### What Will Change in Maps:

**Tooltip Information:**
```html
<!-- BEFORE -->
<p>Revenue: $52,169M</p>

<!-- AFTER (Chicago example) -->
<p>Revenue: $43,517M</p>  <!-- 17% decrease -->
```

**ZIP Code Colors:**
- San Francisco ZIPs will be "hotter" (more revenue)
- Chicago ZIPs will be "cooler" (less revenue)
- Rankings within cities may shift

### How to Regenerate Maps:

```python
import os
os.chdir(r'G:\Meu Drive\Journey\Modelos\Revo\Strategy\Expansion_v2\GeoEco\v1\10percent')

# Regenerate corporate maps
print("Regenerating corporate maps...")
exec(open('corporate_maps_real_data.py').read())

# Regenerate national maps
print("Regenerating national maps...")
exec(open('create_national_maps.py').read())

print("\n✓ ALL MAPS UPDATED!")
```

### Or Run from Terminal:

```bash
cd "G:\Meu Drive\Journey\Modelos\Revo\Strategy\Expansion_v2\GeoEco\v1\10percent"
python corporate_maps_real_data.py
python create_national_maps.py
```

### Maps That Will Be Updated:

**City-Specific Maps:**
- `map_corporate_chicago.html`
- `map_corporate_new_york.html`
- `map_corporate_san_francisco.html`
- `map_corporate_los_angeles.html`
- `map_corporate_dallas.html`
- `map_corporate_houston.html`
- `map_corporate_miami.html`

**National Maps:**
- `map_corporate_national.html`
- `map_intersection_national.html` (if it uses corporate data)

### What Users Will See:

**In Map Tooltips:**
- Updated revenue figures
- New revenue per employee calculations
- Adjusted corporate power scores

**Visual Changes:**
- San Francisco/New York ZIPs more prominent (darker colors)
- Chicago/Houston ZIPs less prominent (lighter colors)
- Rankings may shift within each metro

### Time to Regenerate:

- Corporate maps: ~2-3 minutes
- National maps: ~1-2 minutes
- **Total: ~5 minutes**

### Complete Update Sequence:

```python
# 1. Update data (already done if you ran the MSA update)
# 2. Regenerate charts
exec(open('corporate_statistical_analysis.py').read())
exec(open('create_corporate_travel_time_weighted_charts.py').read())

# 3. Regenerate maps ← YOU ARE HERE
exec(open('corporate_maps_real_data.py').read())
exec(open('create_national_maps.py').read())

# 4. Done!
```

---

**Answer:** YES, maps are included and need updating!  
**They use:** `estimated_revenue_M` which has been adjusted  
**How to update:** Run the map generation scripts after data update  
**Time:** ~5 minutes additional

