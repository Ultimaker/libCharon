---
name: owasp-security
description: OWASP security standards selected for this repository's detected stack profile.
trigger: always_on
---
# OWASP Security Guidelines (Profile-Matched)

These sections were selected because the bootstrap investigation detected the matching stack. Enforcement is layered: these rules guide implementation, pre-commit hooks block secrets/paths mechanically, and `scripts/verify_and_create_pr.sh` runs the adversarial audit before any PR.

## OWASP IoT Top 10 (Firmware / Device Software)

1. **No Hardcoded Credentials**: Zero hardcoded passwords, private keys, API tokens, or HMAC secrets. Load signing/decryption keys from GCP Secret Manager or RAM-backed `/dev/shm` tmpfs mounts.
2. **Secure Network Services**: Exposed ports require TLS. Local IPC/DBus endpoints must authenticate callers and enforce interface permissions.
3. **Secure Update Mechanism**: Firmware SWU updates require detached GPG signatures. NEVER bypass signature verification in update scripts.
4. **Privacy Protection & Log Redaction**: Never write PII, passwords, WiFi credentials, API tokens, or session keys to system journal, service logs, or debug output. Any variable processed with `libLogger` in Python code that can contain PII or secrets MUST be wrapped using `SecretString` ([libLogger/secretString.py](https://github.com/Ultimaker/libLogger/blob/main/libLogger/secretString.py)) and filtered through `RedactingFilter` ([libLogger/redactingFilter.py](https://github.com/Ultimaker/libLogger/blob/main/libLogger/redactingFilter.py)).
5. **Secure Data Storage**: Temporary sensitive decryption targets live on RAM-backed filesystems (`/dev/shm`), never on persistent storage.
6. **Secure Defaults**: SSH disabled by default, random per-device passwords, minimal open ports.
