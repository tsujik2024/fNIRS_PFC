import os
import pandas as pd
import numpy as np
import warnings
import logging
import matplotlib.pyplot as plt

from processing.read_txt import read_txt_file
from processing.read_mat import read_mat
from processing.filter import fir_filter
from processing.tddr import tddr
from processing.ssc_regression import ssc_regression


def extract_timepoint(file_path):
    """
    Extracts the timepoint from the file path based on your folder structure.
    """
    timepoint = os.path.basename(os.path.dirname(file_path))
    return timepoint


def plot_signals(walking_data, subject_id, condition, output_folder):
    """
    Plots the average oxygenated and deoxygenated signals and saves the plot.

    Parameters:
        walking_data (DataFrame): Data containing the signals
        subject_id (str): Subject identifier
        condition (str): Task condition (ST or DT)
        output_folder (str): Output directory for saving plots
    """
    plt.figure(figsize=(12, 6))
    time_points = np.arange(len(walking_data)) / 50  # Assuming 50Hz sampling rate

    plt.plot(time_points, walking_data['grand oxy'], 'r-', label='Oxygenated')
    plt.plot(time_points, walking_data['grand deoxy'], 'b-', label='Deoxygenated')

    plt.xlabel('Time (seconds)')
    plt.ylabel('Signal Amplitude')
    plt.title(f'Average Signals for Subject {subject_id} - {condition}')
    plt.legend()
    plt.grid(True)

    plot_filename = os.path.join(output_folder, f"{subject_id}_{condition}_signals.png")
    plt.savefig(plot_filename)
    plt.close()
    print(f"Signal plot saved to {plot_filename}")


def calculate_snr(walking_data, hbo_columns):
    """
    Calculates the SNR for each HbO channel in the walking_data DataFrame.
    """
    snr_list = []
    for col in hbo_columns:
        signal = walking_data[col].values
        mean_signal = np.mean(signal)
        std_signal = np.std(signal)
        snr = mean_signal / std_signal if std_signal != 0 else np.nan
        snr_list.append({'Channel': col, 'SNR': snr})

    return pd.DataFrame(snr_list)


