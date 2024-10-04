from processing.read_txt import read_txt_file
from processing.filter import fir_filter
from processing.ssc_regression import ssc_regression
from processing.tddr import tddr
from processing.baseline import baseline_subtraction
from processing.create_segments import create_segments
from processing.statistics import calculate_statistics
import pandas as pd
import os

def main():
    # Get the path to the .txt file from the user
    file_path = input('Enter the full path of the .txt file to analyze: ')

    if not os.path.exists(file_path):
        print(f'File {file_path} not found. Please ensure it exists.')
        return

    # Step 1: Read and structure the data
    print("Reading the .txt file...")
    dataMatrix, events_df = read_txt_file(file_path)

    # Ensure the file was read correctly
    if dataMatrix is None or events_df is None:
        print("Error: Could not read the file. Please check the format.")
        return

    # Convert the data matrix into a DataFrame
    df = pd.DataFrame(dataMatrix, columns=[f'CH{i} HbO' if i % 2 == 1 else f'CH{i//2} HbR' for i in range(1, dataMatrix.shape[1] - 1)] + ['Time', 'Event'])

    # Sampling rate (adjust if necessary)
    NIRSsamprate = 50  # in Hz

    # Step 2: Remove initial second of data
    print("Removing the initial second of data...")
    df = df.iloc[NIRSsamprate:]  # Drop the first second based on sampling rate

    # Step 3: Short Channel Correction
    print("Applying short channel regression...")
    # Identify short and long channels based on your configuration
    short_channel_indices = [7, 8]  # Example short channels
    long_channel_indices = [i for i in range(1, 7)]  # Example long channels

    short_channel_cols = [f'CH{ch} HbO' for ch in short_channel_indices] + [f'CH{ch} HbR' for ch in short_channel_indices]
    long_channel_cols = [f'CH{ch} HbO' for ch in long_channel_indices] + [f'CH{ch} HbR' for ch in long_channel_indices]

    short_data = df[short_channel_cols]
    long_data = df[long_channel_cols]

    # Apply short channel regression
    long_corrected = ssc_regression(long_data, short_data)

    # Step 4: TDDR Motion Correction
    print("Applying TDDR motion correction...")
    tddr_corrected = tddr(long_corrected, NIRSsamprate)

    # Step 5: Bandpass Filtering
    print("Applying bandpass filtering...")
    filtered_data = fir_filter(tddr_corrected, order=1000, Wn=[0.01, 0.1], fs=NIRSsamprate)

    # Step 6: Baseline Correction
    print("Applying baseline correction...")
    baseline_corrected = baseline_subtraction(filtered_data, events_df)

    # Step 7: Data Segmentation
    print("Segmenting the data...")
    segments = create_segments(baseline_corrected, events_df)

    # Step 8: Statistical Analysis
    print("Calculating statistics for each segment...")
    stats_df = calculate_statistics(segments, file_path)

    # Save the statistical analysis to a CSV file
    output_file = os.path.splitext(os.path.basename(file_path))[0] + '_statistics.csv'
    stats_df.to_csv(output_file, index=False)
    print(f"Statistical analysis saved to {output_file}")

    # Output completion message
    print("Processing complete. All results have been saved.")

if __name__ == '__main__':
    main()
