# MeshBot

MeshBot is an offline, low-bandwidth field information assistant designed for parks departments, trail systems, and other public-land operators that need a resilient communication layer where cellular coverage is weak or unavailable.

This repository is now positioned as a product MVP rather than a hackathon script. It includes configurable runtime settings, safer default prompt behavior, deployment documentation, and product-facing materials to support pilot conversations with US parks agencies.

## Product positioning

MeshBot is intended to help agencies provide limited offline guidance over Meshtastic-compatible LoRa networks.

Core value:
- Extend basic public guidance into dead zones without relying on cellular or cloud connectivity.
- Offer concise offline support for safety, navigation principles, first aid basics, and environmental hazards.
- Operate on low-power hardware that can be placed at trailheads, ranger stations, maintenance vehicles, or elevated relay points.

Important limitation:
- MeshBot is not a replacement for rangers, emergency dispatch, official signage, maps, weather alerts, or licensed medical direction.

## What is in this repo

- [main.py](main.py): the configurable Meshtastic listener and Ollama client.
- [config.example.json](config.example.json): example deployment settings.
- [requirements.txt](requirements.txt): Python dependency list.
- [PRODUCT_BRIEF.md](PRODUCT_BRIEF.md): buyer-facing product framing and pilot model.
- [SAFETY_AND_COMPLIANCE.md](SAFETY_AND_COMPLIANCE.md): safety, privacy, and procurement considerations.

## Current MVP architecture

1. A Meshtastic device receives inbound text messages over LoRa.
2. A local computer or edge device runs MeshBot and forwards the text to a local Ollama model.
3. The model produces a short answer under strict offline and safety constraints.
4. MeshBot chunks the response and sends it back over Meshtastic.

## Product readiness improvements already made

- External configuration via JSON instead of hard-coded serial port and model values.
- Structured logging for operations and troubleshooting.
- Request timeout handling and safer subprocess error handling.
- Basic message filtering to ignore slash-command style traffic.
- Response chunking that avoids breaking words mid-message when possible.
- Product-oriented default system prompt aimed at parks-department deployments.

## Local setup

Prerequisites:
- Python 3.10+
- Meshtastic CLI installed and available on the system path
- Ollama installed locally with a supported model pulled, for example `phi3:mini`
- A connected Meshtastic-compatible radio

Install:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item config.example.json config.json
```

Update [config.example.json](config.example.json) values in your local [config.json](config.json) copy:
- Set the correct serial port.
- Set the target Meshtastic channel index.
- Set the Ollama model that is actually installed on the device.

Run:

```powershell
python main.py --config config.json
```

## Recommended parks-department pilot package

- One trailhead or backcountry-zone deployment
- One edge compute unit such as Raspberry Pi 5 or equivalent
- One Meshtastic radio node with weather-resistant enclosure
- Solar or battery-backed power system sized for local conditions
- Pre-approved prompt and content policy reviewed by agency staff
- Short operational playbook for seasonal staff and volunteers

## Commercialization gaps still to close

This repository is materially better than the original prototype, but it is not yet a sellable production system by itself.

Still needed before broad agency rollout:
- Hardware enclosure and environmental testing
- Fleet management and remote software update path
- Authentication and channel-governance model
- Better audit logging and incident review workflow
- Curated park-specific knowledge packs instead of general-purpose prompting alone
- Formal legal review of claims, disclaimers, privacy posture, and procurement language
- Test coverage and a repeatable deployment process

## Recommended next steps

1. Run a controlled pilot with one specific park or trail network.
2. Replace the generic model prompt with a park-approved content pack and escalation rules.
3. Add telemetry, health monitoring, and administrative controls.
4. Package the hardware, software, SOPs, and support plan as a single procurement-ready offering.