def process_file_delta_txt(
            file_path,
            output_folder,
            dir_path,
            NIRSsamprate=50,
            st_data_dict=None,
            st_mean_hbo_dict=None,
            warnings_file=None,
            channels_excluded_file=None,
            all_snr_data=None,
            all_ratio_data=None
    ):
    """
    Process NIRS data files and calculate various metrics.
    """
    # Initialize logging if warnings_file is not provided
    if warnings_file is None:
        warnings_file = os.path.join(output_folder, 'warnings.txt')
        logging.basicConfig(
            level=logging.WARNING,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename=warnings_file,
            filemode='a'
        )

        def custom_warning_handler(message, category, filename, lineno, file=None, line=None):
            logging.warning(f"{filename}:{lineno}: {category.__name__}: {message}")

        warnings.showwarning = custom_warning_handler

    print(f"Processing file: {file_path}")

    # Extract filename information
    filename = os.path.basename(file_path)
    filename_without_ext = os.path.splitext(filename)[0]
    conditions = ['LongWalk_ST', 'LongWalk_DT']

    # Initialize variables
    subject_id = 'Unknown'
    condition = 'Unknown'
    dataMatrix = None

    # Load data based on file extension
    try:
        if file_path.endswith('.txt'):
            result = read_txt_file(file_path)
        elif file_path.endswith('.mat'):
            result = read_mat(file_path)
        else:
            warning_msg = f"Unsupported file format for {file_path}"
            warnings.warn(warning_msg)
            return

        dataMatrix = result['data']
        metadata = result['metadata']
    except Exception as e:
        warning_msg = f"Error reading file {file_path}: {str(e)}"
        warnings.warn(warning_msg)
        return

    # Validate data
    if dataMatrix is None or dataMatrix.empty:
        warning_msg = f"Error: Could not read the file {file_path} or data is empty."
        warnings.warn(warning_msg)
        return

    # Extract condition and subject ID
    for cond in conditions:
        if cond in filename_without_ext:
            condition = cond
            subject_id = filename_without_ext.replace(f'_{cond}_converted', '')
            break

    timepoint = extract_timepoint(file_path)

    # Create a copy of dataMatrix
    df = dataMatrix.copy()

    # Apply FIR bandpass filter
    try:
        order = 1000
        Wn = [0.01, 0.1]
        fs = NIRSsamprate
        if len(df) <= 3 * order:
            warning_msg = f"Data too short to apply FIR filter for file {file_path}."
            warnings.warn(warning_msg)
            return
        df_filtered = fir_filter(df.copy(), order=order, Wn=Wn, fs=fs)
        print(f"FIR bandpass filter applied to file {file_path}")
    except Exception as e:
        warning_msg = f"Error applying FIR filter to file {file_path}: {e}"
        warnings.warn(warning_msg)
        return

    # Define channel columns
    short_channel_cols = ['Rx2-Tx7 O2Hb', 'Rx2-Tx7 HHb', 'Rx2-Tx8 O2Hb', 'Rx2-Tx8 HHb']
    long_channel_cols = [
        'Rx1-Tx1 O2Hb', 'Rx1-Tx1 HHb', 'Rx1-Tx2 O2Hb', 'Rx1-Tx2 HHb',
        'Rx1-Tx3 O2Hb', 'Rx1-Tx3 HHb', 'Rx1-Tx4 O2Hb', 'Rx1-Tx4 HHb',
        'Rx2-Tx5 O2Hb', 'Rx2-Tx5 HHb', 'Rx2-Tx6 O2Hb', 'Rx2-Tx6 HHb'
    ]

    # Apply Short Channel Regression
    if all(col in df_filtered.columns for col in short_channel_cols):
        short_data = df_filtered[short_channel_cols]
        long_data = df_filtered[long_channel_cols]

        try:
            df_corrected = ssc_regression(long_data=long_data, short_data=short_data)
            print(f"Short Channel Regression applied to file {file_path}")
        except Exception as e:
            warning_msg = f"Error applying Short Channel Regression to file {file_path}: {e}"
            warnings.warn(warning_msg)
            return
    else:
        print("No short channel columns found. Proceeding without Short Channel Regression.")
        df_corrected = df_filtered

    # Apply TDDR for motion artifact correction
    try:
        df_corrected = tddr(df_corrected.copy(), sample_rate=NIRSsamprate)
        print(f"TDDR motion artifact correction applied for file {file_path}")
    except Exception as e:
        warning_msg = f"Error applying TDDR to file {file_path}: {e}"
        warnings.warn(warning_msg)
        return

    # Average HbO and HbR channels
    hbo_cols = [col for col in df_corrected.columns if 'O2Hb' in col]
    hbr_cols = [col for col in df_corrected.columns if 'HHb' in col]

    if not hbo_cols or not hbr_cols:
        warning_msg = f"No HbO or HHb columns found in file {file_path}. Skipping."
        warnings.warn(warning_msg)
        return

    df_corrected['grand oxy'] = df_corrected[hbo_cols].mean(axis=1)
    df_corrected['grand deoxy'] = df_corrected[hbr_cols].mean(axis=1)

    # Define sample intervals
    s2_sample = int(20 * NIRSsamprate)
    s3_sample = s2_sample + int(120 * NIRSsamprate)

    total_samples = len(df_corrected)
    if s3_sample > total_samples:
        s3_sample = total_samples - 1

    # Process data based on condition
    if condition == 'LongWalk_ST':
        return process_st_condition(
            df_corrected, subject_id, timepoint, s2_sample, s3_sample,
            output_folder, hbo_cols, st_mean_hbo_dict, st_data_dict, all_snr_data
        )
    elif condition == 'LongWalk_DT':
        return process_dt_condition(
            df_corrected, subject_id, timepoint, s2_sample, s3_sample,
            output_folder, hbo_cols, st_mean_hbo_dict, all_snr_data, all_ratio_data
        )


