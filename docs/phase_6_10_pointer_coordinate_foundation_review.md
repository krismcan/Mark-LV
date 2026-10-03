# Phase 6.10 pointer coordinate foundation review

Status: CANDIDATE — current-tree validation blocked in this session. No commit, tag, push, workbook update, or pointer effect.

## Protected predecessor
Branch `nayeon-v1`, commit `d8dac271d565def6a570bc5c939de5774979c315`, tag `nayeon-v1-pointer-execution-eligibility-01`; predecessor regression 1,287/1,287.

## Exact trust claim
Given one exact private Phase 6.7 `_ProposedPoint`, Phase 6.10 samples the current Windows virtual-desktop bounding rectangle once and, only when the point lies inside a valid signed-LONG rectangle, derives a deterministic normalized integer pair for a future `MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK` operation. It performs no pointer effect and grants no execution authority.

## Geometry and mapping
The service reads `SM_XVIRTUALSCREEN` (76), `SM_YVIRTUALSCREEN` (77), `SM_CXVIRTUALSCREEN` (78), and `SM_CYVIRTUALSCREEN` (79), in that order. Origins may be negative. Width and height must be positive exact integers and the last addressable coordinate `origin + extent - 1` must fit signed Windows LONG.

For each axis, where `c` is the proposed coordinate, `o` the sampled origin and `e` the extent:

`n = 0` when `e == 1`; otherwise `n = floor((c - o) * 65535 / (e - 1))`.

For extents greater than one, this maps the first addressable coordinate to 0 and the last to 65535. A one-cell axis maps to 0, including at LONG_MIN and LONG_MAX. Integer floor division makes the contract deterministic. Python integer intermediates do not overflow; all native geometry and addressable endpoints are range checked.

## Privacy and failure semantics
The evidence/result/service are private, redacted and slotted; evidence/result are frozen. Copy, deepcopy, pickle and ordinary JSON serialization are rejected. VERIFIED requires exact revalidated private evidence; INDETERMINATE carries none. NOT_VERIFIED is rejected. These conventions are not a security sandbox against hostile in-process Python code. Unsupported platform, malformed types, non-positive extents, unsafe endpoints, points outside the rectangle, native exceptions or malformed metric values fail closed as `INDETERMINATE`. There is no retry, nearby-point search, geometry repair, or substitution.

## Explicit limitations and non-scope
Phase 6.10 does not claim physical-pixel identity, DPI equivalence, monitor-shape coverage, semantic control identity, click delivery, future geometry freshness, atomic validation/effect, or UI success. It adds no public capability/intent/route, executor mutation, persistence, approval token, focus/refocus, keyboard input, screenshot/OCR/CV/UIA/browser automation, cursor read, cursor movement, click, drag, scroll, hover, or native input injection.

The sampled virtual rectangle is evidence for coordinate normalization only. A future mutation phase must gather/validate geometry at the appropriate execution boundary and combine it with the immutable approved point and fresh Phase 6.9 target/location eligibility. It must separately define native input sequencing, failure/audit semantics and residual TOCTOU.

## Validation plan
Run the dedicated Phase 6.10 deterministic tests, the broader pointer/target/executor/policy boundary suite, full regression discovery, compilation, Windows environment diagnostics, `git diff --check`, and an explicit changed-production mutation-API scan. No live pointer mutation smoke is permitted in this phase.


## Externally written host validation report (not verified by this session)
Focused Phase 6.10: **24/24 passed**. Broader affected boundary: **323/323 passed**. Full regression: **1,311/1,311 passed**, 0 failures/errors. `compileall`, Windows environment diagnostics (Windows 11 AMD64 / Python 3.12.10), and `git diff --check` passed. The dedicated source-guard test also passed and asserts that the new production module contains none of the prohibited pointer/keyboard mutation APIs or public audit/undo integration. No live mutation smoke was run.

The repository remains at predecessor HEAD `d8dac271d565def6a570bc5c939de5774979c315`; only the Phase 6.10 service, tests, and this review document are uncommitted. No commit, tag, push, or Drive update has occurred.

## Validation outcome in this session

Validation is BLOCKED, not a verified milestone. The required interpreter
`C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe` is unavailable
in the tool environment. The repository venv also fails because it references
that same missing interpreter. No substitute interpreter was used.

The following commands were attempted with that exact interpreter; each failed
to start with command-not-found (exit 1), so no tests or Python checks ran:

```powershell
& 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe' -m unittest tests.test_pointer_coordinates -v
& 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe' -m unittest tests.test_pointer_coordinates tests.test_pointer_binding tests.test_pointer_hit_validation tests.test_pointer_observation tests.test_target_validation tests.test_executor tests.test_structured_executor tests.test_policy_confirmation -v
& 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe' -m unittest discover -v
& 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe' -m compileall -q nayeon tests
& 'C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe' -m nayeon.environment
```

The dedicated file contains 26 test methods. The anticipated regression count
is 1,287 predecessor tests plus 26 new tests (1,313); that count remains
unverified until discovery runs successfully. Coverage includes the LONG_MAX
endpoint mapping to 65535 with an exclusive edge of LONG_MAX + 1. Mutation API
checks inspect only the service source and class interfaces, without a broad
repository scan.

The patch tool reported write failures. Targeted PowerShell writes completed
the service comment, endpoint regression, scoped API check, and this validation
record. The existing test and review contents were retained and extended.

Branch remains `nayeon-v1`, HEAD remains `d8dac271d565def6a570bc5c939de5774979c315`.
Only the service, dedicated test file and this review are dirty, all untracked.
The test and review files were already present when inspected after the failed
initial patch, differing from the supplied expected single dirty file.
No commit, tag, push, live native query, or input effect was performed.

## Current-session validation limitation

The requested Python executable `C:\Users\krist\AppData\Local\Python\pythoncore-3.12-64\python.exe` could not be invoked from this session. Direct path inspection returned Access is denied. Focused tests, all ten requested affected modules, full unittest discovery, compileall, and nayeon.environment were each attempted with that exact executable and were blocked before Python started. No test pass is claimed by this session.

The files were concurrently updated during inspection. The host report above is preserved as an external report, not independently established evidence for the current tree. Additional explicit LONG_MIN/LONG_MAX one-cell combinations and point/native privacy checks require a fresh test run.

`git diff --check` produced no errors; tracked diff/stat were empty because all three Phase 6.10 files are untracked. Separate no-index checks produced no whitespace-error diagnostics (exit 1 denotes the added-file diff). The explicit changed-production scan found no SendInput, SetCursorPos, mouse_event, pyautogui, GetCursorPos, SetForegroundWindow, AttachThreadInput, or keybd_event. Final status contained only the three requested Phase 6.10 untracked files. No .venv or Phase 6.7/6.9 files were changed; no live mutation, commit, tag, or push was performed.
Whitespace validation passed: git diff --check and explicit git diff --no-index --check against /dev/null for all three untracked files reported no whitespace errors. Git emitted only LF-to-CRLF conversion warnings.
