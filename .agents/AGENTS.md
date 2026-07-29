# 🤖 VocabTool-App AI Agent Workspace Instructions & Knowledge

本文件記錄 `VocabTool-App` 專案的核心開發規範、架構決策與運作流程。**在每次開啟新 Session / 對話時，AI Agent 均必須自動確認、讀取並嚴格遵守本規範與 `.agents/` 資料夾內的所有指引項目**。

---

## 1. 專案架構規範 (Clean Modular Architecture)

*   **開發源碼目錄 (`www/js/`)**：
    *   `utils/`：純演算法、API 工具、備份匯出與發音（`textUtils.js`, `dictionaryApi.js`, `exportImportUtils.js`, `audioUtils.js`, `sessionUtils.js`）。
    *   `hooks/`：React 業務邏輯與狀態（`useVocabState.js`）。
    *   `components/`：1:1 原裝 UI 視覺元件與關卡模組 (`Header.js`, `Dashboard.js`, `Sessions.js`, `AudioPlayer.js`, `Modals.js`, `sessions/ScanningSession.js`, `sessions/SpellingSession.js`, `sessions/SummarySession.js`)。
    *   `app.js`：核心生命週期與路由進入點。
*   **發布與編譯檔 (`www/index.html`)**：
    *   由建置腳本 `scripts/build.js` 自動生成。
    *   **原因**：Android WebView (`file://`) 嚴格禁止 AJAX 跨檔讀取外部 JSX。預編譯打包可確保離線免 CORS 錯誤。

---

## 2. 開發與打包指令與環境變數 (Commands & Environment)

*   **環境變數設定 (PowerShell 範例)**：
    ```powershell
    # 設定 Java 21 JDK 路徑 (使用 Android Studio 內建 JBR 亦可)
    $env:JAVA_HOME = if (Test-Path "D:\Android\Android Studio\jbr") { "D:\Android\Android Studio\jbr" } else { "$env:ProgramFiles\Android\Android Studio\jbr" }
    
    # 將 Android SDK Platform-Tools (ADB) 加入 PATH
    if ($env:ANDROID_HOME) { $env:Path += ";$env:ANDROID_HOME\platform-tools" } else { $env:Path += ";$env:LOCALAPPDATA\Android\Sdk\platform-tools" }
    ```

*   **開發指令**：
    ```powershell
    # 1. 預編譯打包 JavaScript 模組至 www/index.html
    cmd /c npm run build
    
    # 2. 同步 web 資源至 Android 原生工程
    cmd /c npx cap sync android
    
    # 3. 編譯 Debug APK (-q 限流日誌)
    cd android
    .\gradlew.bat assembleDebug -q
    
    # 4. 安裝並重啟 App 至連線裝置
    adb install -r .\app\build\outputs\apk\debug\app-debug.apk
    adb shell am start -n com.vocabtool.app/com.vocabtool.app.MainActivity
    ```

---

## 3. 重要開發鐵律 (Strict Guidelines)

1. **🔒 Git Server 上傳限制**：所有程式碼開發、模組編譯與版本 tag 動作一律先在 Local 本機端完成。未經使用者明確口頭同意，絕不自動執行 `git push`、推送 tag 或任何將變更上傳至 Git Server 的動作！
2. **🎨 UI 0 變化原則**：進行重構時，務必確保原本的 Tailwind CSS 樣式、動畫、按鈕顏色與排版 100% 零偏離。
3. **🏷️ 語意化版本控制與發布進版時機 (SemVer & Release Workflow)**：
   * **本地開發測試期**：進行功能開發、重構或 Bug 修復時，**版本號保持不動**，專注於程式碼修改與測試，切勿在本地微調時隨意遞增版號。
   * **正式發布 / Git Push 階段**：當功能測試完成、使用者明確指示準備 Git Push 或發布正式版時，方可一次性統一遞增版本號。
   * **進版同步檔案**：主變更 (MAJOR)、功能增刪 (MINOR)、Bug 修復 (PATCH) 與 Android `versionCode` (單調遞增) 必須同步修改於 `app.js`、`build.gradle` 與 `package.json`，並與 Git Tag 保持 100% 一致。說明書 (`README.md`) 與規格書 (`SPECIFICATION.md`) 有修改後，當需要更新到雲端時，內標註的文件版本號必須始終與 App 版本號完全一致（如 App 版本為 1.7.9，則文件版本亦標註為 1.7.9）。
4. **💡 先說明原因再進行動作**：收到使用者回報的問題、警告或異常時，務必先向使用者清楚說明發生的根本原因 (Root Cause) 與預計的修復對策，確認思路後再執行相應的檔案修改與指令操作。
5. **📖 說明書與規格書職責分流原則**：
   * `README.md` 僅作為純粹的使用者操作手冊（專注於功能介紹、按鈕選單、鍵盤操作與 TTS 發音障礙排除）。
   * `SPECIFICATION.md` 為權威技術規格書（收錄系統架構、Schema、正規化備份規格、防禦機制、演算法、建置與 OTA 流水線）。
