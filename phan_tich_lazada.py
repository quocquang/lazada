import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
# from selenium import webdriver  # Assuming scraping part works or is handled separately if needed
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.common.exceptions import NoSuchElementException
import time
import io
import numpy as np
import random
# from webdriver_manager.chrome import ChromeDriverManager # Assume scraping part works
# from selenium.webdriver.chrome.service import Service    # Assume scraping part works
from datetime import datetime
import matplotlib.pyplot as plt
from scipy import stats
import base64
import os # Added for potential environment checks if scraping is re-enabled

# --- Helper Functions ---

# Hàm định dạng tiền tệ tùy chỉnh (Improved robustness)
def format_currency(value):
    """Formats a number as Vietnamese Dong currency."""
    if pd.isna(value) or not isinstance(value, (int, float)):
        return "0 VND"
    # Handle potential zero division or invalid inputs resulting in non-numeric types again
    try:
        return f"{float(value):,.0f} VND".replace(",", ".")
    except (ValueError, TypeError):
        return "0 VND"

# Hàm định dạng phần trăm (Improved robustness)
def format_percent(value):
    """Formats a number as a percentage string."""
    if pd.isna(value) or not isinstance(value, (int, float)):
        return "0.00%"
    try:
        return f"{float(value):.2f}%"
    except (ValueError, TypeError):
         return "0.00%"

# --- Streamlit Page Config ---
st.set_page_config(
    page_title="Phân tích đơn hàng Lazada",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# --- Enhanced CSS ---
st.markdown("""
<style>
    :root {
        --primary: #FF6200; /* Lazada Orange */
        --primary-light: #FF8A3D;
        --primary-dark: #D14700;
        --secondary: #00A0D6; /* Lazada Blue */
        --secondary-light: #33C0F3;
        --text-main: #333333;
        --text-light: #666666;
        --bg-main: #F8F9FA;
        --bg-card: #FFFFFF;
        --bg-sidebar: #1E293B; /* Dark Blue/Gray */
        --success: #28A745;
        --warning: #FFC107;
        --danger: #DC3545;
    }
    /* General */
    body { font-family: 'Roboto', sans-serif; }
    .main { background-color: var(--bg-main); color: var(--text-main); }

    /* Sidebar */
    [data-testid="stSidebar"] { background-color: var(--bg-sidebar); }
    .st-emotion-cache-16txtl3 { color: #FFFFFF; } /* Sidebar headers */
    .stRadio > label { color: #FFFFFF; margin-bottom: 10px;} /* Radio button label color in sidebar */
    .stTextInput>label, .stFileUploader>label, .stButton>label, .stRadio>label, .stDateInput>label, .stSelectbox>label, .stSlider>label { color: #e2e8f0 !important; } /* Sidebar widget labels */
    .stFileUploader > section > button { border-color: var(--primary-light);}

    /* Buttons */
    .stButton>button { background-color: var(--primary); color: white !important; border-radius: 6px; padding: 10px 18px; margin: 8px 0; font-weight: 600; border: none; transition: all 0.3s ease; text-transform: uppercase; letter-spacing: 0.5px; }
    .stButton>button:hover { background-color: var(--primary-light); transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .stButton>button:active { background-color: var(--primary-dark); transform: translateY(0); box-shadow: none; }

    /* Metric Cards - Refined */
    .metric-card {
        background-color: var(--bg-card); padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); text-align: center; margin: 10px 0;
        transition: all 0.3s ease; border-top: 5px solid var(--primary);
        height: 190px; /* Fixed height for alignment */
        display: flex; flex-direction: column; justify-content: space-between; /* Align content */
    }
    .metric-card:hover { transform: translateY(-5px); box-shadow: 0 8px 24px rgba(0,0,0,0.12); }
    .metric-card h2 { /* Value */
        font-size: 24px; font-weight: 700; color: var(--primary); margin: 5px 0; line-height: 1.2;
        word-wrap: break-word; /* Prevent long numbers from overflowing */
    }
    .metric-card h4 { /* Label */
        font-size: 14px; font-weight: 500; color: var(--text-light); margin-bottom: 8px;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    .metric-delta { font-size: 13px; margin-top: 5px; height: 20px; } /* Fixed height for delta */
    .metric-chart { width: 100%; height: 35px; margin-top: auto; margin-bottom: 5px;} /* Pushes chart to bottom */
    .metric-chart img { max-width: 100%; max-height: 100%; object-fit: contain; }

    /* Headers */
    .main-title { text-align: center; color: var(--primary); margin-bottom: 25px; font-size: 34px; font-weight: 700; }
    .tab-header { font-size: 30px; font-weight: 700; background: linear-gradient(90deg, var(--primary) 0%, var(--primary-light) 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-top: 10px; margin-bottom: 20px; text-align: center; padding: 10px 0; border-bottom: 1px solid #eee; }
    .sub-header { font-size: 20px; font-weight: 600; color: var(--primary-dark); margin-top: 25px; margin-bottom: 15px; padding-bottom: 6px; border-bottom: 2px solid var(--primary-light); }

    /* Filter Section */
    .filter-section { background-color: var(--bg-card); padding: 20px 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #e9ecef; }
    .filter-section h3 { font-size: 18px; font-weight: 600; color: var(--text-main); margin-bottom: 16px; text-align: center;}

    /* DataFrames - Keep as is */
    .dataframe { width: 100%; border-collapse: collapse; }
    .dataframe th { background-color: var(--primary); color: white; padding: 12px; text-align: left; font-weight: 600; }
    .dataframe td { padding: 10px; border-bottom: 1px solid #ddd; }
    .dataframe tr:nth-child(even) { background-color: #f9f9f9; }
    .dataframe tr:hover { background-color: #f1f1f1; }

    /* Inputs and Selects - Slight adjustment */
    .stTextInput>div>div>input, .stSelectbox>div>div, .stMultiselect>div>div, .stDateInput>div>div>input { border-radius: 6px !important; border: 1px solid #ced4da !important; padding: 8px 10px !important; background-color: #fff; }
    .stTextInput>div>div>input:focus, .stSelectbox>div>div:focus-within, .stMultiselect>div>div:focus-within, .stDateInput>div>div>input:focus { border-color: var(--primary) !important; box-shadow: 0 0 0 2px rgba(255,98,0,0.2) !important; }
    .stDateInput>div>div>div>button { border: none; background: none; } /* Remove border from date picker button */

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { background-color: var(--bg-card); border-radius: 8px 8px 0 0; padding: 0 15px; border-bottom: 3px solid var(--primary); }
    .stTabs [data-baseweb="tab"] { padding: 10px 20px; font-weight: 600; color: var(--text-light); border-radius: 8px 8px 0 0; }
    .stTabs [aria-selected="true"] { background-color: var(--primary); color: white !important; border-bottom: none; }

    /* Progress Bar */
    .stProgress > div > div > div > div { background-color: var(--primary); }

    /* Links */
    a { color: var(--secondary); text-decoration: none; }
    a:hover { color: var(--secondary-light); text-decoration: underline; }

    /* Footer */
    .footer { text-align: center; margin-top: 40px; padding: 20px; font-size: 13px; color: var(--text-light); border-top: 1px solid #eee; }

    /* Animations */
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    .animate-fadeIn { animation: fadeIn 0.5s ease-in-out; }

    /* Responsive */
    @media (max-width: 768px) {
        .tab-header { font-size: 24px; }
        .metric-card { padding: 16px; height: auto; min-height: 160px;} /* Adjust height for mobile */
        .metric-card h2 { font-size: 20px; }
        .main-title { font-size: 28px; }
        .stButton>button { padding: 8px 14px; font-size: 14px;}
        .stTabs [data-baseweb="tab"] { padding: 10px 16px; font-size: 14px;}
        .filter-section {padding: 15px;}
        .sub-header {font-size: 18px;}
    }
</style>
""", unsafe_allow_html=True)

# --- (Optional) Lazada Scraper Function Placeholder ---
# Keep your original scraper function here if you intend to use it.
# For now, I'll comment out the Selenium imports at the top and the function call
# to focus on the UI/Chart part assuming data is loaded via Excel.
@st.cache_data(ttl=3600, show_spinner="Đang cào dữ liệu...")
def scrape_lazada_products(search_query, max_retries=3):
    # ... (Your original scraping code) ...
    # ... Ensure it returns an empty DataFrame on failure ...
    st.warning("Chức năng cào dữ liệu đang được bảo trì.")
    return pd.DataFrame() # Placeholder return


# --- Metric Card Function (Using Previous Robust Version) ---
def display_metric_with_sparkline(label, value, previous_value=None, value_format_func=format_currency, chart_data=None, chart_color="#FF6200", unit="", higher_is_better=True):
    """Displays a metric in a card with optional delta and sparkline."""
    value_str = value_format_func(value) if value_format_func else str(value)
    delta_html = "<div class='metric-delta'> </div>" # Placeholder for alignment

    if previous_value is not None and isinstance(value, (int, float)) and isinstance(previous_value, (int, float)) and previous_value != 0:
        try:
            delta_val = float(value) - float(previous_value)
            delta_pct = (delta_val / float(previous_value)) * 100

            delta_str_formatted = f"{delta_val:+,.0f}".replace(",", ".") if abs(delta_val) >= 1 else f"{delta_val:+.1f}" # Format delta value intelligently
            delta_pct_str = f"{delta_pct:+.1f}%"

            is_improvement = (delta_val > 0) if higher_is_better else (delta_val < 0)
            is_worse = (delta_val < 0) if higher_is_better else (delta_val > 0)

            color = "var(--success)" if is_improvement else "var(--danger)" if is_worse else "var(--text-light)"
            icon = "▲" if is_improvement else "▼" if is_worse else "●"

            delta_html = f"<div class='metric-delta' style='color:{color};'>{icon} {delta_str_formatted} ({delta_pct_str}) so với trước</div>"
        except Exception: # Catch potential division errors or formatting issues
             delta_html = f"<div class='metric-delta' style='color:var(--warning);'>Lỗi tính delta</div>"

    elif previous_value is not None:
         delta_html = f"<div class='metric-delta' style='color:var(--text-light);'>● Không có dữ liệu trước</div>"


    chart_html = "<div class='metric-chart'></div>" # Placeholder
    if chart_data is not None and len(chart_data) > 1:
        try:
            # Normalize data for better visualization in small chart
            norm_data = np.array(chart_data, dtype=float) # Ensure float
            min_val, max_val = norm_data.min(), norm_data.max()

            if max_val > min_val: # Avoid division by zero if all values are same
                 norm_data = (norm_data - min_val) / (max_val - min_val)
            else:
                 norm_data = np.full_like(norm_data, 0.5) # Flat line in the middle if all same

            fig, ax = plt.subplots(figsize=(4, 0.6)) # Adjusted figsize for better aspect ratio
            ax.plot(range(len(norm_data)), norm_data, color=chart_color, linewidth=2)
            ax.fill_between(range(len(norm_data)), norm_data, alpha=0.2, color=chart_color)
            ax.set_axis_off()
            fig.patch.set_alpha(0) # Transparent figure background
            ax.patch.set_alpha(0)  # Transparent axes background

            buf = io.BytesIO()
            fig.savefig(buf, format='png', transparent=True, bbox_inches='tight', pad_inches=0, dpi=72)
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)
            chart_html = f"<div class='metric-chart'><img src='data:image/png;base64,{img_str}' alt='{label} trend'/></div>"
        except Exception as plot_err:
            # st.warning(f"Could not generate sparkline for {label}: {plot_err}") # Maybe too noisy
            chart_html = "<div class='metric-chart'></div>" # Fallback empty div


    st.markdown(f"""
        <div class="metric-card animate-fadeIn">
            <div>
                <h4>{label}</h4>
                <h2>{value_str}{unit}</h2>
                {delta_html}
            </div>
            {chart_html}
        </div>
    """, unsafe_allow_html=True)


