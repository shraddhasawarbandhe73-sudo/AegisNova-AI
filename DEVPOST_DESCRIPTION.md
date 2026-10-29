# AegisNova AI — AI-Powered Caregiver Event Awareness

## What it does
AegisNova AI is a caregiver-oriented event-awareness prototype. It turns event metadata into an easy-to-review summary, a priority label, a reason for that label, and a suggested next step. It is designed to help a human review activity—not to make medical or emergency decisions.

## How it works
1. A user loads clearly labelled simulated demo events or an authorized event source.
2. The Flask backend sends event metadata to an NVIDIA Nemotron model through the Nebius Token Factory API when a valid key and model access are configured.
3. The model returns a constrained JSON response with a priority, summary, reason, and suggested action.
4. The dashboard displays the output for human review. A transparent rule-based fallback keeps local demo mode usable if the model API is not configured or unavailable.

## Nebius and NVIDIA usage
The hackathon edition adds a runtime call to Nebius Token Factory's OpenAI-compatible chat completions endpoint and is configured by default for `nvidia/nemotron-3-super-120b-a12b`. The exact model availability and successful live inference must be verified using the submitter's own Token Factory account before submission.

## What changed during the hackathon
- Added Nebius Token Factory API configuration and NVIDIA Nemotron model support.
- Added structured AI summaries, reasons, and suggested next steps.
- Added API status reporting and graceful fallback behavior.
- Updated setup documentation and secret-handling guidance.

## Limitations
This prototype does not confirm falls, diagnose medical conditions, or provide emergency response. Demo events are simulated. Model outputs can be wrong and must be checked by a person. Live integrations must only be claimed when configured and tested.

## Before submitting
Replace this draft with details from your actual test, include the working public demo URL, public repository URL, and demo video URL, and describe only features that you personally verified.