def process_st_condition(df_corrected, subject_id, timepoint, s2_sample, s3_sample,
                        output_folder, hbo_cols, st_mean_hbo_dict, st_data_dict, all_snr_data):
    """
    Process Single Task (ST) condition data.
    """
    walking_data_st = df_corrected.iloc[s2_sample:s3_sample + 1].copy()
    walking_data_st.reset_index(drop=True, inplace=True)

    # Plot signals before calculating ratios
    plot_signals(walking_data_st, subject_id, 'ST', output_folder)

    mean_hbo_st = walking_data_st['grand oxy'].mean()
    print(f"Mean HbO for ST condition ({subject_id}): {mean_hbo_st}")

    if st_mean_hbo_dict is not None:
        st_mean_hbo_dict[subject_id] = mean_hbo_st

    if st_data_dict is not None:
        st_data_dict[subject_id] = walking_data_st.copy()

    # Calculate SNR and add to the combined DataFrame
    if all_snr_data is not None:
        snr_st = calculate_snr(walking_data_st, hbo_cols)
        snr_st['Subject'] = subject_id
        snr_st['Condition'] = 'ST'
        snr_st['Timepoint'] = timepoint
        all_snr_data.append(snr_st)


def process_dt_condition(df_corrected, subject_id, timepoint, s2_sample, s3_sample,
                        output_folder, hbo_cols, st_mean_hbo_dict, all_snr_data, all_ratio_data):
    """
    Process Dual Task (DT) condition data.
    """
    if st_mean_hbo_dict is None or subject_id not in st_mean_hbo_dict:
        warning_msg = f"No ST mean HbO data found for subject {subject_id}"
        warnings.warn(warning_msg)
        return

    mean_hbo_st = st_mean_hbo_dict[subject_id]
    walking_data_dt = df_corrected.iloc[s2_sample:s3_sample + 1].copy()
    walking_data_dt.reset_index(drop=True, inplace=True)

    # Plot signals before calculating ratios
    plot_signals(walking_data_dt, subject_id, 'DT', output_folder)

    walking_data_dt['grand oxy'] -= mean_hbo_st

    # Calculate means and ratios
    mid_index = len(walking_data_dt) // 2
    mean_hbo_first_half = walking_data_dt['grand oxy'].iloc[:mid_index].mean()
    mean_hbo_second_half = walking_data_dt['grand oxy'].iloc[mid_index:].mean()
    mean_hbo_overall = walking_data_dt['grand oxy'].mean()
    ratio_dt_st = mean_hbo_overall / mean_hbo_st if abs(mean_hbo_st) > 1e-6 else np.nan

    # Add data to the combined ratio DataFrame
    if all_ratio_data is not None:
        all_ratio_data.append({
            'Subject': subject_id,
            'Timepoint': timepoint,
            'Mean_HbO_FirstHalf': mean_hbo_first_half,
            'Mean_HbO_SecondHalf': mean_hbo_second_half,
            'Mean_HbO_Overall': mean_hbo_overall,
            'Ratio_DT_over_ST': ratio_dt_st
        })

    # Calculate SNR and add to the combined DataFrame
    if all_snr_data is not None:
        snr_dt = calculate_snr(walking_data_dt, hbo_cols)
        snr_dt['Subject'] = subject_id
        snr_dt['Condition'] = 'DT'
        snr_dt['Timepoint'] = timepoint
        all_snr_data.append(snr_dt)


def save_combined_data(all_snr_data, all_ratio_data, output_folder):
    """
    Combines and saves all SNR and ratio data to CSV files.
    """
    # Save combined SNR data

    combined_snr = pd.concat(all_snr_data, ignore_index=True)
    snr_output_file = os.path.join(output_folder, 'combined_SNR.csv')
    combined_snr.to_csv(snr_output_file, index=False)
    print(f"Combined SNR data saved to {snr_output_file}")

    # Save combined ratio data
    if all_ratio_data:
        combined_ratios = pd.DataFrame(all_ratio_data)
        ratio_output_file = os.path.join(output_folder, 'combined_ratios.csv')
        combined_ratios.to_csv(ratio_output_file, index=False)
        print(f"Combined ratio data saved to {ratio_output_file}")