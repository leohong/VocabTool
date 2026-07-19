# Project Rules

- **Git Confirmation**: Always ask the user for explicit confirmation in the chat text before proposing or executing any git push commands. Git commit and add commands can be executed or proposed automatically without blocking.

- **Versioning Rule (X.Y.Z)**:
  - Version format is `X.Y.Z` where `X` is Major version, `Y` is Minor version, and `Z` is the Git Push count.
  - The UI display should only show the first two digits `X.Y` (e.g. `v1.2` extracted dynamically from `APP_VERSION = "1.2.0"`).
  - Before executing any `git commit`/`git push`, the developer or AI agent MUST increment `Z` (the third digit) by 1 (e.g. from `1.2.0` to `1.2.1`) inside the `APP_VERSION` constant in `index.html`.
  - When major or minor features are added, manually increment `X` or `Y` and reset `Z` to `0` or `1`.

- **Change Approval**: Always present the implementation plan/proposal and get the user's explicit consent in the chat BEFORE making any code modifications. If the user only asks for explanations or troubleshooting reasons, do NOT modify the codebase.

- **主程式變更測試規則 (Main Program Test Rule)**: 若主程式 `index.html` 沒有任何程式碼變更（例如僅修改規格書或文件檔案），則不需執行自動化測試。

- **Token 節省開發與測試準則 (Token Saving Rule)**:
  - **精準局部讀取**：禁止一次性 `view_file` 讀取整份 `index.html`。必須先使用 `grep_search` 定位關鍵程式碼所在行數，再指定 `StartLine` 與 `EndLine` 僅讀取所需片段。
  - **精準代碼修改**：修改程式碼時，使用 `replace_file_content` 僅針對特定區間做精準替換，避免覆寫大範圍無關代碼。
  - **禁止在控制台輸出 DOM**：在測試中（無論新寫或修改測試），**絕對禁止**將 `driver.page_source` 或整個 DOM 結構 `print` 輸出到 console / stdout / stderr。這會造成巨大的終端機輸出，嚴重浪費 Token。如有除錯需要，必須將 page source 寫入本地的 `test/failure_source.html` 或其他本地檔案中。
  - **單一功能測試優先**：在確認變更時，優先執行針對該模組的特定測試腳本（如 `python test/test_audio_player.py`），而非每次都跑完整的 `test_all_features.py`。

