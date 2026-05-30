import os
import re
import json
import uuid
import urllib.request
import urllib.parse
from aqt import mw, gui_hooks
from aqt.editor import Editor
from aqt.utils import showInfo, showWarning
from aqt.webview import AnkiWebView

# Detect active theme manager
try:
    from aqt.theme import theme_manager
    IS_DARK_THEME = theme_manager.night_mode
except Exception:
    IS_DARK_THEME = False

# Dual PyQt5/PyQt6 compatibility
try:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
        QLabel, QComboBox, QPushButton, QProgressBar, QSplitter,
        QTabWidget, QWidget, QLineEdit, QFileDialog, QScrollArea, QCheckBox
    )
    from PyQt6.QtCore import QThread, pyqtSignal, Qt
except ImportError:
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
        QLabel, QComboBox, QPushButton, QProgressBar, QSplitter,
        QTabWidget, QWidget, QLineEdit, QFileDialog, QScrollArea, QCheckBox
    )
    from PyQt5.QtCore import QThread, pyqtSignal, Qt

# Premium iOS Theme Stylesheets (Segmented Control style tabs, pill buttons, cream & glass finishes)
QSS_LIGHT_CREAM = """
QDialog {
    background-color: #f7f5f0;
    color: #2D221E;
}
QTabWidget::pane {
    border: 1px solid rgba(140, 120, 83, 0.15);
    background-color: #FAF8F5;
    border-radius: 16px;
}
QTabBar {
    background-color: #EFECE6;
    border-radius: 10px;
    padding: 3px;
}
QTabBar::tab {
    background-color: transparent;
    color: #736d64;
    border: none;
    padding: 8px 18px;
    border-radius: 8px;
    font-weight: bold;
    font-size: 11px;
    text-transform: uppercase;
    margin-right: 4px;
}
QTabBar::tab:selected {
    background-color: #FAF8F5;
    color: #8c7853;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}
QLabel {
    color: #8c7853;
    font-size: 11px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
QTextEdit, QLineEdit {
    background-color: #ffffff;
    color: #2D221E;
    border: 1px solid rgba(140, 120, 83, 0.2);
    border-radius: 10px;
    font-size: 13px;
    padding: 8px;
}
QTextEdit:focus, QLineEdit:focus {
    border: 1.5px solid #8c7853;
}
QComboBox {
    background-color: #ffffff;
    color: #2D221E;
    border: 1px solid rgba(140, 120, 83, 0.2);
    border-radius: 10px;
    padding: 8px 14px;
    font-size: 12px;
}
QComboBox:focus {
    border: 1.5px solid #8c7853;
}
QPushButton {
    background-color: #8c7853;
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #bfa67a;
}
QPushButton:disabled {
    background-color: #e6e4dc;
    color: #a6a49c;
}
QProgressBar {
    border: 1px solid rgba(140, 120, 83, 0.15);
    border-radius: 10px;
    text-align: center;
    background-color: #ffffff;
    color: #2D221E;
}
QProgressBar::chunk {
    background-color: #8c7853;
    border-radius: 9px;
}
QCheckBox {
    spacing: 6px;
    font-size: 12px;
    color: #2D221E;
}
QScrollArea {
    border: none;
    background: transparent;
}
"""

QSS_DARK_GLASS = """
QDialog {
    background-color: #0b0b0e;
    color: #ffffff;
}
QTabWidget::pane {
    border: 1px solid rgba(197, 168, 128, 0.15);
    background-color: rgba(18, 18, 22, 0.7);
    border-radius: 16px;
}
QTabBar {
    background-color: #16161a;
    border-radius: 10px;
    padding: 3px;
}
QTabBar::tab {
    background-color: transparent;
    color: #888884;
    border: none;
    padding: 8px 18px;
    border-radius: 8px;
    font-weight: bold;
    font-size: 11px;
    text-transform: uppercase;
    margin-right: 4px;
}
QTabBar::tab:selected {
    background-color: rgba(18, 18, 22, 0.7);
    color: #c5a880;
    box-shadow: 0 2px 6px rgba(0,0,0,0.3);
}
QLabel {
    color: #c5a880;
    font-size: 11px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
QTextEdit, QLineEdit {
    background-color: #17171c;
    color: #ffffff;
    border: 1px solid rgba(197, 168, 128, 0.2);
    border-radius: 10px;
    font-size: 13px;
    padding: 8px;
}
QTextEdit:focus, QLineEdit:focus {
    border: 1.5px solid #c5a880;
}
QComboBox {
    background-color: #17171c;
    color: #ffffff;
    border: 1px solid rgba(197, 168, 128, 0.2);
    border-radius: 10px;
    padding: 8px 14px;
    font-size: 12px;
}
QComboBox:focus {
    border: 1.5px solid #c5a880;
}
QPushButton {
    background-color: #c5a880;
    color: #0b0b0e;
    border: none;
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #e5d3b3;
}
QPushButton:disabled {
    background-color: #242428;
    color: #646468;
}
QProgressBar {
    border: 1px solid rgba(197, 168, 128, 0.15);
    border-radius: 10px;
    text-align: center;
    background-color: #17171c;
    color: #ffffff;
}
QProgressBar::chunk {
    background-color: #c5a880;
    border-radius: 9px;
}
QCheckBox {
    spacing: 6px;
    font-size: 12px;
    color: #ffffff;
}
QScrollArea {
    border: none;
    background: transparent;
}
"""

IMAGE_PRESETS = {
    "Minimalist Coffee Shop": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?q=80&w=600&auto=format&fit=crop",
    "Midnight Neon": "https://images.unsplash.com/photo-1519681393784-d120267933ba?q=80&w=600&auto=format&fit=crop",
    "Sakura Blossom": "https://images.unsplash.com/photo-1522441815192-d9f04eb0615c?q=80&w=600&auto=format&fit=crop",
    "Nordic Slate": "https://images.unsplash.com/photo-1497366216548-37526070297c?q=80&w=600&auto=format&fit=crop"
}

