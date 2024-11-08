import os
import pandas as pd

from processing.process_file_bc import process_file

# Initialize a list to store filenames with warnings
warning_files = []

def create_summary_sheets(combined_stats_df, output_folder):
    # Filter for ST condition
    summary_ST = combined_stats_df[combined_stats_df['Condition'] == 'LongWalk_ST']
    # Select relevant columns
    summary_ST = summary_ST[['Subject', 'Timepoint',
                             'Overall grand oxy Mean',
                             'First Half grand oxy Mean',
                             'Second Half grand oxy Mean']]

    # Filter for DT condition
    summary_DT = combined_stats_df[combined_stats_df['Condition'] == 'LongWalk_DT']
    # Select relevant columns
    summary_DT = summary_DT[['Subject', 'Timepoint',
                             'Overall grand oxy Mean',
                             'First Half grand oxy Mean',
                             'Second Half grand oxy Mean']]

    # Save to CSV files
    summary_ST_file = os.path.join(output_folder, 'summary_ST.csv')
    summary_DT_file = os.path.join(output_folder, 'summary_DT.csv')

    summary_ST.to_csv(summary_ST_file, index=False)
    summary_DT.to_csv(summary_DT_file, index=False)

    print(f"Summary ST saved to {summary_ST_file}")
    print(f"Summary DT saved to {summary_DT_file}")

def main():
    # Get the directory containing the .txt files from the user
    dir_path = input('Enter the full path of the directory containing the .txt files: ')

    if not os.path.isdir(dir_path):
        print(f"Directory {dir_path} not found. Please ensure it exists.")
        return

    # Create an output directory within the original directory
    output_folder = os.path.join(dir_path, 'turning_bc_for_all')
    os.makedirs(output_folder, exist_ok=True)
    print(f"Results will be saved to {output_folder}")

    # Collect all .txt files in dir_path and its subdirectories, excluding the output folder
    txt_files = []
    for root, dirs, files in os.walk(dir_path):
        # Exclude the output folder
        dirs[:] = [d for d in dirs if os.path.join(root, d) != output_folder]
        for file in files:
            if file.lower().endswith('.txt'):
                txt_files.append(os.path.join(root, file))

    if not txt_files:
        print(f"No .txt files found in directory {dir_path} or its subdirectories.")
        return

    # Initialize list to collect stats DataFrames
    all_stats = []

    for file_path in txt_files:
        stats_df, warning_occurred = process_file(file_path, output_folder, dir_path)
        if stats_df is not None:
            all_stats.append(stats_df)
            if warning_occurred:
                warning_files.append(file_path)

    # After processing all files, combine the stats DataFrames
    if all_stats:
        combined_stats_df = pd.concat(all_stats, ignore_index=True)

        # Create summary sheets
        create_summary_sheets(combined_stats_df, output_folder)
    else:
        print("No data to combine.")
        return

    # After processing all files, write the summary of warnings if any
    if warning_files:
        summary_file = os.path.join(output_folder, 'warning_summary.txt')
        with open(summary_file, 'w') as f:
            f.write('The following files had "invalid value encountered in divide" warnings during processing:\n')
            for file in warning_files:
                f.write(f"{file}\n")
        print(f"Summary of warnings saved to {summary_file}")
    else:
        print("No 'invalid value encountered in divide' warnings were encountered during processing.")

    print("Batch processing complete. All results have been saved.")

if __name__ == '__main__':
    main()
