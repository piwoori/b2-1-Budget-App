import json
from pathlib import Path
from typing import Generator

from budget_app.models import Transaction


class TransactionRepository:
    def __init__(self, file_path: str = "data/transactions.jsonl") -> None:
        self.file_path = Path(file_path)

        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.file_path.exists():
            self.file_path.touch()

    # 거래 내역 저장
    def save(self, transaction: Transaction) -> None:
        with self.file_path.open("a", encoding="utf-8") as file:
            json_line = json.dumps(
                transaction.to_dict(),
                ensure_ascii=False
            )

            file.write(json_line + "\n")

    # 저장된 모든 카테고리를 하나씩 반환
    def stream_all(self) -> Generator[Transaction, None, None]:
        with self.file_path.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if not line:
                    continue

                data = json.loads(line)

                yield Transaction.from_dict(data)


class CategoryRepository:
    def __init__(self, file_path: str = "data/categories.jsonl") -> None:
        self.file_path = Path(file_path)

        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.file_path.exists():
            self.file_path.touch()

    # 카테고리 jsonl에 저장
    def save(self, category: str) -> None:
        with self.file_path.open("a", encoding="utf-8") as file:
            data = {"name": category}
            file.write(json.dumps(data, ensure_ascii=False) + "\n")

    # 한꺼번에 list로 읽지 않고 yield 처리
    def stream_all(self) -> Generator[str, None, None]:
        with self.file_path.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if not line:
                    continue

                data = json.loads(line)
                yield data["name"]

    # 해당 카테고리가 저장되어 있는지 확인
    def exists(self, category: str) -> bool:
        return any(
            saved_category == category
            for saved_category in self.stream_all()
        )


    # 저장된 카테고리를 삭제 (특정 행 하나만 삭제할 수 없기에 지우고 남은 것들만 다시 저장)
    def delete(self, category: str) -> bool:
        if not self.exists(category):
            return False

        categories = [
            saved_category
            for saved_category in self.stream_all()
            if saved_category != category
        ]

        with self.file_path.open("w", encoding="utf-8") as file:
            for saved_category in categories:
                data = {"name": saved_category}
                file.write(json.dumps(data, ensure_ascii=False) + "\n")

        return True


class BudgetRepository:
    def __init__(self, file_path: str = "data/budgets.jsonl") -> None:
        self.file_path = Path(file_path)

        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.file_path.exists():
            self.file_path.touch()

    # 월별 예산을 저장하거나 기존 예산을 수정
    def set(self, month: str, amount: int) -> None:
        budgets = {
            saved_month: saved_amount
            for saved_month, saved_amount in self.stream_all()
        }

        budgets[month] = amount

        with self.file_path.open("w", encoding="utf-8") as file:
            for saved_month, saved_amount in budgets.items():
                data = {
                    "month": saved_month,
                    "amount": saved_amount
                }
                file.write(json.dumps(data, ensure_ascii=False) + "\n")

    # 저장된 모든 월별 예산을 하나씩 반환
    def stream_all(self) -> Generator[tuple[str, int], None, None]:
        with self.file_path.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if not line:
                    continue

                data = json.loads(line)

                yield data["month"], int(data["amount"])

    # 특정 월에 설정된 예산을 조회
    def get(self, month: str) -> int | None:
        for saved_month, amount in self.stream_all():
            if saved_month == month:
                return amount

        return None