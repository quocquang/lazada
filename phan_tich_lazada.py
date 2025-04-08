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
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import calendar
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import altair as alt
import base64

# Hàm định dạng tiền tệ tùy chỉnh
def format_currency(value):
    if pd.isna(value) or value == 0:
        return "0 VND"
    return f"{value:,.0f} VND".replace(",", ".")

# Hàm định dạng phần trăm
def format_percent(value):
    if pd.isna(value):
        return "0%"
    return f"{value:.2f}%"

# Cấu hình trang
st.set_page_config(
    page_title="Phân tích đơn hàng Lazada", 
    layout="wide", 
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# CSS nâng cao (giữ nguyên như code của bạn)
st.markdown("""
<style>
    :root {
        --primary: #FF6200;
        --primary-light: #FF8A3D;
        --primary-dark: #D14700;
        --secondary: #00A0D6;
        --secondary-light: #33C0F3;
        --text-main: #333333;
        --text-light: #666666;
        --bg-main: #F8F9FA;
        --bg-card: #FFFFFF;
        --bg-sidebar: #1E293B;
        --success: #28A745;
        --warning: #FFC107;
        --danger: #DC3545;
    }
    .main { background-color: var(--bg-main); font-family: 'Roboto', sans-serif; color: var(--text-main); }
    .css-1d391kg, .css-1wrcr25 { background-color: var(--bg-sidebar); }
    .sidebar .sidebar-content { background-color: var(--bg-sidebar); }
    .stButton>button { background-color: var(--primary); color: white; border-radius: 6px; padding: 12px 20px; margin: 8px 0; font-weight: 600; border: none; transition: all 0.3s ease; text-transform: uppercase; letter-spacing: 0.5px; }
    .stButton>button:hover { background-color: var(--primary-light); transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .metric-card { background-color: var(--bg-card); padding: 24px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); text-align: center; margin: 12px 0; transition: all 0.3s ease; border-top: 4px solid var(--primary); }
    .metric-card:hover { transform: translateY(-5px); box-shadow: 0 8px 24px rgba(0,0,0,0.12); }
    .metric-card h2 { font-size: 28px; font-weight: 700; color: var(--primary); margin: 8px 0; }
    .metric-card h4 { font-size: 16px; font-weight: 500; color: var(--text-light); margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
    .tab-header { font-size: 32px; font-weight: 700; background: linear-gradient(90deg, var(--primary) 0%, var(--primary-light) 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 24px; text-align: center; padding: 16px 0; }
    .sub-header { font-size: 22px; font-weight: 600; color: var(--primary-dark); margin-top: 32px; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 2px solid var(--primary-light); }
    .filter-section { background-color: var(--bg-card); padding: 16px; border-radius: 12px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
    .filter-section h3 { font-size: 18px; font-weight: 600; color: var(--text-main); margin-bottom: 16px; }
    .dataframe { width: 100%; border-collapse: collapse; }
    .dataframe th { background-color: var(--primary); color: white; padding: 12px; text-align: left; font-weight: 600; }
    .dataframe td { padding: 10px; border-bottom: 1px solid #ddd; }
    .dataframe tr:nth-child(even) { background-color: #f9f9f9; }
    .dataframe tr:hover { background-color: #f1f1f1; }
    .stTextInput>div>div>input, .stSelectbox>div>div>select, .stMultiselect>div>div>select { border-radius: 6px; border: 1px solid #ddd; padding: 10px; }
    .stTextInput>div>div>input:focus, .stSelectbox>div>div>select:focus, .stMultiselect>div>div>select:focus { border-color: var(--primary); box-shadow: 0 0 0 2px rgba(255,98,0,0.2); }
    .stTabs [data-baseweb="tab-list"] { background-color: var(--bg-card); border-radius: 8px 8px 0 0; padding: 0 20px; }
    .stTabs [data-baseweb="tab"] { padding: 12px 24px; font-weight: 500; }
    .stTabs [aria-selected="true"] { background-color: var(--primary); color: white; border-radius: 8px 8px 0 0; }
    .stProgress > div > div > div > div { background-color: var(--primary); }
    a { color: var(--secondary); text-decoration: none; }
    a:hover { color: var(--secondary-light); text-decoration: underline; }
    .footer { text-align: center; margin-top: 40px; padding: 20px; font-size: 14px; color: var(--text-light); border-top: 1px solid #eee; }
    .custom-progress { height: 10px; border-radius: 5px; margin-top: 5px; }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    .animate-fadeIn { animation: fadeIn 0.5s ease-in-out; }
    @media (max-width: 768px) { .tab-header { font-size: 24px; } .metric-card { padding: 16px; } .metric-card h2 { font-size: 22px; } }
</style>
""", unsafe_allow_html=True)

# Các hàm hỗ trợ (giữ nguyên như code của bạn)
@st.cache_data(ttl=3600, show_spinner=False)
def scrape_lazada_products(search_query, max_retries=3):
    if not search_query:
        return pd.DataFrame()
    for attempt in range(max_retries):
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
            url = f"https://www.lazada.vn/catalog/?q={search_query.replace(' ', '+')}&page=1"
            driver.get(url)
            wait_time = random.randint(20, 30)
            st.toast(f"Đang tải dữ liệu từ Lazada... ({wait_time}s)")
            time.sleep(wait_time)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)
            product_cards = driver.find_elements(By.CSS_SELECTOR, "div[data-qa-locator='product-item']")
            data = []
            for card in product_cards[:50]:
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, ".RfADt a")
                    title = title_elem.text
                    link = title_elem.get_attribute('href')
                    price_elem = card.find_element(By.CSS_SELECTOR, ".ooOxS")
                    price_text = price_elem.text.replace("₫", "").replace(".", "").strip()
                    price = int(price_text) if price_text.isdigit() else 0
                    try:
                        quantity_elem = card.find_element(By.CSS_SELECTOR, "span[data-qa-locator='quantity-sold']")
                        quantity_text = quantity_elem.text.replace("Đã bán", "").strip()
                        quantity = int(''.join(filter(str.isdigit, quantity_text))) if quantity_text else np.nan
                    except NoSuchElementException:
                        quantity = np.nan
                    try:
                        rating_elem = card.find_element(By.CSS_SELECTOR, ".score-average")
                        rating = float(rating_elem.text)
                    except (NoSuchElementException, ValueError):
                        rating = np.nan
                    data.append({"Sản Phẩm": title, "Số tiền bán trên lazada": price, "Số lượng bán": quantity, "Đánh giá": rating, "Link": link})
                except Exception:
                    continue
            driver.quit()
            df = pd.DataFrame(data)
            df = df.drop_duplicates(subset=["Sản Phẩm"])
            return df
        except Exception as e:
            if attempt < max_retries - 1:
                st.warning(f"Lỗi khi cào dữ liệu (lần {attempt+1}): {str(e)}. Đang thử lại...")
                time.sleep(5)
            else:
                st.error(f"Lỗi khi cào dữ liệu sau {max_retries} lần thử: {str(e)}")
                return pd.DataFrame()

