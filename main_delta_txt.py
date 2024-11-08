import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
import glob
from collections import defaultdict

# Import processing modules
from processing.read_txt import read_txt_file
from processing.filter import fir_filter
from processing.ssc_regression import ssc_regression
from processing.tddr import tddr
from processing.baseline import baseline_subtraction
from processing.create_segments import create_segments
from processing.nirs_statistics import calculate_statistics
from processing.average_channels import average_channels
from processing.process_file_delta_txt import process_file_delta_txt
from processing.plot_mean_signals import plot_mean_signals


def main():
    """
    Main function to process NIRS data files and generate analysis results.
    """
    # Define paths and parameters
    data_folder = '/Users/tsujik/Desktop/baseline_turning_nov7'  # Replace with your data folder path
    output_folder = '/Users/tsujik/Desktop/baseline_turning_nov7/delta'  # Replace with your output folder path
    dir_path = '/Users/tsujik/Desktop/baseline_turning_nov7'  # Base directory for relative paths
    NIRSsamprate = 50  # Sampling rate

    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Initialize data structures
    st_data_dict = {}
    st_mean_hbo_dict = {}
    all_snr_data = []
    all_ratio_data = []

    # Define paths for warnings and channels excluded files
    warnings_file = os.path.join(output_folder, 'warnings.txt')
    channels_excluded_file = os.path.join(output_folder, 'channels_excluded.txt')

    # Clear previous warnings and channels excluded files if they exist
    for file_path in [warnings_file, channels_excluded_file]:
        try:
            with open(file_path, 'w') as f:
                pass
        except IOError as e:
            print(f"Warning: Could not clear file {file_path}: {str(e)}")

    try:
        # Get a list of all data files to process (both .txt and .mat files)
        txt_files = glob.glob(os.path.join(data_folder, '**', '*.txt'), recursive=True)
        mat_files = glob.glob(os.path.join(data_folder, '**', '*.mat'), recursive=True)
        data_files = txt_files + mat_files

        if not data_files:
            raise FileNotFoundError(f"No .txt or .mat files found in {data_folder}")

        print(f"Found {len(data_files)} total files")

        # Separate files into ST and DT
        st_files = [f for f in data_files if 'LongWalk_ST' in f]
        dt_files = [f for f in data_files if 'LongWalk_DT' in f]

        print(f"Found {len(st_files)} ST files and {len(dt_files)} DT files")

        # Print the first few files of each type for verification
        print("\nExample ST files:")
        for f in st_files[:3]:
            print(f"- {os.path.basename(f)}")
        print("\nExample DT files:")
        for f in dt_files[:3]:
            print(f"- {os.path.basename(f)}")

        # Process all ST files first
        print("\nProcessing ST files...")
        for file_path in st_files:
            try:
                print(f"\nProcessing: {os.path.basename(file_path)}")
                process_file_delta_txt(
                    file_path=file_path,
                    output_folder=output_folder,
                    dir_path=dir_path,
                    NIRSsamprate=NIRSsamprate,
                    st_data_dict=st_data_dict,
                    st_mean_hbo_dict=st_mean_hbo_dict,
                    warnings_file=warnings_file,
                    channels_excluded_file=channels_excluded_file,
                    all_snr_data=all_snr_data,
                    all_ratio_data=all_ratio_data
                )
            except Exception as e:
                print(f"Error processing ST file {file_path}: {str(e)}")
                with open(warnings_file, 'a') as f:
                    f.write(f"Error processing ST file {file_path}: {str(e)}\n")
                continue

        # Now process all DT files
        print("\nProcessing DT files...")
        for file_path in dt_files:
            try:
                print(f"\nProcessing: {os.path.basename(file_path)}")
                process_file_delta_txt(
                    file_path=file_path,
                    output_folder=output_folder,
                    dir_path=dir_path,
                    NIRSsamprate=NIRSsamprate,
                    st_data_dict=st_data_dict,
                    st_mean_hbo_dict=st_mean_hbo_dict,
                    warnings_file=warnings_file,
                    channels_excluded_file=channels_excluded_file,
                    all_snr_data=all_snr_data,
                    all_ratio_data=all_ratio_data
                )
            except Exception as e:
                print(f"Error processing DT file {file_path}: {str(e)}")
                with open(warnings_file, 'a') as f:
                    f.write(f"Error processing DT file {file_path}: {str(e)}\n")
                continue

        # Save combined data
        save_combined_data(all_snr_data, all_ratio_data, output_folder)

        # Print summary
        print("\nProcessing Summary:")
        print(f"Total files processed: {len(st_files) + len(dt_files)}")
        print(f"ST files processed: {len(st_files)}")
        print(f"DT files processed: {len(dt_files)}")
        print(f"Subjects with ST data: {len(st_mean_hbo_dict)}")
        print(f"Total SNR records: {len(all_snr_data)}")
        print(f"Total ratio records: {len(all_ratio_data)}")

    except Exception as e:
        print(f"An error occurred during processing: {str(e)}")
        with open(warnings_file, 'a') as f:
            f.write(f"Fatal error during processing: {str(e)}\n")
        raise


def save_combined_data(all_snr_data, all_ratio_data, output_folder):
    """
    Save combined SNR and ratio data to CSV files.

    Parameters:
        all_snr_data (list): List of DataFrames containing SNR data
        all_ratio_data (list): List of dictionaries containing ratio data
        output_folder (str): Directory to save the combined files
    """
    try:
        # Save combined SNR data
        if all_snr_data:
            combined_snr = pd.concat(all_snr_data, ignore_index=True)
            snr_output_file = os.path.join(output_folder, 'combined_SNR.csv')
            combined_snr.to_csv(snr_output_file, index=False)
            print(f"Combined SNR data saved to {snr_output_file}")
        else:
            print("No SNR data to save")

        # Save combined ratio data
        if all_ratio_data:
            combined_ratios = pd.DataFrame(all_ratio_data)
            ratio_output_file = os.path.join(output_folder, 'combined_ratios.csv')
            combined_ratios.to_csv(ratio_output_file, index=False)
            print(f"Combined ratio data saved to {ratio_output_file}")
        else:
            print("No ratio data to save")

    except Exception as e:
        print(f"Error saving combined data: {str(e)}")
        raise


if __name__ == '__main__':
    main()