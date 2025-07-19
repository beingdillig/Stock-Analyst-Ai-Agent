# server.py
from mcp.server.fastmcp import FastMCP
import pandas as pd
import os
import requests
import json
from dotenv import load_dotenv
from expose_files import container


load_dotenv()
# Create an MCP server
mcp = FastMCP("Demo")


CLIENT_ID = os.getenv('UPSTOX_API')
CLIENT_SECRET = os.getenv('UPSTOX_SECRET') 
access_token = os.getenv('ACCESS_TOKEN')

print(f"Access Token: {access_token}")

data = pd.read_csv("C:/Users/dwiwe/Documents/Html & CSS/Stock analyst MCP server/stocks_info/stock_data.csv")
# Add an addition tool
@mcp.tool()
def fetch_stock(stock:str):
    """
    Fetch stock names based on a partial or approximate match with user input.
    This function accepts a partial or lowercase stock name and searches the 'data' DataFrame 
    for case-insensitive substring matches in the 'name' column. It is useful when the user 
    does not know the exact full name of the stock. The function returns a dictionary containing 
    the list of matching stock names. If no matches are found, an appropriate error message is returned.

    Parameters:
    -----------
    stock : str
        A partial or complete string representing the stock name to search for.

    Returns:
    --------
    dict
        If a match is found:
            {
                'stock': <Series of matching stock names>
            }
        If no match is found:
            {
                'error': 'Please enter the correct stock name from any exchange'
            }

    Example:
    --------
    fetch_stock("hvax")  
    -> May return: {'stock': ['HVAX TECHNOLOGIES LIMITED']}
    """
    equity = data[data['name'].str.lower().str.contains(stock)]
    if not equity.empty:
        return {'stock': equity['name']}
    else:
        return {'error':'Please enter the correct stock name from any exchange'}
    
@mcp.tool()
def get_ohlc(instrument_key):
    """
    Fetches OHLC (Open, High, Low, Close) and quote data for a given instrument key.

    Parameters:
    -----------
    instrument_key : str
        The instrument key (e.g., 'NSE_EQ|INE848E01016').

    Returns:
    --------
    dict or str
        JSON data with quote details, or an error message if fetch fails.
    """
    print("ohlc called")

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }

    params = {
        "instrument_key": instrument_key
    }

    try:
        response = requests.get(
            "https://api.upstox.com/v2/market-quote/quotes",
            headers=headers,
            params=params
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        if response.status_code == 200:
            with open("ohlc.json", "w") as f:
                json.dump(response.json(), f, indent=4)
            return response.json()
        else:
            return f"❌ Error {response.status_code}: {response.text}"
    except Exception as e:
        return f"⚠️ Exception occurred: {str(e)}"
        
@mcp.tool()
def fetch_historical_candles(
    instrument_key: str,
    interval: str,
    count: str,
    from_date: str,
    to_date: str,
):
    """
    Fetch historical candlestick data for a given stock using the Upstox API.
    Claude please the data that is returned to you visualize it for the user to get clear insights and as it a candle data so choose a plot accordingly.
    and let the user know everything, answer like a stock analyst.
    Dont write the raw data in your code please use the file returned, as an import please as the code becomes so big.

    Parameters:
    -----------
    instrument_key : str
        The instrument key of the stock.
        
    interval : str
        Time interval for candlestick data.
        Accepted values:
        - "minutes" (1 to 300 minutes, available from Jan 2022) 
        - "hours"   (1-5 hours, available from Jan 2022)
        - "days"    (available from Jan 2000)
        - "weeks"   (available from Jan 2000)
        - "months"  (available from Jan 2000)

    count : str
        Interval count used **only** for minutes/hours/days/weeks types.
        - For "minutes": 1 to 300
        - For "hours": 1 to 5
        - For "days", "weeks", "months": "1" only

    from_date : str
        Start date of data range. Format: "YYYY-MM-DD"

    to_date : str
        End date of data range. Format: "YYYY-MM-DD"

    Returns:
    --------
    dict or str:
        If successful, returns the response JSON with historical candle data.
        If error or stock not found, returns a string with the error message.
    """

    # Build the request URL based on interval and count
    if interval in ['minutes', 'hours', 'days', 'weeks','months']:
        url = f"https://api.upstox.com/v3/historical-candle/{instrument_key}/{interval}/{count}/{to_date}/{from_date}"
    else:
        url = f"https://api.upstox.com/v3/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}"

    # Set headers with auth token
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }

    # Make the request
    print('hitting url')
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    if response.status_code == 200:
        with open("historic_candles.json", "w") as f:
            json.dump(response.json(), f, indent=4)

        return response.json()
    else:
        return f"❌ Error {response.status_code}: {response.text}"
    

if __name__ == "__main__":
    # Start the server with HTTP transport on 127.0.0.1:8000 (default path /mcp)
    mcp.run(transport="streamable-http")