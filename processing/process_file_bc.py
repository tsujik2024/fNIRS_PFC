import os
import pandas as pd
import numpy as np
import warnings

from processing.read_txt import read_txt_file
from processing.filter import fir_filter
from processing.ssc_regression import ssc_regression
from processing.tddr import tddr
from processing.baseline import baseline_subtraction
from processing.average_channels import average_channels
from processing.nirs_statistics import calculate_statistics, split_segments
from processing.plot_mean_signals import plot_mean_signals  # Ensure this is imported

def process_file(file_path, output_folder, dir_path, NIRSsamprate=50):
    print(f"Processing file: {file_path}")

    # Initialize a flag to indicate if the specific warning occurred
    invalid_divide_warning_occurred = False

    # Extract subject ID, condition, and timepoint from file path
    relative_path = os.path.relpath(file_path, dir_path)
    path_parts = relative_path.split(os.sep)
    timepoint = 'Unknown'
    for part in path_parts:
        if part in ['Baseline', 'Pre', 'Post']:
            timepoint = part
            break
    subject_id = path_parts[0]
    filename = os.path.basename(file_path)
    if 'LongWalk_ST' in filename:
        condition = 'LongWalk_ST'
    elif 'LongWalk_DT' in filename:
        condition = 'LongWalk_DT'
    else:
        condition = 'Unknown'

    # Initialize a list to hold channels excluded due to zeros
    channels_to_exclude = []

    # Capture warnings during processing
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        # Read and structure the data
        result = read_txt_file(file_path)
        dataMatrix = result['data']
        metadata = result['metadata']

        # Ensure the file was read correctly
        if dataMatrix is None or dataMatrix.empty:
            print(f"Error: Could not read the file {file_path}. Please check the format.")
            return None, False

        # Exclude 'Sample number' and 'Event' columns
        data_columns = dataMatrix.columns[1:-1]  # Data columns only
        num_channels = len(data_columns) // 2  # Number of channels

        # Initialize the new column names
        data_column_names = ['Sample number']

        # Assign names to data columns (HbO in odd columns, HbR in even columns)
        for i in range(num_channels):
            data_column_names.append(f'CH{i+1} HbO')  # Oxygenated data
            data_column_names.append(f'CH{i+1} HbR')  # Deoxygenated data

        # Add 'Event' to the end
        data_column_names += ['Event']

        # Check that the number of new column names matches the number of columns
        if len(data_column_names) != len(dataMatrix.columns):
            print(f"Column count mismatch in file {file_path}: Expected {len(dataMatrix.columns)} columns, but got {len(data_column_names)} names.")
            return None, False

        # Assign the new column names
        dataMatrix.columns = data_column_names

        # Proceed with dataMatrix as df
        df = dataMatrix.copy()

        # Remove initial second of data and reset index
        df = df.iloc[NIRSsamprate:].reset_index(drop=True)

        # Update 'Sample number' to reflect new indices
        df['Sample number'] = df.index

        # Since the 'Event' column is unreliable, we will set it to NaN
        df['Event'] = pd.NA

        # Identify and exclude columns with all zeros
        for i in range(1, num_channels + 1):
            hbo_col = f'CH{i} HbO'
            hbr_col = f'CH{i} HbR'

            if hbo_col in df.columns and hbr_col in df.columns:
                # Check if either HbO or HbR column has all zeros
                hbo_zero = df[hbo_col].eq(0).all()
                hbr_zero = df[hbr_col].eq(0).all()
                if hbo_zero or hbr_zero:
                    # Add channel number to the exclusion list
                    channels_to_exclude.append(i)
                    zero_col = 'HbO and HbR' if hbo_zero and hbr_zero else ('HbO' if hbo_zero else 'HbR')
                    print(f"Channel {i} has zero data in {zero_col}. Excluding both HbO and HbR columns for this channel.")

        # Exclude the identified channels
        for ch in channels_to_exclude:
            hbo_col = f'CH{ch} HbO'
            hbr_col = f'CH{ch} HbR'
            if hbo_col in df.columns:
                df.drop(columns=[hbo_col], inplace=True)
            if hbr_col in df.columns:
                df.drop(columns=[hbr_col], inplace=True)

        # Write excluded channels to a TXT file if any channels were excluded
        if channels_to_exclude:
            log_file = os.path.join(output_folder, 'channels_excluded_due_to_zero.txt')
            with open(log_file, 'a') as f:
                f.write(f"Subject: {subject_id}, Condition: {condition}, Timepoint: {timepoint}, Channels Excluded Due to Zeros: {channels_to_exclude}\n")

        # Proceed with processing steps using the updated df
        # Ensure there are channels left to process
        if not any('HbO' in col or 'HbR' in col for col in df.columns):
            print(f"No data left to process for file {file_path} after excluding zero columns.")
            return None, False

        # Calculate total number of samples and total time
        total_samples = len(df)
        total_time = total_samples / NIRSsamprate  # in seconds

        # Define event times in seconds
        event_times = {
            'S1': 0,    # Start of first quiet stance (adjust as needed)
            'S2': 20,   # Participant starts walking (adjust as needed)
            'S3': total_time - 10   # Participant stops walking (10 seconds before end)
        }

        # Convert event times to sample numbers
        event_samples = {
            event_label: int(time * NIRSsamprate)
            for event_label, time in event_times.items()
        }

        # Ensure event sample numbers are within the data range
        event_samples = {k: v for k, v in event_samples.items() if 0 <= v < total_samples}

        # Create events_df DataFrame
        events_df = pd.DataFrame({
            'Sample number': list(event_samples.values()),
            'Event': list(event_samples.keys())
        })

        # Insert the events into the 'Event' column in df
        for idx, row in events_df.iterrows():
            sample_num = row['Sample number']
            event_label = row['Event']
            df.at[sample_num, 'Event'] = event_label

        # Total number of channels (originally 8)
        total_channels = 8

        # Define short and long channel indices
        short_channel_indices = [ch for ch in [7, 8] if ch not in channels_to_exclude]  # Short channels
        long_channel_indices = [ch for ch in range(1, total_channels + 1) if ch not in short_channel_indices and ch not in channels_to_exclude]

        # Create lists of HbO and HbR columns for short and long channels
        short_channel_cols = [f'CH{ch} HbO' for ch in short_channel_indices if f'CH{ch} HbO' in df.columns] + \
                             [f'CH{ch} HbR' for ch in short_channel_indices if f'CH{ch} HbR' in df.columns]
        long_channel_cols = [f'CH{ch} HbO' for ch in long_channel_indices if f'CH{ch} HbO' in df.columns] + \
                            [f'CH{ch} HbR' for ch in long_channel_indices if f'CH{ch} HbR' in df.columns]

        # Check if the short channel columns exist
        if not short_channel_cols:
            print(f"Warning: No short channel columns found in {file_path}. Skipping short channel regression.")
            long_corrected = df[long_channel_cols + ['Sample number', 'Event']].copy()
        else:
            short_data = df[short_channel_cols].copy()
            long_data = df[long_channel_cols].copy()

            # Apply short channel regression
            long_corrected_data = ssc_regression(long_data, short_data)

            # Ensure 'Sample number' and 'Event' columns are preserved
            long_corrected = long_corrected_data.copy()
            long_corrected['Sample number'] = df['Sample number']
            long_corrected['Event'] = df['Event']

        # TDDR Motion Correction
        tddr_corrected_data = tddr(long_corrected, NIRSsamprate)

        # Ensure 'Sample number' and 'Event' columns are preserved
        tddr_corrected = tddr_corrected_data.copy()
        tddr_corrected['Sample number'] = df['Sample number']
        tddr_corrected['Event'] = df['Event']

        # Bandpass Filtering
        filtered_data = fir_filter(tddr_corrected, order=1000, Wn=[0.01, 0.1], fs=NIRSsamprate)

        # Baseline Correction
        baseline_corrected = baseline_subtraction(filtered_data, events_df)

        # Ensure 'Sample number' and 'Event' columns are preserved
        baseline_corrected['Sample number'] = df['Sample number']
        baseline_corrected['Event'] = df['Event']

        # Reset index if necessary
        baseline_corrected.reset_index(drop=True, inplace=True)

        # Average Channels
        averaged_df = average_channels(baseline_corrected, channels_to_exclude=channels_to_exclude)

        # Create a time axis for plotting
        averaged_df['Time'] = averaged_df['Sample number'] / NIRSsamprate

        # Extract sample numbers for 'S2' and 'S3'
        s2_sample = events_df.loc[events_df['Event'] == 'S2', 'Sample number'].values[0]
        s3_sample = events_df.loc[events_df['Event'] == 'S3', 'Sample number'].values[0]

        # Extract walking data (between S2 and S3)
        walking_data = averaged_df[
            (averaged_df['Sample number'] >= s2_sample) & (averaged_df['Sample number'] <= s3_sample)
            ].reset_index(drop=True)

        # Exclude the first 2 seconds and last 2 seconds
        samples_to_exclude = int(2 * NIRSsamprate)
        if len(walking_data) <= 2 * samples_to_exclude:
            print(f"Not enough data after trimming for subject {subject_id}. Skipping.")
            return None, False

        walking_data_trimmed = walking_data.iloc[samples_to_exclude:-samples_to_exclude].reset_index(drop=True)

        # Rename 'Time (s)' to 'Time' if necessary
        if 'Time (s)' in walking_data_trimmed.columns:
            walking_data_trimmed.rename(columns={'Time (s)': 'Time'}, inplace=True)

        # Remove 'Sample number' column if not needed
        if 'Sample number' in walking_data_trimmed.columns:
            walking_data_trimmed.drop(columns=['Sample number'], inplace=True)

        # Create segments for statistical analysis
        try:
            segments = split_segments(walking_data_trimmed)
        except ValueError as e:
            print(f"Error in split_segments for file {file_path}: {e}")
            return None, False

        # Statistical Analysis
        stats_df = calculate_statistics(segments, file_path, subject_id, condition, timepoint)

        # Generate a unique base filename based on the relative path
        base_filename = os.path.relpath(file_path, dir_path).replace(os.sep, '_')
        base_filename = os.path.splitext(base_filename)[0]

        # Now use base_filename for output files
        stats_output_file = os.path.join(output_folder, base_filename + '_statistics.csv')
        plot_output_file = os.path.join(output_folder, base_filename + '_mean_signals.png')

        # Save the statistical analysis to a CSV file
        stats_df.to_csv(stats_output_file, index=False)
        print(f"Statistical analysis saved to {stats_output_file}")

        # Plot the mean signals
        plot_mean_signals(averaged_df, events_df, NIRSsamprate=NIRSsamprate, output_file=plot_output_file)

    # After processing, check for warnings
    for warning in w:
        if issubclass(warning.category, RuntimeWarning):
            if 'invalid value encountered in divide' in str(warning.message):
                invalid_divide_warning_occurred = True

    if invalid_divide_warning_occurred:
        print(f"Warning: 'invalid value encountered in divide' occurred during processing of {file_path}")

    return stats_df, invalid_divide_warning_occurred  # Return the stats_df and warning flag
