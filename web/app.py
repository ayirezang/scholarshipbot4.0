"""
GlobalEdu Bridge — Web UI layer for the terminal scholarship chatbot.
Does not modify main.py or any chatbot logic.
"""

import builtins
import io
import os
import re
import sys
import threading
import time
import uuid
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import main

app = Flask(__name__, static_folder="static")

_sessions = {}
_lock = threading.Lock()


def _strip_markdown(text):
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^\s*>\s+", "", text, flags=re.MULTILINE)
    return text.strip()


def _format_output(raw):
    cleaned = _strip_markdown(raw)
    lines = []
    for line in cleaned.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("🤖"):
            line = line[1:].strip()
        if line.startswith("💬"):
            continue
        lines.append(line)
    return "\n".join(lines)


class ChatSession:
    def __init__(self):
        self._stdout = io.StringIO()
        self._read_pos = 0
        self._pending_input = None
        self._input_event = threading.Event()
        self._response = None
        self._done = False
        self._thread = None

    def _mock_input(self, prompt=""):
        if prompt:
            clean = prompt.strip()
            if clean.startswith("💬"):
                clean = clean[1:].strip()
            if clean.endswith(":"):
                clean = clean[:-1]
            self._stdout.write(clean + "\n")
        self._pending_input = prompt
        self._input_event.clear()
        self._input_event.wait()
        value = self._response or ""
        self._response = None
        self._pending_input = None
        return value

    def _mock_print(self, *args, **kwargs):
        text = " ".join(str(a) for a in args)
        self._stdout.write(text + "\n")

    def _run_chat(self):
        original_input = builtins.input
        original_print = builtins.print
        builtins.input = self._mock_input
        builtins.print = self._mock_print
        try:
            restart = True
            while restart:
                self._stdout = io.StringIO()
                self._read_pos = 0
                restart = main.chat()
        except Exception as exc:
            self._stdout.write(f"\nAn error occurred: {exc}\n")
        finally:
            builtins.input = original_input
            builtins.print = original_print
            self._done = True
            self._input_event.set()

    def start(self):
        self._thread = threading.Thread(target=self._run_chat, daemon=True)
        self._thread.start()

    def discard_pending_output(self):
        with _lock:
            self._read_pos = len(self._stdout.getvalue())

    def get_new_bot_text(self):
        with _lock:
            raw = self._stdout.getvalue()
        new_raw = raw[self._read_pos :]
        self._read_pos = len(raw)
        return _format_output(new_raw)

    def send_message(self, text):
        if self._done:
            return
        self._response = text.strip()
        self._input_event.set()

    def wait_for_response(self, timeout=15.0):
        start_len = len(self._stdout.getvalue())
        deadline = time.time() + timeout
        time.sleep(0.05)
        while time.time() < deadline:
            if self._done:
                time.sleep(0.1)
                return
            current_len = len(self._stdout.getvalue())
            if self._pending_input is not None and current_len > start_len:
                time.sleep(0.08)
                return
            time.sleep(0.05)


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/start", methods=["POST"])
def api_start():
    session_id = str(uuid.uuid4())
    session = ChatSession()
    with _lock:
        _sessions[session_id] = session
    session.start()

    for _ in range(50):
        time.sleep(0.1)
        if session._pending_input is not None:
            session.discard_pending_output()
            return jsonify({"session_id": session_id, "ready": True})

    return jsonify({"session_id": session_id, "ready": True})


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    message = data.get("message", "").strip()

    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400
    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    with _lock:
        session = _sessions.get(session_id)

    if not session:
        return jsonify({"error": "Session not found. Please refresh the page."}), 404

    session.send_message(message)
    session.wait_for_response(timeout=15.0)

    return jsonify({"text": session.get_new_bot_text(), "done": session._done})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
