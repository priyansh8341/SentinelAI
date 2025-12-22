import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3"

def reason_over_changes(previous: str, current: str) -> str:
    prompt = f"""
You are an autonomous business intelligence agent.

Compare the previous snapshot with the current snapshot.
Return a structured brief:

1) Key Changes (5 bullets)
2) Impact Lens (who/what is affected)
3) Bull vs Bear (3 bullets each)
4) What to Watch Next (catalysts + numbers)
5) Risk Flags
6) Tomorrow Plan (5 checklist items)

Previous:
{previous}

Current:
{current}
""".strip()

    r = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }, timeout=120)

    r.raise_for_status()
    return r.json().get("response", "").strip()
