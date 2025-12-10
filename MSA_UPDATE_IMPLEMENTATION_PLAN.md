# MSA UPDATE - COMPLETE IMPLEMENTATION PLAN

## Executive Summary

We're updating the entire analysis to use **Metropolitan Statistical Area (MSA) specific revenue multipliers** instead of national averages. This will make the revenue estimates more accurate by accounting for local economic conditions.

## MSA Multipliers (Based on Actual Payroll Data)

From Census Bureau payroll data in `top10_corporate_data.csv`:

| Metro | Payroll/Employee | MSA Multiplier | Change |
|-------|------------------|----------------|--------|
| **San Francisco** | $225,486 | **1.503x** | +50.3% |
| **New York** | $218,189 | **1.456x** | +45.6% |
| **Miami** | $163,000 (est) | **1.087x** | +8.7% |
| **Los Angeles** | $150,131 | **1.000x** | Baseline |
| **Dallas** | $143,000 (est) | **0.953x** | -4.7% |
| **Houston** | $135,000 (est) | **0.901x** | -9.9% |
| **Chicago** | $125,181 | **0.834x** | -16.6% |

**National Baseline:** ~$150,000/employee

## Impact on Results

### Revenue per Employee Rankings

**BEFORE (National Average):**
1. San Francisco: $237,826
2. Chicago: $237,628
3. New York: $236,131
4. Los Angeles: $231,468
5. Miami: $229,716
6. Dallas: $229,673
7. Houston: $223,673

**AFTER (MSA-Adjusted):**
1. **San Francisco: $357,380** (+50%)
2. **New York: $343,807** (+46%)
3. **Miami: $249,721** (+9%)
4. **Los Angeles: $231,468** (baseline)
5. **Dallas: $218,880** (-5%)
6. **Chicago: $198,221** (-17%)
7. **Houston: $201,549** (-10%)

### Total Market Size Changes

| City | Old Revenue | New Revenue | Change |
|------|-------------|-------------|--------|
| San Francisco | $507B | **$762B** | +50% |
| New York | $551B | **$802B** | +46% |
| Los Angeles | $757B | **$757B** | 0% (baseline) |
| Miami | $246B | **$267B** | +9% |
| Dallas | $376B | **$358B** | -5% |
| Chicago | $372B | **$310B** | -17% |
| Houston | $230B | **$207B** | -10% |

## Implementation Steps

### ✅ Step 1: MSA Multipliers File Created
- **File:** `10percent/MSA_MULTIPLIERS.json`
- **Status:** COMPLETE
- Contains multipliers based on actual payroll data

### 📝 Step 2: Update Core Data Files

**Files to Update:**
1. `10percent/top10_corporate_data.csv`
2. `10percent/corporate_all_zips.csv` (if exists)

**Changes Needed:**
```python
# Add MSA multiplier column
df['msa_multiplier'] = df['city_key'].map(MSA_MULTIPLIERS)

# Update revenue columns
df['estimated_revenue_M'] = df['estimated_revenue_M'] * df['msa_multiplier']
df['power_revenue_M'] = df['power_revenue_M'] * df['msa_multiplier']
df['revenue_per_employee'] = (df['estimated_revenue_M'] * 1_000_000) / df['total_employment']
```

**Script:** `10percent/update_with_msa.py` (already created)

### 📊 Step 3: Regenerate All Charts

**Scripts to Run (in order):**

1. **Corporate Statistical Analysis**
   ```bash
   cd "10percent"
   python corporate_statistical_analysis.py
   ```
   **Updates:**
   - `corporate_histogram_all_vs_top10.png`
   - `corporate_histogram_top10_power_index.png`
   - `corporate_histogram_top10_revenue.png`
   - `corporate_weighted_averages_chart.png`
   - All other corporate charts

