import streamlit as st
import requests
import pandas as pd
import re

# ---------------------------------------
# 기본 설정
# ---------------------------------------
st.set_page_config(
    page_title="식품 나트륨 섭취량 분석",
    page_icon="🧂",
    layout="wide"
)

API_URL = "https://api.data.go.kr/openapi/tn_pubr_public_nutri_info_api"
DAILY_SODIUM_LIMIT = 2000


# ---------------------------------------
# 제목
# ---------------------------------------
st.title("🥗 식품 선택에 따른 나트륨 섭취량 분석 프로그램")

st.caption(
    "식품영양성분 데이터를 활용한 나트륨 섭취량 계산 및 기준치 비교"
)


# ---------------------------------------
# 숫자 변환 함수
# ---------------------------------------
def to_number(value):
    if value is None:
        return None

    text = str(value).replace(",", "").strip()

    if not text:
        return None

    match = re.search(r"-?\d+(?:\.\d+)?", text)

    if not match:
        return None

    try:
        return float(match.group())
    except ValueError:
        return None


# ---------------------------------------
# 기준량에서 숫자와 단위 추출
# ---------------------------------------
def get_reference_quantity(value):

    if value is None:
        return None, None

    text = str(value).lower().replace(" ", "")

    match = re.search(
        r"(\d+(?:\.\d+)?)(g|ml|㎖)",
        text
    )

    if not match:
        return None, None

    amount = float(match.group(1))
    unit = match.group(2)

    if unit == "㎖":
        unit = "ml"

    return amount, unit


# ---------------------------------------
# 식품영양성분 API 검색
# ---------------------------------------
def search_food(keyword, api_key):

    params = {
        "ServiceKey": api_key,
        "pageNo": 1,
        "numOfRows": 50,
        "type": "json",
        "foodNm": keyword
    }

    try:

        response = requests.get(
            API_URL,
            params=params,
            timeout=10
        )

        # HTTP 오류 확인
        if response.status_code != 200:

            return None, (
                f"API 요청 실패 ({response.status_code})\n\n"
                f"응답 내용:\n{response.text[:500]}"
            )

        # JSON 변환
        try:
            data = response.json()

        except ValueError:

            return None, (
                "API 응답을 JSON 형식으로 읽을 수 없습니다.\n\n"
                f"응답 내용:\n{response.text[:500]}"
            )

    except requests.exceptions.Timeout:

        return None, "API 요청 시간이 초과되었습니다."

    except requests.exceptions.ConnectionError:

        return None, "인터넷 연결 또는 API 서버 연결에 문제가 있습니다."

    except requests.exceptions.RequestException as e:

        return None, f"API 연결 오류: {e}"

    # ---------------------------------------
    # API 응답 데이터 처리
    # ---------------------------------------
    try:

        body = data["response"]["body"]

        items = body.get("items", [])

        if isinstance(items, dict):
            items = items.get("item", items)

        if isinstance(items, dict):
            items = [items]

        if not isinstance(items, list):
            items = []

        return items, None

    except (KeyError, TypeError):

        return None, (
            "API 응답 구조를 확인할 수 없습니다.\n\n"
            f"받은 데이터:\n{data}"
        )


# ---------------------------------------
# Session State 초기화
# ---------------------------------------
if "foods" not in st.session_state:
    st.session_state.foods = []

if "search_results" not in st.session_state:
    st.session_state.search_results = []


