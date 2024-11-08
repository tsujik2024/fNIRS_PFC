import os
import shutil
import glob

def extract_fnirs_files(base_dir, destination_dir):
    """
    Searches for files matching 'Turn_*_LongWalk_ST.txt' and 'Turn_*_LongWalk_DT.txt'
    within the 'Baseline' and 'Pre' folders of each subject directory, and copies them
    to the destination_dir without renaming the files, organized in subdirectories.

    Parameters:
    - base_dir: The root directory to start the search.
    - destination_dir: The directory where the files will be copied.
    """

    # Ensure the destination directory exists
    os.makedirs(destination_dir, exist_ok=True)

    # Search patterns for the desired files
    target_patterns = ['Turn_*_LongWalk_ST.txt', 'Turn_*_LongWalk_DT.txt']

    for subject_id in os.listdir(base_dir):
        subject_path = os.path.join(base_dir, subject_id)
        if os.path.isdir(subject_path) and subject_id.startswith('OHSU_Turn_'):
            # Only look into 'Baseline' and 'Pre' folders under subject_path
            for session_folder in ['Baseline', 'Pre']:
                session_path = os.path.join(subject_path, session_folder)
                if os.path.isdir(session_path):
                    # Recursively search for target files within session_path
                    for pattern in target_patterns:
                        search_pattern = os.path.join(session_path, '**', pattern)
                        matches = glob.glob(search_pattern, recursive=True)
                        for file_path in matches:
                            if os.path.isfile(file_path):
                                # Extract the base filename
                                filename = os.path.basename(file_path)
                                # Construct the destination path with subdirectories
                                subject_dest_dir = os.path.join(destination_dir, subject_id, session_folder)
                                os.makedirs(subject_dest_dir, exist_ok=True)
                                destination_file_path = os.path.join(subject_dest_dir, filename)
                                # Copy the file without renaming
                                shutil.copy2(file_path, destination_file_path)
                                print(f"Copied {file_path} to {destination_file_path}")
                            else:
                                print(f"File {file_path} is not a regular file")
                else:
                    print(f"Session folder '{session_folder}' not found in {subject_path}")
        else:
            print(f"Skipping non-subject folder: {subject_id}")

    print("Extraction complete.")

def main():
    # Update the base directory to reflect the correct path
    base_dir = '/Volumes/bdlab/Data/R01 Turning/Laboratory & Virtual Assessments'

    # Ensure you are connected to your institution's VPN and the network drive is mounted

    # Specify the destination directory
    destination_dir = '/Users/tsujik/Documents/turning_pre_post_fnirs_files'

    extract_fnirs_files(base_dir, destination_dir)

if __name__ == "__main__":
    main()
