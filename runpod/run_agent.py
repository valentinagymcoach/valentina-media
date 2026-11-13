"""Browser-Use-Agent: ein VLM (lokal über Ollama oder per OpenAI-kompatibler API) steuert einen
Chromium-Browser im Pod. Öffentliche Seiten ja; Instagram/Facebook/Threads gesperrt; keine Logins.

Aufruf:
  /workspace/ai/agent.sh "Öffne http://127.0.0.1:8188 und lade den Standard-Workflow"
  /workspace/ai/agent.sh --file tasks/beispiel.txt
"""
import argparse, asyncio, os, pathlib
from browser_use import Agent, Browser, ChatOpenAI


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task", nargs="?", help="Aufgabe in Klartext")
    ap.add_argument("--file", help="Aufgabe aus Textdatei lesen")
    ap.add_argument("--max-steps", type=int, default=25)
    ap.add_argument("--headful", action="store_true", help="sichtbarer Browser (braucht X11/VNC)")
    a = ap.parse_args()
    task = pathlib.Path(a.file).read_text() if a.file else a.task
    if not task:
        ap.error("Bitte eine Aufgabe angeben")

    llm = ChatOpenAI(os.environ.get("LLM_MODEL", "qwen3.8:27b"),
                     base_url=os.environ.get("LLM_BASE_URL", "http://127.0.0.1:11434/v1"),
                     api_key=os.environ.get("LLM_API_KEY", "ollama"),
                     temperature=0.2)
    allowed = [d.strip() for d in os.environ.get("ALLOWED_DOMAINS", "").split(",") if d.strip()] or None
    blocked = [d.strip() for d in os.environ.get("BLOCKED_DOMAINS", "").split(",") if d.strip()] or None
    browser = Browser("chromium", headless=not a.headful, allowed_domains=allowed, prohibited_domains=blocked)
    rules = ("Regeln: Nur lesen und recherchieren. Melde dich nirgends an, erstelle keine Konten, gib keine Passwörter ein, "
             "löse keine CAPTCHAs, sende keine Formulare ab und kaufe nichts. Wenn das nötig wäre, brich ab und sag es.\n\nAufgabe: ")
    agent = Agent(task=rules + task, llm=llm, browser=browser, workspace=os.environ.get("AGENT_OUT", "/workspace/ai/agent_out"))
    result = asyncio.run(agent.run(max_steps=a.max_steps))
    print("\n=== Ergebnis ===\n", getattr(result, "final_result", lambda: result)())


if __name__ == "__main__":
    main()
