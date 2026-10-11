import importlib

packages = [
    "pydriller", "git", "tree_sitter", "tree_sitter_python",
    "tree_sitter_javascript", "tree_sitter_java", "lizard",
    "pandas", "numpy", "scipy", "sklearn", "shap",
    "matplotlib", "seaborn", "tqdm",
]

for name in packages:
    try:
        importlib.import_module(name)
        print(f"OK       {name}")
    except Exception as e:
        print(f"FAILED   {name} -> {e}")

# Optional (only if you installed them)
for name in ["transformers", "torch"]:
    try:
        importlib.import_module(name)
        print(f"OK       {name}")
    except Exception:
        print(f"SKIPPED  {name} (not installed, needed later for CodeBERT)")