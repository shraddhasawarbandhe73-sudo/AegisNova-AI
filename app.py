import json
import os
import re
from datetime import datetime, timezone

import requests
from flask import Flask, jsonify, request, send_from_directory

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    import boto3
except Exception:
    boto3 = None

APP_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder="static")

# Nebius Token Factory (OpenAI-compatible API) + NVIDIA Nemotron
NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY", "").strip()
NEBIUS_BASE_URL = os.getenv(
    "NEBIUS_BASE_URL",
    "https://api.tokenfactory.us-central1.nebius.com/v1/chat/completions",
).strip().rstrip("/")
NEBIUS_MODEL = os.getenv("NEBIUS_MODEL", "nvidia/nemotron-3-super-120b-a12b").strip()
NEBIUS_TIMEOUT = int(os.getenv("NEBIUS_TIMEOUT", "45"))

# Optional existing integrations
RING_BASE_URL = os.getenv("RING_API_BASE_URL", "https://api.amazonvision.com").rstrip("/")
RING_ACCESS_TOKEN = os.getenv("RING_ACCESS_TOKEN", "").strip()
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "").strip()
REQUEST_TIMEOUT = 20

LEVELS = {"NORMAL", "ATTENTION", "URGENT"}


def classify_event(event):
    """Transparent fallback classifier; not a medical or emergency detector."""
    raw = " ".join(str(event.get(k, "")) for k in (
        "event_type", "type", "kind", "description", "name", "source",
        "classification", "object_type", "label"
    )).lower()
    score = 15
    reasons = []
    urgent_words = ("fall", "person_down", "distress", "forced_entry", "break_in")
    attention_words = ("motion", "vehicle", "package", "doorbell", "person", "human", "animal", "unknown")
    if any(w in raw for w in urgent_words):
        score = 80
        reasons.append("The event text contains a potentially important indicator; verify it directly.")
    elif any(w in raw for w in attention_words):
        score = 48
        reasons.append("The activity metadata may warrant a quick human review.")
    else:
        reasons.append("No high-priority indicator was found in the supplied event metadata.")
    if any(w in raw for w in ("doorbell", "package", "vehicle")):
        score = max(score, 45)
    level = "URGENT" if score >= 75 else ("ATTENTION" if score >= 35 else "NORMAL")
    summary = {
        "URGENT": "Potentially important event; verify the situation promptly.",
        "ATTENTION": "Activity recorded; check whether it was expected.",
        "NORMAL": "No obvious high-priority indicator in the available metadata.",
    }[level]
    return {
        "level": level, "score": score, "summary": summary,
        "reason": " ".join(reasons), "method": "transparent rule-based fallback",
        "model": None,
    }


def _parse_model_json(content):
    if isinstance(content, list):
        content = "".join(str(part.get("text", "")) if isinstance(part, dict) else str(part) for part in content)
    content = str(content or "").strip()
    match = re.search(r"\{.*\}", content, re.S)
    if not match:
        raise ValueError("Model response did not contain a JSON object.")
    data = json.loads(match.group(0))
    level = str(data.get("level", "ATTENTION")).upper()
    if level not in LEVELS:
        level = "ATTENTION"
    return {
        "level": level,
        "score": {"NORMAL": 15, "ATTENTION": 48, "URGENT": 80}[level],
        "summary": str(data.get("summary", "Review the event details."))[:500],
        "reason": str(data.get("reason", "Verify the available event details."))[:500],
        "suggested_action": str(data.get("suggested_action", "Review the event details and verify the context."))[:500],
    }


def nebius_summary(event, fallback):
    """Use NVIDIA Nemotron through Nebius Token Factory when configured."""
    if not NEBIUS_API_KEY:
        return None
    safe_event = json.dumps(event, ensure_ascii=False, default=str)[:5000]
    system_prompt = (
        "You are AegisNova AI, a cautious event-awareness assistant for caregivers. "
        "You are not a medical device or emergency service. Use only the provided metadata. "
        "Do not claim that a fall, crime, injury, or emergency happened unless the metadata explicitly states it. "
        "Do not invent facts. If evidence is incomplete, say so. Return ONLY valid JSON with keys: "
        "level (NORMAL, ATTENTION, or URGENT), summary (one or two sentences), reason (one sentence), "
        "suggested_action (a cautious, practical next step). Use URGENT only when the supplied text explicitly "
        "indicates a potentially serious immediate concern; otherwise use ATTENTION or NORMAL."
    )
    response = requests.post(
        NEBIUS_BASE_URL,
        headers={"Authorization": f"Bearer {NEBIUS_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": NEBIUS_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this event metadata:\n{safe_event}"},
            ],
            "temperature": 0.1,
            "max_tokens": 350,
        },
        timeout=NEBIUS_TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()
    content = payload["choices"][0]["message"]["content"]
    parsed = _parse_model_json(content)
    parsed["method"] = "Nebius Token Factory + NVIDIA Nemotron"
    parsed["model"] = NEBIUS_MODEL
    return parsed