# The HTML page template loaded inside the AnkiWebView interactive Mind Map canvas
MIND_MAP_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
:root {
    --bg-color: #FAF8F5;
    --text-color: #2D221E;
    --accent-color: #8c7853;
    --card-bg: rgba(255, 255, 255, 0.9);
    --card-border: rgba(140, 120, 83, 0.15);
    --card-shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
    --connector-color: #8c7853;
    --btn-hover: #bfa67a;
    --input-focus: #8c7853;
}

body.dark-theme {
    --bg-color: #0b0b0d;
    --text-color: #ffffff;
    --accent-color: #c5a880;
    --card-bg: rgba(24, 24, 28, 0.8);
    --card-border: rgba(197, 168, 128, 0.25);
    --card-shadow: 0 4px 18px rgba(0, 0, 0, 0.3);
    --connector-color: #c5a880;
    --btn-hover: #e5d3b3;
    --input-focus: #c5a880;
}

body {
    background-color: var(--bg-color);
    color: var(--text-color);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    margin: 0;
    padding: 0;
    overflow: hidden;
    width: 100vw;
    height: 100vh;
    user-select: none;
}

#mindmap-container {
    width: 100%;
    height: 100%;
    overflow: auto;
    position: relative;
    box-sizing: border-box;
    cursor: grab;
    padding: 60px;
}

#connectors {
    position: absolute;
    top: 0;
    left: 0;
    pointer-events: none;
    z-index: 1;
}

#mindmap-tree {
    position: relative;
    z-index: 2;
    display: inline-flex;
    align-items: center;
}

.tree-item {
    display: flex;
    flex-direction: row;
    align-items: center;
    position: relative;
}

.node-children {
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding-left: 60px;
    gap: 20px;
}

.node-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    padding: 14px;
    width: 220px;
    min-height: 100px;
    box-shadow: var(--card-shadow);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
    position: relative;
    box-sizing: border-box;
}

.node-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}

body.dark-theme .node-card:hover {
    box-shadow: 0 8px 24px rgba(0,0,0,0.5);
}

.node-card.is-occluded {
    border: 2px dashed var(--accent-color);
    background: repeating-linear-gradient(
      45deg,
      rgba(197, 168, 128, 0.04),
      rgba(197, 168, 128, 0.04) 10px,
      rgba(197, 168, 128, 0.08) 10px,
      rgba(197, 168, 128, 0.08) 20px
    );
}

.card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    position: relative;
}

.node-check {
    appearance: none;
    -webkit-appearance: none;
    width: 16px;
    height: 16px;
    border: 1.5px solid var(--accent-color);
    border-radius: 4px;
    outline: none;
    cursor: pointer;
    position: relative;
    background: transparent;
    transition: background 0.2s;
}

.node-check:checked {
    background: var(--accent-color);
}

.node-check:checked::after {
    content: "✓";
    position: absolute;
    top: -2px;
    left: 2px;
    color: var(--bg-color);
    font-size: 11px;
    font-weight: bold;
}

.node-title {
    background: transparent;
    border: none;
    border-bottom: 1px dashed transparent;
    color: var(--text-color);
    font-weight: bold;
    font-size: 13px;
    width: 100%;
    outline: none;
    padding: 2px 0;
    transition: border-color 0.2s;
}

.node-title:focus {
    border-bottom-color: var(--input-focus);
}

.card-body {
    width: 100%;
}

.node-details {
    background: transparent;
    border: none;
    color: var(--text-color);
    opacity: 0.8;
    font-size: 11px;
    width: 100%;
    min-height: 40px;
    resize: none;
    outline: none;
    line-height: 1.4;
    padding: 0;
    overflow: hidden;
    font-family: inherit;
}

.card-actions {
    display: none;
    position: absolute;
    top: -30px;
    right: 0;
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 6px;
    padding: 2px;
    gap: 2px;
    z-index: 10;
    box-shadow: var(--card-shadow);
}

.node-card:hover .card-actions {
    display: flex;
}

.btn-action {
    background: transparent;
    border: none;
    cursor: pointer;
    font-size: 11px;
    color: var(--text-color);
    width: 20px;
    height: 20px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.2s;
}

.btn-action:hover {
    background: rgba(0, 0, 0, 0.05);
}

body.dark-theme .btn-action:hover {
    background: rgba(255, 255, 255, 0.08);
}

.btn-delete:hover {
    background: #ef4444 !important;
    color: white;
}

.btn-add-child {
    position: absolute;
    right: -10px;
    top: 50%;
    transform: translateY(-50%);
    background: var(--accent-color);
    color: var(--bg-color);
    border: none;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: 12px;
    font-weight: bold;
    z-index: 5;
    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    opacity: 0;
    transition: opacity 0.2s, transform 0.2s;
}

.node-card:hover .btn-add-child {
    opacity: 1;
}

.btn-add-child:hover {
    transform: translateY(-50%) scale(1.1);
}
</style>
</head>
<body>
<div id="mindmap-container">
    <svg id="connectors"></svg>
    <div id="mindmap-tree"></div>
</div>
<script>
let mindmap = null;

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function findNode(node, id) {
    if (node.id === id) return node;
    if (node.children) {
        for (let child of node.children) {
            let found = findNode(child, id);
            if (found) return found;
        }
    }
    return null;
}

function findParent(node, id) {
    if (node.children) {
        for (let child of node.children) {
            if (child.id === id) return node;
            let parent = findParent(child, id);
            if (parent) return parent;
        }
    }
    return null;
}

