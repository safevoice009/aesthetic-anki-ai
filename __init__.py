import os
import re
import json
import urllib.request
import urllib.parse
from aqt import mw, gui_hooks
from aqt.editor import Editor
from aqt.utils import showInfo, showWarning

# Dual PyQt5/PyQt6 compatibility
try:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
        QLabel, QComboBox, QPushButton, QProgressBar, QSplitter,
        QTabWidget, QWidget, QLineEdit, QFileDialog
    )
    from PyQt6.QtCore import QThread, pyqtSignal, Qt
except ImportError:
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
        QLabel, QComboBox, QPushButton, QProgressBar, QSplitter,
        QTabWidget, QWidget, QLineEdit, QFileDialog
    )
    from PyQt5.QtCore import QThread, pyqtSignal, Qt

# Premium Dark & Sand Gold Styling
QSS_STYLESHEET = """
QDialog {
    background-color: #0d0d0f;
    color: #ffffff;
}
QTabWidget::pane {
    border: 1px solid rgba(197, 168, 128, 0.15);
    background-color: #0d0d0f;
    border-radius: 6px;
}
QTabBar::tab {
    background-color: #141416;
    color: #73736e;
    border: 1px solid rgba(197, 168, 128, 0.15);
    border-bottom: none;
    padding: 8px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: bold;
    font-size: 12px;
}
QTabBar::tab:selected {
    background-color: #0d0d0f;
    color: #c5a880;
    border-bottom: 2px solid #c5a880;
}
QLabel {
    color: #c5a880;
    font-size: 11px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
QTextEdit, QLineEdit {
    background-color: #141416;
    color: #ffffff;
    border: 1px solid rgba(197, 168, 128, 0.15);
    border-radius: 6px;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 13px;
    padding: 8px;
}
QTextEdit:focus, QLineEdit:focus {
    border: 1px solid #c5a880;
}
QComboBox {
    background-color: #141416;
    color: #ffffff;
    border: 1px solid rgba(197, 168, 128, 0.15);
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 13px;
}
QComboBox:focus {
    border: 1px solid #c5a880;
}
QPushButton {
    background-color: #c5a880;
    color: #000000;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #e5d3b3;
}
QPushButton:disabled {
    background-color: #262628;
    color: #666668;
}
QProgressBar {
    border: 1px solid rgba(197, 168, 128, 0.15);
    border-radius: 6px;
    text-align: center;
    background-color: #141416;
    color: #ffffff;
    font-size: 11px;
}
QProgressBar::chunk {
    background-color: #c5a880;
    border-radius: 5px;
}
"""

# Presets for background images matching "studying/coffee/minimalist" themes
IMAGE_PRESETS = {
    "Minimalist Coffee Shop": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?q=80&w=600&auto=format&fit=crop",
    "Midnight Neon": "https://images.unsplash.com/photo-1519681393784-d120267933ba?q=80&w=600&auto=format&fit=crop",
    "Sakura Blossom": "https://images.unsplash.com/photo-1522441815192-d9f04eb0615c?q=80&w=600&auto=format&fit=crop",
    "Nordic Slate": "https://images.unsplash.com/photo-1497366216548-37526070297c?q=80&w=600&auto=format&fit=crop"
}

def markdown_to_html(md_text):
    # Regex fallback formatting for markdown in case the model returns markdown symbols
    html = md_text
    # Bold
    html = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", html)
    # Italics
    html = re.sub(r"\*(.*?)\*", r"<i>\1</i>", html)
    # Inline code
    html = re.sub(r"`(.*?)`", r"<code style='background:#1a1a1c;padding:2px 4px;border-radius:4px;color:#c5a880;'>\1</code>", html)
    # Lists
    html = re.sub(r"^\s*[-*]\s*(.*?)$", r"<li>\1</li>", html, flags=re.MULTILINE)
    return html

