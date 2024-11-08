import pandas as pd
import numpy as np

def average_channels(df: pd.DataFrame, channels_to_exclude=None) -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Must provide a DataFrame, not {type(df)}")

    channels_to_exclude = channels_to_exclude or []
    df_copy = df.copy()

    # Define hemisphere channels
    left_channels = [ch for ch in [4, 5, 6] if ch not in channels_to_exclude]
    right_channels = [ch for ch in [1, 2, 3] if ch not in channels_to_exclude]

    # Build columns
    left_hbo_cols = [f'CH{ch} HbO' for ch in left_channels if f'CH{ch} HbO' in df_copy.columns]
    left_hbr_cols = [f'CH{ch} HbR' for ch in left_channels if f'CH{ch} HbR' in df_copy.columns]
    right_hbo_cols = [f'CH{ch} HbO' for ch in right_channels if f'CH{ch} HbO' in df_copy.columns]
    right_hbr_cols = [f'CH{ch} HbR' for ch in right_channels if f'CH{ch} HbR' in df_copy.columns]

    # Average columns and create the return DataFrame
    ret_df = pd.DataFrame({
        'Sample number': df_copy['Sample number'],
        'left oxy': df_copy[left_hbo_cols].mean(axis=1),
        'left deoxy': df_copy[left_hbr_cols].mean(axis=1),
        'right oxy': df_copy[right_hbo_cols].mean(axis=1),
        'right deoxy': df_copy[right_hbr_cols].mean(axis=1),
        'grand oxy': df_copy[left_hbo_cols + right_hbo_cols].mean(axis=1),
        'grand deoxy': df_copy[left_hbr_cols + right_hbr_cols].mean(axis=1),
        'Event': df_copy['Event']
    })

    return ret_df
