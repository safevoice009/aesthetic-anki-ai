"""Premium Sand Gold themed PyQt modal dialog for card beautification."""

import html

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QTextOption
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from .formatters import TEMPLATE_INSTRUCTIONS, build_prompt
from .llm_worker import LLMWorker

QSS = """
QDialog {
    background-color: #0d0d0f;
    color: #F7F5F0;
    border: 1px solid rgba(197, 168, 128, 0.3);
    border-radius: 8px;
}

QLabel {
    color: #F7F5F0;
    font-family: system-ui, -apple-ui, sans-serif;
    font-weight: 300;
    letter-spacing: 0.03em;
}

QComboBox {
    background-color: #0d0d0f;
    color: #F7F5F0;
    border: 1px solid rgba(197, 168, 128, 0.3);
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    font-family: system-ui, -apple-ui, sans-serif;
    min-height: 20px;
}

QComboBox:hover {
    border-color: #c5a880;
}

QComboBox::drop-down {
    border: none;
    width: 28px;
}

QComboBox::down-arrow {
    image: none;
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #0d0d0f;
    color: #F7F5F0;
    selection-background-color: rgba(197, 168, 128, 0.2);
    border: 1px solid rgba(197, 168, 128, 0.3);
    border-radius: 4px;
    outline: none;
}

QPlainTextEdit {
    background-color: #0d0d0f;
    color: #F7F5F0;
    border: 1px solid rgba(197, 168, 128, 0.25);
    border-radius: 6px;
    padding: 12px;
    font-family: "SF Mono", "Fira Code", monospace;
    font-size: 12px;
    selection-background-color: rgba(197, 168, 128, 0.3);
}

QPlainTextEdit:focus {
    border-color: #c5a880;
}

QPlainTextEdit[readOnly="true"] {
    color: rgba(247, 245, 240, 0.6);
}

QProgressBar {
    background-color: rgba(197, 168, 128, 0.1);
    border: none;
    border-radius: 3px;
    height: 6px;
    text-align: center;
    color: transparent;
}

QProgressBar::chunk {
    background-color: #c5a880;
    border-radius: 3px;
}

QPushButton {
    background-color: #c5a880;
    color: #0d0d0f;
    border: none;
    border-radius: 6px;
    padding: 10px 24px;
    font-size: 13px;
    font-weight: 600;
    font-family: system-ui, -apple-ui, sans-serif;
    letter-spacing: 0.04em;
}

QPushButton:hover {
    background-color: #d4b896;
}

QPushButton:pressed {
    background-color: #b09570;
}

QPushButton:disabled {
    background-color: rgba(197, 168, 128, 0.3);
    color: rgba(13, 13, 15, 0.5);
}

QPushButton#cancelBtn {
    background-color: transparent;
    color: rgba(247, 245, 240, 0.6);
    border: 1px solid rgba(197, 168, 128, 0.2);
}

QPushButton#cancelBtn:hover {
    border-color: rgba(197, 168, 128, 0.5);
    color: #F7F5F0;
}

QSplitter::handle {
    background-color: rgba(197, 168, 128, 0.15);
    width: 1px;
}
"""


