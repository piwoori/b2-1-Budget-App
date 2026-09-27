import argparse

from budget_app.repository import (
    BudgetRepository,
    CategoryRepository,
    TransactionRepository,
)
from budget_app.service import (
    BudgetService,
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

# 거래 목록 조회 명령을 처리
def handle_list(
    transaction_service: TransactionService,
    limit: int,
) -> None:
    try:
        transactions = transaction_service.get_transactions(limit)

        if not transactions:
            print("[안내] 저장된 거래가 없습니다.")
            return

        for transaction in transactions:
            print(
                f"{transaction.id} | "
                f"{transaction.date} | "
                f"{transaction.type} | "
                f"{transaction.category} | "
                f"{transaction.amount} | "
                f"{transaction.memo}"
            )

    except ValueError as error:
        print(f"[오류] {error}")
        print("[힌트] --limit에는 1 이상의 정수를 입력하세요.")

# 거래 검색 명령을 처리
def handle_search(
    transaction_service: TransactionService,
    args: argparse.Namespace,
) -> None:
    try:
        transactions = transaction_service.search_transactions(
            from_date=args.from_date,
            to_date=args.to_date,
            category=args.category,
            transaction_type=args.transaction_type,
            query=args.query,
            tag=args.tag,
        )

        if not transactions:
            print("[안내] 검색 조건에 맞는 거래가 없습니다.")
            return

        for transaction in transactions:
            print(
                f"{transaction.id} | "
                f"{transaction.date} | "
                f"{transaction.type} | "
                f"{transaction.category} | "
                f"{transaction.amount} | "
                f"{transaction.memo}"
            )

    except ValueError as error:
        print(f"[오류] {error}")
        print("[힌트] 검색 옵션의 형식과 값을 확인하세요.")


# 카테고리 추가 명령을 처리
def handle_category_add(category_service: CategoryService) -> None:
    category = input("카테고리명: ").strip()

    if category_service.add_category(category):
        print(f"[저장 완료] category={category}")
    else:
        print("[오류] 카테고리를 추가할 수 없습니다.")
        print("[힌트] 빈 이름이거나 이미 존재하는 카테고리인지 확인하세요.")


# 카테고리 목록 조회 명령을 처리
def handle_category_list(category_service: CategoryService) -> None:
    categories = category_service.get_categories()

    if not categories:
        print("[안내] 등록된 카테고리가 없습니다.")
        return

    for category in categories:
        print(f"- {category}")


# 카테고리 삭제 명령을 처리
def handle_category_remove(category_service: CategoryService) -> None:
    category = input("삭제할 카테고리명: ").strip()

    if category_service.remove_category(category):
        print(f"[삭제 완료] category={category}")
    else:
        print("[오류] 카테고리를 삭제할 수 없습니다.")
        print("[힌트] 존재 여부 또는 해당 카테고리를 사용하는 거래가 있는지 확인하세요.")


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

    list_parser = subparsers.add_parser(
        "list",
        help="거래 목록을 조회합니다.",
    )

    list_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="조회할 거래 개수 (기본값: 10)",
    )

    search_parser = subparsers.add_parser(
        "search",
        help="조건에 맞는 거래를 검색합니다.",
    )

    search_parser.add_argument(
        "--from",
        dest="from_date",
        help="검색 시작 날짜 (YYYY-MM-DD)",
    )

    search_parser.add_argument(
        "--to",
        dest="to_date",
        help="검색 종료 날짜 (YYYY-MM-DD)",
    )

    search_parser.add_argument(
        "--category",
        help="검색할 카테고리",
    )

    search_parser.add_argument(
        "--type",
        dest="transaction_type",
        help="거래 타입 (income/expense)",
    )

    search_parser.add_argument(
        "--q",
        dest="query",
        help="메모 검색 키워드",
    )

    search_parser.add_argument(
        "--tag",
        help="검색할 태그",
    )

    summary_parser = subparsers.add_parser(
        "summary",
        help="월별 거래 요약을 조회합니다.",
    )

    summary_parser.add_argument(
        "--month",
        required=True,
        help="조회할 월 (YYYY-MM)",
    )

    summary_parser.add_argument(
        "--top",
        type=int,
        default=3,
        help="카테고리별 지출 상위 개수 (기본값: 3)",
    )

    budget_parser = subparsers.add_parser(
        "budget",
        help="월별 예산을 관리합니다.",
    )

    budget_subparsers = budget_parser.add_subparsers(
        dest="budget_command",
    )

    budget_set_parser = budget_subparsers.add_parser(
        "set",
        help="월별 예산을 설정합니다.",
    )

    budget_set_parser.add_argument(
        "--month",
        required=True,
        help="예산을 설정할 월 (YYYY-MM)",
    )

    budget_set_parser.add_argument(
        "--amount",
        required=True,
        help="예산 금액",
    )

    category_parser = subparsers.add_parser(
        "category",
        help="카테고리를 관리합니다.",
    )

    category_subparsers = category_parser.add_subparsers(
        dest="category_command"
    )

    category_subparsers.add_parser(
        "add",
        help="새로운 카테고리를 추가합니다.",
    )

    category_subparsers.add_parser(
        "list",
        help="카테고리 목록을 조회합니다.",
    )

    category_subparsers.add_parser(
        "remove",
        help="카테고리를 삭제합니다.",
    )

    return parser