# --- Charting Functions (Refined) ---

# Hàm tạo biểu đồ phân phối (Histogram hoặc Bar)
def create_distribution_chart(df, column, title, color_sequence=px.colors.sequential.Oranges_r, is_currency=False, y_title='Số lượng'):
    """Creates a histogram for numeric or bar chart for categorical data."""
    if df is None or column not in df.columns or df[column].isnull().all() or df.empty:
        # st.warning(f"Không đủ dữ liệu hợp lệ trong cột '{column}' để vẽ biểu đồ phân phối.")
        fig = go.Figure()
        fig.update_layout(title=f"{title} (Không có dữ liệu)", title_x=0.5)
        return fig # Return empty figure with title

    chart_df = df.dropna(subset=[column])
    if chart_df.empty:
        fig = go.Figure()
        fig.update_layout(title=f"{title} (Không có dữ liệu)", title_x=0.5)
        return fig

    # Decide chart type based on dtype and unique values
    is_numeric = pd.api.types.is_numeric_dtype(chart_df[column])
    unique_count = chart_df[column].nunique()

    if is_numeric and unique_count > 15: # Histogram for continuous numeric
        fig = px.histogram(chart_df, x=column, title=title,
                           color_discrete_sequence=[color_sequence[1]], # Pick a color from sequence
                           marginal="box", # Add box plot
                           labels={column: column.replace("_", " ").title()},
                           opacity=0.8)
        fig.update_layout(bargap=0.1)
        xaxis_title = column.replace("_", " ").title()
        yaxis_title = y_title
        if is_currency:
            fig.update_xaxes(tickformat=",.0f") # Format currency on x-axis
            xaxis_title += " (VND)"
        fig.update_layout(xaxis_title=xaxis_title, yaxis_title=yaxis_title)

    else: # Bar chart for categorical or discrete numeric
        col_data = chart_df[column].astype(str).value_counts().reset_index()
        col_data.columns = ['category', 'count']
        # Sort by count descending, limit categories if too many
        col_data = col_data.sort_values('count', ascending=False).head(20)
        fig = px.bar(col_data, y='category', x='count', title=title,
                     color='count', color_continuous_scale=color_sequence,
                     text='count', orientation='h',
                     labels={'category': column.replace("_", " ").title(), 'count': y_title})
        fig.update_traces(textposition='outside', texttemplate='%{text:,}')
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, # Show highest bar at top
                         xaxis_title=y_title, yaxis_title="")
        fig.update_coloraxes(showscale=False) # Hide color scale for bar chart

    fig.update_layout(
        title={'text': title, 'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top', 'font': {'size': 18, 'color': 'var(--text-main)'}},
        xaxis_title_font={'size': 12, 'color': 'var(--text-light)'},
        yaxis_title_font={'size': 12, 'color': 'var(--text-light)'},
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='#EEEEEE'),
        yaxis=dict(showgrid=False, gridwidth=1, gridcolor='#EEEEEE'), # Hide y grid lines for bar
        hoverlabel=dict(bgcolor="white", font_size=12)
    )
    return fig

# Hàm hiển thị biểu đồ thời gian (Refined)
def plot_time_series(df, date_col, value_col, title, add_trend=False, color='var(--primary)', y_format_func=None, aggregate_func='sum', y_axis_label=None):
    """Plots time series data with optional trend line."""
    if df is None or date_col not in df.columns or value_col not in df.columns or df.empty or df[date_col].isnull().all() or df[value_col].isnull().all():
        # st.warning(f"Không đủ dữ liệu để vẽ biểu đồ '{title}'.")
        fig = go.Figure()
        fig.update_layout(title=f"{title} (Không có dữ liệu)", title_x=0.5)
        return fig

    # Ensure date column is datetime and drop rows where date is NaT
    df_time = df.copy()
    df_time[date_col] = pd.to_datetime(df_time[date_col], errors='coerce')
    df_time = df_time.dropna(subset=[date_col, value_col])

    if df_time.empty:
        fig = go.Figure()
        fig.update_layout(title=f"{title} (Không có dữ liệu)", title_x=0.5)
        return fig

    # Aggregate data by day
    df_agg = df_time.groupby(pd.Grouper(key=date_col, freq='D'))[value_col].agg(aggregate_func).reset_index()
    df_agg = df_agg.dropna(subset=[value_col]) # Remove days with no data after aggregation

    if df_agg.empty:
        fig = go.Figure()
        fig.update_layout(title=f"{title} (Dữ liệu rỗng sau khi nhóm)", title_x=0.5)
        return fig

    fig = go.Figure()
    base_name = y_axis_label if y_axis_label else value_col.replace("_", " ").title()

    # Determine hover template formatting based on y_format_func
    y_hover_format = ",.0f" # Default number format
    if y_format_func == format_currency:
        y_hover_format = ",.0f" # Keep as number, add VND in label later if needed
    elif y_format_func == format_percent:
        y_hover_format = ".2f" # Percentage format

    fig.add_trace(go.Scatter(
        x=df_agg[date_col], y=df_agg[value_col], mode='lines+markers', name=base_name,
        line=dict(color=color, width=2.5), marker=dict(size=5),
        hovertemplate=f"<b>Ngày</b>: %{{x|%d-%m-%Y}}<br><b>{base_name}</b>: %{{y:{y_hover_format}}}<extra></extra>"
    ))

    # Trendline (Optional and simplified)
    trend_annotation_text = ""
    if add_trend and len(df_agg) > 5: # Require more points for a meaningful trend
        try:
            x_numeric = np.arange(len(df_agg)) # Simple numeric index for trend calculation
            y = df_agg[value_col].values
            slope, intercept, r_value, _, _ = stats.linregress(x_numeric, y)
            trend_y = intercept + slope * x_numeric
            fig.add_trace(go.Scatter(x=df_agg[date_col], y=trend_y, mode='lines', name='Xu hướng',
                                     line=dict(color='rgba(209, 71, 0, 0.6)', width=1.5, dash='dash'),
                                     hoverinfo='skip'))
        except ValueError:
            pass # Ignore trend calculation errors silently


    yaxis_title = base_name
    yaxis_config = dict(
        title=yaxis_title,
        showgrid=True, gridwidth=1, gridcolor='#EEEEEE',
        title_font={'size': 12, 'color': 'var(--text-light)'}
    )
    if y_format_func == format_currency:
         yaxis_config['tickformat'] = ',.0f' # Format axis ticks as numbers
         if not yaxis_title.endswith("(VND)"): yaxis_title += " (VND)" # Add unit if not present
         yaxis_config['title'] = yaxis_title
    elif y_format_func == format_percent:
         yaxis_config['ticksuffix'] = '%'
         if not yaxis_title.endswith("(%)"): yaxis_title += " (%)"
         yaxis_config['title'] = yaxis_title


    fig.update_layout(
        title={'text': title, 'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top', 'font': {'size': 18, 'color': 'var(--text-main)'}},
        xaxis_title="Ngày", yaxis=yaxis_config,
        xaxis_title_font={'size': 12, 'color': 'var(--text-light)'},
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, tickformat='%d-%m-%y'), # Simpler date format, no grid
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='#EEEEEE'),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5), # Move legend below
        margin=dict(l=60, r=30, t=70, b=80) # Adjust margins for legend/titles
    )

    return fig


