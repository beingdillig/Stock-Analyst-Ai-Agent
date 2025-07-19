import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import numpy as np
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Candlestick Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state= "auto"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        border: 2px,solid,green ;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .insight-card {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

def load_candlestick_data(file_path):
    """
    Load candlestick data from JSON file
    
    Args:
        file_path (str): Path to the JSON file containing candlestick data
    
    Returns:
        pandas.DataFrame: Processed candlestick data
    """
    try:
        # Load JSON data
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        # Extract candles data
        candles = data['data']['candles']
        
        # Create DataFrame
        columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi']
        df = pd.DataFrame(candles, columns=columns)
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        
        # Convert numeric columns
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col])
        
        # Sort by timestamp (oldest first)
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Calculate additional metrics
        df['daily_return'] = df['close'].pct_change() * 100
        df['volatility'] = ((df['high'] - df['low']) / df['open']) * 100
        df['body_size'] = abs(df['close'] - df['open'])
        df['upper_shadow'] = df['high'] - df[['open', 'close']].max(axis=1)
        df['lower_shadow'] = df[['open', 'close']].min(axis=1) - df['low']
        df['is_green'] = df['close'] > df['open']
        df['price_range'] = df['high'] - df['low']
        df['mid_price'] = (df['high'] + df['low']) / 2
        
        # Moving averages
        df['sma_5'] = df['close'].rolling(window=5).mean()
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        
        # RSI calculation
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        return df
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

def calculate_metrics(df):
    """Calculate key trading metrics"""
    if df is None or df.empty:
        return {}
    
    current_price = df['close'].iloc[-1]
    previous_price = df['close'].iloc[-2] if len(df) > 1 else current_price
    price_change = current_price - previous_price
    price_change_pct = (price_change / previous_price) * 100 if previous_price != 0 else 0
    
    max_price = df['high'].max()
    min_price = df['low'].min()
    avg_volume = df['volume'].mean()
    total_volume = df['volume'].sum()
    
    # Calculate volatility
    returns = df['daily_return'].dropna()
    volatility = returns.std() if len(returns) > 0 else 0
    
    # Bull/Bear days
    green_days = df['is_green'].sum()
    red_days = len(df) - green_days
    win_rate = (green_days / len(df)) * 100 if len(df) > 0 else 0
    
    # Recent trend (last 10 days)
    recent_trend = "Bullish" if df['close'].iloc[-1] > df['sma_5'].iloc[-1] else "Bearish"
    
    return {
        'current_price': current_price,
        'price_change': price_change,
        'price_change_pct': price_change_pct,
        'max_price': max_price,
        'min_price': min_price,
        'avg_volume': avg_volume,
        'total_volume': total_volume,
        'volatility': volatility,
        'green_days': green_days,
        'red_days': red_days,
        'win_rate': win_rate,
        'recent_trend': recent_trend,
        'total_days': len(df)
    }