function setMindMap(data, isDark) {
    if (isDark) {
        document.body.classList.add('dark-theme');
    } else {
        document.body.classList.remove('dark-theme');
    }
    mindmap = data;
    render();
}

function renderNode(node, isRoot = false) {
    let occludedClass = node.occluded ? "is-occluded" : "";
    let checkedAttr = node.checked ? "checked" : "";
    
    let deleteButton = isRoot ? '' : `<button class="btn-action btn-delete" title="Delete Node" onclick="deleteNode('${node.id}', event)">✕</button>`;
    
    let html = `
    <div class="tree-item" id="item-${node.id}">
        <div class="node-card ${occludedClass}" data-id="${node.id}" id="card-${node.id}">
            <div class="card-header">
                <input type="checkbox" class="node-check" ${checkedAttr} onchange="toggleCheck('${node.id}', this.checked, event)" />
                <input type="text" class="node-title" value="${escapeHtml(node.title)}" oninput="updateTitle('${node.id}', this.value)" placeholder="Subtopic Title" />
                <div class="card-actions">
                    <button class="btn-action" title="Toggle Occlusion" onclick="toggleOcclude('${node.id}', event)">👁</button>
                    ${deleteButton}
                </div>
            </div>
            <div class="card-body">
                <textarea class="node-details" oninput="updateDetails('${node.id}', this.value)" placeholder="Core definitions or key terms...">${escapeHtml(node.details)}</textarea>
            </div>
            <button class="btn-add-child" title="Add Subtopic" onclick="addChild('${node.id}', event)">＋</button>
        </div>
    `;
    
    if (node.children && node.children.length > 0) {
        html += `<div class="node-children">`;
        node.children.forEach(child => {
            html += renderNode(child);
        });
        html += `</div>`;
    } else {
        html += `<div class="node-children"></div>`;
    }
    
    html += `</div>`;
    return html;
}

function render() {
    const rootEl = document.getElementById('mindmap-tree');
    if (!mindmap) {
        rootEl.innerHTML = '';
        return;
    }
    rootEl.innerHTML = renderNode(mindmap, true);
    autoResizeTextareas();
    setTimeout(() => {
        drawConnectors();
    }, 50);
}

function autoResizeTextareas() {
    document.querySelectorAll('.node-details').forEach(ta => {
        ta.style.height = 'auto';
        ta.style.height = ta.scrollHeight + 'px';
    });
}

function updateTitle(id, val) {
    let node = findNode(mindmap, id);
    if (node) {
        node.title = val;
        syncToPython();
    }
}

function updateDetails(id, val) {
    let node = findNode(mindmap, id);
    if (node) {
        node.details = val;
        syncToPython();
        drawConnectors();
    }
}

function toggleCheck(id, val, e) {
    let node = findNode(mindmap, id);
    if (node) {
        node.checked = val;
        syncToPython();
    }
}

function toggleOcclude(id, e) {
    if (e) e.stopPropagation();
    let node = findNode(mindmap, id);
    if (node) {
        node.occluded = !node.occluded;
        const card = document.getElementById(`card-${id}`);
        if (card) {
            if (node.occluded) card.classList.add('is-occluded');
            else card.classList.remove('is-occluded');
        }
        syncToPython();
    }
}

function addChild(parentId, e) {
    if (e) e.stopPropagation();
    let parent = findNode(mindmap, parentId);
    if (parent) {
        if (!parent.children) parent.children = [];
        let newId = "node_" + Math.random().toString(36).substr(2, 9);
        parent.children.push({
            id: newId,
            title: "New Branch",
            details: "Detail notes",
            checked: true,
            occluded: false,
            children: []
        });
        render();
        syncToPython();
    }
}

function deleteNode(id, e) {
    if (e) e.stopPropagation();
    let parent = findParent(mindmap, id);
    if (parent) {
        parent.children = parent.children.filter(c => c.id !== id);
        render();
        syncToPython();
    }
}

function syncToPython() {
    if (typeof pycmd !== 'undefined') {
        pycmd("sync:" + JSON.stringify(mindmap));
    }
}

function drawConnectors() {
    const svg = document.getElementById('connectors');
    if (!svg) return;
    svg.innerHTML = '';
    const container = document.getElementById('mindmap-container');
    const containerRect = container.getBoundingClientRect();
    
    svg.style.width = container.scrollWidth + 'px';
    svg.style.height = container.scrollHeight + 'px';
    
    function drawLines(node) {
        const parentCard = document.getElementById(`card-${node.id}`);
        if (parentCard && node.children) {
            const r1 = parentCard.getBoundingClientRect();
            const x1 = r1.right - containerRect.left + container.scrollLeft;
            const y1 = r1.top + r1.height / 2 - containerRect.top + container.scrollTop;
            
            node.children.forEach(child => {
                const childCard = document.getElementById(`card-${child.id}`);
                if (childCard) {
                    const r2 = childCard.getBoundingClientRect();
                    const x2 = r2.left - containerRect.left + container.scrollLeft;
                    const y2 = r2.top + r2.height / 2 - containerRect.top + container.scrollTop;
                    
                    const dx = Math.max(40, Math.abs(x2 - x1) * 0.5);
                    
                    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                    path.setAttribute('d', `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`);
                    path.setAttribute('stroke', getComputedStyle(document.documentElement).getPropertyValue('--connector-color') || '#c5a880');
                    path.setAttribute('stroke-width', '2');
                    path.setAttribute('fill', 'none');
                    path.setAttribute('opacity', '0.6');
                    svg.appendChild(path);
                }
                drawLines(child);
            });
        }
    }
    if (mindmap) {
        drawLines(mindmap);
    }
}

// Mouse-drag panning logic
let isPanning = false;
let startX, startY, scrollLeft, scrollTop;
const container = document.getElementById('mindmap-container');

