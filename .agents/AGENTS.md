# 🤖 VocabTool-App AI Agent Workspace Instructions & Knowledge

本文件記錄 `VocabTool-App` 專案的核心開發規範、架構決策與運作流程。在任何電腦開開啟本專案時，AI Agent 均會自動載入本規範以維持無縫工作接續。

---

## 1. 專案架構規範 (Clean Modular Architecture)

*   **開發源碼目錄 (`www/js/`)**：
    *   `utils/`：純演算法與 API 工具（`textUtils.js`, `dictionaryApi.js`）。
    *   `hooks/`：React 業務邏輯與狀態（`useVocabState.js`）。
    *   `components/`：1:1 原裝 UI 視覺元件 (`Header.js`, `Dashboard.js`, `Sessions.js`, `AudioPlayer.js`, `Modals.js`)。
    *   `app.js`：核心生命週期進入點。
*   **發布與編譯檔 (`www/index.html`)**：
    *   由建置腳本 `scripts/build.js` 自動生成。
    *   **原因**：Android WebView (`file://`) 嚴格禁止 AJAX 跨檔讀取外部 JSX。預編譯打包可確保離線免 CORS 錯誤。

---

## 2. 開發與打包指令與環境變數 (Commands & Environment)

*   **環境變數設定 (PowerShell 範例)**：
    ```powershell
    # 設定 Java 21 JDK 路徑 (使用 Android Studio 內建 JBR)
    $env:JAVA_HOME="D:\Android\Android Studio\jbr"
    
    # 將 ADB 加入 PATH (若尚未設定)
    $env:Path += ";C:\Users\hys82\AppData\Local\Android\Sdk\platform-tools"
    ```

*   **開發指令**：
    ```powershell
    # 1. 預編譯打包 JavaScript 模組至 www/index.html
    cmd /c npm run build
    
    # 2. 同步 web 資源至 Android 原生工程
    cmd /c npx cap sync android
    
    # 3. 編譯 Debug APK
    cd android
    .\gradlew.bat assembleDebug
    
    # 4. 安裝並重啟 App 至連線裝置
    & "C:\Users\hys82\AppData\Local\Android\Sdk\platform-tools\adb.exe" install -r .\app\build\outputs\apk\debug\app-debug.apk
    & "C:\Users\hys82\AppData\Local\Android\Sdk\platform-tools\adb.exe" shell am start -n com.vocabtool.app/com.vocabtool.app.MainActivity
    ```

---

## 3. 重要開發鐵律 (Strict Guidelines)

1. **🔒 Git Server 上傳限制**：所有程式碼開發、模組編譯與版本 tag 動作一律先在 Local 本機端完成。未經使用者明確口頭同意，絕不自動執行 `git push`、推送 tag 或任何將變更上傳至 Git Server 的動作！
2. **🎨 UI 0 變化原則**：進行重構時，務必確保原本的 Tailwind CSS 樣式、動畫、按鈕顏色與排版 100% 零偏離。
3. **🏷️ 語意化版本控制與發布進版時機 (SemVer & Release Workflow)**：
   * **本地開發測試期**：進行功能開發、重構或 Bug 修復時，**版本號保持不動**，專注於程式碼修改與測試，切勿在本地微調時隨意遞增版號。
   * **正式發布 / Git Push 階段**：當功能測試完成、使用者明確指示準備 Git Push 或發布正式版時，方可一次性統一遞增版本號。
   * **進版同步檔案**：主變更 (MAJOR)、功能增刪 (MINOR)、Bug 修復 (PATCH) 與 Android `versionCode` (單調遞增) 必須同步修改於 `app.js`、`build.gradle` 與 `package.json`，並與 Git Tag 保持 100% 一致。規格文件如 `SPECIFICATION.md` 僅在規格內文有實質修改時方可進版。

---

## 4. 自動化測試與本地伺服器測試規範 (Testing & Local Server Guidelines)

*   **動態連接埠分配 (Dynamic Port)**：進行本地測試或 Selenium 自動化測試時，**禁止**使用固定 HTTP 連接埠 (例如 8001)。應一律綁定連接埠 `0`（由 OS 分配閒置連接埠），並將目標連線網址指定為 `127.0.0.1`，以防 `localhost` 本機 DNS 解析失敗或 IPv6/IPv4 衝突導致連線逾時。
*   **伺服器資源回收 (Resource Cleanup)**：測試腳本結束前（不論成功或失敗），必須在 `finally` 區塊中明確執行 `httpd.shutdown()` 和 `httpd.server_close()` 釋放線程與 Socket 資源，防止殘存殭屍程序佔用連接埠。
*   **非阻塞本地伺服器 (Non-blocking Local Server)**：在 Windows 環境下，提供本地伺服器測試指令時，應搭配 `start` 開啟新視窗（例如 `npm run serve`），防止持久運行的伺服器行程直接卡死終端機。

---

## 5. Capacitor 原生平台檔案與套件處理規範 (Capacitor Native Platform Guidelines)

*   **WebView 檔案下載限制 (File Export in WebView)**：Android/iOS WebView 預設會阻擋 Blob URL 下載。字庫、歷史紀錄與備份 JSON 的匯出功能必須整合 `@capacitor/filesystem` (寫入 `CACHE` 目錄) 與 `@capacitor/share` (喚起原生分享選單)。
*   **分享取消處理 (Graceful Share Cancellation)**：原生分享外掛在使用者主動取消分享時會拋出例外（例如 `Share canceled`）。寫入成功後若因分享取消而進入 `catch`，不應觸發剪貼簿備份或彈出「請確認 App 權限」之誤導性警告。
*   **Kotlin 與依賴版本管理 (Kotlin Dependencies)**：**禁止**在 `android/build.gradle` 中強制鎖定（force）舊版 Kotlin 標準庫（如 `kotlin-stdlib:1.8.22`），避免與 `@capacitor/filesystem` 等現代原生外掛所需的協程庫發生 `NoClassDefFoundError: Failed resolution of: Lkotlin/coroutines/jvm/internal/SpillingKt;` 衝突。應交由 Gradle 自行解析最高相容版本。

---

## 6. 完整技術手冊 (Full Documentation)

關於更詳細的聽讀特訓機制（盲聽、逐字拼讀高亮）、手滑強制重寫邏輯、CORS WebView 建置原因及各模組詳細依賴關係，請參閱根目錄的：
*   **技術手冊**：[DEVELOPMENT_GUIDE.md](file:///d:/MyProjects/VocabTool-App/DEVELOPMENT_GUIDE.md)

---

## 7. Token 消耗與環境優化鐵律 (Token Optimization Guidelines)
為了防止 AI Agent 對話因 Context 膨脹而耗盡 Token 或響應遲緩，開發與編譯時必須嚴格遵守以下準則：
1. **編譯輸出限流 (Quiet Build Output)**：
   - 執行 Gradle 編譯指令（如 `.\gradlew.bat assembleDebug`）時，一律加上 `-q` (Quiet) 參數或重新導向輸出至檔案（例如 `> build.log`），**嚴禁**將數萬行的完整 Gradle 編譯日誌直接輸出到終端機。
2. **精準檔案操作 (Precise File Operations)**：
   - 除非必要，否則**關鍵修改**一律使用 `replace_file_content` 做局部代碼塊的精準修改，**禁止**重寫或讀取整支大檔案。
3. **無用輸出屏蔽 (Suppress Verbose Output)**：
   - 執行測試或搜尋時，過濾掉不必要的除錯輸出。僅在失敗時將錯誤資訊寫入暫存檔案或截圖，切勿大量 `print`。


