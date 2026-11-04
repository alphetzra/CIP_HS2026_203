"""Creates requirements.txt from the imports used in the project scripts.

Run from the main folder of the repository:
    py generate_requirements.py

It reads every .py file in the scripts folder (skipping environment folders such as .venv),
collects the imported packages, ignores Python's standard library and writes the installed
version of each package into requirements.txt.
"""

import ast
import sys
from pathlib import Path
from importlib import metadata

scripts_folder = Path(__file__).parent / "scripts"
output_file = Path(__file__).parent / "requirements.txt"

#folders that contain installed packages and not our own code
skip_folders = {".venv", "venv", "env", "site-packages", "__pycache__", ".ipynb_checkpoints"}

#1. collect the top-level names of all imports (e.g. "statsmodels.formula.api" -> "statsmodels")
imported = set()
for file in scripts_folder.rglob("*.py"):
    if skip_folders & set(file.parts):
        continue
    tree = ast.parse(file.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imported.add(node.module.split(".")[0])

#2. remove the standard library (json, pathlib, ast, ...)
imported -= set(sys.stdlib_module_names)

#3. find the installed package of each import (e.g. "bs4" -> "beautifulsoup4") and its version
import_to_package = metadata.packages_distributions()
requirements, not_found = set(), []
for name in sorted(imported):
    packages = import_to_package.get(name)
    if packages:
        package = packages[0]
        requirements.add(f"{package}=={metadata.version(package)}")
    else:
        not_found.append(name)

#4. write the file
output_file.write_text("\n".join(sorted(requirements, key=str.lower)) + "\n", encoding="utf-8")

print(f"Saved {len(requirements)} packages to {output_file}")
print("\n".join(sorted(requirements, key=str.lower)))
if not_found:
    print(f"\nNot installed in this Python (check them by hand): {not_found}")
