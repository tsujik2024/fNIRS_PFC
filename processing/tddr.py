import numpy as np
import pandas as pd
from scipy.signal import butter, sosfiltfilt

def tddr(data: pd.DataFrame, sample_rate: int) -> pd.DataFrame:
    """
    Apply Temporal Derivative Distribution Repair (TDDR) algorithm to correct for motion artifacts.

    Parameters:
    - data: DataFrame containing fNIRS data for long channels
    - sample_rate: Sampling rate of the data in Hz

    Returns:
    - DataFrame with TDDR corrected data
    """
    corrected_df = data.copy()
    for col in corrected_df.columns:
        if corrected_df[col].dtype == np.float64:
            corrected_df[col] = _tddr(np.array(corrected_df[col], dtype='float64'), sample_rate)
    return corrected_df

def _tddr(signal: np.array, sample_rate: int) -> np.array:
    # Temporal Derivative Distribution Repair algorithm implementation
    signal_mean = np.mean(signal)
    signal -= signal_mean
    sos = butter(N=3, Wn=0.5, output='sos', fs=sample_rate)
    signal_low = sosfiltfilt(sos, signal)
    signal_high = signal - signal_low
    deriv = np.diff(signal_low)
    w = np.ones(deriv.shape)
    for _ in range(50):
        mu = np.sum(w * deriv) / np.sum(w)
        dev = np.abs(deriv - mu)
        sigma = 1.4826 * np.median(dev)
        r = dev / (sigma * 4.685)
        w = ((1 - r**2) * (r < 1)) ** 2
    new_deriv = w * (deriv - mu)
    signal_low_corrected = np.cumsum(np.insert(new_deriv, 0, 0.0))
    return signal_low_corrected + signal_high + signal_mean
