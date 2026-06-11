# SkillSpector Security Report

**Skill:** unknown  
**Source:** `chapters/mobile/skills/flutter/flutter-release-automation`  
**Scanned:** 2026-06-03 17:43:51 UTC  

## Risk Assessment

| Metric | Value |
|--------|-------|
| Score | 100/100 |
| Severity | CRITICAL |
| Recommendation | DO NOT INSTALL |

## Components (8)

| File | Type | Lines | Executable |
|------|------|-------|------------|
| `SKILL.md` | markdown | 226 | No |
| `assets/release_workflow.yml` | yaml | 325 | No |
| `evals/flutter-release-automation.md` | markdown | 176 | No |
| `references/azure_devops.md` | markdown | 414 | No |
| `references/cd_strategy.md` | markdown | 558 | No |
| `references/fastlane_signing.md` | markdown | 471 | No |
| `references/github_actions.md` | markdown | 464 | No |
| `references/jenkins.md` | markdown | 428 | No |

## Issues (15)

### 🟡 MEDIUM: E1

**Location:** `references/azure_devops.md:19`  
**Confidence:** 50%  

**Message:** External Transmission

**Remediation:** Verify the destination URL is trusted and necessary. Remove or replace with documented APIs. Ensure no secrets, tokens, or PII are transmitted.

---

### 🟡 MEDIUM: E1

**Location:** `references/github_actions.md:26`  
**Confidence:** 50%  

**Message:** External Transmission

**Remediation:** Verify the destination URL is trusted and necessary. Remove or replace with documented APIs. Ensure no secrets, tokens, or PII are transmitted.

---

### 🟡 MEDIUM: E1

**Location:** `references/jenkins.md:28`  
**Confidence:** 50%  

**Message:** External Transmission

**Remediation:** Verify the destination URL is trusted and necessary. Remove or replace with documented APIs. Ensure no secrets, tokens, or PII are transmitted.

---

### 🟡 MEDIUM: PE2

**Location:** `assets/release_workflow.yml:79`  
**Confidence:** 70%  

**Message:** Sudo/Root Execution

**Remediation:** Avoid sudo/root unless strictly required. Prefer least-privilege patterns. If elevation is needed, document the justification and scope.

---

### 🟡 MEDIUM: PE2

**Location:** `references/azure_devops.md:178`  
**Confidence:** 70%  

**Message:** Sudo/Root Execution

**Remediation:** Avoid sudo/root unless strictly required. Prefer least-privilege patterns. If elevation is needed, document the justification and scope.

---

### 🟡 MEDIUM: PE2

**Location:** `references/github_actions.md:139`  
**Confidence:** 70%  

**Message:** Sudo/Root Execution

**Remediation:** Avoid sudo/root unless strictly required. Prefer least-privilege patterns. If elevation is needed, document the justification and scope.

---

### 🟡 MEDIUM: PE2

**Location:** `references/jenkins.md:177`  
**Confidence:** 70%  

**Message:** Sudo/Root Execution

**Remediation:** Avoid sudo/root unless strictly required. Prefer least-privilege patterns. If elevation is needed, document the justification and scope.

---

### 🟡 MEDIUM: PE2

**Location:** `references/jenkins.md:412`  
**Confidence:** 70%  

**Message:** Sudo/Root Execution

**Remediation:** Avoid sudo/root unless strictly required. Prefer least-privilege patterns. If elevation is needed, document the justification and scope.

---

### 🟡 MEDIUM: RA2

**Location:** `evals/flutter-release-automation.md:124`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `evals/flutter-release-automation.md:135`  
**Confidence:** 75%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `references/fastlane_signing.md:16`  
**Confidence:** 90%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🟡 MEDIUM: RA2

**Location:** `references/github_actions.md:35`  
**Confidence:** 60%  

**Message:** Session Persistence

**Remediation:** Remove any persistence mechanisms (cron jobs, startup scripts, state files). Skills should not maintain state across sessions without explicit user consent.

---

### 🔴 HIGH: TM2

**Location:** `assets/release_workflow.yml:78`  
**Confidence:** 75%  

**Message:** Chaining Abuse

**Remediation:** Limit tool chaining depth and validate the output of each tool before passing it to the next. Require explicit user approval for multi-step chains.

---

### 🔴 HIGH: TM2

**Location:** `references/azure_devops.md:177`  
**Confidence:** 75%  

**Message:** Chaining Abuse

**Remediation:** Limit tool chaining depth and validate the output of each tool before passing it to the next. Require explicit user approval for multi-step chains.

---

### 🔴 HIGH: TM2

**Location:** `references/github_actions.md:138`  
**Confidence:** 75%  

**Message:** Chaining Abuse

**Remediation:** Limit tool chaining depth and validate the output of each tool before passing it to the next. Require explicit user approval for multi-step chains.

---

## Metadata

- **Executable Scripts:** No

*Generated by SkillSpector v2.0.0*