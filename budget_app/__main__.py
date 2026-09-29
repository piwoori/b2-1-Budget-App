import sys

from budget_app.cli import main


# 프로그램을 실행하고 반환된 종료 코드를 시스템에 전달
def run() -> None:
    exit_code = main()
    sys.exit(exit_code)


if __name__ == "__main__":
    run()