def create_candlestick_chart(df, show_volume=True, show_indicators=True):
    """Create interactive candlestick chart"""
    # Create subplots
    if show_volume:
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=('Price Action', 'Volume', 'RSI'),
            row_width=[0.2, 0.3, 0.4],
        )
    else:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            subplot_titles=('Price Action', 'RSI'),
            row_width=[0.2, 0.1]
        )
    
    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name="OHLC",
            increasing_line_color='#00ff88',
            decreasing_line_color='#ff4444'
        ),
        row=1, col=1
    )
    
    # Add moving averages if indicators are enabled
    if show_indicators:
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['sma_5'],
                mode='lines',
                name='SMA 5',
                line=dict(color='orange', width=1)
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['sma_20'],
                mode='lines',
                name='SMA 20',
                line=dict(color='blue', width=1)
            ),
            row=1, col=1
        )
        
        # Bollinger Bands
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['bb_upper'],
                mode='lines',
                name='BB Upper',
                line=dict(color='gray', width=1, dash='dash'),
                opacity=0.7
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['bb_lower'],
                mode='lines',
                name='BB Lower',
                line=dict(color='gray', width=1, dash='dash'),
                fill='tonexty',
                fillcolor='rgba(128,128,128,0.1)',
                opacity=0.7
            ),
            row=1, col=1
        )
    
    # Volume chart
    if show_volume:
        colors = ['green' if row['is_green'] else 'red' for _, row in df.iterrows()]
        fig.add_trace(
            go.Bar(
                x=df['timestamp'],
                y=df['volume'],
                name="Volume",
                marker_color=colors,
                opacity=0.7
            ),
            row=2, col=1
        )
        
        # RSI
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['rsi'],
                mode='lines',
                name='RSI',
                line=dict(color='purple', width=2)
            ),
            row=3, col=1
        )
        
        # RSI levels
        fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.7, row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.7, row=3, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="gray", opacity=0.5, row=3, col=1)
    else:
        # RSI only
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['rsi'],
                mode='lines',
                name='RSI',
                line=dict(color='purple', width=2)
            ),
            row=2, col=1
        )
        
        fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.7, row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.7, row=2, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="gray", opacity=0.5, row=2, col=1)
    
    # Update layout
    fig.update_layout(
        title="Candlestick Chart with Technical Indicators",
        yaxis_title="Price (₹)",
        xaxis_rangeslider_visible=False,
        height=800,
        showlegend=True,
        template="plotly_dark"
    )
    
    return fig

def create_volume_analysis(df):
    """Create volume analysis chart"""
    fig = px.bar(
        df, 
        x='timestamp', 
        y='volume',
        color='is_green',
        color_discrete_map={True: 'green', False: 'red'},
        title="Volume Analysis",
        labels={'volume': 'Volume', 'timestamp': 'Date'}
    )
    
    fig.update_layout(
        template="plotly_dark",
        height=400,
        showlegend=False
    )
    
    return fig

def create_returns_analysis(df):
    """Create returns analysis chart"""
    fig = px.bar(
        df.dropna(), 
        x='timestamp', 
        y='daily_return',
        color='daily_return',
        color_continuous_scale=['red', 'yellow', 'green'],
        title="Daily Returns Analysis",
        labels={'daily_return': 'Daily Return (%)', 'timestamp': 'Date'}
    )
    
    fig.update_layout(
        template="plotly_dark",
        height=400
    )
    
    return fig

def create_volatility_analysis(df):
    """Create volatility analysis chart"""
    fig = px.line(
        df, 
        x='timestamp', 
        y='volatility',
        title="Daily Volatility Analysis",
        labels={'volatility': 'Volatility (%)', 'timestamp': 'Date'}
    )
    
    fig.update_traces(line_color='orange')
    fig.update_layout(
        template="plotly_dark",
        height=400
    )
    
    return fig