# --- Data Loading / Processing (Using User's Original Logic) ---
# Wrap in a function for clarity
def load_and_process_data(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file)
        # --- Apply original cleaning/processing ---
        # Strip whitespace, remove currency symbols, replace dots, handle tabs
        df.columns = df.columns.str.strip().str.replace(" ₫", "", regex=False).str.replace(".", "", regex=False).str.replace("\t", " ", regex=False)

        # Date Conversion (Keep original logic)
        date_cols_to_convert = ["Ngày mua hàng", "Ngày nhận được"]
        for col in date_cols_to_convert:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], format="%d/%m/%Y", errors="coerce")

        # Numeric Conversion (Keep original logic)
        numeric_columns_to_convert = [
            "Số tiền bán trên lazada", "Số tiền khách hàng phải chi trả", "Phí vận chuyển",
            "Phí khuyến mãi do người bán trả cho lazada", "Lỗi do cân nặng trừ cho nhà bán hàng",
            "Giảm giá từ Lazada cho người mua", "Phí xử lý đơn hàng",
            "Tổng số tiền người mua thanh toán", "Tổng số tiền người bán nhận được thanh toán",
            "Số lượng"
        ]
        for col in numeric_columns_to_convert:
            if col in df.columns:
                # Important: Ensure the column actually contains convertible data before forcing numeric
                # This attempts conversion, sets errors to NaN, then fills NaN with 0
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)


        # Feature Engineering (Keep original logic)
        if "Ngày mua hàng" in df.columns and df["Ngày mua hàng"].notna().any():
            df["Tháng mua hàng"] = df["Ngày mua hàng"].dt.strftime("%Y-%m")
            # df["Quý"] = df["Ngày mua hàng"].dt.to_period("Q").astype(str) # Optional: Quarters might not be needed often
            df["Ngày trong tuần"] = df["Ngày mua hàng"].dt.day_name()
            df['Năm Tháng'] = df['Ngày mua hàng'].dt.to_period('M').astype(str) # Useful for monthly plots

        if "Ngày nhận được" in df.columns and "Ngày mua hàng" in df.columns:
             # Calculate difference only for valid date pairs
            valid_dates_mask = df["Ngày mua hàng"].notna() & df["Ngày nhận được"].notna()
            df.loc[valid_dates_mask, "Thời gian giao hàng (ngày)"] = (df.loc[valid_dates_mask, "Ngày nhận được"] - df.loc[valid_dates_mask, "Ngày mua hàng"]).dt.days
             # Handle potential negative delivery times -> set to 0 or NaN? Let's use NaN then fill later if needed.
            df.loc[df["Thời gian giao hàng (ngày)"] < 0, "Thời gian giao hàng (ngày)"] = np.nan # Make negatives NaN first

        if "Tổng số tiền người bán nhận được thanh toán" in df.columns and "Số tiền bán trên lazada" in df.columns:
            df["Lợi nhuận"] = df["Tổng số tiền người bán nhận được thanh toán"] - df["Số tiền bán trên lazada"]
            # Use np.where for robust division
            df["Biên lợi nhuận (%)"] = np.where(
                df["Số tiền bán trên lazada"].notna() & (df["Số tiền bán trên lazada"] != 0),
                (df["Lợi nhuận"] / df["Số tiền bán trên lazada"]) * 100,
                0 # Set margin to 0 if price is zero or NaN
            )
            # Clean up potential Inf/-Inf just in case, though np.where should handle it
            df["Biên lợi nhuận (%)"] = df["Biên lợi nhuận (%)"].replace([np.inf, -np.inf], 0).fillna(0)

        # --- End of original processing ---
        st.session_state.original_columns = df.columns.tolist() # Store for reference if needed
        return df

    except Exception as e:
        st.error(f"❌ Lỗi khi đọc hoặc xử lý file Excel: {str(e)}")
        st.error("Vui lòng kiểm tra định dạng file, tên cột và cấu trúc dữ liệu.")
        return pd.DataFrame()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://laz-img-cdn.alicdn.com/images/ims-web/TB1T7K2d8Cw3KVjSZFuXXcAOpXa.png", use_column_width=True) # Use column width
    st.markdown("<h2 style='color: #FFFFFF; text-align: center;'>Lazada Analytics</h2>", unsafe_allow_html=True)
    st.markdown("---", unsafe_allow_html=True)

    st.markdown("<h3 style='color: #FFFFFF;'>📊 Tải Dữ Liệu</h3>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Tải file báo cáo đơn hàng (.xlsx)", type=["xlsx"], label_visibility="collapsed")

    # Initialize session state
    if "df" not in st.session_state: st.session_state.df = pd.DataFrame()
    if "filtered_df" not in st.session_state: st.session_state.filtered_df = pd.DataFrame()
    if "data_loaded" not in st.session_state: st.session_state.data_loaded = False
    if "scraped_df" not in st.session_state: st.session_state.scraped_df = pd.DataFrame()
    if "date_col" not in st.session_state: st.session_state.date_col = "Ngày mua hàng" # Default assumption

    if uploaded_file is not None:
        if not st.session_state.data_loaded or st.session_state.get("uploaded_filename") != uploaded_file.name:
            with st.spinner("⏳ Đang xử lý dữ liệu..."):
                df_processed = load_and_process_data(uploaded_file) # Call the processing function
                if not df_processed.empty:
                    st.session_state.df = df_processed
                    # Identify primary date column AFTER processing
                    if "Ngày mua hàng" in df_processed.columns and df_processed["Ngày mua hàng"].notna().any():
                        st.session_state.date_col = "Ngày mua hàng"
                    # Add fallbacks if needed, e.g., "Ngày tạo đơn"
                    # else: st.session_state.date_col = None # Or a default fallback

                    st.session_state.filtered_df = df_processed.copy() # Initialize filtered_df
                    st.session_state.data_loaded = True
                    st.session_state.uploaded_filename = uploaded_file.name
                    st.success("✅ Tải và xử lý file thành công!")
                else:
                    # Reset if loading failed
                    st.session_state.df = pd.DataFrame()
                    st.session_state.filtered_df = pd.DataFrame()
                    st.session_state.data_loaded = False
                    st.session_state.date_col = "Ngày mua hàng" # Reset assumption
    elif st.session_state.data_loaded:
        st.info(f"ℹ️ Đang dùng dữ liệu: '{st.session_state.uploaded_filename}'")

    # Display data summary if loaded
    if st.session_state.data_loaded and not st.session_state.df.empty:
        df = st.session_state.df # Use the loaded data
        st.info(f"📑 {len(df):,} đơn hàng")
        date_col_display = st.session_state.date_col
        if date_col_display and date_col_display in df.columns:
            try:
                min_d = pd.to_datetime(df[date_col_display].min())
                max_d = pd.to_datetime(df[date_col_display].max())
                if pd.notna(min_d) and pd.notna(max_d):
                     st.info(f"📅 {min_d.strftime('%d/%m/%y')} - {max_d.strftime('%d/%m/%y')}")
            except Exception: pass # Ignore errors displaying date range

        if "Sản Phẩm" in df.columns:
            st.info(f"🏷️ {df['Sản Phẩm'].nunique()} SP unique")

        with st.expander("Xem trước dữ liệu đã xử lý", expanded=False):
            st.dataframe(df.head(), height=200)
            # st.write("Kiểu dữ liệu các cột:", df.dtypes) # For debugging types

    else:
        st.warning("⚠️ Vui lòng tải file Excel báo cáo đơn hàng.")

    st.markdown("---", unsafe_allow_html=True)

    # --- (Optional) Lazada Scraping Section ---
    st.markdown("<h3 style='color: #FFFFFF;'>🔍 Cào Dữ Liệu Đối Thủ</h3>", unsafe_allow_html=True)
    search_query = st.text_input("Nhập từ khóa/sản phẩm", placeholder="Ví dụ: 'kem chống nắng anessa'", label_visibility="collapsed")
    if st.button("🚀 Cào ngay", key="scrape_now", use_container_width=True, help="Bắt đầu cào dữ liệu từ Lazada (có thể mất vài phút)."):
        if search_query:
            # with st.spinner("Đang cào dữ liệu từ Lazada..."): # Managed by @st.cache_data
            scraped_df = scrape_lazada_products(search_query) # Call the cached function
            if not scraped_df.empty:
                st.session_state.scraped_df = scraped_df
                st.success(f"✅ Đã cào {len(scraped_df)} SP cho '{search_query}'")
                st.session_state.last_scraped_query = search_query
            # else: # Error message inside scrape_lazada_products now
            #    st.error("❌ Không tìm thấy sản phẩm hoặc lỗi khi cào dữ liệu.")
        else:
            st.warning("⚠️ Vui lòng nhập từ khóa tìm kiếm.")
    # Display info about scraped data
    last_query = st.session_state.get("last_scraped_query")
    if last_query and not st.session_state.scraped_df.empty:
         st.caption(f"Hiển thị dữ liệu cào cho: '{last_query}'")

    st.markdown("---", unsafe_allow_html=True)

    # --- Navigation ---
    st.markdown("<h3 style='color: #FFFFFF;'>🧭 Điều Hướng</h3>", unsafe_allow_html=True)
    # Define tabs - Scraper tab is conditional
    available_tabs = ["📊 Tổng quan", "📈 Phân tích chi tiết", "📦 Phân tích sản phẩm"]
    captions = ["Dashboard chính", "Thống kê chuyên sâu", "Hiệu quả từng SP"]

    # Conditionally add Scraper tab if data exists
    if "scraped_df" in st.session_state and not st.session_state.scraped_df.empty:
        available_tabs.append("🌐 Dữ liệu đối thủ")
        captions.append("Kết quả cào từ Lazada")

    tab_option = st.radio(
        "Chọn giao diện phân tích:",
        available_tabs,
        captions=captions,
        label_visibility="collapsed",
        key="main_tabs"
    )

    st.markdown("---", unsafe_allow_html=True)
    st.caption(f"© {datetime.now().year} Lazada Analytics")
    st.caption(f"Phiên bản 2.6 | {datetime.now().strftime('%d/%m/%Y')}")


