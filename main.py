import streamlit as st
import requests
import pandas as pd
import re

st.set_page_config(
    page_title="식품 나트륨 섭취량 분석",
    page_icon="🧂",
    layout="wide"
)

API_URL = "https://api.data.go.kr/openapi/tn_pubr_public_nutri_info_api"
DAILY_SODIUM_LIMIT = 2000  # mg

st.title("🧂 식품 선택에 따른 나트륨 섭취량 분석 프로그램")
st.caption("공공데이터포털 전국통합식품영양성분정보 API를 활용하여 선택한 식품의 나트륨 섭취량을 계산합니다.")

# -----------------------------
# API 함수
# -----------------------------
@st.cache_data(ttl=600)
def search_food(keyword, api_key):
    params = {
        "ServiceKey": api_key,
        "pageNo": 1,
        "numOfRows": 50,
        "type": "json",
        "foodNm": keyword
    }

    try:
        response = requests.get(API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        return None, f"API 연결 오류가 발생했습니다: {e}"
    except ValueError:
        return None, "API 응답을 JSON 형식으로 읽을 수 없습니다."

    # 공공데이터 API의 일반적인 response.body.items 구조 처리
    try:
        body = data["response"]["body"]
        items = body.get("items", [])

        if isinstance(items, dict):
            # items 안에 item이 있는 경우
            items = items.get("item", items)

        if isinstance(items, dict):
            items = [items]

        if not isinstance(items, list):
            items = []

        return items, None

    except (KeyError, TypeError):
        return None, "API 응답 구조를 확인할 수 없습니다."


def to_number(value):
    """문자열에 포함된 숫자를 안전하게 추출합니다."""
    if value is None:
        return None
    text = str(value).replace(",", "").strip()
    if text == "" or text.lower() in ["nan", "none", "null"]:
        return None

    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None

    try:
        return float(match.group())
    except ValueError:
        return None


def parse_reference_quantity(value):
    """
    예: '100g', '100 ml' -> (100.0, 'g' 또는 'ml')
    """
    if value is None:
        return None, None

    text = str(value).strip().lower().replace(" ", "")
    match = re.search(r"(\d+(?:\.\d+)?)(g|ml|㎖)", text)

    if not match:
        return None, None

    amount = float(match.group(1))
    unit = "ml" if match.group(2) == "㎖" else match.group(2)
    return amount, unit

