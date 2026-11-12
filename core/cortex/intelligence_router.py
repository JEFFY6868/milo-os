#!/usr/bin/env python3
"""
Milo Cognitive Core (Cortex) — Hybrid Intelligence Router
Seamless Online/Offline Model Switching Engine
Part of MiloOS. Built for Arch Linux & Hyprland.

Modes:
  - auto: Checks network connectivity (0.1ms probe). Uses Gemini Cloud when online,
          instant zero-delay failover to Milo Cortex Local Daemon when offline.
  - online: Forces Gemini 2.5 Flash Lite cloud model (rich web & programming reasoning).
  - offline: Forces 100% offline Local Cortex resident daemon (Qwen2.5-0.5B operated weights, 0ms network).
"""

import sys
import os
import re
import html
import json
import socket
import time
import subprocess
import urllib.request
import urllib.parse
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, Generator, List

# Path setup
CONFIG_DIR = Path.home() / ".config" / "milo"
MODE_FILE = CONFIG_DIR / "intelligence_mode.txt"
EYES_ENV_PATH = CONFIG_DIR / "eyes.env"

# Ensure venv libraries (google-genai, groq) are reachable
VENV_LIB = Path.home() / ".local" / "share" / "milo" / "venv" / "lib"
if VENV_LIB.exists():
    for d in VENV_LIB.glob("python*"):
        sp = d / "site-packages"
        if sp.exists() and str(sp) not in sys.path:
            sys.path.insert(0, str(sp))

# Local cortex dir
CORTEX_DIR = Path(__file__).resolve().parent
if str(CORTEX_DIR) not in sys.path:
    sys.path.insert(0, str(CORTEX_DIR))

try:
    import milo_memory
except Exception:
    milo_memory = None

def search_web_duckduckgo(query: str, max_results: int = 4) -> List[str]:
    """Execute live, zero-cost web search via DuckDuckGo and return top factual snippets."""
    if not query or not query.strip():
        return []
    try:
        url = "https://html.duckduckgo.com/html/"
        data = urllib.parse.urlencode({"q": query.strip()}).encode()
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', content, re.DOTALL)
            results = []
            for s in snippets[:max_results]:
                clean = html.unescape(re.sub(r'<[^>]+>', '', s).strip())
                if clean and len(clean) > 20:
                    results.append(clean)
            return results
    except Exception as e:
        sys.stderr.write(f"Web search error: {e}\n")
        return []


def extract_urls(text: str) -> List[str]:
    """Find all http/https URLs or bare github.com links in text."""
    pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+|(?:\bgithub\.com/[^\s<>"]+)'
    matches = re.findall(pattern, text)
    clean = []
    for m in matches:
        if not m.startswith("http://") and not m.startswith("https://"):
            clean.append("https://" + m)
        else:
            clean.append(m)
    return clean


def fetch_web_content(url: str, max_chars: int = 4000) -> Optional[str]:
    """Fetch URL and extract clean text/markdown with specialized GitHub handling."""
    if not url.startswith("http"):
        url = "https://" + url

    try:
        parsed = urllib.parse.urlparse(url)
        # 1. Specialized GitHub URL Handling
        if "github.com" in parsed.netloc:
            parts = [p for p in parsed.path.strip("/").split("/") if p]
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]
                # Try fetching raw README directly
                for branch in ["main", "master"]:
                    for readme in ["README.md", "readme.md", "README.rst", "README"]:
                        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{readme}"
                        try:
                            req = urllib.request.Request(raw_url, headers={"User-Agent": "MiloOS/1.0"})
                            with urllib.request.urlopen(req, timeout=3.5) as resp:
                                if resp.status == 200:
                                    text = resp.read().decode("utf-8", errors="replace")
                                    return f"[Live GitHub Repo Inspection: {owner}/{repo} (README)]:\n{text[:max_chars]}"
                        except Exception:
                            pass
            elif len(parts) == 1:
                # GitHub User or Organization profile
                org = parts[0]
                api_urls = [
                    f"https://api.github.com/users/{org}/repos?per_page=10&sort=updated",
                    f"https://api.github.com/orgs/{org}/repos?per_page=10&sort=updated"
                ]
                for api_url in api_urls:
                    try:
                        req = urllib.request.Request(api_url, headers={
                            "User-Agent": "MiloOS/1.0",
                            "Accept": "application/vnd.github.v3+json"
                        })
                        with urllib.request.urlopen(req, timeout=3.5) as resp:
                            if resp.status == 200:
                                data = json.loads(resp.read().decode("utf-8"))
                                if isinstance(data, list) and data:
                                    repo_summaries = []
                                    for r in data[:8]:
                                        desc = r.get("description") or "No description provided"
                                        repo_summaries.append(f"- **{r.get('name')}**: {desc} (⭐ {r.get('stargazers_count', 0)}, Language: {r.get('language') or 'N/A'})")
                                    return f"[Live GitHub Profile/Organization Inspection: {org}]:\nRepositories:\n" + "\n".join(repo_summaries)
                    except Exception:
                        pass

        # 2. General Web Page Fetching
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        })
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            raw = resp.read()
            text = raw.decode("utf-8", errors="replace")
            # Strip scripts, styles, and tags
            clean = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
            clean = re.sub(r'<style.*?</style>', '', clean, flags=re.DOTALL | re.IGNORECASE)
            clean = re.sub(r'<[^>]+>', ' ', clean)
            clean = re.sub(r'\s+', ' ', clean).strip()
            return f"[Live Web Content from {url}]:\n{clean[:max_chars]}"
    except Exception as e:
        sys.stderr.write(f"Web fetch error for {url}: {e}\n")
        return None

