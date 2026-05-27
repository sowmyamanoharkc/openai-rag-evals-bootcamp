# Security Incident Response

## What counts as a security incident?

Any of the following must be reported as an incident:

- Lost, stolen, or unrecoverable Acme equipment.
- Suspected phishing email *clicked* (not just received).
- Malware detected on an Acme device.
- Suspicious account behavior (unexpected logins, unfamiliar 2FA prompts).
- Suspected exposure of Confidential or Restricted data.
- Any unauthorized physical access to an Acme office area.

When in doubt, report. The Security team prefers many false alarms over a single missed real incident.

## How to report

There are two reporting channels, depending on severity:

| Severity | Channel | Response SLA |
|---|---|---|
| **Critical** (active breach, data leak in progress) | Call the Security 24/7 hotline (number in IT portal). | 5 minutes |
| **All other** | File a `security-incident` ticket. | 1 business hour |

**Do not** discuss the suspected incident in public Slack channels. Use the `#security-private` channel or direct message a Security team member.

## What happens after you report

1. **Triage (≤ 1 hour):** Security on-call assesses severity and assigns an Incident Commander (IC).
2. **Containment:** The IC may isolate devices, disable accounts, or rotate credentials. Cooperate fully — speed matters.
3. **Investigation:** The IC and forensics team determine scope and root cause. You will be asked to provide a written timeline of your actions.
4. **Resolution & comms:** Affected systems are restored. If customer data was involved, customer notification is led by Legal.
5. **Postmortem:** A blameless postmortem is published within **10 business days** for all incidents of severity High or above. You may be invited to contribute.

## Phishing — special handling

If you **clicked a suspicious link or attachment**, even if you did not enter credentials:

1. Disconnect the device from the network (turn off Wi-Fi / unplug Ethernet).
2. Do **not** shut the device down — Security needs the in-memory state.
3. Call the Security hotline.

If you only **received** a phishing email and did not interact with it, forward it as an attachment to `phishing@acme.example` and delete it. No ticket is required.

## Confidentiality during investigation

You may not discuss an active incident with anyone outside the explicit incident channel. This includes social media, friends, family, and other Acme employees. Violations of incident confidentiality are a serious disciplinary matter.
