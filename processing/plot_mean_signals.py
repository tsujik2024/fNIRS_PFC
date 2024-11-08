import pandas as pd
import matplotlib.pyplot as plt

def plot_mean_signals(averaged_df, events_df, NIRSsamprate=50, output_file=None):
    """
    Plots the overall mean HbO and HbR signals over time and marks event markers.

    Parameters:
    - averaged_df: DataFrame containing processed fNIRS data with 'Sample number'.
    - events_df: DataFrame containing event markers with 'Sample number' and 'Event'.
    - NIRSsamprate: Sampling rate in Hz (default is 50 Hz).
    - output_file: Optional. If provided, saves the plot to the specified file.
    """

    # Ensure 'Time (s)' is calculated correctly
    if 'Time (s)' not in averaged_df.columns:
        if 'Sample number' in averaged_df.columns:
            averaged_df['Time (s)'] = averaged_df['Sample number'] / NIRSsamprate
        else:
            averaged_df['Time (s)'] = averaged_df.index / NIRSsamprate

    # Create a 'Second' column by flooring 'Time (s)'
    averaged_df['Second'] = averaged_df['Time (s)'].astype(int)

    # Group by 'Second' and compute the mean of 'grand oxy' and 'grand deoxy'
    mean_df = averaged_df.groupby('Second')[['grand oxy', 'grand deoxy']].mean().reset_index()

    # Plot the overall mean HbO and HbR signals per second
    plt.figure(figsize=(12, 6))
    plt.plot(mean_df['Second'], mean_df['grand oxy'], label='Mean HbO', color='red')
    plt.plot(mean_df['Second'], mean_df['grand deoxy'], label='Mean HbR', color='blue')

    # Determine the maximum and minimum signal values for annotation placement
    max_signal = max(mean_df['grand oxy'].max(), mean_df['grand deoxy'].max())
    min_signal = min(mean_df['grand oxy'].min(), mean_df['grand deoxy'].min())

    # Mark event markers with vertical lines
    for _, event in events_df.iterrows():
        if 'Sample number' in event and not pd.isnull(event['Sample number']):
            event_time = event['Sample number'] / NIRSsamprate
        else:
            event_time = _ / NIRSsamprate  # Use index if 'Sample number' not available
        event_second = int(event_time)
        plt.axvline(x=event_second, color='green', linestyle='--', alpha=0.7)
        plt.text(event_second, max_signal, str(event['Event']), rotation=90,
                 verticalalignment='bottom', color='green')

    # Customize the plot
    plt.title('Overall Mean HbO and HbR Signals Over Time')
    plt.xlabel('Time (s)')
    plt.ylabel('Signal Amplitude')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    # Save or show the plot
    if output_file:
        plt.savefig(output_file)
        plt.close()
        print(f"Plot saved to {output_file}")
    else:
        plt.show()
