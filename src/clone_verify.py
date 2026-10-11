import os
import subprocess
import sys

import pandas as pd
from tqdm import tqdm

from config import INTERIM_DIR, REPOS_DIR

ENV = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}   # never wait for a password


def git(args, cwd=None, timeout=1800):
    return subprocess.run(
        ["git"] + args, cwd=cwd, env=ENV, capture_output=True,
        text=True, encoding="utf-8", errors="replace", timeout=timeout,
    )


commits = pd.read_csv(INTERIM_DIR / "devgpt_commits.csv")
counts = commits["repo"].value_counts()

# Optional: pass "--skip-big" to leave the largest repo for later
skip_big = "--skip-big" in sys.argv
repos = list(counts.sort_values().index)          # small repos first
if skip_big:
    repos = [r for r in repos if counts[r] < 100]

results = []
repo_info = []

for repo in tqdm(repos, desc="Repos"):
    local = REPOS_DIR / repo.replace("/", "__")
    status = "ok"

    if not (local / ".git").exists() and not (local / "HEAD").exists():
        r = git(["clone", "--filter=blob:none", "--no-checkout",
                 f"https://github.com/{repo}.git", str(local)])
        if r.returncode != 0:
            status = "clone_failed"
            err = (r.stderr or "").strip().splitlines()
            repo_info.append({"repo": repo, "status": status,
                              "total_commits": None,
                              "error": err[-1] if err else ""})
            for sha in commits.loc[commits["repo"] == repo, "sha"]:
                results.append({"repo": repo, "sha": sha, "exists": False,
                                "author_name": None, "author_email": None,
                                "note": "repo not cloneable"})
            continue

    total = git(["rev-list", "--count", "--all"], cwd=local)
    repo_info.append({"repo": repo, "status": status,
                      "total_commits": int(total.stdout.strip() or 0),
                      "error": ""})

    for sha in commits.loc[commits["repo"] == repo, "sha"]:
        chk = git(["cat-file", "-e", f"{sha}^{{commit}}"], cwd=local)
        exists = chk.returncode == 0
        name = email = None
        if exists:
            info = git(["show", "-s", "--format=%an|%ae", sha], cwd=local)
            name, _, email = info.stdout.strip().partition("|")
        results.append({"repo": repo, "sha": sha, "exists": exists,
                        "author_name": name, "author_email": email,
                        "note": "" if exists else "sha not found"})

ver = pd.DataFrame(results)
info = pd.DataFrame(repo_info)

# Merge with existing results when run in two passes
for df, name in ((ver, "devgpt_verification.csv"), (info, "devgpt_repo_status.csv")):
    path = INTERIM_DIR / name
    if path.exists():
        old = pd.read_csv(path)
        key = "sha" if "sha" in df else "repo"
        df = pd.concat([old[~old[key].isin(df[key])], df])
    df.to_csv(path, index=False)

print("\n===== VERIFICATION =====")
print("Repos attempted:   ", len(info))
print("Clone failed:      ", (info["status"] == "clone_failed").sum())
print("Commits checked:   ", len(ver))
print("SHAs found:        ", int(ver["exists"].sum()))
print("SHAs missing:      ", int((~ver["exists"]).sum()))
print("\nAuthor identities per email (top):")
print(ver.dropna(subset=["author_email"])
         .groupby("author_email")["author_name"].agg(lambda s: sorted(set(s)))
         .head(10).to_string())