import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------
# 1. 페이지 기본 설정 및 디자인
# ---------------------------------------------------------
st.set_page_config(
    page_title="효소 활성 분석 및 최적 조건 탐색기",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 온도 및 pH에 따른 효소(아밀레이스) 활성 분석 프로그램")
st.caption("생명과학 I/II 연계 | 데이터 분석 및 최적 반응 조건 시각화 도구")

st.markdown("""
> **연구 및 탐구 배경**  
> 효소는 특정 **온도**와 **pH**에서 최고의 활성도를 보입니다. 본 프로그램은 온도와 pH 조건을 다변화하여 측정한 실험 데이터를 기반으로 
> **최적 활성 조건 탐색, 평균 활성도 계산, 데이터 시각화**를 자동화하기 위해 개발되었습니다.
""")

st.divider()

# ---------------------------------------------------------
# 2. 기본 실험 데이터셋 (아밀레이스 기준 샘플 데이터)
# ---------------------------------------------------------
DEFAULT_DATA = [
    {"온도(℃)": 20, "pH": 5.0, "효소 활성도(%)": 35.0},
    {"온도(℃)": 20, "pH": 7.0, "효소 활성도(%)": 52.0},
    {"온도(℃)": 20, "pH": 9.0, "효소 활성도(%)": 28.0},
    {"온도(℃)": 30, "pH": 5.0, "효소 활성도(%)": 58.0},
    {"온도(℃)": 30, "pH": 7.0, "효소 활성도(%)": 81.0},
    {"온도(℃)": 30, "pH": 9.0, "효소 활성도(%)": 45.0},
    {"온도(℃)": 37, "pH": 5.0, "효소 활성도(%)": 72.0},
    {"온도(℃)": 37, "pH": 7.0, "효소 활성도(%)": 98.5}, # 최적 반응점에 가깝게 설정
    {"온도(℃)": 37, "pH": 9.0, "효소 활성도(%)": 60.0},
    {"온도(℃)": 50, "pH": 5.0, "효소 활성도(%)": 40.0},
    {"온도(℃)": 50, "pH": 7.0, "효소 활성도(%)": 62.0},
    {"온도(℃)": 50, "pH": 9.0, "효소 활성도(%)": 30.0},
    {"온도(℃)": 65, "pH": 5.0, "효소 활성도(%)": 10.0},
    {"온도(℃)": 65, "pH": 7.0, "효소 활성도(%)": 15.0},
    {"온도(℃)": 65, "pH": 9.0, "효소 활성도(%)": 5.0},
]

# ---------------------------------------------------------
# 3. 세션 상태(Session State) 초기화
# ---------------------------------------------------------
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(DEFAULT_DATA)

# ---------------------------------------------------------
# 4. 사이드바: 데이터 입력 및 예외 처리
# ---------------------------------------------------------
st.sidebar.header("📥 실험 데이터 추가 / 관리")

st.sidebar.subheader("신규 데이터 입력")
input_temp = st.sidebar.number_input("온도 (℃)", min_value=-10.0, max_value=100.0, value=37.0, step=1.0)
input_ph = st.sidebar.number_input("pH (0.0~14.0)", min_value=0.0, max_value=14.0, value=7.0, step=0.1)
input_activity = st.sidebar.number_input("효소 상대 활성도 (%)", min_value=0.0, max_value=200.0, value=90.0, step=1.0)

# 예외 처리 및 데이터 추가 함수
if st.sidebar.button("데이터 추가하기", type="primary"):
    # 유효성 검사 (오류 처리)
    if input_temp < 0 or input_temp > 90:
        st.sidebar.error("⚠️ 정상적인 효소 반응 범위(0℃ ~ 90℃)를 벗어난 온도입니다.")
    elif input_ph < 0 or input_ph > 14:
        st.sidebar.error("⚠️ pH는 0에서 14 사이의 값이어야 합니다.")
    elif input_activity < 0:
        st.sidebar.error("⚠️ 효소 활성도는 음수가 될 수 없습니다.")
    else:
        new_row = pd.DataFrame([{"온도(℃)": input_temp, "pH": input_ph, "효소 활성도(%)": input_activity}])
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        st.sidebar.success("✅ 데이터가 성공적으로 추가되었습니다!")

if st.sidebar.button("데이터 초기화"):
    st.session_state.df = pd.DataFrame(DEFAULT_DATA)
    st.sidebar.info("기본 데이터셋으로 초기화되었습니다.")

# ---------------------------------------------------------
# 5. 메인 화면: 데이터 분석 및 주요 지표(KPI)
# ---------------------------------------------------------
col_data, col_summary = st.columns([1, 1])

df = st.session_state.df

with col_data:
    st.subheader("📋 현재 실험 데이터 목록")
    st.dataframe(df, use_container_width=True, height=280)

with col_summary:
    st.subheader("📊 주요 분석 결과")
    if not df.empty:
        # 최적 조건 검색
        max_idx = df["효소 활성도(%)"].idxmax()
        optimal_row = df.loc[max_idx]
        
        avg_act = df["효소 활성도(%)"].mean()
        max_act = optimal_row["효소 활성도(%)"]
        
        # 지표(Metric) 카드 출력
        m_col1, m_col2 = st.columns(2)
        m_col1.metric(label="🏆 최적 반응 온도", value=f"{optimal_row['온도(℃)']} ℃")
        m_col2.metric(label="🏆 최적 반응 pH", value=f"pH {optimal_row['pH']}")
        
        m_col3, m_col4 = st.columns(2)
        m_col3.metric(label="💥 최대 활성도", value=f"{max_act:.1f} %")
        m_col4.metric(label="📈 전체 평균 활성도", value=f"{avg_act:.1f} %")

st.divider()

# ---------------------------------------------------------
# 6. 데이터 시각화 (그래프 표현)
# ---------------------------------------------------------
st.subheader("📈 데이터 시각화 및 조건별 경향 분석")

tab1, tab2, tab3 = st.tabs(["온도 vs 활성도", "pH vs 활성도", "3D 입체 분석"])

with tab1:
    st.markdown("##### 🌡️ 온도에 따른 효소 활성 변화 (pH 그룹별)")
    fig_temp = px.line(
        df,
        x="온도(℃)",
        y="효소 활성도(%)",
        color="pH",
        markers=True,
        title="온도 상승 및 열변성에 따른 효소 활성 곡선"
    )
    fig_temp.update_traces(marker=dict(size=8))
    st.plotly_chart(fig_temp, use_container_width=True)

with tab2:
    st.markdown("##### 🧪 pH에 따른 효소 활성 변화 (온도 그룹별)")
    fig_ph = px.line(
        df,
        x="pH",
        y="효소 활성도(%)",
        color="온도(℃)",
        markers=True,
        title="pH 조건 변동에 따른 효소 활성 곡선"
    )
    fig_ph.update_traces(marker=dict(size=8))
    st.plotly_chart(fig_ph, use_container_width=True)

with tab3:
    st.markdown("##### 🧊 온도-pH-활성도 3차원 입체 산점도")
    fig_3d = px.scatter_3d(
        df,
        x="온도(℃)",
        y="pH",
        z="효소 활성도(%)",
        color="효소 활성도(%)",
        size="효소 활성도(%)",
        opacity=0.8,
        color_continuous_scale="Viridis",
        title="3D 최적 활성 영역 탐색"
    )
    st.plotly_chart(fig_3d, use_container_width=True)

st.divider()

# ---------------------------------------------------------
# 7. 생명과학 원리 연계 보고서 요약 (수행평가 제출용)
# ---------------------------------------------------------
st.subheader("📝 생명과학 개념 연계 및 결론")
st.markdown("""
* **최적 온도 및 열변성 원리:**  
  온도가 상승함에 따라 분자 운동 에너지가 증가하여 반응 속도가 증가하지만, 최적 온도(약 37℃~40℃)를 초과하면 효소(단백질)의 3차원 입체구조가 변형(열변성)되어 활성을 잃게 됩니다.
* **최적 pH와 이온화 상태:**  
  pH 변화는 효소 활성 부위의 아미노산 잔기 이온화 상태를 변화시켜 기질과의 결합력을 떨어뜨립니다.
* **프로그램의 해결 가치:**  
  수작업 분석 시 발생하는 오차를 줄이고, 다변수(온도, pH) 데이터 속에서 **최적 조건(Optimal Condition)**을 자동 산출하여 실험 효율성을 높일 수 있습니다.
""")
