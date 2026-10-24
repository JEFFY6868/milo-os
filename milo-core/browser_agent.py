#!/usr/bin/env python3
"""
Milo Autonomous Browser Agent with Harness² Recursive Self-Healing
Connects browser automation with Omarchy Wayland HUD, Obsidian Knowledge Vault,
and Google Research Harness² Propose-Probe-Compose self-healing mechanics.
"""

import sys
import os
import re
import json
import time
import asyncio
import argparse
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# Paths
HOME = Path.home()
CONFIG_DIR = HOME / ".config" / "milo"
ENV_FILE = CONFIG_DIR / "browser.env"
CONFIG_FILE = CONFIG_DIR / "config.json"
VAULT_DIR = HOME / "Documents" / "Obsidian" / "Milo"
RESEARCH_DIR = VAULT_DIR / "Knowledge" / "Web_Research"
LESSONS_DIR = VAULT_DIR / "Knowledge" / "Harness_Lessons"
LESSONS_INDEX = VAULT_DIR / "Knowledge" / "Harness_Lessons.md"
DAILY_DIR = VAULT_DIR / "Daily"

# Terminal Colors
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def load_env():
    """Load API keys from browser.env if present."""
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if key and val and key not in os.environ:
                    os.environ[key] = val


def get_llm(model_override: Optional[str] = None):
    """Determine and return the configured LLM."""
    load_env()
    from browser_use.llm import ChatGoogle, ChatOpenAI, ChatAnthropic, ChatGroq

    # 1. Google Gemini
    if os.environ.get("GEMINI_API_KEY"):
        model = model_override or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
        return ChatGoogle(model=model)

    # 2. OpenAI / Compatible
    if os.environ.get("OPENAI_API_KEY"):
        base_url = os.environ.get("OPENAI_BASE_URL")
        model = model_override or os.environ.get("OPENAI_MODEL", "gpt-4o")
        kwargs = {"model": model}
        if base_url:
            kwargs["base_url"] = base_url
        return ChatOpenAI(**kwargs)

    # 3. Groq Free Tier
    if os.environ.get("GROQ_API_KEY"):
        model = model_override or os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
        return ChatGroq(model=model)

    # 4. OpenRouter Free Models
    if os.environ.get("OPENROUTER_API_KEY"):
        model = model_override or os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3.2-11b-vision-instruct:free")
        return ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            model=model
        )

    # 5. Anthropic
    if os.environ.get("ANTHROPIC_API_KEY"):
        model = model_override or "claude-3-5-sonnet-20241022"
        return ChatAnthropic(model=model)

    return None


def update_hud(message: str):
    """Safely forward a notification/message to the desktop HUD via omarchy-shell IPC."""
    try:
        clean_msg = message.replace('"', '\\"').replace("'", "")
        os.system(f"omarchy-shell -q milo say \"{clean_msg}\" >/dev/null 2>&1 &")
    except Exception:
        pass


def slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "_", slug)[:40]


@dataclass
class ProbeResult:
    probe_id: int
    name: str
    strategy: str
    success: bool
    result_text: Optional[str] = None
    error_type: Optional[str] = None
    error_detail: Optional[str] = None
    duration_sec: float = 0.0


@dataclass
class HarnessReflection:
    task: str
    timestamp: str
    date_slug: str
    outcome: str  # "SUCCESS", "SELF_HEALED", "FAILED"
    probes: List[ProbeResult] = field(default_factory=list)
    final_output: str = ""
    adopted_strategy: str = ""
    reflection_notes: str = ""


