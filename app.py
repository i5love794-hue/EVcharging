import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from utils import load_data, calculate_revenue, get_region_gap

# 페이지 설정
st.set_page_config(
    page_title="EV Charging Operational Strategy Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 이미지 경로 설정
IMAGE_PATH = "images/"

# 커스텀 CSS
st.markdown("""
<style>
    .main { background-color: #0f172a; color: #f8fafc; }
    .stMetric { background-color: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; }
    h1, h2, h3 { color: #38bdf8 !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: rgba(30, 41, 59, 0.5);
        border-radius: 4px 4px 0px 0px;
        color: #94a3b8;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #38bdf8 !important; color: #0f172a !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# 데이터 로딩
with st.spinner('데이터를 로드하고 분석 중입니다...'):
    usage, pop, patterns = load_data()
    patterns = calculate_revenue(patterns)
    insufficient_regions = get_region_gap(usage, pop)

# 제목
st.title("⚡ EV 충전소 통합 운영 전략 대시보드")
st.markdown("비즈니스 인사이트 리포트 기반의 통합 운영 관리 시스템")

# 탭 구성
tab1, tab2, tab3 = st.tabs(["📊 운영 전략 & 수익", "🎯 비즈니스 프레임워크", "🔍 상세 EDA 분석"])

# --- Tab 1: 운영 전략 & 수익 ---
with tab1:
    # 사이드바 격인 상단 필터
    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        selected_city = st.multiselect(
            "분석 도시 선택", 
            options=sorted(patterns['Charging Station Location'].unique()),
            default=patterns['Charging Station Location'].unique()[:5]
        )
    filtered_df = patterns[patterns['Charging Station Location'].isin(selected_city)]

    # 주요 지표
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("총 예상 매출", f"${filtered_df['Revenue'].sum():,.0f}")
    with m2: st.metric("평균 수익 (Session)", f"${filtered_df['Revenue'].mean():.2f}")
    with m3: st.metric("총 세션 수", f"{len(filtered_df):,}")
    with m4: 
        rev_pach = filtered_df['Revenue'].sum() / (filtered_df['Charging Duration (hours)'].sum() + 1)
        st.metric("RevPACH (시간당 매출)", f"${rev_pach:.2f}")

    st.divider()
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📈 충전 시간별 수익성 분석")
        rev_summary = filtered_df.groupby('Duration Bin')['Revenue'].agg(['mean', 'sum']).reset_index()
        rev_summary.columns = ['충전 시간', '평균 수익($)', '총 수익($)']
        fig_rev = px.bar(rev_summary, x='충전 시간', y='총 수익($)', color='평균 수익($)', color_continuous_scale='Blues')
        st.plotly_chart(fig_rev, use_container_width=True)
    
    with c2:
        st.subheader("🚩 주요 인프라 격차 지역 (Top 10)")
        fig_gap = px.bar(insufficient_regions, x='Gap_Score', y='City', orientation='h', color='EV_Count', color_continuous_scale='Reds')
        st.plotly_chart(fig_gap, use_container_width=True)

# --- Tab 2: 비즈니스 프레임워크 ---
with tab2:
    st.subheader("🏗️ 운영 전략 프레임워크")
    
    # 01. 북극성 지표
    col_str1, col_str2 = st.columns([1, 1.2])
    with col_str1:
        st.markdown("### [1] 북극성 지표 (North Star Metric)")
        st.info("**RevPACH (Revenue per Available Charger Hour)**: 단위 시간당 충전기 수익성을 극대화하는 지표입니다. 회전율, 충전량, 마진율의 결합으로 정의됩니다.")
        if os.path.exists(os.path.join(IMAGE_PATH, "01_north_star_metric.png")):
            st.image(os.path.join(IMAGE_PATH, "01_north_star_metric.png"), caption="North Star Metric Framework")
    
    with col_str2:
        st.markdown("### [2] KPI 분석 트리 (KPI Tree)")
        st.write("북극성 지표를 달성하기 위한 하위 3대 축: 방문 유도, 에너지 효율, 유휴 시간 제어.")
        if os.path.exists(os.path.join(IMAGE_PATH, "02_kpi_tree.png")):
            st.image(os.path.join(IMAGE_PATH, "02_kpi_tree.png"), caption="KPI Analysis Tree")

    st.divider()

    # 03. 고객 퍼널 & 04. ERD
    col_funnel, col_erd = st.columns(2)
    with col_funnel:
        st.markdown("### [3] 고객 퍼널 설계 (Customer Funnel)")
        st.write("발견 → 진입 → 충전 → 완료 → 이탈의 전체 고객 여정 분석.")
        if os.path.exists(os.path.join(IMAGE_PATH, "03_customer_funnel.png")):
            st.image(os.path.join(IMAGE_PATH, "03_customer_funnel.png"), caption="Customer Funnel Design")
            
    with col_erd:
        st.markdown("### [4] 데이터 기반 ERD 여정")
        st.write("사용자-스테이션-세션 데이터 간의 연동 체계.")
        if os.path.exists(os.path.join(IMAGE_PATH, "04_erd_journey.png")):
            st.image(os.path.join(IMAGE_PATH, "04_erd_journey.png"), caption="Data Structure: ERD Journey")

# --- Tab 3: 상세 EDA 분석 ---
with tab3:
    st.subheader("📊 심층 데이터 분석 결과")
    
    # 분석 결과 이미지 나열
    eda_col1, eda_col2 = st.columns(2)
    
    with eda_col1:
        st.markdown("#### 이용 횟수 밀집도 및 사용 시간 분석")
        if os.path.exists(os.path.join(IMAGE_PATH, "05_usage_time_scatter.png")):
            st.image(os.path.join(IMAGE_PATH, "05_usage_time_scatter.png"))
            st.write("충전 시작 시간과 충전 시간의 분포를 통해 장거리/단거리 패턴 파악.")

        st.markdown("#### 요일별 에너지 수요 패턴")
        if os.path.exists(os.path.join(IMAGE_PATH, "07_energy_by_day.png")):
            st.image(os.path.join(IMAGE_PATH, "07_energy_by_day.png"))
            st.write("평일과 주말의 충전량 차이 분석.")

    with eda_col2:
        st.markdown("#### 피크아워 분석: 시간대별 빈도")
        if os.path.exists(os.path.join(IMAGE_PATH, "06_hourly_freq.png")):
            st.image(os.path.join(IMAGE_PATH, "06_hourly_freq.png"))
            st.write("충전소 혼잡 시간대 파악 및 운영 효율화 포인트 도출.")

        st.markdown("#### 회전율 저하 요인: 점유 유휴시간 분석")
        if os.path.exists(os.path.join(IMAGE_PATH, "08_idle_histogram.png")):
            st.image(os.path.join(IMAGE_PATH, "08_idle_histogram.png"))
            st.write("전력 전송 완료 후 방치되는 시간을 데이터로 정량화.")

    st.divider()
    
    st.markdown("#### 시설 타입별 수익 기여도 및 고객 편익(SOC)")
    c3_1, c3_2 = st.columns(2)
    with c3_1:
        if os.path.exists(os.path.join(IMAGE_PATH, "09_revenue_by_type.png")):
            st.image(os.path.join(IMAGE_PATH, "09_revenue_by_type.png"))
    with c3_2:
        if os.path.exists(os.path.join(IMAGE_PATH, "10_soc_diff.png")):
            st.image(os.path.join(IMAGE_PATH, "10_soc_diff.png"))
