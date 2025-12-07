@echo off
cd /d "G:\Meu Drive\Journey\Modelos\Revo\Strategy\Expansion_v2\GeoEco\v1\10percent"

echo ================================================================================
echo MSA UPDATE - EXECUTING
echo ================================================================================
echo.

python -c "import pandas as pd; import numpy as np; import json; import os; import shutil; from datetime import datetime; print('Starting...'); os.chdir(r'G:\Meu Drive\Journey\Modelos\Revo\Strategy\Expansion_v2\GeoEco\v1\10percent'); timestamp = datetime.now().strftime('%%Y%%m%%d_%%H%%M%%S'); backup_dir = f'BACKUP_NATIONAL_AVG_{timestamp}'; os.makedirs(backup_dir, exist_ok=True); shutil.copy2('top10_corporate_data.csv', f'{backup_dir}/top10_corporate_data.csv'); print(f'BACKUP: {backup_dir}'); df = pd.read_csv('top10_corporate_data.csv'); print(f'LOADED: {len(df)} rows'); city_data = df.groupby('city_key').agg({'total_payroll_K': lambda x: (x * 1000).sum(), 'total_employment': 'sum', 'city_name': 'first'}).reset_index(); city_data['payroll_per_emp'] = city_data['total_payroll_K'] * 1000 / city_data['total_employment']; national_baseline = (city_data['payroll_per_emp'] * city_data['total_employment']).sum() / city_data['total_employment'].sum(); city_data['msa_multiplier'] = city_data['payroll_per_emp'] / national_baseline; print(f'BASELINE: ${national_baseline:,.0f}'); print(city_data[['city_name', 'msa_multiplier']].to_string(index=False)); multipliers = dict(zip(city_data['city_key'], city_data['msa_multiplier'])); json.dump({'national_baseline': national_baseline, 'multipliers': multipliers}, open('msa_multipliers.json', 'w'), indent=2); print('SAVED: msa_multipliers.json'); df['msa_multiplier'] = df['city_key'].map(multipliers); df['estimated_revenue_M_original'] = df['estimated_revenue_M'].copy(); df['estimated_revenue_M'] = df['estimated_revenue_M'] * df['msa_multiplier']; df['power_revenue_M'] = df['power_revenue_M'] * df['msa_multiplier']; df['revenue_per_employee'] = (df['estimated_revenue_M'] * 1_000_000) / df['total_employment']; print('APPLIED MULTIPLIERS'); [print(f\"{df[df['city_key']==city]['city_name'].iloc[0]:20} ${df[df['city_key']==city]['estimated_revenue_M_original'].sum():>10,.0f}M -> ${df[df['city_key']==city]['estimated_revenue_M'].sum():>10,.0f}M ({multipliers[city]:.3f}x)\") for city in sorted(df['city_key'].unique())]; df.to_csv('top10_corporate_data.csv', index=False); print('SAVED: top10_corporate_data.csv'); print('UPDATE COMPLETE!')"

echo.
echo ================================================================================
echo DONE! Check the output above.
echo ================================================================================
pause