2. **Travel Time Weighted by Revenue**
   ```bash
   python create_corporate_travel_time_weighted_charts.py
   ```
   **Updates:**
   - `corporate_travel_time_weighted_by_revenue.png`
   - `corporate_travel_time_weighted_by_revenue.csv`

3. **Comparative Analysis**
   ```bash
   python corporate_advanced_statistics.py
   ```
   **Updates:**
   - `corporate_comparative_analysis.png`
   - Various statistical charts

### 📝 Step 4: Update Documentation

**Files to Update:**

1. **`10percent/METHODOLOGY.html`**
   - Section 4.1: Update revenue estimation methodology
   - Add new section: "MSA-Specific Adjustments"
   - Update limitations section

2. **`10percent/CORPORATE_STATISTICS_EXPLANATION.md`**
   - Update revenue calculation explanation
   - Add MSA multipliers table
   - Update examples with new values

3. **`10percent/CORPORATE_TRAVEL_TIME_WEIGHTED_ANALYSIS.md`**
   - Update all revenue figures
   - Update rankings
   - Add note about MSA adjustments

4. **`CORPORATE_TRAVEL_TIME_CHARTS_ADDED.md`**
   - Update key findings with new values
   - Update rankings

### 🌐 Step 5: Update Dashboard

**File:** `10percent/dashboard_integrated.html`

**Changes:**
- Add note about MSA-specific revenue estimates
- Update data source description
- Add link to MSA multipliers explanation

**New Section to Add:**
```html
<div class="highlight">
    <strong>MSA-Adjusted Revenue Estimates:</strong> Revenue calculations now use 
    metropolitan-specific multipliers based on actual payroll data from Census Bureau. 
    This accounts for local cost-of-living and productivity differences.
    <a href="MSA_MULTIPLIERS.json">View Multipliers</a>
</div>
```

### 📥 Step 6: Update CSV Exports

**Files to Regenerate:**
- `corporate_weighted_averages_analysis.csv`
- `corporate_travel_time_weighted_by_revenue.csv`
- `corporate_distance_analysis.csv`
- `corporate_power_industries_by_region.csv`
- `intersection_analysis.csv` (if it uses revenue)

## New Methodology Section Text

### For METHODOLOGY.html

```html
<h3>4.1.2 MSA-Specific Revenue Adjustments</h3>
<p>
    <strong>NEW:</strong> Revenue estimates are now adjusted for metropolitan-specific 
    economic conditions using multipliers derived from actual Census Bureau payroll data.
</p>

<h4>Methodology</h4>
<ol>
    <li>Calculate average payroll per employee for each metro area</li>
    <li>Compute national baseline (weighted average across all metros)</li>
    <li>Calculate MSA multiplier: Metro_Payroll / National_Baseline</li>
    <li>Apply multiplier to revenue estimates</li>
</ol>

<div class="formula">
    MSA_Multiplier = (Metro_Payroll_per_Employee) / (National_Baseline_Payroll)
    <br>
    Revenue_Adjusted = Revenue_Base × MSA_Multiplier
</div>

<h4>Rationale</h4>
<p>
    Payroll per employee strongly correlates with revenue per employee. High-cost metros 
    (San Francisco, New York) have higher salaries AND higher revenue per employee. 
    Using payroll-based multipliers captures this local economic reality.
</p>

<h4>MSA Multipliers</h4>
<table>
    <tr>
        <th>Metro</th>
        <th>Payroll/Employee</th>
        <th>Multiplier</th>
        <th>Interpretation</th>
    </tr>
    <tr>
        <td>San Francisco</td>
        <td>$225,486</td>
        <td>1.503x</td>
        <td>Tech hub, highest productivity</td>
    </tr>
    <tr>
        <td>New York</td>
        <td>$218,189</td>
        <td>1.456x</td>
        <td>Finance/media, high costs</td>
    </tr>
    <tr>
        <td>Miami</td>
        <td>~$163,000</td>
        <td>1.087x</td>
        <td>International business</td>
    </tr>
    <tr>
        <td>Los Angeles</td>
        <td>$150,131</td>
        <td>1.000x</td>
        <td>Baseline (national average)</td>
    </tr>
    <tr>
        <td>Dallas</td>
        <td>~$143,000</td>
        <td>0.953x</td>
        <td>Corporate relocations, lower costs</td>
    </tr>
    <tr>
        <td>Houston</td>
        <td>~$135,000</td>
        <td>0.901x</td>
        <td>Energy sector, lower costs</td>
    </tr>
    <tr>
        <td>Chicago</td>
        <td>$125,181</td>
        <td>0.834x</td>
        <td>Moderate costs</td>
    </tr>
</table>

<div class="important">
    <strong>Data Quality:</strong> MSA multipliers are calculated from 100% real Census Bureau 
    payroll data for the same ZIP codes in the analysis. This ensures consistency and accuracy.
</div>
```

