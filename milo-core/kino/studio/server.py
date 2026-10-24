#!/usr/bin/env python3
"""
Kino Cinema Studio — Backend Server
Exposes REST API and serves the Director's Web UI.
Directly interfaces with KinoEngine and Obsidian Cinema Vault.
"""

import sys
import os
import re
import json
import asyncio
from pathlib import Path
from datetime import datetime

from starlette.applications import Starlette
from starlette.routing import Route, Mount, WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect
from starlette.responses import JSONResponse, FileResponse, Response
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import uvicorn
from livekit.api import AccessToken, VideoGrants
import edge_tts
import milo_companion

# Setup paths to import kino_agent
KINO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KINO_DIR))

from kino_agent import (
    KinoEngine,
    PROJECTS_DIR,
    IDEAS_DIR,
    CHARACTERS_DIR,
    SHOTLISTS_DIR,
    VAULT_DIR,
    CINEMA_DIR,
    slugify
)

engine = KinoEngine()
STATIC_DIR = Path(__file__).resolve().parent / "static"

LIVEKIT_URL = "ws://127.0.0.1:7880"
LIVEKIT_API_KEY = "milo_key"
LIVEKIT_API_SECRET = "milo_livekit_secret_token_32_bytes_long_key_12345"


async def get_status(request):
    return JSONResponse({
        "status": "online",
        "name": "Kino Cinema Studio",
        "director": "Jeffy",
        "version": "1.0.0",
        "vault_path": str(CINEMA_DIR),
        "timestamp": datetime.now().isoformat()
    })


async def list_projects(request):
    projects = []
    if PROJECTS_DIR.exists():
        for p in PROJECTS_DIR.iterdir():
            if p.is_dir() and not p.name.startswith("."):
                overview_file = p / "Overview.md"
                beats_file = p / "BeatSheet.md"
                chars_file = p / "Characters.md"
                shots_file = p / "Shotlist.md"

                title = p.name.replace("_", " ").title()
                logline = ""
                genre = "Cinema / Narrative"
                created = datetime.fromtimestamp(p.stat().st_ctime).strftime("%Y-%m-%d")

                if overview_file.exists():
                    try:
                        content = overview_file.read_text(encoding="utf-8")
                        for line in content.splitlines():
                            if line.startswith("# 🎬 Film Project:"):
                                title = line.replace("# 🎬 Film Project:", "").strip()
                            elif line.startswith("- **Created:**"):
                                created = line.replace("- **Created:**", "").strip()
                    except Exception:
                        pass

                projects.append({
                    "slug": p.name,
                    "title": title,
                    "created": created,
                    "has_beats": beats_file.exists(),
                    "has_chars": chars_file.exists(),
                    "has_shots": shots_file.exists(),
                })
    return JSONResponse({"projects": projects})


async def get_project(request):
    slug = request.path_params.get("slug")
    proj_dir = PROJECTS_DIR / slug
    if not proj_dir.exists() or not proj_dir.is_dir():
        return JSONResponse({"error": "Project not found"}, status_code=404)

    files = {}
    for item in proj_dir.glob("*.md"):
        try:
            files[item.name] = item.read_text(encoding="utf-8")
        except Exception as e:
            files[item.name] = f"Error reading file: {e}"

    return JSONResponse({
        "slug": slug,
        "files": files
    })


