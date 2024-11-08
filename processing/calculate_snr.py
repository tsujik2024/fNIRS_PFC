import pandas as pd
import numpy as np

def calculate_snr(walking_data, hbo_columns):
    """
    Calculates the SNR for each HbO channel in the walking_data DataFrame.

    Parameters:
        walking_data (DataFrame): The data during the walking task.
        hbo_columns (list): List of HbO column names.

    Returns:
        DataFrame: A DataFrame containing the SNR for each channel.
    """
    snr_list = []
    for col in hbo_columns:
        signal = walking_data[col].values
        mean_signal = np.mean(signal)
        std_signal = np.std(signal)
        if std_signal != 0:
            snr = mean_signal / std_signal
        else:
            snr = np.nan  # Avoid division by zero
        snr_list.append({'Channel': col, 'SNR': snr})

    snr_df = pd.DataFrame(snr_list)
    return snr_df
