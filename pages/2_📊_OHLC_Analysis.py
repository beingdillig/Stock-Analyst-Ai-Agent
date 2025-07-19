import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
import numpy as np

# Configure page
st.set_page_config(
    page_title="📈 Stock Market Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .bullish { color: #28a745; }
    .bearish { color: #dc3545; }
    .neutral { color: #6c757d; }
</style>
""", unsafe_allow_html=True)

# Title and header
st.markdown('<div class="main-header"><h1>📈 Stock Market Data Analyzer</h1><p>Interactive visualization for real-time stock market data</p></div>', unsafe_allow_html=True)

# Sidebar for data input
st.sidebar.header("📊 Data Input")
st.sidebar.info("📁 Reading from: ohlc.json")

def parse_stock_data(json_data):
    """Parse JSON stock data into a structured format"""
    try:
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data
        
        if data.get("status") != "success":
            st.error("❌ Invalid data format: Status is not success")
            return None
        
        stock_data = data.get("data", {})
        parsed_stocks = []
        
        for instrument_key, stock_info in stock_data.items():
            ohlc = stock_info.get("ohlc", {})
            
            parsed_stock = {
                "instrument_key": instrument_key,
                "symbol": stock_info.get("symbol", "N/A"),
                "last_price": stock_info.get("last_price", 0),
                "open": ohlc.get("open", 0),
                "high": ohlc.get("high", 0),
                "low": ohlc.get("low", 0),
                "close": ohlc.get("close", 0),
                "volume": stock_info.get("volume", 0),
                "average_price": stock_info.get("average_price", 0),
                "net_change": stock_info.get("net_change", 0),
                "net_change_percent": (stock_info.get("net_change", 0) / stock_info.get("last_price", 1)) * 100 if stock_info.get("last_price", 0) != 0 else 0,
                "upper_circuit": stock_info.get("upper_circuit_limit", 0),
                "lower_circuit": stock_info.get("lower_circuit_limit", 0),
                "timestamp": stock_info.get("timestamp", ""),
                "total_buy_quantity": stock_info.get("total_buy_quantity", 0),
                "total_sell_quantity": stock_info.get("total_sell_quantity", 0)
            }
            parsed_stocks.append(parsed_stock)
        
        return parsed_stocks
    except Exception as e:
        st.error(f"❌ Error parsing JSON data: {str(e)}")
        return None

# Read data from ohlc.json file
json_data = None
try:
    with open('ohlc.json', 'r') as file:
        json_data = json.load(file)
    st.sidebar.success("✅ ohlc.json loaded successfully")
except FileNotFoundError:
    st.sidebar.error("❌ ohlc.json file not found")
    st.error("📁 Please ensure 'ohlc.json' file exists in the same directory as this script")
except json.JSONDecodeError:
    st.sidebar.error("❌ Invalid JSON format in ohlc.json")
except Exception as e:
    st.sidebar.error(f"❌ Error reading ohlc.json: {str(e)}")

# Process data if available
if json_data:
    stocks = parse_stock_data(json_data)
    
    if stocks:
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(stocks)
        
        # Main dashboard
        st.header("📋 Stock Overview")
        
        # Select stock for detailed analysis
        selected_symbol = st.selectbox("Select a stock for detailed analysis:", df['symbol'].unique())
        selected_stock = df[df['symbol'] == selected_symbol].iloc[0]
        
        # Key metrics in columns
        col1, col2, col3, col4, col5 = st.columns(5)
        
        # Determine trend
        trend_class = "bullish" if selected_stock['net_change'] > 0 else "bearish" if selected_stock['net_change'] < 0 else "neutral"
        trend_icon = "📈" if selected_stock['net_change'] > 0 else "📉" if selected_stock['net_change'] < 0 else "➡️"
        
        with col1:
            st.metric(
                label="💰 Last Price",
                value=f"₹{selected_stock['last_price']:.2f}",
                delta=f"{selected_stock['net_change']:.2f} ({selected_stock['net_change_percent']:.2f}%)"
            )
        
        with col2:
            st.metric(
                label="📊 Volume",
                value=f"{selected_stock['volume']:,}"
            )
        
        with col3:
            st.metric(
                label="🎯 Day High",
                value=f"₹{selected_stock['high']:.2f}"
            )
        
        with col4:
            st.metric(
                label="🎯 Day Low",
                value=f"₹{selected_stock['low']:.2f}"
            )
        
        with col5:
            st.metric(
                label="📈 Average Price",
                value=f"₹{selected_stock['average_price']:.2f}"
            )
        
        # Create visualizations
        st.header("📊 Interactive Visualizations")
        
        # Create tabs for different visualizations
        tab1, tab2, tab3, tab4 = st.tabs(["🕯️ OHLC Candlestick", "📊 Price Analysis", "📈 Market Depth", "🎯 Circuit Limits"])
        
        with tab1:
            st.subheader(f"🕯️ OHLC Candlestick Chart - {selected_stock['symbol']}")
            
            # Create candlestick chart
            fig_candle = go.Figure(data=go.Candlestick(
                x=[selected_stock['symbol']],
                open=[selected_stock['open']],
                high=[selected_stock['high']],
                low=[selected_stock['low']],
                close=[selected_stock['close']],
                name=selected_stock['symbol']
            ))
            
            fig_candle.update_layout(
                title=f"{selected_stock['symbol']} - Current Session OHLC",
                xaxis_title="Stock",
                yaxis_title="Price (₹)",
                template="plotly_white",
                height=500
            )
            
            st.plotly_chart(fig_candle, use_container_width=True)
        
        with tab2:
            st.subheader("📊 Price Analysis Dashboard")
            
            # Create subplots for comprehensive analysis
            fig_analysis = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Price Range Analysis', 'Volume vs Price', 'Circuit Limit Analysis', 'Buy vs Sell Pressure'),
                specs=[[{"type": "bar"}, {"type": "scatter"}],
                       [{"type": "bar"}, {"type": "bar"}]]
            )
            
            # Price Range Analysis
            price_data = ['Open', 'High', 'Low', 'Close', 'Last Price']
            price_values = [selected_stock['open'], selected_stock['high'], 
                          selected_stock['low'], selected_stock['close'], selected_stock['last_price']]
            colors = ['blue', 'green', 'red', 'orange', 'purple']
            
            fig_analysis.add_trace(
                go.Bar(x=price_data, y=price_values, name="Prices", marker_color=colors),
                row=1, col=1
            )
            
            # Volume vs Price scatter
            fig_analysis.add_trace(
                go.Scatter(x=[selected_stock['volume']], y=[selected_stock['last_price']], 
                          mode='markers', marker=dict(size=20, color='red'),
                          name="Volume vs Price"),
                row=1, col=2
            )
            
            # Circuit Limits
            circuit_data = ['Lower Circuit', 'Current Price', 'Upper Circuit']
            circuit_values = [selected_stock['lower_circuit'], selected_stock['last_price'], selected_stock['upper_circuit']]
            circuit_colors = ['red', 'blue', 'green']
            
            fig_analysis.add_trace(
                go.Bar(x=circuit_data, y=circuit_values, name="Circuit Limits", marker_color=circuit_colors),
                row=2, col=1
            )
            
            # Buy vs Sell Pressure
            if selected_stock['total_buy_quantity'] > 0 or selected_stock['total_sell_quantity'] > 0:
                pressure_data = ['Buy Quantity', 'Sell Quantity']
                pressure_values = [selected_stock['total_buy_quantity'], selected_stock['total_sell_quantity']]
                pressure_colors = ['green', 'red']
                
                fig_analysis.add_trace(
                    go.Bar(x=pressure_data, y=pressure_values, name="Market Pressure", marker_color=pressure_colors),
                    row=2, col=2
                )
            
            fig_analysis.update_layout(height=700, showlegend=False, template="plotly_white")
            st.plotly_chart(fig_analysis, use_container_width=True)
        
        with tab3:
            st.subheader("📈 Market Depth & Trading Activity")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Volume Analysis
                fig_volume = go.Figure(data=go.Bar(
                    x=['Volume'],
                    y=[selected_stock['volume']],
                    marker_color='lightblue',
                    text=[f"{selected_stock['volume']:,}"],
                    textposition='auto'
                ))
                fig_volume.update_layout(
                    title="📊 Trading Volume",
                    yaxis_title="Volume",
                    template="plotly_white",
                    height=400
                )
                st.plotly_chart(fig_volume, use_container_width=True)
            
            with col2:
                # Price Performance Gauge
                price_range = selected_stock['high'] - selected_stock['low']
                current_position = (selected_stock['last_price'] - selected_stock['low']) / price_range * 100 if price_range > 0 else 50
                
                fig_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = current_position,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Price Position in Day's Range (%)"},
                    delta = {'reference': 50},
                    gauge = {
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 25], 'color': "lightgray"},
                            {'range': [25, 75], 'color': "gray"},
                            {'range': [75, 100], 'color': "lightgreen"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 90
                        }
                    }
                ))
                fig_gauge.update_layout(height=400)
                st.plotly_chart(fig_gauge, use_container_width=True)
        
        with tab4:
            st.subheader("🎯 Circuit Limits & Risk Analysis")
            
            # Circuit limit visualization
            circuit_fig = go.Figure()
            
            # Add horizontal lines for circuit limits
            circuit_fig.add_hline(y=selected_stock['upper_circuit'], line_dash="dash", 
                                 line_color="green", annotation_text="Upper Circuit")
            circuit_fig.add_hline(y=selected_stock['lower_circuit'], line_dash="dash", 
                                 line_color="red", annotation_text="Lower Circuit")
            circuit_fig.add_hline(y=selected_stock['last_price'], line_dash="solid", 
                                 line_color="blue", annotation_text="Current Price")
            
            # Add OHLC data as scatter points
            circuit_fig.add_trace(go.Scatter(
                x=['Open', 'High', 'Low', 'Close'],
                y=[selected_stock['open'], selected_stock['high'], 
                   selected_stock['low'], selected_stock['close']],
                mode='markers+lines',
                marker=dict(size=10, color=['blue', 'green', 'red', 'orange']),
                name='OHLC Points'
            ))
            
            circuit_fig.update_layout(
                title=f"Circuit Limits Analysis - {selected_stock['symbol']}",
                xaxis_title="Price Points",
                yaxis_title="Price (₹)",
                template="plotly_white",
                height=500
            )
            
            st.plotly_chart(circuit_fig, use_container_width=True)
            
            # Risk metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                upper_buffer = ((selected_stock['upper_circuit'] - selected_stock['last_price']) / selected_stock['last_price']) * 100
                st.metric("📈 Upper Circuit Buffer", f"{upper_buffer:.2f}%")
            
            with col2:
                lower_buffer = ((selected_stock['last_price'] - selected_stock['lower_circuit']) / selected_stock['last_price']) * 100
                st.metric("📉 Lower Circuit Buffer", f"{lower_buffer:.2f}%")
            
            with col3:
                volatility = ((selected_stock['high'] - selected_stock['low']) / selected_stock['average_price']) * 100
                st.metric("📊 Intraday Volatility", f"{volatility:.2f}%")
        
        # Additional Analysis Section
        st.header("🔍 Detailed Stock Analysis")
        
        with st.expander("📊 Technical Analysis Summary", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**📈 Price Action:**")
                if selected_stock['net_change'] > 0:
                    st.success(f"✅ Bullish momentum with +{selected_stock['net_change_percent']:.2f}% gain")
                elif selected_stock['net_change'] < 0:
                    st.error(f"❌ Bearish pressure with {selected_stock['net_change_percent']:.2f}% decline")
                else:
                    st.info("➡️ Neutral trading with no significant change")
                
                st.write("**📊 Volume Analysis:**")
                if selected_stock['volume'] > 50000:
                    st.success("✅ High trading volume indicates strong interest")
                elif selected_stock['volume'] > 20000:
                    st.warning("⚠️ Moderate trading volume")
                else:
                    st.error("❌ Low trading volume - limited liquidity")
            
            with col2:
                st.write("**🎯 Support & Resistance:**")
                st.info(f"**Resistance:** ₹{selected_stock['high']:.2f} (Day High)")
                st.info(f"**Support:** ₹{selected_stock['low']:.2f} (Day Low)")
                
                st.write("**⚠️ Risk Assessment:**")
                if upper_buffer > 10 and lower_buffer > 10:
                    st.success("✅ Low risk - Well within circuit limits")
                elif upper_buffer < 5 or lower_buffer < 5:
                    st.error("❌ High risk - Near circuit limits")
                else:
                    st.warning("⚠️ Moderate risk")
        
        # Summary table for all stocks
        if len(df) > 1:
            st.header("📋 All Stocks Summary")
            
            # Create summary dataframe
            summary_df = df[['symbol', 'last_price', 'net_change', 'net_change_percent', 'volume', 'high', 'low']].copy()
            summary_df['net_change_percent'] = summary_df['net_change_percent'].round(2)
            
            # Color code the dataframe
            def color_negative_red(val):
                color = 'red' if val < 0 else 'green' if val > 0 else 'black'
                return f'color: {color}'
            
            styled_df = summary_df.style.applymap(color_negative_red, subset=['net_change', 'net_change_percent'])
            st.dataframe(styled_df, use_container_width=True)

else:
    st.info("📁 Please ensure 'ohlc.json' file exists in the same directory to start the analysis.")
    
    # Show sample format
    with st.expander("📋 Expected ohlc.json Format", expanded=False):
        st.code('''
{
    "status": "success",
    "data": {
        "NSE_EQ:SYMBOL": {
            "ohlc": {
                "open": 117.0,
                "high": 118.75,
                "low": 114.0,
                "close": 116.23
            },
            "symbol": "GTPL",
            "last_price": 116.23,
            "volume": 38651,
            "average_price": 115.64,
            "net_change": -2.53,
            "upper_circuit_limit": 138.28,
            "lower_circuit_limit": 92.19,
            "timestamp": "2025-06-14T17:41:14.773+05:30"
        }
    }
}
        ''', language='json')

# Footer
st.markdown("---")
st.markdown("📊 **Stock Market Analyzer** | Built with Streamlit & Plotly | 🚀 Real-time Market Data Visualization")