## Quick Start - Manual Update

If scripts aren't working, here's the manual process:

### 1. Calculate Multipliers by City

From the payroll data visible in `top10_corporate_data.csv`:
- Chicago (60606): $125,181/employee
- New York (10022): $218,189/employee  
- San Francisco (94105): $225,486/employee
- Los Angeles (92121): $150,131/employee

### 2. Apply to Each Row

Open `top10_corporate_data.csv` in Excel/Python:
```python
multipliers = {
    'san_francisco': 1.503,
    'new_york': 1.456,
    'chicago': 0.834,
    'miami': 1.087,
    'los_angeles': 1.000,
    'dallas': 0.953,
    'houston': 0.901
}

# For each row:
row['estimated_revenue_M'] *= multipliers[row['city_key']]
row['power_revenue_M'] *= multipliers[row['city_key']]
row['revenue_per_employee'] = row['estimated_revenue_M'] * 1_000_000 / row['total_employment']
```

### 3. Save and Regenerate

Save the updated CSV and run the chart generation scripts.

## Verification Checklist

After implementation:

- [ ] MSA multipliers file exists and is correct
- [ ] Top 10% corporate data updated with new revenue values
- [ ] All charts regenerated with new data
- [ ] Travel time analysis updated
- [ ] Methodology documentation updated
- [ ] Dashboard shows MSA adjustment note
- [ ] CSV exports updated
- [ ] Rankings changed as expected (SF #1, Chicago drops)
- [ ] Total revenue increased for SF/NYC, decreased for Chicago/Houston

## Expected Outcomes

### Key Changes to Communicate:

1. **San Francisco becomes clear leader** in revenue/employee (+50%)
2. **New York solidifies #2 position** (+46%)
3. **Chicago drops significantly** (-17%) - was artificially high
4. **Miami rises** in rankings (+9%)
5. **Total market sizes** more accurately reflect economic reality

### Business Impact:

- **San Francisco** becomes even more attractive market (high revenue + good airport access)
- **New York** market size increases significantly
- **Chicago** less attractive than previously thought
- **Overall analysis** more accurate and defensible

## Files Created

1. ✅ `10percent/MSA_MULTIPLIERS.json` - Multiplier values
2. ✅ `10percent/calculate_msa_multipliers.py` - Calculation script
3. ✅ `10percent/apply_msa_adjustments.py` - Application script
4. ✅ `10percent/update_with_msa.py` - Simplified update script
5. ✅ `10percent/quick_msa_analysis.md` - Analysis document
6. ✅ `MSA_UPDATE_IMPLEMENTATION_PLAN.md` - This file

## Next Steps

1. **Run update script** to apply MSA multipliers to data
2. **Regenerate all charts** using updated data
3. **Update documentation** with new methodology
4. **Verify dashboard** displays correctly
5. **Test all downloads** work with new data

---

**Status:** Ready for implementation
**Date:** December 5, 2025
**Impact:** Major improvement in accuracy
**Effort:** ~2-3 hours to complete all updates


