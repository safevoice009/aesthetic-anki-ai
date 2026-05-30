"""QThread-based async worker for LLM API calls."""

import json
import urllib.request
import urllib.error

from PyQt6.QtCore import QThread, pyqtSignal


class LLMWorker(QThread):
    finished = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, url: str, payload: dict, timeout: int = 60, parent=None):
        super().__init__(parent)
        self._url = url
        self._payload = payload
        self._timeout = timeout

    def run(self):
        try:
            data = json.dumps(self._payload).encode("utf-8")
            req = urllib.request.Request(
                self._url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))

            content = ""
            choices = result.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", "")

            if not content:
                self.error_occurred.emit("Empty response from LLM.")
                return

            self.finished.emit(content)

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            self.error_occurred.emit(f"HTTP {e.code}: {body[:300]}")
        except urllib.error.URLError as e:
            self.error_occurred.emit(f"Connection failed: {e.reason}")
        except json.JSONDecodeError:
            self.error_occurred.emit("Invalid JSON response from LLM.")
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error: {e}")
