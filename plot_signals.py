import pandas as pd
import matplotlib.pyplot as plt
import os

def plot_mean_signals(df, events_df, NIRSsamprate=50, output_file=None):
    """
    Plots the overall mean of HbO and HbR signals over time and marks event markers.

    Parameters:
    - df: DataFrame containing HbO and HbR signals with 'Sample number'.
    - events_df: DataFrame containing event markers with 'Sample number' and 'Event'.
    - NIRSsamprate: Sampling rate in Hz (default is 50 Hz).
    - output_file: Optional. If provided, saves the plot to the specified file.
    """

    # Identify HbO and HbR columns
    hbo_cols = [col for col in df.columns if 'HbO' in col]
    hbr_cols = [col for col in df.columns if 'HbR' in col]

    # Compute the mean HbO and HbR signals over all channels
    df['Mean HbO'] = df[hbo_cols].mean(axis=1)
    df['Mean HbR'] = df[hbr_cols].mean(axis=1)

    # Create a time axis based on the 'Sample number' and sampling rate
    df['Time (s)'] = df['Sample number'] / NIRSsamprate

    # Plot the mean HbO and HbR signals
    plt.figure(figsize=(12, 6))
    plt.plot(df['Time (s)'], df['Mean HbO'], label='Mean HbO', color='red')
    plt.plot(df['Time (s)'], df['Mean HbR'], label='Mean HbR', color='blue')

    # Mark event markers with vertical lines
    for idx, event in events_df.iterrows():
        event_time = event['Sample number'] / NIRSsamprate
        plt.axvline(x=event_time, color='green', linestyle='--', alpha=0.7)
        plt.text(event_time, df['Mean HbO'].max(), str(event['Event']), rotation=90,
                 verticalalignment='bottom', color='green')

    # Customize the plot
    plt.title('Mean HbO and HbR Signals Over Time')
    plt.xlabel('Time (s)')
    plt.ylabel('Signal Amplitude')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    # Save or show the plot
    if output_file:
        plt.savefig(output_file)
        print(f"Plot saved to {output_file}")
    else:
        plt.show()

def main():
    # Assuming you have the processed data saved to a CSV file
    # Modify the file paths as needed
    data_file = input('Enter the full path of the processed data CSV file: ')
    events_file = input('Enter the full path of the events CSV file: ')

    # Read the processed data
    df = pd.read_csv(data_file)
    events_df = pd.read_csv(events_file)

    # Ensure 'Sample number' is numeric
    df['Sample number'] = pd.to_numeric(df['Sample number'], errors='coerce')
    events_df['Sample number'] = pd.to_numeric(events_df['Sample number'], errors='coerce')

    # Remove any rows with NaN 'Sample number'
    df = df.dropna(subset=['Sample number'])
    events_df = events_df.dropna(subset=['Sample number'])

    # Convert 'Sample number' to integers
    df['Sample number'] = df['Sample number'].astype(int)
    events_df['Sample number'] = events_df['Sample number'].astype(int)

    # Plot the mean signals
    plot_mean_signals(df, events_df)

if __name__ == '__main__':
    main()
