# run_tests.py
import subprocess
import os
import shutil
import platform


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

    # Используем переменную для отслеживания статуса тестов
    tests_passed = False

    try:
        # Запускаем тесты. Если падает, здесь будет исключение CalledProcessError
        run_command(["docker-compose", "run", "--rm", "tests"], check=True)
        tests_passed = True  # Если дошли до сюда, значит, все тесты прошли успешно

    except subprocess.CalledProcessError:
        # Если тесты упали, мы попадаем сюда
        print("\n!!! ТЕСТЫ ПРОВАЛИЛИСЬ !!!")
        tests_passed = False  # Явно указываем, что тесты не прошли

    finally:
        # --- Этот блок выполняется ВСЕГДА (успех или провал) ---
        # Очистка Docker окружения
        print("\n--- Очистка Docker окружения ---")
        run_command(["docker-compose", "down"], check=False)
        # 4. Генерируем Allure отчет (и при успехе, и при провале)
        print("\n--- Генерация Allure отчета ---")
        allure_report_dir = "allure-report"
        if os.path.exists(allure_report_dir):
            shutil.rmtree(allure_report_dir)

        # check=False, потому что 'generate' может вернуть ошибку, если нет результатов (хотя это маловероятно)
        run_command(["allure", "generate", allure_results_dir, "--clean", "-o", allure_report_dir], check=False)

        # 5. Открываем отчет в браузере (используя улучшенный способ для Windows, если вы его добавили)
        print("\n--- Открытие отчета в браузере ---")
        # Здесь используйте ваш код для открытия отчета из предыдущего ответа
        # run_command(["allure", "open", allure_report_dir], check=False)
        command = ["allure", "open", allure_report_dir]

        if platform.system() == 'Windows':
            # Используем 'start', чтобы запустить в новом независимом процессе
            # Это предотвращает зависание основного скрипта
            subprocess.Popen(['start'] + command, shell=True)
        else:
            # В Linux/macOS используем run_command, как раньше
            run_command(command, check=False)
        # Опционально: Выйти из скрипта с кодом 1, если тесты упали, чтобы CI/CD знал об этом
        if not tests_passed:
            exit(1)


if __name__ == "__main__":
    main()
