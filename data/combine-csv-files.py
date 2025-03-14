import os
import pandas as pd
import glob

def combine_csv_files(input_directory='.', output_file='combined_output.csv'):
    """
    Combines all CSV files in the specified directory into a single CSV file.
    
    Args:
        input_directory: Directory containing CSV files (default: current directory)
        output_file: Name of the output CSV file
    """
    # Get a list of all CSV files in the directory
    csv_files = glob.glob(os.path.join(input_directory, '*.csv'))
    
    if not csv_files:
        print(f"No CSV files found in {input_directory}")
        return
    
    print(f"Found {len(csv_files)} CSV files to combine")
    
    # Create an empty list to store dataframes
    all_dfs = []
    
    # Read the first file with header
    first_df = pd.read_csv(csv_files[0])
    all_dfs.append(first_df)
    
    # Read the rest of the files without headers
    for file in csv_files[1:]:
        df = pd.read_csv(file, header=0)  # Read with header
        all_dfs.append(df)
    
    # Combine all dataframes
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # Write the combined dataframe to a CSV file
    combined_df.to_csv(output_file, index=False)
    print(f"Successfully combined {len(csv_files)} CSV files into {output_file}")

if __name__ == "__main__":
    combine_csv_files()