import os
import shutil
import glob

def extract_fnirs_files(base_dir, destination_dir):
    """
    Searches for files matching 'Turn_*_LongWalk_ST.txt' and 'Turn_*_LongWalk_DT.txt'
    within the base_dir and copies them to the destination_dir, prefixed with the subject ID.

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
            # Recursively search for target files within the subject's directory
            for pattern in target_patterns:
                search_pattern = os.path.join(subject_path, '**', pattern)
                matches = glob.glob(search_pattern, recursive=True)
                for file_path in matches:
                    if os.path.isfile(file_path):
                        # Extract the base filename
                        filename = os.path.basename(file_path)
                        # Construct a unique filename to avoid overwriting
                        destination_file = f"{subject_id}_{filename}"
                        destination_path = os.path.join(destination_dir, destination_file)
                        shutil.copy2(file_path, destination_path)
                        print(f"Copied {file_path} to {destination_path}")
                    else:
                        print(f"File {file_path} is not a regular file")
        else:
            print(f"Skipping non-subject folder: {subject_id}")

    print("Extraction complete.")

def main():
    # Update the base directory to reflect the correct path
    base_dir = '/Volumes/bdlab/Data/RO1 Turning/Laboratory & Virtual Assessments'

    # Ensure you are connected to your institution's VPN and the network drive is mounted

    # Specify the destination directory
    destination_dir = os.path.join(base_dir, 'consolidated_fnirs_files')

    extract_fnirs_files(base_dir, destination_dir)

if __name__ == "__main__":
    main()
