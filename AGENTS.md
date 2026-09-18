# Project Workspace Rules: AI Knowledge Assistant

## Spec-Driven & ADR-First Feature Lifecycle

### Workflow Triggers: `go`, `status`, `check status`, `features`
Whenever the user types **`go`**, **`status`**, **`check status`**, **`project status`**, or mentions feature progress:
1. **Activate the `spec-driven-development` workflow immediately.**
2. **Scan the `features/` directory:**
   - Read each feature's `tasks.md` and `design.md`.
   - Extract Feature ID, Title, Status, and Current Focus / Next Action Needed.
3. **Display the Live Feature Status Dashboard:**
   - Print a clean Markdown table summarizing all features.
   - Highlight any pending Architectural Decision Records (ADRs) awaiting user review.
   - List the immediate next tasks ready for execution.
4. **Enforce the ADR-First Rule:**
   - If a new feature is requested or a feature is in `DESIGN_READY` status, present the ADRs and High-Level Design (HLD) for user review before implementing any production code.
