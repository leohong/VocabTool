# 🤖 VocabTool-App AI Agent Workspace Directives

> **Scope**: Target workspace (`VocabTool-App`). This document contains mandatory system constraints, architecture blueprints, build workflows, and governance rules for AI Agents.

---

## 1. System Architecture & Component Mapping

* **Source Directory (`www/js/`)**:
  * `utils/`: Pure utilities, API clients, algorithms, I/O, audio (`textUtils.js`, `dictionaryApi.js`, `exportImportUtils.js`, `audioUtils.js`, `sessionUtils.js`).
  * `hooks/`: React state management and business logic (`useVocabState.js`).
  * `components/`: UI components and session modules (`Header.js`, `Dashboard.js`, `Sessions.js`, `AudioPlayer.js`, `Modals.js`, `sessions/*.js`).
  * `app.js`: Application lifecycle and router entry point.
* **Compiled Production Target (`www/index.html`)**:
  * Generated via `scripts/build.js`.
  * **Constraint**: Pre-bundled JSX to circumvent CORS restrictions under Android WebView (`file://` origin).

---

## 2. Build Pipeline & Environment Specifications

* **Environment Setup (PowerShell)**:
  ```powershell
  $env:JAVA_HOME = if (Test-Path "D:\Android\Android Studio\jbr") { "D:\Android\Android Studio\jbr" } else { "$env:ProgramFiles\Android\Android Studio\jbr" }
  if ($env:ANDROID_HOME) { $env:Path += ";$env:ANDROID_HOME\platform-tools" } else { $env:Path += ";$env:LOCALAPPDATA\Android\Sdk\platform-tools" }
  ```

* **CLI Execution Flow**:
  ```powershell
  # 1. Bundle JS modules into www/index.html
  cmd /c npm run build

  # 2. Sync web assets to Android platform
  cmd /c npx cap sync android

  # 3. Compile Debug APK with suppressed verbose logs
  cd android; .\gradlew.bat assembleDebug -q

  # 4. Deploy and launch on target device
  adb install -r .\app\build\outputs\apk\debug\app-debug.apk
  adb shell am start -n com.vocabtool.app/com.vocabtool.app.MainActivity
  ```

---

## 3. Mandatory Governance & Development Mandates

1. **🔒 Remote Git Operations (Local-Only Mandate)**:
   * **STRICT RULE**: ALL code development, compilation, and tagging MUST occur locally.
   * **NEVER** execute `git push`, push tags, or sync changes to remote repositories without explicit user confirmation.
2. **🎨 UI/Visual Preservation (Zero Visual Delta)**:
   * Maintain 100% fidelity for Tailwind CSS classes, color schemes, animations, and component layouts during refactoring.
3. **🏷️ SemVer & Release Lifecycle**:
   * **Development Phase**: Keep version numbers frozen during feature additions, refactoring, or bug fixes.
   * **Release Phase**: Synchronize version increments across `app.js`, `android/app/build.gradle`, and `package.json` ONLY when explicitly instructed to issue a release or execute Git push. Ensure `README.md` and `SPECIFICATION.md` metadata match the release tag.
4. **💡 Root Cause Communication Protocol**:
   * Before modifying code or configurations in response to bugs, warnings, or failures, ALWAYS explicitly explain the underlying Root Cause and proposed resolution strategy to the user.
5. **📖 Documentation Boundary**:
   * `README.md`: End-user operational manual (features, UI navigation, shortcuts, TTS troubleshooting).
   * `SPECIFICATION.md`: Authoritative technical specification (architecture, data schemas, normalization specs, algorithms, defense mechanisms).
6. **🌐 Data Integrity & Schema Preservation**:
   * **Metrics Retention**: Data pruning/deduplication MUST preserve all SRS tracking fields (`archivedDate`, `step`, `interval`, `immune`, `totalFails`, `mistakesCount`, `correctCount`).
   * **Orphan Purge (Restoration Safety)**: Automatically drop orphaned mistake entries whose corresponding vocabulary words no longer exist in the active dictionary during backup rehydration.
7. **🔘 4選1 測驗 (MCQ) UI 與發音控制規範**:
   * **標籤與快速鍵**: 選項標籤與鍵盤快捷鍵嚴格採用 `1, 2, 3, 4` (含 Numpad)，不使用 A/B/C/D；4選1 模式下遮蔽左右方向鍵跳卡。
   * **發音開關適應**: 卡片載入呼叫 `speak(currentWord.en, false)` 遵循全域 `speechEnabled` 開關；點選選項不重複朗讀。
   * **物件級狀態重置**: `useEffect` 換卡重置依賴項須為 `[currentWord, ...]` 物件參考，確保連續相同字串時按鈕狀態 100% 歸零。

---

## 4. Testing & Local Server Protocols

* **LocalStorage DB Mocking**: 測試腳本寫入 `vocab_currentDB` 時，必須同步寫入 `vocab_dbList: JSON.stringify(['testDB'])`，防止 state hook 降級回載入預設字庫。
* **Dynamic Port Allocation**: ALWAYS bind to port `0` (OS auto-assignment) on host `127.0.0.1`. NEVER hardcode fixed ports (e.g., `8001`) to avoid IPv4/v6 resolution timeouts or port collision.
* **Resource Reclamation**: Explicitly execute `httpd.shutdown()` and `httpd.server_close()` in `finally` blocks to prevent zombie listener processes.
* **Non-blocking Server Execution**: On Windows, launch background dev servers using `start` (e.g., `start npm run serve`) to avoid blocking shell execution.
* **Dual-Repo Sync**: 同步 `VocabTool` Web 庫時，需將 `www/index.html` 覆蓋至 `VocabTool/index.html`；推送遇遠端更新時統一執行 `git pull --rebase origin main`。

---

## 5. Capacitor Native Platform Integrations

* **WebView File Export**: WebViews restrict direct Blob URL downloads. File export features MUST use `@capacitor/filesystem` (`CACHE` directory) paired with `@capacitor/share` (native system picker).
* **Graceful Cancellation**: Intercept native share cancellation (`Share canceled`) gracefully without triggering clipboard fallback warnings.
* **Kotlin Dependency Resolution**: Exclude legacy `kotlin-stdlib-jdk7/8` transitive dependencies in `android/build.gradle` (`configurations.all`) to prevent class duplication errors against modern `kotlin-stdlib` (1.8.22+).

---

## 6. Token & Context Optimization Guidelines

1. **Quiet Build Logs**: Always append `-q` to Gradle builds or redirect stdout (`> build.log`). Never flood the context with raw build logs.
2. **Targeted File Modifications**: Use precise line replacement tools (`replace_file_content` / `multi_replace_file_content`) over whole-file overwrites.
3. **Filtered Debug Output**: Suppress non-essential logging during test execution or directory searches.

---

## 7. Knowledge Base References

* **Technical Manual**: [DEVELOPMENT_GUIDE.md](file:///d:/MyProjects/VocabTool-App/.agents/DEVELOPMENT_GUIDE.md)
* **Token Saver Guide**: [AI_AGENT_TOKEN_SAVER.md](file:///d:/MyProjects/VocabTool-App/.agents/AI_AGENT_TOKEN_SAVER.md)