def display_metric_with_sparkline(label, value, delta=None, delta_color="normal", chart_data=None, chart_color="#FF6200"):
    if isinstance(value, (int, float)):
        if label.startswith("Tổng số") or "lượng" in label.lower():
            value_str = f"{value:,.0f}".replace(",", ".")
        else:
            value_str = format_currency(value)
    else:
        value_str = str(value)
    delta_html = ""
    if delta:
        color = "green" if delta_color == "good" else "red" if delta_color == "bad" else "gray"
        icon = "↑" if delta_color == "good" else "↓" if delta_color == "bad" else "→"
        delta_html = f"<span style='color:{color};font-size:14px;'>{icon} {delta}</span>"
    chart_html = ""
    if chart_data is not None and len(chart_data) > 1:
        fig, ax = plt.figure(figsize=(3, 0.5)), plt.gca()
        ax.plot(range(len(chart_data)), chart_data, color=chart_color)
        ax.fill_between(range(len(chart_data)), chart_data, alpha=0.2, color=chart_color)
        ax.set_axis_off()
        buf = io.BytesIO()
        fig.savefig(buf, format='png', transparent=True, bbox_inches='tight', pad_inches=0)
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        chart_html = f"<img src='data:image/png;base64,{img_str}' style='width:100%;height:30px;margin-top:5px;'/>"
    st.markdown(f"""
        <div class="metric-card">
            <h4>{label}</h4>
            <h2>{value_str}</h2>
            {delta_html}
            {chart_html}
        </div>
    """, unsafe_allow_html=True)

