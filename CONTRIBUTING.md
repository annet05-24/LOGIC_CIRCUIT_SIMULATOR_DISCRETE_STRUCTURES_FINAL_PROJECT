# Contributing

## Branches

- `main` always works. Do not commit to it directly.
- Each member works on their own branch, for example:
  `member1-parser`, `member2-circuit`, `member3-ui`
- For a specific piece of work, branch from yours, e.g. `member3-truth-table-panel`.

```bash
git checkout -b member3-ui          # create and switch to your branch
git add .
git commit -m "Add truth table panel"
git push -u origin member3-ui
```

Then open a **Pull Request** on GitHub into `main` and ask a teammate to review it.

## Staying up to date

```bash
git checkout main
git pull
git checkout member3-ui
git merge main
```

## Rules

1. **Stay in your own folder.** Parsing = Member 1, circuit = Member 2, ui = Member 3.
   If you need a change in someone else's folder, ask them.
2. **Never change `docs/CONTRACTS.md` alone.** All three members must agree, because
   changing a data format breaks the other parts.
3. **Run the tests before opening a pull request:**
   `python -m unittest discover -s tests -v`
4. **Small, clear commits.** "Add NOT gate drawing" is good; "stuff" is not.
5. **Don't commit** `__pycache__`, virtual environments or editor settings
   (the `.gitignore` already covers these).

## Code style

- Follow PEP 8 (4-space indentation, `snake_case` names).
- Give every function a one-line docstring saying what it does.
- Keep functions short and focused.