6. **🌐 數據正規化與指標完整性鐵律**：
   * 進行備份與狀態瘦身時，僅剝離重複嵌入的 `data` 物件，必須 100% 完整保留 `archivedDate`, `step`, `interval`, `immune`, `totalFails`, `mistakesCount`, `correctCount` 等所有特訓冷卻規格指標。
   * 還原解析時若錯題單字已自字典中被刪除，採方案 A 自動過濾清理孤兒錯題，保證關卡與歷史殿堂出題乾淨。

---

## 4. 自動化測試與本地伺服器測試規範 (Testing & Local Server Guidelines)

*   **動態連接埠分配 (Dynamic Port)**：進行本地測試或 Selenium 自動化測試時，**禁止**使用固定 HTTP 連接埠 (例如 8001)。應一律綁定連接埠 `0`（由 OS 分配閒置連接埠），並將目標連線網址指定為 `127.0.0.1`，以防 `localhost` 本機 DNS 解析失敗或 IPv6/IPv4 衝突導致連線逾時。
*   **伺服器資源回收 (Resource Cleanup)**：測試腳本結束前（不論成功或失敗），必須在 `finally` 區塊中明確執行 `httpd.shutdown()` 和 `httpd.server_close()` 釋放線程與 Socket 資源，防止殘存殭屍程序佔用連接埠。
*   **非阻塞本地伺服器 (Non-blocking Local Server)**：在 Windows 環境下，提供本地伺服器測試指令時，應搭配 `start` 開啟新視窗（例如 `npm run serve`），防止持久運行的伺服器行程直接卡死終端機。

---

## 5. Capacitor 原生平台檔案與套件處理規範 (Capacitor Native Platform Guidelines)

*   **WebView 檔案下載限制 (File Export in WebView)**：Android/iOS WebView 預設會阻擋 Blob URL 下載。字庫、歷史紀錄與備份 JSON 的匯出功能必須整合 `@capacitor/filesystem` (寫入 `CACHE` 目錄) 與 `@capacitor/share` (喚起原生分享選單)。
*   **分享取消處理 (Graceful Share Cancellation)**：原生分享外掛在使用者主動取消分享時會拋出例外（例如 `Share canceled`）。寫入成功後若因分享取消而進入 `catch`，不應觸發剪貼簿備份或彈出「請確認 App 權限」之誤導性警告。
*   **Kotlin 依賴衝突解決 (Kotlin Dependencies)**：當遇到舊外掛（如 Cordova）引入 `kotlin-stdlib-jdk7/8` 導致 Gradle `CheckDuplicates` 報出重複 Class 衝突時，應在 `android/build.gradle` 的 `allprojects` 區塊加入 `configurations.all { exclude group: 'org.jetbrains.kotlin', module: 'kotlin-stdlib-jdk7'; exclude group: 'org.jetbrains.kotlin', module: 'kotlin-stdlib-jdk8' }` 予以全域排除，由更高版的 `kotlin-stdlib` (1.8.22+) 統一處理。

---

## 6. 完整技術與 Token 指引手冊 (Full Documentation & Token Saver)

關於更詳細的聽讀特訓機制（盲聽、逐字拼讀高亮）、手滑強制重寫邏輯、CORS WebView 建置原因、各模組詳細依賴關係及 Token 節省技巧，請參閱 `.agents/` 目錄：
*   **技術手冊**：[DEVELOPMENT_GUIDE.md](file:///e:/ProjectCode/VocabTool-App/.agents/DEVELOPMENT_GUIDE.md)
*   **Token 節省指南**：[AI_AGENT_TOKEN_SAVER.md](file:///e:/ProjectCode/VocabTool-App/.agents/AI_AGENT_TOKEN_SAVER.md)

---

## 7. Token 消耗與環境優化鐵律 (Token Optimization Guidelines)
為了防止 AI Agent 對話因 Context 膨脹而耗盡 Token 或響應遲緩，開發與編譯時必須嚴格遵守以下準則：
1. **編譯輸出限流 (Quiet Build Output)**：
   - 執行 Gradle 編譯指令（如 `.\gradlew.bat assembleDebug`）時，一律加上 `-q` (Quiet) 參數或重新導向輸出至檔案（例如 `> build.log`），**嚴禁**將數萬行的完整 Gradle 編譯日誌直接輸出到終端機。
2. **精準檔案操作 (Precise File Operations)**：
   - 除非必要，否則**關鍵修改**一律使用 `replace_file_content` 做局部代碼塊的精準修改，**禁止**重寫或讀取整支大檔案。
3. **無用輸出屏蔽 (Suppress Verbose Output)**：
   - 執行測試或搜尋時，過濾掉不必要的除錯輸出。僅在失敗時將錯誤資訊寫入暫存檔案或截圖，切勿大量 `print`。


