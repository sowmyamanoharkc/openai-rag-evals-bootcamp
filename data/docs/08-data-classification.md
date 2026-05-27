# Data Classification Policy

All data handled at Acme Corp falls into one of four classifications. The classification determines how data may be stored, shared, and processed.

## Levels

### Public

Information explicitly approved for public release. Examples: marketing pages, published blog posts, open-source projects, job listings.

- **Storage:** Anywhere.
- **Sharing:** No restrictions.

### Internal

Information that is not secret but is intended for Acme Corp employees and contractors only. Examples: internal documentation, org charts, non-sensitive Slack channels.

- **Storage:** Approved Acme Corp systems (Google Workspace, Confluence, GitHub, Slack).
- **Sharing:** With employees and contractors only. May be shared with external parties under an active NDA.

### Confidential

Information whose disclosure would harm Acme Corp or its customers. Examples: pre-release product roadmaps, sales pipeline data, individual performance reviews, source code.

- **Storage:** Approved Acme Corp systems with role-based access controls.
- **Sharing:** Strictly need-to-know. External sharing requires an NDA **and** Director approval.
- **Email:** May be sent over Acme email; must not be forwarded outside the company.

### Restricted

Information whose disclosure would cause severe harm. Examples: customer PII, payment data, authentication secrets, private keys, ML training data containing personal information.

- **Storage:** Only in systems explicitly designated for Restricted data. The current list is in the Security portal.
- **Sharing:** Need-to-know with documented approval from a VP or higher and Security.
- **Email:** Restricted data **must never be sent over email**, including encrypted email.
- **Personal devices:** Restricted data **must never** be stored on personal devices, even temporarily.

## Default classification

When in doubt, assume **Confidential**. Public and Restricted both require explicit designation.

## AI / LLM tools

Sending data to **external** AI/LLM tools (ChatGPT, Claude, Gemini, etc.) is governed by classification:

- **Public:** Allowed.
- **Internal:** Allowed only with the approved Acme Corp enterprise tools (which have data-retention agreements). Personal accounts are prohibited.
- **Confidential & Restricted:** Prohibited from any external LLM, including enterprise accounts.

## Reporting violations

If you believe Confidential or Restricted data has been mishandled, file a `data-incident` ticket immediately. Do not attempt to remediate the issue yourself before notifying Security.
