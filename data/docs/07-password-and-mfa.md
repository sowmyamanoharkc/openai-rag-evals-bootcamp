# Password and Multi-Factor Authentication Policy

## Password requirements

All Acme Corp accounts must use a password that meets the following criteria:

- Minimum length: **14 characters**.
- Must include at least 3 of: uppercase letters, lowercase letters, digits, symbols.
- Must not match any password used on the account in the previous 365 days.
- Must not appear in the **HaveIBeenPwned** breached-password database (checked automatically at password change).

Passwords are not required to be rotated on a fixed schedule. **Mandatory rotation is triggered only by:**

- A confirmed breach of the account.
- A change in role with elevated privileges.
- The annual security review for service accounts.

## Password manager

Acme Corp issues every employee a license to **1Password Business**. All work-related credentials must be stored in 1Password. Storing work credentials in browser password managers, plain text files, or sticky notes is prohibited.

## Multi-Factor Authentication (MFA)

MFA is **mandatory** on every Acme Corp account, with no exceptions. Approved second factors, in order of preference:

1. **Hardware security key** (YubiKey 5 series or equivalent FIDO2 device) — preferred and required for production access.
2. **Push notification** (Acme MFA mobile app).
3. **TOTP code** (1Password, Authy, Google Authenticator).

**SMS-based MFA is not approved** and is being phased out for legacy accounts by March 31, 2026.

## Lost or stolen second factor

If your hardware key or phone is lost or stolen, contact the **Security helpdesk** immediately (24/7 line listed in the IT portal). They will revoke the device and issue a temporary recovery factor. You must visit IT in person or complete an identity verification call within **48 hours** to receive a permanent replacement.

## Service accounts

Service accounts must use a 30+ character random password rotated every **90 days**. Interactive logins are disabled. Service-account credentials must never be shared between humans or stored in source control.
