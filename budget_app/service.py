from budget_app.models import Transaction
from budget_app.repository import (
    BudgetRepository,
    CategoryRepository,
    TransactionRepository,
)
from budget_app.validators import (
    validate_amount,
    validate_category,
    validate_date,
    validate_month,
    validate_type,
)


class BudgetService:
    # 예산 저장소를 전달받아 초기화
    def __init__(
        self,
        budget_repository: BudgetRepository,
    ) -> None:
        self.budget_repository = budget_repository

    # 월과 금액을 검증한 뒤 예산을 저장
    def set_budget(
        self,
        month: str,
        amount: str,
    ) -> None:
        if not validate_month(month):
            raise ValueError("월 형식이 올바르지 않습니다.")

        if not validate_amount(amount):
            raise ValueError("예산은 0보다 큰 정수여야 합니다.")

        self.budget_repository.set(
            month,
            int(amount),
        )

    # 특정 월에 설정된 예산을 조회
    def get_budget(self, month: str) -> int | None:
        if not validate_month(month):
            raise ValueError("월 형식이 올바르지 않습니다.")

        return self.budget_repository.get(month)


class CategoryService:
    def __init__(
        self,
        category_repository: CategoryRepository,
        transaction_repository: TransactionRepository,
    ) -> None:
        self.category_repository = category_repository
        self.transaction_repository = transaction_repository

    # 새로운 카테고리를 추가
    def add_category(self, category: str) -> bool:
        category = category.strip()

        if not category:
            return False

        if self.category_repository.exists(category):
            return False

        self.category_repository.save(category)
        return True

    # 저장된 모든 카테고리를 목록으로 반환
    def get_categories(self) -> list[str]:
        return list(self.category_repository.stream_all())

    # 카테고리를 사용 중인 거래가 있는지 확인
    def is_category_in_use(self, category: str) -> bool:
        return any(
            transaction.category == category
            for transaction in self.transaction_repository.stream_all()
        )

    # 사용 중이지 않은 카테고리를 삭제
    def remove_category(self, category: str) -> bool:
        if not self.category_repository.exists(category):
            return False

        if self.is_category_in_use(category):
            return False

        return self.category_repository.delete(category)


class TransactionService:
    # 거래, 카테고리, 예산 저장소를 전달받아 초기화
    def __init__(
        self,
        transaction_repository: TransactionRepository,
        category_repository: CategoryRepository,
        budget_repository: BudgetRepository,
    ) -> None:
        self.transaction_repository = transaction_repository
        self.category_repository = category_repository
        self.budget_repository = budget_repository

    # 다음 거래 ID를 생성
    def generate_id(self) -> str:
        max_number = 0

        for transaction in self.transaction_repository.stream_all():
            try:
                number = int(transaction.id.replace("TX-", ""))
                max_number = max(max_number, number)
            except ValueError:
                continue

        return f"TX-{max_number + 1:06d}"

    # 입력값을 검증하고 새로운 거래를 추가
    def add_transaction(
        self,
        date: str,
        transaction_type: str,
        category: str,
        amount: str,
        memo: str = "",
        tags: list[str] | None = None,
    ) -> Transaction:
        categories = list(self.category_repository.stream_all())

        if not validate_date(date):
            raise ValueError("날짜 형식이 올바르지 않습니다.")

        if not validate_type(transaction_type):
            raise ValueError("거래 타입은 income 또는 expense여야 합니다.")

        if not validate_category(category, categories):
            raise ValueError("등록되지 않은 카테고리입니다.")

        if not validate_amount(amount):
            raise ValueError("금액은 0보다 큰 정수여야 합니다.")

        transaction = Transaction(
            id=self.generate_id(),
            type=transaction_type,
            date=date,
            amount=int(amount),
            category=category,
            memo=memo.strip(),
            tags=tags or [],
        )

        self.transaction_repository.save(transaction)

        return transaction

    # 최신 거래를 지정한 개수만큼 조회
    def get_transactions(self, limit: int = 10) -> list[Transaction]:
        if limit <= 0:
            raise ValueError("limit은 1 이상의 정수여야 합니다.")

        recent_transactions: list[Transaction] = []

        for transaction in self.transaction_repository.stream_all():
            recent_transactions.append(transaction)

            if len(recent_transactions) > limit:
                recent_transactions.pop(0)

        recent_transactions.reverse()

        return recent_transactions

    # 조건에 맞는 거래를 검색
    def search_transactions(
        self,
        from_date: str | None = None,
        to_date: str | None = None,
        category: str | None = None,
        transaction_type: str | None = None,
        query: str | None = None,
        tag: str | None = None,
    ) -> list[Transaction]:

        if from_date and not validate_date(from_date):
            raise ValueError("--from 날짜 형식이 올바르지 않습니다.")

        if to_date and not validate_date(to_date):
            raise ValueError("--to 날짜 형식이 올바르지 않습니다.")

        if transaction_type and not validate_type(transaction_type):
            raise ValueError("--type은 income 또는 expense여야 합니다.")

        if from_date and to_date and from_date > to_date:
            raise ValueError("--from은 --to보다 늦을 수 없습니다.")

        results: list[Transaction] = []

        for transaction in self.transaction_repository.stream_all():
            if from_date and transaction.date < from_date:
                continue

            if to_date and transaction.date > to_date:
                continue

            if category and transaction.category != category:
                continue

            if transaction_type and transaction.type != transaction_type:
                continue

            if query and query.lower() not in transaction.memo.lower():
                continue

            if tag and tag not in transaction.tags:
                continue

            results.append(transaction)

        results.reverse()

        return results

    # 특정 월의 수입, 지출, 잔액과 카테고리별 지출을 요약
    def get_monthly_summary(
        self,
        month: str,
        top: int = 3,
    ) -> dict:
        if not validate_month(month):
            raise ValueError("월 형식이 올바르지 않습니다.")

        if top <= 0:
            raise ValueError("top은 1 이상의 정수여야 합니다.")

        total_income = 0
        total_expense = 0
        category_expenses: dict[str, int] = {}
        transaction_count = 0

        for transaction in self.transaction_repository.stream_all():
            if not transaction.date.startswith(month):
                continue

            transaction_count += 1

            if transaction.type == "income":
                total_income += transaction.amount

            elif transaction.type == "expense":
                total_expense += transaction.amount

                category_expenses[transaction.category] = (
                    category_expenses.get(transaction.category, 0)
                    + transaction.amount
                )

        top_categories = sorted(
            category_expenses.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:top]

        budget = self.budget_repository.get(month)

        budget_usage = None
        budget_exceeded = False

        if budget is not None:
            budget_usage = (total_expense / budget) * 100
            budget_exceeded = total_expense > budget

        return {
            "transaction_count": transaction_count,
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense,
            "top_categories": top_categories,
            "budget": budget,
            "budget_usage": budget_usage,
            "budget_exceeded": budget_exceeded,
        }