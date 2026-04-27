# Safety and Compliance Notes

## Purpose

This document is a starting point for preparing MeshBot for procurement review by US parks departments. It is not legal advice.

## Claims discipline

MeshBot should be marketed as:
- An offline informational aid
- A resilience tool for low-connectivity areas
- A supplement to existing public-safety communications

MeshBot should not be marketed as:
- A guaranteed emergency communications system
- A substitute for licensed medical, legal, or law-enforcement direction
- A real-time alerting platform unless backed by actual integrated data feeds

## Safety guardrails

Minimum safety posture:
- Always state that the system has no live internet or dispatch access.
- Encourage direct contact with rangers or emergency responders whenever available.
- Keep responses short and procedural.
- Avoid confidence inflation and avoid invented facts.
- Escalate language when users describe imminent danger.

## Privacy posture

Before sale, decide and document:
- Whether message content is logged
- How long logs are retained
- Whether logs include device identifiers or only message text
- Who can retrieve logs and under what authority
- Whether any data ever leaves the device or park network

For many agencies, the simplest and strongest initial posture is:
- Local-only processing
- Minimal retained logs
- Clear retention policy
- No cloud dependency by default

## Security posture

Before production rollout, add:
- Device hardening baseline
- Controlled update process
- Radio channel governance and key rotation policy
- Physical tamper response procedure
- Access control for maintenance staff

## Accessibility and public communication

Parks departments may ask for:
- Plain-language disclaimers
- Multilingual support considerations
- Signage wording at installation sites
- Public notice about limitations and emergency alternatives

## Procurement readiness checklist

- Defined hardware bill of materials
- Installation and maintenance SOP
- Support and replacement plan
- Known limitations statement
- Pilot reporting template
- Privacy statement
- Security baseline
- Insurance and liability review

## Operational recommendation

Do not deploy the current MVP as a fully autonomous public-safety product without:
- Hardware validation
- Field testing in realistic terrain
- Agency-reviewed prompt rules
- A written incident escalation policy