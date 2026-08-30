# Publishing this repository to GitHub

This artifact is complete and ready to push, but it has **not** been published for
you — creating a GitHub repository requires your account credentials. Follow the
steps below, then replace every `<your-username>` placeholder in `README.md`,
`CITATION.cff`, and the manuscript's Data Availability section with your actual
GitHub handle.

## 1. Create the repository

**Option A — GitHub CLI** (installs from https://cli.github.com):

```bash
cd hyperbench
git init
git add .
git commit -m "HYPERBENCH: reproducibility artifact for traversable-hyperspace manuscript"
gh repo create hyperbench --public --source=. --remote=origin --push
```

**Option B — web interface:** create an empty public repository named
`hyperbench` at https://github.com/new (no README, no .gitignore — this
repository already has both), then:

```bash
cd hyperbench
git init
git add .
git commit -m "HYPERBENCH: reproducibility artifact for traversable-hyperspace manuscript"
git branch -M main
git remote add origin https://github.com/<your-username>/hyperbench.git
git push -u origin main
```

## 2. Update the placeholders

```bash
grep -rn "<your-username>" .
```

Replace each occurrence, then commit again. Do the same for `[Author Name]`,
`[Surname]`, `[Given name]`, `[Department of Computer Science, Institution]`,
and the placeholder ORCID in `CITATION.cff` and `LICENSE`.

## 3. Mint a DOI (recommended for citation)

Journals increasingly require an archived, versioned artifact rather than a bare
GitHub link, because repositories can be force-pushed, renamed, or deleted.

1. Sign in to https://zenodo.org with your GitHub account.
2. Under **GitHub** in your Zenodo settings, toggle the `hyperbench` repository on.
3. In GitHub, create a release (`v1.0.0`). Zenodo archives it and issues a DOI.
4. Add the DOI badge to `README.md` and cite the DOI — not the GitHub URL — in
   the manuscript's Data Availability statement.

## 4. Enable continuous verification (optional)

`.github/workflows/tests.yml` is included. On push, GitHub Actions installs the
pinned dependencies and runs the 15-assertion suite, so any change that breaks a
published number fails visibly.

## 5. Before submission

- [ ] Placeholders replaced everywhere (`grep -rn "<your-username>\|\[Author Name\]" .`)
- [ ] `python tests/test_paper_claims.py` passes on a clean clone
- [ ] `results/results_summary.json` regenerated and committed
- [ ] DOI minted and inserted into the manuscript
- [ ] Manuscript's Data Availability section points at the DOI