class SelfHealingAgent:
    """
    Implements Google Research's Harness² Propose-Probe-Compose loop:
    - Probe 1: Directed, low-step autonomous browser-use agent
    - Diagnosis: Categorizes failure (Rate-Limit 429, DOM Stagnation, Timeout, Bot Obstruction)
    - Propose: Adapts the harness (Prompt injection, Model switch, Direct API extraction)
    - Probe 2+: Executes refined candidate harness
    - Compose: Synthesizes final answer & logs Harness Reflection into Obsidian
    """

    def __init__(self, task: str, headed: bool = False, max_steps: int = 8, self_heal: bool = True):
        self.task = task
        self.headed = headed
        self.max_steps = max_steps
        self.self_heal = self_heal
        self.reflection = HarnessReflection(
            task=task,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            date_slug=datetime.now().strftime("%Y-%m-%d"),
            outcome="PENDING"
        )

    async def execute(self) -> str:
        load_env()
        print(f"\n{BOLD}{CYAN}🌐 MILO HARNESS² BROWSER AGENT ACTIVE{RESET}")
        print(f"  {BOLD}Task:{RESET} {self.task}")
        print(f"  {BOLD}Mode:{RESET} {'Headed (Visible Window)' if self.headed else 'Headless (Background)'}")
        print(f"  {BOLD}Engine:{RESET} browser-use + Harness² Self-Healing")
        print(f"  {BOLD}Recursion Budget (k):{RESET} 2 probes\n")

        update_hud(f"🌐 Milo Browsing: {self.task[:45]}...")

        # --- PROBE 1: Directed Browser-Use Agent ---
        probe1 = await self._run_browser_use_probe(probe_id=1, model_name=None)
        self.reflection.probes.append(probe1)

        if probe1.success and probe1.result_text and probe1.result_text != "None":
            self.reflection.outcome = "SUCCESS"
            self.reflection.final_output = probe1.result_text
            self.reflection.adopted_strategy = "Primary Directed Agent (Base Harness)"
            self.reflection.reflection_notes = "Task achieved within primary recursion budget without errors."
            self._finalize()
            return probe1.result_text

        # If Probe 1 failed or yielded empty, initiate Harness² Self-Healing
        if not self.self_heal:
            print(f"{RED}✖ Probe 1 failed and Self-Healing is disabled.{RESET}")
            self.reflection.outcome = "FAILED"
            self.reflection.final_output = probe1.error_detail or "Execution failed without self-healing."
            self._finalize()
            return self.reflection.final_output

        print(f"\n{YELLOW}{BOLD}🛡️ [HARNESS² PROPOSE] Failure Signature Detected:{RESET}")
        print(f"  {DIM}Failure Reason:{RESET} {probe1.error_type} - {probe1.error_detail}")
        print(f"{MAGENTA}{BOLD}⚡ Proposing Candidate Recovery Probe...{RESET}")
        update_hud(f"🛡️ Self-Healing: Triggered recovery probe...")

        # --- PROBE 2: Contrastive Recovery Probe ---
        probe2 = await self._run_recovery_probe(probe_id=2, previous_error=probe1.error_type or "Unknown")
        self.reflection.probes.append(probe2)

        if probe2.success and probe2.result_text:
            self.reflection.outcome = "SELF_HEALED"
            self.reflection.final_output = probe2.result_text
            self.reflection.adopted_strategy = probe2.strategy
            self.reflection.reflection_notes = (
                f"Recovered successfully via {probe2.strategy}. "
                f"Initial failure ({probe1.error_type}) bypassed without crashing."
            )
            self._finalize()
            return probe2.result_text

        # If all probes failed
        self.reflection.outcome = "FAILED"
        self.reflection.final_output = f"All candidate probes exhausted. Last error: {probe2.error_detail}"
        self.reflection.adopted_strategy = "Exhausted"
        self.reflection.reflection_notes = "Both base probe and recovery probes failed."
        self._finalize()
        return self.reflection.final_output

    async def _run_browser_use_probe(self, probe_id: int, model_name: Optional[str] = None) -> ProbeResult:
        start_time = time.time()
        print(f"{CYAN}▶ [Probe {probe_id}] Executing Directed Browser-Use Harness...{RESET}")

        llm = get_llm(model_override=model_name)
        if not llm:
            return ProbeResult(
                probe_id=probe_id,
                name="Browser-Use Directed",
                strategy="Base Model Navigation",
                success=False,
                error_type="MissingCredentials",
                error_detail="No valid LLM API key configured in ~/.config/milo/browser.env",
                duration_sec=time.time() - start_time
            )

        try:
            from browser_use import Agent
            from browser_use.browser.profile import BrowserProfile

            step_count = 0

            def on_step(state, output, step_idx):
                nonlocal step_count
                step_count += 1
                action_name = getattr(output, "current_action_name", "Browsing") or "Browsing"
                print(f"  {DIM}↳ [Step {step_count}/{self.max_steps}]{RESET} {action_name}")
                update_hud(f"🌐 [{step_count}] {action_name[:30]}")

            profile = BrowserProfile(headless=(not self.headed))

            # Directed system guidance to optimize actions and prevent rate-limit burnout
            system_guidance = (
                "You are an efficient, high-speed research assistant. "
                "CRITICAL OBJECTIVE: Complete the user's task in the fewest possible steps (target 2-4 actions). "
                "Navigate directly to canonical search engines or direct URLs. "
                "As soon as you locate the needed information, extract it immediately and call done. "
                "Do not get stuck clicking advertisements, cookie prompts, or decorative links."
            )

            agent = Agent(
                task=self.task,
                llm=llm,
                browser_profile=profile,
                register_new_step_callback=on_step,
                max_actions_per_step=self.max_steps,
                extend_system_message=system_guidance,
                loop_detection_enabled=True,
                max_failures=1,
                planning_replan_on_stall=2
            )

            result = await agent.run()
            duration = time.time() - start_time

            final_text = str(result.final_result() if hasattr(result, "final_result") else result)
            has_errors = getattr(result, "has_errors", lambda: False)()

            if final_text and final_text != "None" and not has_errors:
                return ProbeResult(
                    probe_id=probe_id,
                    name="Browser-Use Directed",
                    strategy="Directed Fast-Path Agent",
                    success=True,
                    result_text=final_text,
                    duration_sec=duration
                )
            else:
                errors = getattr(result, "errors", lambda: ["Unsuccessful result or empty output"])()
                return ProbeResult(
                    probe_id=probe_id,
                    name="Browser-Use Directed",
                    strategy="Directed Fast-Path Agent",
                    success=False,
                    error_type="AgentStepFailure",
                    error_detail=str(errors[-1] if errors else "Empty output"),
                    duration_sec=duration
                )

        except Exception as e:
            duration = time.time() - start_time
            err_str = str(e)
            err_type = "RateLimitQuota429" if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str else (
                "ModelUnavailable503" if "503" in err_str else type(e).__name__
            )
            return ProbeResult(
                probe_id=probe_id,
                name="Browser-Use Directed",
                strategy="Directed Fast-Path Agent",
                success=False,
                error_type=err_type,
                error_detail=err_str[:250],
                duration_sec=duration
            )

    async def _run_recovery_probe(self, probe_id: int, previous_error: str) -> ProbeResult:
        """Executes a contrastive recovery probe designed specifically for the failure mode."""
        start_time = time.time()
        print(f"{MAGENTA}▶ [Probe {probe_id}] Probing Resilient Direct Knowledge Extractor...{RESET}")

        try:
            # 1. Clean query for knowledge extraction
            clean_query = self._extract_search_keywords(self.task)
            print(f"  {DIM}Synthesized Knowledge Target:{RESET} {clean_query}")

            # 2. Query DuckDuckGo Lite Canonical Search
            ddg_result = await self._fetch_ddg_lite_search(clean_query)
            if ddg_result:
                duration = time.time() - start_time
                return ProbeResult(
                    probe_id=probe_id,
                    name="Resilient Knowledge Extractor",
                    strategy="Zero-Quota Direct Web Search Probe (DDG Lite)",
                    success=True,
                    result_text=ddg_result,
                    duration_sec=duration
                )

            # 3. Fallback: Wikipedia Knowledge API
            wiki_result = await self._fetch_wikipedia_knowledge(clean_query)
            if wiki_result:
                duration = time.time() - start_time
                return ProbeResult(
                    probe_id=probe_id,
                    name="Resilient Knowledge Extractor",
                    strategy="Zero-Quota Direct Knowledge Probe (Wikipedia Canonical)",
                    success=True,
                    result_text=wiki_result,
                    duration_sec=duration
                )

            return ProbeResult(
                probe_id=probe_id,
                name="Resilient Knowledge Extractor",
                strategy="Zero-Quota Direct Knowledge Probe",
                success=False,
                error_type="ExtractionEmpty",
                error_detail="No search or encyclopedic snippet matched the target query.",
                duration_sec=time.time() - start_time
            )

        except Exception as e:
            return ProbeResult(
                probe_id=probe_id,
                name="Resilient Knowledge Extractor",
                strategy="Zero-Quota Direct Knowledge Probe",
                success=False,
                error_type=type(e).__name__,
                error_detail=str(e)[:200],
                duration_sec=time.time() - start_time
            )

    async def _fetch_ddg_lite_search(self, query: str) -> Optional[str]:
        def _sync_fetch():
            data = urllib.parse.urlencode({"q": query}).encode()
            req = urllib.request.Request(
                "https://lite.duckduckgo.com/lite/",
                data=data,
                headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0"}
            )
            try:
                with urllib.request.urlopen(req, timeout=8) as resp:
                    html = resp.read().decode("utf-8")
                    snippets = re.findall(r'<td class=[\'\"]result-snippet[\'\"]>(.*?)</td>', html, re.DOTALL)
                    if snippets:
                        cleaned_snippets = []
                        for s in snippets[:3]:
                            clean = re.sub(r'<[^<]+?>', '', s).strip()
                            clean = clean.replace('&quot;', '"').replace('&#x27;', "'").replace('&amp;', '&')
                            if clean and len(clean) > 20:
                                cleaned_snippets.append(f"• {clean}")
                        if cleaned_snippets:
                            return "\n\n".join(cleaned_snippets)
            except Exception:
                pass
            return None

        return await asyncio.to_thread(_sync_fetch)

    def _extract_search_keywords(self, task: str) -> str:
        query = re.sub(r"(?i)\b(what is|who is|find|tell me|search for|about|please|answer in one sentence|briefly)\b", "", task)
        return query.strip().strip("?.! ")

    async def _fetch_wikipedia_knowledge(self, query: str) -> Optional[str]:
        def _sync_fetch():
            encoded = urllib.parse.quote(query)
            url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded}&utf8=&format=json"
            req = urllib.request.Request(url, headers={"User-Agent": "MiloAgent/2.0 (Harness2 Self-Healing)"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                search_results = data.get("query", {}).get("search", [])
                if not search_results:
                    return None
                top = search_results[0]
                title = top.get("title", "")
                snippet = re.sub(r"<[^<]+?>", "", top.get("snippet", ""))

                # Fetch full intro extract if possible
                title_encoded = urllib.parse.quote(title)
                extract_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=&explaintext=&titles={title_encoded}&format=json"
                req_ext = urllib.request.Request(extract_url, headers={"User-Agent": "MiloAgent/2.0 (Harness2 Self-Healing)"})
                try:
                    with urllib.request.urlopen(req_ext, timeout=8) as resp_ext:
                        data_ext = json.loads(resp_ext.read().decode("utf-8"))
                        pages = data_ext.get("query", {}).get("pages", {})
                        for pid, pdata in pages.items():
                            extract = pdata.get("extract", "")
                            if extract:
                                first_para = extract.split("\n\n")[0]
                                return f"**{title}**:\n{first_para}"
                except Exception:
                    pass
                return f"**{title}**:\n{snippet}"

        return await asyncio.to_thread(_sync_fetch)

    async def _fetch_ddg_instant_knowledge(self, query: str) -> Optional[str]:
        def _sync_fetch():
            encoded = urllib.parse.quote(query)
            url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
            req = urllib.request.Request(url, headers={"User-Agent": "MiloAgent/2.0 (Harness2 Self-Healing)"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                abstract = data.get("AbstractText", "")
                heading = data.get("Heading", query)
                if abstract:
                    return f"**{heading}**:\n{abstract}"
                answer = data.get("Answer", "")
                if answer:
                    return f"**{heading}**:\n{answer}"
                return None

        return await asyncio.to_thread(_sync_fetch)

    def _finalize(self):
        """Saves deliverables to Obsidian Research and logs Harness² continuous reflection lessons."""
        outcome = self.reflection.outcome
        color = GREEN if outcome == "SUCCESS" else (YELLOW if outcome == "SELF_HEALED" else RED)

        print(f"\n{color}{BOLD}✦ Task Completed with Status: {outcome}{RESET}")
        print(f"{BOLD}Adopted Strategy:{RESET} {self.reflection.adopted_strategy}")
        print(f"{BOLD}Summary Deliverable:{RESET}\n{self.reflection.final_output}\n")

        # 1. Save to Obsidian Research & Daily
        save_to_obsidian_research(self.task, self.reflection)

        # 2. Save Harness² Reflection Lesson (Continuous Learning)
        save_harness_reflection_lesson(self.reflection)

        # 3. Update HUD
        status_icon = "✦" if outcome == "SUCCESS" else ("🛡️" if outcome == "SELF_HEALED" else "✖")
        short_summary = self.reflection.final_output.strip().replace("\n", " ")[:120]
        update_hud(f"{status_icon} Milo: {short_summary}...")


def save_to_obsidian_research(task: str, ref: HarnessReflection):
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    DAILY_DIR.mkdir(parents=True, exist_ok=True)

    file_slug = f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}_{slugify(task)}"
    report_file = RESEARCH_DIR / f"{file_slug}.md"

    probes_summary = "\n".join([
        f"- **Probe {p.probe_id} ({p.name}):** {'✅ Succeeded' if p.success else '❌ Failed'} (`{p.duration_sec:.2f}s`) - Strategy: *{p.strategy}*"
        for p in ref.probes
    ])

    report_content = f"""# 🌐 Web Research: {task}

- **Date:** {ref.timestamp}
- **Agent:** Milo Harness² Self-Healing Agent
- **Status:** `{ref.outcome}`
- **Adopted Strategy:** {ref.adopted_strategy}

---

## 📋 Probes & Execution Contrast
{probes_summary}

---

## 💡 Deliverable & Findings
{ref.final_output}

---

## 🧭 Navigation
- Back to [[Dashboard]]
- Harness Lessons: [[Knowledge/Harness_Lessons|Harness Lessons Index]]
- Daily Note: [[Daily/{ref.date_slug}]]
"""
    report_file.write_text(report_content)
    print(f"{CYAN}📝 Research Logged to Obsidian: [[Knowledge/Web_Research/{file_slug}]]{RESET}")

    # Append to Daily Note
    daily_file = DAILY_DIR / f"{ref.date_slug}.md"
    if not daily_file.exists():
        daily_file.write_text(f"# 📅 Daily Note: {ref.date_slug}\n\n## 💬 Conversations & Interaction Log\n\n")

    daily_entry = f"""### {datetime.now().strftime('%H:%M')} - Web Research ({ref.outcome})
- **Task:** {task}
- **Strategy:** {ref.adopted_strategy}
- **Findings:** [[Knowledge/Web_Research/{file_slug}|View Full Report]]
- **Summary:** {ref.final_output[:200]}...

"""
    with open(daily_file, "a") as f:
        f.write(daily_entry)


def save_harness_reflection_lesson(ref: HarnessReflection):
    """Writes detailed Harness² reflection notes into Knowledge/Harness_Lessons/ and updates the index."""
    LESSONS_DIR.mkdir(parents=True, exist_ok=True)

    file_slug = f"Lesson_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}_{slugify(ref.task)}"
    lesson_file = LESSONS_DIR / f"{file_slug}.md"

    probe_table_rows = "\n".join([
        f"| {p.probe_id} | {p.name} | {'✅ Passed' if p.success else '❌ Failed'} | `{p.duration_sec:.2f}s` | {p.strategy} | {p.error_type or 'None'} |"
        for p in ref.probes
    ])

    lesson_content = f"""# 🧬 Harness² Reflection Lesson: {ref.task}

- **Timestamp:** {ref.timestamp}
- **Outcome Status:** `{ref.outcome}`
- **Winning Harness Component:** `{ref.adopted_strategy}`

---

## 🔬 Propose-Probe-Compose Analysis

| Probe | Name | Outcome | Duration | Strategy | Failure Signature |
| :---: | :--- | :---: | :---: | :--- | :--- |
{probe_table_rows}

---

## 🧠 Reflection & Learned Lesson

{ref.reflection_notes}

### Adopted Recommendation for Future Tasks:
- When encountering `{ref.probes[0].error_type if ref.probes and ref.probes[0].error_type else 'Execution'}`:
  Deploy **{ref.adopted_strategy}** to bypass obstruction and preserve responsiveness.

---

## 🧭 Navigation
- [[Knowledge/Harness_Lessons|All Harness Lessons]]
- [[Dashboard]]
"""
    lesson_file.write_text(lesson_content)
    print(f"{MAGENTA}🧬 Harness² Lesson Saved: [[Knowledge/Harness_Lessons/{file_slug}]]{RESET}")

    # Maintain central index in Knowledge/Harness_Lessons.md
    if not LESSONS_INDEX.exists():
        LESSONS_INDEX.write_text("""# 🧬 Milo Harness² Continuous Learning Lessons

Automated reflection lessons captured by Milo's Self-Healing Agent. Inspired by Google Research's Harness² (Recursive Agent Harnessing).

---

## 📜 Reflection Log

| Timestamp | Task | Outcome | Probes | Winning Strategy | Lesson Note |
| :--- | :--- | :---: | :---: | :--- | :--- |
""")

    short_task = ref.task.replace("|", "/")[:35]
    short_strategy = ref.adopted_strategy.replace("|", "/")[:30]
    row = f"| {ref.timestamp[:16]} | {short_task} | `{ref.outcome}` | {len(ref.probes)} | {short_strategy} | [[Knowledge/Harness_Lessons/{file_slug}|View Lesson]] |\n"

    with open(LESSONS_INDEX, "a") as f:
        f.write(row)


def main():
    parser = argparse.ArgumentParser(description="Milo Autonomous Browser Agent with Harness² Self-Healing")
    parser.add_argument("task", nargs="+", help="The web browsing instruction for Milo")
    parser.add_argument("--headed", "--watch", action="store_true", help="Launch visible browser window in Hyprland")
    parser.add_argument("--headless", action="store_true", help="Run browser in background")
    parser.add_argument("--max-steps", type=int, default=8, help="Maximum action steps per probe")
    parser.add_argument("--no-self-heal", action="store_true", help="Disable Harness² self-healing recursion")

    args = parser.parse_args()
    task = " ".join(args.task)
    headed = args.headed and not args.headless
    self_heal = not args.no_self_heal

    agent = SelfHealingAgent(
        task=task,
        headed=headed,
        max_steps=args.max_steps,
        self_heal=self_heal
    )

    asyncio.run(agent.execute())


if __name__ == "__main__":
    main()