def wrap_with_theme(html_content, theme_name, bg_url, custom_css, font_family, max_width):
    # Parse font selections
    font_stack = "sans-serif"
    if font_family == "Serif (Georgia)":
        font_stack = "'Georgia', 'Times New Roman', serif"
    elif font_family == "Modern (Segoe UI)":
        font_stack = "'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif"
    elif font_family == "Calligraphy (Playfair)":
        font_stack = "'Playfair Display', 'Brush Script MT', cursive, serif"
    elif font_family == "Retro Monospace (JetBrains Mono)":
        font_stack = "'JetBrains Mono', 'Courier New', monospace"
        
    theme_styles = ""
    if theme_name == "Minimalist Coffee Shop":
        theme_styles = f"""
            background: linear-gradient(rgba(247, 245, 240, 0.92), rgba(247, 245, 240, 0.92)), url('{bg_url}');
            background-size: cover;
            background-position: center;
            color: #2D221E;
            border: 1px solid rgba(45, 34, 30, 0.15);
            border-radius: 12px;
            font-family: {font_stack};
            padding: 22px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
            max-width: {max_width};
            margin: 8px auto;
        """
    elif theme_name == "Midnight Neon":
        theme_styles = f"""
            background: linear-gradient(rgba(13, 13, 15, 0.85), rgba(13, 13, 15, 0.85)), url('{bg_url}');
            background-size: cover;
            background-position: center;
            color: #ffffff;
            border: 1px solid #c5a880;
            border-radius: 12px;
            font-family: {font_stack};
            padding: 22px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            max-width: {max_width};
            margin: 8px auto;
        """
    elif theme_name == "Sakura Blossom":
        theme_styles = f"""
            background: linear-gradient(rgba(255, 245, 245, 0.94), rgba(255, 245, 245, 0.94)), url('{bg_url}');
            background-size: cover;
            background-position: center;
            color: #3a2a2a;
            border: 1px solid rgba(224, 184, 184, 0.5);
            border-radius: 12px;
            font-family: {font_stack};
            padding: 22px;
            box-shadow: 0 4px 20px rgba(224, 184, 184, 0.2);
            max-width: {max_width};
            margin: 8px auto;
        """
    else: # Nordic Slate
        theme_styles = f"""
            background: linear-gradient(rgba(240, 244, 248, 0.95), rgba(240, 244, 248, 0.95)), url('{bg_url}');
            background-size: cover;
            background-position: center;
            color: #2c3e50;
            border: 1px solid rgba(180, 190, 200, 0.5);
            border-radius: 12px;
            font-family: {font_stack};
            padding: 22px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.03);
            max-width: {max_width};
            margin: 8px auto;
        """
        
    theme_styles = theme_styles.replace("{bg_url}", bg_url)
    
    # Custom CSS overrides
    full_css = theme_styles + "\n" + custom_css
    
    # Wrap formatting
    return f'<div style="{full_css}">{html_content}</div>'


class LLMWorker(QThread):
    finished = pyqtSignal(str, str)  # Emits (html_result, error_message)

    def __init__(self, text, template, api_url, custom_system_prompt):
        super().__init__()
        self.text = text
        self.template = template
        self.api_url = api_url
        self.custom_system_prompt = custom_system_prompt

    def run(self):
        # Build prompt using custom system prompt if provided
        if self.custom_system_prompt:
            prompt = self.custom_system_prompt.replace("{text}", self.text).replace("{template}", self.template)
        else:
            cloze_note = ""
            if "Cloze" in self.template:
                cloze_note = "Identify key technical terms, statistics, or phrases and wrap them in Anki's standard cloze deletion markers, e.g. {{c1::hidden text}} or {{c2::hidden text}}."
                
            prompt = f"""You are an expert card designer. Structure the following raw text to be highly readable for study. 
Use semantic HTML tags: headings (e.g. <h3> or <h4>), clear bullet points, bold terms, or key-value grids/tables.
Do not include any background containers, card margins, or generic card borders, as these will be wrapped automatically.
{cloze_note}
Return ONLY clean raw HTML ready to insert inside a container div. Do not wrap in ```html blockquotes.

Original Text:
{self.text}"""

        payload = {
            "model": "Qwen2.5-Coder-7B-Instruct-int4-ov",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }

        try:
            req = urllib.request.Request(
                self.api_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=25) as response:
                res_body = json.loads(response.read().decode("utf-8"))
                html = res_body["choices"][0]["message"]["content"].strip()
                
                # Strip markdown fences if returned
                if html.startswith("```html"):
                    html = html[7:]
                elif html.startswith("```"):
                    html = html[3:]
                if html.endswith("```"):
                    html = html[:-3]
                html = html.strip()
                
                # Parse markdown fallbacks if LLM returned standard md elements
                html = markdown_to_html(html)
                
                self.finished.emit(html, "")
        except Exception as e:
            self.finished.emit("", str(e))


