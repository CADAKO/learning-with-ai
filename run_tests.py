# run_tests.py
import subprocess
import os
import shutil


def run_command(command, check=True):
    """Вспомогательная функция для выполнения команд в терминале."""
    print(f"--> Выполняю команду: {' '.join(command)}")
    try:
        subprocess.run(command, check=check, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка выполнения команды: {e}")
        exit(1)


def main():
    # 1. Подготовка папки для результатов Allure
    allure_results_dir = "allure-results"
    if os.path.exists(allure_results_dir):
        shutil.rmtree(allure_results_dir)
    os.makedirs(allure_results_dir, exist_ok=True)

    # 2. Сборка образов Docker
    print("\n--- Сборка Docker образов ---")
    run_command(["docker-compose", "build", "tests", "api", "discount"])

    # 3. Запуск тестов внутри Docker контейнера
    print("\n--- Запуск тестов и генерация сырых данных Allure ---")
    # Обратите внимание: мы не используем 'docker compose down' здесь,
    # потому что 'run --rm' сам остановит зависимые сервисы после завершения тестов
    try:
        run_command(["docker-compose", "run", "--rm", "tests"])

        # 4. Генерация HTML-отчета Allure (требует локально установленного Allure CLI)
        print("\n--- Генерация Allure отчета ---")
        allure_report_dir = "allure-report"
        if os.path.exists(allure_report_dir):
            shutil.rmtree(allure_report_dir)

        run_command(["allure", "generate", allure_results_dir, "--clean", "-o", allure_report_dir])

        # 5. Открытие отчета в браузере
        print("\n--- Открытие отчета в браузере ---")
        run_command(["allure", "open", allure_report_dir], check=False)
    except subprocess.CalledProcessError:
        print("\n!!! Tests Failed")
    finally:
        print("\n--- Очистка Docker окружения ---")
        run_command(["docker-compose", "down"], check=False)


if __name__ == "__main__":
    main()
