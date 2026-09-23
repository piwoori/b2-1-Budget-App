from datetime import datetime

# 문자열을 날짜 형식(YYYY-MM-DD)으로 변환
def validate_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


# 거래 타입 확인
def validate_type(value: str) -> bool:
    return value in ("income", "expense")


# 문자열 입력 확인
def validate_amount(value: str) -> bool:
    try:
        amount = int(value)
        return amount > 0
    except ValueError:
        return False


# 이미 등록되어 있는 카테고리인지 확인
def validate_category(value: str, categories: list[str]) -> bool:
    return value in categories