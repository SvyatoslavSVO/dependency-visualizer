import argparse
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--package", required=True)
    parser.add_argument("-u", "--url", required=True)
    parser.add_argument("-t", "--test-mode", action="store_true")
    parser.add_argument("-o", "--output", default="graph.png")
    parser.add_argument("-a", "--ascii-tree", action="store_true")
    parser.add_argument("-d", "--max-depth", type=int, default=3)
    return parser.parse_args()


def check_args(args):
    if not args.package.strip():
        raise ValueError("Пустое имя пакета")

    if args.max_depth < 0:
        raise ValueError("Глубина не может быть меньше 0")

    if not args.output.endswith(".png"):
        raise ValueError("Файл должен быть в формате .png")

    if args.test_mode:
        if not os.path.isfile(args.url):
            raise FileNotFoundError(f"Файл не найден: {args.url}")
        if not args.package.isupper() or not args.package.isalpha():
            raise ValueError(
                "Для тестов имя пакета должно быть из заглавных латинских букв"
            )
    else:
        if not (
            args.url.startswith("http://") or args.url.startswith("https://")
        ):
            raise ValueError("Некорректный URL репозитория")


def main():
    try:
        args = get_args()
        check_args(args)
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)

    print("Параметры:")
    for k, v in vars(args).items():
        print(f"{k} = {v}")


if __name__ == "__main__":
    main()