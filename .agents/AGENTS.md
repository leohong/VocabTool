# VocabTool-App AI Agent Directives

## 1. Build Invariant
- **Source (`www/js/`)**: `utils/`, `hooks/`, `components/`, `app.js`.
- **Build Invariant**: Edits in `www/js/` MUST be followed by `npm run build` (`node scripts/build.js`) to regenerate `www/index.html` (required for Android WebView `file://` CORS policy).

## 2. Mandatory Governance
1. **Remote Git**: NEVER `git push`, push tags, or sync remotes without explicit user confirmation.
2. **UI Preservation**: Maintain 100% fidelity for Tailwind CSS classes, layouts, colors, and animations (Zero Visual Delta).
3. **SemVer**: Freeze version numbers during feature dev/fixes. Sync version increments across `app.js`, `android/app/build.gradle`, `package.json`, `README.md`, and `SPECIFICATION.md` ONLY when explicitly asked to release.
4. **Root Cause Protocol**: ALWAYS explain root cause and proposed resolution strategy before modifying code for bugs/failures.
5. **Documentation Boundary**:
   - `README.md`: End-user operational manual.
   - `SPECIFICATION.md`: Authoritative technical specification & developer manual (architecture, schemas, algorithms, CLI pipelines, testing).

## 3. Token & Context Optimization
- **Quiet Logs**: Redirect build logs (`> build.log`) or append `-q` (e.g. Gradle). Never flood context with raw logs.
- **Precise Edits**: Use targeted `replace_file_content` / `multi_replace_file_content` instead of whole-file overwrites.
- **Filtered Debug Output**: Suppress non-essential logging during test execution or directory searches.

## 4. References
- **Technical Specification & Dev Guide**: [SPECIFICATION.md](file:///d:/MyProjects/VocabTool-App/SPECIFICATION.md)
