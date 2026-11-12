import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

HTTP_NOT_FOUND = 404
DEFAULT_TIMEOUT = 10
DEFAULT_DEPTH = 3
MIN_DEPTH = 0
ROOT_DEPTH = 0
STEP = 1


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--package", required=True)
    parser.add_argument("-u", "--url", required=True)
    parser.add_argument("-t", "--test-mode", action="store_true")
    parser.add_argument("-o", "--output", default="graph.png")
    parser.add_argument("-a", "--ascii-tree", action="store_true")
    parser.add_argument("-d", "--max-depth", type=int, default=DEFAULT_DEPTH)
    parser.add_argument("-l", "--load-order", action="store_true")
    return parser.parse_args()


def validate_test_args(args):
    if not os.path.isfile(args.url):
        raise FileNotFoundError(f"Файл не найден: {args.url}")
    if not args.package.isupper() or not args.package.isalpha():
        msg = "Имя пакета должно быть из заглавных латинских букв"
        raise ValueError(msg)


def validate_url_args(args):
    is_http = args.url.startswith("http://")
    is_https = args.url.startswith("https://")
    if not (is_http or is_https):
        raise ValueError("Некорректный URL репозитория")


def check_args(args):
    if not args.package.strip():
        raise ValueError("Пустое имя пакета")
    if args.max_depth < MIN_DEPTH:
        raise ValueError("Глубина не может быть меньше 0")
    if not args.output.endswith(".png"):
        raise ValueError("Файл должен быть в формате .png")
    if args.test_mode:
        validate_test_args(args)
    else:
        validate_url_args(args)


def parse_json_repo(text):
    repo = {}
    data = json.loads(text)
    for key, val in data.items():
        if not key.isupper() or not key.isalpha():
            raise ValueError(f"Неверное имя пакета: {key}")
        repo[key] = list(val)
    return repo


def parse_text_repo(text):
    repo = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if ":" not in line:
            raise ValueError(f"Ошибка в строке: {line}")
        pkg, deps = line.split(":", STEP)
        items = [x.strip() for x in deps.split(",") if x.strip()]
        repo[pkg.strip()] = items
    return repo


def read_test_repo(path):
    with open(path, "r", encoding="utf-8") as file_obj:
        text = file_obj.read().strip()
    if text.startswith("{"):
        return parse_json_repo(text)
    return parse_text_repo(text)


def fetch_fallback_npm(pkg, base_url):
    url = f"{base_url}/{pkg}"
    try:
        with urllib.request.urlopen(url, timeout=DEFAULT_TIMEOUT) as resp:
            full = json.loads(resp.read().decode("utf-8"))
            ver = full.get("dist-tags", {}).get("latest")
            if ver:
                versions = full.get("versions", {})
                deps = versions.get(ver, {}).get("dependencies", {})
                return list(deps.keys())
    except Exception:
        pass
    raise RuntimeError(f"Пакет {pkg} не найден")


