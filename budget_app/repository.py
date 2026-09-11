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

    def save(self, transaction: Transaction) -> None:
        with self.file_path.open("a", encoding="utf-8") as file:
            json_line = json.dumps(
                transaction.to_dict(),
                ensure_ascii=False
            )

            file.write(json_line + "\n")

    def stream_all(self) -> Generator[Transaction, None, None]:
        with self.file_path.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if not line:
                    continue

                data = json.loads(line)

                yield Transaction.from_dict(data)