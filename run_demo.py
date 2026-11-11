import json
import os
import subprocess
import sys

linear = {"A": ["B"], "B": ["C"], "C": ["D"], "D": ["E"], "E": ["F"], "F": []}
diamond = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": ["E"], "E": []}
cycles = {
    "A": ["B", "C"],
    "B": ["C", "D"],
    "C": ["B", "E"],
    "D": ["A", "F"],
    "E": [],
    "F": [],
}
text_repo = "A: B, C, D\nB: E, F\nC: F\nD: G\nE: G\nF: G\nG:\n"


def make_files():
    with open("test_linear.json", "w", encoding="utf-8") as f:
        json.dump(linear, f, indent=2)
    with open("test_diamond.json", "w", encoding="utf-8") as f:
        json.dump(diamond, f, indent=2)
    with open("test_cycles.json", "w", encoding="utf-8") as f:
        json.dump(cycles, f, indent=2)
    with open("test_complex.txt", "w", encoding="utf-8") as f:
        f.write(text_repo)


def run_test(name, args):
    print(f"--- {name} ---")
    print("Команда: python dep_visualizer.py " + " ".join(args))
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    res = subprocess.run(
        [sys.executable, "dep_visualizer.py"] + args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    if res.stdout:
        print(res.stdout.strip())
    if res.stderr:
        print(res.stderr.strip())
    print()


def main():
    with open("report_output.txt", "w", encoding="utf-8") as f:
        sys.stdout = f
        sys.stderr = f

        make_files()

        print("ЭТАП 1\n")
        run_test(
            "Вывод параметров",
            [
                "-p",
                "A",
                "-u",
                "test_diamond.json",
                "-t",
                "-o",
                "stage1.png",
                "-d",
                "2",
            ],
        )
        run_test(
            "Ошибка: пустое имя", ["-p", " ", "-u", "https://registry.npmjs.org"]
        )
        run_test(
            "Ошибка: неверный URL",
            ["-p", "express", "-u", "ftp://registry.npmjs.org"],
        )
        run_test("Ошибка: нет файла", ["-p", "A", "-u", "missing.json", "-t"])
        run_test(
            "Ошибка: имя пакета в тесте",
            ["-p", "pkg1", "-u", "test_diamond.json", "-t"],
        )
        run_test(
            "Ошибка: глубина < 0",
            ["-p", "A", "-u", "test_diamond.json", "-t", "-d", "-1"],
        )
        run_test(
            "Ошибка: формат файла",
            ["-p", "A", "-u", "test_diamond.json", "-t", "-o", "out.jpg"],
        )

        print("ЭТАП 2\n")
        run_test(
            "Прямые зависимости body-parser",
            [
                "-p",
                "body-parser",
                "-u",
                "https://registry.npmjs.org",
                "-d",
                "1",
                "-o",
                "bp.png",
            ],
        )

        print("ЭТАП 3\n")
        run_test(
            "Линейный граф (глубина 3)",
            [
                "-p",
                "A",
                "-u",
                "test_linear.json",
                "-t",
                "-d",
                "3",
                "-a",
                "-o",
                "linear.png",
            ],
        )
        run_test(
            "Ромбовидный граф",
            [
                "-p",
                "A",
                "-u",
                "test_diamond.json",
                "-t",
                "-d",
                "5",
                "-a",
                "-o",
                "diamond.png",
            ],
        )
        run_test(
            "Граф с циклами",
            [
                "-p",
                "A",
                "-u",
                "test_cycles.json",
                "-t",
                "-d",
                "6",
                "-a",
                "-o",
                "cycles.png",
            ],
        )

        print("ЭТАП 4\n")
        run_test(
            "Порядок загрузки (ромб)",
            [
                "-p",
                "A",
                "-u",
                "test_diamond.json",
                "-t",
                "-d",
                "5",
                "-l",
                "-o",
                "ord1.png",
            ],
        )
        run_test(
            "Порядок загрузки (текстовый репо)",
            [
                "-p",
                "A",
                "-u",
                "test_complex.txt",
                "-t",
                "-d",
                "5",
                "-l",
                "-o",
                "ord2.png",
            ],
        )
        run_test(
            "Порядок загрузки (циклы)",
            [
                "-p",
                "A",
                "-u",
                "test_cycles.json",
                "-t",
                "-d",
                "5",
                "-l",
                "-o",
                "ord3.png",
            ],
        )

        print("ЭТАП 5\n")
        run_test(
            "Пакет cookie-signature",
            [
                "-p",
                "cookie-signature",
                "-u",
                "https://registry.npmjs.org",
                "-d",
                "2",
                "-a",
                "-o",
                "pkg1.png",
            ],
        )
        run_test(
            "Пакет http-errors",
            [
                "-p",
                "http-errors",
                "-u",
                "https://registry.npmjs.org",
                "-d",
                "2",
                "-a",
                "-o",
                "pkg2.png",
            ],
        )
        run_test(
            "Пакет send",
            [
                "-p",
                "send",
                "-u",
                "https://registry.npmjs.org",
                "-d",
                "2",
                "-a",
                "-o",
                "pkg3.png",
            ],
        )


if __name__ == "__main__":
    main()