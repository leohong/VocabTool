# 🤖 VocabTool-App AI Agent Workspace Directives

> **Scope**: Target workspace (`VocabTool-App`). Mandatory system constraints, build invariants, and governance rules for AI Agents.

---

## 1. System Architecture & Build Invariant

* **Source Directory (`www/js/`)**:
  * `utils/`: Pure utilities, API clients, I/O, audio (`textUtils.js`, `dictionaryApi.js`, `exportImportUtils.js`, `audioUtils.js`, `sessionUtils.js`, `persistentStorage.js`).
  * `hooks/`: React state management and business logic (`useVocabState.js`).
  * `components/`: UI components and session modules (`Header.js`, `Dashboard.js`, `Sessions.js`, `AudioPlayer.js`, `Modals.js`, `sessions/*.js`).
  * `app.js`: Application lifecycle and router entry point.
* **Production Build Invariant (`www/index.html`)**:
  * Pre-bundled via `npm run build` (`scripts/build.js`).
  * **Constraint**: Pre-bundled JSX is required to circumvent CORS restrictions under Android WebView (`file://` origin). Always run `npm run build` after editing `www/js/`.

---

## 2. Mandatory Governance & Development Mandates

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
   * `README.md`: End-user operational manual.
   * `SPECIFICATION.md`: Authoritative technical specification (architecture, data schemas, normalization specs, algorithms, 4-choice quiz specs).
   * `DEVELOPMENT_GUIDE.md`: Developer manual, CLI build pipelines, PowerShell setup, testing & server protocols.

---

## 3. Token & Context Optimization Guidelines

1. **Quiet Build Logs**: Always append `-q` to Gradle builds or redirect stdout (`> build.log`). Never flood the context with raw build logs.
2. **Targeted File Modifications**: Use precise line replacement tools (`replace_file_content` / `multi_replace_file_content`) over whole-file overwrites.
3. **Filtered Debug Output**: Suppress non-essential logging during test execution or directory searches.

---

## 4. Knowledge Base References

* **Technical Manual**: [DEVELOPMENT_GUIDE.md](file:///d:/MyProjects/VocabTool-App/.agents/DEVELOPMENT_GUIDE.md)
* **Technical Specification**: [SPECIFICATION.md](file:///d:/MyProjects/VocabTool-App/SPECIFICATION.md)
* **Token Saver Guide**: [AI_AGENT_TOKEN_SAVER.md](file:///d:/MyProjects/VocabTool-App/.agents/AI_AGENT_TOKEN_SAVER.md)
