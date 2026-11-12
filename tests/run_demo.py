import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_PATH = os.path.join("src", "dep_visualizer.py")
TESTS_DIR = "tests"
REPORT_FILE = "report_output.txt"
NPM_URL = "https://registry.npmjs.org"
SEP_LEN = 60


def run_case(log_file, title, args):
    sep = "=" * SEP_LEN
    cmd_str = " ".join(args)
    header = f"\n{sep}\nТЕСТ: {title}\nКоманда: {cmd_str}\n{sep}\n"
    print(header, end="")
    log_file.write(header)

    cmd = [sys.executable, SCRIPT_PATH] + args
    res = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8"
    )

    if res.stdout:
        print(res.stdout, end="")
        log_file.write(res.stdout)
    if res.stderr:
        err_msg = f"[STDERR]: {res.stderr}"
        print(err_msg, end="")
        log_file.write(err_msg)


def run_stage_1_and_2(log):
    t_lin = os.path.join(TESTS_DIR, "test_linear.json")
    a1 = ["-p", "A", "-u", t_lin, "-t", "-o", "stage1.png"]
    run_case(log, "Этап 1: Базовый запуск", a1)

    a2 = ["-p", "A", "-u", t_lin, "-t", "-d", "-1"]
    run_case(log, "Этап 1: Ошибка глубины", a2)

    a3 = ["-p", "pkg1", "-u", t_lin, "-t"]
    run_case(log, "Этап 1: Ошибка имени", a3)

    a4 = ["-p", "express", "-u", NPM_URL, "-d", "1", "-o", "p1.png"]
    run_case(log, "Этап 2: Пакет express", a4)


def run_stage_3(log):
    t_lin = os.path.join(TESTS_DIR, "test_linear.json")
    t_dia = os.path.join(TESTS_DIR, "test_diamond.json")
    t_cyc = os.path.join(TESTS_DIR, "test_cycles.json")

    a1 = ["-p", "A", "-u", t_lin, "-t", "-d", "4", "-a", "-o", "l.png"]
    run_case(log, "Этап 3: Линейный граф", a1)

    a2 = ["-p", "A", "-u", t_dia, "-t", "-d", "3", "-a", "-o", "d.png"]
    run_case(log, "Этап 3: Ромбовидный граф", a2)

    a3 = ["-p", "A", "-u", t_cyc, "-t", "-d", "5", "-a", "-o", "c.png"]
    run_case(log, "Этап 3: Граф с циклами", a3)


def run_stage_4_and_5(log):
    t_dia = os.path.join(TESTS_DIR, "test_diamond.json")
    t_cpx = os.path.join(TESTS_DIR, "test_complex.txt")

    a1 = ["-p", "A", "-u", t_dia, "-t", "-l", "-o", "ord1.png"]
    run_case(log, "Этап 4: Порядок загрузки (ромб)", a1)

    a2 = ["-p", "A", "-u", t_cpx, "-t", "-l", "-a", "-o", "ord2.png"]
    run_case(log, "Этап 4: Порядок загрузки (сложный)", a2)

    a3 = [
        "-p", "body-parser", "-u", NPM_URL,
        "-d", "2", "-a", "-l", "-o", "bp.png",
    ]
    run_case(log, "Этап 5: Визуализация body-parser", a3)


def main():
    with open(REPORT_FILE, "w", encoding="utf-8") as log:
        run_stage_1_and_2(log)
        run_stage_3(log)
        run_stage_4_and_5(log)
    print(f"\nВсе тесты завершены. Отчет: {REPORT_FILE}")


if __name__ == "__main__":
    main()