# === MAIN APPLICATION AREA ===

st.markdown('<h1 class="main-title animate-fadeIn">📦 Bảng điều khiển Phân tích Đơn hàng Lazada</h1>', unsafe_allow_html=True)

# Check if data is loaded before showing filters and analysis
if not st.session_state.data_loaded or st.session_state.df.empty:
    st.info("👋 Chào mừng! Vui lòng tải lên file Excel báo cáo đơn hàng ở thanh bên trái để bắt đầu phân tích.")
    st.stop() # Stop execution if no data

# Use the processed data from session state
df = st.session_state.df
date_col = st.session_state.date_col # Get the primary date column

# --- Filters ---
st.markdown('<div class="filter-section animate-fadeIn">', unsafe_allow_html=True)
st.markdown('<h3>🔎 Bộ lọc dữ liệu</h3>', unsafe_allow_html=True)

f_col1, f_col2, f_col3 = st.columns([1.5, 1, 1]) # Adjust column ratios

# Filter: Date Range
with f_col1:
    if date_col and date_col in df.columns:
        try: # Add try-except for robust date handling
            min_date_val = pd.to_datetime(df[date_col].min()).date()
            max_date_val = pd.to_datetime(df[date_col].max()).date()

            # Handle case where min_date > max_date or NaT
            if pd.isna(min_date_val) or pd.isna(max_date_val):
                 min_date_val = datetime.now().date() - pd.Timedelta(days=30)
                 max_date_val = datetime.now().date()
            elif min_date_val > max_date_val:
                min_date_val, max_date_val = max_date_val, min_date_val # Swap

            date_range_key = "date_filter_range"
            # Initialize if not set
            if date_range_key not in st.session_state:
                 st.session_state[date_range_key] = (min_date_val, max_date_val)

            selected_date_range = st.date_input(
                f"📅 Khoảng thời gian ({date_col})",
                value=st.session_state[date_range_key],
                min_value=min_date_val,
                max_value=max_date_val,
                format="DD/MM/YYYY",
                key=date_range_key # Use the key here
            )
            if len(selected_date_range) == 2:
                start_date_filter, end_date_filter = pd.to_datetime(selected_date_range[0]), pd.to_datetime(selected_date_range[1])
            else: # Default to full range if selection is incomplete
                start_date_filter, end_date_filter = pd.to_datetime(min_date_val), pd.to_datetime(max_date_val)
        except Exception as date_err:
             st.warning(f"Lỗi lọc ngày: {date_err}")
             start_date_filter, end_date_filter = None, None
    else:
        st.caption("Không có cột ngày hợp lệ để lọc.")
        start_date_filter, end_date_filter = None, None

# Filter: Product
with f_col2:
    if "Sản Phẩm" in df.columns:
        unique_products = ["Tất cả"] + sorted([str(x) for x in df["Sản Phẩm"].dropna().unique()], key=str.lower)
        selected_product = st.selectbox("🏷️ Sản phẩm", unique_products, index=0, key="product_filter")
    else:
        selected_product = "Tất cả"
        st.caption("Thiếu cột 'Sản Phẩm'.")

# Filter: Order Status
with f_col3:
    if "Trạng thái" in df.columns:
        unique_statuses = ["Tất cả"] + sorted([str(x) for x in df["Trạng thái"].dropna().unique()], key=str.lower)
        selected_status = st.selectbox("🚦 Trạng thái", unique_statuses, index=0, key="status_filter")
    else:
        selected_status = "Tất cả"
        st.caption("Thiếu cột 'Trạng thái'.")


# --- Apply Filters ---
filtered_df = df.copy() # Start with the full processed dataframe

# Apply date filter
if date_col and start_date_filter and end_date_filter:
    try:
        filtered_df = filtered_df[
            (filtered_df[date_col] >= start_date_filter) &
            (filtered_df[date_col] <= end_date_filter)
        ]
    except TypeError as e:
         st.error(f"Lỗi kiểu dữ liệu khi lọc ngày: {e}. Đảm bảo cột '{date_col}' là kiểu ngày tháng.")


# Apply product filter
if selected_product != "Tất cả" and "Sản Phẩm" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["Sản Phẩm"] == selected_product]

# Apply status filter
if selected_status != "Tất cả" and "Trạng thái" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["Trạng thái"] == selected_status]

# --- Advanced Filters (Inside Expander) ---
with st.expander("🔧 Bộ lọc nâng cao", expanded=False):
    adv_f_col1, adv_f_col2 = st.columns(2)

    # Filter: Selling Price Range
    with adv_f_col1:
        price_col = "Số tiền bán trên lazada"
        if price_col in df.columns and pd.api.types.is_numeric_dtype(df[price_col]):
            min_price = float(df[price_col].min())
            max_price = float(df[price_col].max())
            if max_price > min_price:
                 selected_price_range = st.slider(
                    f"💰 Khoảng {price_col} (VND)",
                    min_value=min_price, max_value=max_price,
                    value=(min_price, max_price), # Default to full range
                    step=max(1.0, (max_price - min_price) // 100), # Dynamic step
                    format="%d VND",
                    key="adv_price_filter"
                )
                 # Apply filter
                 filtered_df = filtered_df[
                    (filtered_df[price_col] >= selected_price_range[0]) &
                    (filtered_df[price_col] <= selected_price_range[1])
                ]
            else:
                 st.caption(f"{price_col} cố định.")
        else:
            st.caption(f"Thiếu cột số '{price_col}'.")

    # Filter: Quantity Range
    with adv_f_col2:
        qty_col = "Số lượng"
        if qty_col in df.columns and pd.api.types.is_numeric_dtype(df[qty_col]):
            min_qty = int(df[qty_col].min())
            max_qty = int(df[qty_col].max())
            if max_qty > min_qty:
                selected_quantity_range = st.slider(
                    f"🔢 Khoảng {qty_col}",
                    min_value=min_qty, max_value=max_qty,
                    value=(min_qty, max_qty), # Default full range
                    step=1,
                    key="adv_quantity_filter"
                )
                 # Apply filter
                filtered_df = filtered_df[
                    (filtered_df[qty_col] >= selected_quantity_range[0]) &
                    (filtered_df[qty_col] <= selected_quantity_range[1])
                ]
            else:
                 st.caption(f"{qty_col} cố định.")
        else:
            st.caption(f"Thiếu cột số '{qty_col}'.")

# Store the final filtered dataframe
st.session_state.filtered_df = filtered_df

# Display filter summary and reset button
filter_info_col, reset_button_col = st.columns([4, 1])
with filter_info_col:
    st.caption(f"📊 Hiển thị {len(filtered_df):,} / {len(df):,} đơn hàng sau khi lọc.")
with reset_button_col:
    if st.button("🔄 Reset", key="reset_filters", help="Đặt lại tất cả bộ lọc", use_container_width=True):
        # Reset filter widgets to default values by clearing relevant session state keys
        keys_to_clear = ["date_filter_range", "product_filter", "status_filter", "adv_price_filter", "adv_quantity_filter"]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        # Rerun to apply reset state
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True) # Close filter-section div
st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)