def bedrock_summary(event, fallback):
    """Optional legacy Amazon Bedrock path; only used if explicitly configured."""
    if not BEDROCK_MODEL_ID or boto3 is None:
        return None
    try:
        prompt = (
            "You are a cautious event-awareness assistant, not a medical or emergency diagnosis system. "
            "Use only event metadata; do not invent facts. Return JSON with keys level (NORMAL, ATTENTION, URGENT), "
            "summary, reason, suggested_action. Event metadata: " + json.dumps(event, ensure_ascii=False, default=str)[:4000]
        )
        client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
        response = client.converse(
            modelId=BEDROCK_MODEL_ID,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 300, "temperature": 0.1},
        )
        content = response["output"]["message"]["content"][0]["text"]
        parsed = _parse_model_json(content)
        parsed["method"] = "Amazon Bedrock"
        parsed["model"] = BEDROCK_MODEL_ID
        return parsed
    except Exception:
        return None


def analyze_event(event):
    fallback = classify_event(event)
    if NEBIUS_API_KEY:
        try:
            result = nebius_summary(event, fallback)
            if result:
                return result
        except Exception:
            # Keep the demo usable without leaking keys or provider response details.
            fallback["ai_note"] = "Nebius AI request failed; showing the transparent fallback result. Check API key, model access, and network."
            fallback["nebius_error"] = True
            return fallback
    bedrock = bedrock_summary(event, fallback)
    if bedrock:
        return bedrock
    return fallback


def ring_request(path):
    if not RING_ACCESS_TOKEN:
        raise RuntimeError("Ring token not configured. Use Demo Events or add RING_ACCESS_TOKEN to your private .env file.")
    response = requests.get(
        f"{RING_BASE_URL}{path}",
        headers={"Authorization": f"Bearer {RING_ACCESS_TOKEN}", "Accept": "application/json"},
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code == 401:
        raise RuntimeError("Ring token is invalid or expired. Generate a fresh token in the Ring Developer Playground.")
    response.raise_for_status()
    return response.json()


@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.get("/api/status")
def status():
    return jsonify({
        "ring_configured": bool(RING_ACCESS_TOKEN),
        "nebius_configured": bool(NEBIUS_API_KEY),
        "nebius_model": NEBIUS_MODEL if NEBIUS_API_KEY else None,
        "bedrock_configured": bool(BEDROCK_MODEL_ID and boto3 is not None),
        "mode": "Nebius + NVIDIA Nemotron" if NEBIUS_API_KEY else ("Amazon Bedrock" if BEDROCK_MODEL_ID and boto3 is not None else "Demo Mode / Rule-based fallback"),
    })


@app.get("/api/devices")
def devices():
    try:
        data = ring_request("/v1/devices")
        return jsonify({"ok": True, "data": data})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.get("/api/events")
def events():
    device_id = request.args.get("device_id", "").strip()
    if not device_id:
        return jsonify({"ok": False, "error": "Choose a Ring device first."}), 400
    safe_id = requests.utils.quote(device_id, safe=".")
    try:
        data = ring_request(f"/v1/history/devices/{safe_id}/events")
        raw_events = data if isinstance(data, list) else data.get("events", data.get("data", []))
        enriched = []
        for event in raw_events[:100]:
            item = dict(event) if isinstance(event, dict) else {"event": str(event)}
            item["guardian_analysis"] = analyze_event(item)
            enriched.append(item)
        return jsonify({"ok": True, "events": enriched, "count": len(enriched)})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.post("/api/analyze")
def analyze():
    event = request.get_json(silent=True)
    if not isinstance(event, dict):
        return jsonify({"ok": False, "error": "Send an event as a JSON object."}), 400
    result = analyze_event(event)
    return jsonify({"ok": True, "analysis": result})


@app.get("/api/demo-events")
def demo_events():
    now = datetime.now(timezone.utc).isoformat()
    demo = [
        {"event_type": "motion_detected", "device_name": "Front Door", "timestamp": now, "description": "Motion detected near the entrance"},
        {"event_type": "package_delivery", "device_name": "Front Door", "timestamp": now, "description": "Package delivery activity"},
        {"event_type": "device_status", "device_name": "Living Room", "timestamp": now, "description": "Routine device status update"},
    ]
    return jsonify({"ok": True, "events": [
        {**e, "guardian_analysis": analyze_event(e), "demo": True} for e in demo
    ]})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