def get_cortex_socket() -> Optional[Path]:
    """Find the first active, responsive Cortex socket."""
    candidates = []
    if os.environ.get("XDG_RUNTIME_DIR"):
        candidates.append(Path(os.environ["XDG_RUNTIME_DIR"]) / "milo-cortex.sock")
    candidates.append(Path(f"/run/user/{os.getuid()}/milo-cortex.sock"))
    candidates.append(Path(f"/tmp/milo-cortex-{os.getuid()}.sock"))
    candidates.append(Path("/tmp/milo-cortex-1000.sock"))

    for sock in candidates:
        if sock.exists():
            try:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.settimeout(0.3)
                s.connect(str(sock))
                s.sendall(b'{"action":"ping"}\n')
                data = s.recv(256)
                s.close()
                if b"pong" in data:
                    return sock
            except Exception:
                pass
    return None

SOCKET_PATH = get_cortex_socket() or Path(f"/run/user/{os.getuid()}/milo-cortex.sock")


def get_mode() -> str:
    """Get current intelligence mode ('auto', 'online', or 'offline')."""
    if MODE_FILE.exists():
        try:
            val = MODE_FILE.read_text(encoding="utf-8").strip().lower()
            if val in ("auto", "online", "offline"):
                return val
        except Exception:
            pass
    return "auto"


def set_mode(mode: str) -> str:
    """Set intelligence mode and persist to disk."""
    mode = mode.strip().lower()
    if mode not in ("auto", "online", "offline"):
        mode = "auto"
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    MODE_FILE.write_text(mode + "\n", encoding="utf-8")
    return mode


def toggle_mode() -> str:
    """Cycle mode: auto -> online -> offline -> auto."""
    current = get_mode()
    cycle = {"auto": "online", "online": "offline", "offline": "auto"}
    new_mode = cycle.get(current, "auto")
    set_mode(new_mode)
    return new_mode


def is_online(timeout: float = 0.5) -> bool:
    """Sub-millisecond network reachability probe without DNS overhead."""
    for host in [("1.1.1.1", 53), ("8.8.8.8", 53), ("1.0.0.1", 53)]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(timeout)
            s.connect(host)
            s.close()
            return True
        except Exception:
            continue
    return False


def is_daemon_warm() -> bool:
    """Check if the resident Cortex daemon is responsive."""
    return get_cortex_socket() is not None


def get_status() -> Dict[str, Any]:
    """Retrieve full live status for wallpaper HUD and Omarchy status bar."""
    mode = get_mode()
    online = is_online()
    daemon_warm = is_daemon_warm()

    if mode == "offline":
        active_backend = "cortex_local"
        label = "⚡ OFFLINE (Cortex 0.5B)"
        color = "#ffaa00"
        desc = "100% Offline Local Model (0ms network)"
    elif mode == "online":
        active_backend = "gemini_cloud"
        label = "🌐 ONLINE (Gemini Cloud)"
        color = "#00ffcc" if online else "#ff0838"
        desc = "Gemini 2.5 Flash Lite Cloud" if online else "Online forced but disconnected!"
    else:  # auto
        if online:
            active_backend = "gemini_cloud"
            label = "🔄 AUTO (🌐 Gemini Cloud)"
            color = "#00ffcc"
            desc = "Auto-routing: Connected to Gemini Cloud"
        else:
            active_backend = "cortex_local"
            label = "🔄 AUTO (⚡ Cortex Offline)"
            color = "#ffaa00"
            desc = "Auto-routing: Offline failover to Local Model"

    return {
        "mode": mode,
        "is_online": online,
        "active_backend": active_backend,
        "daemon_warm": daemon_warm,
        "label": label,
        "color": color,
        "description": desc
    }


def query_cortex_daemon(prompt: str, max_tokens: int = 180) -> Optional[str]:
    """Query local resident daemon over UNIX domain socket with fast timeout."""
    sock_path = get_cortex_socket()
    if not sock_path:
        return None
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(4.0)
        s.connect(str(sock_path))
        req = {
            "action": "synthesize",
            "query": prompt,
            "context_facts": "",
            "max_tokens": max_tokens,
            "temperature": 0.3
        }
        s.sendall((json.dumps(req) + "\n").encode("utf-8"))
        chunks = []
        buffer = ""
        while True:
            data = s.recv(1024)
            if not data:
                break
            buffer += data.decode("utf-8")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                resp = json.loads(line)
                if "chunk" in resp:
                    chunks.append(resp["chunk"])
                elif resp.get("done"):
                    s.close()
                    return "".join(chunks).strip()
                elif "error" in resp:
                    s.close()
                    return None
        s.close()
        return "".join(chunks).strip() if chunks else None
    except Exception:
        return None


