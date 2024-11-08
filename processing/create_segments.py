import pandas as pd

def create_segments(df: pd.DataFrame, events: pd.DataFrame) -> dict:
    """
    Split the trial into segments based on event markers.

    Parameters:
    - df: DataFrame of the processed fNIRS data
    - events: DataFrame of event markers

    Returns:
    - Dictionary with keys as segment names and values as DataFrames for each segment
    """
    segments = {}
    events = events[events['Event'].notnull()]

    if len(events) != 3:
        raise ValueError("Expected exactly 3 event markers for segmentation.")

    start_quiet, start_walk, end_walk = events['Sample number']

    # Define segments based on the event indices
    segments['Quiet Stance'] = df.iloc[start_quiet:start_walk]
    segments['Walking'] = df.iloc[start_walk:end_walk]
    segments['Early Walking'] = df.iloc[start_walk:(start_walk + (end_walk - start_walk) // 2)]
    segments['Late Walking'] = df.iloc[(start_walk + (end_walk - start_walk) // 2):end_walk]

    return segments