# 월별 거래 요약 명령을 처리
def handle_summary(
    transaction_service: TransactionService,
    month: str,
    top: int,
) -> None:
    try:
        summary = transaction_service.get_monthly_summary(
            month,
            top,
        )

        if summary["transaction_count"] == 0:
            print("[안내] 해당 월의 거래 데이터가 없습니다.")
            return

        print(f"총 수입: {summary['total_income']}원")
        print(f"총 지출: {summary['total_expense']}원")
        print(f"잔액: {summary['balance']}원")

        if summary["budget"] is not None:
            print(f"예산: {summary['budget']}원")
            print(f"예산 사용률: {summary['budget_usage']:.1f}%")

            if summary["budget_exceeded"]:
                print("[경고] 설정한 예산을 초과했습니다.")
        else:
            print("예산: 설정되지 않음")

        print(f"지출 TOP {top}")

        if not summary["top_categories"]:
            print("- 지출 내역 없음")
            return

        for index, (category, amount) in enumerate(
            summary["top_categories"],
            start=1,
        ):
            print(f"{index}) {category} {amount}원")

    except ValueError as error:
        print(f"[오류] {error}")
        print("[힌트] --month는 YYYY-MM 형식, --top은 1 이상의 정수로 입력하세요.")


# 월별 예산 설정 명령을 처리
def handle_budget_set(
    budget_service: BudgetService,
    month: str,
    amount: str,
) -> None:
    try:
        budget_service.set_budget(
            month,
            amount,
        )

        print(
            f"[저장 완료] "
            f"{month} 예산 = {int(amount)}원"
        )

    except ValueError as error:
        print(f"[오류] {error}")
        print("[힌트] --month는 YYYY-MM 형식, --amount는 0보다 큰 정수로 입력하세요.")


# 프로그램 실행에 필요한 저장소와 서비스를 생성
def main() -> None:
    parser = create_parser()
    args = parser.parse_args()

    budget_repository = BudgetRepository()
    transaction_repository = TransactionRepository()
    category_repository = CategoryRepository()

    budget_service = BudgetService(
        budget_repository,
    )

    transaction_service = TransactionService(
        transaction_repository,
        category_repository,
        budget_repository,
    )

    category_service = CategoryService(
        category_repository,
        transaction_repository,
    )

    if args.command == "add":
        handle_add(transaction_service)

    elif args.command == "list":
        handle_list(
            transaction_service,
            args.limit,
        )

    elif args.command == "search":
        handle_search(
            transaction_service,
            args,
        )

    elif args.command == "summary":
        handle_summary(
            transaction_service,
            args.month,
            args.top,
        )

    elif args.command == "budget":
        if args.budget_command == "set":
            handle_budget_set(
                budget_service,
                args.month,
                args.amount,
            )
        else:
            parser.print_help()

    elif args.command == "category":
        if args.category_command == "add":
            handle_category_add(category_service)

        elif args.category_command == "list":
            handle_category_list(category_service)

        elif args.category_command == "remove":
            handle_category_remove(category_service)

        else:
            parser.print_help()

    else:
        parser.print_help()