def query_gemini_cloud(prompt: str, timeout: float = 6.0) -> Optional[str]:
    """Query Gemini Cloud via Google GenAI SDK with strict timeout."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # Check keys.env, eyes.env, and artemis .env
        env_candidates = [
            CONFIG_DIR / "keys.env",
            EYES_ENV_PATH,
            Path.home() / "Projects/artemis/.env"
        ]
        for env_f in env_candidates:
            if env_f.exists():
                try:
                    for line in env_f.read_text().splitlines():
                        line = line.strip()
                        if line.startswith("GEMINI_API_KEY="):
                            api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                            if api_key:
                                break
                except Exception:
                    pass
            if api_key:
                break

    if not api_key:
        return None

    import concurrent.futures
    def _call():
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            if milo_memory:
                system_instruction = milo_memory.build_system_prompt_with_memory()
            else:
                system_instruction = (
                    "You are Milo (J.A.R.V.I.S.), an ambient AI desktop companion and Arch Linux copilot on Hyprland. "
                    "Keep answers concise, precise, engaging, and practical. Output exact terminal syntax when requested."
                )
            resp = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
                config={"system_instruction": system_instruction}
            )
            if resp and resp.text:
                return resp.text.strip()
            return None
        except Exception as e:
            sys.stderr.write(f"Gemini error: {e}\n")
            return None

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_call)
            return future.result(timeout=timeout)
    except Exception as e:
        sys.stderr.write(f"Gemini future timeout/error: {e}\n")
        return None


def query_groq_cloud(prompt: str, timeout: float = 4.0) -> Optional[str]:
    """Query Groq Cloud via Groq SDK with ultra-fast Llama-3.3-70B failover."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        env_f = CONFIG_DIR / "keys.env"
        if env_f.exists():
            try:
                for line in env_f.read_text().splitlines():
                    line = line.strip()
                    if line.startswith("GROQ_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if api_key:
                            break
            except Exception:
                pass
    if not api_key:
        return None

    import concurrent.futures
    def _call():
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            if milo_memory:
                system_instruction = milo_memory.build_system_prompt_with_memory()
            else:
                system_instruction = (
                    "You are Milo (J.A.R.V.I.S.), an ambient AI desktop companion and Arch Linux copilot on Hyprland. "
                    "Keep answers concise, precise, engaging, and practical. Output exact terminal syntax when requested."
                )
            # Fast, high-throughput Groq models
            models = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]
            resp = None
            for mod in models:
                try:
                    resp = client.chat.completions.create(
                        model=mod,
                        messages=[
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=2048,
                        temperature=0.7,
                    )
                    if resp.choices and resp.choices[0].message.content:
                        return resp.choices[0].message.content.strip()
                except Exception as me:
                    sys.stderr.write(f"Groq model {mod} error: {me}\n")
                    continue
            return None
        except Exception as e:
            sys.stderr.write(f"Groq error: {e}\n")
            return None

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_call)
            return future.result(timeout=timeout)
    except Exception as e:
        sys.stderr.write(f"Groq future timeout/error: {e}\n")
        return None


