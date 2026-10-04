# Phase 6.15 — UIA ↔ Pointer Coordinate Contract

## Purpose

Phase 6.15 adds a private, read-only contract check for the one coordinate-space identity case that Windows documents clearly enough to rely on without conversion: a proposed native screen point interpreted by a **Per-Monitor DPI Aware** thread.

The milestone remains detached from pointer execution and from UI Automation observation. It does not move, click, invoke, focus, search, or mutate anything.

## Why this boundary exists

Phase 6.14 deliberately did not claim that the existing private `_ProposedPoint` was a physical desktop point. That matters because UI Automation point lookup consumes physical desktop screen coordinates, while DPI-unaware or system-aware callers can observe DPI-virtualized coordinate spaces.

Microsoft documents that Per-Monitor DPI Aware applications use the actual monitor DPI and that logical and physical coordinates are identical for that awareness level. Phase 6.15 therefore certifies only that identity case and fails closed everywhere else.

Reviewed Microsoft contracts:

- `IUIAutomation::ElementFromPoint` / `AutomationElement.FromPoint`: desktop point lookup; the managed contract explicitly calls the input physical screen coordinates.
- `GetThreadDpiAwarenessContext`: returns the current thread DPI-awareness context.
- `GetAwarenessFromDpiAwarenessContext`: maps that context to the reviewed awareness values.
- `DPI_AWARENESS_PER_MONITOR_AWARE`: per-monitor aware processes are not automatically scaled by the system.
- `LogicalToPhysicalPointForPerMonitorDPI`: Microsoft notes that physical and logical coordinates are identical for a Per-Monitor-aware application.

## Contract

`_PhysicalCoordinateContractService.certify(point)` accepts only the exact private `_ProposedPoint` type on Windows.

It:

1. snapshots the exact point;
2. reads the current thread awareness once;
3. reads the current thread awareness a second time;
4. requires both exact values to be `DPI_AWARENESS_PER_MONITOR_AWARE (2)`;
5. revalidates the same point;
6. returns VERIFIED with private evidence only for that identity case.

Anything else returns INDETERMINATE with no evidence. Production never returns NOT_VERIFIED.

The two reads are a bounded sequential sample, not a continuous guarantee. A context can theoretically change away and back between samples. VERIFIED is therefore descriptive point-in-time evidence, not reusable authority.

## Deliberate non-scope

No coordinate conversion or scaling formula is introduced. In particular, this phase does not use logical-to-physical conversion APIs, monitor-DPI arithmetic, rounding repair, clamping, nearest-point behavior, or assumptions about mixed-DPI monitor layouts.

It also adds no:

- pointer movement or click;
- SendInput or cursor API;
- UI Automation call;
- process/thread DPI-awareness mutation;
- public capability, intent, route, or model-selectable tool;
- audit/undo integration;
- persistence or reusable authorization;
- semantic element identity, clickability, action success, or task success claim.

## Failure behavior

Unsupported platform, malformed point, unavailable native APIs, null/invalid awareness context, unknown awareness value, DPI-unaware or system-aware context, changed awareness sample, point tampering, or native exception all collapse to INDETERMINATE. Native error detail is not retained.

## Future integration rule

A later integration phase may use this contract only as a fresh same-operation prerequisite before treating the exact approved pointer point as a physical UIA point. If the runtime thread is not Per-Monitor aware, integration must deliberately establish a safe coordinate context or remain blocked. Phase 6.15 itself does not change the runtime DPI mode.

## Validation

Focused tests cover exact read order/cardinality, all reviewed awareness values, malformed native values, exceptions without retries, point tamper/type rejection, platform failure, real ctypes signatures under mocks, private/frozen invariants, and static no-mutation/no-UIA guards.

Validation results:

- focused Phase 6.15: 16/16 passed;
- affected pointer/UIA set: 245/245 passed;
- full regression: 1425/1425 passed;
- compileall: PASS;
- tracked diff check: PASS.

A live **read-only** native smoke on the current Windows Python host sampled the current thread awareness twice:

- `SMOKE_AWARENESS_1=0`
- `SMOKE_AWARENESS_2=0`
- `SMOKE_STATUS=indeterminate`
- `SMOKE_EVIDENCE=False`

This confirms two things. First, the production contract fails closed on the current DPI-unaware host. Second, a future UIA/pointer integration cannot assume the existing runtime has physical/logical coordinate identity. A later phase must deliberately establish or use a Per-Monitor-aware execution context before this evidence can become VERIFIED.

The smoke made no pointer, keyboard, focus, window, UI Automation, or DPI-awareness mutation.

No live pointer effect or UI mutation is authorized by this milestone.
