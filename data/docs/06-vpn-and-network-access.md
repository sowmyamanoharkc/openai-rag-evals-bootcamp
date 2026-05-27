# VPN and Network Access

## Default access model

Acme Corp uses a **zero-trust network architecture**. Most internal applications are accessed via the corporate identity provider (SSO) and do not require a VPN. The VPN is only required for:

1. SSH access to non-production infrastructure.
2. Database admin tooling (DBeaver, pgAdmin, mysql-cli).
3. Internal-only services that have not yet migrated to SSO. The current list is in the IT portal under **"VPN-only services"**.

## Approved VPN client

The only approved VPN client is **Acme VPN 2.x** (a Tailscale-based client). It is auto-installed on all Acme-issued laptops via the device management agent. Personal devices may install Acme VPN 2.x only after enrolling in the BYOD program; see Security for enrollment.

OpenVPN, WireGuard, and other clients are **not** approved for accessing Acme resources.

## MFA on VPN connection

Every VPN session requires a fresh MFA challenge (push notification or hardware token). VPN sessions automatically expire after **8 hours** of continuous use; you must reauthenticate at that point.

## Production access

Production environments are **never** accessible from the standard VPN. Access requires:

1. Membership in the relevant on-call group, **or** an approved time-bound access ticket.
2. Connection through the production bastion service (`bastion.prod.acme.internal`).
3. A hardware MFA token (YubiKey or equivalent). Software TOTP is not accepted for production.

All production sessions are recorded.

## Foreign country access

Connecting to Acme VPN from a country other than your normal country of work is allowed for trips up to 30 days (see Remote Work Policy). The VPN may automatically block connections from countries on the **restricted list** (the current list is maintained by Security). Access from a restricted country requires a 7-day-advance ticket to Security.

## Reporting connectivity issues

For VPN or network issues, file a ticket in the **IT** queue with the tag `vpn`. Include your VPN client version, OS version, and any error messages.
