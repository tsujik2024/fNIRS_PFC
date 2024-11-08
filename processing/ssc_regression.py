# ssc_regression.py
import pandas as pd
import numpy as np


def ssc_regression(long_data: pd.DataFrame, short_data: pd.DataFrame):
    """
    Apply short channel correction technique to remove the superficial
    component of the probed tissue.

    Parameters:
    - long_data: DataFrame containing fNIRS data for the long channels
    - short_data: DataFrame containing fNIRS data for the short reference channels

    Returns:
    - DataFrame of corrected long channels
    """
    long_data_corrected = long_data.copy()
    short_mean = short_data.mean(axis=1)  # Calculate the mean across short channels

    for col in long_data.columns:
        Y = long_data[col]
        X = short_mean
        beta = np.dot(X, Y) / np.dot(X, X)  # Linear regression parameter
        long_data_corrected[col] = Y - beta * X  # Subtract regression fit

    return long_data_corrected
