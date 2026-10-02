import csv
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

    # 저장된 모든 거래를 하나씩 반환
    def stream_all(self) -> Generator[Transaction, None, None]:
        with self.file_path.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if not line:
                    continue

                data = json.loads(line)

                yield Transaction.from_dict(data)

    # 저장된 거래를 최신순으로 하나씩 반환
    def stream_all_reverse(
        self,
    ) -> Generator[Transaction, None, None]:
        with self.file_path.open(
            "rb",
        ) as file:
            file.seek(0, 2)
            position = file.tell()
            line = bytearray()

            while position > 0:
                position -= 1
                file.seek(position)

                byte = file.read(1)

                if byte == b"\n":
                    if line:
                        decoded_line = bytes(
                            reversed(line)
                        ).decode("utf-8")

                        data = json.loads(decoded_line)

                        yield Transaction.from_dict(data)

                        line.clear()
                else:
                    line.append(byte[0])

            if line:
                decoded_line = bytes(
                    reversed(line)
                ).decode("utf-8")

                data = json.loads(decoded_line)

                yield Transaction.from_dict(data)

    # 전체 거래를 임시 파일에 저장한 뒤 기존 파일을 안전하게 교체
    def rewrite(self, transactions: list[Transaction]) -> None:
        temp_path = self.file_path.with_suffix(".tmp")

        with temp_path.open("w", encoding="utf-8") as file:
            for transaction in transactions:
                json_line = json.dumps(
                    transaction.to_dict(),
                    ensure_ascii=False,
                )
                file.write(json_line + "\n")

        temp_path.replace(self.file_path)

    # ID에 해당하는 거래를 수정
    def update(self, updated_transaction: Transaction) -> bool:
        transactions: list[Transaction] = []
        found = False

        for transaction in self.stream_all():
            if transaction.id == updated_transaction.id:
                transactions.append(updated_transaction)
                found = True
            else:
                transactions.append(transaction)

        if not found:
            return False

        self.rewrite(transactions)
        return True

    # ID에 해당하는 거래를 삭제
    def delete(self, transaction_id: str) -> bool:
        transactions: list[Transaction] = []
        found = False

        for transaction in self.stream_all():
            if transaction.id == transaction_id:
                found = True
                continue

            transactions.append(transaction)

        if not found:
            return False

        self.rewrite(transactions)
        return True

    # 전달받은 거래를 CSV 파일로 내보내기
    def export_csv(
        self,
        output_path: str,
        transactions: list[Transaction],
    ) -> int:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        count = 0

        with path.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "date",
                    "type",
                    "category",
                    "amount",
                    "memo",
                    "tags",
                ],
            )

            writer.writeheader()

            for transaction in transactions:
                writer.writerow({
                    "date": transaction.date,
                    "type": transaction.type,
                    "category": transaction.category,
                    "amount": transaction.amount,
                    "memo": transaction.memo,
                    "tags": ",".join(transaction.tags),
                })
                count += 1

        return count

    # CSV 파일의 거래 데이터를 하나씩 읽어 반환
    def stream_csv(
        self,
        input_path: str,
    ) -> Generator[dict, None, None]:
        path = Path(input_path)

        if not path.exists():
            raise FileNotFoundError(
                f"파일을 찾을 수 없습니다: {input_path}"
            )

        with path.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as file:
            reader = csv.DictReader(file)

            required_fields = {
                "date",
                "type",
                "category",
                "amount",
                "memo",
                "tags",
            }

            if (
                reader.fieldnames is None
                or not required_fields.issubset(reader.fieldnames)
            ):
                raise ValueError(
                    "CSV 헤더 형식이 올바르지 않습니다."
                )

            for row in reader:
                yield row


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