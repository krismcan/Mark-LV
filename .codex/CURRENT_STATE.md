# Nayeon v1 - Codex current state

> This is the concise live handoff for Codex. Git remains authoritative. Read this after the root AGENTS.md at the start of every Nayeon task.

- **Branch:** `nayeon-v1`
- **Latest completed product phase:** Phase 8.5 - Typed Provider Connection Ownership & Persistence
- **Latest milestone tag:** `nayeon-v1-provider-connection-ownership-persistence-01`
- **Full regression baseline:** **1,821 / 1,821**
- **Last updated:** 8 Oct 2026
- **Next restart point:** Phase 8.6 architecture audit - trusted provider-connection composition, provider-to-credential identity binding, and explicit bootstrap; scope not yet approved

## Latest architecture invariant

Phase 8.5 owns one immutable schema-v1 non-secret ProviderConnectionDocumentV1 via a strict codec, explicit native-Path 16 KiB bounded atomic-replace ProviderConnectionFileStore, and lazy process-local ProviderConnectionService with persist-before-swap replace/clear; an unconfigured document persists connection=null. The three new modules have no runtime/app/UI consumers, no secret-store authority, and no provider factory/validator or presentation imports. Credential use requires separately approved trusted composition with explicit provider-to-credential identity validation. Product commit d6661f6e0ac02e881056bf98c49df20618758c79; maintenance commits e29b5586bca5bf31fd98916b3687a5f856c6a8a0 and 0e63e952104944d856ec454323ba3e7facc3a1aa; both maintenance tags are preserved; full post-commit 1821/1821 passed. No real credential, SDK, network or native store operation was used.

## Required startup behavior

Inspect current HEAD/tag/status and read the latest relevant phase review before editing. If Git disagrees with this file, report the mismatch and treat Git as authoritative.

## Close-out rule

When the next product phase is sealed, refresh this file again as part of that phase close-out before the next Codex implementation session.
