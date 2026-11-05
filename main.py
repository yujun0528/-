
import streamlit as st
import requests
import pandas as pd
import re
from urllib.parse import unquote

st.set_page_config(
    page_title="식품 나트륨 섭취량 분석",
    page_icon="🧂",
    layout="wide"
)


API_URL = "https://apis.data.go.kr/1471000/FoodNtrCpntDbInfo03/getFoodNtrCpntDbInq03"
DAILY_SODIUM_LIMIT = 2000


st.title("🥗 식품 선택에 따른 나트륨 섭취량 분석 프로그램")
st.caption("식품영양성분 데이터를 활용한 나트륨 섭취량 계산 및 기준치 비교")


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


def get_value(item, names):
    for name in names:
        if name in item and item[name] not in [None, ""]:
            return item[name]

    upper_item = {str(k).upper(): v for k, v in item.items()}

    for name in names:
        value = upper_item.get(name.upper())
        if value not in [None, ""]:
            return value

    return None


def get_reference_quantity(value):
    if value is None:
        return None, None

    text = str(value).lower().replace(" ", "")

    match = re.search(r"(\d+(?:\.\d+)?)(g|ml|㎖)", text)

    if not match:
        return None, None

    amount = float(match.group(1))
    unit = match.group(2)

    if unit == "㎖":
        unit = "ml"

    return amount, unit


def extract_items(data):
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]

    if not isinstance(data, dict):
        return []

    for key in ["items", "item"]:
        value = data.get(key)

        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]

        if isinstance(value, dict):
            nested = extract_items(value)

            if nested:
                return nested

    for value in data.values():
        if isinstance(value, dict):
            nested = extract_items(value)

            if nested:
                return nested

        elif isinstance(value, list):
            nested = [x for x in value if isinstance(x, dict)]

            if nested:
                return nested

    return []


def search_food(keyword, api_key):
    params = {
        "serviceKey": unquote(api_key.strip()),
        "pageNo": 1,
        "numOfRows": 100,
        "type": "json",
        "FOOD_NM_KR": keyword
    }

    try:
        response = requests.get(
            API_URL,
            params=params,
            timeout=20
        )

        if response.status_code != 200:
            return None, (
                f"API 요청 실패 ({response.status_code})\n"
                f"응답 내용: {response.text[:500]}"
            )

        try:
            data = response.json()
        except ValueError:
            return None, (
                "API 응답을 JSON으로 읽을 수 없습니다.\n"
                f"응답 내용: {response.text[:500]}"
            )

        header = data.get("header", {})

        if isinstance(header, dict):
            result_code = str(
                header.get("resultCode", header.get("result_code", ""))
            )

            if result_code and result_code not in ["00", "0"]:
                result_message = header.get(
                    "resultMsg",
                    header.get("result_message", "알 수 없는 API 오류")
                )

                return None, (
                    f"API 오류 코드: {result_code}\n"
                    f"오류 내용: {result_message}"
                )

        items = extract_items(data)

        if not items:
            return None, (
                "검색 결과가 없거나 응답 데이터 형식을 확인할 수 없습니다.\n"
                f"응답 내용: {str(data)[:1000]}"
            )

        return items, None

    except requests.exceptions.Timeout:
        return None, "API 요청 시간이 초과되었습니다."

    except requests.exceptions.ConnectionError:
        return None, "API 서버에 연결할 수 없습니다."

    except requests.exceptions.RequestException as e:
        return None, f"API 연결 오류: {e}"


if "foods" not in st.session_state:
    st.session_state.foods = []

if "search_results" not in st.session_state:
    st.session_state.search_results = []


