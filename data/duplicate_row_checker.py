import pandas as pd

def check_duplicates(csv_file):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(csv_file)

    # Check for duplicate rows
    duplicates = df[df.duplicated(keep=False)]

    if not duplicates.empty:
        print("Duplicate rows found:")
        print(duplicates)
        #print("\nCount of duplicate rows:")
        #print(duplicates.value_counts())
    else:
        print("No duplicate rows found.")

if __name__ == "__main__":
    csv_file_path = 'simplyhired_data_scientist.csv'
    
    # Check for duplicates
    check_duplicates(csv_file_path)
