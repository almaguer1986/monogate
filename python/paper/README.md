# monogate preprint — build & submission guide

## Quick build

```bash
# from python/paper/ directory — requires TeX Live 2022+ or MiKTeX
pdflatex preprint.tex
pdflatex preprint.tex   # second pass resolves cross-references
# Output: preprint.pdf  (rename to monogate_eml_extensions_v0.8.pdf for sharing)
```

### With Docker (no local TeX install needed)

```bash
docker run --rm \
  -v "$(pwd)/paper:/work" \
  -w /work \
  texlive/texlive:latest \
  bash -c "pdflatex preprint.tex && pdflatex preprint.tex"
```

---

## arXiv upload — exact steps

1. **Build a clean PDF** (see above). Zero errors, zero `Undefined reference` warnings.

2. **Create the submission archive:**
   ```bash
   mkdir -p paper/figures paper/anc
   # Copy results file as ancillary data:
   cp results/sin_n11.json paper/anc/sin_n11.json
   # Package:
   cd paper/
   tar -czf monogate_arxiv_v1.tar.gz preprint.tex anc/
   ```

3. **Go to https://arxiv.org/submit**  
   - New submission → choose **cs.SC** (Symbolic Computation) as primary  
   - Secondary: **cs.LG** (Machine Learning), **math.NA** (Numerical Analysis)  
   - Upload `monogate_arxiv_v1.tar.gz`

4. **Fill in metadata:**
   - Title: `Practical Extensions to the EML Universal Operator: Hybrid Routing, Phantom Attractors, Performance Kernels, and the N=11 Sin Barrier`
   - Authors: `Art Almaguer`
   - Abstract: copy from `arxiv_submission_notes.md` (≤ 250 words)
   - Comments: `14 pages; source code at https://github.com/almaguer1986/monogate`
   - MSC Class: `68W30` (symbolic computation), `65D15` (algorithms for functional approximation)

5. **After submission — update placeholders:**
   - Note the arXiv ID (e.g. `2604.XXXXX`)
   - Update in repository: `README.md`, `assets/n11_share_card.md`,
     `explorer/src/components/ResearchTab.jsx`,
     `explorer/src/components/LeaderboardTab.jsx`
   - See `arxiv_submission_notes.md` for the full post-submission checklist

---

## arXiv submission checklist

### LaTeX / PDF
- [ ] Zero errors in `pdflatex` output (`No error` in log)
- [ ] Zero `Undefined reference` warnings (run twice)
- [ ] Zero `Citation ... undefined` warnings
- [ ] All `\label{...}` have matching `\ref{...}` in text
  - `tab:tree_counts` — referenced in §7.1 and Conjecture
  - `tab:perf` — referenced in §8.1
  - `fig:attractor` — referenced in §5.1
  - `thm:barrier` — referenced in §7.3 and Conclusion
- [ ] `\cite{odrzywolekEML2026}` resolves correctly
- [ ] Abstract ≤ 250 words (arXiv form character limit)
- [ ] No custom `.sty` files needed (all packages are standard TeX Live)

### Figures
- [ ] Fig. 1 (`fig:attractor`): currently a `\fbox` placeholder.
  - **Before public submission:** replace with actual screenshot from explorer.
  - Generate: run `npm run dev` in `explorer/`, visit Attractor Lab tab.
  - Save as `paper/figures/attractor_phase_transition.pdf`
  - Then update `preprint.tex`:
    ```latex
    % Replace the \fbox{...} block with:
    \includegraphics[width=0.9\linewidth]{figures/attractor_phase_transition}
    ```

### Content
- [ ] Author name and email correct in `\author{}`
- [ ] Date: `\date{April 2026}` or `\date{\today}`
- [ ] Version note: add `v1` to title or comments field on arXiv (not in `.tex`)
- [ ] ORCID (optional): if registered, add to author block

### Licensing
- [ ] arXiv license: select **CC BY 4.0** (recommended for open research)

### Ancillary data
- [ ] `sin_n11.json` included in `anc/` folder of archive
- [ ] Brief note in paper pointing to data: present in §"Data and Code Availability"

---

## Packages used (all available on arXiv TeX Live 2022)

| Package | Purpose |
|---------|---------|
| `amsmath, amssymb, amsthm` | Math environments and symbols |
| `booktabs` | Professional tables |
| `hyperref` | Clickable links |
| `xcolor` | Colour support |
| `listings` | Code listings |
| `graphicx` | Figure inclusion |
| `microtype` | Typography improvements |
| `array` | Extended table columns |
| `geometry` | Page margins |

No custom packages, no local `.sty` files, no external fonts.

---

## Version history

| Version | arXiv | Date | Notes |
|---------|-------|------|-------|
| v0.1 | — | 2026-04-16 | Draft: N≤9, BEST, attractors |
| v0.2 | — | 2026-04-16 | Added N=10, MCTS section |
| v0.3 | — | 2026-04-16 | Added N=11 (281M trees), Rust, SIREN, Performance section |
| **v0.8** | **pending** | **2026-04-16** | **Final polish, arXiv-ready** |
