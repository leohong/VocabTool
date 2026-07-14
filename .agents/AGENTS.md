# Project Rules

- **Git Confirmation**: Always ask the user for explicit confirmation in the chat text before proposing or executing any git push or commit commands.

- **Versioning Rule (X.Y.Z)**:
  - Version format is `X.Y.Z` where `X` is Major version, `Y` is Minor version, and `Z` is the Git Push count.
  - The UI display should only show the first two digits `X.Y` (e.g. `v1.2` extracted dynamically from `APP_VERSION = "1.2.0"`).
  - Before executing any `git commit`/`git push`, the developer or AI agent MUST increment `Z` (the third digit) by 1 (e.g. from `1.2.0` to `1.2.1`) inside the `APP_VERSION` constant in `index.html`.
  - When major or minor features are added, manually increment `X` or `Y` and reset `Z` to `0` or `1`.