def handle_task_intent(prompt: str) -> Optional[Tuple[str, str]]:
    """Intercept task queries and mutations against ~/.config/omarchy/todos.json."""
    # Never intercept internal agent / meta prompts
    if prompt.startswith("You are Milo") or "system:" in prompt.lower() or len(prompt.split()) > 25:
        return None

    p = prompt.strip().lower()
    todos_path = Path.home() / ".config" / "omarchy" / "todos.json"

    def _read_todos() -> List[Dict[str, Any]]:
        if not todos_path.exists():
            return []
        try:
            data = json.loads(todos_path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def _save_todos(todos: List[Dict[str, Any]]) -> None:
        todos_path.parent.mkdir(parents=True, exist_ok=True)
        todos_path.write_text(json.dumps(todos, indent=2) + "\n", encoding="utf-8")
        try:
            Path("/tmp/milo-scratchpad-trigger").write_text(f"{int(time.time()*1000)} update\n")
        except Exception:
            pass

    # 1. Add task: "add task <X>", "create task <X>", "remind me to <X>", "new task <X>"
    add_match = re.match(r'^(?:milo\s+)?(?:add\s+task|create\s+task|new\s+task|remind\s+me\s+to|add\s+todo)\s*[:\-]?\s*(.+)$', p, re.IGNORECASE)
    if add_match:
        task_text = prompt.strip()[add_match.start(1):].strip().strip('"\'')
        if task_text:
            todos = _read_todos()
            item = {
                "id": int(time.time() * 1000),
                "text": task_text,
                "done": False,
                "created_at": time.strftime("%I:%M %p")
            }
            todos.append(item)
            _save_todos(todos)
            return f"Affirmative, Jeffy. Added '{task_text}' to your Milo Scratchpad.", "Milo Task Copilot"

    # 2. What are the pending tasks / what needs to be done?
    if re.search(r'\b(pending\s+tasks?|what(?:\'?s|\s+is|\s+are)(?:\s+the)?\s+pending(?:\s+tasks?)?|uncompleted\s+tasks?|what\s+needs\s+to\s+be\s+done|unfinished\s+tasks?)\b', p):
        todos = _read_todos()
        pending = [t for t in todos if not t.get("done", False)]
        if not pending:
            return "All tactical missions are completed! No pending tasks on your Milo Scratchpad.", "Milo Task Copilot"
        resp = f"You have {len(pending)} pending task{'s' if len(pending) > 1 else ''}:\n"
        for i, t in enumerate(pending, 1):
            resp += f"• {t['text']}\n"
        return resp.strip(), "Milo Task Copilot"

    # 3. What are the finished / completed tasks?
    if re.search(r'\b(finished\s+tasks?|completed\s+tasks?|what(?:\'?s|\s+is|\s+are)(?:\s+the)?\s+(?:finished|completed)(?:\s+tasks?)?|what\s+did\s+i\s+(?:finish|complete|do))\b', p):
        todos = _read_todos()
        done = [t for t in todos if t.get("done", False)]
        if not done:
            return "No completed tasks yet on your Milo Scratchpad.", "Milo Task Copilot"
        resp = f"You have completed {len(done)} task{'s' if len(done) > 1 else ''}:\n"
        for i, t in enumerate(done, 1):
            resp += f"✔ {t['text']}\n"
        return resp.strip(), "Milo Task Copilot"

    # 4. What are my tasks? / list tasks / summarize tasks / show tasks
    if re.search(r'\b(what\s+are\s+(?:my\s+|the\s+)?tasks?|list\s+tasks?|show\s+tasks?|my\s+tasks?|summarize(?:\s+my)?\s+tasks?|task\s+summary|scratchpad\s+tasks?)\b', p):
        todos = _read_todos()
        if not todos:
            return "Your Milo Scratchpad is currently empty. Ready for new tactical directives.", "Milo Task Copilot"
        done = [t for t in todos if t.get("done", False)]
        pending = [t for t in todos if not t.get("done", False)]
        resp = f"Milo Scratchpad Report: {len(done)}/{len(todos)} completed ({len(pending)} pending).\n"
        if pending:
            resp += "\nPending:\n" + "\n".join(f"• {t['text']}" for t in pending)
        if done:
            resp += "\n\nCompleted:\n" + "\n".join(f"✔ {t['text']}" for t in done)
        return resp.strip(), "Milo Task Copilot"

    # 5. Mark task done: "mark task X as done", "complete task X"
    done_match = re.search(r'\b(?:mark|set)?\s*task\s*(\d+)\s*(?:as\s*)?(?:done|completed|finished)\b', p)
    if done_match:
        idx = int(done_match.group(1))
        todos = _read_todos()
        if 1 <= idx <= len(todos):
            todos[idx - 1]["done"] = True
            _save_todos(todos)
            return f"Marked task #{idx} ('{todos[idx-1]['text']}') as completed.", "Milo Task Copilot"

    return None


def get_calendar_context_summary() -> str:
    """Return compact text summary of today's calendar for LLM context injection."""
    cache = Path.home() / ".local" / "share" / "milo" / "calendar" / "agenda_today.json"
    if not cache.exists():
        return ""
    try:
        events = json.loads(cache.read_text(encoding="utf-8"))
        if not events:
            return "No scheduled events for today. Horizon is clear."
        lines = []
        for e in events:
            status = " [ACTIVE NOW]" if e.get("is_active") else (" [COMPLETED]" if e.get("is_past") else f" [{e.get('status_text', '')}]")
            lines.append(f"• {e.get('event_time')} ({e.get('duration_min')}m): {e.get('title')}{status}")
        return "\n".join(lines)
    except Exception:
        return ""


def handle_calendar_intent(prompt: str) -> Optional[Tuple[str, str]]:
    """Intercept natural language calendar queries & actions to query or manipulate Milo Calendar."""
    if prompt.startswith("You are Milo") or "system:" in prompt.lower() or len(prompt.split()) > 35:
        return None

    p = prompt.strip().lower()
    milo_cal_bin = Path.home() / ".local" / "bin" / "milo-calendar"
    if not milo_cal_bin.exists():
        return None

    # 1. Spoken Daily / Morning Briefing
    if re.search(r'\b(?:give\s+me\s+my\s+|what(?:\'?s|\s+is)\s+my\s+)?(?:daily\s+|morning\s+|calendar\s+)?briefing\b', p) or \
       re.search(r'\bbrief\s+(?:me\s+on\s+)?(?:today|my\s+day|the\s+day)\b', p):
        try:
            res = subprocess.run([str(milo_cal_bin), "briefing"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip(), "Milo Calendar Copilot"
        except Exception:
            pass

    # 2. Next Event Countdown / Query
    if re.search(r'\b(?:what(?:\'?s|\s+is)\s+(?:my\s+|the\s+)?next\s+(?:event|meeting|item|appointment)|when\s+is\s+my\s+next\s+(?:event|meeting|appointment)|next\s+event|upcoming\s+event)\b', p) or \
       p in ["next event", "what's next", "whats next", "upcoming event"]:
        try:
            res = subprocess.run([str(milo_cal_bin), "next"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                clean_out = re.sub(r'\x1b\[[0-9;]*m', '', res.stdout.strip())
                return clean_out, "Milo Calendar Copilot"
        except Exception:
            pass

    # 3. Schedule / Add to Calendar: "schedule X", "add to calendar X", "put on calendar X"
    sched_match = re.match(r'^(?:milo\s+)?(?:schedule|add\s+to\s+calendar|put\s+on\s+(?:my\s+)?calendar|calendar\s+add|book)\s*[:\-]?\s*(.+)$', p, re.IGNORECASE)
    if sched_match:
        sched_text = prompt.strip()[sched_match.start(1):].strip().strip('"\'')
        if sched_text:
            try:
                res = subprocess.run([str(milo_cal_bin), "quick", sched_text], capture_output=True, text=True, timeout=6)
                if res.returncode == 0 and res.stdout.strip():
                    clean_out = re.sub(r'\x1b\[[0-9;]*m', '', res.stdout.strip())
                    return clean_out, "Milo Calendar Copilot"
            except Exception as e:
                return f"Failed to schedule event: {e}", "Milo Calendar Copilot"

    # 4. Today's Agenda / Schedule: "what's on my calendar today", "my agenda", "show calendar"
    if re.search(r'\b(?:what(?:\'?s|\s+is|\s+are)\s+(?:on\s+)?(?:my\s+|the\s+)?(?:calendar|agenda|schedule)(?:\s+today)?|today(?:\'s)?\s+(?:calendar|agenda|schedule|events)|show\s+(?:my\s+)?calendar|check\s+(?:my\s+)?calendar|my\s+schedule\s+today)\b', p):
        try:
            res = subprocess.run([str(milo_cal_bin), "today", "--json"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                events = json.loads(res.stdout.strip())
                if not events:
                    return "No tactical events scheduled for today. Your schedule is completely open, Sir.", "Milo Calendar Copilot"
                resp = f"Here is your agenda for today ({date.today().strftime('%A, %b %d')}):\n"
                for ev in events:
                    t_str = datetime.strptime(ev["event_time"], "%H:%M").strftime("%I:%M %p")
                    dur = f"{ev.get('duration_min', 60)}m"
                    cat = ev.get('category', 'work').upper()
                    status = ev.get('status_text', '')
                    if ev.get("is_active"):
                        icon = "● ACTIVE NOW"
                    elif ev.get("is_past"):
                        icon = "✔ COMPLETED"
                    else:
                        icon = f"⏳ {status}"
                    resp += f"• [{t_str} - {dur}] {ev['title']} ({cat}) · {icon}\n"
                    if ev.get("description"):
                        resp += f"    ↳ {ev['description']}\n"
                return resp.strip(), "Milo Calendar Copilot"
        except Exception as e:
            sys.stderr.write(f"Calendar today intent error: {e}\n")

    # 5. Remove / Delete Event: "delete event X", "remove event X", "cancel event X"
    rm_match = re.search(r'\b(?:delete|remove|cancel)\s+(?:calendar\s+)?event\s*#?\s*(\d+)\b', p)
    if rm_match:
        ev_id = rm_match.group(1)
        try:
            res = subprocess.run([str(milo_cal_bin), "rm", ev_id], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                clean_out = re.sub(r'\x1b\[[0-9;]*m', '', res.stdout.strip())
                return clean_out, "Milo Calendar Copilot"
        except Exception:
            pass

    # 6. Worktime Query or Configuration: "what are my work hours", "set worktime to 9am to 6pm"
    wt_set_match = re.search(r'\b(?:set|change|update)\s+(?:my\s+)?(?:work\s*time|work\s*hours)\s+(?:to\s+)?(.+)\b', p)
    if wt_set_match:
        target_range = wt_set_match.group(1).strip()
        try:
            res = subprocess.run([str(milo_cal_bin), "worktime", "--set", target_range], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                clean_out = re.sub(r'\x1b\[[0-9;]*m', '', res.stdout.strip())
                first_line = clean_out.splitlines()[0] if clean_out else f"Work hours set to {target_range}."
                return first_line, "Milo Calendar Copilot"
        except Exception as e:
            return f"Failed to set worktime: {e}", "Milo Calendar Copilot"

    if re.search(r'\b(?:what(?:\'?s|\s+is|\s+are)\s+(?:my\s+)?(?:work\s*time|work\s*hours)|am\s+i\s+(?:in\s+work\s*hours|on\s+duty|working)|work\s*time\s+status)\b', p):
        try:
            res = subprocess.run([str(milo_cal_bin), "worktime", "--json"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                wt_info = json.loads(res.stdout.strip())
                msg = f"Your daily work hours are {wt_info.get('start')} to {wt_info.get('end')}. Currently: {wt_info.get('status_text')}."
                return msg, "Milo Calendar Copilot"
        except Exception:
            pass

    return None


def handle_music_intent(prompt: str) -> Optional[Tuple[str, str]]:
    """Intercept natural language music control queries & actions to manipulate Milo Music."""
    if prompt.startswith("You are Milo") or "system:" in prompt.lower() or len(prompt.split()) > 20:
        return None

    p = prompt.strip().lower()
    music_bin = Path.home() / ".local" / "bin" / "milo-music"
    if not music_bin.exists():
        return None

    # Play / Resume
    if re.search(r'\b(?:play\s+(?:music|song|soundtrack|audio)|resume\s+(?:music|song|soundtrack|playback)|start\s+music)\b', p) or p in ["play", "play music", "music play"]:
        try:
            res = subprocess.run([str(music_bin), "status"], capture_output=True, text=True, timeout=3)
            out = res.stdout.strip()
            if ":::Paused" in out or ":::Stopped" in out or not out:
                subprocess.run([str(music_bin), "play-pause"], check=False)
            return "Playing Milo Cyber Soundtrack.", "Milo Cyber Soundtrack"
        except Exception:
            return None

    # Pause / Stop
    if re.search(r'\b(?:pause\s+(?:music|song|soundtrack|playback)|stop\s+(?:music|song|soundtrack|playing))\b', p) or p in ["pause", "pause music", "stop music"]:
        try:
            subprocess.run([str(music_bin), "play-pause"], check=False)
            return "Milo Soundtrack paused.", "Milo Cyber Soundtrack"
        except Exception:
            return None

    # Next / Skip
    if re.search(r'\b(?:next\s+(?:song|track|music)|skip\s+(?:this\s+)?(?:song|track)|play\s+next)\b', p) or p in ["next", "skip", "next song", "next track"]:
        try:
            subprocess.run([str(music_bin), "next"], check=False)
            time.sleep(0.3)
            res = subprocess.run([str(music_bin), "status"], capture_output=True, text=True, timeout=3)
            out = res.stdout.strip()
            if ":::" in out:
                parts = out.split(":::")
                return f"Skipped. Now playing {parts[0]} by {parts[1]}.", "Milo Cyber Soundtrack"
            return "Skipped to next track.", "Milo Cyber Soundtrack"
        except Exception:
            return None

    # Previous track
    if re.search(r'\b(?:previous\s+(?:song|track|music)|prev\s+(?:song|track)|play\s+previous|go\s+back\s+(?:a\s+)?song)\b', p) or p in ["prev", "previous", "previous song"]:
        try:
            subprocess.run([str(music_bin), "prev"], check=False)
            time.sleep(0.3)
            res = subprocess.run([str(music_bin), "status"], capture_output=True, text=True, timeout=3)
            out = res.stdout.strip()
            if ":::" in out:
                parts = out.split(":::")
                return f"Playing previous track: {parts[0]} by {parts[1]}.", "Milo Cyber Soundtrack"
            return "Playing previous track.", "Milo Cyber Soundtrack"
        except Exception:
            return None

    # What song is playing / status
    if re.search(r'\b(?:what(?:\'?s|\s+is)\s+(?:this\s+)?(?:song|music|track|playing)|what\s+(?:song|music|track)\s+is\s+(?:this\s+|currently\s+)?playing|what\s+am\s+i\s+listening\s+to|current\s+(?:song|track|music)|music\s+status)\b', p):
        try:
            res = subprocess.run([str(music_bin), "status"], capture_output=True, text=True, timeout=3)
            out = res.stdout.strip()
            if ":::" in out:
                parts = out.split(":::")
                st_word = "Playing" if parts[2] == "Playing" else "Paused"
                return f"{st_word}: '{parts[0]}' by {parts[1]}.", "Milo Cyber Soundtrack"
            return "No soundtrack is currently loaded.", "Milo Cyber Soundtrack"
        except Exception:
            return None

    return None


def handle_camera_intent(prompt: str) -> Optional[Tuple[str, str]]:
    """Intercept conversational requests to inspect user or physical surroundings via webcam."""
    if prompt.startswith("You are Milo") or "system:" in prompt.lower() or len(prompt.split()) > 30:
        return None

    p = prompt.strip().lower()

    # Exact shortcuts
    exact_cmds = {
        "look", "/look", "milo look",
        "see", "/see", "milo see",
        "cam", "/cam", "milo cam",
        "camera", "/camera", "milo camera",
        "posture", "/posture", "check posture",
        "desk", "/desk", "check desk"
    }

    cam_patterns = [
        r'^/?(?:milo\s+)?(?:look|see|cam|camera)(?:\s+.*)?$',
        r'\blook\s+(?:at\s+(?:me|this|my|us)|around|here|in\s+front)\b',
        r'\bcan\s+you\s+see\s*(?:me|this|what|us)?\b',
        r'\bwhat\s+(?:do\s+you\s+see|am\s+i\s+(?:doing|holding|wearing|eating|drinking))\b',
        r'\b(?:take\s+a\s+look|look\s+through\s+(?:the\s+)?camera)\b',
        r'\bcheck\s+(?:my\s+)?(?:posture|ergonomics|desk|workspace|lighting)\b',
        r'\bhow\s+do\s+i\s+look\b',
        r'\b(?:what(?:\'?s|\s+is)\s+(?:in|on)\s+my\s+hand)\b',
        r'\bread\s+(?:this|what\s+i(?:\'m|\s+am)\s+holding)\b',
        r'\b(?:activate|open|turn\s+on)?\s*optical\s*(?:sensor|vision|camera|feed)\b',
    ]

    is_cam = (p in exact_cmds) or any(re.search(pat, p) for pat in cam_patterns)
    if not is_cam:
        return None

    try:
        cmd = ["/home/jeffy/.local/bin/milo-look", "--raw"]
        if "posture" in p or "ergonomics" in p:
            cmd.append("--posture")
        elif "desk" in p or "workspace" in p:
            cmd.append("--desk")
        elif "read" in p:
            cmd.append("--read")
        elif p not in exact_cmds:
            cmd.append(prompt)

        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip(), "Milo Optical Sensor"
    except Exception as e:
        sys.stderr.write(f"Camera intent error: {e}\n")

    return None


def handle_mail_intent(prompt: str) -> Optional[Tuple[str, str]]:
    """Intercept natural language email queries & actions to query Milo Gmail."""
    if prompt.startswith("You are Milo") or "system:" in prompt.lower() or len(prompt.split()) > 35:
        return None

    p = prompt.strip().lower()
    milo_mail_bin = Path.home() / ".local" / "bin" / "milo-mail"
    if not milo_mail_bin.exists():
        return None

    # 0. Anthropic / Claude Priority Sentinel Check & Alert Intent
    if re.search(r'\b(?:alert|notify|tell)\s+me\s+(?:if|when)\s+(?:there\s+is\s+|i\s+get\s+)?(?:a\s+)?(?:mail|email|message)\s+from\s+(?:anthropic|claude)\b', p) or \
       re.search(r'\b(?:did|has)\s+(?:anthropic|claude)\s+(?:email|emailed|sent|replied)\b', p) or \
       re.search(r'\b(?:any|check)\s+(?:mail|email|updates?)\s+from\s+(?:anthropic|claude)\b', p) or \
       p in ["check anthropic", "check claude", "anthropic email", "claude email", "anthropic sentinel"]:
        try:
            res = subprocess.run([str(milo_mail_bin), "sentinel"], capture_output=True, text=True, timeout=12)
            if res.stdout.strip():
                clean_out = re.sub(r'\x1b\[[0-9;]*m', '', res.stdout.strip())
                return clean_out, "Milo Anthropic Sentinel"
        except Exception:
            pass

    # 1. Unread Mail Summary / Briefing
    if re.search(r'\b(?:summarize|brief\s+me\s+on|give\s+me\s+a\s+summary\s+of)\s+(?:my\s+)?(?:unread\s+)?(?:emails?|mail|inbox)\b', p) or \
       re.search(r'\b(?:email|mail)\s+(?:summary|briefing)\b', p):
        try:
            res = subprocess.run([str(milo_mail_bin), "summarize"], capture_output=True, text=True, timeout=18)
            if res.stdout.strip():
                return res.stdout.strip(), "Milo Mail Copilot"
        except Exception:
            pass

    # 2. Check Mail / Any New Emails / Status
    if re.search(r'\b(?:check\s+(?:my\s+)?(?:email|mail|inbox)|any\s+(?:new\s+)?(?:emails?|mail)|what(?:\'?s|\s+is)\s+in\s+my\s+(?:inbox|mail|email)|do\s+i\s+have\s+(?:any\s+)?(?:new\s+)?(?:emails?|mail))\b', p) or \
       p in ["check mail", "check email", "emails", "unread mail", "unread emails", "inbox"]:
        try:
            res = subprocess.run([str(milo_mail_bin), "list"], capture_output=True, text=True, timeout=12)
            if res.stdout.strip():
                clean_out = re.sub(r'\x1b\[[0-9;]*m', '', res.stdout.strip())
                return clean_out, "Milo Mail Copilot"
        except Exception:
            pass

    # 3. Read specific email: "read email #X" or "read email X"
    read_match = re.search(r'\bread\s+(?:email|mail)\s+#?([0-9]+)\b', p)
    if read_match:
        mid = read_match.group(1)
        try:
            res = subprocess.run([str(milo_mail_bin), "read", mid], capture_output=True, text=True, timeout=10)
            if res.stdout.strip():
                clean_out = re.sub(r'\x1b\[[0-9;]*m', '', res.stdout.strip())
                return clean_out, "Milo Mail Copilot"
        except Exception:
            pass

    return None


def handle_pkg_intent(prompt: str) -> Optional[Tuple[str, str]]:
    """Detect and handle package install/remove/update requests."""
    p_lower = prompt.lower().strip()

    is_install = any(k in p_lower for k in [
        "install ", "installing", "reinstall", "setup ", "get ", "download and install"
    ]) or p_lower.startswith("install") or p_lower.startswith("milo install")

    is_remove = any(k in p_lower for k in [
        "uninstall", "remove ", "delete package"
    ]) or p_lower.startswith("uninstall") or p_lower.startswith("remove")

    is_update = any(k in p_lower for k in [
        "update system", "update packages", "upgrade system", "upgrade packages"
    ])

    if not (is_install or is_remove or is_update):
        return None

    milo_pkg_bin = Path.home() / ".local" / "bin" / "milo-pkg"
    if not milo_pkg_bin.exists():
        milo_pkg_bin = Path.home() / "Projects" / "milo-os" / "bin" / "milo-pkg"

    if is_update:
        try:
            subprocess.Popen([
                "foot", "-a", "milo-floating", "-T", "MILO // System Package Upgrade",
                str(milo_pkg_bin), "update"
            ])
            return "📦 **[MILO PACKAGE MANAGER ACTIVE]**\n\n✦ Launching system upgrade console via pacman & AUR...", "Milo Package Copilot"
        except Exception as e:
            return f"Failed to launch package updater: {e}", "Milo Package Copilot"

    target = ""
    if is_remove:
        action = "remove"
        target = re.sub(r'^(?:milo\s+)?(?:uninstall|remove|delete)\s+(?:package\s+)?', '', prompt, flags=re.IGNORECASE).strip()
    else:
        action = "install"
        target = re.sub(r'^(?:milo\s+)?(?:c*an\s+(?:you|u)\s+)?(?:could\s+you\s+)?(?:please\s+|plz\s+)?(?:try\s+)?(?:install|installing|reinstall|setup|get|download\s+and\s+install)\s+(?:again\s+)?(?:for\s+me\s+)?', '', prompt, flags=re.IGNORECASE).strip()
        target = re.sub(r'\s+(?:again|for\s+me|please|plz)$', '', target, flags=re.IGNORECASE).strip()

    # If target is fuzzy or generic, check known target names
    if not target or target in ["it", "this", "app", "application", "again"]:
        for known in ["opencode", "discord", "telegram", "vlc", "steam", "spotify", "gimp", "obs"]:
            if known in p_lower:
                target = known
                break
        if not target or target in ["it", "this", "app", "application", "again"]:
            from datetime import timedelta
            for days_ago in [0, 1]:
                check_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
                for note_path in [
                    Path.home() / "Documents" / "Obsidian" / "Milo" / "Daily" / f"{check_date}.md",
                    Path.home() / "MiloNotes" / "Daily" / f"{check_date}.md"
                ]:
                    if note_path.exists():
                        try:
                            txt = note_path.read_text(encoding="utf-8").lower()
                            for known in ["opencode", "discord", "telegram", "vlc", "steam", "spotify", "gimp", "obs"]:
                                if known in txt:
                                    target = known
                                    break
                        except Exception:
                            pass
                    if target and target not in ["it", "this", "app", "application", "again"]:
                        break
                if target and target not in ["it", "this", "app", "application", "again"]:
                    break

    if not target or target in ["it", "this", "app", "application", "again"]:
        return None

    target = target.strip("'\"`.,!? ")

    try:
        title = f"MILO // {'Install' if action == 'install' else 'Remove'} {target}"
        subprocess.Popen([
            "foot", "-a", "milo-floating", "-T", title,
            str(milo_pkg_bin), action, target
        ])
        verb = "installation" if action == "install" else "removal"
        return f"📦 **[MILO PACKAGE MANAGER ACTIVE]**\n\n✦ Target: `{target}`\n✦ Resolving repository & spawning {verb} console...", "Milo Package Copilot"
    except Exception as e:
        return f"Failed to spawn package manager: {e}", "Milo Package Copilot"


def handle_datetime_intent(prompt: str) -> Optional[Tuple[str, str]]:
    """Instant sub-millisecond ground-truth date, time, and day resolution."""
    p_clean = prompt.lower().strip().rstrip("?.! ")

    # Direct date question patterns
    date_patterns = [
        "whats today date", "what's today date", "whats todays date", "what's today's date",
        "what is today date", "what is today's date", "what is the date today", "what is the date",
        "whats the date", "what's the date", "what date is it", "today date", "today's date",
        "date today", "current date", "what is the current date", "whats date", "what date"
    ]
    is_date = p_clean in date_patterns or (
        "date" in p_clean and any(w in p_clean for w in ["today", "current", "what is", "whats", "what's"])
    )

    # Direct time question patterns
    time_patterns = [
        "whats the time", "what's the time", "what time is it", "what is the time",
        "current time", "time now", "tell me the time", "what time is it now", "whats time",
        "what's time", "what time"
    ]
    is_time = p_clean in time_patterns or (
        "time" in p_clean and any(w in p_clean for w in ["current", "now", "what is", "whats", "what's", "tell me"])
        and "calendar" not in p_clean and "schedule" not in p_clean and "spend" not in p_clean
    )

    # Day of week patterns
    day_patterns = [
        "what day is it", "what day is today", "what day is it today", "which day is today",
        "which day is it", "day of the week", "whats the day", "what's the day"
    ]
    is_day = p_clean in day_patterns

    if not (is_date or is_time or is_day):
        return None

    now = datetime.now()
    day_name = now.strftime("%A")
    date_formatted = now.strftime("%B %d, %Y")
    time_formatted = now.strftime("%I:%M %p")

    if is_time and not is_date:
        msg = f"The current time is {time_formatted} ({day_name}, {date_formatted})."
    elif is_day and not is_date and not is_time:
        msg = f"Today is {day_name}, {date_formatted}."
    else:
        msg = f"Today is {day_name}, {date_formatted}. Current time is {time_formatted}."

    return msg, "Milo Chronometer"


def execute_hybrid_query(prompt: str) -> Tuple[str, str]:
    """
    Execute query using current intelligence mode and automatic failover.
    Returns: (response_text, provider_name)
    """
    # 0. Check real-time date/time chronometer intent first
    dt_res = handle_datetime_intent(prompt)
    if dt_res:
        return dt_res

    # 0.1 Check package manager intent
    pkg_res = handle_pkg_intent(prompt)
    if pkg_res:
        return pkg_res

    # 0.1 Check task-specific intent
    task_res = handle_task_intent(prompt)
    if task_res:
        return task_res

    # 0.1 Check calendar-specific intent
    cal_res = handle_calendar_intent(prompt)
    if cal_res:
        return cal_res

    # 0.2 Check music-specific intent
    music_res = handle_music_intent(prompt)
    if music_res:
        return music_res

    # 0.3 Check mail-specific intent
    mail_res = handle_mail_intent(prompt)
    if mail_res:
        return mail_res

    # 1. Check optical vision intent
    cam_res = handle_camera_intent(prompt)
    if cam_res:
        return cam_res

    # 2. Check explicit memory & recall intent
    if milo_memory:
        mem_res = milo_memory.handle_memory_intent(prompt)
        if mem_res:
            return mem_res

    mode = get_mode()
    online = is_online()

    # Pre-fetch live web/GitHub context or live search if online
    query_prompt = prompt

    # Inject live calendar context if relevant to the conversational query
    lower_prompt = prompt.lower()
    cal_keywords = ["calendar", "schedule", "free", "busy", "meeting", "events", "agenda", "afternoon", "evening", "plans", "tomorrow", "today"]
    if any(k in lower_prompt for k in cal_keywords):
        cal_summary = get_calendar_context_summary()
        if cal_summary:
            query_prompt = f"{query_prompt}\n\n--- [LIVE USER CALENDAR CONTEXT FOR TODAY] ---\n{cal_summary}\n--- [END CALENDAR CONTEXT] ---"
    if online:
        urls = extract_urls(prompt)
        web_contexts = []
        if urls:
            for u in urls[:2]:
                content = fetch_web_content(u)
                if content:
                    web_contexts.append(content)
        else:
            lower_p = prompt.lower().strip()
            # Detect if query needs web searching
            search_intent = (
                lower_p.startswith(("search", "lookup", "look up", "google", "browse", "find out", "who is", "what is", "where is", "when is", "tell me about"))
                or any(kw in lower_p for kw in ["latest", "news", "release", "specs", "price", "llm", "ai model", "update", "today", "yesterday", "versus", "vs", "benchmark"])
                or "?" in prompt
            )
            if search_intent:
                clean_query = re.sub(r"^(?:search(?:\s+for)?|lookup|look\s+up|google|browse|find\s+out(?:\s+about)?)\s+", "", prompt, flags=re.IGNORECASE).strip()
                snippets = search_web_duckduckgo(clean_query or prompt, max_results=3)
                if snippets:
                    web_contexts.append("\n".join(f"• {s}" for s in snippets))

        if web_contexts:
            query_prompt = (
                f"{prompt}\n\n"
                f"--- [LIVE WEB CONTEXT PROVIDED BY MILO OS] ---\n"
                + "\n\n".join(web_contexts)
                + "\n--- [END LIVE WEB CONTEXT] ---\n"
                "Use the live web context above to provide an accurate, up-to-date answer in 1 to 3 direct, punchy sentences. Never say you cannot browse or tell the user to manually search."
            )

    # 1. Force Offline
    if mode == "offline":
        ans = query_cortex_daemon(prompt)
        if ans:
            return ans, "⚡ Cortex Local (Offline)"
        return "Local resident daemon is unreachable. Run `milo-cortex daemon start`.", "Error"

    # 2. Force Online
    if mode == "online":
        if not online:
            # Inform user or auto-fallback
            ans = query_cortex_daemon(prompt)
            if ans:
                return f"[Offline Fallback]: {ans}", "⚡ Cortex Local (Offline Failover)"
            return "Network disconnected and local daemon unavailable.", "Error"
        # Try ultra-fast Groq Cloud first (sub-second inference)
        groq_ans = query_groq_cloud(query_prompt, timeout=5.0)
        if groq_ans:
            return groq_ans, "⚡ Groq Cloud (Llama 3.3 70B)"
        # Fallback to Gemini Cloud
        ans = query_gemini_cloud(query_prompt, timeout=8.0)
        if ans:
            return ans, "🌐 Gemini Cloud"
        # Cloud failed, fallback to local
        local_ans = query_cortex_daemon(prompt)
        if local_ans:
            return local_ans, "⚡ Cortex Local (Cloud Fallback)"
        return "Unable to retrieve response from cloud or local daemon.", "Error"

    # 3. Auto Mode (Smart Failover)
    if online:
        # Try ultra-fast Groq Cloud first (sub-second inference)
        groq_ans = query_groq_cloud(query_prompt, timeout=5.0)
        if groq_ans:
            return groq_ans, "⚡ Groq Cloud (Llama 3.3 70B)"
        # Fallback to Gemini Cloud
        cloud_ans = query_gemini_cloud(query_prompt, timeout=8.0)
        if cloud_ans:
            return cloud_ans, "🌐 Gemini Cloud"

    # Fallback to Local Resident Daemon
    local_ans = query_cortex_daemon(prompt)
    if local_ans:
        provider = "⚡ Cortex Local" if not online else "⚡ Cortex Local (Cloud Failover)"
        return local_ans, provider

    return "Standing by, Sir. Both cloud and local backends are currently unreachable.", "None"


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "status":
            print(json.dumps(get_status(), indent=2))
        elif cmd == "get":
            print(get_mode())
        elif cmd == "set" and len(sys.argv) > 2:
            new_m = set_mode(sys.argv[2])
            print(f"Intelligence mode set to: {new_m}")
        elif cmd == "toggle":
            new_m = toggle_mode()
            print(f"Toggled intelligence mode to: {new_m}")
        elif cmd == "ask":
            q = " ".join(sys.argv[2:])
            ans, prov = execute_hybrid_query(q)
            print(f"[{prov}]: {ans}")
    else:
        print(json.dumps(get_status(), indent=2))
