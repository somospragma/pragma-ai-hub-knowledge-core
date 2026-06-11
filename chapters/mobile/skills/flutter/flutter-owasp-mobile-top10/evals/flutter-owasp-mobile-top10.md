# SkillSpector Security Report

**Skill:** unknown  
**Source:** `chapters/mobile/skills/flutter/flutter-owasp-mobile-top10`  
**Scanned:** 2026-06-03 17:43:39 UTC  

## Risk Assessment

| Metric | Value |
|--------|-------|
| Score | 100/100 |
| Severity | CRITICAL |
| Recommendation | DO NOT INSTALL |

## Components (16)

| File | Type | Lines | Executable |
|------|------|-------|------------|
| `SKILL.md` | markdown | 466 | No |
| `evals/flutter-owasp-mobile-top10.md` | markdown | 569 | No |
| `references/m1-platform.md` | markdown | 314 | No |
| `references/m10-extraneous.md` | markdown | 346 | No |
| `references/m2-storage.md` | markdown | 223 | No |
| `references/m3-communication.md` | markdown | 203 | No |
| `references/m4-authentication.md` | markdown | 218 | No |
| `references/m5-cryptography.md` | markdown | 232 | No |
| `references/m6-authorization.md` | markdown | 217 | No |
| `references/m7-code-quality.md` | markdown | 293 | No |
| `references/m8-tampering.md` | markdown | 284 | No |
| `references/m9-reverse-engineering.md` | markdown | 193 | No |
| `references/owasp_masvs_checklist.md` | markdown | 235 | No |
| `references/owasp_scan_script.md` | markdown | 268 | No |
| `references/quick-reference.md` | markdown | 245 | No |
| `scripts/owasp_scan.sh` | shell | 229 | Yes |

## Issues (66)

### 🟡 MEDIUM: E1

**Location:** `SKILL.md:268`  
**Confidence:** 50%  

**Message:** External Transmission

**Remediation:** Verify the destination URL is trusted and necessary. Remove or replace with documented APIs. Ensure no secrets, tokens, or PII are transmitted.

---

### 🟡 MEDIUM: E1

**Location:** `references/m2-storage.md:176`  
**Confidence:** 50%  

**Message:** External Transmission

**Remediation:** Verify the destination URL is trusted and necessary. Remove or replace with documented APIs. Ensure no secrets, tokens, or PII are transmitted.

---

### 🟡 MEDIUM: E1

**Location:** `references/m4-authentication.md:35`  
**Confidence:** 50%  

**Message:** External Transmission

**Remediation:** Verify the destination URL is trusted and necessary. Remove or replace with documented APIs. Ensure no secrets, tokens, or PII are transmitted.

---

### 🟡 MEDIUM: E1

**Location:** `references/m6-authorization.md:41`  
**Confidence:** 50%  

**Message:** External Transmission

**Remediation:** Verify the destination URL is trusted and necessary. Remove or replace with documented APIs. Ensure no secrets, tokens, or PII are transmitted.

---

### 🟡 MEDIUM: E1

**Location:** `references/m9-reverse-engineering.md:157`  
**Confidence:** 50%  

**Message:** External Transmission

**Remediation:** Verify the destination URL is trusted and necessary. Remove or replace with documented APIs. Ensure no secrets, tokens, or PII are transmitted.

---

### 🟡 MEDIUM: EA2

**Location:** `evals/flutter-owasp-mobile-top10.md:99`  
**Confidence:** 85%  

**Message:** Autonomous Decision Making

**Remediation:** Add human-in-the-loop confirmation for destructive, irreversible, or high-impact operations. Never auto-execute commands that modify files, send data, or alter system state.

---

### 🟡 MEDIUM: EA2

**Location:** `references/owasp_masvs_checklist.md:185`  
**Confidence:** 75%  

**Message:** Autonomous Decision Making

**Remediation:** Add human-in-the-loop confirmation for destructive, irreversible, or high-impact operations. Never auto-execute commands that modify files, send data, or alter system state.

---

### 🔴 HIGH: PE3

**Location:** `references/m2-storage.md:25`  
**Confidence:** 70%  

**Message:** Credential Access

**Remediation:** Remove references to credential paths. Use environment variables or secrets managers. For docs, use placeholder paths (e.g., /path/to/config). Never load .env or token files in production code paths.

---

### 🔴 HIGH: PE3

**Location:** `references/m2-storage.md:53`  
**Confidence:** 70%  

**Message:** Credential Access

