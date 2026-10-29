# AegisNova AI — Nebius × NVIDIA Hackathon Edition

AegisNova AI is a caregiver event-awareness prototype. This edition adds an **AI Safety Event Analyzer** that can call an NVIDIA Nemotron model through the Nebius Token Factory OpenAI-compatible API. It produces a short event summary, a priority label, a reason, and a cautious suggested next step.

## What is implemented
- Flask web app and responsive dashboard.
- AI analysis route: `POST /api/analyze`.
- Nebius Token Factory integration using `NEBIUS_API_KEY` and configurable model ID.
- Default model: `nvidia/nemotron-3-super-120b-a12b` (confirm availability in your Token Factory account/model catalog).
- Clearly labelled simulated demo events.
- Transparent local rule-based fallback if no Nebius key is configured or the API call fails.
- Optional legacy Ring event endpoints and optional Amazon Bedrock path.
- API-key protection guidance and `.gitignore` excludes `.env`.

## Important: configure and test before submission
This ZIP contains code, **not an API key, hosted demo, or verified live model response**. To meet the hackathon requirement, you must configure your own Nebius Token Factory key, run a live analysis request, and provide a working hosted demo or test build. Do not claim a live Nemotron integration until you have tested it successfully.

## Run on Windows
1. Install Python 3.10+.
2. Extract the ZIP.
3. Double-click `RUN_AEGISNOVA AI.bat` (it installs dependencies and creates `.env` from `.env.example` on first run).
4. Open `.env` in Notepad and paste your key after `NEBIUS_API_KEY=`. Keep this file private.
5. Save `.env`, close the app window if it is already running, then run `RUN_AEGISNOVA AI.bat` again.
6. Browser opens at `http://127.0.0.1:5000`.
7. Click **Use Demo Events**, then use **Analyze Test Event** to verify a model response.

## Configure Nebius Token Factory
- Create an API key in your Nebius Token Factory account.
- In `.env`, set:
  - `NEBIUS_API_KEY=your_private_key`
  - `NEBIUS_BASE_URL=https://api.tokenfactory.us-central1.nebius.com/v1/chat/completions`
  - `NEBIUS_MODEL=nvidia/nemotron-3-super-120b-a12b`
- Confirm that this model is available to your account. You can change `NEBIUS_MODEL` to an NVIDIA open model that is currently listed in your Token Factory account.
- The backend calls the Token Factory API at runtime. If the call fails, the dashboard shows the fallback method; this is not proof of live model use.

## Routes
- `GET /` — dashboard
- `GET /api/status` — integration status
- `GET /api/demo-events` — simulated events
- `POST /api/analyze` — analyze JSON event metadata
- `GET /api/devices` — optional Ring device discovery
- `GET /api/events?device_id=...` — optional Ring event history

Example test request (with app running):
```bash
curl -X POST http://127.0.0.1:5000/api/analyze -H "Content-Type: application/json" -d "{"event_type":"motion_detected","description":"Motion near the entrance"}"
```

## Security
- Never upload `.env`, API keys, Ring tokens, AWS credentials, or private footage to GitHub.
- If a key was previously committed publicly, revoke/rotate it immediately.
- Only use data and integrations you are authorized to access.

## Safety limitations
AegisNova AI is an experimental awareness prototype, not a medical device, fall detector, or emergency service. Event metadata may be incomplete or misleading. AI-generated text can be wrong; always verify the event and make human decisions. Demo events are simulated and must not be presented as real incidents.

## Hackathon submission checklist
- [ ] Confirm age and country eligibility in the official rules.
- [ ] Configure a Nebius Token Factory key and verify the app makes a successful runtime call to an NVIDIA open-source model.
- [ ] Run and test the app; record actual output, not a mock response.
- [ ] Deploy a publicly accessible demo/test build and provide its URL.
- [ ] Keep this repository public and ensure an open-source license is visible on GitHub.
- [ ] Record a public YouTube demo shorter than 3 minutes showing the working app and the actual AI call.
- [ ] Explain exactly what changed in this edition compared with the earlier AegisNova AI project.
- [ ] Complete the required tool feedback in Devpost honestly.

Official rules: https://nebiusglobalaihackathon.devpost.com/rules
