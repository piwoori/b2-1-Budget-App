from budget_app.models import Transaction
from budget_app.repository import (
    CategoryRepository,
    TransactionRepository,
)
from budget_app.validators import (
    validate_amount,
    validate_category,
    validate_date,
    validate_type,
)


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
    def __init__(
        self,
        transaction_repository: TransactionRepository,
        category_repository: CategoryRepository,
    ) -> None:
        self.transaction_repository = transaction_repository
        self.category_repository = category_repository

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