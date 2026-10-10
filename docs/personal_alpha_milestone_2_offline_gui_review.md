# Nayeon Personal Alpha Milestone 2 — Offline Desktop Chat

## Scope
Isolated standard-library Tkinter desktop application under
`nayeon/desktop_alpha/`; launch manually with
`python -m nayeon.desktop_alpha`. Shows a dark themed chat transcript,
input area, and disabled consent buttons. All submitted requests are
nonacting offline previews, and only ephemeral UI text is retained.

## Security properties
No provider requests, key access, filesystem operations, application
launch, model or runtime tool, direct policy grant, hidden startup
behavior, background task or persistent history. Approval and rejection
buttons are disabled; offline controller has no pending actions. UI
has no imports from runtime authority services. This milestone provides
the presentation surface only, NOT a verified action or release gate.

## Tests and acceptance
Headless tests validate exact outcomes, strict request lengths, immutable
sanitized replies, no action dependency graph, no top-level widget
construction or implicit launch. Full regression + staged scope + annotated
tag + remote verification + Codex handoff + master workbook update are
required before enabling a real session.

## Next Milestone
Bind only an explicitly approved Notepad request via the existing
ConversationSession / Permission / Policy / Confirmation / Executor /
Verification spine. All other app names fail closed. Only a human
button may approve, and only verified executable identity may yield
a reported successful action. Formal 5/19, 0/12 unchanged.
