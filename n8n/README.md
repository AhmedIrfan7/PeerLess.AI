# n8n Workflows — n8n/

Exported n8n workflow JSON files for PEERLESS.AI automation.

## Safety Requirement

**All notification workflows are HOLD-by-default.**
Every workflow that could result in external communication (email, webhook, etc.) must pause for human approval before sending.
No workflow may be configured to auto-approve or auto-send.

## Import Instructions

1. Open the n8n UI at http://localhost:5678
2. Go to Workflows → Import from file
3. Select the JSON file from this directory

## Planned Workflows

- `notification_draft.json` — Drafts a notification for human approval (HOLD-by-default)
- `report_export.json` — Triggers report export with disclaimer injection