async def save_project_file(request):
    try:
        data = await request.json()
        slug = data.get("slug")
        filename = data.get("filename")
        content = data.get("content")

        if not slug or not filename or content is None:
            return JSONResponse({"error": "Missing parameters"}, status_code=400)

        # Sanitize filename
        safe_filename = Path(filename).name
        if not safe_filename.endswith(".md"):
            safe_filename += ".md"

        target_path = PROJECTS_DIR / slug / safe_filename
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")

        return JSONResponse({"success": True, "saved_path": str(target_path)})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def create_project(request):
    try:
        data = await request.json()
        title = data.get("title", "").strip()
        if not title:
            return JSONResponse({"error": "Title required"}, status_code=400)

        msg = engine.init_project(title)
        slug = slugify(title)
        return JSONResponse({"success": True, "slug": slug, "message": msg})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def list_ideas(request):
    ideas = []
    if IDEAS_DIR.exists():
        for f in sorted(IDEAS_DIR.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.name == "Index.md":
                continue
            try:
                content = f.read_text(encoding="utf-8")
                title = f.stem
                for line in content.splitlines():
                    if line.startswith("# "):
                        title = line.replace("# ", "").strip()
                        break
                ideas.append({
                    "filename": f.name,
                    "title": title,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "content": content
                })
            except Exception:
                pass
    return JSONResponse({"ideas": ideas})


async def list_characters(request):
    characters = []
    if CHARACTERS_DIR.exists():
        for f in sorted(CHARACTERS_DIR.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.name == "Index.md":
                continue
            try:
                content = f.read_text(encoding="utf-8")
                name = f.stem.replace("_", " ").title()
                for line in content.splitlines():
                    if line.startswith("# 👤 Character Dossier:"):
                        name = line.replace("# 👤 Character Dossier:", "").strip()
                        break
                characters.append({
                    "slug": f.stem,
                    "filename": f.name,
                    "name": name,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "content": content
                })
            except Exception:
                pass
    return JSONResponse({"characters": characters})


async def list_shotlists(request):
    shotlists = []
    if SHOTLISTS_DIR.exists():
        for f in sorted(SHOTLISTS_DIR.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.name == "Index.md":
                continue
            try:
                content = f.read_text(encoding="utf-8")
                title = f.stem
                for line in content.splitlines():
                    if line.startswith("# 🎥"):
                        title = line.replace("# 🎥", "").strip()
                        break
                shotlists.append({
                    "filename": f.name,
                    "title": title,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "content": content
                })
            except Exception:
                pass
    return JSONResponse({"shotlists": shotlists})


# AI Action Endpoints (Async non-blocking via asyncio.to_thread)
async def ai_doctor(request):
    try:
        data = await request.json()
        pitch = data.get("scene_pitch", "").strip()
        if not pitch:
            return JSONResponse({"error": "scene_pitch required"}, status_code=400)

        result = await asyncio.to_thread(engine.script_doctor, pitch)
        return JSONResponse({"success": True, "result": result})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def ai_shotlist(request):
    try:
        data = await request.json()
        scene = data.get("scene_description", "").strip()
        if not scene:
            return JSONResponse({"error": "scene_description required"}, status_code=400)

        result = await asyncio.to_thread(engine.generate_shotlist, scene)
        return JSONResponse({"success": True, "result": result})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def ai_character(request):
    try:
        data = await request.json()
        name = data.get("name", "").strip()
        details = data.get("details", "").strip()
        project = data.get("project", "")
        if not name or not details:
            return JSONResponse({"error": "name and details required"}, status_code=400)

        result = await asyncio.to_thread(engine.develop_character, name, details, project)
        return JSONResponse({"success": True, "result": result})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def ai_idea(request):
    try:
        data = await request.json()
        raw_idea = data.get("raw_idea", "").strip()
        if not raw_idea:
            return JSONResponse({"error": "raw_idea required"}, status_code=400)

        result = await asyncio.to_thread(engine.develop_idea, raw_idea)
        return JSONResponse({"success": True, "result": result})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


class CallSignalingManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

call_manager = CallSignalingManager()

async def call_websocket_endpoint(websocket: WebSocket):
    await call_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") in ("call_accepted", "call_declined", "call_ended"):
                    await call_manager.broadcast(msg)
            except Exception:
                pass
    except (WebSocketDisconnect, Exception):
        call_manager.disconnect(websocket)

async def trigger_call(request):
    try:
        data = {}
        if request.method == "POST":
            try:
                data = await request.json()
            except Exception:
                pass
        text = data.get("text") or request.query_params.get("text", "Screenplay brainstorm session")
        caller = data.get("caller") or request.query_params.get("caller", "Milo AI")
        
        event = {
            "type": "incoming_call",
            "caller": caller,
            "text": text,
            "timestamp": int(datetime.now().timestamp())
        }
        await call_manager.broadcast(event)
        return JSONResponse({"success": True, "broadcasted_to": len(call_manager.active_connections)})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

async def call_page(request):
    call_file = STATIC_DIR / "call.html"
    if call_file.exists():
        return FileResponse(call_file)
    return JSONResponse({"error": "call.html not found"}, status_code=404)

async def manifest_file(request):
    mf = STATIC_DIR / "manifest.json"
    if mf.exists():
        return FileResponse(mf, media_type="application/manifest+json")
    return JSONResponse({"error": "manifest.json not found"}, status_code=404)

async def sw_file(request):
    sw = STATIC_DIR / "sw.js"
    if sw.exists():
        return FileResponse(sw, media_type="application/javascript")
    return JSONResponse({"error": "sw.js not found"}, status_code=404)

async def get_voice_token(request):
    try:
        identity = request.query_params.get("identity", "jeffy")
        room = request.query_params.get("room", "milo-voice")
        token = AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        token.with_identity(identity).with_name("Jeffy").with_grants(
            VideoGrants(room_join=True, room=room)
        )
        
        # Determine dynamic LiveKit host from request header
        host_header = request.headers.get("host", "127.0.0.1:3140")
        client_host = host_header.split(":")[0]
        livekit_ws = f"ws://{client_host}:7880"

        return JSONResponse({
            "url": livekit_ws,
            "token": token.to_jwt(),
            "room": room,
            "identity": identity
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def post_voice_query(request):
    try:
        data = await request.json()
        query = data.get("query", "").strip()
        voice = data.get("voice", "en-US-ChristopherNeural")
        mode = data.get("mode", "milo_main").lower()
        if not query:
            return JSONResponse({"error": "Query required"}, status_code=400)

        # Route query based on explicit mode or cinema subagent
        if mode == "kino_story":
            reply = await asyncio.to_thread(engine.script_doctor, query)
        elif mode == "kino_characters":
            reply = await asyncio.to_thread(engine.develop_idea, query)
        elif mode == "kino_shotlist":
            reply = await asyncio.to_thread(engine.generate_shotlist, query)
        elif mode == "milo_main":
            # Milo Main AI: Personal Desktop Companion with Live Hyprland State & Obsidian Memory
            milo_res = await asyncio.to_thread(milo_companion.ask_milo, query, voice)
            reply = milo_res.get("reply", "")
        else:
            # Fallback heuristic if mode is generic
            if any(w in query.lower() for w in ["kino", "scene", "script", "shot", "character", "pitch", "director", "dialogue", "act "]):
                reply = await asyncio.to_thread(engine.script_doctor, query)
            else:
                milo_res = await asyncio.to_thread(milo_companion.ask_milo, query, voice)
                reply = milo_res.get("reply", "")

        clean_speech = re.sub(r"[#*_`>\[\]\(\)]", " ", reply)
        clean_speech = re.sub(r"\s+", " ", clean_speech).strip()[:350]

        return JSONResponse({
            "success": True,
            "query": query,
            "reply": reply,
            "clean_speech": clean_speech,
            "voice": voice
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def post_voice_transcribe(request):
    """
    Server-side Speech-To-Text endpoint.
    Accepts audio data (WebM, WAV, OGG) from mobile/desktop browser MediaRecorder,
    and accurately transcribes it using Gemini 2.5 Flash Lite supporting Tamil, English, and Tanglish.
    """
    try:
        content_type = request.headers.get("content-type", "")
        audio_bytes = None
        mime_type = "audio/webm"

        if "multipart/form-data" in content_type:
            form = await request.form()
            audio_field = form.get("audio") or form.get("file")
            if audio_field:
                audio_bytes = await audio_field.read()
                mime_type = getattr(audio_field, "content_type", "") or ""
                filename = getattr(audio_field, "filename", "") or ""
                if not mime_type or mime_type == "application/octet-stream":
                    if filename.endswith(".wav"):
                        mime_type = "audio/wav"
                    elif filename.endswith(".ogg") or filename.endswith(".opus"):
                        mime_type = "audio/ogg"
                    elif filename.endswith(".mp4") or filename.endswith(".m4a"):
                        mime_type = "audio/mp4"
                    else:
                        mime_type = "audio/webm"
        else:
            audio_bytes = await request.body()
            if "audio/" in content_type:
                mime_type = content_type.split(";")[0].strip()
            else:
                mime_type = "audio/webm"

        if not audio_bytes or len(audio_bytes) < 300:
            return JSONResponse({"error": "Audio stream empty or too short", "text": ""}, status_code=400)

        # Retrieve Gemini API key
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            env_file = Path.home() / ".config/milo/browser.env"
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    if line.startswith("GEMINI_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break

        if not api_key:
            return JSONResponse({"error": "Gemini API key not found"}, status_code=500)

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)

        lang_hint = request.query_params.get("lang", "any")
        prompt = (
            "You are an ultra-accurate speech recognition engine. "
            "Transcribe the spoken audio into text. "
            "The speaker is Jeffy, speaking in either Tamil, English, or Tanglish (a natural mix of Tamil and English words). "
            "Transcribe exactly what was spoken in natural phonetic script (e.g. Tamil or Tanglish/English). "
            "Output ONLY the transcribed words. Do NOT include notes, timestamps, explanations, or quotes."
        )

        models_to_try = ["gemini-3.5-flash-lite", "gemini-3.5-transcribe", "gemini-flash-lite-latest"]
        resp = None
        for m in models_to_try:
            try:
                resp = await asyncio.to_thread(
                    client.models.generate_content,
                    model=m,
                    contents=[audio_part, prompt]
                )
                if resp and resp.text:
                    break
            except Exception:
                continue

        raw_text = (resp.text if resp else "").strip()
        # Clean up any surrounding quotes
        if raw_text.startswith('"') and raw_text.endswith('"'):
            raw_text = raw_text[1:-1].strip()

        return JSONResponse({
            "success": True,
            "text": raw_text
        })
    except Exception as e:
        return JSONResponse({"error": str(e), "text": ""}, status_code=500)


async def stream_voice_tts(request):
    try:
        text = request.query_params.get("text", "").strip()
        voice = request.query_params.get("voice", "en-US-ChristopherNeural")
        fmt = request.query_params.get("format", "opus").lower()
        if not text:
            return JSONResponse({"error": "Text required"}, status_code=400)

        # Smart Voice Auto-Detection:
        # If text contains Tamil Unicode characters (\u0B80-\u0BFF), use Tamil voice.
        has_tamil = bool(re.search(r"[\u0B80-\u0BFF]", text))
        if has_tamil and not voice.startswith("ta-"):
            voice = "ta-IN-ValluvarNeural"

        audio_data = bytearray()
        try:
            communicate = edge_tts.Communicate(text, voice)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data.extend(chunk["data"])
        except Exception as tts_err:
            # Fallback voice if specific voice failed
            fallback_voice = "ta-IN-ValluvarNeural" if has_tamil else "en-US-ChristopherNeural"
            communicate = edge_tts.Communicate(text, fallback_voice)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data.extend(chunk["data"])

        if fmt == "mp3":
            return Response(content=bytes(audio_data), media_type="audio/mpeg")

        # Convert to Ogg Opus: universally decoded by GStreamer (opusdec) & all browsers
        import subprocess
        proc = await asyncio.to_thread(
            subprocess.run,
            ["ffmpeg", "-y", "-f", "mp3", "-i", "pipe:0", "-c:a", "libopus", "-b:a", "32k", "-f", "ogg", "pipe:1"],
            input=bytes(audio_data),
            capture_output=True,
            timeout=10
        )
        if proc.returncode == 0 and proc.stdout:
            return Response(content=proc.stdout, media_type="audio/ogg; codecs=opus")

        return Response(content=bytes(audio_data), media_type="audio/mpeg")
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def index_page(request):
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse({"error": "index.html not found"}, status_code=404)


async def download_apk(request):
    apk_file = STATIC_DIR / "MiloNativeCall.apk"
    if apk_file.exists():
        return FileResponse(
            apk_file,
            media_type="application/vnd.android.package-archive",
            filename="MiloNativeCall.apk"
        )
    return JSONResponse({"error": "APK file not found"}, status_code=404)


# Routes
routes = [
    Route("/", endpoint=index_page),
    Route("/download", endpoint=download_apk),
    Route("/app", endpoint=download_apk),
    Route("/app.apk", endpoint=download_apk),
    Route("/milo.apk", endpoint=download_apk),
    Route("/call", endpoint=call_page),
    Route("/manifest.json", endpoint=manifest_file),
    Route("/sw.js", endpoint=sw_file),
    Route("/api/status", endpoint=get_status, methods=["GET"]),
    Route("/api/projects", endpoint=list_projects, methods=["GET"]),
    Route("/api/project/create", endpoint=create_project, methods=["POST"]),
    Route("/api/project/{slug}", endpoint=get_project, methods=["GET"]),
    Route("/api/project/save", endpoint=save_project_file, methods=["POST"]),
    Route("/api/ideas", endpoint=list_ideas, methods=["GET"]),
    Route("/api/characters", endpoint=list_characters, methods=["GET"]),
    Route("/api/shotlists", endpoint=list_shotlists, methods=["GET"]),
    Route("/api/ai/doctor", endpoint=ai_doctor, methods=["POST"]),
    Route("/api/ai/shotlist", endpoint=ai_shotlist, methods=["POST"]),
    Route("/api/ai/character", endpoint=ai_character, methods=["POST"]),
    Route("/api/ai/idea", endpoint=ai_idea, methods=["POST"]),
    Route("/api/voice/token", endpoint=get_voice_token, methods=["GET"]),
    Route("/api/voice/query", endpoint=post_voice_query, methods=["POST"]),
    Route("/api/voice/transcribe", endpoint=post_voice_transcribe, methods=["POST"]),
    Route("/api/voice/tts", endpoint=stream_voice_tts, methods=["GET"]),
    Route("/api/call/trigger", endpoint=trigger_call, methods=["POST", "GET"]),
    WebSocketRoute("/ws/call", endpoint=call_websocket_endpoint),
    Mount("/static", app=StaticFiles(directory=str(STATIC_DIR)), name="static")
]

middleware = [
    Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
]

app = Starlette(debug=True, routes=routes, middleware=middleware)

if __name__ == "__main__":
    port = int(os.environ.get("KINO_PORT", 3140))
    host = os.environ.get("KINO_HOST", "0.0.0.0")
    print(f"🎬 Starting Kino Cinema Studio at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