class BeautifierDialog(QDialog):
    def __init__(self, editor, card_text: str, parent=None):
        super().__init__(parent)
        self._editor = editor
        self._original_text = card_text
        self._worker = None

        self.setWindowTitle("Local AI Card Beautifier")
        self.setMinimumSize(880, 620)
        self.setModal(True)
        self.setStyleSheet(QSS)

        self._build_ui()
        self._center_on_parent()

    def _center_on_parent(self):
        if self.parent():
            geom = self.parent().geometry()
            self.move(
                geom.center().x() - self.width() // 2,
                geom.center().y() - self.height() // 2,
            )

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # --- Header ---
        header = QLabel("♢  Card Beautifier")
        header_font = QFont("system-ui", 16, QFont.Weight.Light)
        header_font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 105)
        header.setFont(header_font)
        header.setStyleSheet("color: #c5a880; letter-spacing: 0.08em;")
        layout.addWidget(header)

        subtitle = QLabel("Select a template, preview the result, then apply.")
        subtitle.setStyleSheet("color: rgba(247, 245, 240, 0.5); font-size: 12px;")
        layout.addWidget(subtitle)

        # --- Template selector ---
        self._template_dropdown = QComboBox()
        templates = list(TEMPLATE_INSTRUCTIONS.keys())
        for t in templates:
            self._template_dropdown.addItem(t)
        self._template_dropdown.currentIndexChanged.connect(self._on_template_changed)
        layout.addWidget(self._template_dropdown)

        # --- Preview panels ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)

        before_widget = QWidget()
        before_layout = QVBoxLayout(before_widget)
        before_layout.setContentsMargins(0, 0, 0, 0)
        before_label = QLabel("BEFORE")
        before_label.setStyleSheet(
            "color: rgba(247, 245, 240, 0.35); font-size: 10px; letter-spacing: 0.15em; margin-bottom: 4px;"
        )
        self._before_edit = QPlainTextEdit()
        self._before_edit.setPlainText(self._original_text)
        self._before_edit.setReadOnly(True)
        self._before_edit.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        before_layout.addWidget(before_label)
        before_layout.addWidget(self._before_edit)

        after_widget = QWidget()
        after_layout = QVBoxLayout(after_widget)
        after_layout.setContentsMargins(0, 0, 0, 0)
        after_label = QLabel("AFTER")
        after_label.setStyleSheet(
            "color: rgba(247, 245, 240, 0.35); font-size: 10px; letter-spacing: 0.15em; margin-bottom: 4px;"
        )
        self._after_edit = QPlainTextEdit()
        self._after_edit.setReadOnly(True)
        self._after_edit.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        after_layout.addWidget(after_label)
        after_layout.addWidget(self._after_edit)

        splitter.addWidget(before_widget)
        splitter.addWidget(after_widget)
        layout.addWidget(splitter, stretch=1)

        # --- Progress bar ---
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setFixedHeight(6)
        self._progress.hide()
        layout.addWidget(self._progress)

        # --- Buttons ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setObjectName("cancelBtn")
        self._cancel_btn.clicked.connect(self.reject)

        self._apply_btn = QPushButton("Apply to Card")
        self._apply_btn.clicked.connect(self._apply_result)
        self._apply_btn.setEnabled(False)

        self._generate_btn = QPushButton("Generate")
        self._generate_btn.clicked.connect(self._generate)

        btn_layout.addWidget(self._cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self._generate_btn)
        btn_layout.addWidget(self._apply_btn)
        layout.addLayout(btn_layout)

    def _on_template_changed(self):
        self._after_edit.clear()

    def _set_loading(self, loading: bool):
        self._generate_btn.setEnabled(not loading)
        self._apply_btn.setEnabled(False)
        self._template_dropdown.setEnabled(not loading)
        self._progress.setVisible(loading)

    def _generate(self):
        content = self._before_edit.toPlainText().strip()
        if not content:
            return

        template = self._template_dropdown.currentText()
        messages = build_prompt(content, template)

        from aqt import mw

        config = mw.addonManager.getConfig(__name__)
        api_url = config.get("api_url", "http://127.0.0.1:8082/v1/chat/completions")
        model = config.get("model", "local-model")
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 2048)
        timeout = config.get("timeout_seconds", 60)

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        self._set_loading(True)
        self._worker = LLMWorker(api_url, payload, timeout, self)
        self._worker.finished.connect(self._on_result)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()

    def _on_result(self, html_output: str):
        self._set_loading(False)
        sanitized = html_output.strip()
        if sanitized.startswith("```html"):
            sanitized = sanitized[len("```html"):]
        if sanitized.startswith("```"):
            sanitized = sanitized[3:]
        if sanitized.endswith("```"):
            sanitized = sanitized[:-3]
        sanitized = sanitized.strip()

        self._after_edit.setPlainText(sanitized)
        self._apply_btn.setEnabled(bool(sanitized))

    def _on_error(self, msg: str):
        self._set_loading(False)
        self._after_edit.setPlainText(f"// Error: {msg}")
        self._apply_btn.setEnabled(False)

    def _apply_result(self):
        html_output = self._after_edit.toPlainText().strip()
        if not html_output:
            return

        note = self._editor.note
        fields = note.keys() if hasattr(note, "keys") else list(note.keys()) if hasattr(note, "keys") else []

        if fields:
            first_field = fields[0]
            note[first_field] = html_output
        else:
            if hasattr(note, "fields"):
                for fld in note.keys():
                    note[fld] = html_output
                    break
                else:
                    return

        if hasattr(self._editor, "loadNote"):
            self._editor.loadNote()
        elif hasattr(self._editor, "setNote"):
            self._editor.setNote(note)

        self.accept()
