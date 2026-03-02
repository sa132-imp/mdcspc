import pandas as pd
from pathlib import Path

# Load the CSV data
csv_file = Path('tests/data/xmr_golden_input.csv')
df_csv = pd.read_csv(csv_file, parse_dates=["Month"])

# Check and add 'last_date' if needed (let's assume it's the last available 'Month' for each OrgCode and MetricName)
df_csv['last_date'] = df_csv.groupby(['OrgCode', 'MetricName'])['Month'].transform('last')

# Print the columns to check if 'last_date' was added
print("CSV Columns after adding 'last_date':", df_csv.columns)

# Now print the 'last_date' column
print("CSV last_date:\n", df_csv['last_date'].head())