# =======================================
# 사이드바
# =======================================
with st.sidebar:

    st.header("🔎 식품 검색")

    # -----------------------------------
    # Secrets에서 인증키 불러오기
    # -----------------------------------
    try:

        api_key = st.secrets["KOBIS_KEY"]

    except Exception:

        api_key = ""

    if not api_key:

        st.warning(
            "API 인증키가 설정되지 않았습니다.\n\n"
            "Streamlit Cloud의 Settings → Secrets에서 "
            "KOBIS_KEY를 설정해주세요."
        )

    # -----------------------------------
    # 식품명 입력
    # -----------------------------------
    keyword = st.text_input(
        "식품명을 입력하세요",
        placeholder="예: 라면"
    )

    # -----------------------------------
    # 검색 버튼
    # -----------------------------------
    if st.button(
        "🔎 식품 검색",
        use_container_width=True
    ):

        if not keyword.strip():

            st.warning("식품명을 입력해주세요.")

        elif not api_key:

            st.error("API 인증키가 설정되지 않았습니다.")

        else:

            with st.spinner(
                "식품 데이터를 검색하고 있습니다..."
            ):

                results, error = search_food(
                    keyword.strip(),
                    api_key
                )

            # API 오류
            if error:

                st.error(error)

                st.session_state.search_results = []

            else:

                # 나트륨 값이 존재하는 데이터만 사용
                results = [
                    item
                    for item in results
                    if to_number(item.get("nat")) is not None
                ]

                if not results:

                    st.info(
                        "검색 결과가 없습니다. "
                        "다른 식품명을 입력해보세요."
                    )

                    st.session_state.search_results = []

                else:

                    st.session_state.search_results = results


    # ===================================
    # 검색 결과
    # ===================================
    if st.session_state.search_results:

        st.markdown("---")

        st.subheader("검색 결과")

        labels = []

        for item in st.session_state.search_results:

            name = item.get(
                "foodNm",
                "이름 없음"
            )

            sodium = to_number(
                item.get("nat")
            )

            labels.append(
                f"{name} | 나트륨 {sodium:g} mg"
            )

        # 식품 선택
        selected_index = st.selectbox(
            "식품을 선택하세요",
            range(len(labels)),
            format_func=lambda x: labels[x]
        )

        selected = (
            st.session_state.search_results[
                selected_index
            ]
        )

        name = selected.get(
            "foodNm",
            "이름 없음"
        )

        sodium = to_number(
            selected.get("nat")
        )

        reference = selected.get(
            "nutConSrtrQua",
            "기준량 정보 없음"
        )

        st.write(
            f"**선택 식품:** {name}"
        )

        st.write(
            f"**기준량:** {reference}"
        )

        st.write(
            f"**나트륨:** {sodium:g} mg"
        )

        # -----------------------------------
        # 기준량 확인
        # -----------------------------------
        ref_amount, ref_unit = (
            get_reference_quantity(reference)
        )

        if ref_amount and ref_unit:

            intake = st.number_input(
                f"섭취량 ({ref_unit})",
                min_value=0.1,
                value=float(ref_amount),
                step=10.0
            )

        else:

            intake = st.number_input(
                "섭취량 (기준량의 배수)",
                min_value=0.1,
                value=1.0,
                step=0.1
            )

        # -----------------------------------
        # 식품 추가
        # -----------------------------------
        if st.button(
            "➕ 식품 추가",
            use_container_width=True
        ):

            if ref_amount and ref_unit:

                multiplier = (
                    intake / ref_amount
                )

                intake_sodium = (
                    sodium * multiplier
                )

            else:

                multiplier = intake

                intake_sodium = (
                    sodium * multiplier
                )

            st.session_state.foods.append(
                {
                    "식품명": name,
                    "섭취량": intake,
                    "단위": (
                        ref_unit
                        if ref_unit
                        else "배"
                    ),
                    "기준량": reference,
                    "기준 나트륨(mg)": sodium,
                    "섭취 나트륨(mg)": intake_sodium
                }
            )

            st.success(
                "식품이 추가되었습니다!"
            )

    # -----------------------------------
    # 전체 삭제
    # -----------------------------------
    st.markdown("---")

    if st.button(
        "🗑️ 선택한 식품 전체 삭제",
        use_container_width=True
    ):

        st.session_state.foods = []

        st.rerun()


# =======================================
# 1. 선택한 식품
# =======================================
st.header("1. 선택한 식품")

if not st.session_state.foods:

    st.info(
        "왼쪽에서 식품을 검색하고 "
        "식품을 추가해주세요."
    )

