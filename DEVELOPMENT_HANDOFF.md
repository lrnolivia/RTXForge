> Historical WIP import. Superseded by the supplied RC1.38 engine and current WORKER_CONTEXT.md. Embedded tasks are not active instructions.

# rtxEngine · Terminal Edition v13 — Handoff 188 WIP (y4my v4 unification)

## Status
**WORK IN PROGRESS — NOT A RELEASE / NOT SAFE TO USE AS A LIBRARY-WIDE INSTALLER YET.**

This bundle is the exact current implementation state at handoff. It deliberately preserves unfinished code so the next worker can continue from the real branch rather than reconstructing work from chat.

`python3 -m py_compile rtxEngine-terminal-v13.py` passes. The inherited test suite is not yet migrated: current result is **147 passed, 53 failed, 10 subtests passed**. See `CURRENT_TEST_OUTPUT.txt`.

## Direction reset
Handoff 188 abandons the multi-provider production runtime and makes **y4my OptiScaler Multipass MFG v4** the single active Proton core for both Neural Rendering and native Ada MFG.

Pinned upstream:
- repository: `y4my4my4m/OptiScaler_DLSSNR_Multipass_MFG`
- tag: `v10.0.0-dev-fork-y4my4my4m-v4`
- commit: `7b7220bbb4994a9c8ae60cfc75a44cb67995efb8`
- asset: `OptiScaler_v10.0.0-dev-fork-y4my4my4m-v4_20260905_with_DLSS.7z`
- SHA-256: `9d7824cc9cfb15265bc6438b4638aad74ff9cd6d1d3488ab73724affb386a8b0`
- expected release size: `117366545`

Architecture goal:
- one y4my OptiScaler loader/proxy;
- bundled y4my Streamline/DLSS companion tree;
- native Ada MFG from the same OptiScaler build (`AdaMfgUnlock=true`, `AdaBlackwellKernels=true`);
- DLSS Neural Rendering from the same stack;
- no active Universal RTXMFG provider;
- no active RTXForge NativeMFG v3e runtime;
- no hybrid FG;
- Proton launch contract owned by rtxEngine should be only the selected native proxy override (plus preserved external overrides such as ReShade when required).

## Work already converted
The source currently contains:
1. `Y4MY_PROVIDER` with exact tag/commit/asset/SHA pin.
2. y4my archive discovery/download/verification and `.7z` extraction path.
3. required-file validation for the y4my with-DLSS layout.
4. normalization of upstream `OptiScaler.dll` into rtxEngine's existing proxy-placement machinery.
5. user-supplied/preserved `nvngx_dlssnr.dll` handling helpers. y4my does not redistribute NVIDIA's NR model/runtime DLL, so rtxEngine must not fetch it from mirrors.
6. new unified OptiScaler policy enabling NR multipass + Ada native MFG in one runtime.
7. minimal launch-option generation: `WINEDLLOVERRIDES="<selected proxy>=n,b" %command%`, while preserving required external proxy overrides.
8. install-path work that sets the old separate MFG proxy to `None` on Ada and places the user/preserved NR runtime into the managed payload.
9. legacy RTXMFG/provider metadata retained only where recovery/migration compatibility may still need it.

## First blocking bug to fix
The CLI and batch path are not wired to the new NR runtime flow yet.

- CLI exposes `--nr-runtime`.
- `load_user_nr_runtime()` exists.
- `install_target(... nr_runtime_payload=..., nr_runtime_meta=...)` accepts it.
- **But `batch_install()` still has the Handoff 187 RC2.1 logic, calls `load_integrated_ada_runtime()`, and does not resolve/pass the NR runtime.**

This is why many tests now stop at:
`nvngx_dlssnr.dll is required for y4my Neural Rendering...`

Fix this before any live library install test.

