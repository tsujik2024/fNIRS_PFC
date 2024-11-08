import pandas as pd
import numpy as np


def read_txt_file(file_path: str) -> dict:
    """
    Parse a .txt export of fNIRS data generated in Oxysoft.

    :param file_path: path to raw data file
    :return: dictionary of metadata and raw fnirs data
    """
    lines = None
    with open(file_path, 'r') as f:
        # Split the .txt file into lines
        lines = f.read().split('\n')

    if lines is None:
        raise AttributeError(f"Could not open {file_path}.")

    # Split each line into columns
    rows = [[i for i in j.split('\t')] for j in lines]

    metadata = _read_metadata(rows)
    df = _read_data(rows)

    # Add info to metadata
    metadata['Export file'] = file_path

    return {'metadata': metadata, 'data': df}


def _read_metadata(rows: list) -> dict:
    # Copy to avoid accidental mutation to original list
    rows_copy = [i for i in rows]
    metadata = dict()
    for i in range(7):
        row = rows_copy[i]
        if '' in row:
            pass
        elif 'OxySoft export of:' in row:
            metadata['Original file'] = row[1]
        else:
            # Remove trailing ":" before setting as key
            metadata[row[0].split(':')[0]] = row[1]

    return metadata


def _read_data(rows: list) -> pd.DataFrame:
    # Copy to avoid accidental mutation to original list
    rows_copy = [i for i in rows]

    # Get column labels to use for DataFrame, also get sample rate
    start = None
    end = None
    sample_rate = None

    # Find the start/end indexes of the columns labels
    for idx, row in enumerate(rows_copy):
        if "Datafile sample rate:" in row:
            sample_rate = int(float(row[1]))
        elif "(Sample number)" in row:
            start = idx
        elif "(Event)" in row:
            end = idx
            break

    if start is not None and end is not None and sample_rate is not None:
        col_labels = rows_copy[start:(end + 1)]
        col_labels = [i[1] for i in col_labels]
    else:
        raise ValueError(f"""Could not find start, end, or sample rate in the
        .txt file. Start: {start}, end: {end}, sample_rate: {sample_rate}""")

    # Remove extra characters from column labels
    for idx, label in enumerate(col_labels):
        if "O2Hb" in label or "HHb" in label:
            new_label = label.split('(')[0].rstrip()
            col_labels[idx] = new_label
        elif "(Sample number)" in label or "(Event)" in label:
            new_label = label.split('(')[1].split(')')[0]
            col_labels[idx] = new_label
        else:
            raise KeyError(f"Unexpected value found in column labels: {label}")

    # Create DataFrame
    data = rows_copy[(end + 4):-1]  # Last line is empty, ignore it
    for idx, row in enumerate(data):
        # The rows (lists) that contain event markers have an empty string as
        # their last element. Pop this element to keep list length consistent.
        if len(row) == len(col_labels) + 1:
            data[idx].pop()
        elif len(row) == len(col_labels):
            pass
        else:
            raise ValueError(f"""Unexpected number of items in row {idx}.
            Expected {len(col_labels)}, found {len(row)}.""")

    df = pd.DataFrame(data=data, columns=col_labels)

    # Drop initial 1 second of recording
    df.drop(df.index[range(sample_rate)], inplace=True)
    # Cast columns to most logical dtype
    df = df.apply(pd.to_numeric, errors='ignore')
    # Replace '' with np.nan in the 'Event' columns
    df.loc[df['Event'] == '', 'Event'] = np.nan

    return df