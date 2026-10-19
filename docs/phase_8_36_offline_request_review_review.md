# Phase 8.36 — Independent review and failure ledger

Status: **PENDING final product review, not a release**.

- Design PR #1, exact v0.5 amendment reviewed with no final findings.
- Pure owner Increment A PR #2, 26 focused tests, independent review no findings.
- Native Tk integration Increment B PR #3, latest test-only commit `606f3ce1f624432dfb05644a7628f1d63a734b8d`, independent review complete no findings. Earlier 2 P2 production issues (reply-worker ingress, stale success after cleanup fault) fixed and proved with fault-injection tests. Third P2 test issue required started actual worker, fixed.
- During new B development, 242 affected tests yielded one expected refusal `Unauthorized untracked 8.34 path`. This is a real fail-closed historical guard; Increment C must preserve it as historical safety proof while admitting exact 8.36 successor.
- This review file is release-candidate evidence only; full native regression and reviewer verdict must be appended after they actually happen. Do not claim three green full runs, Git tag, GitHub product push, original master workbook or public dashboard update prematurely.

## Security review targets

1. Exact path allowance 19 only, no extra linked/aliased/ignored files.
2. Immutable sealed 8.34 parent tree + peeled annotated tag and all 8.30–8.34 predecessor attack assertions still reachable.
3. Byte-pinned file identity across worktree, index, HEAD, staged and committed successor; unexpected merge or descendant refused.
4. No real credentials/provider/network/actions; non-authorising receipt and no hidden AI response.
5. Native Tk before/after-effect tests: reentrant Confirm, Cancel, Reset, Destroy; worker admission; independent cleanup failure; last Tcl state observation and 30-second monotonic deadline.
6. Precise test maintenance must not convert historical refusal into GO; old synthetic fixtures call private historical bodies explicitly.

**Review result: not yet issued.**
