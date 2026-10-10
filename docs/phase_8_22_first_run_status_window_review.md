# Phase 8.22 - Explicit first-run status window

A native Tkinter panel can be mounted by a trusted parent using an injected
`FirstRunReadOnlyController`. It does not automatically run an observation on
construction and has exactly one enabled user action: **Refresh status**.
The current point-in-time summary is displayed with fixed, non-secret text.
Unknown, unsafe, unsupported and failing observations fail closed and never
claim a working provider connection.

The panel does not accept keys or offer validation, storage, removal,
approval or active provider controls. This is deliberately not a public
production first-run app or full Phase 8 closure. Synthetic Tk widgets verify
button wiring and redaction without live Windows credential access.
Next milestone: separate trusted human operation review integration, retaining
a strict non-secret presenter and explicit external authority boundary.
