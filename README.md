@"
# PatchLens: AI-assisted commits vs developers' own commits

Run order (from the project root, with the virtual environment active):
1. python src/extract_sharings.py   (combine DevGPT snapshots, count commits)
2. python src/explore.py            (concentration and code-block checks)
3. python src/clone_verify.py       (clone repos, verify SHAs)

Data: DevGPT from https://zenodo.org/records/8303722 (not included here).
Place the snapshots in data/raw/DevGPT/.
"@ | Out-File -Encoding utf8 README.md