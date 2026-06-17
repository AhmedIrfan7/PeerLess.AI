# PEERLESS.AI — Safety & Legal Policy

> **This document is binding for all developers, contributors, and operators of PEERLESS.AI.**
> Any change to these policies must be reviewed, approved, and committed as a `docs:` commit referencing the reason for amendment.

---

## 1. Core Safety Philosophy

PEERLESS.AI is a **decision-support tool**, not a decision-making tool. It is designed to surface concerns that warrant expert human attention — it is not designed to render verdicts.

The distinction matters legally and ethically:

- A **flag** says: *"This pattern may be worth investigating."*
- An **accusation** says: *"This person did something wrong."*

PEERLESS.AI only ever produces flags. It never produces accusations.

---

## 2. Mandatory UI Disclosures

These disclosures are **not optional**. They must appear in the UI at all times, cannot be dismissed permanently, and must survive any redesign.

### 2.1 Per-Finding Label
Every single finding rendered in the report view **must** be prefixed with:

```
⚠️  Flagged concern — pending human review.
```

This label must be visually distinct (e.g., amber/yellow accent) and must appear before the finding content, not after it.

### 2.2 Report-Level Disclaimer
The following disclaimer must appear at the **top of every report page**, above the fold, before any findings are shown:

```
PEERLESS.AI surfaces possible concerns for expert review.
It does not adjudicate misconduct. Findings are not conclusions.
```

This disclaimer must be styled as a prominent banner (not fine print). It must not be hidden behind a toggle.

### 2.3 Export Disclaimer
Any exported document (PDF, JSON, CSV) must include the full report-level disclaimer text in its header section.

---

## 3. Prohibited Actions (Hard Constraints)

The following actions are **categorically prohibited** in all versions of PEERLESS.AI, including internal builds:

| # | Prohibited Action | Why |
|---|------------------|-----|
| 1 | Automatically sending email to any author, editor, or institution | Risk of reputational harm before human review |
| 2 | Automatically posting findings to any public platform or API | Findings are unreviewed drafts; public exposure before approval violates the core principle |
| 3 | Logging or storing author personal data beyond what is required for the session | Privacy; GDPR compliance |
| 4 | Sharing findings outside the authenticated session without explicit human export action | Confidentiality |
| 5 | Presenting a finding as a confirmed fact in the UI or in exports | Epistemic accuracy |
| 6 | Running `conflict_of_interest` or `reviewer_matcher` agents without the Phase 2 feature flag | These agents involve more sensitive inferences; staged rollout is required |

---

## 4. Human Approval Gates

### 4.1 Report Approval
Every finding in the report has a `status` field: `draft | approved | rejected`.

- All findings begin as `draft`.
- A credentialed reviewer (human) must transition each finding to `approved` or `rejected`.
- Only `approved` findings may be included in an exported or shared report.

### 4.2 n8n Workflow Gates
n8n is used for automation workflows (e.g., drafting notifications). Every n8n workflow that produces external communication **must**:

1. Be configured with **HOLD-by-default** — the workflow pauses and creates a human-readable draft.
2. Require a human to explicitly click **"Approve & Send"** before any message leaves the system.
3. Log the approver identity, timestamp, and the exact content that was sent.

No n8n workflow may be configured to auto-approve or auto-send without this human gate.

### 4.3 Feature Flags for High-Risk Agents
The following agents are disabled by default and may only be enabled for authenticated operators:

| Agent | Environment Variable | Default |
|-------|---------------------|---------|
| `conflict_of_interest` | `FEATURE_COI_ENABLED` | `false` |
| `reviewer_matcher` | `FEATURE_REVIEWER_ENABLED` | `false` |

When these flags are enabled, additional disclaimers must be shown in the UI, clearly stating that the inferences are probabilistic and particularly sensitive.

---

## 5. Data Handling

### 5.1 Uploaded Papers
- Papers are stored under `./storage/papers/` (local filesystem for hackathon).
- Papers must not be used to train or fine-tune any model without explicit written consent from the uploader.
- Papers uploaded by users are treated as confidential unless the user explicitly marks them as public.

### 5.2 Retention
- For the hackathon/demo: no formal retention policy. Data persists until the Docker volume is cleared.
- For any production deployment: a retention policy must be defined before launch, limiting storage to the minimum necessary period.

### 5.3 No Third-Party Data Sharing
Findings, paper content, and metadata must not be transmitted to any third-party service other than:
- **Google Gemini API** (LLM inference — paper excerpts sent for analysis)
- **Crossref API** (citation DOI verification)
- **PubMed E-utilities** (citation metadata lookup)
- **arXiv API** (citation and preprint lookup)

All of the above are used at query time only — no bulk upload of paper content.

---

## 6. LLM Safety Constraints

### 6.1 Prompt Discipline
- LLM prompts must instruct the model to **flag and cite evidence**, not to render judgments.
- Prompts must not ask the model to determine whether an author "committed" misconduct.
- Prompts must include a system-level instruction: *"You surface concerns for human expert review. You do not make final determinations."*

### 6.2 Hallucination Mitigation
- Any claim that can be verified by code or API must be verified. The LLM must not be the sole source of truth for:
  - Statistical test results
  - Whether a citation exists or has been retracted
  - Whether a DOI resolves
- LLM outputs for factual claims must cite the specific evidence retrieved from APIs or computations.

### 6.3 Confidence Calibration
- Agent confidence scores (0.0–1.0) represent the agent's computed certainty that the flag warrants investigation — not that misconduct occurred.
- Confidence scores must be derived from observable signals (e.g., GRIM inconsistency degree, citation resolution failure rate), not from LLM self-assessment alone.

---

## 7. Incident Response

If a finding is later determined to be a false positive that caused reputational harm:
1. The finding must be immediately retracted from all exports.
2. The affected report must be marked as `RETRACTED` in the database.
3. The incident must be logged with full details (what was flagged, who approved it, when it was shared).
4. A post-mortem must be conducted and documented.

---

## 8. Contributor Acknowledgement

All contributors to PEERLESS.AI must acknowledge this Safety Policy before their first commit by adding their name to this section:

*(List maintained separately for production deployments. For the hackathon build, the project lead is responsible for all commits.)*

---

*Last amended: 2026-06-17 — Step 0 bootstrap.*
