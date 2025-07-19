import streamlit as st
import pandas as pd
from openai import OpenAI
from fastmcp import Client
import os
import json
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Load OpenAI API Key
api_key = os.getenv("OPEN_AI_API")

# Initialize OpenAI Client
open_client = OpenAI(
    base_url="https://api.a4f.co/v1",
    api_key=api_key,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "result" not in st.session_state:
    st.session_state.final_verdict = ""

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "provider-6/gpt-4.1"



# Initialize MCP Client (async)
mcp_client = Client("http://127.0.0.1:8000/mcp")

# App Title
st.title("📊 Stock Analyst AI (LLM + MCP)")


def chat_bot(result, stock_name, instrument_key, user_input):
    messages = [
                                  {
                                      "role": "system",
                                      "content": f"""
              You are an experienced stock analyst AI. With the data that is being provided, you have to answer user queries.


              The stock selected by the user is: {stock_name} ({instrument_key})
              and the data is: {json.dumps(result, indent=2)},,
              use this context to answer the user query.
              """
                                  },
                    {"role": "user", "content": user_input}
                ]

    completion = open_client.chat.completions.create(
          model="provider-6/gpt-4.1",
          messages=messages,
      )

    return completion.choices[0].message.content

# --------------------------
# 🔹 Load and display stock list
# --------------------------
@st.cache_data
def load_stocks():
    df = pd.read_csv("stocks_info\\stock_data.csv")
    df = df.dropna(subset=["segment", "name", "instrument_key"])
    df["display"] = df["segment"] + " | " + df["name"] + " | " + df["instrument_key"]
    return df

df = load_stocks()

# User selects a stock (searchable)
selected_display = st.selectbox("🔍 Select a stock", df["display"].tolist())

# Extract selected row details
selected_row = df[df["display"] == selected_display].iloc[0]
segment = selected_row["segment"]
stock_name = selected_row["name"]
instrument_key = selected_row["instrument_key"]

# Text prompt input from user
# user_input = st.text_input("💬 Ask a question about the selected stock:")

# Ask button
if st.button("Analyze This Stock"):
    async def process():
        with st.spinner("Thinking..."):
            async with mcp_client:
                # Construct system prompt with updated multi-tool format
                messages = [
                    {
                        "role": "system",
                        "content": f"""
You are an experienced stock analyst AI. Analyze this stock at your best to answer further user queries. You can use these tools, and you can call one or multiple tools depending on the depth of analysis you want to do,

Tools:
1. get_ohlc(instrument_key:str)
2. fetch_historical_candles(
Parameters:
    -----------
    instrument_key : str
        The instrument key of the stock.
        
    interval : str
        Time interval for candlestick data.
        Accepted values:
        - "minutes" (1 to 300 minutes, available from Jan 2022) 
        - "hours"   (1-5 hours, available from Jan 2022)
        - "days"    (1, available from Jan 2000)
        - "weeks"   (1, available from Jan 2000)
        - "months"  (1, available from Jan 2000)

    count : str
        Interval count used **only** for minutes/hours/days/weeks types.
        - For "minutes": 1 to 300
        - For "hours": 1 to 5
        - For "days", "weeks", "months": "1" only (**But you can use any date range**)

    from_date : str
        Start date of data range. Format: "YYYY-MM-DD"

    to_date : str
        End date of data range. Format: "YYYY-MM-DD"

  example:
)

The stock selected by the user is: {stock_name} ({instrument_key})

👉 Your output must be a **JSON array** of tool call objects. For example:
[
  {{
    "tool": "get_ohlc",
    "input": {{
      "instrument_key": "{instrument_key}"
    }}
  }},
  {{
    "tool": "fetch_historical_candles",
    "input": {{
      "instrument_key": "{instrument_key}",
      "interval": "weeks",
      "count": "1",
      "from_date": "2024-06-14",
      "to_date": "2025-06-14"
    }}
  }},
    {{
    "tool": "fetch_historical_candles",
    "input": {{
      "instrument_key": "{instrument_key}",
      "interval": "months",
      "count": "1",
      "from_date": "2022-06-14",
      "to_date": "2025-06-14"
    }}
  }}

]
Always follow this structure and ensure valid JSON format.
"""
                    },
                    {"role": "user", "content": "Analyze the stock at your best in depth."}
                ]

                # Ask LLM what tools to call
                completion = open_client.chat.completions.create(
                    model="provider-6/gpt-4.1",
                    messages=messages
                )

                reply = completion.choices[0].message.content
                st.subheader("🤖 LLM Reasoning")
                st.code(reply)
                st.write(reply)

                # Parse and execute one or multiple tool calls
                if reply:
                  try:
                      tool_calls = json.loads(reply)
                      result_content = []

                      # Ensure it's a list
                      if not isinstance(tool_calls, list):
                          tool_calls = [tool_calls]

                      for tool_call in tool_calls:
                          tool_name = tool_call.get("tool")
                          tool_input = tool_call.get("input", {})

                          if tool_name:
                              st.info(f"🛠 Executing `{tool_name}`...")
                              result = await mcp_client.call_tool(tool_name, tool_input)

                              if hasattr(result[0], "text"):
                                  raw = result[0].text
                                  st.status('text')
                              elif hasattr(result[0], "body"):
                                  raw = result[0].body.decode()
                                  st.status('body')
                              else:
                                  raw = str(result[0])
                                  st.status('raw')

                              try:
                                  parsed = json.loads(raw)
                                  result_content = parsed
                              except json.JSONDecodeError:
                                  parsed = {"raw": raw}
                                  result_content.append(raw)
                              st.success(f"✅ Tool `{tool_name}` executed:")

                  except Exception as e:
                      st.error("❌ Couldn't parse tool calls or execute them.")
                      st.exception(e)

                  messages = [
                                              {
                                                  "role": "system",
                                                  "content": f"""
                          You are an experienced stock analyst AI. With the data returned by the tools, you have to analyze the stock and provide insights.


                          The stock selected by the user is: {stock_name} ({instrument_key})
                          and the data returned by the tools is:
                          {json.dumps(result_content, indent=2)},
                          Please do the technical analysis, calculate RSI, moving averages, support/resistance and provide a detailed insights based on the data and calculations.
                          """
                                              },
                                {"role": "user", "content": "Analyze the stock at your best in depth, and provide insights based on the data returned by the tools."}
                            ]

                  completion = open_client.chat.completions.create(
                      model="provider-6/gpt-4.1",
                      messages=messages,
                  )

                  final_reply = completion.choices[0].message.content
                  st.session_state["result"] = result_content
                  st.subheader("🤖 LLM Reasoning")
                  st.session_state.messages.append({"role": "assistant", "content": final_reply})
                  # st.write(result_content)

                else:
                    print("⚠️ Reply is empty.")
                    tool_calls = None
          
    # Run async process
    asyncio.run(process())

for message in st.session_state.messages:
  with st.chat_message(message["role"]):
      st.markdown(message["content"])

if st.session_state.get("result"):
    prompt = st.chat_input("Shoot your question here!")

    if prompt:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner():
            reply = chat_bot(st.session_state['result'], stock_name, instrument_key, prompt)
        
        with st.chat_message("assistant"):
            st.markdown(reply)
        # 5. Append assistant message to session state
        st.session_state.messages.append({"role": "assistant", "content": reply})