# === Tab Implementation ===
# Use the filtered data from session state
current_filtered_df = st.session_state.filtered_df
date_col = st.session_state.date_col # Ensure date_col is available

# --- Tab: Tổng quan (Overview) ---
if tab_option == "📊 Tổng quan":
    st.markdown('<h1 class="tab-header">📊 Tổng quan hiệu suất</h1>', unsafe_allow_html=True)

    # --- Key Metrics ---
    st.markdown('<h2 class="sub-header">Chỉ số chính</h2>', unsafe_allow_html=True)
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)

    # Prepare data for sparklines/deltas (Using the robust logic from previous fix)
    daily_summary = pd.DataFrame()
    previous_period_avg = pd.Series(dtype=float)

    # Check if necessary columns exist before attempting aggregation
    can_aggregate = (date_col and date_col in current_filtered_df.columns and not current_filtered_df.empty)

    if can_aggregate:
        try:
            agg_dict = {}
            # Use index for orders if 'ma_don_hang' is missing or unreliable
            agg_dict['total_orders'] = (current_filtered_df.index, 'nunique')

            if 'Tổng số tiền người mua thanh toán' in current_filtered_df.columns:
                agg_dict['total_revenue'] = ('Tổng số tiền người mua thanh toán', 'sum')
            if 'Lợi nhuận' in current_filtered_df.columns:
                agg_dict['total_profit'] = ('Lợi nhuận', 'sum')
            if 'Thời gian giao hàng (ngày)' in current_filtered_df.columns and current_filtered_df['Thời gian giao hàng (ngày)'].notna().any():
                 agg_dict['avg_delivery'] = ('Thời gian giao hàng (ngày)', 'mean')

            if agg_dict:
                daily_summary = current_filtered_df.groupby(pd.Grouper(key=date_col, freq='D')).agg(**agg_dict).fillna(0)

                expected_cols = ['total_orders', 'total_revenue', 'total_profit', 'avg_delivery']
                for col in expected_cols:
                    if col not in daily_summary.columns:
                        daily_summary[col] = 0

                if len(daily_summary) > 1:
                    previous_period_avg = daily_summary.iloc[:-1].mean()
                # Handle case with 0 or 1 day later

        except Exception as agg_err:
             st.warning(f"⚠️ Lỗi khi tổng hợp hàng ngày: {agg_err}")
             daily_summary = pd.DataFrame() # Ensure it's empty on error
             previous_period_avg = pd.Series(dtype=float)


    # Display Metrics
    with m_col1:
        total_orders = len(current_filtered_df) # Simple count as fallback
        if 'ma_don_hang' in current_filtered_df.columns: # Use unique order ID if available
             total_orders = current_filtered_df['ma_don_hang'].nunique()
        prev_orders = previous_period_avg.get('total_orders', None)
        display_metric_with_sparkline(
            "Tổng đơn hàng", total_orders, previous_value=prev_orders,
            value_format_func=lambda x: f"{int(x):,}".replace(",", "."), # Integer format
            chart_data=daily_summary['total_orders'].tolist() if not daily_summary.empty else None,
            higher_is_better=True
        )

    with m_col2:
        rev_col = 'Tổng số tiền người mua thanh toán'
        total_revenue = current_filtered_df[rev_col].sum() if rev_col in current_filtered_df.columns else 0
        prev_revenue = previous_period_avg.get('total_revenue', None)
        display_metric_with_sparkline(
            "Tổng doanh thu", total_revenue, previous_value=prev_revenue,
            value_format_func=format_currency,
            chart_data=daily_summary['total_revenue'].tolist() if not daily_summary.empty else None,
            higher_is_better=True
        )

    with m_col3:
        profit_col = 'Lợi nhuận'
        total_profit = current_filtered_df[profit_col].sum() if profit_col in current_filtered_df.columns else 0
        prev_profit = previous_period_avg.get('total_profit', None)
        display_metric_with_sparkline(
            "Tổng lợi nhuận", total_profit, previous_value=prev_profit,
            value_format_func=format_currency,
            chart_data=daily_summary['total_profit'].tolist() if not daily_summary.empty else None,
            higher_is_better=True
        )

    with m_col4:
        delivery_col = "Thời gian giao hàng (ngày)"
        avg_delivery = 0
        if delivery_col in current_filtered_df.columns:
            valid_delivery = current_filtered_df[delivery_col].dropna()
            if not valid_delivery.empty:
                avg_delivery = valid_delivery.mean()
        prev_delivery = previous_period_avg.get('avg_delivery', None)
        display_metric_with_sparkline(
            "Giao hàng TB", avg_delivery, previous_value=prev_delivery,
            value_format_func=lambda x: f"{x:.1f}", unit=" ngày",
            chart_data=daily_summary['avg_delivery'].tolist() if not daily_summary.empty else None,
            higher_is_better=False # Lower is better
        )

    # --- Time Series Charts ---
    st.markdown('<h2 class="sub-header">Xu hướng theo thời gian</h2>', unsafe_allow_html=True)
    ts_col1, ts_col2 = st.columns(2)

    with ts_col1:
        if date_col and rev_col in current_filtered_df.columns:
            fig_revenue_time = plot_time_series(
                current_filtered_df, date_col, rev_col,
                "Doanh thu theo thời gian",
                y_format_func=format_currency, aggregate_func='sum',
                y_axis_label="Doanh thu"
                )
            st.plotly_chart(fig_revenue_time, use_container_width=True)
        else:
            st.info(f"ℹ️ Thiếu dữ liệu '{date_col}' hoặc '{rev_col}' để vẽ biểu đồ.")

    with ts_col2:
         if date_col and profit_col in current_filtered_df.columns:
             fig_profit_time = plot_time_series(
                 current_filtered_df, date_col, profit_col,
                 "Lợi nhuận theo thời gian", color='var(--success)',
                 y_format_func=format_currency, aggregate_func='sum',
                 y_axis_label="Lợi nhuận"
                 )
             st.plotly_chart(fig_profit_time, use_container_width=True)
         else:
             st.info(f"ℹ️ Thiếu dữ liệu '{date_col}' hoặc '{profit_col}' để vẽ biểu đồ.")


    # --- Other Overview Charts ---
    st.markdown('<h2 class="sub-header">Phân bổ chính</h2>', unsafe_allow_html=True)
    dist_col1, dist_col2 = st.columns(2)

    with dist_col1:
         status_col = "Trạng thái"
         if status_col in current_filtered_df.columns and current_filtered_df[status_col].notna().any():
            status_counts = current_filtered_df[status_col].value_counts().reset_index()
            status_counts.columns = [status_col, "Số lượng"]
            fig_status = px.pie(status_counts, values="Số lượng", names=status_col,
                                title="Tỷ lệ trạng thái đơn hàng", hole=0.4,
                                color_discrete_sequence=px.colors.sequential.Oranges_r)
            fig_status.update_traces(textposition='inside', textinfo='percent+label', pull=[0.05] * len(status_counts))
            fig_status.update_layout(title_x=0.5, legend_title_text='Trạng thái',
                                     legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
                                     title_font_size=18)
            st.plotly_chart(fig_status, use_container_width=True)
         else:
             st.info(f"ℹ️ Thiếu dữ liệu '{status_col}'.")

    with dist_col2:
         day_col = "Ngày trong tuần"
         if day_col in current_filtered_df.columns and current_filtered_df[day_col].notna().any():
             day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
             day_map_vn = {'Monday': 'T2', 'Tuesday': 'T3', 'Wednesday': 'T4', 'Thursday': 'T5', 'Friday': 'T6', 'Saturday': 'T7', 'Sunday': 'CN'}
             # Ensure column is string before mapping
             day_counts = current_filtered_df[day_col].astype(str).map(day_map_vn).value_counts().reset_index()
             day_counts.columns = ["day_vn", "Số đơn hàng"]
             # Map the VN names back to the order for sorting
             day_counts['order'] = day_counts['day_vn'].map({v: i for i, k in enumerate(day_map_vn.values())})
             day_counts = day_counts.sort_values('order').drop('order', axis=1)


             fig_day = px.bar(day_counts, x="day_vn", y="Số đơn hàng", title="Đơn hàng theo ngày trong tuần",
                              color="Số đơn hàng", color_continuous_scale=px.colors.sequential.Oranges, text_auto='.2s')
             fig_day.update_traces(textposition='outside')
             fig_day.update_layout(title_x=0.5, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                   coloraxis_showscale=False, xaxis_title="", yaxis_title="Số đơn hàng",
                                   title_font_size=18)
             st.plotly_chart(fig_day, use_container_width=True)
         else:
             st.info(f"ℹ️ Thiếu dữ liệu '{day_col}'.")


