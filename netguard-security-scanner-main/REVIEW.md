# Senior Engineering Review — NetGuard

**Reviewer perspective:** Senior Software Engineer audit prior to public GitHub release / resume
listing.
**Scope:** full repository — backend, frontend, tests, CI, Docker, documentation, security posture.
**Method:** every claim below was checked by running a tool (`pytest`, `pyflakes`, `eslint`,
`vitest`, `tsc`, `npm run build`, fresh venv installs, manual regex testing), not by inspection
alone. This review builds on an existing, well-executed prior pass (see `CHANGELOG.md [1.1.0]`) —
it re-verifies that work and closes the gaps that pass left behind.

---

## Overall Score: 8.5/10

This was already a genuinely strong portfolio project going into this pass: real Nmap-based
scanning, SNMP polling, CVE correlation, structured logging, typed API responses, and a real test
suite — not a CRUD app in a networking costume. This pass found and fixed one real security gap
(nmap argument injection via the scan target field), removed dead dependencies, corrected an
inaccurate performance claim, and tightened Docker/CI hygiene. The remaining half-point is held
back by the same honestly-documented, intentional scope limits as before (minimal auth, no rate
limiting, SQLite over a server-grade DB) — these are appropriate for what this project is, not
oversights.

| Dimension | Score | Notes |
|---|---|---|
| Repository quality | 9/10 | Clean structure, all standard GitHub meta files present, root `.gitignore` added this pass |
| Code quality | 8/10 | `pyflakes`/`eslint` clean; dead dependencies removed; `scanner.py:run_scan` remains a long function (unchanged — refactoring risked altering behavior, out of scope for this pass) |
| Documentation | 9/10 | README verified accurate against the running code (test counts, API surface, tech stack); one inaccurate performance claim found and corrected |
| Architecture | 8/10 | Clear separation of concerns; no ORM is a reasonable choice at this scale |
| Security | 8/10 | Real fix applied this pass (target-field argument injection); everything else was already honestly scoped in `SECURITY.md` |
| Maintainability | 8/10 | Structured logging, typed responses, and 45 backend + 9 frontend tests make this safe to extend |
| Scalability | 6/10 | SQLite + in-thread scanning is fine for a single-user demo; would need a job queue + server DB for concurrent multi-user use (unchanged, correctly out of scope) |
| Performance | 8/10 | Initial JS chunk verified at 254.96 kB minified / 83.50 kB gzipped via a fresh `npm run build` — the prior pass's changelog entry mislabeled this as "255KB gzip," now corrected |
| Test coverage | 7/10 | 45 backend tests (was 43 — 2 new regression tests added this pass) + 9 frontend tests, all passing; `reports.py` and `snmp_client.py` internals still only covered indirectly via API tests |

---

## What Was Actually Found and Fixed This Pass

- **Real security fix — nmap argument injection.** `python-nmap` forwards the `target` field to the
  `nmap` CLI via `shlex.split()`. Because the field only checked for blank/length, a value like
  `"127.0.0.1 --script vuln"` would be split into multiple nmap arguments, letting a caller smuggle
  in extra flags the operator never asked for. Added a strict allow-list validator in
  `ScanRequest.target` (rejects whitespace and a leading `-`) and two regression tests. Verified all
  documented target formats (single IP, range, CIDR, hostname, IPv6) still work.
- **Dead dependencies removed.** `scapy` and `pandas` were listed in `requirements.txt` but never
  imported anywhere in `app/` or `tests/` — confirmed via `grep`, removed, then reinstalled in a
  clean virtualenv and reran the full suite to confirm nothing broke.
- **Dead Docker package removed.** The backend `Dockerfile` installed `libcap2-bin` with a comment
  claiming it granted nmap capabilities, but no `setcap` call existed anywhere in the file — it was
  leftover intent from an approach that was never actually implemented (the container uses
  compose-level `NET_ADMIN`/`NET_RAW` instead). Removed the unused package and corrected the comment
  to describe what the container actually does.
- **An inaccurate performance claim corrected.** The changelog and (implicitly) the README claimed
  the code-split bundle was "~255KB gzip." Running `npm run build` fresh shows the real number is
  254.96 kB minified / 83.50 kB gzipped for the initial chunk — a meaningful difference. Corrected
  in `CHANGELOG.md`.
- **Docker build reproducibility.** Frontend `Dockerfile` now uses `npm ci` instead of `npm install`,
  so Docker builds always match `package-lock.json` exactly instead of potentially drifting.
- **Stale documentation reference removed.** `docs/SETUP.md` had a troubleshooting row for a
  `scapy` install failure that no longer applies now that the dependency is gone.
- **Root-level `.gitignore` added.** OS/editor artifacts (`.DS_Store`, `.vscode/`, `.idea/`) weren't
  covered outside the `backend/` and `frontend/` subfolders.
- **README accuracy pass.** Removed `Pandas` from the backend tech-stack list (matching the
  dependency removal) and updated the stated backend test count from 43 to 45.

## What Was Re-Verified From the Prior Pass (Still Holds Up)

- `pyflakes app/ tests/` — clean.
- `eslint .` — 0 errors (2 pre-existing, harmless `react-refresh` warnings about context files
  exporting both a component and a hook, which is a normal, common pattern).
