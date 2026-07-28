# Contributing to NetGuard

Thanks for considering a contribution! This is primarily a portfolio project, but
it's built and tested like a real one, and contributions are welcome.

## Getting Started

1. Fork the repository and clone your fork.
2. Follow the setup steps in `README.md` / `docs/SETUP.md` to get the backend and
   frontend running locally.
3. Create a branch for your change: `git checkout -b fix/short-description`.

## Development Workflow

**Backend**
```bash
cd backend
source venv/bin/activate
pip install -r requirements-dev.txt  # includes pytest, httpx, pyflakes
pytest              # run the test suite
python3 -m pyflakes app/ tests/  # static check for unused imports/dead code
```

**Frontend**
```bash
cd frontend
npm install
npm run lint         # ESLint
npm test             # Vitest component tests
npm run build         # type-check + production build
```

Please run tests and lint locally before opening a pull request - CI (see
`.github/workflows/ci.yml`) runs the same checks and will block merges on failure.

## Code Style

- **Backend**: standard PEP 8-ish formatting, type hints where they aid clarity,
  docstrings on modules and non-trivial functions. Prefer explicit over clever.
- **Frontend**: TypeScript strict mode is on - avoid `any` where a real type is
  easy to express. Components are functional with hooks; keep presentational
  components free of data-fetching logic where practical.
- Comments should explain **why**, not **what** - the code itself should make the
  "what" obvious.

## Commit Messages

Keep them descriptive and scoped, e.g.:
```
fix(scanner): handle empty ping-sweep result without dividing by zero
feat(topology): group hosts by VLAN in the graph view
docs(readme): correct macOS setup steps for Apple Silicon
```

## Pull Requests

- Keep PRs focused on one change where possible - easier to review, easier to revert.
- Describe **what** changed and **why**, not just a restatement of the diff.
- Link any related issue.
- Make sure `pytest`, `npm run lint`, `npm test`, and `npm run build` all pass.

## Reporting Bugs

Open an issue with:
- Steps to reproduce
- Expected vs. actual behavior
- Backend/frontend logs if relevant (scrub any real IPs/hostnames from your own
  network if you'd rather not share them)

## Security Issues

Please do **not** open a public issue for security vulnerabilities - see
`SECURITY.md` for how to report those privately.
