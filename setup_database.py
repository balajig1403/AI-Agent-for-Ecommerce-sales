import pandas as pd
import sqlite3
import os

# --- Configuration ---
DATABASE_FILE = "ecommerce_data.db"
CSV_FILES = [
    'Product-Level Ad Sales and Metrics (mapped).csv',
    'Product-Level Eligibility Table (mapped).csv',
    'Product-Level Total Sales and Metrics (mapped).csv'
]
# --- End of Configuration ---

# Function to create a clean table name from a filename
def clean_table_name(filename):
    # Removes the extension and replaces special characters
    return os.path.splitext(filename)[0].replace('-', '_').replace(' ', '_').replace('(mapped)', '').strip('_')

# Create a connection to the SQLite database
conn = sqlite3.connect(DATABASE_FILE)
print(f"Opened database connection to '{DATABASE_FILE}'.")

# Loop through the CSV files and load them into the database
# Loop through the CSV files and load them into the database
for file in CSV_FILES:
    if os.path.exists(file):
        table_name = clean_table_name(file)
        try:
            # Read the CSV with all our fixes for encoding and parsing errors
            df = pd.read_csv(
                file, 
                encoding='latin-1', 
                engine='python', 
                on_bad_lines='skip'
            )
            
            # Clean up column names, including removing NUL characters
            df.columns = df.columns.str.replace(' ', '_').str.replace('(', '').str.replace(')', '').str.replace('\x00', '')
            
            # Load the DataFrame into an SQL table
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            print(f"✅ Successfully loaded '{file}' into table '{table_name}'.")

        except Exception as e:
            # Catch any other unexpected errors during loading
            print(f"❌ An unexpected error occurred with {file}: {e}")
    else:
        # Warning if a file from the list is not found
        print(f"⚠️ Warning: File not found - '{file}'")

# Close the database connection
conn.close()
print(f"\nProcess complete. Database connection closed.")