with st.sidebar:
    st.header("🔎 식품 검색")

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

    keyword = st.text_input(
        "식품명을 입력하세요",
        placeholder="예: 라면"
    )

    if st.button("🔎 식품 검색", use_container_width=True):
        if not keyword.strip():
            st.warning("식품명을 입력해주세요.")

        elif not api_key:
            st.error("API 인증키가 설정되지 않았습니다.")

        else:
            with st.spinner("식품 데이터를 검색하고 있습니다..."):
                results, error = search_food(
                    keyword.strip(),
                    api_key
                )

            if error:
                st.error(error)
                st.session_state.search_results = []

            else:
                valid_results = []

                for item in results:
                    name = get_value(item, ["FOOD_NM_KR"])
                    sodium = get_value(
                        item,
                        ["AMT_NUM13", "NA", "NAT"]
                    )

                    if name and to_number(sodium) is not None:
                        valid_results.append(item)

                if not valid_results:
                    st.info(
                        "검색 결과가 없습니다. "
                        "다른 식품명을 입력해보세요."
                    )
                    st.session_state.search_results = []

                else:
                    st.session_state.search_results = valid_results

    if st.session_state.search_results:
        st.markdown("---")
        st.subheader("검색 결과")

        labels = []

        for item in st.session_state.search_results:
            name = get_value(item, ["FOOD_NM_KR"])
            sodium = to_number(
                get_value(item, ["AMT_NUM13", "NA", "NAT"])
            )
            reference = get_value(item, ["SERVING_SIZE"])

            labels.append(
                f"{name} | 나트륨 {sodium:g} mg | 기준량 {reference or '정보 없음'}"
            )

        selected_index = st.selectbox(
            "식품을 선택하세요",
            range(len(labels)),
            format_func=lambda x: labels[x]
        )

        selected = st.session_state.search_results[selected_index]

        name = get_value(selected, ["FOOD_NM_KR"])
        sodium = to_number(
            get_value(selected, ["AMT_NUM13", "NA", "NAT"])
        )
        reference = get_value(selected, ["SERVING_SIZE"])

        st.write(f"**선택 식품:** {name}")
        st.write(f"**영양성분 기준량:** {reference or '정보 없음'}")
        st.write(f"**나트륨:** {sodium:g} mg")

        ref_amount, ref_unit = get_reference_quantity(reference)

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

        if st.button("➕ 식품 추가", use_container_width=True):
            if ref_amount and ref_unit:
                multiplier = intake / ref_amount
                intake_sodium = sodium * multiplier
                intake_unit = ref_unit
            else:
                multiplier = intake
                intake_sodium = sodium * multiplier
                intake_unit = "배"

            st.session_state.foods.append({
                "식품명": name,
                "섭취량": intake,
                "단위": intake_unit,
                "기준량": reference or "정보 없음",
                "기준 나트륨(mg)": sodium,
                "섭취 나트륨(mg)": intake_sodium
            })

            st.success("식품이 추가되었습니다!")

    st.markdown("---")

    if st.button("🗑️ 선택한 식품 전체 삭제", use_container_width=True):
        st.session_state.foods = []
        st.rerun()


st.header("1. 선택한 식품")

if not st.session_state.foods:
    st.info("왼쪽에서 식품을 검색하고 식품을 추가해주세요.")

else:
    df = pd.DataFrame(st.session_state.foods)

    display_df = df.copy()

    display_df["섭취량"] = display_df.apply(
        lambda row: f"{row['섭취량']:g} {row['단위']}",
        axis=1
    )

    display_df["기준 나트륨(mg)"] = display_df[
        "기준 나트륨(mg)"
    ].round(1)

    display_df["섭취 나트륨(mg)"] = display_df[
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

    st.header("2. 나트륨 섭취량 분석")

    total_sodium = float(
        df["섭취 나트륨(mg)"].sum()
    )

    percentage = (
        total_sodium / DAILY_SODIUM_LIMIT
    ) * 100

    excess = total_sodium - DAILY_SODIUM_LIMIT

    max_index = df["섭취 나트륨(mg)"].idxmax()
    max_food = df.loc[max_index, "식품명"]
    max_sodium = float(
        df.loc[max_index, "섭취 나트륨(mg)"]
    )

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

    if total_sodium > DAILY_SODIUM_LIMIT:
        st.warning(
            f"현재 선택한 식품의 총 나트륨은 "
            f"{total_sodium:,.1f} mg으로 "
            f"1일 기준치를 {excess:,.1f} mg 초과합니다."
        )

    else:
        st.success(
            f"현재 선택한 식품의 총 나트륨은 "
            f"1일 기준치의 {percentage:.1f}%입니다."
        )

    st.write(
        f"**가장 많은 나트륨을 포함한 식품:** "
        f"{max_food} ({max_sodium:,.1f} mg)"
    )

    st.header("3. 식품별 나트륨 섭취량")

    chart_df = df[
        ["식품명", "섭취 나트륨(mg)"]
    ].copy()

    chart_df = chart_df.set_index("식품명")

    st.bar_chart(
        chart_df,
        y="섭취 나트륨(mg)"
    )

    st.header("4. 1일 나트륨 기준치 비교")

    comparison_df = pd.DataFrame({
        "구분": ["총 섭취량", "1일 기준치"],
        "나트륨(mg)": [
            total_sodium,
            DAILY_SODIUM_LIMIT
        ]
    }).set_index("구분")

    st.bar_chart(
        comparison_df,
        y="나트륨(mg)"
    )

    st.header("5. 생명과학 개념 연계")

    st.write(
        "나트륨은 체액의 삼투압과 전해질 균형 유지 등에 관여하는 무기질입니다. "
        "식품마다 나트륨 함량이 다르기 때문에 여러 식품을 함께 섭취하면 "
        "총 섭취량도 달라질 수 있습니다. 이 프로그램은 식품영양성분 데이터를 "
        "이용해 식품 선택에 따른 나트륨 섭취량의 차이를 수치와 그래프로 "
        "확인할 수 있도록 구현했습니다."
    )


with st.expander("📌 데이터 출처 및 프로그램 정보"):
    st.write("데이터 출처: 식품의약품안전처 식품영양성분DB정보")
    st.write("개발 환경: Python + Streamlit")
    st.write("1일 나트륨 기준치: 2,000 mg")
