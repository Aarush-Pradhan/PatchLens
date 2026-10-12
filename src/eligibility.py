import subprocess
from collections import defaultdict

import pandas as pd

from config import INTERIM_DIR, REPOS_DIR, COPILOT_PREVIEW_DATE


ALIASES = {"tisztamo@nore.ply": "tisztamo@users.noreply.github.com"}

SEP = "\x1f"  # safe separator, cannot appear in names

commits = pd.read_csv(INTERIM_DIR / "devgpt_commits.csv")
ver = pd.read_csv(INTERIM_DIR / "devgpt_verification.csv")
ver = ver[ver["exists"]].copy()
ver["dev"] = ver["author_email"].str.lower().replace(ALIASES)

linked_all = set(commits["sha"])
cutoff = pd.Timestamp(COPILOT_PREVIEW_DATE, tz="UTC")

# ---- Identity check for the biggest repo ----
junior = ver[ver["repo"] == "tisztamo/Junior"]
print("===== IDENTITIES IN tisztamo/Junior (linked commits) =====")
print(junior.groupby(["author_name", "author_email"]).size().to_string())

# ---- Ordinary commits per (repo, developer) ----
rows = []
for repo in sorted(ver["repo"].unique()):
    local = REPOS_DIR / repo.replace("/", "__")
    if not local.exists():
        continue
    out = subprocess.run(
        ["git", "log", "--all", "--no-merges",
         f"--format=%H{SEP}%ae{SEP}%an{SEP}%aI"],
        cwd=local, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    ).stdout

    stats = defaultdict(lambda: {"ordinary": 0, "pre2021": 0})
    seen = set()
    for line in out.splitlines():
        parts = line.split(SEP)
        if len(parts) != 4:
            continue
        sha, email, name, date = parts
        if sha in seen:
            continue
        seen.add(sha)
        email = ALIASES.get(email.lower(), email.lower())
        if "[bot]" in name.lower() or "bot@" in email:
            continue
        if sha in linked_all:
            continue
        stats[email]["ordinary"] += 1
        if pd.Timestamp(date).tz_convert("UTC") < cutoff:
            stats[email]["pre2021"] += 1

    for dev, g in ver[ver["repo"] == repo].groupby("dev"):
        rows.append({
            "repo": repo, "dev": dev,
            "linked_verified": len(g),
            "ordinary": stats[dev]["ordinary"],
            "ordinary_pre2021": stats[dev]["pre2021"],
        })

el = pd.DataFrame(rows)
el["eligible"] = (el["linked_verified"] >= 1) & (el["ordinary"] >= 5)
el.to_csv(INTERIM_DIR / "devgpt_eligibility.csv", index=False)


def summary(df, label):
    print(f"\n----- {label} -----")
    print("Developer-repo pairs:                  ", len(df))
    print("Distinct developers:                   ", df["dev"].nunique())
    print("Eligible for RQ4 (>=1 linked, >=5 ord):", int(df["eligible"].sum()))
    print("Eligible developers (distinct):        ", df.loc[df["eligible"], "dev"].nunique())
    print("With >=1 pre-2021 ordinary commit:     ", int((df["ordinary_pre2021"] >= 1).sum()))
    print("Linked commits in eligible pairs:      ", int(df.loc[df["eligible"], "linked_verified"].sum()))


print("\n===== ELIGIBILITY =====")
summary(el, "All repositories")
summary(el[el["repo"] != "tisztamo/Junior"], "Excluding tisztamo/Junior")

print("\nTop 10 pairs by ordinary commits:")
print(el.sort_values("ordinary", ascending=False).head(10).to_string(index=False))