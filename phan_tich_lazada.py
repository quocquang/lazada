import streamlit as st
import pandas as pd
import plotly.express as px
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time
import io
import numpy as np
import random

# Hàm định dạng tiền tệ VND
def format_vnd(number):
    return f"{number:,.0f} VND".replace(",", ".")

# Cấu hình trang
st.set_page_config(page_title="Phân tích đơn hàng Lazada", layout="wide", page_icon="📊")

# CSS tùy chỉnh
st.markdown("""
    <style>
    .main {background-color: #f5f5f5;}
    .stButton>button {background-color: #ff6200; color: white; border-radius: 5px; padding: 10px 20px; margin: 5px; font-weight: bold;}
    .stSelectbox, .stMultiselect {background-color: #ffffff; border-radius: 5px; padding: 5px;}
    .metric-card {background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); text-align: center; margin: 10px;}
    .tab-header {font-size: 28px; color: #ff6200; margin-bottom: 20px; text-align: center;}
    .sub-header {font-size: 20px; color: #333; margin-top: 20px; margin-bottom: 10px;}
    .filter-section {background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 20px;}
    </style>
""", unsafe_allow_html=True)

# Hàm cào dữ liệu từ Lazada
def scrape_lazada_products(search_query):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.binary_location = "/usr/bin/chromium"  # Đường dẫn tới Chromium binary
    
    try:
        # Dùng ChromeDriver từ gói chromium
        service = Service(executable_path="/usr/lib/chromium/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        url = f"https://www.lazada.vn/catalog/?q={search_query.replace(' ', '+')}&page=1"
        driver.get(url)
        time.sleep(random.randint(5, 10))
        
        elems = driver.find_elements(By.CSS_SELECTOR, ".RfADt [href]")
        titles = [elem.text for elem in elems]
        links = [elem.get_attribute('href') for elem in elems]
        
        elems_price = driver.find_elements(By.CSS_SELECTOR, ".ooOxS")
        prices = [elem.text.replace("₫", "").replace(".", "").strip() for elem in elems_price]
        prices = [int(price) if price.isdigit() else 0 for price in prices]
        
        quantities = []
        for i in range(len(titles)):
            try:
                quantity_elem = driver.find_element(By.XPATH, f"//div[@data-qa-locator='product-item'][{i+1}]//span[contains(text(), 'Đã bán')]")
                quantity_text = quantity_elem.text.replace("Đã bán", "").strip()
                quantity = int(''.join(filter(str.isdigit, quantity_text))) if quantity_text else np.nan
            except NoSuchElementException:
                quantity = np.nan
            quantities.append(quantity)
        
        driver.quit()
        
        df = pd.DataFrame({
            "Sản Phẩm": titles,
            "Số tiền bán trên lazada": prices,
            "Số lượng bán": quantities,
            "Link": links
        })
        return df.head(50)
    except Exception as e:
        st.error(f"Lỗi khi cào dữ liệu: {str(e)}")
        return pd.DataFrame()

# Tải dữ liệu từ file Excel
st.sidebar.header("Tải dữ liệu")
uploaded_file = st.sidebar.file_uploader("Tải lên file Excel (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip().str.replace(" ₫", "").str.replace(".", "").str.replace("\t", " ")
        df["Ngày mua hàng"] = pd.to_datetime(df["Ngày mua hàng"], format="%d/%m/%Y", errors="coerce")
        df["Ngày nhận được"] = pd.to_datetime(df["Ngày nhận được"], format="%d/%m/%Y", errors="coerce")
        numeric_columns = ["Số tiền bán trên lazada", "Số tiền khách hàng phải chi trả", "Phí vận chuyển", 
                           "Phí khuyến mãi do người bán trả cho lazada", "Lỗi do cân nặng trừ cho nhà bán hàng", 
                           "Giảm giá từ Lazada cho người mua", "Phí xử lý đơn hàng", "Tổng số tiền người mua thanh toán", 
                           "Tổng số tiền người bán nhận được thanh toán", "Số lượng"]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        st.session_state.df = df
        st.sidebar.success("Tải file Excel thành công!")
    except Exception as e:
        st.sidebar.error(f"Lỗi khi đọc file Excel: {str(e)}")
else:
    df = pd.DataFrame()

# Cào dữ liệu từ Lazada
st.sidebar.header("Cào dữ liệu từ Lazada")
search_query = st.sidebar.text_input("Nhập từ khóa tìm kiếm sản phẩm", "Rogaine")
if st.sidebar.button("Cào dữ liệu"):
    with st.spinner("Đang cào dữ liệu từ Lazada..."):
        scraped_df = scrape_lazada_products(search_query)
        if not scraped_df.empty:
            st.session_state.scraped_df = scraped_df
            st.sidebar.success("Cào dữ liệu thành công!")
        else:
            st.sidebar.error("Không tìm thấy sản phẩm nào hoặc lỗi khi cào dữ liệu.")

# Sử dụng dữ liệu từ session state
if "df" in st.session_state:
    df = st.session_state.df
else:
    df = pd.DataFrame()

# Tiêu đề chính
st.title("📦 Phân tích đơn hàng Lazada")
st.markdown("---")

# Bộ lọc tổng
st.markdown('<div class="filter-section"><h3>Bộ lọc tổng</h3></div>', unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    product_filter_global = st.text_input("Tìm kiếm sản phẩm", "")
with col2:
    date_range_global = st.date_input("Chọn khoảng ngày mua", 
                                      [df["Ngày mua hàng"].min(), df["Ngày mua hàng"].max()] if not df.empty else [pd.to_datetime("2021-01-01"), pd.to_datetime("2025-12-31")], 
                                      key="date_range_global")
with col3:
    apply_filter = st.button("Áp dụng bộ lọc tổng")

# Áp dụng bộ lọc tổng
if apply_filter and not df.empty:
    df_filtered = df[df["Sản Phẩm"].str.contains(product_filter_global, case=False, na=False) & 
                     (df["Ngày mua hàng"].dt.date >= pd.to_datetime(date_range_global[0]).date()) & 
                     (df["Ngày mua hàng"].dt.date <= pd.to_datetime(date_range_global[1]).date())]
else:
    df_filtered = df.copy() if not df.empty else pd.DataFrame()

# Sidebar điều hướng
st.sidebar.header("Điều hướng")
tab_option = st.sidebar.selectbox("Chọn giao diện", ["Phân tích chính", "Thống kê chi tiết", "Dữ liệu cào từ Lazada"])

# Hàm hiển thị số liệu dạng thẻ
def display_metric(label, value, delta=None):
    if isinstance(value, (int, float)):
        if label == "Tổng số đơn hàng" or label == "Tổng số lượng":
            value_str = f"{value:,.0f}".replace(",", ".")
        else:
            value_str = format_vnd(value)
    else:
        value_str = str(value)
    delta_str = f" ({delta})" if delta else ""
    st.markdown(f"""
        <div class="metric-card">
            <h4>{label}</h4>
            <h2>{value_str}{delta_str}</h2>
        </div>
    """, unsafe_allow_html=True)

# Tab 1: Phân tích chính
if tab_option == "Phân tích chính" and not df_filtered.empty:
    st.markdown('<p class="tab-header">Phân tích chính</p>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["Tổng quan", "Theo sản phẩm", "Theo ngày mua", "Lọc dữ liệu"])
    
    with tab1:
        st.subheader("Tổng quan đơn hàng")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            display_metric("Tổng số đơn hàng", len(df_filtered))
        with col2:
            display_metric("Tổng tiền khách trả", df_filtered["Tổng số tiền người mua thanh toán"].sum())
        with col3:
            if "Tổng số tiền người bán nhận được thanh toán" in df_filtered.columns:
                display_metric("Tổng tiền người bán nhận", df_filtered["Tổng số tiền người bán nhận được thanh toán"].sum())
            else:
                display_metric("Tổng tiền người bán nhận", "N/A", "Không có dữ liệu")
        with col4:
            display_metric("Tổng số lượng", df_filtered["Số lượng"].sum())
        
        st.markdown('<p class="sub-header">Biểu đồ tổng quan</p>', unsafe_allow_html=True)
        fig = px.pie(df_filtered, names="Sản Phẩm", values="Số lượng", title="Tỷ lệ số lượng theo sản phẩm", 
                     color_discrete_sequence=px.colors.sequential.Oranges)
        fig.update_layout(width=1000, height=600)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Phân tích theo sản phẩm")
        product_summary = df_filtered.groupby("Sản Phẩm").agg({
            "Số lượng": "sum",
            "Tổng số tiền người mua thanh toán": "sum",
            "Tổng số tiền người bán nhận được thanh toán": "sum" if "Tổng số tiền người bán nhận được thanh toán" in df_filtered.columns else lambda x: 0
        }).reset_index()
        st.dataframe(product_summary.style.format({
            "Số lượng": lambda x: f"{x:,.0f}".replace(",", "."),
            "Tổng số tiền người mua thanh toán": format_vnd,
            "Tổng số tiền người bán nhận được thanh toán": format_vnd
        }))
        
        st.markdown('<p class="sub-header">Biểu đồ số lượng sản phẩm</p>', unsafe_allow_html=True)
        fig = px.bar(product_summary, x="Sản Phẩm", y="Số lượng", title="Số lượng sản phẩm bán ra",
                     color="Sản Phẩm", color_discrete_sequence=px.colors.sequential.Oranges)
        fig.update_layout(width=1000, height=600)
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("Phân tích theo ngày mua hàng")
        date_summary = df_filtered.groupby(df_filtered["Ngày mua hàng"].dt.date).agg({
            "Số lượng": "sum",
            "Tổng số tiền người mua thanh toán": "sum"
        }).reset_index()
        st.dataframe(date_summary.style.format({
            "Số lượng": lambda x: f"{x:,.0f}".replace(",", "."),
            "Tổng số tiền người mua thanh toán": format_vnd
        }))

        st.markdown('<p class="sub-header">Biểu đồ doanh thu theo ngày</p>', unsafe_allow_html=True)
        fig = px.line(date_summary, x="Ngày mua hàng", y="Tổng số tiền người mua thanh toán", 
                      title="Doanh thu theo ngày", line_shape="spline", 
                      color_discrete_sequence=["#ff6200"])
        fig.update_layout(width=1000, height=600)
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.subheader("Lọc dữ liệu đơn hàng")
        col1, col2 = st.columns([1, 3])
        with col1:
            product_filter = st.multiselect("Chọn sản phẩm", options=df_filtered["Sản Phẩm"].unique(), 
                                            default=df_filtered["Sản Phẩm"].unique())
            date_range = st.date_input("Chọn khoảng ngày mua", 
                                      [df_filtered["Ngày mua hàng"].min(), df_filtered["Ngày mua hàng"].max()], 
                                      key="date_range_tab4")
            min_price = st.number_input("Giá tối thiểu", min_value=0, value=0)
            max_price = st.number_input("Giá tối đa", min_value=0, value=int(df_filtered["Số tiền bán trên lazada"].max()))
            min_total = st.number_input("Tổng tiền tối thiểu", min_value=0, value=0)
            max_total = st.number_input("Tổng tiền tối đa", min_value=0, value=int(df_filtered["Tổng số tiền người mua thanh toán"].max()))
        with col2:
            filtered_df = df_filtered[df_filtered["Sản Phẩm"].isin(product_filter) & 
                                      (df_filtered["Ngày mua hàng"].dt.date >= pd.to_datetime(date_range[0]).date()) & 
                                      (df_filtered["Ngày mua hàng"].dt.date <= pd.to_datetime(date_range[1]).date()) &
                                      (df_filtered["Số tiền bán trên lazada"] >= min_price) &
                                      (df_filtered["Số tiền bán trên lazada"] <= max_price) &
                                      (df_filtered["Tổng số tiền người mua thanh toán"] >= min_total) &
                                      (df_filtered["Tổng số tiền người mua thanh toán"] <= max_total)]
            st.dataframe(filtered_df.style.format({
                "Số lượng": lambda x: f"{x:,.0f}".replace(",", "."),
                "Số tiền bán trên lazada": format_vnd,
                "Tổng số tiền người mua thanh toán": format_vnd,
                "Tổng số tiền người bán nhận được thanh toán": format_vnd if "Tổng số tiền người bán nhận được thanh toán" in df_filtered.columns else "N/A"
            }))
            if not filtered_df.empty:
                st.markdown('<p class="sub-header">Biểu đồ số lượng sản phẩm đã lọc</p>', unsafe_allow_html=True)
                fig = px.pie(filtered_df, names="Sản Phẩm", values="Số lượng", title="Tỷ lệ số lượng sản phẩm đã lọc",
                             color_discrete_sequence=px.colors.sequential.Oranges)
                fig.update_layout(width=1000, height=600)
                st.plotly_chart(fig, use_container_width=True)
                buffer = io.BytesIO()
                filtered_df.to_excel(buffer, index=False)
                st.download_button("Tải xuống dữ liệu đã lọc", buffer.getvalue(), "filtered_orders.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Tab 2: Thống kê chi tiết
elif tab_option == "Thống kê chi tiết" and not df_filtered.empty:
    st.markdown('<p class="tab-header">Thống kê chi tiết</p>', unsafe_allow_html=True)
    
    st.subheader("Phân tích lợi nhuận")
    if "Tổng số tiền người bán nhận được thanh toán" in df_filtered.columns:
        df_filtered["Lợi nhuận"] = df_filtered["Tổng số tiền người bán nhận được thanh toán"] - df_filtered["Số tiền bán trên lazada"]
        profit_ratio = (df_filtered["Lợi nhuận"].sum() / df_filtered["Số tiền bán trên lazada"].sum() * 100) if df_filtered["Số tiền bán trên lazada"].sum() > 0 else 0
    else:
        df_filtered["Lợi nhuận"] = 0
        profit_ratio = 0
    profit_summary = df_filtered.groupby("Sản Phẩm").agg({
        "Lợi nhuận": "sum",
        "Số lượng": "sum"
    }).reset_index()
    st.dataframe(profit_summary.style.format({
        "Số lượng": lambda x: f"{x:,.0f}".replace(",", "."),
        "Lợi nhuận": format_vnd
    }))
    col1, col2 = st.columns(2)
    with col1:
        display_metric("Tổng lợi nhuận", df_filtered["Lợi nhuận"].sum())
    with col2:
        display_metric("Tỷ lệ lợi nhuận", f"{profit_ratio:.1f}%")

    st.markdown('<p class="sub-header">Biểu đồ lợi nhuận theo sản phẩm</p>', unsafe_allow_html=True)
    fig = px.bar(profit_summary, x="Sản Phẩm", y="Lợi nhuận", title="Lợi nhuận theo sản phẩm",
                 color="Sản Phẩm", color_discrete_sequence=px.colors.sequential.Oranges)
    fig.update_layout(width=1000, height=600)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Tỷ lệ đơn miễn phí vận chuyển")
    free_shipping_ratio = df_filtered["Miễn phí vận chuyển"].mean() * 100 if "Miễn phí vận chuyển" in df_filtered.columns else 0
    col1, col2 = st.columns(2)
    with col1:
        display_metric("Tỷ lệ miễn phí vận chuyển", f"{free_shipping_ratio:.1f}%")
    with col2:
        if "Miễn phí vận chuyển" in df_filtered.columns:
            fig = px.pie(df_filtered, names="Miễn phí vận chuyển", title="Phân bố đơn miễn phí vận chuyển",
                         color_discrete_sequence=["#ff6200", "#e0e0e0"])
            fig.update_layout(width=1000, height=600)
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Thống kê chi phí")
    cost_columns = ["Phí vận chuyển", "Phí khuyến mãi do người bán trả cho lazada", "Phí xử lý đơn hàng", "Lỗi do cân nặng trừ cho nhà bán hàng"]
    available_costs = {col: df_filtered[col].sum() if col in df_filtered.columns else 0 for col in cost_columns}
    cost_summary = pd.DataFrame({
        "Loại chi phí": cost_columns,
        "Tổng chi phí": [available_costs[col] for col in cost_columns]
    })
    avg_cost_per_order = sum(available_costs.values()) / len(df_filtered) if len(df_filtered) > 0 else 0
    st.dataframe(cost_summary.style.format({
        "Tổng chi phí": format_vnd
    }))
    col1, col2 = st.columns(2)
    with col1:
        display_metric("Tổng chi phí", sum(available_costs.values()))
    with col2:
        display_metric("Chi phí trung bình mỗi đơn", avg_cost_per_order)

    st.markdown('<p class="sub-header">Biểu đồ phân tích chi phí</p>', unsafe_allow_html=True)
    fig = px.bar(cost_summary, x="Loại chi phí", y="Tổng chi phí", title="Phân tích chi phí",
                 color="Loại chi phí", color_discrete_sequence=px.colors.sequential.Oranges)
    fig.update_layout(width=1000, height=600)
    st.plotly_chart(fig, use_container_width=True)

    buffer = io.BytesIO()
    df_filtered.to_excel(buffer, index=False)
    st.download_button("Tải xuống toàn bộ dữ liệu", buffer.getvalue(), "orders_report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Tab 3: Dữ liệu cào từ Lazada
elif tab_option == "Dữ liệu cào từ Lazada":
    st.markdown('<p class="tab-header">Dữ liệu cào từ Lazada</p>', unsafe_allow_html=True)
    
    if "scraped_df" in st.session_state and not st.session_state.scraped_df.empty:
        st.subheader("Dữ liệu sản phẩm từ Lazada")
        st.dataframe(st.session_state.scraped_df.style.format({
            "Số tiền bán trên lazada": format_vnd,
            "Số lượng bán": lambda x: f"{int(x):,.0f}".replace(",", ".") if pd.notna(x) else "NaN"
        }))
        
        st.markdown('<p class="sub-header">Biểu đồ giá sản phẩm từ Lazada</p>', unsafe_allow_html=True)
        fig = px.bar(st.session_state.scraped_df, x="Sản Phẩm", y="Số tiền bán trên lazada", 
                     title="Giá sản phẩm từ Lazada", color="Sản Phẩm", color_discrete_sequence=px.colors.sequential.Oranges)
        fig.update_layout(width=1000, height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        buffer = io.BytesIO()
        st.session_state.scraped_df.to_excel(buffer, index=False)
        st.download_button("Tải xuống dữ liệu cào từ Lazada", buffer.getvalue(), "lazada_products.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.warning("Chưa có dữ liệu cào. Vui lòng nhập từ khóa và nhấn 'Cào dữ liệu' trong sidebar.")

# Thông báo nếu chưa tải dữ liệu
if df.empty and tab_option != "Dữ liệu cào từ Lazada":
    st.warning("Vui lòng tải lên file Excel để bắt đầu phân tích.")

# Footer
st.markdown("---")
st.markdown("Được phát triển bởi xAI | Ngày cập nhật: 04/03/2025", unsafe_allow_html=True)