container.addEventListener('mousedown', (e) => {
    if (e.target === container || e.target.id === 'connectors' || e.target.classList.contains('node-children') || e.target.classList.contains('tree-item')) {
        isPanning = true;
        startX = e.pageX - container.offsetLeft;
        startY = e.pageY - container.offsetTop;
        scrollLeft = container.scrollLeft;
        scrollTop = container.scrollTop;
        container.style.cursor = 'grabbing';
    }
});

container.addEventListener('mouseleave', () => {
    isPanning = false;
    container.style.cursor = 'default';
});

container.addEventListener('mouseup', () => {
    isPanning = false;
    container.style.cursor = 'default';
});

container.addEventListener('mousemove', (e) => {
    if (!isPanning) return;
    e.preventDefault();
    const x = e.pageX - container.offsetLeft;
    const y = e.pageY - container.offsetTop;
    const walkX = (x - startX) * 1.5;
    const walkY = (y - startY) * 1.5;
    container.scrollLeft = scrollLeft - walkX;
    container.scrollTop = scrollTop - walkY;
    drawConnectors();
});

container.addEventListener('scroll', drawConnectors);
window.addEventListener('resize', drawConnectors);
</script>
</body>
</html>
"""

def markdown_to_html(md_text):
    html = md_text
    html = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", html)
    html = re.sub(r"\*(.*?)\*", r"<i>\1</i>", html)
    html = re.sub(r"`(.*?)`", r"<code style='background:rgba(0,0,0,0.1);padding:2px 4px;border-radius:4px;'>\1</code>", html)
    html = re.sub(r"^\s*[-*]\s*(.*?)$", r"<li>\1</li>", html, flags=re.MULTILINE)
    return html

def fallback_layout(text, template_name):
    # Generates a premium styled HTML card dynamically in case the local LLM fails or refuses
    clean_text = text.replace("\n", "<br>")
    if "Question & Answer" in template_name:
        parts = text.split("?")
        if len(parts) >= 2:
            q = parts[0].strip() + "?"
            a = "?".join(parts[1:]).strip()
            return f"<h3>Question</h3><p style='font-size:15px; font-weight:500;'>{q}</p><hr><h3>Answer</h3><p style='font-size:14px; line-height:1.6;'>{a}</p>"
        return f"<h3>Question</h3><p style='font-size:15px;'>{text}</p><hr><h3>Details</h3><p style='font-size:14px; line-height:1.6;'>Refer to card back for answers.</p>"
    elif "Vocabulary" in template_name or "Table" in template_name:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        rows = ""
        for line in lines:
            if ":" in line:
                term, val = line.split(":", 1)
                rows += f"<tr><td style='font-weight:bold; padding:8px; border-bottom:1px solid rgba(0,0,0,0.05);'>{term.strip()}</td><td style='padding:8px; border-bottom:1px solid rgba(0,0,0,0.05);'>{val.strip()}</td></tr>"
            else:
                rows += f"<tr><td colspan='2' style='padding:8px; border-bottom:1px solid rgba(0,0,0,0.05);'>{line}</td></tr>"
        return f"<table style='width:100%; border-collapse:collapse;'>{rows}</table>"
    elif "Code Showcase" in template_name:
        return f"<pre style='background:#1e1e1e; color:#d4d4d4; padding:16px; border-radius:8px; font-family:monospace; overflow-x:auto;'>{text}</pre>"
    else: # Concept Card
        return f"<h3>Concept Overview</h3><hr><p style='font-size:15px; line-height:1.6;'>{clean_text}</p>"

def wrap_with_theme(html_content, theme_name, bg_url, custom_css, font_family, max_width):
    font_stack = "sans-serif"
    if font_family == "Serif (Georgia)":
        font_stack = "'Georgia', 'Times New Roman', serif"
    elif font_family == "Modern (Segoe UI)":
        font_stack = "'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif"
    elif font_family == "Calligraphy (Playfair)":
        font_stack = "'Playfair Display', serif"
    elif font_family == "Retro Monospace (JetBrains Mono)":
        font_stack = "'JetBrains Mono', monospace"
        
    css_rules = ""
    
    # We output clean class selectors inside an embedded <style> block.
    # This allows Anki to adapt card colors dynamically to Night Mode / prefers-color-scheme during reviews.
    if theme_name == "Minimalist Coffee Shop":
        css_rules = f"""
            .aesthetic-card {{
                background: linear-gradient(rgba(253, 251, 247, 0.95), rgba(253, 251, 247, 0.95)), url('{bg_url}');
                background-size: cover;
                background-position: center;
                color: #2D221E;
                border: 1px solid rgba(140, 120, 83, 0.18);
                border-radius: 12px;
                font-family: {font_stack};
                padding: 24px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.05);
                max-width: {max_width};
                margin: 8px auto;
                transition: all 0.3s ease;
            }}
            .nightMode .aesthetic-card,
            @media (prefers-color-scheme: dark) {{
                .aesthetic-card {{
                    background: linear-gradient(rgba(24, 20, 17, 0.94), rgba(24, 20, 17, 0.94)), url('{bg_url}');
                    color: #f3ede2;
                    border: 1px solid rgba(197, 168, 128, 0.25);
                    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                }}
            }}
        """
    elif theme_name == "Midnight Neon":
        css_rules = f"""
            .aesthetic-card {{
                background: linear-gradient(rgba(13, 13, 17, 0.90), rgba(13, 13, 17, 0.90)), url('{bg_url}');
                background-size: cover;
                background-position: center;
                color: #ffffff;
                border: 1px solid rgba(197, 168, 128, 0.3);
                border-radius: 12px;
                font-family: {font_stack};
                padding: 24px;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
                max-width: {max_width};
                margin: 8px auto;
            }}
            .nightMode .aesthetic-card,
            @media (prefers-color-scheme: dark) {{
                .aesthetic-card {{
                    border: 1px solid #c5a880;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
                }}
            }}
        """
    elif theme_name == "Sakura Blossom":
        css_rules = f"""
            .aesthetic-card {{
                background: linear-gradient(rgba(255, 245, 245, 0.96), rgba(255, 245, 245, 0.96)), url('{bg_url}');
                background-size: cover;
                background-position: center;
                color: #3a2a2a;
                border: 1px solid rgba(224, 184, 184, 0.5);
                border-radius: 12px;
                font-family: {font_stack};
                padding: 24px;
                box-shadow: 0 4px 20px rgba(224, 184, 184, 0.2);
                max-width: {max_width};
                margin: 8px auto;
            }}
            .nightMode .aesthetic-card,
            @media (prefers-color-scheme: dark) {{
                .aesthetic-card {{
                    background: linear-gradient(rgba(36, 20, 22, 0.95), rgba(36, 20, 22, 0.95)), url('{bg_url}');
                    color: #ffd4da;
                    border: 1px solid rgba(224, 184, 184, 0.3);
                    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                }}
            }}
        """
    else: # Nordic Slate
        css_rules = f"""
            .aesthetic-card {{
                background: linear-gradient(rgba(240, 244, 248, 0.96), rgba(240, 244, 248, 0.96)), url('{bg_url}');
                background-size: cover;
                background-position: center;
                color: #2c3e50;
                border: 1px solid rgba(180, 190, 200, 0.5);
                border-radius: 12px;
                font-family: {font_stack};
                padding: 24px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.03);
                max-width: {max_width};
                margin: 8px auto;
            }}
            .nightMode .aesthetic-card,
            @media (prefers-color-scheme: dark) {{
                .aesthetic-card {{
                    background: linear-gradient(rgba(15, 23, 42, 0.95), rgba(15, 23, 42, 0.95)), url('{bg_url}');
                    color: #e2e8f0;
                    border: 1px solid rgba(148, 163, 184, 0.3);
                    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                }}
            }}
        """
        
    custom_rule = ""
    if custom_css.strip():
        custom_rule = f"\n.aesthetic-card {{ {custom_css} }}"
        
    return f"""<style>
{css_rules}{custom_rule}
</style>
<div class="aesthetic-card">
{html_content}
</div>"""


def generate_master_mindmap_html(node, root_title, theme, bg_url, custom_css, font_family, max_width, reveal_all=False):
    # Generates the nested interactive tree view to be used directly as a flashcard.
    # Uses inline handlers for Reveal-on-Tap click events to enable full mobile compatibility.
    def render_node_html(n):
        title = n.get("title", "").strip()
        details = n.get("details", "").strip()
        occluded = n.get("occluded", False)
        
        if occluded:
            if reveal_all:
                details_html = f'<span class="mm-occlusion revealed">{details}</span>'
            else:
                details_html = f'<span class="mm-occlusion" onclick="event.stopPropagation(); this.classList.toggle(\'revealed\')">{details}</span>'
        else:
            details_html = details
            
        node_html = f"""
        <div class="mm-node">
            <h4 class="mm-node-title">{title}</h4>
            <p style="margin:0; font-size:12.5px; line-height:1.5;">{details_html}</p>
        </div>
        """
        
        children = n.get("children", [])
        if children:
            children_html = '<div class="mm-tree">'
            for child in children:
                children_html += render_node_html(child)
            children_html += '</div>'
            node_html += children_html
            
        return node_html

    tree_html = ""
    for child in node.get("children", []):
        tree_html += render_node_html(child)
        
    card_body = f"""
    <div class="mm-master-card">
        <h3 style="text-align: center; margin: 0 0 16px 0; font-size: 16px; text-transform: uppercase; letter-spacing: 0.5px;">
            {root_title}
        </h3>
        <div class="mm-tree" style="border-left: 1px dashed #c5a880; margin-left: 4px; padding-left: 8px;">
            {tree_html}
        </div>
    </div>
    """
    
    occlusion_css = """
    .mm-master-card {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        text-align: left;
    }
    .mm-tree {
        display: flex;
        flex-direction: column;
        gap: 12px;
        margin-top: 8px;
    }
    .mm-node {
        border-radius: 8px;
        padding: 10px;
        margin: 4px 0;
        background: rgba(0, 0, 0, 0.02);
        border: 1px solid rgba(0, 0, 0, 0.06);
    }
    .nightMode .mm-node {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    .mm-node-title {
        margin: 0 0 4px 0;
        font-size: 13.5px;
        font-weight: bold;
    }
    .nightMode .mm-node-title {
        color: #c5a880;
    }
    .mm-occlusion {
        position: relative;
        display: inline-block;
        background: #c5a880 !important;
        color: transparent !important;
        border-radius: 4px;
        padding: 2px 8px;
        cursor: pointer;
        user-select: none;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        min-width: 80px;
        text-align: center;
    }
    .mm-occlusion * {
        color: transparent !important;
    }
    .mm-occlusion.revealed {
        background: transparent !important;
        color: inherit !important;
        box-shadow: none;
    }
    .mm-occlusion.revealed * {
        color: inherit !important;
    }
    .mm-occlusion::after {
        content: "Reveal 👁";
        position: absolute;
        left: 0; top: 0; right: 0; bottom: 0;
        background: #c5a880;
        color: #121216 !important;
        font-size: 10px;
        font-weight: bold;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 4px;
    }
    .mm-occlusion.revealed::after {
        display: none !important;
    }
    """
    
    return wrap_with_theme(card_body, theme, bg_url, custom_css + "\n" + occlusion_css, font_family, max_width)


def normalize_node(node):
    if not isinstance(node, dict):
        return None
    normalized = {
        "id": str(uuid.uuid4())[:8],
        "title": str(node.get("title", "")),
        "details": str(node.get("details", "")),
        "checked": bool(node.get("checked", True)),
        "occluded": bool(node.get("occluded", False)),
        "children": []
    }
    for child in node.get("children", []):
        normalized_child = normalize_node(child)
        if normalized_child:
            normalized["children"].append(normalized_child)
    return normalized


def normalize_mindmap(data, default_title="Core Concept"):
    if isinstance(data, list):
        data = {"nodes": data}
    if not isinstance(data, dict):
        data = {}
    
    root_title = str(data.get("title", default_title)) if data.get("title") else default_title
    root = {
        "id": "root",
        "title": root_title,
        "details": "",
        "checked": True,
        "occluded": False,
        "children": []
    }
    
    nodes = data.get("nodes") or data.get("children") or data.get("branches") or []
    if not isinstance(nodes, list):
        nodes = [nodes]
        
    for node in nodes:
        norm = normalize_node(node)
        if norm:
            root["children"].append(norm)
    return root


def parse_text_to_mindmap_json(text, topic):
    # Regex fallback parser in case the LLM outputs non-valid JSON
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    nodes = []
    for line in lines:
        clean_line = re.sub(r"^[-*#\s\d\.]+", "", line).strip()
        if not clean_line:
            continue
        if ":" in clean_line:
            t, d = clean_line.split(":", 1)
            nodes.append({"title": t.strip(), "details": d.strip()})
        else:
            nodes.append({"title": clean_line, "details": "Branch detail"})
    return {"title": topic, "nodes": nodes}


class LLMWorker(QThread):
    finished = pyqtSignal(str, str)  # Emits (html_result, error_message)

    def __init__(self, text, template, api_url, custom_system_prompt):
        super().__init__()
        self.text = text
        self.template = template
        self.api_url = api_url
        self.custom_system_prompt = custom_system_prompt

    def run(self):
        # Structured system instructions separated from task query to maximize prompt following
        system_content = (
            "You are a strict layout compiler. You MUST structure whatever text is provided into the "
            f"requested template layout ('{self.template}'). Do not evaluate, explain, or apologize. "
            "Even if the text is a single word, incomplete, or a typo, you MUST style and compile it. "
            "Never apologize, never say you cannot structure it, and never add conversational filler. "
            "Output ONLY raw HTML. Do not wrap inside markdown blockquotes."
        )
        
        user_content = f"Structure and layout the following text:\n\n{self.text}"

        # Cloze detection inject if requested
        if "Cloze" in self.template:
            system_content += " CRITICAL: Wrap primary definition keywords in standard Anki Cloze tags, e.g. {{c1::cloze term}}."

        if self.custom_system_prompt:
            # Fallback to custom prompts if configured
            system_content = self.custom_system_prompt.replace("{template}", self.template)

        payload = {
            "model": "Qwen2.5-Coder-7B-Instruct-int4-ov",
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.1
        }

        try:
            req = urllib.request.Request(
                self.api_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=120) as response:
                res_body = json.loads(response.read().decode("utf-8"))
                html = res_body["choices"][0]["message"]["content"].strip()
                
                # Strip markdown code blocks
                if html.startswith("```html"):
                    html = html[7:]
                elif html.startswith("```"):
                    html = html[3:]
                if html.endswith("```"):
                    html = html[:-3]
                html = html.strip()
                
                html = markdown_to_html(html)
                self.finished.emit(html, "")
        except Exception as e:
            self.finished.emit("", str(e))


class MindMapWorker(QThread):
    finished = pyqtSignal(dict, str)  # Emits (mind_map_json, error_message)

    def __init__(self, topic, api_url):
        super().__init__()
        self.topic = topic
        self.api_url = api_url

    def run(self):
        system_prompt = (
            "You are a master educational study planner. You must map out topics as structural trees. "
            "You must return ONLY a JSON object representing the branches and core concepts. "
            "Never apologize, never add explanations, and never output conversational text."
        )
        
        user_prompt = f"""Create a comprehensive study mind map tree for the topic '{self.topic}'.
Return this exact JSON structure:
{{
  "title": "{self.topic}",
  "nodes": [
    {{
      "title": "Subtopic Branch 1",
      "details": "Core definition, explanation or facts about Subtopic 1",
      "children": [
        {{
          "title": "Sub-detail 1.1",
          "details": "More specific notes or clinical details"
        }}
      ]
    }}
  ]
}}

Provide 3-6 core branches, with nesting up to 2-3 levels deep where appropriate.
Topic: {self.topic}"""

        payload = {
            "model": "Qwen2.5-Coder-7B-Instruct-int4-ov",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2
        }

        try:
            req = urllib.request.Request(
                self.api_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=120) as response:
                res_body = json.loads(response.read().decode("utf-8"))
                raw_json = res_body["choices"][0]["message"]["content"].strip()
                
                if raw_json.startswith("```json"):
                    raw_json = raw_json[7:]
                elif raw_json.startswith("```"):
                    raw_json = raw_json[3:]
                if raw_json.endswith("```"):
                    raw_json = raw_json[:-3]
                raw_json = raw_json.strip()
                
                try:
                    data = json.loads(raw_json)
                    self.finished.emit(data, "")
                except Exception:
                    data = parse_text_to_mindmap_json(raw_json, self.topic)
                    self.finished.emit(data, "")
        except Exception as e:
            self.finished.emit({}, str(e))


class BeautifierDialog(QDialog):
    def __init__(self, editor, initial_text):
        super().__init__(editor.parentWindow)
        self.editor = editor
        self.setWindowTitle("Aesthetic Anki AI")
        self.resize(980, 640)
        
        if IS_DARK_THEME:
            self.setStyleSheet(QSS_DARK_GLASS)
        else:
            self.setStyleSheet(QSS_LIGHT_CREAM)
            
        self.worker = None
        self.mm_worker = None
        self.raw_html_result = ""
        self.mindmap_data = None
        
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

        self.tabs = QTabWidget()
        
        # --- TAB 1: WORKSPACE ---
        workspace_tab = QWidget()
        workspace_layout = QVBoxLayout(workspace_tab)
        workspace_layout.setContentsMargins(10, 10, 10, 10)
        workspace_layout.setSpacing(10)

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

        # Right pane (Premium Webview Preview)
        right_widget = QVBoxLayout()
        right_widget.addWidget(QLabel("AI Beautified Preview"))
        self.preview_edit = AnkiWebView(self)
        self.preview_edit.setHtml(
            "<div style='font-family:sans-serif; color:#73736e; text-align:center; padding-top:100px;'>"
            "Generated layout preview will render here...</div>"
        )
        
        right_container = QWidget()
        right_container.setLayout(right_widget)
        right_widget.layout().addWidget(self.preview_edit)
        splitter.addWidget(right_container)
        
        splitter.setSizes([400, 540])
        workspace_layout.addWidget(splitter)
        self.tabs.addTab(workspace_tab, "Beautifier Workspace")

        # --- TAB 2: AI MIND MAP GENERATOR ---
        mindmap_tab = QWidget()
        mindmap_layout = QVBoxLayout(mindmap_tab)
        mindmap_layout.setContentsMargins(10, 10, 10, 10)
        mindmap_layout.setSpacing(10)

        mm_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left control sidebar
        sidebar = QWidget()
        sidebar.setMaximumWidth(280)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(5, 5, 5, 5)
        sidebar_layout.setSpacing(10)
        
        sidebar_layout.addWidget(QLabel("Concept Topic:"))
        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("e.g. Mitosis, Cardiovascular pharmacology, Neural Networks...")
        sidebar_layout.addWidget(self.topic_input)
        
        self.gen_mm_btn = QPushButton("Generate Mind Map 🧠")
        self.gen_mm_btn.clicked.connect(self.start_mind_map_generation)
        sidebar_layout.addWidget(self.gen_mm_btn)
        
        sidebar_layout.addSpacing(15)
        sidebar_layout.addWidget(QLabel("Card Options:"))
        
        self.gen_individual_chk = QCheckBox("Generate Individual Cards")
        self.gen_individual_chk.setChecked(True)
        sidebar_layout.addWidget(self.gen_individual_chk)
        
        self.gen_master_chk = QCheckBox("Generate Master Card")
        self.gen_master_chk.setChecked(True)
        sidebar_layout.addWidget(self.gen_master_chk)
        
        sidebar_layout.addStretch()
        
        self.batch_gen_btn = QPushButton("Batch Generate Cards ⚡")
        self.batch_gen_btn.setStyleSheet("background-color: #8c7853; color: white;" if not IS_DARK_THEME else "background-color: #c5a880; color: black;")
        self.batch_gen_btn.setEnabled(False)
        self.batch_gen_btn.clicked.connect(self.batch_generate_notes)
        sidebar_layout.addWidget(self.batch_gen_btn)
        
        mm_splitter.addWidget(sidebar)
        
        # Right pane: Interactive SVG visual tree diagram
        self.mm_tree_view = AnkiWebView(self)
        self.mm_tree_view.set_bridge_command(self.on_mindmap_bridge, self)
        self.mm_tree_view.setHtml(MIND_MAP_HTML_TEMPLATE)
        
        mm_splitter.addWidget(self.mm_tree_view)
        mm_splitter.setSizes([260, 700])
        mindmap_layout.addWidget(mm_splitter)

        self.tabs.addTab(mindmap_tab, "AI Mind Map Generator")

        # --- TAB 3: AESTHETICS & SETTINGS ---
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        settings_layout.setContentsMargins(16, 12, 16, 12)
        settings_layout.setSpacing(8)

        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Aesthetic Theme:"))
        self.theme_select = QComboBox()
        self.theme_select.addItems(["Minimalist Coffee Shop", "Midnight Neon", "Sakura Blossom", "Nordic Slate"])
        self.theme_select.setCurrentText(self.config.get("theme", "Minimalist Coffee Shop"))
        self.theme_select.currentTextChanged.connect(self.on_theme_preset_changed)
        theme_row.addWidget(self.theme_select)
        
        theme_row.addWidget(QLabel("Font Preset:"))
        self.font_select = QComboBox()
        self.font_select.addItems(["Serif (Georgia)", "Modern (Segoe UI)", "Calligraphy (Playfair)", "Retro Monospace (JetBrains Mono)"])
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

        bg_row = QVBoxLayout()
        bg_row.addWidget(QLabel("Card Background Image URL (Minimalist/Study):"))
        self.bg_url_edit = QLineEdit()
        self.bg_url_edit.setText(self.config.get("background_image_url", ""))
        self.bg_url_edit.textChanged.connect(self.on_style_field_changed)
        bg_row.addWidget(self.bg_url_edit)
        settings_layout.addLayout(bg_row)

        css_row = QVBoxLayout()
        css_row.addWidget(QLabel("Custom CSS Style Overrides:"))
        self.css_edit = QTextEdit()
        self.css_edit.setMaximumHeight(80)
        self.css_edit.setPlainText(self.config.get("custom_css", ""))
        self.css_edit.setPlaceholderText("e.g. font-size: 15px; border-color: red;")
        self.css_edit.textChanged.connect(self.on_style_field_changed)
        css_row.addWidget(self.css_edit)
        settings_layout.addLayout(css_row)

        prompt_row = QVBoxLayout()
        prompt_row.addWidget(QLabel("AI Prompt Instruction Fine-Tuner:"))
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setMaximumHeight(80)
        self.prompt_edit.setPlainText(self.config.get("custom_system_prompt", ""))
        self.prompt_edit.setPlaceholderText("Define formatting styles or specifications.")
        prompt_row.addWidget(self.prompt_edit)
        settings_layout.addLayout(prompt_row)

        api_row = QHBoxLayout()
        api_row.addWidget(QLabel("LLM API Endpoint:"))
        self.api_url_edit = QLineEdit()
        self.api_url_edit.setText(self.config.get("api_url", "http://127.0.0.1:8082/v1/chat/completions"))
        api_row.addWidget(self.api_url_edit)
        settings_layout.addLayout(api_row)

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
        self.status_label.setStyleSheet("color: #73736e; font-size: 11px; text-transform: none; font-weight: normal;")
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

        refusal_phrases = ["I'm sorry", "sorry, but", "cannot structure", "does not provide", "does not contain", "unable to assist"]
        is_refusal = any(phrase in html for phrase in refusal_phrases)

        if error:
            self.status_label.setText("Failed to connect to local server.")
            showWarning(f"Error querying local server: {error}\nMake sure team-leader/ov_server is active.", self)
        elif is_refusal or not html.strip():
            self.status_label.setText("Local fallback compiler used (refusal or empty output bypassed).")
            self.raw_html_result = fallback_layout(self.input_edit.toPlainText().strip(), self.template_select.currentText())
            self.update_preview_live()
            self.insert_btn.setEnabled(True)
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

    # --- MIND MAP ACTIONS ---
    def start_mind_map_generation(self):
        topic = self.topic_input.text().strip()
        if not topic:
            showWarning("Please enter a concept topic first.", self)
            return

        self.gen_mm_btn.setEnabled(False)
        self.batch_gen_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("AI structuring concept branches...")

        api_url = self.api_url_edit.text().strip()
        self.mm_worker = MindMapWorker(topic, api_url)
        self.mm_worker.finished.connect(self.on_mind_map_finished)
        self.mm_worker.start()

    def on_mind_map_finished(self, data, error):
        self.progress_bar.setVisible(False)
        self.gen_mm_btn.setEnabled(True)

        if error:
            self.status_label.setText("Failed to connect to local server.")
            showWarning(f"Error querying local server: {error}", self)
        else:
            self.status_label.setText("Mind map tree compiled successfully!")
            self.mindmap_data = normalize_mindmap(data, self.topic_input.text().strip())
            
            # Send initial mind map tree to interactive canvas
            is_dark = 1 if IS_DARK_THEME else 0
            js_code = f"setMindMap({json.dumps(self.mindmap_data)}, {is_dark});"
            self.mm_tree_view.eval(js_code)
            self.batch_gen_btn.setEnabled(True)

    def on_mindmap_bridge(self, cmd: str):
        if cmd.startswith("sync:"):
            try:
                json_str = cmd[5:]
                self.mindmap_data = json.loads(json_str)
            except Exception:
                pass

    def batch_generate_notes(self):
        if not self.mindmap_data:
            showWarning("No mind map data loaded.", self)
            return
            
        root_title = self.mindmap_data.get("title", self.topic_input.text().strip() or "Core Concept")
        
        # Collect checkboxes state
        gen_individual = self.gen_individual_chk.isChecked()
        gen_master = self.gen_master_chk.isChecked()
        
        if not gen_individual and not gen_master:
            showWarning("Please select at least one card generation option (Individual or Master).", self)
            return

        # Fetch current deck
        try:
            deck_id = self.editor.deckChooser.selected_deck_id()
        except Exception:
            deck_id = mw.col.decks.active()
            
        model = mw.col.models.by_name("Basic")
        if not model:
            model = mw.col.models.default()

        theme = self.theme_select.currentText()
        bg_url = self.bg_url_edit.text().strip()
        custom_css = self.css_edit.toPlainText().strip()
        font_family = self.font_select.currentText()
        max_width = self.max_width_edit.text().strip()

        count = 0
        
        # 1. Generate Individual Cards
        if gen_individual:
            individual_nodes = []
            def collect_checked(n):
                if n.get("id") != "root" and n.get("checked", True):
                    t = n.get("title", "").strip()
                    d = n.get("details", "").strip()
                    if t and d:
                        individual_nodes.append((t, d))
                for child in n.get("children", []):
                    collect_checked(child)
                    
            collect_checked(self.mindmap_data)
            
            for title, details in individual_nodes:
                note = mw.col.new_note(model)
                front_content = f"<h3>{root_title}</h3><hr><p style='font-size:16px; font-weight:bold;'>{title}</p>"
                back_content = f"<p style='font-size:14px; line-height:1.6;'>{details}</p>"
                
                note.fields[0] = wrap_with_theme(front_content, theme, bg_url, custom_css, font_family, max_width)
                note.fields[1] = wrap_with_theme(back_content, theme, bg_url, custom_css, font_family, max_width)
                
                if hasattr(mw.col, "add_note"):
                    mw.col.add_note(note, deck_id)
                else:
                    note.did = deck_id
                    mw.col.addNote(note)
                count += 1
                
        # 2. Generate Master Mind Map Card (Interactive reveal on tap for mobile / desktop)
        if gen_master:
            master_front = generate_master_mindmap_html(
                self.mindmap_data, root_title, theme, bg_url, custom_css, font_family, max_width, reveal_all=False
            )
            master_back = generate_master_mindmap_html(
                self.mindmap_data, root_title, theme, bg_url, custom_css, font_family, max_width, reveal_all=True
            )
            
            note = mw.col.new_note(model)
            note.fields[0] = master_front
            note.fields[1] = master_back
            
            if hasattr(mw.col, "add_note"):
                mw.col.add_note(note, deck_id)
            else:
                note.did = deck_id
                mw.col.addNote(note)
            count += 1

        showInfo(f"Successfully generated {count} premium study cards directly into your deck!", self)
        self.accept()

    def auto_detect_template(self, text):
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
