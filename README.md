# Aesthetic Anki AI — Premium Card Layout Formatter 🪄

An ultra-premium, highly customizable Anki add-on that uses local LLMs to format, beautify, and style your cards using gorgeous studygram aesthetics (Minimalist Coffee, Midnight Neon, Sakura Blossom, Nordic Slate).

---

## Features
- **✨ Auto-Layout Detection:** Automatically analyzes the structure of your card content (detects code blocks, question-and-answer patterns, list terms) and applies the optimal layout format before formatting.
- **🎨 Premium Studygram Presets:** Four built-in luxury themes (Minimalist Coffee Shop, Midnight Neon glassmorphism, Sakura Blossom, and Nordic Slate) that style your cards with gorgeous background wallpapers and custom typography.
- **⚙️ AI Prompt Fine-Tuner:** Customize the system prompt sent to the LLM directly inside the add-on settings to translate text, add icons, or generate cloze deletions.
- **📥 Custom CSS Import:** Modify card styling on the fly or load external `.css` files directly into the formatting engine.
- **⚡ Asynchronous Execution:** Spawns thread-safe queries using `QThread` to ensure the Anki editor never freezes during generations.

---

## Installation

### Manual Installation (Development / Symlink)
To load this add-on into your Anki environment:

1. Clone or copy this repository to your machine.
2. Locate your Anki add-on folder:
   - **Linux (Flatpak):** `~/.var/app/net.ankiweb.Anki/data/Anki2/addons21/`
   - **Linux (Standard):** `~/.local/share/Anki2/addons21/`
   - **macOS:** `~/Library/Application Support/Anki2/addons21/`
   - **Windows:** `%APPDATA%\Anki2\addons21\`
3. Create a symlink or directory named `aesthetic_anki_ai` in that folder pointing to this directory.
4. Run the helper installation script (for Linux):
   ```bash
   chmod +x install_addon.sh && ./install_addon.sh
   ```
5. Restart Anki.

---

## How to Use
1. Open the Anki Card Editor (Add Card or Edit Card).
2. Click the new magic wand (**🪄**) button in the toolbar.
3. Select your desired layout preset or choose **✨ Auto-Detect Layout**.
4. Click **Analyze & Beautify** to fetch the formatted card live from your local LLM.
5. Review the live preview, customize settings under the **Aesthetics & Settings** tab, and click **Insert into Card** to replace or insert styled HTML at your cursor selection.

---

## Local LLM Setup
By default, the plugin connects to `http://127.0.0.1:8082/v1/chat/completions` (OpenAI-compatible server format). You can configure it to talk directly to your active local model provider (Ollama, LM Studio, AnythingLLM, OpenVINO) by updating the **LLM API Endpoint** text field under the Settings tab.
