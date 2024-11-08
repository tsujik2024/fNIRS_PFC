import pandas as pd
import numpy as np


def baseline_subtraction(df: pd.DataFrame, events_df: pd.DataFrame, baseline_df: pd.DataFrame = None):
    corrected_df = df.copy()

    if baseline_df is not None:
        # Use the provided baseline_df to compute the baseline mean
        for ch in corrected_df.columns:
            if ch not in ['Sample number', 'Event', 'Time (s)']:
                baseline_mean = baseline_df[ch].mean()
                corrected_df[ch] = corrected_df[ch] - baseline_mean
    else:
        if len(events_df) != 3:
            raise ValueError(
                f"The number of events found was {len(events_df)}, expected 3."
            )
        # Find the sample numbers corresponding to 'S1' and 'S2'
        s1_sample = events_df.loc[events_df['Event'] == 'S1', 'Sample number'].values[0]
        s2_sample = events_df.loc[events_df['Event'] == 'S2', 'Sample number'].values[0]

        start = int(s1_sample)
        end = int(s2_sample)

        # Check if 'start' and 'end' are within bounds
        if start < 0 or end > len(corrected_df):
            raise ValueError(
                f"Event indices are out of bounds: start={start}, end={end}, data length={len(corrected_df)}"
            )

        for ch in corrected_df.columns:
            if ch not in ['Sample number', 'Event', 'Time (s)']:
                # Calculate the mean during the baseline period
                quiet_stance = corrected_df.loc[start:end, ch]
                quiet_stance_mean = quiet_stance.mean()
                # Subtract the mean from the entire signal
                corrected_df[ch] = corrected_df[ch] - quiet_stance_mean

    return corrected_df