def get_npm_deps(pkg, base_url):
    clean_url = base_url.rstrip("/")
    url = f"{clean_url}/{pkg}/latest"
    headers = {"Accept": "application/json"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return list(data.get("dependencies", {}).keys())
    except urllib.error.HTTPError as err:
        if err.code == HTTP_NOT_FOUND:
            return fetch_fallback_npm(pkg, clean_url)
        raise RuntimeError(f"Ошибка HTTP: {err.code}")
    except urllib.error.URLError as err:
        raise RuntimeError(f"Ошибка сети: {err.reason}")


def resolve_pkg_deps(pkg, is_test, url, test_repo):
    if is_test:
        return test_repo.get(pkg, [])
    try:
        return get_npm_deps(pkg, url)
    except Exception as err:
        print(f"Ошибка для {pkg}: {err}", file=sys.stderr)
        return []


def push_children(stack, graph, deps, next_depth):
    for dep in reversed(deps):
        if dep not in graph:
            graph[dep] = []
        stack.append((dep, next_depth))


def build_graph(root, max_depth, is_test, url, test_repo=None):
    graph = {}
    stack = [(root, ROOT_DEPTH)]
    visited = {}

    while stack:
        pkg, depth = stack.pop()
        if pkg in visited and visited[pkg] <= depth:
            continue
        visited[pkg] = depth

        if depth >= max_depth:
            graph.setdefault(pkg, [])
            continue

        if pkg not in graph:
            graph[pkg] = resolve_pkg_deps(pkg, is_test, url, test_repo)

        push_children(stack, graph, graph[pkg], depth + STEP)

    return graph


def enqueue_unvisited_deps(stack, deps, visited, in_stack):
    for dep in reversed(deps):
        if dep not in visited and dep not in in_stack:
            stack.append((dep, False))


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
        deps = graph.get(node, [])
        enqueue_unvisited_deps(stack, deps, visited, in_stack)

    return order


def format_tree_node(node, pref, is_last, depth, in_path):
    if depth == ROOT_DEPTH:
        print(node)
        return False
    branch = "└── " if is_last else "├── "
    if in_path:
        print(f"{pref}{branch}{node} (цикл)")
        return True
    print(f"{pref}{branch}{node}")
    return False


def push_tree_children(stack, children, new_pref, next_depth, new_path):
    last_idx = len(children) - STEP
    for idx in range(last_idx, -STEP, -STEP):
        is_last = idx == last_idx
        item = (children[idx], new_pref, is_last, next_depth, new_path)
        stack.append(item)


def show_tree(graph, root, max_depth):
    print("\nДерево зависимостей:")
    stack = [(root, "", True, ROOT_DEPTH, set())]

    while stack:
        node, pref, is_last, depth, path = stack.pop()
        is_cycle = format_tree_node(node, pref, is_last, depth, node in path)
        if is_cycle or depth >= max_depth:
            continue

        children = graph.get(node, [])
        new_path = path | {node}
        pad = "" if depth == ROOT_DEPTH else ("    " if is_last else "│   ")
        push_tree_children(stack, children, pref + pad, depth + STEP, new_path)


def build_dot_text(graph):
    lines = ["digraph G {"]
    for pkg, deps in graph.items():
        lines.append(f'    "{pkg}";')
        for dep in deps:
            lines.append(f'    "{pkg}" -> "{dep}";')
    lines.append("}")
    return "\n".join(lines)


def render_remote_png(dot_text, out_file):
    try:
        params = urllib.parse.urlencode({"graph": dot_text, "format": "png"})
        url = f"https://quickchart.io/graphviz?{params}"
        headers = {"User-Agent": "Mozilla/5.0"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
            with open(out_file, "wb") as img:
                img.write(resp.read())
        print(f"\nГраф сохранен в {out_file}")
    except Exception:
        pass


def make_graphviz(graph, out_file):
    dot_text = build_dot_text(graph)
    dot_file = os.path.splitext(out_file)[0] + ".dot"
    with open(dot_file, "w", encoding="utf-8") as file_obj:
        file_obj.write(dot_text)

    try:
        cmd = ["dot", "-Tpng", dot_file, "-o", out_file]
        subprocess.run(
            cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print(f"\nГраф сохранен в {out_file}")
    except (FileNotFoundError, subprocess.CalledProcessError):
        render_remote_png(dot_text, out_file)

    return dot_text


def load_test_data(args):
    if not args.test_mode:
        return None
    try:
        return read_test_repo(args.url)
    except Exception as err:
        print(f"Ошибка чтения файла: {err}", file=sys.stderr)
        sys.exit(STEP)


def main():
    try:
        args = get_args()
        check_args(args)
    except Exception as err:
        print(f"Ошибка: {err}", file=sys.stderr)
        sys.exit(STEP)

    test_repo = load_test_data(args)
    graph = build_graph(
        args.package, args.max_depth, args.test_mode, args.url, test_repo
    )

    if args.load_order:
        print("\nПорядок загрузки:")
        order = calc_load_order(graph, args.package)
        print(" -> ".join(order))

    if args.ascii_tree:
        show_tree(graph, args.package, args.max_depth)

    dot_code = make_graphviz(graph, args.output)
    print("\nКод Graphviz:")
    print(dot_code)


if __name__ == "__main__":
    main()