def main():
    # Header
    st.markdown('<h1 class="main-header">📈 Candlestick Data Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar for file upload and controls
    st.sidebar.header("📁 Data Controls")
    
    # File upload option
    uploaded_file = st.sidebar.file_uploader(
        "Upload JSON file", 
        type=['json'],
        help="Upload your candlestick data JSON file"
    )
    
    # Alternative: Use file path input
    st.sidebar.subheader("Or specify file path:")
    file_path = st.sidebar.text_input(
        "File Path", 
        value="C:\\Users\\dwiwe\\Documents\\Html & CSS\\Stock analyst MCP server\\historic_candles.json",
        help="Enter the path to your JSON file"
    )
    
    # Load data
    df = None
    if uploaded_file is not None:
        # Load from uploaded file
        try:
            data = json.load(uploaded_file)
            candles = data['data']['candles']
            columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi']
            df = pd.DataFrame(candles, columns=columns)
            
            # Process the data (same as in load_candlestick_data function)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date
            
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col])
            
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            # Calculate additional metrics
            df['daily_return'] = df['close'].pct_change() * 100
            df['volatility'] = ((df['high'] - df['low']) / df['open']) * 100
            df['body_size'] = abs(df['close'] - df['open'])
            df['upper_shadow'] = df['high'] - df[['open', 'close']].max(axis=1)
            df['lower_shadow'] = df[['open', 'close']].min(axis=1) - df['low']
            df['is_green'] = df['close'] > df['open']
            df['price_range'] = df['high'] - df['low']
            df['mid_price'] = (df['high'] + df['low']) / 2
            
            # Moving averages
            df['sma_5'] = df['close'].rolling(window=5).mean()
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            
            # RSI calculation
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            
        except Exception as e:
            st.error(f"Error processing uploaded file: {str(e)}")
    else:
        # Load from file path
        df = load_candlestick_data(file_path)
    
    if df is not None and not df.empty:
        # Sidebar filters
        st.sidebar.subheader("📊 Filters & Options")
        
        # Date range filter
        min_date = df['date'].min()
        max_date = df['date'].max()
        
        selected_range = st.sidebar.date_input(
            "Select Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # Filter dataframe
        if len(selected_range) == 2:
            mask = (df['date'] >= selected_range[0]) & (df['date'] <= selected_range[1])
            filtered_df = df.loc[mask].copy()
        else:
            filtered_df = df.copy()
        
        # Chart options
        show_volume = st.sidebar.checkbox("Show Volume", value=True)
        show_indicators = st.sidebar.checkbox("Show Technical Indicators", value=True)
        
        # Calculate metrics
        metrics = calculate_metrics(filtered_df)
        
        # Display key metrics
        st.subheader("📈 Key Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <h3>Current Price</h3>
                    <h2>₹{metrics['current_price']:.2f}</h2>
                    <p style="color: {'#00ff88' if metrics['price_change'] >= 0 else '#ff4444'}">
                        {'+' if metrics['price_change'] >= 0 else ''}{metrics['price_change']:.2f} 
                        ({metrics['price_change_pct']:.2f}%)
                    </p>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        with col2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <h3>Price Range</h3>
                    <h2>₹{metrics['min_price']:.2f} - ₹{metrics['max_price']:.2f}</h2>
                    <p>Range: ₹{metrics['max_price'] - metrics['min_price']:.2f}</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        with col3:
            st.markdown(
                f"""
                <div class="metric-card">
                    <h3>Average Volume</h3>
                    <h2>{metrics['avg_volume']:,.0f}</h2>
                    <p>Total: {metrics['total_volume']:,.0f}</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        with col4:
            st.markdown(
                f"""
                <div class="metric-card">
                    <h3>Win Rate</h3>
                    <h2>{metrics['win_rate']:.1f}%</h2>
                    <p>{metrics['green_days']}W / {metrics['red_days']}L</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        st.markdown("---")
        
        # Main candlestick chart
        st.subheader("📊 Price Action Analysis")
        candlestick_fig = create_candlestick_chart(filtered_df, show_volume, show_indicators)
        st.plotly_chart(candlestick_fig, use_container_width=True)
        
        # Additional analysis tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Volume Analysis", "📈 Returns", "⚡ Volatility", "🎯 Insights"])
        
        with tab1:
            st.subheader("Volume Analysis")
            volume_fig = create_volume_analysis(filtered_df)
            st.plotly_chart(volume_fig, use_container_width=True)
            
            # Volume statistics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Average Volume", f"{metrics['avg_volume']:,.0f}")
                st.metric("Max Volume", f"{filtered_df['volume'].max():,.0f}")
            with col2:
                st.metric("Min Volume", f"{filtered_df['volume'].min():,.0f}")
                st.metric("Volume Std Dev", f"{filtered_df['volume'].std():,.0f}")
        
        with tab2:
            st.subheader("Daily Returns Analysis")
            returns_fig = create_returns_analysis(filtered_df)
            st.plotly_chart(returns_fig, use_container_width=True)
            
            # Returns statistics
            returns_stats = filtered_df['daily_return'].describe()
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Average Return", f"{returns_stats['mean']:.2f}%")
                st.metric("Best Day", f"{returns_stats['max']:.2f}%")
            with col2:
                st.metric("Worst Day", f"{returns_stats['min']:.2f}%")
                st.metric("Return Std Dev", f"{returns_stats['std']:.2f}%")
        
        with tab3:
            st.subheader("Volatility Analysis")
            volatility_fig = create_volatility_analysis(filtered_df)
            st.plotly_chart(volatility_fig, use_container_width=True)
            
            # Volatility statistics
            vol_stats = filtered_df['volatility'].describe()
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Average Volatility", f"{vol_stats['mean']:.2f}%")
                st.metric("Max Volatility", f"{vol_stats['max']:.2f}%")
            with col2:
                st.metric("Min Volatility", f"{vol_stats['min']:.2f}%")
                st.metric("Volatility Std Dev", f"{vol_stats['std']:.2f}%")
        
        with tab4:
            st.subheader("🎯 Key Insights & Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📈 Trading Statistics")
                st.markdown(f"**Total Trading Days:** {metrics['total_days']}")
                st.markdown(f"**Winning Days:** {metrics['green_days']} ({metrics['win_rate']:.1f}%)")
                st.markdown(f"**Losing Days:** {metrics['red_days']} ({100-metrics['win_rate']:.1f}%)")
                st.markdown(f"**Current Trend:** {metrics['recent_trend']}")
                st.markdown(f"**Volatility Level:** {metrics['volatility']:.2f}%")
                
                # Risk assessment
                risk_level = "High" if metrics['volatility'] > 3 else "Moderate" if metrics['volatility'] > 2 else "Low"
                st.markdown(f"**Risk Level:** {risk_level}")
            
            with col2:
                st.markdown("### 💡 Automated Insights")
                
                # Generate insights
                insights = []
                
                if metrics['win_rate'] > 60:
                    insights.append("🟢 Strong bullish trend with high win rate")
                elif metrics['win_rate'] < 40:
                    insights.append("🔴 Bearish trend with low win rate")
                else:
                    insights.append("🟡 Neutral trend with balanced win/loss ratio")
                
                if metrics['volatility'] > 4:
                    insights.append("⚠️ High volatility indicates increased risk")
                elif metrics['volatility'] < 2:
                    insights.append("✅ Low volatility suggests stable price action")
                
                if filtered_df['volume'].iloc[-5:].mean() > filtered_df['volume'].mean():
                    insights.append("📈 Recent volume above average - increased activity")
                
                # RSI insights
                current_rsi = filtered_df['rsi'].iloc[-1]
                if not pd.isna(current_rsi):
                    if current_rsi > 70:
                        insights.append("🔴 RSI indicates overbought conditions")
                    elif current_rsi < 30:
                        insights.append("🟢 RSI indicates oversold conditions")
                    else:
                        insights.append("🟡 RSI in neutral territory")
                
                for insight in insights:
                    st.markdown(f"- {insight}")
        
        # Data table (expandable)
        with st.expander("📋 Raw Data Table"):
            st.dataframe(
                filtered_df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'daily_return', 'volatility']].round(2),
                use_container_width=True
            )
        
        # Export functionality
        st.sidebar.subheader("💾 Export Data")
        if st.sidebar.button("Download Processed Data as CSV"):
            csv = filtered_df.to_csv(index=False)
            st.sidebar.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"candlestick_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    else:
        st.warning("⚠️ Please upload a JSON file or ensure the file path is correct.")
        st.info("""
        📋 **File Format Requirements:**
        
        Your JSON file should have the following structure:
        ```json
        {
            "status": "success",
            "data": {
                "candles": [
                    ["2025-06-06T00:00:00+05:30", 32.85, 33.31, 32.69, 32.9, 52446, 0],
                    ["2025-06-05T00:00:00+05:30", 33.15, 33.15, 32.61, 32.69, 139035, 0],
                    ...
                ]
            }
        }
        ```
        
        Where each candle array contains:
        [timestamp, open, high, low, close, volume, open_interest]
        """)

if __name__ == "__main__":
    main()