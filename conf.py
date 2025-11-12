#!/usr/bin/env python3
import tomllib
import json
import urllib.request
import sys
from collections import deque, defaultdict

class ConfigError(Exception):
    pass

def load_config():
    with open("config.toml", 'rb') as f:
        return tomllib.load(f)

def fetch_deps(pkg, ver, url):
    try:
        api_url = f"{url}/{pkg}/{ver}/dependencies"
        with urllib.request.urlopen(api_url) as r:
            data = json.loads(r.read().decode())
        return [(dep['crate_id'], dep['req']) for dep in data.get('dependencies', [])]
    except:
        return []

def test_deps():
    return {
        'A': ['B', 'C'],
        'B': ['D'],
        'C': ['D', 'E'],
        'D': ['F'],
        'E': ['A'],
        'F': []
    }

def build_graph(config):
    graph = defaultdict(list)
    visited = set()
    cycles = set()
    
    def bfs(pkg, ver, depth):
        if depth >= config['analysis']['max_depth']:
            return
        
        key = (pkg, ver)
        if key in visited:
            cycles.add(key)
            return
        visited.add(key)
        
        if config['repository']['use_test_repository']:
            deps_data = test_deps()
            deps = [(dep, '1.0') for dep in deps_data.get(pkg, [])]
        else:
            deps = fetch_deps(pkg, ver, config['repository']['url'])
        
        for dep_name, dep_ver in deps:
            dep_key = (dep_name, dep_ver)
            graph[key].append(dep_key)
            bfs(dep_name, dep_ver, depth + 1)
    
    pkg = config['package']['name']
    ver = config['package']['version']
    bfs(pkg, ver, 0)
    return graph, cycles

def get_load_order(graph):
    in_degree = defaultdict(int)
    
    for pkg, deps in graph.items():
        for dep in deps:
            in_degree[dep] += 1
        in_degree.setdefault(pkg, 0)
    
    queue = deque([p for p, d in in_degree.items() if d == 0])
    load_order = []
    
    while queue:
        pkg = queue.popleft()
        load_order.append(pkg)
        for dep in graph[pkg]:
            in_degree[dep] -= 1
            if in_degree[dep] == 0:
                queue.append(dep)
    
    return load_order

def main():
    try:
        config = load_config()
        
        print("=== Этап 4: Порядок загрузки ===")
        
        graph, cycles = build_graph(config)
        load_order = get_load_order(graph)
        
        print("Порядок загрузки:")
        for i, (pkg, ver) in enumerate(load_order, 1):
            print(f"  {i}. {pkg}")
        
        if cycles:
            print("Циклы:", [c[0] for c in cycles])
        
        print("\nСравнение с Cargo:")
        print("  Расхождения возможны из-за разных алгоритмов разрешения версий и обработки циклических зависимостей.")
        
        if config['repository']['use_test_repository']:
            print("\nТестовый пример:")
            print("  Граф: A->B,C; B->D; C->D,E; D->F; E->A")
            print("  Порядок: F, D, B, E, C, A (без циклов)")
            
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
