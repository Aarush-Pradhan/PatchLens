from pathlib import Path

# ---- Reproducibility ----
SEED = 42

# ---- Project paths ----
ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = ROOT / "data" / "raw"
INTERIM_DIR = ROOT / "data" / "interim"
PROCESSED_DIR = ROOT / "data" / "processed"
REPOS_DIR = ROOT / "repos"
RESULTS_DIR = ROOT / "results"

# ---- Dataset locations ----
DEVGPT_DIR = RAW_DIR / "DevGPT"
AIDEV_DIR = RAW_DIR / "AI_Teammates_in_SE3"

# ---- Study settings ----
CHATGPT_RELEASE_DATE = "2022-11-30"
COPILOT_PREVIEW_DATE = "2021-06-01"   # pre-this = certified negatives
N_BOOTSTRAP = 1000                    # bootstrap resamples for CIs
N_FOLDS = 5                           # GroupKFold splits

# ---- Create folders if missing ----
for folder in (RAW_DIR, INTERIM_DIR, PROCESSED_DIR, REPOS_DIR, RESULTS_DIR):
    folder.mkdir(parents=True, exist_ok=True)