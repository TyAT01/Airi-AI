import os
import json
import subprocess
import sys
from typing import List, Dict, Any, Set

ROOT = os.getcwd()
SEARCH_ROOTS = ['apps', 'packages', 'plugins', 'services', 'integrations', 'docs']
IGNORE_DIRS = { 'node_modules', '.git', 'dist', 'build', '.next', '.nuxt', '.turbo', 'coverage', '.cache', 'out', '.vite' }

def walk_packages(directory: str, out: List[str]):
    try:
        entries = os.scandir(directory)
    except OSError:
        return

    for entry in entries:
        if entry.name.startswith('.'):
            if entry.name != '.vitepress':
                continue

        if entry.is_dir():
            if entry.name in IGNORE_DIRS:
                continue
            walk_packages(entry.path, out)
        elif entry.is_file() and entry.name == 'package.json':
            out.append(entry.path)

def collect_package_jsons() -> List[str]:
    files = [os.path.join(ROOT, 'package.json')]
    for base in SEARCH_ROOTS:
        full = os.path.join(ROOT, base)
        if os.path.exists(full):
            walk_packages(full, files)
    return files

def main():
    pkg_files = collect_package_jsons()
    results = []
    for f in pkg_files:
        try:
            with open(f, 'r') as jf:
                data = json.load(jf)
                results.append({
                    "name": data.get("name", "unknown"),
                    "path": os.path.relpath(f, ROOT)
                })
        except:
            continue

    if '--json' in sys.argv:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            print(f"{r['name']}: {r['path']}")

if __name__ == "__main__":
    main()
