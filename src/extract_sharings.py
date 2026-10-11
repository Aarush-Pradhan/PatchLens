import json
from collections import Counter

import pandas as pd

from config import DEVGPT_DIR, INTERIM_DIR

snapshots = sorted(DEVGPT_DIR.glob("snapshot_*/*commit_sharings.json"))
print(f"Found {len(snapshots)} snapshot files\n")

commit_rows = {}    # key: Sha -> later snapshots overwrite earlier ones
sharing_rows = {}   # key: (Sha, sharing URL)
conv_keys = Counter()
mention_props = Counter()
raw_total = 0

for path in snapshots:
    snap = path.parent.name.replace("snapshot_", "")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    sources = data["Sources"]
    raw_total += len(sources)
    print(f"{snap}: {len(sources)} commit records")

    for c in sources:
        sha = c.get("Sha")
        if not sha:
            continue
        sharings = c.get("ChatgptSharing") or []
        commit_rows[sha] = {
            "sha": sha,
            "repo": c.get("RepoName"),
            "author": c.get("Author"),
            "language": c.get("RepoLanguage"),
            "commit_at": c.get("CommitAt"),
            "author_at": c.get("AuthorAt"),
            "message": c.get("Message"),
            "url": c.get("URL"),
            "snapshot": snap,
            "n_sharings": len(sharings),
            "n_ok_sharings": sum(1 for s in sharings if s.get("Status") == 200),
        }
        for s in sharings:
            convs = s.get("Conversations") or []
            for cv in convs:
                conv_keys.update(cv.keys())
            mention = s.get("Mention") or {}
            mention_props[mention.get("MentionedProperty")] += 1
            sharing_rows[(sha, s.get("URL"))] = {
                "sha": sha,
                "repo": c.get("RepoName"),
                "author": c.get("Author"),
                "sharing_url": s.get("URL"),
                "status": s.get("Status"),
                "mentioned_in": mention.get("MentionedProperty"),
                "date_of_conversation": s.get("DateOfConversation"),
                "title": s.get("Title"),
                "n_prompts": s.get("NumberOfPrompts"),
                "model": s.get("Model"),
                "conversations": convs,
            }

commits = pd.DataFrame(commit_rows.values())
commits["commit_at"] = pd.to_datetime(commits["commit_at"], utc=True, errors="coerce")

# ---- Save ----
commits.to_csv(INTERIM_DIR / "devgpt_commits.csv", index=False)
with open(INTERIM_DIR / "devgpt_sharings.jsonl", "w", encoding="utf-8") as f:
    for row in sharing_rows.values():
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

# ---- Counts ----
ok = commits[commits["n_ok_sharings"] > 0]
print("\n===== COUNTS =====")
print("Raw commit records (all snapshots):", raw_total)
print("Unique commits (by SHA):           ", len(commits))
print("Unique sharings:                   ", len(sharing_rows))
print("Commits with >=1 working sharing:  ", len(ok))
print("Unique repositories:               ", commits["repo"].nunique())
print("Unique authors:                    ", commits["author"].nunique())
print("Commit date range:                 ", commits["commit_at"].min(), "->", commits["commit_at"].max())
print("\nTop languages:\n", commits["language"].value_counts().head(10).to_string())
print("\nWhere the ChatGPT link was mentioned:", dict(mention_props))
print("\nFields inside each Conversation:", dict(conv_keys))