import os
import shutil
import glob


def extract_fnirs_files(base_dir, destination_dir):
    """
    Searches for files matching 'Turn_*_LongWalk_ST.txt' and 'Turn_*_LongWalk_DT.txt'
    within the 'Baseline', 'Pre', and 'Post' folders of each subject directory,
    and copies them to the destination_dir without renaming the files, organized in subdirectories.

    Only processes subjects with SubIDs in the 500s and 600s.

    Parameters:
    - base_dir: The root directory to start the search.
    - destination_dir: The directory where the files will be copied.
    """

    # Ensure the destination directory exists
    os.makedirs(destination_dir, exist_ok=True)

    # Search patterns for the desired files
    target_patterns = ['Turn_*_LongWalk_ST.txt', 'Turn_*_LongWalk_DT.txt']

    # Define the session folders to search within each subject directory
    session_folders = ['Baseline', 'Pre', 'Post']  # Added 'Post' to the list

    for subject_id in os.listdir(base_dir):
        subject_path = os.path.join(base_dir, subject_id)

        # Check if the path is a directory and starts with 'OHSU_Turn_'
        if os.path.isdir(subject_path) and subject_id.startswith('OHSU_Turn_'):

            # Extract the numeric part of the SubID to filter for 500s and 600s
            try:
                # Assuming the format is 'OHSU_Turn_<number>'
                subid_number_str = subject_id.split('_')[-1]
                subid_number = int(subid_number_str)
            except (IndexError, ValueError):
                print(f"Unable to extract numeric SubID from '{subject_id}'. Skipping.")
                continue

            # Check if the SubID number is in the 500s or 600s
            if 500 <= subid_number <= 699:
                print(f"Processing subject: {subject_id}")
            else:
                print(f"Skipping subject {subject_id} with SubID number {subid_number}.")
                continue  # Skip subjects not in the 500s or 600s

            # Iterate over each session folder ('Baseline', 'Pre', 'Post')
            for session_folder in session_folders:
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
                                try:
                                    shutil.copy2(file_path, destination_file_path)
                                    print(f"Copied {file_path} to {destination_file_path}")
                                except Exception as e:
                                    print(f"Failed to copy {file_path} to {destination_file_path}: {e}")
                            else:
                                print(f"File {file_path} is not a regular file.")
                else:
                    print(f"Session folder '{session_folder}' not found in {subject_path}. Skipping this session.")
        else:
            print(f"Skipping non-subject folder or improperly named folder: {subject_id}")

    print("Extraction complete.")


def main():
    # Update the base directory to reflect the correct path
    base_dir = '/Volumes/bdlab/Data/R01 Turning/Laboratory & Virtual Assessments'

    # Specify the destination directory
    destination_dir = '/Users/tsujik/Documents/turning_pre_post_fnirs_files'

    # Call the extraction function
    extract_fnirs_files(base_dir, destination_dir)


if __name__ == "__main__":
    main()