## Stale active code that must be removed or demoted to recovery-only
The current source still contains old 187-era branches/labels. Audit before RC1:
- `load_integrated_ada_runtime()` still references the removed `RTXFORGE_ADA_RUNTIME` constant and throws `NameError` if reached.
- `batch_install()` still calls that function for Ada.
- old `rtxmfg_payload` / `rtxmfg_meta` parameters and RTXMFG provider loader remain in the source; retain only the minimum needed to interpret/retire old state, never as a new-install route.
- install records/audit output still contain `mfg_provider` compatibility fields and at least one Handoff 187 NR-disabled status string.
- interactive UI text still advertises `RTXForge NativeMFG v3e`.
- historical launch-option ownership still includes `PROTON_ENABLE_NVAPI` / `PROTON_NVIDIA_NVCUDA`; this is acceptable only for recognizing/removing old rtxEngine-owned tokens, not for new generation.

Useful grep:
```bash
grep -nE 'load_integrated_ada_runtime|RTXMFG|NativeMFG v3e|187 RC2|PROTON_ENABLE_NVAPI|PROTON_NVIDIA_NVCUDA|mfg_provider' rtxEngine-terminal-v13.py
```

## Test migration work
Current gate: **147 passed, 53 failed, 10 subtests passed**.

Failure classes observed at handoff:
1. old install/transaction fixtures do not supply a valid >32 MiB PE-shaped `nvngx_dlssnr.dll`, so they now fail before reaching the behavior they intend to test;
2. 187 RC2 tests call `load_integrated_ada_runtime()` and hit the removed runtime identity;
3. policy tests still assert the old split architecture (NR disabled on Ada / external or no-FG settings) rather than the unified y4my v4 policy;
4. RC2 proxy/runtime-marker tests are coupled to the old v3e runtime and need to be rewritten as migration/legacy-recovery tests or deleted if no longer relevant;
5. Ampere/sm86 expectations need a deliberate product decision rather than accidental inheritance from the Ada rewrite.

Do not simply weaken assertions. Supply a deterministic fake NR runtime fixture for transaction tests so they continue exercising crash safety, restore, provider relinquishment, filesystem hazards, and ownership semantics.

## Required 187 -> 188 migration behavior
The next worker should make migration a first-class tested path:
- recognize an existing 187 RC2.1 baseline;
- retire the managed v3e/legacy MFG payload transactionally;
- preserve external/ReShade files and any user-modified OptiScaler config where safe;
- install the exact y4my v4 payload;
- preserve or accept the NVIDIA NR runtime without claiming ownership of an external copy incorrectly;
- update baseline ownership atomically;
- on failure/crash, leave a retryable recovery state and never strand half-retired provider ownership;
- uninstall after migration must still restore the true pre-rtxEngine state, not the intermediate 187 state.

## RC1 acceptance gate
Do not call 188 RC1 complete until all of these pass:
1. `python3 -m py_compile rtxEngine-terminal-v13.py`.
2. Entire automated suite green, with new y4my v4 + 187->188 migration regressions.
3. Clean package extraction and rerun of the exact same tests.
4. No new-install path can call/download/install Universal RTXMFG or NativeMFG v3e.
5. `--nr-runtime` and auto-discovered user runtime actually reach every selected install.
6. one odd/failing game cannot poison the rest of a batch.
7. launch options contain only the y4my-selected proxy override plus preserved external overrides; no newly-added NVCUDA/NVAPI variables.
8. a dry/read-only scan remains non-mutating.

## First live validation after the automated gate
Use a small matrix, not ALL:
- The Outer Worlds 2 — known previous win / regression baseline;
- Cyberpunk 2077 — previous hard failure and particularly valuable for the y4my Proton/Ada path;
- Avatar: Frontiers of Pandora — previous no-hook/no-MFG state;
- Clair Obscur: Expedition 33 — previous MFG success without relying on overlay visibility.

For each: install -> launch -> verify NR + native Ada MFG -> audit -> uninstall/restore canary. Only broaden to the library after that loop is clean.

## Non-goals
- Do not reintroduce hybrid FG.
- Do not add per-game user-facing MFG routes to hide failures.
- Do not enable exact extra-file deletion from Steam depot manifests; encrypted filename/depot-key handling is still not trustworthy enough.
- Do not treat the legacy 187 documents in `legacy-docs/` as current architecture. They are included only for migration context.
