import json
import pandas as pd
from config import INTERIM_DIR

commits = pd.read_csv(INTERIM_DIR / "devgpt_commits.csv")

print("===== COMMITS PER REPO (top 10) =====")
print(commits["repo"].value_counts().head(10).to_string())

print("\n===== COMMITS PER AUTHOR (top 10) =====")
print(commits["author"].value_counts().head(10).to_string())

top_repo_share = commits["repo"].value_counts().iloc[0] / len(commits)
top_author_share = commits["author"].value_counts().iloc[0] / len(commits)
print(f"\nTop repo share:   {top_repo_share:.1%}")
print(f"Top author share: {top_author_share:.1%}")

print("\nRepos with >=5 linked commits:  ", (commits["repo"].value_counts() >= 5).sum())
print("Authors with >=5 linked commits:", (commits["author"].value_counts() >= 5).sum())

# ---- Code blocks in the conversations ----
n_convs = n_with_code = n_blocks = 0
block_langs = {}
with open(INTERIM_DIR / "devgpt_sharings.jsonl", encoding="utf-8") as f:
    for line in f:
        row = json.loads(line)
        has_code = False
        for cv in row["conversations"]:
            n_convs += 1
            for block in cv.get("ListOfCode") or []:
                n_blocks += 1
                has_code = True
                lang = block.get("Type") if isinstance(block, dict) else None
                block_langs[lang] = block_langs.get(lang, 0) + 1
        n_with_code += has_code

print("\n===== CODE BLOCKS =====")
print("Sharings with at least one code block:", n_with_code)
print("Total code blocks:", n_blocks)
print("Block types:", dict(sorted(block_langs.items(), key=lambda x: -x[1])[:10]))

# Example block structure
with open(INTERIM_DIR / "devgpt_sharings.jsonl", encoding="utf-8") as f:
    for line in f:
        row = json.loads(line)
        for cv in row["conversations"]:
            if cv.get("ListOfCode"):
                print("\nExample ListOfCode item:", str(cv["ListOfCode"][0])[:300])
                raise SystemExit