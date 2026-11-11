import argparse
import json
import os
import sys
import urllib.error
import urllib.request

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


def get_npm_deps(pkg, base_url):
    base_url = base_url.rstrip("/")
    url = f"{base_url}/{pkg}/latest"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return list(data.get("dependencies", {}).keys())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            try:
                with urllib.request.urlopen(
                    f"{base_url}/{pkg}", timeout=10
                ) as resp:
                    full = json.loads(resp.read().decode("utf-8"))
                    ver = full.get("dist-tags", {}).get("latest")
                    if ver:
                        deps = (
                            full.get("versions", {})
                            .get(ver, {})
                            .get("dependencies", {})
                        )
                        return list(deps.keys())
            except Exception:
                pass
            raise RuntimeError(f"Пакет {pkg} не найден")
        raise RuntimeError(f"Ошибка HTTP: {e.code}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Ошибка сети: {e.reason}")


def main():
    try:
        args = get_args()
        check_args(args)
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        deps = get_npm_deps(args.package, args.url)
        print(f"Прямые зависимости {args.package}:")
        if deps:
            for d in deps:
                print(f"- {d}")
        else:
            print("нет")
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()