else:

    df = pd.DataFrame(
        st.session_state.foods
    )

    # 화면 표시용 데이터
    display_df = df.copy()

    display_df["섭취량"] = display_df.apply(
        lambda row:
        f"{row['섭취량']:g} {row['단위']}",
        axis=1
    )

    display_df[
        "기준 나트륨(mg)"
    ] = display_df[
        "기준 나트륨(mg)"
    ].round(1)

    display_df[
        "섭취 나트륨(mg)"
    ] = display_df[
        "섭취 나트륨(mg)"
    ].round(1)

    st.dataframe(
        display_df[
            [
                "식품명",
                "섭취량",
                "기준 나트륨(mg)",
                "섭취 나트륨(mg)"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )


    # ===================================
    # 2. 나트륨 섭취량 분석
    # ===================================
    st.header("2. 나트륨 섭취량 분석")

    total_sodium = float(
        df["섭취 나트륨(mg)"].sum()
    )

    percentage = (
        total_sodium
        / DAILY_SODIUM_LIMIT
        * 100
    )

    excess = (
        total_sodium
        - DAILY_SODIUM_LIMIT
    )

    # 가장 많은 나트륨을 포함한 식품
    max_index = df[
        "섭취 나트륨(mg)"
    ].idxmax()

    max_food = df.loc[
        max_index,
        "식품명"
    ]

    max_sodium = float(
        df.loc[
            max_index,
            "섭취 나트륨(mg)"
        ]
    )


    # -----------------------------------
    # 분석 결과
    # -----------------------------------
    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "총 나트륨 섭취량",
            f"{total_sodium:,.1f} mg"
        )

    with col2:

        st.metric(
            "1일 기준치",
            "2,000 mg"
        )

    with col3:

        st.metric(
            "기준치 대비",
            f"{percentage:.1f}%"
        )

    with col4:

        if excess > 0:

            st.metric(
                "기준치 초과량",
                f"{excess:,.1f} mg"
            )

        else:

            st.metric(
                "남은 기준량",
                f"{abs(excess):,.1f} mg"
            )


    # -----------------------------------
    # 기준치 비교 결과
    # -----------------------------------
    if total_sodium > DAILY_SODIUM_LIMIT:

        st.warning(
            f"현재 선택한 식품의 총 나트륨은 "
            f"{total_sodium:,.1f} mg으로 "
            f"1일 기준치를 "
            f"{excess:,.1f} mg 초과합니다."
        )

    else:

        st.success(
            f"현재 선택한 식품의 총 나트륨은 "
            f"1일 기준치의 "
            f"{percentage:.1f}%입니다."
        )


    # -----------------------------------
    # 가장 많은 식품
    # -----------------------------------
    st.write(
        f"**가장 많은 나트륨을 포함한 식품:** "
        f"{max_food} "
        f"({max_sodium:,.1f} mg)"
    )


    # ===================================
    # 3. 식품별 나트륨 섭취량
    # ===================================
    st.header("3. 식품별 나트륨 섭취량")

    chart_df = df[
        [
            "식품명",
            "섭취 나트륨(mg)"
        ]
    ].copy()

    chart_df = chart_df.set_index(
        "식품명"
    )

    st.bar_chart(
        chart_df,
        y="섭취 나트륨(mg)"
    )


    # ===================================
    # 4. 1일 기준치 비교
    # ===================================
    st.header(
        "4. 1일 나트륨 기준치 비교"
    )

    comparison_df = pd.DataFrame(
        {
            "구분": [
                "총 섭취량",
                "1일 기준치"
            ],
            "나트륨(mg)": [
                total_sodium,
                DAILY_SODIUM_LIMIT
            ]
        }
    )

    comparison_df = comparison_df.set_index(
        "구분"
    )

    st.bar_chart(
        comparison_df,
        y="나트륨(mg)"
    )


    # ===================================
    # 5. 생명과학 개념 연계
    # ===================================
    st.header("5. 생명과학 개념 연계")

    st.write(
        "나트륨은 체액의 삼투압과 전해질 균형 "
        "유지 등에 관여하는 무기질입니다. "
        "식품마다 나트륨 함량이 다르기 때문에 "
        "여러 식품을 함께 섭취하면 총 섭취량도 "
        "달라질 수 있습니다. "
        "이 프로그램은 식품영양성분 데이터를 "
        "이용해 식품 선택에 따른 나트륨 섭취량의 "
        "차이를 수치와 그래프로 확인할 수 있도록 "
        "구현했습니다."
    )


# =======================================
# 데이터 출처 및 프로그램 정보
# =======================================
with st.expander(
    "📌 데이터 출처 및 프로그램 정보"
):

    st.write(
        "데이터 출처: "
        "공공데이터포털 전국통합식품영양성분정보표준데이터"
    )

    st.write(
        "개발 환경: Python + Streamlit"
    )

    st.write(
        "1일 나트륨 기준치: 2,000 mg"
    )