# --- Tab: Phân tích chi tiết ---
elif tab_option == "📈 Phân tích chi tiết":
    st.markdown('<h1 class="tab-header">📈 Phân tích chi tiết</h1>', unsafe_allow_html=True)

    det_col1, det_col2 = st.columns(2)
    date_col = st.session_state.date_col # Use consistent date column

    with det_col1:
        # Monthly Revenue Bar Chart
        st.markdown('<h2 class="sub-header">Doanh thu / Lợi nhuận hàng tháng</h2>', unsafe_allow_html=True)
        month_col = "Năm Tháng" # Use the Year-Month column created earlier
        rev_col = "Tổng số tiền người mua thanh toán"
        profit_col = "Lợi nhuận"

        if month_col in current_filtered_df.columns and date_col: # Need date_col for grouping
             monthly_agg = {}
             if rev_col in current_filtered_df.columns: monthly_agg[rev_col] = 'sum'
             if profit_col in current_filtered_df.columns: monthly_agg[profit_col] = 'sum'

             if monthly_agg: # Proceed if at least one column exists
                # Group by the Year-Month column
                revenue_profit_by_month = current_filtered_df.groupby(month_col).agg(monthly_agg).reset_index()

                fig_month = go.Figure()
                # Add Revenue bar
                if rev_col in revenue_profit_by_month.columns:
                    fig_month.add_trace(go.Bar(
                        x=revenue_profit_by_month[month_col],
                        y=revenue_profit_by_month[rev_col],
                        name='Doanh thu', marker_color='var(--primary)',
                        text=revenue_profit_by_month[rev_col],
                        hovertemplate = f'<b>Tháng</b>: %{{x}}<br><b>Doanh thu</b>: %{{y:,.0f}} VND<extra></extra>'
                    ))
                # Add Profit bar (if exists)
                if profit_col in revenue_profit_by_month.columns:
                     fig_month.add_trace(go.Bar(
                        x=revenue_profit_by_month[month_col],
                        y=revenue_profit_by_month[profit_col],
                        name='Lợi nhuận', marker_color='var(--success)',
                        text=revenue_profit_by_month[profit_col],
                        hovertemplate = f'<b>Tháng</b>: %{{x}}<br><b>Lợi nhuận</b>: %{{y:,.0f}} VND<extra></extra>'
                    ))

                fig_month.update_layout(
                    barmode='group', # Group bars side-by-side
                    title="Tổng doanh thu & Lợi nhuận theo tháng",
                    title_x=0.5, xaxis_title="", yaxis_title="Số tiền (VND)",
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                    yaxis_tickformat=",.0f", title_font_size=18
                )
                fig_month.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                st.plotly_chart(fig_month, use_container_width=True)
             else:
                 st.info(f"ℹ️ Thiếu dữ liệu '{rev_col}' hoặc '{profit_col}'.")

        else:
            st.info(f"ℹ️ Thiếu cột '{month_col}' hoặc '{date_col}' để nhóm theo tháng.")


    with det_col2:
         # Distribution of Delivery Time
         st.markdown('<h2 class="sub-header">Phân phối Thời gian giao hàng</h2>', unsafe_allow_html=True)
         delivery_col = "Thời gian giao hàng (ngày)"
         if delivery_col in current_filtered_df.columns and current_filtered_df[delivery_col].notna().any():
             fig_delivery = create_distribution_chart(
                 current_filtered_df.dropna(subset=[delivery_col]), delivery_col,
                 "Phân phối thời gian giao hàng (ngày)",
                 color_sequence=px.colors.sequential.Blues_r) # Use Blue for time/process
             st.plotly_chart(fig_delivery, use_container_width=True)
         else:
             st.info(f"ℹ️ Thiếu dữ liệu '{delivery_col}'.")


    det_col3, det_col4 = st.columns(2)

    with det_col3:
        # Profit Margin Distribution
        st.markdown('<h2 class="sub-header">Phân phối Biên lợi nhuận</h2>', unsafe_allow_html=True)
        margin_col = "Biên lợi nhuận (%)"
        if margin_col in current_filtered_df.columns:
             # Filter out extreme outliers for better visualization if needed
             # q_low = current_filtered_df[margin_col].quantile(0.01)
             # q_hi  = current_filtered_df[margin_col].quantile(0.99)
             # margin_df_filtered = current_filtered_df[(current_filtered_df[margin_col] > q_low) & (current_filtered_df[margin_col] < q_hi)]
             # Or plot all data:
             margin_df_filtered = current_filtered_df.dropna(subset=[margin_col])

             if not margin_df_filtered.empty:
                 fig_margin_dist = create_distribution_chart(
                     margin_df_filtered, margin_col,
                     "Phân phối biên lợi nhuận (%)",
                     color_sequence=px.colors.sequential.Greens_r) # Green for profit margin
                 fig_margin_dist.update_layout(xaxis_ticksuffix="%")
                 st.plotly_chart(fig_margin_dist, use_container_width=True)
             else:
                 st.info(f"ℹ️ Không có dữ liệu hợp lệ cho '{margin_col}' sau khi lọc.")
        else:
            st.info(f"ℹ️ Thiếu dữ liệu '{margin_col}'.")


    with det_col4:
        # Fees Distribution (Example: Shipping Fees)
        st.markdown('<h2 class="sub-header">Phân phối Phí vận chuyển</h2>', unsafe_allow_html=True)
        fee_col = 'Phí vận chuyển'
        if fee_col in current_filtered_df.columns and pd.api.types.is_numeric_dtype(current_filtered_df[fee_col]):
             non_zero_fees = current_filtered_df[current_filtered_df[fee_col] > 0]
             if not non_zero_fees.empty:
                fig_fees = create_distribution_chart(
                    non_zero_fees, fee_col,
                    f"Phân phối {fee_col} (> 0 VND)", is_currency=True,
                    color_sequence=px.colors.sequential.Reds_r) # Red for costs
                st.plotly_chart(fig_fees, use_container_width=True)
             else:
                st.info(f"ℹ️ Không có {fee_col} lớn hơn 0.")
        else:
             st.info(f"ℹ️ Thiếu dữ liệu số cho '{fee_col}'.")

    # --- Correlation Heatmap ---
    st.markdown('<h2 class="sub-header">Tương quan giữa các yếu tố</h2>', unsafe_allow_html=True)
    # Select relevant numeric columns that exist
    potential_corr_cols = [
        "Số tiền bán trên lazada", "Số lượng",
        "Tổng số tiền người mua thanh toán", "Lợi nhuận",
        "Phí vận chuyển", "Phí khuyến mãi do người bán trả cho lazada",
        "Thời gian giao hàng (ngày)", "Biên lợi nhuận (%)"
    ]
    corr_cols = [col for col in potential_corr_cols if col in current_filtered_df.columns and pd.api.types.is_numeric_dtype(current_filtered_df[col])]

    if len(corr_cols) >= 2:
        # Drop rows with NaNs in the selected columns for correlation calculation
        corr_df = current_filtered_df[corr_cols].dropna()
        if len(corr_df) > 1: # Need at least 2 rows for correlation
             corr_matrix = corr_df.corr()
             fig_corr = px.imshow(corr_matrix, text_auto=".2f",
                                aspect="auto", color_continuous_scale=px.colors.diverging.RdBu, # Red-Blue scale
                                title="Ma trận tương quan các yếu tố số",
                                labels=dict(color="Hệ số corr"), zmin=-1, zmax=1) # Set scale from -1 to 1
             fig_corr.update_layout(title_x=0.5, height=500, title_font_size=18)
             fig_corr.update_xaxes(tickangle=-45) # Rotate x-axis labels
             st.plotly_chart(fig_corr, use_container_width=True)
        else:
             st.info("ℹ️ Không đủ dữ liệu (sau khi loại bỏ NaN) để tính tương quan.")

    else:
        st.info("ℹ️ Không đủ các cột số cần thiết để tính ma trận tương quan.")