**Remediation:** Remove references to credential paths. Use environment variables or secrets managers. For docs, use placeholder paths (e.g., /path/to/config). Never load .env or token files in production code paths.

---

### 🔴 HIGH: PE3

**Location:** `references/m4-authentication.md:77`  
**Confidence:** 70%  

**Message:** Credential Access

**Remediation:** Remove references to credential paths. Use environment variables or secrets managers. For docs, use placeholder paths (e.g., /path/to/config). Never load .env or token files in production code paths.

---

### 🔴 HIGH: PE3

**Location:** `references/owasp_masvs_checklist.md:16`  
**Confidence:** 70%  

**Message:** Credential Access

**Remediation:** Remove references to credential paths. Use environment variables or secrets managers. For docs, use placeholder paths (e.g., /path/to/config). Never load .env or token files in production code paths.

---

### 🔴 HIGH: PE3

**Location:** `references/owasp_masvs_checklist.md:41`  
**Confidence:** 70%  

**Message:** Credential Access

**Remediation:** Remove references to credential paths. Use environment variables or secrets managers. For docs, use placeholder paths (e.g., /path/to/config). Never load .env or token files in production code paths.

---

### 🔴 HIGH: PE3

**Location:** `references/owasp_masvs_checklist.md:50`  
**Confidence:** 70%  

**Message:** Credential Access

**Remediation:** Remove references to credential paths. Use environment variables or secrets managers. For docs, use placeholder paths (e.g., /path/to/config). Never load .env or token files in production code paths.

---

### 🔴 HIGH: PE3

**Location:** `references/owasp_masvs_checklist.md:69`  
**Confidence:** 70%  

**Message:** Credential Access

**Remediation:** Remove references to credential paths. Use environment variables or secrets managers. For docs, use placeholder paths (e.g., /path/to/config). Never load .env or token files in production code paths.

---

### 🔴 HIGH: P2

**Location:** `SKILL.md:276`  
**Confidence:** 70%  

**Message:** Hidden Instructions

**Remediation:** Audit all comments and invisible characters. Remove any instructions that direct the agent to perform unauthorized actions. Use plain, reviewable content.

---

### 🔴 HIGH: P2

**Location:** `references/m1-platform.md:40`  
**Confidence:** 70%  

**Message:** Hidden Instructions

**Remediation:** Audit all comments and invisible characters. Remove any instructions that direct the agent to perform unauthorized actions. Use plain, reviewable content.

---

### 🔴 HIGH: P2

**Location:** `references/m3-communication.md:43`  
**Confidence:** 70%  

**Message:** Hidden Instructions

**Remediation:** Audit all comments and invisible characters. Remove any instructions that direct the agent to perform unauthorized actions. Use plain, reviewable content.

---

### 🔴 HIGH: P2

**Location:** `references/m3-communication.md:87`  
**Confidence:** 70%  

**Message:** Hidden Instructions

**Remediation:** Audit all comments and invisible characters. Remove any instructions that direct the agent to perform unauthorized actions. Use plain, reviewable content.

---

### 🟡 MEDIUM: RA2

**Location:** `SKILL.md:261`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `evals/flutter-owasp-mobile-top10.md:231`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `evals/flutter-owasp-mobile-top10.md:242`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `evals/flutter-owasp-mobile-top10.md:253`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `evals/flutter-owasp-mobile-top10.md:264`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `evals/flutter-owasp-mobile-top10.md:275`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `evals/flutter-owasp-mobile-top10.md:286`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `evals/flutter-owasp-mobile-top10.md:297`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `evals/flutter-owasp-mobile-top10.md:308`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `evals/flutter-owasp-mobile-top10.md:319`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `evals/flutter-owasp-mobile-top10.md:330`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `evals/flutter-owasp-mobile-top10.md:341`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `evals/flutter-owasp-mobile-top10.md:352`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `evals/flutter-owasp-mobile-top10.md:363`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `evals/flutter-owasp-mobile-top10.md:374`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `evals/flutter-owasp-mobile-top10.md:385`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `evals/flutter-owasp-mobile-top10.md:396`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `evals/flutter-owasp-mobile-top10.md:407`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `references/m1-platform.md:114`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `references/m1-platform.md:116`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `references/m1-platform.md:263`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `references/m1-platform.md:288`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `references/m3-communication.md:11`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `references/m5-cryptography.md:218`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `references/owasp_scan_script.md:34`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `references/owasp_scan_script.md:129`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `references/owasp_scan_script.md:130`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `references/quick-reference.md:40`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `references/quick-reference.md:41`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `references/quick-reference.md:117`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `references/quick-reference.md:232`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `scripts/owasp_scan.sh:23`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `scripts/owasp_scan.sh:114`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `scripts/owasp_scan.sh:115`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: TM3

