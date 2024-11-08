import pandas as pd
import numpy as np
from scipy import integrate
from scipy import stats

def calculate_statistics(segments: dict, file: str, subject_id: str, condition: str, timepoint: str) -> pd.DataFrame:
    stats_dict = {
        'Subject': subject_id,
        'Condition': condition,
        'Timepoint': timepoint
    }

    for seg_name, seg_df in segments.items():
        for col in seg_df.columns:
            if col in ['Time', 'Event']:
                continue
            if 'grand oxy' not in col:  # Adjust based on your column names
                continue

            # Skip if the column is empty or contains all NaN values
            if seg_df[col].dropna().empty:
                print(f"Warning: Column {col} in segment {seg_name} is empty or all NaN for file {file}. Skipping calculations for this column.")
                continue

            # 1. Mean oxygenation
            stats_dict[f'{seg_name} {col} Mean'] = seg_df[col].mean()

            # 2. Standard deviation of oxygenation
            stats_dict[f'{seg_name} {col} StdDev'] = seg_df[col].std()

            # 3. Peak amplitude
            stats_dict[f'{seg_name} {col} Peak Amplitude'] = seg_df[col].max() - seg_df[col].min()

            # 4. Time to peak
            max_idx = seg_df[col].idxmax()
            if pd.isna(max_idx):
                print(f"Warning: Cannot find peak in column {col} for segment {seg_name} in file {file}.")
                stats_dict[f'{seg_name} {col} Time to Peak'] = np.nan
            else:
                peak_time = seg_df.loc[max_idx, 'Time']
                stats_dict[f'{seg_name} {col} Time to Peak'] = peak_time - seg_df['Time'].iloc[0]

            # 5. Area under the curve
            auc = integrate.trapz(seg_df[col], seg_df['Time'])
            stats_dict[f'{seg_name} {col} AUC'] = auc

            # 6. Slope (linear trend)
            slope, _, _, _, _ = stats.linregress(seg_df['Time'], seg_df[col])
            stats_dict[f'{seg_name} {col} Slope'] = slope

    return pd.DataFrame([stats_dict])

def split_segments(df: pd.DataFrame) -> dict:
    """
    Split the DataFrame into overall, first half (60 seconds), and second half (60 seconds) segments.

    Parameters:
    - df: Input DataFrame

    Returns:
    - Dictionary of DataFrames for each segment
    """
    overall = df.copy()
    first_half = df[df['Time'] <= 60].copy()
    second_half = df[df['Time'] > 60].copy()

    return {
        'Overall': overall,
        'First Half': first_half,
        'Second Half': second_half
    }


# Main processing function
def process_file(file_path: str) -> pd.DataFrame:
    """
    Process a single file and calculate statistics for all segments.

    Parameters:
    - file_path: Path to the input file

    Returns:
    - DataFrame with calculated statistics
    """
    df = pd.read_csv(file_path)
    segments = split_segments(df)
    stats = calculate_statistics(segments, file_path)
    return stats