- `pytest` — 45/45 passing (43 prior + 2 new).
- `npm test` — 9/9 passing.
- `npm run build` — TypeScript compiles clean, production build succeeds.
- Every REST/WebSocket endpoint documented in the README's API Overview table exists in
  `backend/app/main.py` with a matching path and method.
- `SECURITY.md`'s claims (parameterized SQL, hashed passwords, HMAC-signed tokens, env-driven
  secrets with a startup warning on the insecure default) all check out against the actual code.

## What Would Impress Recruiters

1. **The project topic itself** — Nmap-based scanning, OS fingerprinting, SNMP polling, and CVE
   correlation is a genuinely different portfolio piece from another CRUD clone.
2. **A documented history of finding and fixing a real security bug in your own code** — the
   argument-injection fix in this pass, plus the CVE false-positive fixes from an earlier pass, are
   both strong, specific interview stories backed by regression tests, not just claims.
3. **Verification discipline** — this README's numbers (test counts, bundle size) are checked
   against actual tool output rather than asserted, and `SECURITY.md` is honest about limitations
   instead of glossing over them.

## Interview Questions This Project Could Generate

- "You validate the scan target with a regex allow-list — walk me through why, and what attack it
  closes off. What's still not covered by that fix?" (a good answer: it stops flag/argument
  injection into the single `nmap` process; it does not restrict *which* real hosts can be scanned,
  which is the actual intended feature and not a vulnerability by itself.)
- "Why SQLite instead of Postgres, and what would push you to switch?"
- "Walk me through what happens end-to-end when a user starts a scan." (tests this: request →
  Pydantic validation → background thread → nmap → risk engine → DB → WebSocket push)
- "What's actually stopping this from being production-ready today?" (rate limiting, a real IdP,
  a job queue, and a server-grade DB — all named explicitly in `SECURITY.md`.)

## Remaining Issues (Honest List)

None of these were touched in this pass — they're genuine scope decisions or would require a
product/architecture conversation, not code-review-level fixes:

- **No rate limiting** on `/api/auth/login`.
- **No job queue** — scans run in a plain Python thread; fine for one user, would need Celery/RQ
  for concurrent multi-user load.
- **SQLite, not a server-grade DB** — appropriate at this scale.
- **SNMPv2c only** — SNMPv3 would be needed for a real enterprise deployment.
- **Static VLAN assignment** — real VLAN membership would need switch-side SNMP queries
  (Q-BRIDGE-MIB).
- **Test coverage gaps**: `reports.py` and `snmp_client.py`'s async internals are exercised only
  indirectly via API tests.
- **No dependency vulnerability scanning in CI** (`pip-audit`/`npm audit` not yet wired in).
- **`scanner.py:run_scan` is a long function.** Noted, not refactored — restructuring a working,
  tested background-thread scan pipeline carries real regression risk for a cosmetic win, and was
  out of scope for "don't change architecture."

## Resume Readiness: Ready

This is a strong resume line item as-is: "Full-stack network security scanner — FastAPI + React,
real Nmap/SNMP integration, rule-based risk scoring, CVE correlation, 54 passing tests, CI/CD."
The project topic, test discipline, and documentation honesty will hold up to follow-up questions
in an interview, which is the real bar for "resume ready" — not just "the demo doesn't crash."

## GitHub Readiness: Ready

All standard community-health files exist and are substantive (not boilerplate): `LICENSE`,
`CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CHANGELOG.md`, a working CI workflow, and
a root `.gitignore`. The only manual step left before pushing is capturing the actual screenshots
and demo GIF named in the README's Screenshots section (they're intentionally not pre-committed,
since they'd depend on the pusher's own scan results and OS theme) and updating the CI badge URL
in `README.md` if this is pushed under a different GitHub username than `ayushkumar9122006`.

## Top 10 Improvements Made (This Pass)

1. Closed an nmap argument-injection gap in the scan `target` field, with regression tests.
2. Removed two fully unused dependencies (`scapy`, `pandas`) after confirming via grep + a clean
   reinstall + full test rerun that nothing depended on them.
3. Removed an unused `libcap2-bin` package from the backend Dockerfile and fixed a misleading
   comment describing capabilities the container never actually granted.
4. Switched the frontend Dockerfile from `npm install` to `npm ci` for reproducible builds.
5. Corrected an inaccurate bundle-size claim in `CHANGELOG.md` (255KB gzip → 255KB minified /
   84KB gzipped, verified via a fresh build).
6. Removed a stale `scapy`-related troubleshooting entry from `docs/SETUP.md`.
7. Added a root-level `.gitignore` for OS/editor artifacts not covered by the subfolder ones.
8. Corrected the README's tech-stack list and backend test count to match the current, verified
   state of the code.
9. Added two regression tests documenting the security fix, bringing the backend suite to 45
   tests, all independently re-run and confirmed passing in a fresh virtualenv.
10. Re-verified every existing claim in `README.md` and `SECURITY.md` against actual tool output
    (`pytest`, `pyflakes`, `eslint`, `npm run build`) rather than trusting the prior pass's
    documentation at face value.

---

*This review reflects the state of the repository as of this pass. Re-run `pytest`,
`python3 -m pyflakes app/ tests/`, `npm run lint`, `npm test`, and `npm run build` to reproduce the
verified state described above.*
