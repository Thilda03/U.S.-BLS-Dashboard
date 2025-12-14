import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv # type: ignore

#Load API key
load_dotenv()
API_KEY = os.getenv("BLS_API_KEY")

# Define Series IDs and the data file path
SERIES_IDS = {
   "CES0000000001": "total_nonfarm_employment",
    "LNS14000000": "unemployment_rate",
    "LNS11000000": "labor_force",
    "LNS12000000": "employment",
    "LNS13000000": "unemployment",
    "CES0500000002": "avg_weekly_hours",
    "CES0500000003": "avg_hourly_earnings", 
}
DATA_FILE = "data/bls_data.csv"

# --- 1. Determine Start and End Years for API Call ---
def get_years_to_fetch():
    current_year = datetime.now().year
    
    # Target: At least one year of previous data (plus the current year).
    # Since new data is released monthly, we'll fetch two years (or more) 
    # to ensure all recent data is caught.
    start_year = current_year - 2
    end_year = current_year
    
    # If the CSV exists, find the last year in the file and only fetch from there.
    # However, for simplicity and to account for BLS revisions, it's safer 
    # to refetch the last 2-3 years, or even all data if the file isn't huge.
    # We will stick to the last 2-3 years for robustness.
    
    return str(start_year), str(end_year)

# --- 2. Call the BLS API ---
def fetch_bls_data(start_year, end_year):
    print(f"Fetching data from {start_year} to {end_year}...")
    headers = {'Content-type': 'application/json'}
    data = {
        "seriesid": SERIES_IDS,
        "startyear": start_year,
        "endyear": end_year,
        "registrationkey": API_KEY, # Use the API key
        "catalog": False,
        "calculations": False,
        "annualaverage": False
    }
    
    url = 'https://api.bls.gov/publicAPI/v2/timeseries/data/'
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
    
    return response.json()

# --- 3. Process and Clean the JSON Response ---
def process_data(json_data):
    all_data = []
    
    # The BLS response structure is nested
    for series in json_data['Results']['series']:
        series_id = series['seriesID']
        for item in series['data']:
            year = item['year']
            period = item['period'] # e.g., 'M01', 'M12'
            value = float(item['value'])
            
            # Convert 'year' and 'period' to a proper date
            if period.startswith('M'):
                month = int(period[1:])
                # We use the 1st day of the month for time series
                date_str = f'{year}-{month:02d}-01'
            else:
                # Handle other periods like Q, A, etc. if needed, but M is standard for this data
                continue
                
            all_data.append({
                'Date': date_str,
                'SeriesID': series_id,
                'Value': value
            })

    df = pd.DataFrame(all_data)
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Pivot the table to have dates as index and SeriesIDs as columns
    df_pivot = df.pivot(index='Date', columns='SeriesID', values='Value')
    
    # Optional: Merge with a descriptive CSV if you want column names to be clearer
    # For now, we'll rename the most important ones for the dashboard
    df_pivot = df_pivot.rename(columns={
        'LNS14000000': 'Unemployment Rate',
        'CES0000000001': 'Total Nonfarm Employment (Thousands)'
    })
    
    return df_pivot

# --- 4. Merge and Save the Data ---
def save_data(new_df):
    
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    
    # 1. Load old data if it exists
    if os.path.exists(DATA_FILE):
        old_df = pd.read_csv(DATA_FILE, index_col='Date', parse_dates=True)
        # Convert index of new_df to match old_df's format if necessary
        new_df.index = pd.to_datetime(new_df.index) 
        
        # 2. Merge: The easiest way to handle updates/de-duplication is to 
        # concatenate both, drop duplicates, and sort by date.
        combined_df = pd.concat([old_df, new_df])
        
        # Drop duplicates, keeping the 'last' (newest) record, and sort by date
        combined_df = combined_df[~combined_df.index.duplicated(keep='last')]
        combined_df = combined_df.sort_index()

        print(f"Old rows: {len(old_df)}, New rows: {len(new_df)}, Final rows: {len(combined_df)}")
        
    else:
        combined_df = new_df
        print(f"Created new data file with {len(combined_df)} rows.")

    # Save to CSV
    combined_df.to_csv(DATA_FILE)
    print(f"Data successfully saved to {DATA_FILE}")

# --- Main Execution ---
if __name__ == "__main__":
    if not API_KEY:
        print("ERROR: BLS_API_KEY not found. Please set it as an environment variable or in a .env file.")
    else:
        try:
            start_year, end_year = get_years_to_fetch()
            json_data = fetch_bls_data(start_year, end_year)
            
            # Check for errors in the API response
            if json_data.get('status') == 'REQUEST_NOT_PROCESSED':
                raise Exception(f"BLS API Error: {json_data.get('message', 'Unknown Error')}")
                
            df_new = process_data(json_data)
            save_data(df_new)
            
        except Exception as e:
            print(f"An error occurred: {e}")