class BeautifierDialog(QDialog):
    def __init__(self, editor, initial_text):
        super().__init__(editor.parentWindow)
        self.editor = editor
        self.setWindowTitle("Aesthetic Anki AI")
        self.resize(920, 620)
        self.setStyleSheet(QSS_STYLESHEET)
        
        self.worker = None
        self.raw_html_result = "" # Cache for wrapping dynamically
        
        # Load user configurations
        self.load_config()
        self.init_ui(initial_text)

    def load_config(self):
        self.config = mw.addonManager.getConfig(__name__) or {
            "theme": "Minimalist Coffee Shop",
            "background_image_url": IMAGE_PRESETS["Minimalist Coffee Shop"],
            "custom_css": "",
            "api_url": "http://127.0.0.1:8082/v1/chat/completions",
            "custom_system_prompt": "",
            "font_family": "Serif (Georgia)",
            "card_max_width": "600px"
        }

    def save_config(self):
        mw.addonManager.writeConfig(__name__, self.config)

    def init_ui(self, initial_text):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # Tabs system
        self.tabs = QTabWidget()
        
        # --- TAB 1: WORKSPACE ---
        workspace_tab = QWidget()
        workspace_layout = QVBoxLayout(workspace_tab)
        workspace_layout.setContentsMargins(10, 10, 10, 10)
        workspace_layout.setSpacing(10)

        # Workspace controls
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Select Template Layout:"))
        
        self.template_select = QComboBox()
        self.template_select.addItems([
            "✨ Auto-Detect Layout",
            "✨ Auto-Generate Cloze Deletion",
            "Concept Card (Grid Layout)", 
            "Code Showcase (Dark Block)", 
            "Question & Answer (Glassmorphic Box)",
            "Vocabulary / Key Terms (Table style)"
        ])
        controls_layout.addWidget(self.template_select)
        controls_layout.addStretch()
        workspace_layout.addLayout(controls_layout)

        # Splitter for input/output
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left pane (Input)
        left_widget = QVBoxLayout()
        left_widget.addWidget(QLabel("Original Content"))
        self.input_edit = QTextEdit()
        self.input_edit.setPlainText(initial_text)
        self.input_edit.setPlaceholderText("Enter card content to beautify...")
        
        left_container = QWidget()
        left_container.setLayout(left_widget)
        left_widget.layout().addWidget(self.input_edit)
        splitter.addWidget(left_container)

        # Right pane (Preview)
        right_widget = QVBoxLayout()
        right_widget.addWidget(QLabel("AI Beautified Preview (Theme Applied)"))
        self.preview_edit = QTextEdit()
        self.preview_edit.setReadOnly(True)
        self.preview_edit.setPlaceholderText("Generated premium layout will preview here...")
        
        right_container = QWidget()
        right_container.setLayout(right_widget)
        right_widget.layout().addWidget(self.preview_edit)
        splitter.addWidget(right_container)
        
        workspace_layout.addWidget(splitter)
        self.tabs.addTab(workspace_tab, "Beautifier Workspace")

        # --- TAB 2: AESTHETICS & SETTINGS ---
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        settings_layout.setContentsMargins(16, 12, 16, 12)
        settings_layout.setSpacing(8)

        # Theme selector row
        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Aesthetic Theme:"))
        self.theme_select = QComboBox()
        self.theme_select.addItems([
            "Minimalist Coffee Shop",
            "Midnight Neon",
            "Sakura Blossom",
            "Nordic Slate"
        ])
        self.theme_select.setCurrentText(self.config.get("theme", "Minimalist Coffee Shop"))
        self.theme_select.currentTextChanged.connect(self.on_theme_preset_changed)
        theme_row.addWidget(self.theme_select)
        
        theme_row.addWidget(QLabel("Font Preset:"))
        self.font_select = QComboBox()
        self.font_select.addItems([
            "Serif (Georgia)",
            "Modern (Segoe UI)",
            "Calligraphy (Playfair)",
            "Retro Monospace (JetBrains Mono)"
        ])
        self.font_select.setCurrentText(self.config.get("font_family", "Serif (Georgia)"))
        self.font_select.currentTextChanged.connect(self.on_style_field_changed)
        theme_row.addWidget(self.font_select)
        
        theme_row.addWidget(QLabel("Max Width:"))
        self.max_width_edit = QLineEdit()
        self.max_width_edit.setMaximumWidth(80)
        self.max_width_edit.setText(self.config.get("card_max_width", "600px"))
        self.max_width_edit.textChanged.connect(self.on_style_field_changed)
        theme_row.addWidget(self.max_width_edit)
        settings_layout.addLayout(theme_row)

        # Background Image URL row
        bg_row = QVBoxLayout()
        bg_row.addWidget(QLabel("Card Background Image URL (Minimalist/Study):"))
        self.bg_url_edit = QLineEdit()
        self.bg_url_edit.setText(self.config.get("background_image_url", ""))
        self.bg_url_edit.textChanged.connect(self.on_style_field_changed)
        bg_row.addWidget(self.bg_url_edit)
        settings_layout.addLayout(bg_row)

        # Custom CSS row
        css_row = QVBoxLayout()
        css_row.addWidget(QLabel("Custom CSS Style Overrides:"))
        self.css_edit = QTextEdit()
        self.css_edit.setMaximumHeight(80)
        self.css_edit.setPlainText(self.config.get("custom_css", ""))
        self.css_edit.setPlaceholderText("e.g. font-size: 15px; border-color: red;")
        self.css_edit.textChanged.connect(self.on_style_field_changed)
        css_row.addWidget(self.css_edit)
        settings_layout.addLayout(css_row)

        # Custom Prompt Fine-Tuner
        prompt_row = QVBoxLayout()
        prompt_row.addWidget(QLabel("AI Prompt Instruction Fine-Tuner (Leave blank for default):"))
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setMaximumHeight(80)
        self.prompt_edit.setPlainText(self.config.get("custom_system_prompt", ""))
        self.prompt_edit.setPlaceholderText("Define formatting styles, translations, or layout specifications. Use {text} and {template} placeholders.")
        prompt_row.addWidget(self.prompt_edit)
        settings_layout.addLayout(prompt_row)

        # Local LLM API URL
        api_row = QHBoxLayout()
        api_row.addWidget(QLabel("LLM API Endpoint:"))
        self.api_url_edit = QLineEdit()
        self.api_url_edit.setText(self.config.get("api_url", "http://127.0.0.1:8082/v1/chat/completions"))
        api_row.addWidget(self.api_url_edit)
        settings_layout.addLayout(api_row)

        # Settings Actions (Import / Save)
        settings_btn_row = QHBoxLayout()
        self.import_btn = QPushButton("Import CSS File 📥")
        self.import_btn.clicked.connect(self.import_custom_css)
        self.save_btn = QPushButton("Save Settings 💾")
        self.save_btn.clicked.connect(self.save_settings_action)
        settings_btn_row.addWidget(self.import_btn)
        settings_btn_row.addStretch()
        settings_btn_row.addWidget(self.save_btn)
        settings_layout.addLayout(settings_btn_row)

        self.tabs.addTab(settings_tab, "Aesthetics & Settings")
        main_layout.addWidget(self.tabs)

        # Progress / Status
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #dcdcd8; font-size: 11px; text-transform: none; font-weight: normal;")
        main_layout.addWidget(self.status_label)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        self.beautify_btn = QPushButton("Analyze & Beautify 🪄")
        self.beautify_btn.clicked.connect(self.start_beautification)
        
        self.insert_btn = QPushButton("Insert into Card ✓")
        self.insert_btn.setEnabled(False)
        self.insert_btn.clicked.connect(self.insert_into_card)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("background-color: #262628; color: #ffffff;")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.beautify_btn)
        btn_layout.addWidget(self.insert_btn)
        main_layout.addLayout(btn_layout)

    def on_theme_preset_changed(self, theme_name):
        if theme_name in IMAGE_PRESETS:
            self.bg_url_edit.setText(IMAGE_PRESETS[theme_name])
        self.update_preview_live()

    def on_style_field_changed(self):
        self.update_preview_live()

    def update_preview_live(self):
        if not self.raw_html_result:
            return
        theme = self.theme_select.currentText()
        bg_url = self.bg_url_edit.text().strip()
        custom_css = self.css_edit.toPlainText().strip()
        font_family = self.font_select.currentText()
        max_width = self.max_width_edit.text().strip()
        wrapped_html = wrap_with_theme(self.raw_html_result, theme, bg_url, custom_css, font_family, max_width)
        self.preview_edit.setHtml(wrapped_html)

    def import_custom_css(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Custom CSS File", "", "CSS Files (*.css)")
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.css_edit.setPlainText(f.read())
                self.status_label.setText("Custom CSS file imported successfully!")
            except Exception as e:
                showWarning(f"Failed to read CSS file: {e}", self)

    def save_settings_action(self):
        self.config["theme"] = self.theme_select.currentText()
        self.config["background_image_url"] = self.bg_url_edit.text().strip()
        self.config["custom_css"] = self.css_edit.toPlainText().strip()
        self.config["custom_system_prompt"] = self.prompt_edit.toPlainText().strip()
        self.config["api_url"] = self.api_url_edit.text().strip()
        self.config["font_family"] = self.font_select.currentText()
        self.config["card_max_width"] = self.max_width_edit.text().strip()
        self.save_config()
        self.status_label.setText("Aesthetic settings successfully saved!")

    def auto_detect_template(self, text):
        # Quick regex structural checks to determine best styling
        code_patterns = [
            r"\bdef\s+\w+\(", r"\bclass\s+\w+", r"\bimport\s+\w+",
            r"#include\s+<", r"\bpublic\s+class\s+", r"function\s+\w+\(",
            r"\bconst\s+\w+\s*=", r"<\/?[a-z][\s\S]*>", r"```[a-z]*"
        ]
        is_code = any(re.search(pat, text) for pat in code_patterns) or text.count(";") > 5
        if is_code:
            return "Code Showcase (Dark Block)"

        is_qa = "?" in text and len(text.split("\n")) <= 4
        if is_qa:
            return "Question & Answer (Glassmorphic Box)"

        is_list = text.count(":") >= 2 or text.count("- ") >= 2 or text.count("* ") >= 2
        if is_list:
            return "Vocabulary / Key Terms (Table style)"

        return "Concept Card (Grid Layout)"

    def start_beautification(self):
        text = self.input_edit.toPlainText().strip()
        if not text:
            showWarning("Please enter some text to beautify first.", self)
            return

        self.beautify_btn.setEnabled(False)
        self.insert_btn.setEnabled(False)
        self.progress_bar.setVisible(True)

        template = self.template_select.currentText()
        if "Auto-Detect Layout" in template:
            detected = self.auto_detect_template(text)
            self.status_label.setText(f"Auto-detected structure: {detected}. Contacting LLM...")
            template = detected
        elif "Auto-Generate Cloze" in template:
            self.status_label.setText("Extracting key terms for Cloze Deletion formatting...")
            template = "Cloze Deletion formatting"
        else:
            self.status_label.setText("Querying local OpenVINO model pipeline...")

        api_url = self.api_url_edit.text().strip()
        custom_system_prompt = self.prompt_edit.toPlainText().strip()
        
        self.worker = LLMWorker(text, template, api_url, custom_system_prompt)
        self.worker.finished.connect(self.on_beautify_finished)
        self.worker.start()

    def on_beautify_finished(self, html, error):
        self.progress_bar.setVisible(False)
        self.beautify_btn.setEnabled(True)

        if error:
            self.status_label.setText("Failed to connect to local server.")
            showWarning(f"Error querying local server: {error}\nMake sure team-leader/ov_server is active.", self)
        else:
            self.status_label.setText("Layout generated successfully!")
            self.raw_html_result = html
            self.update_preview_live()
            self.insert_btn.setEnabled(True)

    def insert_into_card(self):
        theme = self.theme_select.currentText()
        bg_url = self.bg_url_edit.text().strip()
        custom_css = self.css_edit.toPlainText().strip()
        font_family = self.font_select.currentText()
        max_width = self.max_width_edit.text().strip()
        final_html = wrap_with_theme(self.raw_html_result, theme, bg_url, custom_css, font_family, max_width)
        
        if final_html:
            self.editor.web.eval(f"document.execCommand('insertHTML', false, {json.dumps(final_html)})")
            self.accept()


def on_beautify_click(editor: Editor):
    try:
        current_field_index = editor.currentField
        if current_field_index is not None:
            initial_text = editor.note.fields[current_field_index]
        else:
            initial_text = ""
    except Exception:
        initial_text = ""
        
    dialog = BeautifierDialog(editor, initial_text)
    # Dual PyQt5/PyQt6 dialog execution compatibility
    if hasattr(dialog, "exec"):
        dialog.exec()
    else:
        dialog.exec_()


def add_beautifier_button(buttons, editor):
    addon_dir = os.path.dirname(__file__)
    icon_path = os.path.join(addon_dir, "wand.svg")
    
    btn = editor.addButton(
        icon=icon_path,
        cmd="aesthetic_anki_ai",
        func=lambda _editor=None: on_beautify_click(editor),
        tip="🪄 Aesthetic Anki AI (Auto-layout & presets)",
        label="🪄"
    )
    buttons.append(btn)
    return buttons


def init():
    gui_hooks.editor_did_init_buttons.append(add_beautifier_button)


init()