# --- Tab: Phân tích sản phẩm ---
elif tab_option == "📦 Phân tích sản phẩm":
    st.markdown('<h1 class="tab-header">📦 Phân tích sản phẩm</h1>', unsafe_allow_html=True)

    product_col = "Sản Phẩm"
    qty_col = "Số lượng"
    rev_col = "Tổng số tiền người mua thanh toán"
    profit_col = "Lợi nhuận"
    margin_col = "Biên lợi nhuận (%)"
    price_col = "Số tiền bán trên lazada"
    date_col = st.session_state.date_col

    if product_col not in current_filtered_df.columns:
        st.error(f"❌ Thiếu cột '{product_col}'. Không thể thực hiện phân tích sản phẩm.")
        st.stop()

    # --- Top Products ---
    prod_col1, prod_col2 = st.columns(2)
    with prod_col1:
        st.markdown('<h2 class="sub-header">Top Sản phẩm Bán chạy (SL)</h2>', unsafe_allow_html=True)
        if qty_col in current_filtered_df.columns and pd.api.types.is_numeric_dtype(current_filtered_df[qty_col]):
            top_products_qty = current_filtered_df.groupby(product_col)[qty_col].sum().nlargest(10).reset_index().sort_values(qty_col, ascending=True)
            fig_top_qty = px.bar(top_products_qty, y=product_col, x=qty_col, title="", # Title in sub-header
                             labels={product_col: "", qty_col: "Tổng số lượng bán"},
                             orientation='h', color=qty_col, color_continuous_scale=px.colors.sequential.Oranges, text=qty_col)
            fig_top_qty.update_layout(yaxis_title="", xaxis_title="Số lượng", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False, height=400)
            fig_top_qty.update_traces(textposition='outside', texttemplate='%{text:,}')
            st.plotly_chart(fig_top_qty, use_container_width=True)
        else:
            st.info(f"ℹ️ Thiếu dữ liệu số cho '{qty_col}'.")

    with prod_col2:
        st.markdown('<h2 class="sub-header">Top Sản phẩm Doanh thu cao</h2>', unsafe_allow_html=True)
        if rev_col in current_filtered_df.columns and pd.api.types.is_numeric_dtype(current_filtered_df[rev_col]):
            top_products_rev = current_filtered_df.groupby(product_col)[rev_col].sum().nlargest(10).reset_index().sort_values(rev_col, ascending=True)
            fig_top_rev = px.bar(top_products_rev, y=product_col, x=rev_col, title="",
                                 labels={product_col: "", rev_col: "Tổng doanh thu"},
                                 orientation='h', color=rev_col, color_continuous_scale=px.colors.sequential.Oranges, text=rev_col)
            fig_top_rev.update_layout(yaxis_title="", xaxis_title="Doanh thu (VND)", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False, height=400, xaxis_tickformat=",.0f")
            fig_top_rev.update_traces(textposition='outside', texttemplate='%{text:,.0f}')
            st.plotly_chart(fig_top_rev, use_container_width=True)
        else:
            st.info(f"ℹ️ Thiếu dữ liệu số cho '{rev_col}'.")


    # --- Product Profitability ---
    prod_col3, prod_col4 = st.columns(2)
    with prod_col3:
        st.markdown('<h2 class="sub-header">Top Sản phẩm Lợi nhuận cao</h2>', unsafe_allow_html=True)
        if profit_col in current_filtered_df.columns and pd.api.types.is_numeric_dtype(current_filtered_df[profit_col]):
            profit_by_product = current_filtered_df.groupby(product_col)[profit_col].sum().nlargest(10).reset_index().sort_values(profit_col, ascending=True)
            fig_profit_prod = px.bar(profit_by_product, y=product_col, x=profit_col, title="",
                                     labels={product_col: "", profit_col: "Tổng lợi nhuận"},
                                     orientation='h', color=profit_col, color_continuous_scale=px.colors.sequential.Greens, text=profit_col)
            fig_profit_prod.update_layout(yaxis_title="", xaxis_title="Lợi nhuận (VND)", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False, height=400, xaxis_tickformat=",.0f")
            fig_profit_prod.update_traces(textposition='outside', texttemplate='%{text:,.0f}')
            st.plotly_chart(fig_profit_prod, use_container_width=True)
        else:
            st.info(f"ℹ️ Thiếu dữ liệu số cho '{profit_col}'.")

    with prod_col4:
         st.markdown('<h2 class="sub-header">Top SP Biên lợi nhuận TB cao</h2>', unsafe_allow_html=True)
         if margin_col in current_filtered_df.columns and pd.api.types.is_numeric_dtype(current_filtered_df[margin_col]):
             margin_by_product = current_filtered_df.groupby(product_col)[margin_col].mean().reset_index()
             top_margins = margin_by_product.nlargest(10, margin_col).sort_values(margin_col, ascending=True)
             fig_margin = px.bar(top_margins, y=product_col, x=margin_col, title="",
                                labels={product_col: "", margin_col: "Biên LN TB (%)"},
                                orientation='h', color=margin_col, color_continuous_scale=px.colors.sequential.Greens, text=margin_col)
             fig_margin.update_layout(yaxis_title="", xaxis_title="Biên lợi nhuận (%)", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False, height=400, xaxis_ticksuffix="%")
             fig_margin.update_traces(textposition='outside', texttemplate='%{text:.1f}%')
             st.plotly_chart(fig_margin, use_container_width=True)
         else:
             st.info(f"ℹ️ Thiếu dữ liệu số cho '{margin_col}'.")


    # --- Pareto Analysis (80/20 Rule) ---
    st.markdown('<h2 class="sub-header">Phân tích Pareto (Quy tắc 80/20)</h2>', unsafe_allow_html=True)
    pareto_col1, pareto_col2 = st.columns(2)

    # Pareto by Sales Quantity
    with pareto_col1:
         if qty_col in current_filtered_df.columns and pd.api.types.is_numeric_dtype(current_filtered_df[qty_col]) and current_filtered_df[qty_col].sum() > 0:
            sales_by_product = current_filtered_df.groupby(product_col)[qty_col].sum().sort_values(ascending=False).reset_index()
            sales_by_product["Cumulative %"] = (sales_by_product[qty_col].cumsum() / sales_by_product[qty_col].sum()) * 100

            cutoff_80_idx = sales_by_product[sales_by_product["Cumulative %"] >= 80].index.min()
            num_prods_80 = cutoff_80_idx + 1 if pd.notna(cutoff_80_idx) else len(sales_by_product)
            pct_prods_80 = (num_prods_80 / len(sales_by_product)) * 100 if len(sales_by_product) > 0 else 0
            pareto_title_qty = f"Pareto SL: {num_prods_80} SP ({pct_prods_80:.0f}%) tạo 80% SL"

            fig_pareto_qty = make_subplots(specs=[[{"secondary_y": True}]])
            fig_pareto_qty.add_trace(go.Bar(x=sales_by_product[product_col], y=sales_by_product[qty_col], name="Số lượng", marker_color="var(--primary)"), secondary_y=False)
            fig_pareto_qty.add_trace(go.Scatter(x=sales_by_product[product_col], y=sales_by_product["Cumulative %"], name="Tích lũy %", mode="lines+markers", line=dict(color="var(--primary-dark)")), secondary_y=True)
            fig_pareto_qty.add_hline(y=80, line_dash="dash", line_color="grey", annotation_text="80%", annotation_position="bottom right", secondary_y=True)
            if pd.notna(cutoff_80_idx): # Add vertical line at cutoff
                fig_pareto_qty.add_vline(x=cutoff_80_idx, line_dash="dash", line_color="grey", secondary_y=False)


            fig_pareto_qty.update_layout(
                title=pareto_title_qty, title_font_size=16,
                xaxis_title="", yaxis_title="Số lượng bán",
                yaxis2=dict(title="Tỷ lệ tích lũy (%)", overlaying="y", side="right", range=[0, 101], showgrid=False),
                title_x=0.5, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=450,
                legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5),
                xaxis={'categoryorder':'array', 'categoryarray':sales_by_product[product_col].tolist(), 'tickangle': -90, 'showticklabels': False}, # Hide labels if too many
                 margin=dict(b=50) # Add bottom margin
            )
            st.plotly_chart(fig_pareto_qty, use_container_width=True)
         else:
             st.info(f"ℹ️ Thiếu dữ liệu số cho '{qty_col}' hoặc tổng bằng 0.")

     # Pareto by Revenue
    with pareto_col2:
         if rev_col in current_filtered_df.columns and pd.api.types.is_numeric_dtype(current_filtered_df[rev_col]) and current_filtered_df[rev_col].sum() > 0:
            revenue_by_product = current_filtered_df.groupby(product_col)[rev_col].sum().sort_values(ascending=False).reset_index()
            revenue_by_product["Cumulative %"] = (revenue_by_product[rev_col].cumsum() / revenue_by_product[rev_col].sum()) * 100

            cutoff_80_rev_idx = revenue_by_product[revenue_by_product["Cumulative %"] >= 80].index.min()
            num_prods_80_rev = cutoff_80_rev_idx + 1 if pd.notna(cutoff_80_rev_idx) else len(revenue_by_product)
            pct_prods_80_rev = (num_prods_80_rev / len(revenue_by_product)) * 100 if len(revenue_by_product) > 0 else 0
            pareto_title_rev = f"Pareto DT: {num_prods_80_rev} SP ({pct_prods_80_rev:.0f}%) tạo 80% DT"

            fig_pareto_rev = make_subplots(specs=[[{"secondary_y": True}]])
            fig_pareto_rev.add_trace(go.Bar(x=revenue_by_product[product_col], y=revenue_by_product[rev_col], name="Doanh thu", marker_color="var(--secondary)"), secondary_y=False)
            fig_pareto_rev.add_trace(go.Scatter(x=revenue_by_product[product_col], y=revenue_by_product["Cumulative %"], name="Tích lũy %", mode="lines+markers", line=dict(color="var(--secondary-light)")), secondary_y=True)
            fig_pareto_rev.add_hline(y=80, line_dash="dash", line_color="grey", annotation_text="80%", annotation_position="bottom right", secondary_y=True)
            if pd.notna(cutoff_80_rev_idx): # Add vertical line
                 fig_pareto_rev.add_vline(x=cutoff_80_rev_idx, line_dash="dash", line_color="grey", secondary_y=False)

            fig_pareto_rev.update_layout(
                title=pareto_title_rev, title_font_size=16,
                xaxis_title="", yaxis_title="Doanh thu (VND)", yaxis_tickformat=",.0f",
                yaxis2=dict(title="Tỷ lệ tích lũy (%)", overlaying="y", side="right", range=[0, 101], showgrid=False),
                title_x=0.5, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=450,
                legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5),
                xaxis={'categoryorder':'array', 'categoryarray':revenue_by_product[product_col].tolist(), 'tickangle': -90, 'showticklabels': False},
                 margin=dict(b=50)
            )
            st.plotly_chart(fig_pareto_rev, use_container_width=True)
         else:
             st.info(f"ℹ️ Thiếu dữ liệu số cho '{rev_col}' hoặc tổng bằng 0.")

    # --- Product Sales Over Time (Top 5 - Optional) ---
    # This can be noisy if many products. Pareto is often more insightful.
    # Keep it if desired:
    st.markdown('<h2 class="sub-header">Số lượng bán theo thời gian (Top 5 SP)</h2>', unsafe_allow_html=True)
    if date_col and date_col in current_filtered_df.columns and qty_col in current_filtered_df.columns and pd.api.types.is_numeric_dtype(current_filtered_df[qty_col]):
        # Find top 5 products based on quantity in the filtered dataframe
        top_5_products_filtered = current_filtered_df.groupby(product_col)[qty_col].sum().nlargest(5).index
        sales_over_time_df = current_filtered_df[current_filtered_df[product_col].isin(top_5_products_filtered)]

        # Aggregate weekly or monthly depending on time range
        time_range_days = (pd.to_datetime(current_filtered_df[date_col].max()) - pd.to_datetime(current_filtered_df[date_col].min())).days
        freq = 'W' if time_range_days <= 180 else 'M' # Weekly if <= 6 months, else monthly
        freq_label = "Tuần" if freq == 'W' else "Tháng"

        sales_agg = sales_over_time_df.groupby([pd.Grouper(key=date_col, freq=freq), product_col])[qty_col].sum().reset_index()

        if not sales_agg.empty:
            fig_sales_time = px.line(sales_agg, x=date_col, y=qty_col, color=product_col,
                                    title=f"Số lượng bán theo {freq_label} (Top 5 SP)",
                                    labels={date_col: freq_label, qty_col: "Số lượng bán", product_col: "Sản phẩm"},
                                    markers=True,
                                    color_discrete_sequence=px.colors.qualitative.Vivid) # Use a qualitative palette
            fig_sales_time.update_layout(title_x=0.5, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                         legend_title_text='Sản phẩm', title_font_size=18,
                                         legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5))
            st.plotly_chart(fig_sales_time, use_container_width=True)
        else:
            st.info("ℹ️ Không đủ dữ liệu (sau khi lọc) để hiển thị xu hướng bán hàng của SP.")
    else:
        st.info(f"ℹ️ Thiếu dữ liệu '{date_col}' hoặc '{qty_col}' để vẽ biểu đồ.")



