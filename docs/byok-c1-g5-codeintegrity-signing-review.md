# BYOK C1 G5 — authorised Windows Code Integrity signing decision packet

**Observation date:** 8 November 2026 (read-only inspection of Kristian). **Outcome:** G5 **BLOCKED**, no security exception or workaround authorised. This is supporting evidence for P104 and the [P100 G0–G6 review request](https://github.com/krismcan/Mark-LV/pull/24#issuecomment-6709413936), not a release approval.

## Authenticated host event observation

Actual Windows event channel: `Microsoft-Windows-CodeIntegrity/Operational`. Two pairs of event IDs **3033 and 3077** on 2026-11-07 near **14:16:31 UTC**. All four observed records reference the identical executable basename:

`P97_DisabledNativeAdmission_FINAL_x86_20261107.exe`

| Event record | Event ID | Time UTC (approximate) |
| --- | --- | --- |
| 17121 | 3033 | 2026-11-07 14:16:31.438 |
| 17123 | 3077 | 2026-11-07 14:16:31.438 |
| 17126 | 3033 | 2026-11-07 14:16:31.851 |
| 17128 | 3077 | 2026-11-07 14:16:31.851 |

Fields confirmed in both 3077 events:

- Policy name: `VerifiedAndReputableDesktop`
- Policy GUID: `{0283ac0f-fff1-49ae-ada1-8a933130cad6}`
- Policy version ID: `27555.1000.240208`
- Native status: `0xc0e90002`
- Logged SHA-256: `85F21E133BEDD8612FDEDAC0CF8D43FC4080741A3D5D378E48FC28C8233EA8D2`
- Logged SHA-256 flat hash: `4FE76B174659F3566E9C7EA3818B32BF26CB7B75FF4965AFF009A8D1F172E63F`

**Interpretation constraint:** Two event pairs do not prove two separate execution attempts. The data shows the same blocked binary and policy, not an authorised test pathway. No blocked executable was rerun during this evidence recovery. Full local paths, the interactive user and raw token/SID data are deliberately excluded.

## Specific questions for the Windows App Control policy owner

1. Who is authorised to approve test signing for this exact enterprise policy, and what is the formal change ticket/approval path?
2. Is execution of this x86 **review-only** native C# test permitted at all? If yes, specify a vendor/enterprise-approved signing pipeline or authorised managed test environment, certificate custody, image identity, audit requirements, and allowed test scope.
3. What source-to-binary and signature verification receipts are required, and how must the policy owner's written GO be tied to the exact test executable and policy version?
4. If blocked testing cannot be authorised, provide a written HOLD and identify the legitimate organisational alternative, if any. Do **not** disable/relax policy, create broad exceptions, rename/repackage the denied executable, or switch privilege contexts to evade the block.
5. The unrelated original OpenAI Support #18729810 P62 platform restriction remains independent and must not be replayed or bypassed.

## Separate source-review gate

G5 Windows signing approval is **not** G0–G4 Windows service custody approval. A qualified independent native Windows C#/.NET/WinCred/LocalSystem/IPC security reviewer must separately examine the source-specific architecture and produce a signed GO/HOLD per gate. No qualified reviewer had submitted approval when this packet was authored.

**Release restrictions remain:** No installed BYOK custody service, real user key, WinCred mutation, unreviewed native effect, P85 gate alteration, test-policy bypass, production merge/release, or Google Drive master/dashboard sync. This packet is documentation-only. **C1 PRODUCTION RELEASE HOLD.**