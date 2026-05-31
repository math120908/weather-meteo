#!/usr/bin/env python3
"""Generate a demo.cast file for weather-meteo by running live commands."""

import json
import os
import pty
import subprocess
import time

WIDTH = 100
HEIGHT = 35
PROMPT = "$ "


def run_cmd(cmd: str) -> str:
    """Run command in a PTY to preserve ANSI color codes."""
    primary, replica = pty.openpty()
    env = os.environ.copy()
    env["TERM"] = "xterm-256color"
    env["COLUMNS"] = str(WIDTH)
    env["LINES"] = str(HEIGHT)
    env["FORCE_COLOR"] = "1"
    proc = subprocess.Popen(
        cmd,
        shell=True,
        stdout=replica,
        stderr=replica,
        close_fds=True,
        env=env,
    )
    os.close(replica)
    output = b""
    while True:
        try:
            chunk = os.read(primary, 4096)
            if not chunk:
                break
            output += chunk
        except OSError:
            break
    os.close(primary)
    proc.wait()
    return output.decode("utf-8", errors="replace")


class CastWriter:
    def __init__(self, path: str):
        self.path = path
        self.events: list[str] = []
        self.t = 0.0

    def _emit(self, text: str):
        self.events.append(json.dumps([round(self.t, 4), "o", text]))

    def pause(self, secs: float):
        self.t += secs

    def type_text(self, text: str, char_delay: float = 0.065):
        """Simulate typing character by character."""
        import random
        for ch in text:
            self._emit(ch)
            jitter = random.uniform(-0.015, 0.015)
            self.t += max(0.03, char_delay + jitter)

    def newline(self):
        self._emit("\r\n")
        self.t += 0.05

    def show_output(self, text: str):
        """Dump command output all at once."""
        # Replace bare \n with \r\n for terminal display
        text = text.replace("\r\n", "\n").replace("\n", "\r\n")
        self._emit(text)
        self.t += 0.05

    def blank_line(self):
        self._emit("\r\n")
        self.t += 0.05

    def write(self):
        header = {
            "version": 2,
            "width": WIDTH,
            "height": HEIGHT,
            "timestamp": int(time.time()),
            "title": "weather-meteo demo",
            "env": {"TERM": "xterm-256color", "SHELL": "/bin/bash"},
        }
        with open(self.path, "w") as f:
            f.write(json.dumps(header) + "\n")
            for event in self.events:
                f.write(event + "\n")
        print(f"Wrote {self.path} ({len(self.events)} events)")


def main():
    import os
    out = os.path.join(os.path.dirname(__file__), "demo.cast")
    w = CastWriter(out)

    # Brief intro pause
    w.pause(0.5)

    # Intro comment line
    w._emit(PROMPT)
    w.pause(0.3)
    w.type_text("# weather-meteo: CLI weather powered by Open-Meteo", char_delay=0.055)
    w.newline()
    w.pause(1.2)

    # ── Command 1: weather-meteo (current) ───────────────────────────────────
    w._emit(PROMPT)
    w.pause(0.4)
    w.type_text("weather-meteo")
    w.newline()
    w.pause(0.5)

    out1 = run_cmd("weather-meteo")
    w.show_output(out1)
    w.pause(2.5)

    # ── Command 2: weather-meteo week ────────────────────────────────────────
    w._emit(PROMPT)
    w.pause(0.4)
    w.type_text("weather-meteo week")
    w.newline()
    w.pause(0.5)

    out2 = run_cmd("weather-meteo week")
    w.show_output(out2)
    w.pause(2.5)

    # ── Command 3: weather-meteo hourly -H 6 ─────────────────────────────────
    w._emit(PROMPT)
    w.pause(0.4)
    w.type_text("weather-meteo hourly -H 6")
    w.newline()
    w.pause(0.5)

    out3 = run_cmd("weather-meteo hourly -H 6")
    w.show_output(out3)
    w.pause(2.5)

    # ── Command 4: weather-meteo compare sandymount taipei ───────────────────
    w._emit(PROMPT)
    w.pause(0.4)
    w.type_text("weather-meteo compare sandymount taipei")
    w.newline()
    w.pause(0.6)

    out4 = run_cmd("weather-meteo compare sandymount taipei")
    w.show_output(out4)
    w.pause(3.0)

    # Final prompt
    w._emit(PROMPT)
    w.pause(1.0)

    w.write()


if __name__ == "__main__":
    main()
