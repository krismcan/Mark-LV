# Nayeon v1 - Codex current state

> This is the concise live handoff for Codex. Git remains authoritative. Read this after the root AGENTS.md at the start of every Nayeon task.

- **Branch:** `nayeon-v1`
- **Latest completed product phase:** Personal Alpha Milestone 3 - Approval-bound Verified Notepad
- **Latest milestone tag:** `nayeon-v1-personal-alpha-verified-notepad-01`
- **Full regression baseline:** **1,985 / 1,985**
- **Last updated:** 10 Oct 2026
- **Next restart point:** Three authorized Personal Alpha milestones complete. Await separately approved next product scope. Live human UI acceptance not performed; formal release gates remain open.

## Latest architecture invariant

Only exact local open notepad command can reach existing ConversationSession. GUI controller enforces default-deny permission with open_app only, mandatory saved-token explicit approval, App Paths-pinned Windows launch, independent matching executable identity verification. No real Notepad clicked during tests. 109/109 affected and 1,985/1,985 pre/postcommit full regressions pass; product annotated tag and peeled remote commit verified. Formal readiness 5/19 planned exits, 0/12 verified release gates.

## Required startup behavior

Inspect current HEAD/tag/status and read the latest relevant phase review before editing. If Git disagrees with this file, report the mismatch and treat Git as authoritative.

## Close-out rule

When the next product phase is sealed, refresh this file again as part of that phase close-out before the next Codex implementation session.
