# 📊 Stock Analyst AI Agent

> A full-stack AI-powered stock analysis platform using **LLMs**, **FastMCP**, and **Upstox API**, enabling users to analyze stocks deeply and ask questions backed by real data.

---

## 🚀 Overview

**Stock Analyst AI Agent** is a conversational financial assistant designed for retail traders and investors. It combines LLM reasoning with actual stock data from the **Upstox API**, enabling real-time insights like:

- Live OHLC data fetching
- Historical candlestick analysis
- Multi-tool reasoning via FastMCP
- Custom visualizations Pages (Candlestick, OHLC)
- Real-time Q&A about stocks

---

## 🚀 Features

- 🔍 **Interactive Chatbot** — Ask questions about specific stocks or trends.
- 📊 **Candlestick & OHLC Charts** — Navigate two dynamic pages with rich visualizations.
- 📂 **Historical Data Analysis** — Plots using `stock_data.csv` and embedding from `embedding.csv`.
- **Real Time Stock Information** — Fetches Live quote-level data including prices and volumes using `get_ohlc` tool from the Mcp server.



## 🧠 How It Works

This project uses:

- `streamlit` as a front-end for user interaction
- `FastMCP` to expose backend functions as callable tools
- `OpenAI LLM (GPT4.1)` for multi-tool reasoning
- `Upstox API` to fetch stock and historical market data
- `pandas` for internal stock lookups
- `.env` for managing sensitive API keys securely

The User first chooses the stock then the LLM decides which tools (e.g., `get_ohlc`, `fetch_historical_candles`) to call and then analyzes the returned data to provide a technical analysis-based answer.

---

## 🔧 Tech Stack

| Component      | Technology                 |
|----------------|----------------------------|
| Frontend       | Streamlit                  |
| Backend        | Python, FastMCP            |
| LLM            | OpenAI                     |
| Market Data    | Upstox API                 |
| Auth & Secrets | dotenv (.env)              |

---

## 📂 Directory Structure

```bash
Stock-Analyst-Ai-Agent/
│
├── StockAnalyst.py             # Main Streamlit UI
├── modelcp.py                  # FastMCP server for Upstox tools
├── main.py                     # To get your UPSTOX access token.
├── stocks_info/
│   └── stock_data.csv          # All supported stocks metadata
├── .env                        # Contains API secrets (not to be committed)
├── requirements.txt            # All Python dependencies
├── Pages/
    └── 1_📈_Candlestick.py     # Candlestick visualizations page 
    └── 2_📊_OHLC_Analysis.py   # Ohlc and other visualizations page
├── historic_candles.json
├── ohlc.json  
```
---
# 🔐 Environment Setup
Create a .env file in the root directory with the following keys:

### Upstox Credentials
UPSTOX_API=your_client_id
UPSTOX_SECRET=your_client_secret
ACCESS_TOKEN=your_upstox_access_token

### LLM / OpenAI API
OPEN_AI_API=your_a4f_or_openai_key
#### Important: Never share .env directly. Add .env to your .gitignore.


---
# 🛠️ Installation & Setup
```
# Clone the repository
git clone https://github.com/beingdillig/Stock-Analyst-Ai-Agent.git
cd Stock-Analyst-Ai-Agent

# Install dependencies
pip install -r requirements.txt

# Start the main.py server to get the access token.
uvicorn main:app --reload
```
Paste the access token received by 
logging in to the Upstox by visting the main.py server link, Then.
```
# Start the FastMCP tool server
python server.py

# In another terminal/tab, start the Streamlit app
streamlit run StockAnalyst.py
```
---
# 💬 How to Use
* Select a stock from the dropdown (uses stock_data.csv for searchable stock metadata).

* Click “Analyze This Stock”

* The LLM thinks through which tools to call

* Executes those tools using FastMCP

* Analyzes all returned data

* Presents full technical analysis

* Ask follow-up questions using the input box (e.g., "What’s the RSI of this stock?")

* LLM uses cached data (st.session_state['result'])

* Provides insightful answers with reasoning

---
## 🧮 Logic Flow
```
User -> Streamlit -> LLM (chat.completion) -> Decides tools to use
       -> FastMCP tool server (calls Upstox API)
       -> Receives data
       -> LLM analyzes and returns final output
```

## 📦 Dependencies
* Key libraries:

  *  streamlit

   * fastmcp

    * openai

    * python-dotenv

    * pandas  

    * requests

    * asyncio

---
### 📈 Example Use Case
    User: "Analyze HVAX TECHNOLOGIES LIMITED stock deeply."

    LLM selects:

        get_ohlc for latest price and quote

        fetch_historical_candles for last 6 months weekly trend

    Tools return raw JSON

    LLM calculates:

        RSI, moving averages

        Trend strength

        Resistance/support zones

    LLM responds with a full professional analysis

---
### ⚠️ Warnings

    ❗ Keep your .env secure

    ❗ Don't push your ACCESS_TOKEN or any API key to GitHub

    ❗ Git may convert LF to CRLF on Windows — this is safe and typical on Windows machines


### 🤝 Contribution
```
Feel free to fork and improve! Pull requests welcome.
     Fork -> clone -> create branch
git checkout -b my-new-feature
```

## 🙋 FAQ

Ques: Can I switch LLM providers?

    Ans: Yes, just change the base_url and model in OpenAI() config.

Q: Does this work with live stock prices?

    Ans: Yes, via the Upstox API.

Q: Can I visualize the historic_candles and other stuff?

    Ans: Yes! There are two pages
    
    1. Candlestick
    2. Ohlc
    On these pages you will get everything visualized and the charts and plots are interactive.