# --- Tab: Dữ liệu đối thủ (Scraped Data) ---
elif tab_option == "🌐 Dữ liệu đối thủ":
    st.markdown('<h1 class="tab-header">🌐 Dữ liệu đối thủ từ Lazada</h1>', unsafe_allow_html=True)
    last_query = st.session_state.get("last_scraped_query")
    scraped_df = st.session_state.get("scraped_df")

    if scraped_df is None or scraped_df.empty:
         st.warning("⚠️ Chưa có dữ liệu cào từ Lazada. Vui lòng sử dụng chức năng 'Cào dữ liệu đối thủ' ở thanh bên trái.")
    else:
        if last_query:
            st.info(f"Hiển thị kết quả cào cho từ khóa: **'{last_query}'** ({len(scraped_df)} sản phẩm)")

        # --- Display DataFrame ---
        st.markdown('<h2 class="sub-header">Danh sách sản phẩm đối thủ</h2>', unsafe_allow_html=True)
        # Prepare display version
        scraped_display = scraped_df.copy()
        # Rename columns for clarity and apply formatting
        rename_map = {
            "Số tiền bán trên lazada": "Giá (VND)",
            "Số lượng bán": "Đã bán (ước tính)", # Your original column name
            "Đánh giá": "Rating (sao)" # Your original column name
        }
        scraped_display = scraped_display.rename(columns=rename_map)

        # Formatting functions for scraped data columns
        if "Giá (VND)" in scraped_display.columns:
             scraped_display["Giá (VND)"] = scraped_display["Giá (VND)"].apply(lambda x: format_currency(x).replace(" VND","")) # Format price
        if "Đã bán (ước tính)" in scraped_display.columns:
             scraped_display["Đã bán (ước tính)"] = scraped_display["Đã bán (ước tính)"].apply(lambda x: f"{int(x):,}".replace(",",".") if pd.notna(x) and x > 0 else "-")
        if "Rating (sao)" in scraped_display.columns:
             scraped_display["Rating (sao)"] = scraped_display["Rating (sao)"].apply(lambda x: f"{x:.1f} ⭐" if pd.notna(x) else "-")
        if 'Link' in scraped_display.columns:
            scraped_display['Link'] = scraped_display['Link'].apply(lambda x: f'<a href="{x}" target="_blank">🔗</a>' if pd.notna(x) else "") # Make link clickable

        # Select and order columns for display
        display_cols_order = ['Sản Phẩm', 'Giá (VND)', 'Đã bán (ước tính)', 'Rating (sao)', 'Link']
        cols_to_show = [col for col in display_cols_order if col in scraped_display.columns]

        st.dataframe(
            scraped_display[cols_to_show],
            hide_index=True,
            column_config={ # Define column widths and potentially other configs
                 "Sản Phẩm": st.column_config.TextColumn("Sản Phẩm", width="large"),
                 "Giá (VND)": st.column_config.TextColumn("Giá (VND)", width="small"),
                 "Đã bán (ước tính)": st.column_config.TextColumn("Đã bán", width="small"),
                 "Rating (sao)": st.column_config.TextColumn("Rating", width="small", help="Đánh giá trung bình"),
                 "Link": st.column_config.LinkColumn("Link", width="small"),
            },
            use_container_width=True
         )
        # Alternative HTML display (less flexible styling):
        # st.markdown(scraped_display[cols_to_show].to_html(escape=False, index=False, classes='dataframe'), unsafe_allow_html=True)


        st.markdown("---")

        # --- Analysis of Scraped Data ---
        st.markdown('<h2 class="sub-header">Phân tích dữ liệu đối thủ</h2>', unsafe_allow_html=True)
        scrape_an_col1, scrape_an_col2 = st.columns(2)

        # Use original column names for analysis before renaming
        price_col_orig = "Số tiền bán trên lazada"
        rating_col_orig = "Đánh giá" # Your original name
        sales_col_orig = "Số lượng bán" # Your original name

        with scrape_an_col1:
            # Price Distribution
            if price_col_orig in scraped_df.columns and scraped_df[price_col_orig].notna().any():
                 fig_scraped_price = create_distribution_chart(scraped_df, price_col_orig, "Phân phối Giá bán Đối thủ", is_currency=True)
                 st.plotly_chart(fig_scraped_price, use_container_width=True)
            else:
                 st.info("ℹ️ Thiếu dữ liệu giá bán đối thủ.")

        with scrape_an_col2:
            # Rating Distribution
            if rating_col_orig in scraped_df.columns and scraped_df[rating_col_orig].notna().any():
                fig_scraped_rating = create_distribution_chart(
                    scraped_df.dropna(subset=[rating_col_orig]), rating_col_orig,
                    "Phân phối Đánh giá Đối thủ", color_sequence=px.colors.sequential.YlOrBr_r)
                fig_scraped_rating.update_layout(xaxis_ticksuffix=" ⭐")
                st.plotly_chart(fig_scraped_rating, use_container_width=True)
            else:
                st.info("ℹ️ Thiếu dữ liệu đánh giá đối thủ.")

        # Scatter Plot: Price vs Rating (if available)
        st.markdown('<h2 class="sub-header">Tương quan Giá và Đánh giá Đối thủ</h2>', unsafe_allow_html=True)
        if price_col_orig in scraped_df.columns and rating_col_orig in scraped_df.columns:
            scatter_scrape_df = scraped_df[[product_col, price_col_orig, rating_col_orig]].dropna()
            if not scatter_scrape_df.empty:
                fig_scrape_scatter = px.scatter(scatter_scrape_df,
                                                x=price_col_orig, y=rating_col_orig,
                                                title="", # Title in header
                                                labels={price_col_orig: "Giá bán (VND)", rating_col_orig: "Đánh giá (Sao)"},
                                                hover_name=product_col, # Show product name on hover
                                                color_discrete_sequence=[px.colors.sequential.Oranges[-3]],
                                                opacity=0.7)
                fig_scrape_scatter.update_layout(title_x=0.5, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_tickformat=",.0f")
                st.plotly_chart(fig_scrape_scatter, use_container_width=True)
            else:
                 st.info("ℹ️ Không đủ dữ liệu giá và đánh giá để vẽ biểu đồ phân tán.")
        else:
            st.info(f"ℹ️ Thiếu cột '{price_col_orig}' hoặc '{rating_col_orig}'.")

# --- Footer ---
st.markdown("---", unsafe_allow_html=True)
st.markdown('<p class="footer">Lazada Analytics Tool | Dữ liệu chỉ mang tính tham khảo.</p>', unsafe_allow_html=True)
