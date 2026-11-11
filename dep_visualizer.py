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
    parser.add_argument("-l", "--load-order", action="store_true")
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


def read_test_repo(path):
    repo = {}
    with open(path, "r", encoding="utf-8") as f:
        text = f.read().strip()
        if text.startswith("{"):
            data = json.loads(text)
            for k, v in data.items():
                if not k.isupper() or not k.isalpha():
                    raise ValueError(f"Неверное имя пакета в файле: {k}")
                repo[k] = list(v)
        else:
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                if ":" not in line:
                    raise ValueError(f"Ошибка в строке: {line}")
                pkg, deps = line.split(":", 1)
                repo[pkg.strip()] = [
                    x.strip() for x in deps.split(",") if x.strip()
                ]
    return repo


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


def build_graph(root, max_depth, is_test, url, test_repo=None):
    graph = {}
    stack = [(root, 0)]
    visited = {}

    while stack:
        pkg, depth = stack.pop()

        if pkg in visited and visited[pkg] <= depth:
            continue
        visited[pkg] = depth

        if depth >= max_depth:
            if pkg not in graph:
                graph[pkg] = []
            continue

        if pkg not in graph:
            if is_test:
                deps = test_repo.get(pkg, [])
            else:
                try:
                    deps = get_npm_deps(pkg, url)
                except Exception as e:
                    print(f"Ошибка для {pkg}: {e}", file=sys.stderr)
                    deps = []
            graph[pkg] = deps
        else:
            deps = graph[pkg]

        for d in reversed(deps):
            if d not in graph:
                graph[d] = []
            stack.append((d, depth + 1))

    return graph


def calc_load_order(graph, root):
    order = []
    visited = set()
    in_stack = set()
    stack = [(root, False)]

    while stack:
        node, done = stack.pop()

        if done:
            in_stack.discard(node)
            if node not in visited:
                visited.add(node)
                order.append(node)
            continue

        if node in visited or node in in_stack:
            continue

        in_stack.add(node)
        stack.append((node, True))

        for dep in reversed(graph.get(node, [])):
            if dep not in visited and dep not in in_stack:
                stack.append((dep, False))

    return order


def main():
    try:
        args = get_args()
        check_args(args)
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)

    test_repo = None
    if args.test_mode:
        try:
            test_repo = read_test_repo(args.url)
        except Exception as e:
            print(f"Ошибка чтения файла: {e}", file=sys.stderr)
            sys.exit(1)

    graph = build_graph(
        args.package, args.max_depth, args.test_mode, args.url, test_repo
    )

    if args.load_order:
        print("Порядок загрузки:")
        order = calc_load_order(graph, args.package)
        print(" -> ".join(order))


if __name__ == "__main__":
    main()