def create_distribution_chart(df, column, title, color_sequence=None):
    if color_sequence is None:
        color_sequence = px.colors.sequential.Oranges
    if df[column].dtype == 'object':
        value_counts = df[column].value_counts().reset_index()
        value_counts.columns = [column, 'Count']
        fig = px.bar(value_counts, x=column, y='Count', title=title, color=column, color_discrete_sequence=color_sequence, text='Count')
        fig.update_traces(texttemplate='%{text}', textposition='outside')
    else:
        fig = px.histogram(df, x=column, title=title, color_discrete_sequence=color_sequence, marginal="box")
        fig.update_layout(bargap=0.1)
    fig.update_layout(
        title={'text': title, 'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top', 'font': {'size': 22, 'color': '#333333'}},
        xaxis_title_font={'size': 14, 'color': '#666666'}, yaxis_title_font={'size': 14, 'color': '#666666'},
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=True, gridwidth=1, gridcolor='#EEEEEE'),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='#EEEEEE')
    )
    return fig

def plot_time_series(df, date_col, value_col, title, add_trend=True, color='#FF6200'):
    df_sorted = df.sort_values(by=date_col)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_sorted[date_col], y=df_sorted[value_col], mode='lines+markers', name=value_col, line=dict(color=color, width=3), marker=dict(size=8, color=color)))
    if add_trend and len(df_sorted) > 2:
        x = np.arange(len(df_sorted))
        y = df_sorted[value_col].values
        slope, intercept, r_value, _, _ = stats.linregress(x, y)
        trend_y = intercept + slope * x
        fig.add_trace(go.Scatter(x=df_sorted[date_col], y=trend_y, mode='lines', name='Xu hướng', line=dict(color='rgba(255, 98, 0, 0.5)', width=2, dash='dash')))
        trend_direction = "tăng" if slope > 0 else "giảm"
        r_squared = r_value**2
        fig.add_annotation(x=df_sorted[date_col].iloc[-1], y=trend_y[-1], text=f"Xu hướng: {trend_direction} (R² = {r_squared:.2f})", showarrow=True, arrowhead=2, arrowcolor="#FF6200", arrowwidth=2, ax=40, ay=-40, font=dict(size=12, color="#333"), bgcolor="rgba(255, 255, 255, 0.8)", bordercolor="#FF6200", borderwidth=1, borderpad=4)
    fig.update_layout(
        title={'text': title, 'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top', 'font': {'size': 22, 'color': '#333333'}},
        xaxis_title="Ngày", yaxis_title=value_col, xaxis_title_font={'size': 14, 'color': '#666666'}, yaxis_title_font={'size': 14, 'color': '#666666'},
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=True, gridwidth=1, gridcolor='#EEEEEE', tickformat='%d-%m-%Y'),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='#EEEEEE'), hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# Sidebar (giữ nguyên nhưng thêm thông tin phiên bản)
with st.sidebar:
    st.image("https://laz-img-cdn.alicdn.com/images/ims-web/TB1T7K2d8Cw3KVjSZFuXXcAOpXa.png", width=150)
    st.title("Lazada Analytics")
    st.header("📊 Tải dữ liệu")
    uploaded_file = st.file_uploader("Tải lên file Excel (.xlsx)", type=["xlsx"])
    if uploaded_file is not None:
        try:
            with st.spinner("Đang xử lý dữ liệu..."):
                df = pd.read_excel(uploaded_file)
                df.columns = df.columns.str.strip().str.replace(" ₫", "").str.replace(".", "").str.replace("\t", " ")
                date_cols = ["Ngày mua hàng", "Ngày nhận được"]
                for col in date_cols:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], format="%d/%m/%Y", errors="coerce")
                numeric_columns = ["Số tiền bán trên lazada", "Số tiền khách hàng phải chi trả", "Phí vận chuyển", "Phí khuyến mãi do người bán trả cho lazada", "Lỗi do cân nặng trừ cho nhà bán hàng", "Giảm giá từ Lazada cho người mua", "Phí xử lý đơn hàng", "Tổng số tiền người mua thanh toán", "Tổng số tiền người bán nhận được thanh toán", "Số lượng"]
                for col in numeric_columns:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
                if "Ngày mua hàng" in df.columns:
                    df["Tháng mua hàng"] = df["Ngày mua hàng"].dt.strftime("%Y-%m")
                    df["Quý"] = df["Ngày mua hàng"].dt.to_period("Q").astype(str)
                    df["Ngày trong tuần"] = df["Ngày mua hàng"].dt.day_name()
                if all(x in df.columns for x in ["Ngày mua hàng", "Ngày nhận được"]):
                    df["Thời gian giao hàng (ngày)"] = (df["Ngày nhận được"] - df["Ngày mua hàng"]).dt.days
                if all(x in df.columns for x in ["Số tiền bán trên lazada", "Tổng số tiền người bán nhận được thanh toán"]):
                    df["Lợi nhuận"] = df["Tổng số tiền người bán nhận được thanh toán"] - df["Số tiền bán trên lazada"]
                    df["Biên lợi nhuận (%)"] = (df["Lợi nhuận"] / df["Số tiền bán trên lazada"] * 100).replace([np.inf, -np.inf], np.nan).fillna(0)
                st.session_state.df = df
                st.success("✅ Tải file Excel thành công!")
                st.info(f"📑 Số lượng đơn hàng: {len(df):,}")
                if "Ngày mua hàng" in df.columns:
                    start_date = df["Ngày mua hàng"].min().strftime("%d/%m/%Y")
                    end_date = df["Ngày mua hàng"].max().strftime("%d/%m/%Y") 
                    st.info(f"📅 Khoảng thời gian: {start_date} - {end_date}")
                if "Sản Phẩm" in df.columns:
                    num_products = df["Sản Phẩm"].nunique()
                    st.info(f"🏷️ Số lượng sản phẩm: {num_products}")
                with st.expander("Xem trước dữ liệu", expanded=False):
                    st.dataframe(df.head())
        except Exception as e:
            st.error(f"❌ Lỗi khi đọc file Excel: {str(e)}")
    else:
        df = pd.DataFrame()
        if "df" in st.session_state:
            st.info("ℹ️ Đã tải dữ liệu từ phiên trước")
        else:
            st.warning("⚠️ Vui lòng tải lên file Excel để bắt đầu phân tích")
    st.header("🔍 Cào dữ liệu Lazada")
    search_query = st.text_input("Từ khóa tìm kiếm", "Rogaine")
    if st.button("🚀 Cào dữ liệu"):
        if search_query:
            with st.spinner("Đang cào dữ liệu từ Lazada..."):
                scraped_df = scrape_lazada_products(search_query)
                if not scraped_df.empty:
                    st.session_state.scraped_df = scraped_df
                    st.success("✅ Cào dữ liệu thành công!")
                    st.info(f"🔍 Đã tìm thấy {len(scraped_df)} sản phẩm")
                else:
                    st.error("❌ Không tìm thấy sản phẩm nào hoặc lỗi khi cào dữ liệu.")
        else:
            st.warning("⚠️ Vui lòng nhập từ khóa tìm kiếm")
    st.header("📱 Điều hướng")
    tab_option = st.radio("Chọn giao diện", ["📊 Tổng quan", "📈 Phân tích chi tiết", "🔍 Phân tích sản phẩm", "🌐 Dữ liệu từ Lazada"], captions=["Dashboard chính", "Thống kê sâu", "Phân tích theo sản phẩm", "Kết quả cào từ Lazada"])
    st.markdown("---")
    st.caption(f"© 2025 Lazada Analytics | Phiên bản 2.1")
    st.caption(f"Cập nhật: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# Sử dụng dữ liệu từ session state
if "df" in st.session_state:
    df = st.session_state.df
else:
    df = pd.DataFrame()

# Tiêu đề chính
st.markdown('<h1 style="text-align: center; color: #FF6200; margin-bottom: 20px;">📦 Phân tích đơn hàng Lazada</h1>', unsafe_allow_html=True)

# Bộ lọc tổng quát
if not df.empty:
    st.markdown('<h2 class="sub-header">🔎 Bộ lọc dữ liệu</h2>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="filter-section animate-fadeIn">', unsafe_allow_html=True)
        st.markdown('<h3>Lọc dữ liệu theo tiêu chí</h3>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1], gap="medium")
        with col1:
            if "Ngày mua hàng" in df.columns:
                min_date = df["Ngày mua hàng"].min().to_pydatetime()
                max_date = df["Ngày mua hàng"].max().to_pydatetime()
                date_range = st.date_input("Chọn khoảng thời gian", [min_date, max_date], min_value=min_date, max_value=max_date, format="DD/MM/YYYY")
                if len(date_range) == 2:
                    start_date, end_date = date_range
                    filtered_df = df[(df["Ngày mua hàng"] >= pd.to_datetime(start_date)) & (df["Ngày mua hàng"] <= pd.to_datetime(end_date))]
                else:
                    filtered_df = df
            else:
                filtered_df = df
                st.warning("⚠️ Không tìm thấy cột 'Ngày mua hàng' để lọc theo thời gian.")
        with col2:
            if "Sản Phẩm" in df.columns:
                product_options = ["Tất cả"] + sorted(df["Sản Phẩm"].unique().tolist())
                selected_product = st.selectbox("Chọn sản phẩm", product_options, index=0)
                if selected_product != "Tất cả":
                    filtered_df = filtered_df[filtered_df["Sản Phẩm"] == selected_product]
        with col3:
            if "Trạng thái" in df.columns:
                status_options = ["Tất cả"] + sorted(df["Trạng thái"].unique().tolist())
                selected_status = st.selectbox("Chọn trạng thái đơn hàng", status_options, index=0)
                if selected_status != "Tất cả":
                    filtered_df = filtered_df[filtered_df["Trạng thái"] == selected_status]
            else:
                st.info("ℹ️ Không có cột 'Trạng thái' trong dữ liệu.")
        with st.expander("🔧 Bộ lọc nâng cao", expanded=False):
            col4, col5 = st.columns(2)
            with col4:
                if "Số tiền bán trên lazada" in df.columns:
                    min_price = float(df["Số tiền bán trên lazada"].min())
                    max_price = float(df["Số tiền bán trên lazada"].max())
                    price_range = st.slider("Khoảng giá (VND)", min_price, max_price, (min_price, max_price), step=1000.0, format="%.0f")
                    filtered_df = filtered_df[(filtered_df["Số tiền bán trên lazada"] >= price_range[0]) & (filtered_df["Số tiền bán trên lazada"] <= price_range[1])]
            with col5:
                if "Số lượng" in df.columns:
                    min_quantity = int(df["Số lượng"].min())
                    max_quantity = int(df["Số lượng"].max())
                    quantity_range = st.slider("Khoảng số lượng bán", min_quantity, max_quantity, (min_quantity, max_quantity))
                    filtered_df = filtered_df[(filtered_df["Số lượng"] >= quantity_range[0]) & (filtered_df["Số lượng"] <= quantity_range[1])]
        if st.button("🔄 Đặt lại bộ lọc", help="Xóa tất cả bộ lọc và trở về dữ liệu ban đầu"):
            filtered_df = df
            st.success("✅ Đã đặt lại bộ lọc!")
        st.markdown('</ clausdiv>', unsafe_allow_html=True)
        st.info(f"📊 Số lượng đơn hàng sau khi lọc: {len(filtered_df):,}")

    # Các tab giao diện
    if tab_option == "📊 Tổng quan":
        st.markdown('<h1 class="tab-header">Tổng quan</h1>', unsafe_allow_html=True)
        col_metrics = st.columns(4)
        with col_metrics[0]:
            total_orders = len(filtered_df)
            display_metric_with_sparkline("Tổng số đơn hàng", total_orders)
        with col_metrics[1]:
            total_revenue = filtered_df["Tổng số tiền người mua thanh toán"].sum() if "Tổng số tiền người mua thanh toán" in filtered_df.columns else 0
            display_metric_with_sparkline("Tổng doanh thu", total_revenue)
        with col_metrics[2]:
            total_profit = filtered_df["Lợi nhuận"].sum() if "Lợi nhuận" in filtered_df.columns else 0
            display_metric_with_sparkline("Tổng lợi nhuận", total_profit)
        with col_metrics[3]:
            avg_delivery = filtered_df["Thời gian giao hàng (ngày)"].mean() if "Thời gian giao hàng (ngày)" in filtered_df.columns else 0
            display_metric_with_sparkline("Thời gian giao trung bình", f"{avg_delivery:.1f} ngày")
        if "Ngày mua hàng" in filtered_df.columns and "Tổng số tiền người mua thanh toán" in filtered_df.columns:
            revenue_by_date = filtered_df.groupby("Ngày mua hàng")["Tổng số tiền người mua thanh toán"].sum().reset_index()
            fig = plot_time_series(revenue_by_date, "Ngày mua hàng", "Tổng số tiền người mua thanh toán", "Xu hướng doanh thu theo thời gian")
            st.plotly_chart(fig, use_container_width=True)

    elif tab_option == "📈 Phân tích chi tiết":
        st.markdown('<h1 class="tab-header">Phân tích chi tiết</h1>', unsafe_allow_html=True)
        
        # Biểu đồ doanh thu theo tháng
        if "Tháng mua hàng" in filtered_df.columns and "Tổng số tiền người mua thanh toán" in filtered_df.columns:
            revenue_by_month = filtered_df.groupby("Tháng mua hàng")["Tổng số tiền người mua thanh toán"].sum().reset_index()
            fig_month = px.bar(revenue_by_month, x="Tháng mua hàng", y="Tổng số tiền người mua thanh toán", title="Doanh thu theo tháng", 
                              color="Tổng số tiền người mua thanh toán", color_continuous_scale=px.colors.sequential.Oranges, text_auto=True)
            fig_month.update_traces(textposition='outside')
            fig_month.update_layout(title_x=0.5, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_month, use_container_width=True)
        
        # Biểu đồ phân phối phí vận chuyển
        if "Phí vận chuyển" in filtered_df.columns:
            fig_shipping = create_distribution_chart(filtered_df, "Phí vận chuyển", "Phân phối phí vận chuyển")
            st.plotly_chart(fig_shipping, use_container_width=True)
        
        # Biểu đồ lợi nhuận theo ngày trong tuần
        if "Ngày trong tuần" in filtered_df.columns and "Lợi nhuận" in filtered_df.columns:
            profit_by_day = filtered_df.groupby("Ngày trong tuần")["Lợi nhuận"].sum().reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']).reset_index()
            fig_day = px.bar(profit_by_day, x="Ngày trong tuần", y="Lợi nhuận", title="Lợi nhuận theo ngày trong tuần", 
                            color="Lợi nhuận", color_continuous_scale=px.colors.sequential.Oranges, text_auto=True)
            fig_day.update_traces(textposition='outside')
            fig_day.update_layout(title_x=0.5, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_day, use_container_width=True)

    elif tab_option == "🔍 Phân tích sản phẩm":
        st.markdown('<h1 class="tab-header">Phân tích sản phẩm</h1>', unsafe_allow_html=True)
        
        # Top 10 sản phẩm bán chạy
        if "Sản Phẩm" in filtered_df.columns and "Số lượng" in filtered_df.columns:
            top_products = filtered_df.groupby("Sản Phẩm")["Số lượng"].sum().nlargest(10).reset_index()
            fig_top = px.bar(top_products, x="Sản Phẩm", y="Số lượng", title="Top 10 sản phẩm bán chạy", 
                            color="Số lượng", color_continuous_scale=px.colors.sequential.Oranges, text_auto=True)
            fig_top.update_traces(textposition='outside')
            fig_top.update_layout(title_x=0.5, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_top, use_container_width=True)
        
        # Biểu đồ lợi nhuận theo sản phẩm
        if "Sản Phẩm" in filtered_df.columns and "Lợi nhuận" in filtered_df.columns:
            profit_by_product = filtered_df.groupby("Sản Phẩm")["Lợi nhuận"].sum().nlargest(10).reset_index()
            fig_profit = px.pie(profit_by_product, values="Lợi nhuận", names="Sản Phẩm", title="Top 10 sản phẩm có lợi nhuận cao nhất",
                               color_discrete_sequence=px.colors.sequential.Oranges)
            fig_profit.update_layout(title_x=0.5)
            st.plotly_chart(fig_profit, use_container_width=True)
        
        # Phân phối giá bán sản phẩm
        if "Sản Phẩm" in filtered_df.columns and "Số tiền bán trên lazada" in filtered_df.columns:
            fig_price_dist = create_distribution_chart(filtered_df, "Số tiền bán trên lazada", "Phân phối giá bán sản phẩm")
            st.plotly_chart(fig_price_dist, use_container_width=True)

    elif tab_option == "🌐 Dữ liệu từ Lazada":
        st.markdown('<h1 class="tab-header">Dữ liệu từ Lazada</h1>', unsafe_allow_html=True)
        if "scraped_df" in st.session_state:
            st.dataframe(st.session_state.scraped_df)
            # Biểu đồ giá sản phẩm từ Lazada
            if "Số tiền bán trên lazada" in st.session_state.scraped_df.columns:
                fig_scraped_price = px.box(st.session_state.scraped_df, y="Số tiền bán trên lazada", title="Phân phối giá sản phẩm từ Lazada",
                                          color_discrete_sequence=["#FF6200"])
                fig_scraped_price.update_layout(title_x=0.5)
                st.plotly_chart(fig_scraped_price, use_container_width=True)
        else:
            st.warning("⚠️ Chưa có dữ liệu cào từ Lazada. Vui lòng cào dữ liệu từ sidebar.")

else:
    st.warning("⚠️ Vui lòng tải lên dữ liệu để bắt đầu phân tích!")
