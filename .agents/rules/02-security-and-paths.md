---
name: security-and-paths
description: Security guidelines, secret protection, and path sanitation.
trigger: always_on
---
# Security & Path Protection Guidelines

1. **No Hardcoded Absolute Paths**:
   - Never commit absolute local filesystem paths (e.g. `<home>/<username>/` or `<Users>/<username>/`).
2. **No Secret Leaks**:
   - Never commit private keys, API tokens, or passphrases.
   - Use RAM-backed filesystem mounts (`/dev/shm`) for temporary secret processing.
3. **No Security Feature Downgrades**:
   - Agents are **STRICTLY FORBIDDEN** from disabling, weakening, or bypassing security, authentication, or authorization controls — for example switching `signInRequired`, `needs_authentication`, `verify`, `ssl_verify`, `check_permissions` or `authorized` to a falsy value, or skipping scope checks — to bypass test failures or browser verification roadblocks.
   - This rule is written WITHOUT the literal downgrade assignments on purpose: `check_security_downgrades` scans every added line, and a rule document that spelled out `<setting>=false` would flag itself on the commit that introduced it.
   - All authentication features and security parameters must remain intact and fully enforced.
4. **Branch Guard**:
   - Direct commits to `main`, `master`, or `staging` branches are strictly forbidden.

5. **PII & Secret Redaction in Logging**:
   - Never write PII, passwords, credentials, API tokens, or session keys to log files, stdout, or debug output.
