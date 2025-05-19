import pandas as pd
import numpy as np

def time_to_seconds(t):
    """Convert a time string like '1:28.495' to seconds. Return np.nan if not valid."""
    try:
        mins, secs = t.split(':')
        return int(mins) * 60 + float(secs)
    except:
        return np.nan

# Load data
drivers = pd.read_csv("data-f1/kaggle/drivers.csv")
qualifying = pd.read_csv("data-f1/kaggle/qualifying.csv")
races = pd.read_csv("data-f1/kaggle/races.csv")

# Merge datasets
qual_with_drivers = pd.merge(qualifying, drivers, on="driverId", how="left")
merged_df = pd.merge(qual_with_drivers, races, on="raceId", how="left")

# Select and rename columns
result = merged_df[[
    "code", "name", "year", "q1", "q2", "q3"
]].rename(columns={
    "code": "Abbreviation",
    "name": "GrandPrix",
    "year": "Year",
    "q1": "Q1",
    "q2": "Q2",
    "q3": "Q3"
})

# Convert Q1–Q3 to seconds
for session in ['Q1', 'Q2', 'Q3']:
    result[f'{session}_sec'] = result[session].apply(time_to_seconds)

# Estimate missing Q2 and Q3 times based on earlier sessions
def estimate_missing_times(row):
    if pd.isna(row['Q2_sec']) and not pd.isna(row['Q1_sec']):
        row['Q2_sec'] = row['Q1_sec'] * 1.03  # Slightly slower than Q1

    if pd.isna(row['Q3_sec']):
        if not pd.isna(row['Q2_sec']):
            row['Q3_sec'] = row['Q2_sec'] * 1.02  # Slightly slower than Q2
        elif not pd.isna(row['Q1_sec']):
            row['Q3_sec'] = row['Q1_sec'] * 1.05  # Fallback if Q2 missing too
    return row

result = result.apply(estimate_missing_times, axis=1)

# Fill any remaining NaNs with median times per session
for session in ['Q1_sec', 'Q2_sec', 'Q3_sec']:
    median_val = result[session].median()
    result[session] = result[session].fillna(median_val)

# Calculate gaps to leader per race and session (after filling missing times)
for session in ['Q1', 'Q2', 'Q3']:
    sec_col = f'{session}_sec'
    gap_col = f'{session}_gap'
    result[gap_col] = result.groupby(['GrandPrix', 'Year'])[sec_col].transform(
        lambda x: x - x.min()
    )

# Drop intermediate _sec columns if not needed
result.drop(columns=['Q1_sec', 'Q2_sec', 'Q3_sec'], inplace=True)

# Save to CSV
result.to_csv("qualifying_results_cleaned_with_gaps.csv", index=False)

# Display some rows
print(result.head(20))
