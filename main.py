from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, HTMLResponse
import requests
import webbrowser
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Your Upstox app credentials (from developer console)
CLIENT_ID = os.getenv('UPSTOX_API')
CLIENT_SECRET = os.getenv('UPSTOX_SECRET') 
access_token = os.getenv('ACCESS_TOKEN')

REDIRECT_URI = "http://localhost:8000/callback"

@app.get("/")
def login():
    auth_url = (
        f"https://api.upstox.com/v2/login/authorization/dialog"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
    )
    return RedirectResponse(auth_url)

@app.get("/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    
    if not code:
        return HTMLResponse("<h3>Authorization failed or denied.</h3>")

    print(f"[+] Authorization Code: {code}")

    # Exchange auth code for token
    token_url = "https://api.upstox.com/v2/login/authorization/token"
    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": code
    }

    response = requests.post(token_url, data=token_data)
    tokens = response.json()

    print("\n[+] Token Response:")
    print(tokens)

    access_token = tokens.get("access_token")
    if not access_token:
        return HTMLResponse("<h3>Token exchange failed.</h3>")

    # Get live quote for a sample stock (e.g., NHPC)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    params = {
        "instrument_key": "NSE_EQ|INE848E01016"  # Replace with your desired instrument key
    }

    ltp_url = "https://api.upstox.com/v2/market/quote/ltp"
    quote_response = requests.get(ltp_url, headers=headers, params=params)
    quotes_data = quote_response.json()

    print("\n[+] LTP Data:")
    print(quotes_data)

    # Return to browser
    return HTMLResponse(
        f"<h3>Access token fetched!</h3><pre>{quotes_data}</pre>"
    )

if __name__ == "__main__":
    import uvicorn
    webbrowser.open("http://localhost:8000/")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