**Location:** `SKILL.md:143`  
**Confidence:** 80%  

**Message:** Unsafe Defaults

**Remediation:** Override unsafe defaults with secure settings (verify=True, auth required, restrictive permissions). Review and harden all tool configurations.

---

### 🟡 MEDIUM: TM3

**Location:** `SKILL.md:143`  
**Confidence:** 80%  

**Message:** Unsafe Defaults

**Remediation:** Override unsafe defaults with secure settings (verify=True, auth required, restrictive permissions). Review and harden all tool configurations.

---

### 🟡 MEDIUM: TM3

**Location:** `references/m10-extraneous.md:69`  
**Confidence:** 80%  

**Message:** Unsafe Defaults

**Remediation:** Override unsafe defaults with secure settings (verify=True, auth required, restrictive permissions). Review and harden all tool configurations.

---

### 🟡 MEDIUM: TM3

**Location:** `references/m10-extraneous.md:69`  
**Confidence:** 80%  

**Message:** Unsafe Defaults

**Remediation:** Override unsafe defaults with secure settings (verify=True, auth required, restrictive permissions). Review and harden all tool configurations.

---

### 🟡 MEDIUM: TM3

**Location:** `references/owasp_masvs_checklist.md:72`  
**Confidence:** 80%  

**Message:** Unsafe Defaults

**Remediation:** Override unsafe defaults with secure settings (verify=True, auth required, restrictive permissions). Review and harden all tool configurations.

---

### 🟡 MEDIUM: TM3

**Location:** `references/owasp_masvs_checklist.md:72`  
**Confidence:** 80%  

**Message:** Unsafe Defaults

**Remediation:** Override unsafe defaults with secure settings (verify=True, auth required, restrictive permissions). Review and harden all tool configurations.

---

### 🟡 MEDIUM: TM3

**Location:** `references/owasp_masvs_checklist.md:78`  
**Confidence:** 80%  

**Message:** Unsafe Defaults

**Remediation:** Override unsafe defaults with secure settings (verify=True, auth required, restrictive permissions). Review and harden all tool configurations.

---

### 🟡 MEDIUM: TM3

**Location:** `references/owasp_masvs_checklist.md:78`  
**Confidence:** 80%  

**Message:** Unsafe Defaults

**Remediation:** Override unsafe defaults with secure settings (verify=True, auth required, restrictive permissions). Review and harden all tool configurations.

---

### 🟡 MEDIUM: TM3

**Location:** `references/owasp_scan_script.md:80`  
**Confidence:** 80%  

**Message:** Unsafe Defaults

**Remediation:** Override unsafe defaults with secure settings (verify=True, auth required, restrictive permissions). Review and harden all tool configurations.

---

### 🟡 MEDIUM: TM3

**Location:** `references/owasp_scan_script.md:80`  
**Confidence:** 80%  

**Message:** Unsafe Defaults

**Remediation:** Override unsafe defaults with secure settings (verify=True, auth required, restrictive permissions). Review and harden all tool configurations.

---

### 🟡 MEDIUM: TM3

**Location:** `references/quick-reference.md:81`  
**Confidence:** 80%  

**Message:** Unsafe Defaults

**Remediation:** Override unsafe defaults with secure settings (verify=True, auth required, restrictive permissions). Review and harden all tool configurations.

---

### 🟡 MEDIUM: TM3

**Location:** `references/quick-reference.md:81`  
**Confidence:** 80%  

**Message:** Unsafe Defaults

**Remediation:** Override unsafe defaults with secure settings (verify=True, auth required, restrictive permissions). Review and harden all tool configurations.

---

### 🟡 MEDIUM: TM3

**Location:** `scripts/owasp_scan.sh:67`  
**Confidence:** 80%  

**Message:** Unsafe Defaults

**Remediation:** Override unsafe defaults with secure settings (verify=True, auth required, restrictive permissions). Review and harden all tool configurations.

---

### 🟡 MEDIUM: TM3

**Location:** `scripts/owasp_scan.sh:67`  
**Confidence:** 80%  

**Message:** Unsafe Defaults

**Remediation:** Override unsafe defaults with secure settings (verify=True, auth required, restrictive permissions). Review and harden all tool configurations.

---

## Metadata

- **Executable Scripts:** Yes

*Generated by SkillSpector v2.0.0*