import argparse

from budget_app.repository import (
    CategoryRepository,
    TransactionRepository,
)
from budget_app.service import (
    CategoryService,
    TransactionService,
)


# 거래 추가 명령을 처리
def handle_add(transaction_service: TransactionService) -> None:
    print("[거래 추가]")

    date = input("날짜(YYYY-MM-DD): ").strip()
    transaction_type = input("타입(income/expense): ").strip()
    category = input("카테고리: ").strip()
    amount = input("금액(양수): ").strip()
    memo = input("메모(선택): ").strip()

    tags_input = input("태그(쉼표로 구분, 없으면 엔터): ").strip()

    tags = [
        tag.strip()
        for tag in tags_input.split(",")
        if tag.strip()
    ]

    try:
        transaction = transaction_service.add_transaction(
            date=date,
            transaction_type=transaction_type,
            category=category,
            amount=amount,
            memo=memo,
            tags=tags,
        )

        print(f"[저장 완료] id={transaction.id}")

    except ValueError as error:
        print(f"[오류] {error}")


# CLI 명령어와 옵션을 설정
def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="budget_app",
        description="나만의 용돈 기입장 프로그램",
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "add",
        help="새로운 거래를 추가합니다.",
    )

    return parser


# 프로그램 실행에 필요한 저장소와 서비스를 생성
def main() -> None:
    parser = create_parser()
    args = parser.parse_args()

    transaction_repository = TransactionRepository()
    category_repository = CategoryRepository()

    transaction_service = TransactionService(
        transaction_repository,
        category_repository,
    )

    category_service = CategoryService(
        category_repository,
        transaction_repository,
    )

    if args.command == "add":
        handle_add(transaction_service)
    else:
        parser.print_help()