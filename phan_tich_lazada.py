import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time
import io
import numpy as np
import random
# Use Service and ChromeDriverManager to handle the driver automatically
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import matplotlib.pyplot as plt
from scipy import stats
import base64
import os # Needed for environment variable check

# Hàm định dạng tiền tệ tùy chỉnh
def format_currency(value):
    """Formats a number as Vietnamese Dong currency."""
    if pd.isna(value) or not isinstance(value, (int, float)):
        return "0 VND"
    return f"{value:,.0f} VND".replace(",", ".")

# Hàm định dạng phần trăm
def format_percent(value):
    """Formats a number as a percentage string."""
    if pd.isna(value) or not isinstance(value, (int, float)):
        return "0.00%"
    return f"{value:.2f}%"

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="Phân tích đơn hàng Lazada",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# --- CSS Nâng cao ---
# (Giữ nguyên CSS từ mã gốc của bạn)
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
    .css-1d391kg, .css-1wrcr25, .css-1lcbmhc, .css-1l02zno { background-color: var(--bg-sidebar); } /* Target specific sidebar background classes */
    .sidebar .sidebar-content { background-color: var(--bg-sidebar); }
    .st-emotion-cache-16txtl3 { color: #FFFFFF; } /* Sidebar text color */
    .stRadio > label { color: #FFFFFF; } /* Radio button label color in sidebar */
    .stTextInput>label, .stFileUploader>label, .stButton>label, .stRadio>label { color: #e2e8f0; } /* Sidebar widget labels */

    /* Buttons */
    .stButton>button { background-color: var(--primary); color: white; border-radius: 6px; padding: 10px 18px; margin: 8px 0; font-weight: 600; border: none; transition: all 0.3s ease; text-transform: uppercase; letter-spacing: 0.5px; }
    .stButton>button:hover { background-color: var(--primary-light); transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .stButton>button:active { background-color: var(--primary-dark); transform: translateY(0); box-shadow: none; }

    /* Metric Cards */
    .metric-card { background-color: var(--bg-card); padding: 24px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); text-align: center; margin: 12px 0; transition: all 0.3s ease; border-top: 4px solid var(--primary); height: 180px; /* Fixed height */ display: flex; flex-direction: column; justify-content: space-between; }
    .metric-card:hover { transform: translateY(-5px); box-shadow: 0 8px 24px rgba(0,0,0,0.12); }
    .metric-card h2 { font-size: 26px; font-weight: 700; color: var(--primary); margin: 8px 0; line-height: 1.2; }
    .metric-card h4 { font-size: 14px; font-weight: 500; color: var(--text-light); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-delta { font-size: 14px; margin-top: 5px; }
    .metric-chart { width: 100%; height: 35px; margin-top: auto; } /* Pushes chart to bottom */
    .metric-chart img { width: 100%; height: 100%; object-fit: contain; }

    /* Headers */
    .main-title { text-align: center; color: var(--primary); margin-bottom: 30px; font-size: 36px; font-weight: 700; }
    .tab-header { font-size: 32px; font-weight: 700; background: linear-gradient(90deg, var(--primary) 0%, var(--primary-light) 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 24px; text-align: center; padding: 16px 0; }
    .sub-header { font-size: 22px; font-weight: 600; color: var(--primary-dark); margin-top: 32px; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 2px solid var(--primary-light); }

    /* Filter Section */
    .filter-section { background-color: var(--bg-card); padding: 20px; border-radius: 12px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #e9ecef; }
    .filter-section h3 { font-size: 18px; font-weight: 600; color: var(--text-main); margin-bottom: 16px; }

    /* DataFrames */
    .dataframe { width: 100%; border-collapse: collapse; }
    .dataframe th { background-color: var(--primary); color: white; padding: 12px; text-align: left; font-weight: 600; }
    .dataframe td { padding: 10px; border-bottom: 1px solid #ddd; }
    .dataframe tr:nth-child(even) { background-color: #f9f9f9; }
    .dataframe tr:hover { background-color: #f1f1f1; }

    /* Inputs and Selects */
    .stTextInput>div>div>input, .stSelectbox>div>div, .stMultiselect>div>div, .stDateInput>div>div>input { border-radius: 6px !important; border: 1px solid #ced4da !important; padding: 10px !important; background-color: #fff; }
    .stTextInput>div>div>input:focus, .stSelectbox>div>div:focus-within, .stMultiselect>div>div:focus-within, .stDateInput>div>div>input:focus { border-color: var(--primary) !important; box-shadow: 0 0 0 2px rgba(255,98,0,0.2) !important; }
    .stDateInput>div>div>div>button { border: none; background: none; } /* Remove border from date picker button */

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { background-color: var(--bg-card); border-radius: 8px 8px 0 0; padding: 0 20px; border-bottom: 2px solid var(--primary); }
    .stTabs [data-baseweb="tab"] { padding: 12px 24px; font-weight: 600; color: var(--text-light); border-radius: 8px 8px 0 0; }
    .stTabs [aria-selected="true"] { background-color: var(--primary); color: white; border-bottom: none; }

    /* Progress Bar */
    .stProgress > div > div > div > div { background-color: var(--primary); }

    /* Links */
    a { color: var(--secondary); text-decoration: none; }
    a:hover { color: var(--secondary-light); text-decoration: underline; }

    /* Footer */
    .footer { text-align: center; margin-top: 40px; padding: 20px; font-size: 14px; color: var(--text-light); border-top: 1px solid #eee; }

    /* Animations */
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    .animate-fadeIn { animation: fadeIn 0.5s ease-in-out; }

    /* Responsive */
    @media (max-width: 768px) {
        .tab-header { font-size: 24px; }
        .metric-card { padding: 16px; height: auto; min-height: 150px;} /* Adjust height for mobile */
        .metric-card h2 { font-size: 20px; }
        .main-title { font-size: 28px; }
        .stButton>button { padding: 8px 14px; font-size: 14px;}
        .stTabs [data-baseweb="tab"] { padding: 10px 16px; font-size: 14px;}
    }
</style>
""", unsafe_allow_html=True)


# --- Helper Functions ---

# Hàm cào dữ liệu từ Lazada
# @st.cache_data(ttl=3600, show_spinner="Đang cào dữ liệu từ Lazada...")
# Wrapped scrape function to handle caching and spinner display better
def get_scraped_data(search_query, max_retries=3):
    """Wraps the scraping function to manage caching and spinner display."""
    if not search_query:
        return pd.DataFrame()

    # Define cache key based on search query
    cache_key = f"lazada_scrape_{search_query.lower().replace(' ', '_')}"

    # Check cache first
    cached_data = st.session_state.get(cache_key)
    if cached_data is not None:
        st.toast(f"Sử dụng dữ liệu đã cào cho '{search_query}' từ cache.", icon="💾")
        return cached_data

    # If not in cache, scrape
    with st.spinner(f"⏳ Đang cào dữ liệu cho '{search_query}' từ Lazada... Việc này có thể mất vài phút."):
        scraped_df = _scrape_lazada_products_internal(search_query, max_retries)

    if not scraped_df.empty:
        st.session_state[cache_key] = scraped_df # Cache the result
        # Set a timestamp for the cache (optional, for display)
        st.session_state[f"{cache_key}_timestamp"] = datetime.now()
        st.success(f"✅ Cào dữ liệu thành công cho '{search_query}'!")
        st.info(f"🔍 Đã tìm thấy {len(scraped_df)} sản phẩm.")
    else:
        st.error(f"❌ Không tìm thấy sản phẩm nào hoặc lỗi khi cào dữ liệu cho '{search_query}'.")

    return scraped_df

# Internal scraping function (not directly cached with st.cache_data to allow spinner control)
def _scrape_lazada_products_internal(search_query, max_retries=3):
    """Internal function to perform the actual scraping."""
    if not search_query:
        return pd.DataFrame()

    # Check if running in Streamlit Cloud
    # STREAMLIT_CLOUD = os.getenv('STREAMLIT_SHARING_MODE') == 'true'
    STREAMLIT_CLOUD = True # Assume cloud environment for driver setup

    for attempt in range(max_retries):
        driver = None # Initialize driver to None
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920x1080") # Specify window size
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36") # Set user agent directly

            # Set up the WebDriver service
            if STREAMLIT_CLOUD:
                 # For Streamlit Cloud, assume Chrome is available in the path
                 # or configure path if necessary, but webdriver-manager should handle it.
                service = ChromeService(ChromeDriverManager().install())
            else:
                 # Local setup
                service = ChromeService(ChromeDriverManager().install())

            driver = webdriver.Chrome(service=service, options=chrome_options)

            # Deprecated, use options instead:
            # driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})

            url = f"https://www.lazada.vn/catalog/?q={search_query.replace(' ', '+')}&_keyori=ss&from=input&spm=a2o4n.home.search.go.1905e182Qk5B3t"
            driver.get(url)

            # Dynamic wait based on attempt number
            wait_time = random.uniform(15 + attempt * 5, 25 + attempt * 5)
            st.info(f"Đang chờ trang tải (lần {attempt+1}, ~{wait_time:.0f}s)...")
            time.sleep(wait_time)

            # Scroll down more gradually
            scroll_pause_time = 3
            screen_height = driver.execute_script("return window.screen.height;")
            i = 1
            max_scrolls = 5
            scroll_count = 0
            while scroll_count < max_scrolls:
                driver.execute_script(f"window.scrollTo(0, {screen_height * i});")
                i += 1
                scroll_count += 1
                time.sleep(scroll_pause_time)
                # Check if we reached the bottom
                new_height = driver.execute_script("return document.body.scrollHeight")
                last_height = driver.execute_script("return window.pageYOffset + window.innerHeight")
                if last_height >= new_height - 100: # Added buffer
                    st.info("Đã cuộn đến cuối trang.")
                    break
                if scroll_count == max_scrolls:
                     st.info(f"Đã cuộn {max_scrolls} lần.")


            # More specific selector to avoid grabbing unintended divs
            # Inspect the Lazada page to find the most stable container for product items
            product_cards = driver.find_elements(By.CSS_SELECTOR, "div[data-qa-locator='product-item']")
            st.info(f"Tìm thấy {len(product_cards)} thẻ sản phẩm tiềm năng.")

            if not product_cards:
                st.warning(f"Không tìm thấy thẻ sản phẩm nào với selector 'div[data-qa-locator=\"product-item\"]'. Có thể cấu trúc trang đã thay đổi hoặc không có kết quả.")
                # Try an alternative selector if the primary one fails
                product_cards = driver.find_elements(By.CSS_SELECTOR, ".Bm3ON") # Example alternative, needs verification
                if product_cards:
                    st.info(f"Đã thử selector thay thế và tìm thấy {len(product_cards)} thẻ.")
                else:
                    st.warning("Selector thay thế cũng không thành công.")
                    # Take a screenshot for debugging if needed (optional)
                    # driver.save_screenshot(f"debug_scrape_attempt_{attempt+1}.png")
                    # st.image(f"debug_scrape_attempt_{attempt+1}.png")

            data = []
            max_products_to_scrape = 50
            products_scraped_count = 0

            for card in product_cards:
                if products_scraped_count >= max_products_to_scrape:
                    break
                try:
                    # Extract Title and Link
                    try:
                        title_elem = card.find_element(By.CSS_SELECTOR, ".RfADt a")
                        title = title_elem.get_attribute('title') or title_elem.text # Get title attribute first
                        link = title_elem.get_attribute('href')
                        if not title: # Skip if title is empty
                             continue
                    except NoSuchElementException:
                        # Try alternative selector for title if needed
                        # title_elem = card.find_element(By.CSS_SELECTOR, "a.product-title-link") # Example
                        st.warning("Không tìm thấy tiêu đề/link sản phẩm trong một thẻ.")
                        continue # Skip this card if no title/link

                    # Extract Price
                    try:
                        price_elem = card.find_element(By.CSS_SELECTOR, ".ooOxS")
                        price_text = price_elem.text.replace("₫", "").replace(".", "").strip()
                        price = int(price_text) if price_text.isdigit() else 0
                    except (NoSuchElementException, ValueError):
                        price = 0 # Default to 0 if price not found or invalid

                    # Extract Quantity Sold (Handle potential absence)
                    quantity = np.nan # Default to NaN
                    try:
                        # Common selectors for 'sold count'
                        possible_qty_selectors = [
                            "span[class*='sold-count']", # Check for classes containing 'sold-count'
                            "span[data-qa-locator='quantity-sold']", # Original selector
                            "._1cEkb" # Another possible class based on inspection
                        ]
                        for selector in possible_qty_selectors:
                            try:
                                quantity_elem = card.find_element(By.CSS_SELECTOR, selector)
                                quantity_text = quantity_elem.text
                                # Extract numbers more reliably
                                digits = ''.join(filter(str.isdigit, quantity_text))
                                if digits:
                                    quantity = int(digits)
                                    break # Found quantity, exit loop
                            except NoSuchElementException:
                                continue # Try next selector
                    except Exception as qty_err:
                        st.warning(f"Lỗi nhỏ khi lấy số lượng bán: {qty_err}")
                        pass # Continue even if quantity extraction fails minorly


                    # Extract Rating (Handle potential absence)
                    rating = np.nan # Default to NaN
                    try:
                        # Look for score/average rating elements
                        rating_elem = card.find_element(By.CSS_SELECTOR, ".score-average")
                        rating_text = rating_elem.text.strip()
                        if rating_text:
                           rating = float(rating_text)
                    except (NoSuchElementException, ValueError):
                        # Try finding star rating icons if text average is missing
                         try:
                             stars = card.find_elements(By.CSS_SELECTOR, "i.star-icon-full") # Count full stars
                             partial_stars = card.find_elements(By.CSS_SELECTOR, "i.star-icon-half") # Count half stars
                             if stars:
                                 rating = len(stars) + 0.5 * len(partial_stars)
                         except (NoSuchElementException, ValueError):
                             pass # Rating stays NaN if stars also not found

                    # Append data only if title and price are valid
                    if title and price > 0:
                         data.append({
                            "Sản Phẩm": title,
                            "Số tiền bán trên lazada": price,
                            "Số lượng bán (ước tính)": quantity, # Rename column for clarity
                            "Đánh giá (sao)": rating, # Rename column for clarity
                            "Link": link
                        })
                         products_scraped_count += 1

                except Exception as card_err:
                    st.warning(f"Lỗi khi xử lý một thẻ sản phẩm: {str(card_err)}")
                    continue # Move to the next card

            driver.quit() # Ensure driver is closed

            if not data:
                 st.warning(f"Không có dữ liệu sản phẩm hợp lệ nào được trích xuất (lần {attempt+1}).")
                 if attempt < max_retries - 1:
                     st.info("Đang thử lại...")
                     time.sleep(5) # Wait before retrying
                     continue # Go to next attempt
                 else:
                     return pd.DataFrame() # Return empty DF after max retries


            df = pd.DataFrame(data)
            # Drop duplicates based on Title AND Link to be more specific
            df = df.drop_duplicates(subset=["Sản Phẩm", "Link"])
            st.success(f"Hoàn tất cào dữ liệu (lần {attempt+1}). Số sản phẩm duy nhất: {len(df)}")
            return df

        except Exception as e:
            if driver:
                driver.quit() # Ensure driver is closed on error
            if attempt < max_retries - 1:
                st.warning(f"Lỗi nghiêm trọng khi cào dữ liệu (lần {attempt+1}): {str(e)}. Đang thử lại sau 10 giây...")
                time.sleep(10)
            else:
                st.error(f"Lỗi khi cào dữ liệu sau {max_retries} lần thử: {str(e)}")
                st.error("Nguyên nhân có thể do: Kết nối mạng, thay đổi cấu trúc trang Lazada, hoặc bị chặn IP.")
                st.error("Vui lòng thử lại sau hoặc kiểm tra lại từ khóa tìm kiếm.")
                return pd.DataFrame() # Return empty DF on final failure

    return pd.DataFrame() # Should not be reached if logic is correct, but acts as a safeguard

# Hàm hiển thị số liệu dạng thẻ với biểu đồ mini
def display_metric_with_sparkline(label, value, previous_value=None, value_format_func=format_currency, chart_data=None, chart_color="#FF6200", unit="", higher_is_better=True):
    """Displays a metric in a card with optional delta and sparkline."""
    value_str = value_format_func(value) if value_format_func else str(value)
    delta_html = ""

    if previous_value is not None and previous_value != 0 and isinstance(value, (int, float)) and isinstance(previous_value, (int, float)):
        delta_val = value - previous_value
        delta_pct = (delta_val / previous_value) * 100
        delta_str = f"{delta_val:+,.0f}".replace(",", ".") # Format delta value
        delta_pct_str = f"{delta_pct:+.1f}%"

        is_improvement = (delta_val > 0) if higher_is_better else (delta_val < 0)
        is_worse = (delta_val < 0) if higher_is_better else (delta_val > 0)

        color = "var(--success)" if is_improvement else "var(--danger)" if is_worse else "var(--text-light)"
        icon = "▲" if is_improvement else "▼" if is_worse else "●"

        delta_html = f"<div class='metric-delta' style='color:{color};'>{icon} {delta_str} ({delta_pct_str}) so với trước</div>"
    elif previous_value is not None:
         delta_html = f"<div class='metric-delta' style='color:var(--text-light);'>● Không có dữ liệu trước</div>"


    chart_html = "<div class='metric-chart'></div>" # Placeholder
    if chart_data is not None and len(chart_data) > 1:
        try:
            # Normalize data for better visualization in small chart
            norm_data = np.array(chart_data)
            if norm_data.max() > norm_data.min(): # Avoid division by zero if all values are same
                 norm_data = (norm_data - norm_data.min()) / (norm_data.max() - norm_data.min())
            else:
                 norm_data = np.zeros_like(norm_data) # Flat line if all same

            fig, ax = plt.subplots(figsize=(4, 0.6)) # Adjusted figsize for better aspect ratio
            ax.plot(range(len(norm_data)), norm_data, color=chart_color, linewidth=2)
            ax.fill_between(range(len(norm_data)), norm_data, alpha=0.2, color=chart_color)
            ax.set_axis_off()
            fig.patch.set_alpha(0) # Transparent figure background
            ax.patch.set_alpha(0)  # Transparent axes background

            buf = io.BytesIO()
            # Use bbox_inches='tight' and pad_inches=0 to remove padding
            fig.savefig(buf, format='png', transparent=True, bbox_inches='tight', pad_inches=0, dpi=72)
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)
            chart_html = f"<div class='metric-chart'><img src='data:image/png;base64,{img_str}' alt='{label} trend'/></div>"
        except Exception as plot_err:
            st.warning(f"Could not generate sparkline for {label}: {plot_err}")
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


# Hàm tạo biểu đồ phân phối (Histogram hoặc Bar)
def create_distribution_chart(df, column, title, color_sequence=px.colors.sequential.Oranges_r, is_currency=False):
    """Creates a histogram for numeric or bar chart for categorical data."""
    if df is None or column not in df.columns or df[column].isnull().all():
        st.warning(f"Không đủ dữ liệu hợp lệ trong cột '{column}' để vẽ biểu đồ phân phối.")
        return go.Figure() # Return empty figure

    if pd.api.types.is_numeric_dtype(df[column]) and df[column].nunique() > 10: # Use histogram for continuous numeric data
        fig = px.histogram(df, x=column, title=title,
                           color_discrete_sequence=color_sequence,
                           marginal="box", # Add box plot
                           labels={column: column.replace("_", " ").title()},
                           opacity=0.8)
        fig.update_layout(bargap=0.1)
        if is_currency:
             fig.update_xaxes(tickformat="~s") # Use SI units for large currency values
    else: # Use bar chart for categorical or discrete numeric data
        # Ensure column is treated as string for grouping if it's not already
        col_data = df[column].astype(str).value_counts().reset_index()
        col_data.columns = [column, 'Số lượng']
        # Sort by count descending, limit categories if too many
        col_data = col_data.sort_values('Số lượng', ascending=False).head(20)
        fig = px.bar(col_data, y=column, x='Số lượng', title=title,
                     color='Số lượng', color_continuous_scale=color_sequence,
                     text='Số lượng', orientation='h',
                     labels={column: column.replace("_", " ").title()})
        fig.update_traces(textposition='outside')
        fig.update_layout(yaxis={'categoryorder':'total ascending'}) # Show highest bar at top

    fig.update_layout(
        title={'text': title, 'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top', 'font': {'size': 20, 'color': 'var(--text-main)'}},
        xaxis_title_font={'size': 14, 'color': 'var(--text-light)'},
        yaxis_title_font={'size': 14, 'color': 'var(--text-light)'},
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='#EEEEEE'),
        yaxis=dict(showgrid=False), # Hide y grid lines for bar, looks cleaner
        coloraxis_showscale=False # Hide color scale for simpler look
    )
    return fig

# Hàm hiển thị biểu đồ thời gian với xu hướng
def plot_time_series(df, date_col, value_col, title, add_trend=True, color='var(--primary)', y_format_func=None, aggregate_func='sum'):
    """Plots time series data with optional trend line."""
    if df is None or date_col not in df.columns or value_col not in df.columns or df.empty:
         st.warning(f"Không đủ dữ liệu để vẽ biểu đồ '{title}'. Cần cột '{date_col}' và '{value_col}'.")
         return go.Figure()

    # Ensure date column is datetime
    df[date_col] = pd.to_datetime(df[date_col])
    df_agg = df.groupby(pd.Grouper(key=date_col, freq='D'))[value_col].agg(aggregate_func).reset_index() # Aggregate by day
    df_agg = df_agg.dropna(subset=[value_col]) # Remove days with no data

    if df_agg.empty:
        st.warning(f"Không có dữ liệu sau khi tổng hợp theo ngày cho biểu đồ '{title}'.")
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_agg[date_col], y=df_agg[value_col], mode='lines+markers', name=value_col.replace("_", " ").title(),
                             line=dict(color=color, width=2.5), marker=dict(size=6),
                             hovertemplate=f"<b>Ngày</b>: %{{x|%d-%m-%Y}}<br><b>{value_col.replace('_', ' ').title()}</b>: %{{y:,.0f}}<extra></extra>")) # Custom hover

    trend_annotation_text = ""
    if add_trend and len(df_agg) > 2:
        # Calculate trend using numpy for potentially better handling of dates
        x_numeric = df_agg[date_col].apply(lambda date: date.toordinal()) # Convert dates to ordinal numbers
        y = df_agg[value_col].values
        try:
            slope, intercept, r_value, _, _ = stats.linregress(x_numeric, y)
            trend_y = intercept + slope * x_numeric
            fig.add_trace(go.Scatter(x=df_agg[date_col], y=trend_y, mode='lines', name='Xu hướng',
                                     line=dict(color='rgba(209, 71, 0, 0.6)', width=2, dash='dash'), # Darker orange for trend
                                     hoverinfo='skip')) # Don't show hover for trend line

            # Add trend annotation
            trend_direction = "tăng" if slope > 0.01 else "giảm" if slope < -0.01 else "ổn định"
            r_squared = r_value**2
            trend_annotation_text = f"Xu hướng: {trend_direction} (R²={r_squared:.2f})"
            # Position annotation near the end of the trend line
            fig.add_annotation(
                x=df_agg[date_col].iloc[-1], y=trend_y[-1],
                text=trend_annotation_text, showarrow=True, arrowhead=1,
                font=dict(size=11, color="#333"), align="left",
                bgcolor="rgba(255, 255, 255, 0.7)", bordercolor=color, borderwidth=1, borderpad=4,
                ax=30, ay=-30 # Adjust arrow position
            )
        except ValueError as linreg_err:
            st.warning(f"Không thể tính đường xu hướng cho '{title}': {linreg_err}")


    yaxis_title = value_col.replace("_", " ").title()
    yaxis_config = dict(
        title=yaxis_title,
        showgrid=True, gridwidth=1, gridcolor='#EEEEEE',
        title_font={'size': 14, 'color': 'var(--text-light)'}
    )
    if y_format_func == format_currency:
         yaxis_config['tickprefix'] = "" # Let Plotly handle currency formatting if possible
         yaxis_config['ticksuffix'] = " VND"
         yaxis_config['separatethousands'] = True
    elif y_format_func:
         # Apply custom formatting if needed (Plotly's tickformat might be sufficient)
         pass

    fig.update_layout(
        title={'text': title, 'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top', 'font': {'size': 20, 'color': 'var(--text-main)'}},
        xaxis_title="Ngày", yaxis=yaxis_config,
        xaxis_title_font={'size': 14, 'color': 'var(--text-light)'},
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='#EEEEEE', tickformat='%d-%m-%Y'),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=50, r=50, t=80, b=50) # Adjust margins
    )

    return fig

# --- Data Loading and Processing Function ---
def load_and_process_data(uploaded_file):
    """Loads data from uploaded Excel and performs cleaning and feature engineering."""
    try:
        df = pd.read_excel(uploaded_file)
        st.session_state.raw_df = df.copy() # Store raw df if needed later

        # --- Data Cleaning ---
        # 1. Standardize column names: lower case, replace spaces/special chars with underscore
        original_columns = df.columns.tolist()
        df.columns = df.columns.str.strip().str.lower()
        df.columns = df.columns.str.replace(" ₫", "", regex=False)
        df.columns = df.columns.str.replace(r"[.\(\)\/]", "", regex=True) # Remove .,() /
        df.columns = df.columns.str.replace(r"\s+", "_", regex=True) # Replace spaces with _
        df.columns = df.columns.str.replace("đ", "d", regex=False) # Replace Vietnamese d
        # Specific renames if needed (example)
        df = df.rename(columns={
            "so_tien_ban_tren_lazada": "gia_ban_lazada",
            "tong_so_tien_nguoi_ban_nhan_duoc_thanh_toan": "tien_nhan_duoc",
            "tong_so_tien_nguoi_mua_thanh_toan": "doanh_thu_khach_tra",
            "phi_khuyen_mai_do_nguoi_ban_tra_cho_lazada": "phi_khuyen_mai",
            "loi_do_can_nang_tru_cho_nha_ban_hang": "phi_can_nang",
            "giam_gia_tu_lazada_cho_nguoi_mua": "lazada_giam_gia",
            "phi_xu_ly_don_hang": "phi_xu_ly",
            "san_pham": "san_pham" # Ensure product name column is consistent
        })
        cleaned_columns = df.columns.tolist()
        st.session_state.column_mapping = dict(zip(original_columns, cleaned_columns))

        # 2. Identify and Convert Data Types
        date_cols = [col for col in df.columns if "ngay" in col]
        for col in date_cols:
            # Try multiple date formats
            df[col] = pd.to_datetime(df[col], format="%d/%m/%Y", errors='coerce')
            if df[col].isnull().any(): # If first format failed, try another
                df[col] = pd.to_datetime(df[col], errors='coerce') # Let pandas infer

        # Identify potential numeric columns based on keywords and attempt conversion
        potential_numeric_cols = [
            'gia_ban_lazada', 'tien_nhan_duoc', 'doanh_thu_khach_tra',
            'phi_van_chuyen', 'phi_khuyen_mai', 'phi_can_nang',
            'lazada_giam_gia', 'phi_xu_ly', 'so_luong'
        ]
        # Add any other columns that look like numbers but might be objects
        for col in df.select_dtypes(include='object').columns:
            if df[col].astype(str).str.match(r'^-?\d+(\.\d+)?$').all(): # Check if all non-null values look numeric
                if col not in potential_numeric_cols:
                    potential_numeric_cols.append(col)

        for col in potential_numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Ensure 'so_luong' (quantity) is integer if present
        if 'so_luong' in df.columns:
            df['so_luong'] = df['so_luong'].astype(int)

        # --- Feature Engineering ---
        # Basic Date Features
        date_col_to_use = None
        if "ngay_mua_hang" in df.columns and df["ngay_mua_hang"].notna().any():
            date_col_to_use = "ngay_mua_hang"
        elif "ngay_tao_don" in df.columns and df["ngay_tao_don"].notna().any():
             date_col_to_use = "ngay_tao_don" # Fallback date column
        # Add more fallbacks if necessary

        if date_col_to_use:
            df[date_col_to_use] = pd.to_datetime(df[date_col_to_use]) # Ensure it's datetime
            df["thang_mua"] = df[date_col_to_use].dt.strftime("%Y-%m")
            df["quy_mua"] = df[date_col_to_use].dt.to_period("Q").astype(str)
            df["ngay_trong_tuan"] = df[date_col_to_use].dt.day_name()
            df["nam_mua"] = df[date_col_to_use].dt.year
            df["tuan_mua"] = df[date_col_to_use].dt.strftime("%Y-%U") # Year-Week Number
            st.session_state.date_col = date_col_to_use # Store the primary date column used
        else:
             st.warning("⚠️ Không tìm thấy cột ngày chính ('ngay_mua_hang' hoặc 'ngay_tao_don'). Các phân tích theo thời gian sẽ bị hạn chế.")
             st.session_state.date_col = None


        # Delivery Time
        if date_col_to_use and "ngay_nhan_duoc" in df.columns and df["ngay_nhan_duoc"].notna().any():
            df["ngay_nhan_duoc"] = pd.to_datetime(df["ngay_nhan_duoc"])
            # Calculate difference only for valid date pairs
            valid_dates_mask = df[date_col_to_use].notna() & df["ngay_nhan_duoc"].notna()
            df.loc[valid_dates_mask, "thoi_gian_giao_hang_ngay"] = (df.loc[valid_dates_mask, "ngay_nhan_duoc"] - df.loc[valid_dates_mask, date_col_to_use]).dt.days
            # Handle potential negative delivery times (maybe return?) - set to 0 or NaN
            df.loc[df["thoi_gian_giao_hang_ngay"] < 0, "thoi_gian_giao_hang_ngay"] = 0

        # Financial Metrics (Check required columns exist)
        required_profit_cols = ["tien_nhan_duoc", "gia_ban_lazada"]
        if all(col in df.columns for col in required_profit_cols):
            # Simple Profit (Seller Received - Listed Price) - This might not be true profit
            # A better profit might be: tien_nhan_duoc - COGS (if available)
            # Using available data:
            df["loi_nhuan_tam_tinh"] = df["tien_nhan_duoc"] - df["gia_ban_lazada"] # Or adjust based on actual cost structure

            # Margin based on selling price
            # Use np.where to avoid division by zero
            df["bien_loi_nhuan_pct"] = np.where(
                df["gia_ban_lazada"] != 0,
                (df["loi_nhuan_tam_tinh"] / df["gia_ban_lazada"]) * 100,
                0 # Set margin to 0 if selling price is 0
            )
            # Handle potential infinite values if needed, though the where clause should prevent it
            df["bien_loi_nhuan_pct"] = df["bien_loi_nhuan_pct"].replace([np.inf, -np.inf], 0).fillna(0)
        else:
            missing_cols = [col for col in required_profit_cols if col not in df.columns]
            st.warning(f"⚠️ Không thể tính lợi nhuận. Thiếu các cột: {', '.join(missing_cols)}")

        # Calculate Total Cost (sum of various fees)
        fee_cols = ['phi_van_chuyen', 'phi_khuyen_mai', 'phi_can_nang', 'phi_xu_ly']
        existing_fee_cols = [col for col in fee_cols if col in df.columns]
        if existing_fee_cols:
             df["tong_chi_phi_san"] = df[existing_fee_cols].sum(axis=1)
        else:
             st.info("ℹ️ Không có các cột phí chi tiết để tính tổng chi phí sàn.")


        # Identify Categorical Columns (excluding dates and high cardinality numerics/text)
        potential_cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        date_cols_found = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
        numeric_cols_found = df.select_dtypes(include=np.number).columns.tolist()

        # Filter out IDs, names, links, and dates from potential categorical cols
        cat_cols = [
            col for col in potential_cat_cols
            if "id" not in col and "link" not in col and "san_pham" not in col # Exclude product name here, handle separately
            and col not in date_cols_found
            and df[col].nunique() < 50 # Consider columns with fewer than 50 unique values as categorical
        ]
        # Add status if it exists and wasn't caught
        if 'trang_thai' in df.columns and 'trang_thai' not in cat_cols:
             cat_cols.append('trang_thai')

        st.session_state.categorical_cols = cat_cols
        st.session_state.numeric_cols = [col for col in numeric_cols_found if col not in date_cols_found and 'id' not in col]
        st.session_state.date_cols = date_cols_found


        return df

    except Exception as e:
        st.error(f"❌ Lỗi nghiêm trọng khi đọc hoặc xử lý file Excel: {str(e)}")
        st.error("Vui lòng kiểm tra định dạng file, tên cột và thử lại.")
        # Provide more specific advice based on common errors if possible
        if "No sheet named" in str(e):
             st.error("Gợi ý: Đảm bảo file Excel có sheet chứa dữ liệu đơn hàng.")
        elif isinstance(e, ValueError) and "time data" in str(e):
             st.error("Gợi ý: Kiểm tra lại định dạng cột ngày tháng. Định dạng mong muốn là DD/MM/YYYY.")
        return pd.DataFrame()


# --- SIDEBAR ---
with st.sidebar:
    st.image("https://laz-img-cdn.alicdn.com/images/ims-web/TB1T7K2d8Cw3KVjSZFuXXcAOpXa.png", width=150, use_column_width=True)
    st.markdown("<h2 style='color: #FFFFFF;'>Lazada Analytics</h2>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("<h3 style='color: #FFFFFF;'>📊 Tải dữ liệu</h3>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Tải lên file báo cáo đơn hàng (.xlsx)", type=["xlsx"], label_visibility="collapsed")

    # Initialize session state variables
    if "df" not in st.session_state:
        st.session_state.df = pd.DataFrame()
    if "filtered_df" not in st.session_state:
        st.session_state.filtered_df = pd.DataFrame()
    if "data_loaded" not in st.session_state:
        st.session_state.data_loaded = False
    if "scraped_df" not in st.session_state:
         st.session_state.scraped_df = pd.DataFrame()


    if uploaded_file is not None:
        if not st.session_state.data_loaded or st.session_state.get("uploaded_filename") != uploaded_file.name:
            with st.spinner("⏳ Đang xử lý dữ liệu..."):
                df_processed = load_and_process_data(uploaded_file)
                if not df_processed.empty:
                    st.session_state.df = df_processed
                    st.session_state.filtered_df = df_processed.copy() # Initialize filtered_df
                    st.session_state.data_loaded = True
                    st.session_state.uploaded_filename = uploaded_file.name
                    st.success("✅ Tải và xử lý file thành công!")
                else:
                    st.session_state.data_loaded = False # Reset if loading failed
                    st.session_state.df = pd.DataFrame()
                    st.session_state.filtered_df = pd.DataFrame()
    elif st.session_state.data_loaded:
        st.info(f"ℹ️ Đang sử dụng dữ liệu từ file: '{st.session_state.uploaded_filename}'")


    # Display data summary if loaded
    if st.session_state.data_loaded and not st.session_state.df.empty:
        df = st.session_state.df # Use the loaded data
        st.info(f"📑 Số đơn hàng: {len(df):,}")
        date_col = st.session_state.get("date_col")
        if date_col and date_col in df.columns:
            try:
                min_d = pd.to_datetime(df[date_col].min())
                max_d = pd.to_datetime(df[date_col].max())
                if pd.notna(min_d) and pd.notna(max_d):
                     st.info(f"📅 Thời gian: {min_d.strftime('%d/%m/%Y')} - {max_d.strftime('%d/%m/%Y')}")
                else:
                     st.warning("⚠️ Không thể xác định khoảng thời gian (thiếu dữ liệu ngày hợp lệ).")
            except Exception:
                 st.warning("⚠️ Lỗi khi xử lý ngày để hiển thị khoảng thời gian.")

        if "san_pham" in df.columns:
            num_products = df["san_pham"].nunique()
            st.info(f"🏷️ Số loại sản phẩm: {num_products}")

        with st.expander("Xem trước dữ liệu đã xử lý"):
            st.dataframe(df.head(), height=200)
        with st.expander("Ánh xạ tên cột (Gốc -> Mới)"):
             if 'column_mapping' in st.session_state:
                 st.json(st.session_state.column_mapping, expanded=False)

    else:
        st.warning("⚠️ Vui lòng tải lên file Excel báo cáo đơn hàng của Lazada.")

    st.markdown("---")

    # --- Lazada Scraping Section ---
    st.markdown("<h3 style='color: #FFFFFF;'>🔍 Cào dữ liệu đối thủ</h3>", unsafe_allow_html=True)
    search_query = st.text_input("Nhập từ khóa/sản phẩm", placeholder="Ví dụ: 'kem chống nắng anessa'", label_visibility="collapsed")

    col1_scrape, col2_scrape = st.columns(2)
    with col1_scrape:
        if st.button("🚀 Cào ngay", key="scrape_now", use_container_width=True, help="Bắt đầu quá trình cào dữ liệu từ Lazada (có thể mất vài phút)."):
            if search_query:
                 scraped_df = get_scraped_data(search_query) # Use the wrapper function
                 if not scraped_df.empty:
                     st.session_state.scraped_df = scraped_df
                     st.session_state.last_scraped_query = search_query
                 else:
                     # Error message handled within get_scraped_data
                     st.session_state.scraped_df = pd.DataFrame() # Ensure it's empty on failure
            else:
                st.warning("⚠️ Vui lòng nhập từ khóa tìm kiếm.")
    with col2_scrape:
         if st.button("🗑️ Xóa Cache", key="clear_scrape_cache", use_container_width=True, help="Xóa dữ liệu đã cào được lưu trong cache."):
             # Find and remove cache entries related to scraping
             keys_to_remove = [k for k in st.session_state if k.startswith("lazada_scrape_")]
             for key in keys_to_remove:
                 del st.session_state[key]
             # Also clear the displayed scraped data
             st.session_state.scraped_df = pd.DataFrame()
             if 'last_scraped_query' in st.session_state:
                 del st.session_state['last_scraped_query']
             st.success("Cache dữ liệu cào đã được xóa.")


    # Display info about cached/last scraped data
    last_query = st.session_state.get("last_scraped_query")
    if last_query:
        cache_key = f"lazada_scrape_{last_query.lower().replace(' ', '_')}"
        cache_time = st.session_state.get(f"{cache_key}_timestamp")
        if cache_time:
             st.caption(f"Dữ liệu cho '{last_query}' được cào lúc: {cache_time.strftime('%H:%M:%S %d/%m/%Y')}")
        else:
             st.caption(f"Hiển thị dữ liệu cào cho: '{last_query}'")

    st.markdown("---")

    # --- Navigation ---
    st.markdown("<h3 style='color: #FFFFFF;'>🧭 Điều hướng</h3>", unsafe_allow_html=True)
    available_tabs = ["📊 Tổng quan", "📈 Phân tích chi tiết", "💰 Tài chính & Lợi nhuận", "📦 Phân tích sản phẩm"]
    if not st.session_state.scraped_df.empty:
        available_tabs.append("🌐 Dữ liệu đối thủ") # Add competitor tab only if data exists

    tab_option = st.radio(
        "Chọn giao diện phân tích:",
        available_tabs,
        captions=["Dashboard chính", "Thống kê chuyên sâu", "Phí, doanh thu, lãi", "Hiệu quả từng SP", "Kết quả cào từ Lazada"][:len(available_tabs)],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.caption(f"© {datetime.now().year} Lazada Analytics Tool")
    st.caption(f"Phiên bản 2.5 | Cập nhật: {datetime.now().strftime('%d/%m/%Y')}")


# === MAIN APPLICATION AREA ===

st.markdown('<h1 class="main-title">📦 Bảng điều khiển Phân tích Đơn hàng Lazada</h1>', unsafe_allow_html=True)

# Check if data is loaded before showing filters and analysis
if not st.session_state.data_loaded or st.session_state.df.empty:
    st.warning("⚠️ Vui lòng tải lên file Excel báo cáo đơn hàng ở thanh bên trái để bắt đầu.")
    st.stop() # Stop execution if no data

# Use the processed data from session state
df = st.session_state.df
date_col = st.session_state.get("date_col") # Get the primary date column identified during processing

# --- Filters ---
st.markdown('<h2 class="sub-header animate-fadeIn">🔎 Bộ lọc dữ liệu</h2>', unsafe_allow_html=True)
with st.container(border=False): # Use container for better grouping
    st.markdown('<div class="filter-section animate-fadeIn">', unsafe_allow_html=True)
    # st.markdown('<h3>Lọc dữ liệu theo tiêu chí</h3>', unsafe_allow_html=True) # Optional header inside

    f_col1, f_col2, f_col3 = st.columns([1.5, 1, 1])

    # Filter: Date Range
    with f_col1:
        if date_col:
             min_date = pd.to_datetime(df[date_col].min()).date() if pd.notna(df[date_col].min()) else datetime.now().date()
             max_date = pd.to_datetime(df[date_col].max()).date() if pd.notna(df[date_col].max()) else datetime.now().date()

             if min_date > max_date: # Handle potential edge case where min > max
                min_date, max_date = max_date, min_date # Swap them

             selected_date_range = st.date_input(
                f"📅 Khoảng thời gian ({date_col.replace('_', ' ').title()})",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                format="DD/MM/YYYY",
                key="date_filter"
            )
             # Ensure selected_date_range has two dates
             if len(selected_date_range) == 2:
                 start_date_filter, end_date_filter = pd.to_datetime(selected_date_range[0]), pd.to_datetime(selected_date_range[1])
             else: # Default to full range if selection is incomplete
                 start_date_filter, end_date_filter = pd.to_datetime(min_date), pd.to_datetime(max_date)
        else:
            st.caption("Không có cột ngày để lọc.")
            start_date_filter, end_date_filter = None, None # No date filtering

    # Filter: Product
    with f_col2:
        if "san_pham" in df.columns:
            unique_products = ["Tất cả"] + sorted([str(x) for x in df["san_pham"].dropna().unique()], key=str.lower)
            selected_product = st.selectbox("🏷️ Sản phẩm", unique_products, index=0, key="product_filter")
        else:
            selected_product = "Tất cả"
            st.caption("Không có cột 'san_pham'.")

    # Filter: Order Status
    with f_col3:
        if "trang_thai" in df.columns:
            unique_statuses = ["Tất cả"] + sorted([str(x) for x in df["trang_thai"].dropna().unique()], key=str.lower)
            selected_status = st.selectbox("🚦 Trạng thái đơn", unique_statuses, index=0, key="status_filter")
        else:
            selected_status = "Tất cả"
            st.caption("Không có cột 'trang_thai'.")


    # --- Advanced Filters ---
    with st.expander("🔧 Bộ lọc nâng cao", expanded=False):
        adv_f_col1, adv_f_col2, adv_f_col3 = st.columns(3)

        # Filter: Selling Price Range
        with adv_f_col1:
            if "gia_ban_lazada" in df.columns:
                min_price = float(df["gia_ban_lazada"].min())
                max_price = float(df["gia_ban_lazada"].max())
                if max_price > min_price: # Only show slider if there's a range
                     selected_price_range = st.slider(
                        "💰 Khoảng giá bán (VND)",
                        min_value=min_price, max_value=max_price,
                        value=(min_price, max_price),
                        step=max(1.0, (max_price - min_price) // 100), # Dynamic step
                        format="%d VND",
                        key="price_filter"
                    )
                else:
                     st.caption(f"Giá bán cố định: {format_currency(min_price)}")
                     selected_price_range = (min_price, max_price)
            else:
                selected_price_range = None
                st.caption("Không có cột 'gia_ban_lazada'.")

        # Filter: Quantity Range
        with adv_f_col2:
            if "so_luong" in df.columns and df["so_luong"].max() > df["so_luong"].min():
                min_qty = int(df["so_luong"].min())
                max_qty = int(df["so_luong"].max())
                selected_quantity_range = st.slider(
                    "🔢 Khoảng số lượng",
                    min_value=min_qty, max_value=max_qty,
                    value=(min_qty, max_qty),
                    step=1,
                    key="quantity_filter"
                )
            else:
                selected_quantity_range = None
                st.caption("Không có cột 'so_luong' hoặc số lượng không đổi.")

        # Filter: Categorical Columns (Dynamic)
        with adv_f_col3:
             cat_cols_filter = st.session_state.get('categorical_cols', [])
             if cat_cols_filter:
                 # Let user choose which categorical column to filter by
                 chosen_cat_col = st.selectbox("Lọc theo:", ["(Không chọn)"] + cat_cols_filter, index=0, key="dynamic_cat_choice")
                 if chosen_cat_col != "(Không chọn)":
                     unique_cat_values = ["Tất cả"] + sorted([str(x) for x in df[chosen_cat_col].dropna().unique()])
                     selected_cat_value = st.selectbox(f"Chọn {chosen_cat_col.replace('_',' ').title()}:", unique_cat_values, index=0, key="dynamic_cat_filter")
                 else:
                     selected_cat_value = "Tất cả"
             else:
                 selected_cat_value = "Tất cả"
                 chosen_cat_col = None # No column chosen
                 st.caption("Không có cột phân loại phù hợp.")


    # --- Apply Filters ---
    filtered_df = df.copy() # Start with the full processed dataframe

    # Apply date filter
    if date_col and start_date_filter and end_date_filter:
        filtered_df = filtered_df[
            (filtered_df[date_col] >= start_date_filter) &
            (filtered_df[date_col] <= end_date_filter)
        ]

    # Apply product filter
    if selected_product != "Tất cả":
        filtered_df = filtered_df[filtered_df["san_pham"] == selected_product]

    # Apply status filter
    if selected_status != "Tất cả" and "trang_thai" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["trang_thai"] == selected_status]

    # Apply price filter
    if selected_price_range and "gia_ban_lazada" in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df["gia_ban_lazada"] >= selected_price_range[0]) &
            (filtered_df["gia_ban_lazada"] <= selected_price_range[1])
        ]

    # Apply quantity filter
    if selected_quantity_range and "so_luong" in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df["so_luong"] >= selected_quantity_range[0]) &
            (filtered_df["so_luong"] <= selected_quantity_range[1])
        ]

    # Apply dynamic categorical filter
    if chosen_cat_col and selected_cat_value != "Tất cả":
         filtered_df = filtered_df[filtered_df[chosen_cat_col] == selected_cat_value]

    # Store the filtered dataframe in session state for use in tabs
    st.session_state.filtered_df = filtered_df

    # Display filter summary and reset button
    filter_info_col, reset_button_col = st.columns([4, 1])
    with filter_info_col:
        st.info(f"📊 Áp dụng bộ lọc: {len(filtered_df):,} / {len(df):,} đơn hàng.")
    with reset_button_col:
        if st.button("🔄 Đặt lại bộ lọc", key="reset_filters", help="Xóa tất cả bộ lọc", use_container_width=True):
            # Reset filter widgets to default values
            st.session_state.date_filter = (min_date, max_date) if date_col else None
            st.session_state.product_filter = "Tất cả"
            st.session_state.status_filter = "Tất cả"
            if selected_price_range: st.session_state.price_filter = (min_price, max_price)
            if selected_quantity_range: st.session_state.quantity_filter = (min_qty, max_qty)
            st.session_state.dynamic_cat_choice = "(Không chọn)"
            st.session_state.dynamic_cat_filter = "Tất cả"
            # Re-run to apply reset state
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True) # Close filter-section div
    st.markdown("<hr style='margin: 25px 0;'>", unsafe_allow_html=True)


# === Tab Implementation ===
# Use the filtered data from session state
current_filtered_df = st.session_state.filtered_df

# --- Tab: Tổng quan (Overview) ---
if tab_option == "📊 Tổng quan":
    st.markdown('<h1 class="tab-header">📊 Tổng quan hiệu suất</h1>', unsafe_allow_html=True)

    # --- Key Metrics ---
    st.markdown('<h2 class="sub-header">Chỉ số chính</h2>', unsafe_allow_html=True)
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)

    # Prepare data for sparklines/deltas (e.g., daily aggregates)
    daily_summary = pd.DataFrame()
    if date_col and not current_filtered_df.empty:
        daily_summary = current_filtered_df.groupby(pd.Grouper(key=date_col, freq='D')).agg(
            total_orders=('ma_don_hang', 'nunique'), # Assuming 'ma_don_hang' is unique order ID
            total_revenue=('doanh_thu_khach_tra', 'sum'),
            total_profit=('loi_nhuan_tam_tinh', 'sum'),
            avg_delivery=('thoi_gian_giao_hang_ngay', 'mean')
        ).fillna(0)
        # Get previous period for delta calculation (e.g., previous day/week/month average)
        # Simple approach: use the average of the period before the last day/entry
        if len(daily_summary) > 1:
             last_day_data = daily_summary.iloc[-1]
             previous_period_avg = daily_summary.iloc[:-1].mean()
        else:
             last_day_data = daily_summary.iloc[0] if not daily_summary.empty else pd.Series(dtype=float)
             previous_period_avg = pd.Series(dtype=float) # No previous data


    with m_col1:
        total_orders = current_filtered_df['ma_don_hang'].nunique() if 'ma_don_hang' in current_filtered_df.columns else len(current_filtered_df)
        prev_orders = previous_period_avg.get('total_orders')
        display_metric_with_sparkline(
            "Tổng số đơn hàng", total_orders,
            previous_value=prev_orders,
            value_format_func=lambda x: f"{x:,.0f}".replace(",", "."), # Custom format for count
            chart_data=daily_summary['total_orders'].tolist() if 'total_orders' in daily_summary else None,
            higher_is_better=True
        )

    with m_col2:
        total_revenue = current_filtered_df["doanh_thu_khach_tra"].sum() if "doanh_thu_khach_tra" in current_filtered_df.columns else 0
        prev_revenue = previous_period_avg.get('total_revenue')
        display_metric_with_sparkline(
            "Tổng doanh thu", total_revenue,
            previous_value=prev_revenue,
            value_format_func=format_currency,
            chart_data=daily_summary['total_revenue'].tolist() if 'total_revenue' in daily_summary else None,
            higher_is_better=True
        )

    with m_col3:
        total_profit = current_filtered_df["loi_nhuan_tam_tinh"].sum() if "loi_nhuan_tam_tinh" in current_filtered_df.columns else 0
        prev_profit = previous_period_avg.get('total_profit')
        display_metric_with_sparkline(
            "Tổng lợi nhuận (tạm tính)", total_profit,
            previous_value=prev_profit,
            value_format_func=format_currency,
            chart_data=daily_summary['total_profit'].tolist() if 'total_profit' in daily_summary else None,
            higher_is_better=True
        )

    with m_col4:
        avg_delivery = current_filtered_df["thoi_gian_giao_hang_ngay"].mean() if "thoi_gian_giao_hang_ngay" in current_filtered_df.columns and current_filtered_df["thoi_gian_giao_hang_ngay"].notna().any() else 0
        prev_delivery = previous_period_avg.get('avg_delivery')
        display_metric_with_sparkline(
            "Thời gian giao TB", avg_delivery,
            previous_value=prev_delivery,
            value_format_func=lambda x: f"{x:.1f}", # Format for days
            unit=" ngày",
            chart_data=daily_summary['avg_delivery'].tolist() if 'avg_delivery' in daily_summary else None,
            higher_is_better=False # Lower delivery time is better
        )

    # --- Time Series Charts ---
    st.markdown('<h2 class="sub-header">Xu hướng theo thời gian</h2>', unsafe_allow_html=True)
    ts_col1, ts_col2 = st.columns(2)

    with ts_col1:
        if date_col and "doanh_thu_khach_tra" in current_filtered_df.columns:
            fig_revenue_time = plot_time_series(current_filtered_df, date_col, "doanh_thu_khach_tra", "Doanh thu theo thời gian", y_format_func=format_currency, aggregate_func='sum')
            st.plotly_chart(fig_revenue_time, use_container_width=True)
        else:
            st.info("ℹ️ Không đủ dữ liệu (Ngày mua/Doanh thu) để vẽ biểu đồ xu hướng doanh thu.")

    with ts_col2:
         if date_col and "loi_nhuan_tam_tinh" in current_filtered_df.columns:
             fig_profit_time = plot_time_series(current_filtered_df, date_col, "loi_nhuan_tam_tinh", "Lợi nhuận (tạm tính) theo thời gian", color='var(--secondary)', y_format_func=format_currency, aggregate_func='sum')
             st.plotly_chart(fig_profit_time, use_container_width=True)
         else:
             st.info("ℹ️ Không đủ dữ liệu (Ngày mua/Lợi nhuận) để vẽ biểu đồ xu hướng lợi nhuận.")


    # --- Other Overview Charts ---
    st.markdown('<h2 class="sub-header">Phân bổ chính</h2>', unsafe_allow_html=True)
    dist_col1, dist_col2 = st.columns(2)

    with dist_col1:
         if "trang_thai" in current_filtered_df.columns:
            status_counts = current_filtered_df["trang_thai"].value_counts().reset_index()
            status_counts.columns = ["Trạng thái", "Số lượng"]
            fig_status = px.pie(status_counts, values="Số lượng", names="Trạng thái", title="Tỷ lệ trạng thái đơn hàng",
                               hole=0.4, color_discrete_sequence=px.colors.sequential.Oranges_r) # Use reversed Oranges
            fig_status.update_traces(textposition='inside', textinfo='percent+label', pull=[0.05] * len(status_counts)) # Pull slices slightly
            fig_status.update_layout(title_x=0.5, legend_title_text='Trạng thái', legend=dict(orientation="h", yanchor="bottom", y=-0.1))
            st.plotly_chart(fig_status, use_container_width=True)
         else:
             st.info("ℹ️ Không có dữ liệu trạng thái đơn hàng để hiển thị.")

    with dist_col2:
         # Example: Distribution of Orders by Day of Week
         if "ngay_trong_tuan" in current_filtered_df.columns:
             day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
             day_counts = current_filtered_df["ngay_trong_tuan"].value_counts().reindex(day_order).reset_index()
             day_counts.columns = ["Ngày trong tuần", "Số đơn hàng"]
             fig_day = px.bar(day_counts, x="Ngày trong tuần", y="Số đơn hàng", title="Số đơn hàng theo ngày trong tuần",
                             color="Số đơn hàng", color_continuous_scale=px.colors.sequential.Oranges, text_auto='.2s')
             fig_day.update_traces(textposition='outside')
             fig_day.update_layout(title_x=0.5, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False)
             st.plotly_chart(fig_day, use_container_width=True)
         else:
             st.info("ℹ️ Không có dữ liệu ngày trong tuần để hiển thị.")


# --- Tab: Phân tích chi tiết ---
elif tab_option == "📈 Phân tích chi tiết":
    st.markdown('<h1 class="tab-header">📈 Phân tích chi tiết</h1>', unsafe_allow_html=True)

    det_col1, det_col2 = st.columns(2)

    with det_col1:
        # Monthly Revenue Bar Chart
        st.markdown('<h2 class="sub-header">Doanh thu hàng tháng</h2>', unsafe_allow_html=True)
        if "thang_mua" in current_filtered_df.columns and "doanh_thu_khach_tra" in current_filtered_df.columns:
            revenue_by_month = current_filtered_df.groupby("thang_mua")["doanh_thu_khach_tra"].sum().reset_index()
            fig_month = px.bar(revenue_by_month, x="thang_mua", y="doanh_thu_khach_tra",
                               title="Tổng doanh thu theo tháng",
                               labels={"thang_mua": "Tháng", "doanh_thu_khach_tra": "Doanh thu"},
                               color="doanh_thu_khach_tra", color_continuous_scale=px.colors.sequential.Oranges, text_auto=True)
            fig_month.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
            fig_month.update_layout(title_x=0.5, xaxis_title="", yaxis_title="Doanh thu (VND)", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False)
            st.plotly_chart(fig_month, use_container_width=True)
        else:
            st.info("ℹ️ Thiếu dữ liệu 'thang_mua' hoặc 'doanh_thu_khach_tra'.")

    with det_col2:
         # Distribution of Delivery Time
         st.markdown('<h2 class="sub-header">Phân phối thời gian giao hàng</h2>', unsafe_allow_html=True)
         if "thoi_gian_giao_hang_ngay" in current_filtered_df.columns and current_filtered_df["thoi_gian_giao_hang_ngay"].notna().any():
             fig_delivery = create_distribution_chart(current_filtered_df.dropna(subset=["thoi_gian_giao_hang_ngay"]), "thoi_gian_giao_hang_ngay", "Phân phối thời gian giao hàng (ngày)")
             st.plotly_chart(fig_delivery, use_container_width=True)
         else:
             st.info("ℹ️ Không có dữ liệu 'thoi_gian_giao_hang_ngay'.")

    det_col3, det_col4 = st.columns(2)

    with det_col3:
        # Scatter plot: Delivery Time vs Revenue/Profit
        st.markdown('<h2 class="sub-header">Thời gian giao hàng vs Doanh thu</h2>', unsafe_allow_html=True)
        scatter_y_col = "doanh_thu_khach_tra" if "doanh_thu_khach_tra" in current_filtered_df.columns else "loi_nhuan_tam_tinh" if "loi_nhuan_tam_tinh" in current_filtered_df.columns else None

        if "thoi_gian_giao_hang_ngay" in current_filtered_df.columns and scatter_y_col:
             temp_df_scatter = current_filtered_df.dropna(subset=["thoi_gian_giao_hang_ngay", scatter_y_col])
             if not temp_df_scatter.empty:
                fig_scatter = px.scatter(temp_df_scatter, x="thoi_gian_giao_hang_ngay", y=scatter_y_col,
                                        title=f"Thời gian giao hàng vs {scatter_y_col.replace('_', ' ').title()}",
                                        labels={"thoi_gian_giao_hang_ngay": "Thời gian giao hàng (ngày)", scatter_y_col: scatter_y_col.replace('_', ' ').title()},
                                        trendline="ols", # Add Ordinary Least Squares trendline
                                        color_discrete_sequence=[px.colors.sequential.Oranges[-2]], # Darker orange
                                        opacity=0.6)
                fig_scatter.update_layout(title_x=0.5, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_scatter, use_container_width=True)
             else:
                 st.info("ℹ️ Không có đủ dữ liệu hợp lệ cho biểu đồ phân tán.")
        else:
            st.info("ℹ️ Thiếu dữ liệu 'thoi_gian_giao_hang_ngay' hoặc cột Y (Doanh thu/Lợi nhuận).")

    with det_col4:
        # Distribution of Order Value
        st.markdown('<h2 class="sub-header">Phân phối giá trị đơn hàng</h2>', unsafe_allow_html=True)
        if "doanh_thu_khach_tra" in current_filtered_df.columns and current_filtered_df["doanh_thu_khach_tra"].notna().any():
             fig_order_value = create_distribution_chart(current_filtered_df, "doanh_thu_khach_tra", "Phân phối giá trị đơn hàng (Doanh thu)", is_currency=True)
             st.plotly_chart(fig_order_value, use_container_width=True)
        else:
             st.info("ℹ️ Không có dữ liệu 'doanh_thu_khach_tra'.")


# --- Tab: Tài chính & Lợi nhuận ---
elif tab_option == "💰 Tài chính & Lợi nhuận":
    st.markdown('<h1 class="tab-header">💰 Tài chính & Lợi nhuận</h1>', unsafe_allow_html=True)

    fin_col1, fin_col2 = st.columns(2)

    with fin_col1:
         # Monthly Profit Trend
         st.markdown('<h2 class="sub-header">Lợi nhuận (tạm tính) hàng tháng</h2>', unsafe_allow_html=True)
         if "thang_mua" in current_filtered_df.columns and "loi_nhuan_tam_tinh" in current_filtered_df.columns:
             profit_by_month = current_filtered_df.groupby("thang_mua")["loi_nhuan_tam_tinh"].sum().reset_index()
             fig_profit_month = px.bar(profit_by_month, x="thang_mua", y="loi_nhuan_tam_tinh",
                                title="Tổng lợi nhuận (tạm tính) theo tháng",
                                labels={"thang_mua": "Tháng", "loi_nhuan_tam_tinh": "Lợi nhuận"},
                                color="loi_nhuan_tam_tinh", color_continuous_scale=px.colors.sequential.Greens, text_auto=True) # Use Greens for profit
             fig_profit_month.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
             fig_profit_month.update_layout(title_x=0.5, xaxis_title="", yaxis_title="Lợi nhuận (VND)", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False)
             st.plotly_chart(fig_profit_month, use_container_width=True)
         else:
             st.info("ℹ️ Thiếu dữ liệu 'thang_mua' hoặc 'loi_nhuan_tam_tinh'.")

    with fin_col2:
         # Fees Distribution (Example: Shipping Fees)
         st.markdown('<h2 class="sub-header">Phân phối Phí Vận Chuyển</h2>', unsafe_allow_html=True)
         fee_col_to_plot = 'phi_van_chuyen'
         if fee_col_to_plot in current_filtered_df.columns and current_filtered_df[fee_col_to_plot].sum() > 0:
             # Exclude zero fees for a more meaningful distribution of actual fees paid
             non_zero_fees = current_filtered_df[current_filtered_df[fee_col_to_plot] > 0]
             if not non_zero_fees.empty:
                fig_fees = create_distribution_chart(non_zero_fees, fee_col_to_plot, f"Phân phối {fee_col_to_plot.replace('_', ' ').title()} (> 0 VND)", is_currency=True, color_sequence=px.colors.sequential.Reds_r) # Use Reds for costs
                st.plotly_chart(fig_fees, use_container_width=True)
             else:
                st.info(f"ℹ️ Không có {fee_col_to_plot.replace('_', ' ').title()} lớn hơn 0.")

         else:
             st.info(f"ℹ️ Không có dữ liệu '{fee_col_to_plot}'.")


    # Correlation Heatmap
    st.markdown('<h2 class="sub-header">Tương quan giữa các yếu tố tài chính</h2>', unsafe_allow_html=True)
    financial_cols = [
        'gia_ban_lazada', 'tien_nhan_duoc', 'doanh_thu_khach_tra',
        'phi_van_chuyen', 'phi_khuyen_mai', 'phi_can_nang', 'phi_xu_ly',
        'lazada_giam_gia', 'loi_nhuan_tam_tinh', 'bien_loi_nhuan_pct', 'tong_chi_phi_san'
    ]
    existing_financial_cols = [col for col in financial_cols if col in current_filtered_df.columns and pd.api.types.is_numeric_dtype(current_filtered_df[col])]

    if len(existing_financial_cols) >= 2:
        corr_matrix = current_filtered_df[existing_financial_cols].corr()
        fig_corr = px.imshow(corr_matrix, text_auto=".2f", # Format correlation values
                             aspect="auto", color_continuous_scale=px.colors.diverging.RdBu, # Red-Blue scale for correlation
                             title="Ma trận tương quan",
                             labels=dict(color="Hệ số corr"))
        fig_corr.update_layout(title_x=0.5, height=600) # Adjust height if needed
        fig_corr.update_xaxes(tickangle=45)
        st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.info("ℹ️ Không đủ các cột tài chính dạng số để tính ma trận tương quan.")


# --- Tab: Phân tích sản phẩm ---
elif tab_option == "📦 Phân tích sản phẩm":
    st.markdown('<h1 class="tab-header">📦 Phân tích sản phẩm</h1>', unsafe_allow_html=True)

    if "san_pham" not in current_filtered_df.columns:
        st.error("❌ Thiếu cột 'san_pham' trong dữ liệu. Không thể thực hiện phân tích sản phẩm.")
        st.stop()

    # --- Top Products ---
    prod_col1, prod_col2 = st.columns(2)
    with prod_col1:
        st.markdown('<h2 class="sub-header">Top Sản phẩm Bán chạy</h2>', unsafe_allow_html=True)
        if "so_luong" in current_filtered_df.columns:
            top_products_qty = current_filtered_df.groupby("san_pham")["so_luong"].sum().nlargest(10).reset_index().sort_values("so_luong", ascending=True)
            fig_top_qty = px.bar(top_products_qty, y="san_pham", x="so_luong", title="Top 10 Sản phẩm Bán chạy nhất (Số lượng)",
                             labels={"san_pham": "Sản phẩm", "so_luong": "Tổng số lượng bán"},
                             orientation='h', color="so_luong", color_continuous_scale=px.colors.sequential.Oranges, text='so_luong')
            fig_top_qty.update_layout(title_x=0.5, yaxis_title="", xaxis_title="Số lượng", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False)
            fig_top_qty.update_traces(textposition='outside')
            st.plotly_chart(fig_top_qty, use_container_width=True)
        else:
            st.info("ℹ️ Thiếu cột 'so_luong'.")

    with prod_col2:
        st.markdown('<h2 class="sub-header">Top Sản phẩm Doanh thu cao</h2>', unsafe_allow_html=True)
        if "doanh_thu_khach_tra" in current_filtered_df.columns:
            top_products_rev = current_filtered_df.groupby("san_pham")["doanh_thu_khach_tra"].sum().nlargest(10).reset_index().sort_values("doanh_thu_khach_tra", ascending=True)
            fig_top_rev = px.bar(top_products_rev, y="san_pham", x="doanh_thu_khach_tra", title="Top 10 Sản phẩm Doanh thu cao nhất",
                                 labels={"san_pham": "Sản phẩm", "doanh_thu_khach_tra": "Tổng doanh thu"},
                                 orientation='h', color="doanh_thu_khach_tra", color_continuous_scale=px.colors.sequential.Oranges, text='doanh_thu_khach_tra')
            fig_top_rev.update_layout(title_x=0.5, yaxis_title="", xaxis_title="Doanh thu (VND)", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False)
            fig_top_rev.update_traces(texttemplate='%{x:,.0f}', textposition='outside')
            st.plotly_chart(fig_top_rev, use_container_width=True)
        else:
            st.info("ℹ️ Thiếu cột 'doanh_thu_khach_tra'.")


    # --- Product Profitability ---
    prod_col3, prod_col4 = st.columns(2)
    with prod_col3:
        st.markdown('<h2 class="sub-header">Top Sản phẩm Lợi nhuận cao</h2>', unsafe_allow_html=True)
        if "loi_nhuan_tam_tinh" in current_filtered_df.columns:
            profit_by_product = current_filtered_df.groupby("san_pham")["loi_nhuan_tam_tinh"].sum().nlargest(10).reset_index().sort_values("loi_nhuan_tam_tinh", ascending=True)
            fig_profit_prod = px.bar(profit_by_product, y="san_pham", x="loi_nhuan_tam_tinh", title="Top 10 Sản phẩm Lợi nhuận cao nhất (Tạm tính)",
                                     labels={"san_pham": "Sản phẩm", "loi_nhuan_tam_tinh": "Tổng lợi nhuận"},
                                     orientation='h', color="loi_nhuan_tam_tinh", color_continuous_scale=px.colors.sequential.Greens, text='loi_nhuan_tam_tinh')
            fig_profit_prod.update_layout(title_x=0.5, yaxis_title="", xaxis_title="Lợi nhuận (VND)", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False)
            fig_profit_prod.update_traces(texttemplate='%{x:,.0f}', textposition='outside')
            st.plotly_chart(fig_profit_prod, use_container_width=True)
        else:
            st.info("ℹ️ Thiếu cột 'loi_nhuan_tam_tinh'.")

    with prod_col4:
         st.markdown('<h2 class="sub-header">Biên lợi nhuận trung bình</h2>', unsafe_allow_html=True)
         if "bien_loi_nhuan_pct" in current_filtered_df.columns:
             # Calculate average margin per product, handling potential NaNs
             margin_by_product = current_filtered_df.groupby("san_pham")["bien_loi_nhuan_pct"].mean().reset_index()
             # Filter out products with zero or NaN average margin if desired, or sort directly
             top_margins = margin_by_product.nlargest(10, "bien_loi_nhuan_pct").sort_values("bien_loi_nhuan_pct", ascending=True)
             fig_margin = px.bar(top_margins, y="san_pham", x="bien_loi_nhuan_pct", title="Top 10 Sản phẩm Biên lợi nhuận TB cao nhất",
                                labels={"san_pham": "Sản phẩm", "bien_loi_nhuan_pct": "Biên LN TB (%)"},
                                orientation='h', color="bien_loi_nhuan_pct", color_continuous_scale=px.colors.sequential.Greens, text='bien_loi_nhuan_pct')
             fig_margin.update_layout(title_x=0.5, yaxis_title="", xaxis_title="Biên lợi nhuận (%)", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False)
             fig_margin.update_traces(texttemplate='%{x:.1f}%', textposition='outside')
             st.plotly_chart(fig_margin, use_container_width=True)
         else:
             st.info("ℹ️ Thiếu cột 'bien_loi_nhuan_pct'.")


    # --- Product Sales Over Time (Top 5) ---
    st.markdown('<h2 class="sub-header">Số lượng bán theo thời gian (Top 5 SP)</h2>', unsafe_allow_html=True)
    if date_col and "so_luong" in current_filtered_df.columns:
        top_5_products = current_filtered_df.groupby("san_pham")["so_luong"].sum().nlargest(5).index
        sales_over_time = current_filtered_df[current_filtered_df["san_pham"].isin(top_5_products)].groupby([pd.Grouper(key=date_col, freq='W'), "san_pham"])["so_luong"].sum().reset_index() # Aggregate weekly

        if not sales_over_time.empty:
            fig_sales_time = px.line(sales_over_time, x=date_col, y="so_luong", color="san_pham",
                                    title="Số lượng bán hàng tuần của 5 sản phẩm hàng đầu",
                                    labels={date_col: "Tuần", "so_luong": "Số lượng bán", "san_pham": "Sản phẩm"},
                                    markers=True,
                                    color_discrete_sequence=px.colors.qualitative.Vivid) # Use a qualitative palette
            fig_sales_time.update_layout(title_x=0.5, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', legend_title_text='Sản phẩm')
            st.plotly_chart(fig_sales_time, use_container_width=True)
        else:
            st.info("ℹ️ Không đủ dữ liệu để hiển thị xu hướng bán hàng của sản phẩm.")
    else:
        st.info("ℹ️ Thiếu dữ liệu Ngày, Số lượng hoặc Sản phẩm.")

    # --- Pareto Analysis (80/20 Rule) ---
    st.markdown('<h2 class="sub-header">Phân tích Pareto (Quy tắc 80/20)</h2>', unsafe_allow_html=True)
    pareto_col1, pareto_col2 = st.columns(2)

    # Pareto by Sales Quantity
    with pareto_col1:
         if "so_luong" in current_filtered_df.columns:
            sales_by_product = current_filtered_df.groupby("san_pham")["so_luong"].sum().sort_values(ascending=False).reset_index()
            sales_by_product["Cumulative %"] = (sales_by_product["so_luong"].cumsum() / sales_by_product["so_luong"].sum()) * 100

            # Find 80% mark
            cutoff_80 = sales_by_product[sales_by_product["Cumulative %"] >= 80].iloc[0] if not sales_by_product[sales_by_product["Cumulative %"] >= 80].empty else None
            num_prods_80 = sales_by_product[sales_by_product["Cumulative %"] <= 80].shape[0] + 1 if cutoff_80 is not None else len(sales_by_product)
            pct_prods_80 = (num_prods_80 / len(sales_by_product)) * 100 if len(sales_by_product) > 0 else 0

            fig_pareto_qty = make_subplots(specs=[[{"secondary_y": True}]])
            # Bar chart for quantity
            fig_pareto_qty.add_trace(go.Bar(x=sales_by_product["san_pham"], y=sales_by_product["so_luong"], name="Số lượng", marker_color="var(--primary)"), secondary_y=False)
            # Line chart for cumulative percentage
            fig_pareto_qty.add_trace(go.Scatter(x=sales_by_product["san_pham"], y=sales_by_product["Cumulative %"], name="Tỷ lệ tích lũy (%)", mode="lines+markers", line=dict(color="var(--primary-dark)")), secondary_y=True)
            # Add 80% line
            fig_pareto_qty.add_hline(y=80, line_dash="dash", line_color="grey", annotation_text="80%", annotation_position="bottom right", secondary_y=True)

            fig_pareto_qty.update_layout(
                title=f"Pareto: Số lượng bán ({num_prods_80} SP ({pct_prods_80:.0f}%) tạo ra 80% SL)",
                xaxis_title="Sản phẩm (Sắp xếp theo số lượng)",
                yaxis_title="Số lượng bán",
                yaxis2=dict(title="Tỷ lệ tích lũy (%)", overlaying="y", side="right", range=[0, 101]),
                title_x=0.5, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5), # Adjust legend position
                xaxis={'categoryorder':'array', 'categoryarray':sales_by_product["san_pham"].tolist(), 'tickangle': -45} # Order x-axis and rotate labels
            )
            st.plotly_chart(fig_pareto_qty, use_container_width=True)
         else:
             st.info("ℹ️ Thiếu cột 'so_luong' cho phân tích Pareto.")

     # Pareto by Revenue
    with pareto_col2:
         if "doanh_thu_khach_tra" in current_filtered_df.columns:
            revenue_by_product = current_filtered_df.groupby("san_pham")["doanh_thu_khach_tra"].sum().sort_values(ascending=False).reset_index()
            revenue_by_product["Cumulative %"] = (revenue_by_product["doanh_thu_khach_tra"].cumsum() / revenue_by_product["doanh_thu_khach_tra"].sum()) * 100

            # Find 80% mark
            cutoff_80_rev = revenue_by_product[revenue_by_product["Cumulative %"] >= 80].iloc[0] if not revenue_by_product[revenue_by_product["Cumulative %"] >= 80].empty else None
            num_prods_80_rev = revenue_by_product[revenue_by_product["Cumulative %"] <= 80].shape[0] + 1 if cutoff_80_rev is not None else len(revenue_by_product)
            pct_prods_80_rev = (num_prods_80_rev / len(revenue_by_product)) * 100 if len(revenue_by_product) > 0 else 0


            fig_pareto_rev = make_subplots(specs=[[{"secondary_y": True}]])
            # Bar chart for revenue
            fig_pareto_rev.add_trace(go.Bar(x=revenue_by_product["san_pham"], y=revenue_by_product["doanh_thu_khach_tra"], name="Doanh thu", marker_color="var(--secondary)"), secondary_y=False)
            # Line chart for cumulative percentage
            fig_pareto_rev.add_trace(go.Scatter(x=revenue_by_product["san_pham"], y=revenue_by_product["Cumulative %"], name="Tỷ lệ tích lũy (%)", mode="lines+markers", line=dict(color="var(--secondary-light)")), secondary_y=True)
             # Add 80% line
            fig_pareto_rev.add_hline(y=80, line_dash="dash", line_color="grey", annotation_text="80%", annotation_position="bottom right", secondary_y=True)

            fig_pareto_rev.update_layout(
                title=f"Pareto: Doanh thu ({num_prods_80_rev} SP ({pct_prods_80_rev:.0f}%) tạo ra 80% DT)",
                xaxis_title="Sản phẩm (Sắp xếp theo doanh thu)",
                yaxis_title="Doanh thu (VND)",
                yaxis2=dict(title="Tỷ lệ tích lũy (%)", overlaying="y", side="right", range=[0, 101]),
                title_x=0.5, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
                xaxis={'categoryorder':'array', 'categoryarray':revenue_by_product["san_pham"].tolist(), 'tickangle': -45}
            )
            st.plotly_chart(fig_pareto_rev, use_container_width=True)
         else:
             st.info("ℹ️ Thiếu cột 'doanh_thu_khach_tra' cho phân tích Pareto.")


# --- Tab: Dữ liệu đối thủ (Scraped Data) ---
elif tab_option == "🌐 Dữ liệu đối thủ":
    st.markdown('<h1 class="tab-header">🌐 Dữ liệu đối thủ từ Lazada</h1>', unsafe_allow_html=True)
    last_query = st.session_state.get("last_scraped_query")
    if last_query:
         st.info(f"Hiển thị kết quả cào cho từ khóa: **'{last_query}'**")

    scraped_df = st.session_state.get("scraped_df")

    if scraped_df is not None and not scraped_df.empty:
        # Display Dataframe with clickable links
        def make_clickable(link):
            return f'<a target="_blank" href="{link}">🔗 Link</a>'
        scraped_display_df = scraped_df.copy()
        if 'Link' in scraped_display_df.columns:
             scraped_display_df['Link'] = scraped_display_df['Link'].apply(make_clickable)
        # Format numeric columns for display
        if 'Số tiền bán trên lazada' in scraped_display_df.columns:
             scraped_display_df['Giá (VND)'] = scraped_display_df['Số tiền bán trên lazada'].apply(lambda x: f"{x:,.0f}".replace(",", "."))
        if 'Số lượng bán (ước tính)' in scraped_display_df.columns:
             scraped_display_df['Đã bán'] = scraped_display_df['Số lượng bán (ước tính)'].apply(lambda x: f"{x:,.0f}".replace(",", ".") if pd.notna(x) else "N/A")
        if 'Đánh giá (sao)' in scraped_display_df.columns:
             scraped_display_df['Rating'] = scraped_display_df['Đánh giá (sao)'].apply(lambda x: f"{x:.1f} ⭐" if pd.notna(x) else "N/A")

        # Select columns to display nicely
        display_cols = ['Sản Phẩm', 'Giá (VND)', 'Đã bán', 'Rating', 'Link']
        final_display_cols = [col for col in display_cols if col in scraped_display_df.columns]

        st.markdown(scraped_display_df[final_display_cols].to_html(escape=False, index=False), unsafe_allow_html=True)
        st.markdown("---")

        # --- Analysis of Scraped Data ---
        st.markdown('<h2 class="sub-header">Phân tích dữ liệu đối thủ</h2>', unsafe_allow_html=True)
        scrape_an_col1, scrape_an_col2 = st.columns(2)

        with scrape_an_col1:
            # Price Distribution
            if "Số tiền bán trên lazada" in scraped_df.columns:
                 fig_scraped_price = create_distribution_chart(scraped_df, "Số tiền bán trên lazada", "Phân phối Giá bán của Đối thủ", is_currency=True)
                 st.plotly_chart(fig_scraped_price, use_container_width=True)
            else:
                 st.info("ℹ️ Không có dữ liệu giá bán.")

        with scrape_an_col2:
            # Rating Distribution
            if "Đánh giá (sao)" in scraped_df.columns and scraped_df["Đánh giá (sao)"].notna().any():
                # Use histogram for ratings as they are somewhat continuous
                fig_scraped_rating = px.histogram(scraped_df.dropna(subset=["Đánh giá (sao)"]), x="Đánh giá (sao)",
                                                  title="Phân phối Đánh giá của Đối thủ",
                                                  nbins=10, color_discrete_sequence=[px.colors.sequential.Oranges[-2]])
                fig_scraped_rating.update_layout(title_x=0.5, bargap=0.1, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_scraped_rating, use_container_width=True)
            else:
                st.info("ℹ️ Không có dữ liệu đánh giá.")

        # Scatter Plot: Price vs Rating (if available)
        if "Số tiền bán trên lazada" in scraped_df.columns and "Đánh giá (sao)" in scraped_df.columns:
            temp_scatter_scrape = scraped_df.dropna(subset=["Số tiền bán trên lazada", "Đánh giá (sao)"])
            if not temp_scatter_scrape.empty:
                fig_scrape_scatter = px.scatter(temp_scatter_scrape,
                                                x="Số tiền bán trên lazada", y="Đánh giá (sao)",
                                                title="Giá bán vs Đánh giá của Đối thủ",
                                                labels={"Số tiền bán trên lazada": "Giá bán (VND)", "Đánh giá (sao)": "Đánh giá (Sao)"},
                                                hover_name="Sản Phẩm", # Show product name on hover
                                                color_discrete_sequence=[px.colors.sequential.Oranges[-3]],
                                                opacity=0.7)
                fig_scrape_scatter.update_layout(title_x=0.5, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_scrape_scatter, use_container_width=True)
            else:
                 st.info("ℹ️ Không đủ dữ liệu giá và đánh giá để vẽ biểu đồ phân tán.")


    else:
        st.warning("⚠️ Chưa có dữ liệu cào từ Lazada. Vui lòng sử dụng chức năng 'Cào dữ liệu đối thủ' ở thanh bên trái.")


# --- Footer ---
st.markdown("---")
st.markdown('<p class="footer">Phát triển bởi AI | Dữ liệu mẫu dùng cho mục đích minh họa.</p>', unsafe_allow_html=True)
