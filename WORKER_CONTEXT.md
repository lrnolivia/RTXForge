# RTXForge Worker Context

**Canonical development source of truth — refreshed 2026-09-10**

Read this file completely before changing RTXForge or RTXForge-MFG. It replaces the old overlapping `rtxforgenotes.md`, `update.md`, and temporary Astra handoff as the single worker-facing context document.

---

## 1. Repositories and source of truth

Use the normal local repositories:

```text
~/Repos/RTXForge
~/Repos/RTXForge-MFG
```

The temporary `-online` clones were used to refresh these repos and then deleted.

### RTXForge

```text
Repository: lrnolivia/RTXForge
Branch: main
```

Important app-repo integration commits before this context refresh:

```text
ffb098b  Pin working NativeMfgMenu v3e runtime
70e6d78  Preserve known Forza game-side winmm proxy
```

Do not assume those are still HEAD. At worker startup, fetch and inspect the current branch before editing.

### RTXForge-MFG

```text
Repository: lrnolivia/RTXForge-MFG
Branch: rtxforge-proton
Known-working v3e commit:
deca7b7a8f1953de3cf6fe2731ede440b3ddaadf

Golden tag:
RTXForge-NativeMFG-v3e-working

Commit message:
RTXForge.NativeMfgMenu.v3e: apply native count in DLSSG dispatcher
```

Pinned upstream OptiScaler base:

```text
7b7220bbb4994a9c8ae60cfc75a44cb67995efb8
```

Important earlier checkpoints:

```text
v3d diagnostic:
91004fa12354f892034255a1357dfdf33424f3c3

v3c failed apply:
b276b5e434c6094962779bd0a77c5adb67642a7a

v3b diagnostic:
174610ec8e1110601383b47c2d90d7c8c4b5ad56
```

### Golden local v3e checkpoint

A known-working runtime copy was preserved at:

```text
~/RTXForge-Golden-v3e
```

Recorded identity:

```text
Commit:
deca7b7a8f1953de3cf6fe2731ede440b3ddaadf

Runtime DLL SHA256:
95580ebc7d2f562d6d99cd798587f757a51cd7bd52e24b0895c42414c3a3c2e8

GitHub Actions build:
34455052784

Game:
The Outer Worlds 2

GPU:
RTX 4070
```

Observed working status:

- native 2X works
- native 3X works
- native 4X works
- repeated 2X -> 3X -> 4X transitions work
- no fatal in the successful run
- no DLSS-G SetOptions error in the successful run
- Off/Auto/Dynamic are not fully implemented yet
- `runtime_verified=false`

Do not destroy or repoint the golden tag while active runtime work continues.

---

## 2. Product scope

RTXForge is a **Linux/Bazzite/Proton application** distributed as an AppImage.

Current direction:

```text
Linux / Bazzite / Proton
GNOME first
KDE integration may follow
Windows client: not active
```

Do not turn the current project into a Windows client or generic cross-platform injector while finishing this work.

---

## 3. Runtime stack direction

Keep MFG and NR separable internally.

### MFG

Preferred/default route:

```text
game-native Streamline DLSS-G
        ↓
RTXForge-MFG / y4my OptiScaler core
        ↓
OptiScaler-owned native NVIDIA DLSS-G output
        ↓
Ada MFG unlock
        ↓
Blackwell kernels
```

Baseline:

```ini
[FrameGen]
Enabled=true
FGInput=dlssg
FGOutput=dlssg
FGNvngxReplacement=none

[DLSSG]
AdaMfgUnlock=true
AdaBlackwellKernels=true
```

Rules:

- Native Streamline DLSS-G is the preferred/default MFG route.
- y4my remains the OptiScaler/MFG core.
- Do not route normal MFG through `nvngxfg`.
- Do not make DLSS Enabler / Artur Headless a hidden dependency or automatic fallback.
- Cyberpunk 2077 remains a useful proof case: native Streamline reproduced normal performance; the Enabler route reproduced severe performance loss.
- Preserve working MFG behavior while changing NR.

### NR

The current 0.4.x-era NR composition is incomplete.

Current partial composition:

```text
y4my OptiScaler core
+ y4my NR forwarder
+ DLSS-Unlocked patched nvngx_dlssnr.dll
```

Target:

```text
DLSS-Unlocked complete Proton-working NR route
+ y4my native Streamline MFG route left untouched
```

Do not treat copying the patched NR DLL alone as complete NR integration. Bring over the NR-specific Proton plumbing required by the chosen DLSS-Unlocked route as a unit: forwarder, runtime, file layout, proxy/loading behavior, config, required runtime/Streamline pieces, and Proton loading expectations.

Do not wholesale import DLSS-Unlocked MFG defaults if they would restore Enabler/`nvngxfg` as the normal generator.

---

## 4. Native MFG breakthrough: what is proven

### Test environment

```text
Game: The Outer Worlds 2
Game directory:
/var/mnt/Games/Non-Steam Games/The Outer Worlds 2/Arkansas/Binaries/Win64

Live proxy:
dxgi.dll

Primary log:
OptiScaler.log

GPU:
RTX 4070 / Ada

Platform:
Bazzite / Proton / D3D12
```

Successful test configuration:

```ini
FrameGen.Enabled=true
FGInput=dlssg
FGOutput=dlssg
FGNvngxReplacement=none

DLSSG.OverrideForceDMFG=false
DLSSG.ForceDMFG=false
DLSSG.AdaMfgUnlock=true
DLSSG.AdaBlackwellKernels=true

DlssNr.Enabled=false

NvApi.DisableFlipMetering=true
NvApi.DisableReflexSync=true
```

Keep NR disabled while finishing MFG behavior.

### Proven native mapping

The Outer Worlds 2 exposes its native 2X/3X/4X selector and v3e makes it control OptiScaler's actual DLSS-G generated-frame count:

```text
Native 2X -> native numFramesToGenerate=1 -> output count=1
Native 3X -> native numFramesToGenerate=2 -> output count=2
Native 4X -> native numFramesToGenerate=3 -> output count=3
```

The successful session exercised:

```text
1 -> 2 -> 3
3 -> 1
1 -> 2
2 -> 3
```

This is the first confirmed working native-menu control path.

Important: this is not yet full production verification. Keep:

```text
runtime_verified=false
```

until remaining mode semantics and the regression matrix are complete.

---

## 5. Winning architecture — do not regress

The game queries DLSS-G early and can cache the returned function pointers for the lifetime of the process.

The safe architecture is:

```text
game-native MFG menu
        |
        v
permanent synthetic game-facing slDLSSGSetOptions
        |
        | capture primitive request state only
        v
NativeDlssgBridgeState
        |
        v
OptiScaler DLSSG_Dx12::Dispatch()
        |
        | translate native request into
        | OptiScaler-owned output state
        v
existing normal OptiScaler raw DLSS-G SetOptions push
        |
        v
real NVIDIA DLSS-G / MFG output
```

Mental model:

> **The game's Streamline instance is the controller; OptiScaler's own DLSS-G instance is the renderer. Do not try to make the controller become the renderer.**

### Non-negotiable callback rule

The cached game-facing `slDLSSGSetOptions` pointer must remain synthetic permanently.

Do not:

- switch the cached callback from synthetic to real later
- forward that cached callback directly into real DLSS-G
- call `hkslDLSSGSetOptions()` from `hkslSetConstants()`
- create a second raw DLSS-G SetOptions call merely to consume the bridge

The successful design consumes native control state through the existing OptiScaler output path.

---

## 6. Native bridge state

Current bridge concept:

```cpp
struct NativeDlssgBridgeState
{
    std::mutex mutex;

    bool valid = false;
    uint32_t viewport = 0;
    uint32_t structVersion = 0;
    uint32_t mode = 0;
    uint32_t numFramesToGenerate = 1;
    uint32_t dynamicTargetFrameRate = 0;

    uint64_t generation = 0;
    uint64_t lastConsumedGeneration = 0;
};
```

Synthetic SetOptions:

- safely copies supported older structure layouts
- captures primitive values only
- increments generation when the request changes
- returns `sl::Result::eOk`
- never calls real DLSS-G

Synthetic GetState:

- remains synthetic
- exposes enough capability to reveal native 2X/3X/4X on the explicitly enabled RTXForge Ada route
- should not blindly mirror every unlocked internal maximum without a reason

v3e also has a consume helper so a generation handled by the output dispatcher is not unexpectedly consumed later by the older hook-side bridge path.

---

## 7. Experiment history and failure boundaries

Do not repeat these dead ends without new evidence.

### v2 / v2a — failed

Early synthetic callbacks later forwarded/switched into real DLSS-G callbacks.

Result: fatal.

Meaning: TOW2 does not tolerate that cached-pointer lifecycle transition safely.

### v2b — safe boot base

Cached GetState and SetOptions remained synthetic permanently.

Result: full boot.

Meaning: permanent synthetic callbacks are the safe foundation.

### v2c — selector mapping proof

Permanent synthetic callbacks plus request capture.

Result: boot and mapping proved:

```text
2X -> 1
3X -> 2
4X -> 3
```

### v3 / v3a — wrong consumers

Attempts to consume/probe from other Streamline hook paths did not provide the usable runtime boundary.

### v3b — useful diagnostic only

A canary in `hkslSetConstants` saw every pending generation.

That proved observation, not safe apply.

### v3c — failed apply and key lesson

Attempt: when SetConstants saw a pending generation, call `hkslDLSSGSetOptions()`.

Observed boundary:

```text
MfgUnlock::TryApply succeeded
        ↓
native request captured
        ↓
hkslSetConstants sees request
        ↓
v3c dispatch begins
        ↓
hkslDLSSGSetOptions logs bridged request
        ↓
process dies before dispatch result returns
```

Meaning:

> `SetConstants` being active does not make it a safe place to re-enter DLSS-G.

The unlock had already succeeded, so do not blame `MfgUnlock::TryApply()` for this failure without new evidence.

### v3d — correct consumer identified

Removed v3c re-entry and observed the bridge from `DLSSG_Dx12::Dispatch()`.

Result:

- every pending native generation appeared inside OptiScaler's actual DLSS-G output dispatcher
- source viewport `1`
- OptiScaler output viewport `0`
- `_maxInterpolationCount=5`
- configured output count remained `1`

The viewport difference is valid because the game-native instance is the control source and OptiScaler's own instance is the output generator.

### v3e — working apply

Instead of making a new Streamline call:

1. Read the newest native bridge generation inside `DLSSG_Dx12::Dispatch()`.
2. For native `sl::DLSSGMode::eOn`:
   - read `numFramesToGenerate`
   - preserve explicit interpolation override precedence
   - clamp the count
   - write it to `FGDLSSGInterpolationCount` with `set_volatile_value()`
3. Mark that generation consumed.
4. Let the existing dispatcher continue normally.
5. Existing code updates `_framesToInterpolate`, builds `sl::DLSSGOptions`, and performs its normal raw `StreamlineProxy::DLSSGSetOptions()` call.

No second DLSS-G call is introduced.

That is why v3e works where v3c did not.

---

## 8. Current v3e runtime changes

The v3e runtime commit changes four files:

```text
.github/workflows/rtxforge-proton.yml
OptiScaler/framegen/dlssg/DLSSG_Dx12.cpp
OptiScaler/hooks/Streamline_Hooks.cpp
OptiScaler/hooks/Streamline_Hooks.h
```

Behavior:

- runtime capability is `RTXForge.NativeMfgMenu.v3e`
- native bridge state is read inside the real OptiScaler DLSS-G dispatcher
- ordinary native `eOn` requests apply `numFramesToGenerate`
- explicit `FGDLSSGOverrideInterpolationCount` still wins
- request is clamped
- output count is written via `FGDLSSGInterpolationCount.set_volatile_value(...)`
- bridge generation is consumed
- existing raw DLSS-G output call remains the only real apply call
- non-`eOn` modes are currently logged/handled without complete semantic translation

---

## 9. RTXForge app integration already completed

Do **not** spend another worker cycle redoing AppImage/runtime integration.

The golden v3e runtime is already pinned into RTXForge.

Current pinned provenance:

```text
RTXForge-MFG commit:
deca7b7a8f1953de3cf6fe2731ede440b3ddaadf

Capability:
RTXForge.NativeMfgMenu.v3e

Runtime DLL SHA256:
95580ebc7d2f562d6d99cd798587f757a51cd7bd52e24b0895c42414c3a3c2e8

GitHub Actions build:
34455052784
```

`provider.json`, `docs/proton-runtime-build.json`, `build/accept_runtime.py`, and the bundled loader were updated for v3e.

`runtime_verified=false` remains intentional.

### Actual local AppImage path

The GNOME desktop launcher uses:

```text
~/.local/share/rtxforge/application/RTXForge.AppImage
```

It does **not** launch the convenience copy in `~/Applications`.

A stale AppImage at the wrong path caused one false-negative compatibility test during this session. When rebuilding locally, update or verify the actual launcher target before concluding a new build is active.

---

## 10. Forza Horizon 6 compatibility fix

Forza Horizon 6 contains an existing game-side:

```text
winmm.dll
SHA256:
bfe362f716b95b830206a1b986e2e94735691e8d7dd71f9148f7b9cfd3c5f435
```

Evidence from the active file:

- no OptiScaler marker
- no adjacent `OptiScaler.ini`
- PE timestamp reports 2022
- historical known-working Forza OptiScaler deployments repeatedly used `dxgi.dll`, not this `winmm.dll`

RTXForge originally treated the existing `winmm.dll` as an unowned competing proxy and blocked installation even with **Recognize previous installs** enabled.

App commit:

```text
70e6d78  Preserve known Forza game-side winmm proxy
```

The compatibility rule is intentionally exact:

```text
game identity + filename + SHA256
```

It preserves this specific Forza `winmm.dll` as an external game-side input and lets RTXForge use a separate proxy, which falls back to `dxgi.dll` for Forza.

Do not weaken this into a global `ignore winmm.dll` rule.

### Result

After the rebuilt AppImage was copied to the actual GNOME launcher path, RTXForge successfully installed the v3e MFG package to Forza Horizon 6 while leaving the game-side `winmm.dll` untouched.

This proves the **installer compatibility fix** worked.

It does **not** yet prove v3e gameplay/runtime behavior in Forza. Treat Forza as a high-value cross-game validation target.

### High On Life 2 Demo

High On Life 2 Demo also exposed an unrecognized proxy-shaped DLL during the library-wide install attempt.

Do not infer it is safe from the Forza result. Fingerprint and classify it independently before adding any exception.

---

## 11. Immediate Astra mission

Continue from **v3e**.

Do not reopen the old "how do we make 2X/3X/4X work?" problem unless an actual regression appears.

Immediate goal:

> Finish native The Outer Worlds 2 DLSS-G mode semantics around the already-working 2X/3X/4X bridge without changing the successful apply architecture.

### A. Map native modes precisely

Observed numeric modes include:

```text
0
1
2
```

Known:

```text
mode=1
```

is the ordinary active MFG mode used by working 2X/3X/4X selections.

Do not assign user-facing meanings to `0` and `2` by guess. Map them with controlled native-menu tests.

A startup capture with:

```text
mode=2
numFramesToGenerate=1
```

has been observed; v3e deliberately did not apply it.

### B. Implement Off / Auto / Dynamic through the existing output path

Do not solve these with an additional Streamline invocation.

Preserve:

```text
native game state
        ↓
bridge
        ↓
DLSSG_Dx12::Dispatch
        ↓
modify state/options the existing dispatcher is already about to send
        ↓
existing raw StreamlineProxy::DLSSGSetOptions()
```

### C. Preserve explicit override precedence

An explicit RTXForge/OptiScaler interpolation override must continue to win over the native game multiplier.

### D. One conceptual variable per experiment

Do not simultaneously alter mode translation, callback lifetime, unlock behavior, NR, Reflex behavior, and output route. Change one thing, build, test, preserve the log.

---

## 12. Validation required before `runtime_verified=true`

At minimum:

- cold launch
- launch with each relevant native menu state
- repeated 2X / 3X / 4X transitions
- 4X -> 2X
- 2X -> 4X
- native Off
- native Auto/Dynamic if exposed
- explicit interpolation override precedence
- menu open/close
- save/load or equivalent gameplay transition
- longer gameplay session
- normal shutdown
- MFG unlock still applies
- no new fatal
- no `Couldn't set DLSSG options`
- NR remains disabled during MFG-only validation
- no regression to known-good MFG-only behavior

After TOW2 is stable, test the same architecture in at least one additional native Streamline MFG game. **Forza Horizon 6 is already installed with v3e and is a strong next target.**

Only after controlled validation succeeds should app/runtime provenance move to:

```text
runtime_verified=true
```

---

## 13. Runtime experiment discipline

For each RTXForge-MFG experiment:

```text
verify exact source HEAD
-> change one conceptual variable
-> git diff --check
-> commit
-> push
-> identify the exact GitHub Actions run for that commit
-> download the exact artifact
-> verify PE/MZ, fork_commit, capability, SHA256, compiled marker
-> back up live proxy DLL
-> deploy exact artifact
-> verify live SHA256
-> test in a real game
-> preserve relevant log
```

Compilation, CI, metadata verification, and deployment are not runtime success.

---

## 14. App behavior that must be preserved

### Adoption lifecycle hotfix

Correct state model:

```text
CLEAN
No recognizable OptiScaler install
No active managed stack
-> fresh install

MANAGED
Managed manifest + managed files present
-> repair/change profile/uninstall

EXTERNAL
Recognizable external OptiScaler proxy + INI present
No valid RTXForge ownership
-> adoption may be offered
```

Rules:

- historical state alone must never force adoption
- clean post-uninstall games must be installable again
- adoption requires a recognizable external OptiScaler proxy and INI that exist now
- incomplete external installs are not silently adopted
- CLI says `ADOPT` only when adoption actually occurred
- do not show a misleading "enable Recognize previous installs" message when the setting is already enabled; if recognition fails, report the actual reason

Still desired:

- Deep Clean state normalization
- Install -> Uninstall -> Install integration fixture
- Steam Verify / externally removed managed-files integration coverage

### Prepared-package cache self-healing

Prepared payloads are disposable derived cache.

Correct behavior:

```text
valid payload + matching manifest
-> reuse

listing / manifest / payload drift
-> do not trust cache
-> remove invalid derived payload/manifest only
-> keep pinned source archive
-> verify source archive hash
-> rebuild extraction
-> regenerate files.json
-> verify rebuilt payload
-> continue
```

Readonly/dry-run stays non-mutating and should report that normal Prepare/Install is required to repair stale derived cache.

Security rule:

> Self-healing must never mean accepting drift.

---

## 15. Product/UI backlog

These are product requirements. Do not destabilize runtime work as collateral UI work unless a separate worker is assigned.

### Library cards/details

- reduce unnecessary hero-art padding
- use artwork-derived accent tones more strongly in detail views
- universal profile/status badges such as `NR + MFG`, `MFG`, `Unavailable`
- expose useful applied-state information: profile, active fixes, compatibility notes, runtime status, test status
- prefer compatibility/configuration metadata over decorative genre metadata when space is limited
- add game description where useful
- add **Open Directory**
- add **Launch Game**
- keep SteamGridDB credit unobtrusive
- improve Non-Steam title -> likely Steam App ID matching when confidence is high

### Install-profile controls

- `NR + MFG` before `MFG`
- make active profile visually obvious
- keep profile/status color language consistent across cards, filters, and details

### Library density/scrolling

- smaller library-view pills
- roughly 2–2.5 poster rows visible by default
- collapse/condense large header on scroll
- avoid oversized permanent chrome

### Progress/status presentation

Replace the disliked full-width status bar with a smaller, clearer floating/compact progress surface. Tasteful animation is okay; clarity wins.

### Integrated game testing

Desired Test workflow:

1. choose Test on a game
2. record runtime/profile/config identity
3. launch the game
4. capture relevant logs for that test session
5. stop capture when the game closes
6. store result against the game
7. export support ZIP with logs/test record

Investigate Desktop -> Game Mode / Gamescope handoff, but do not promise automatic session switching until proven.

### Troubleshooting notes / Bench

Each game should retain notes, failures, last tested runtime/profile, logs, and current disposition.

Support a Bench workflow that can restore/rollback when the user chooses and temporarily exclude problem games from normal bulk experimentation without deleting their history.

### Library Status / Reports

Provide a report showing working, untested, and benched/problem games; installed profile; test status; notes; latest relevant log; and runtime identity. Allow support-ZIP export.

---

## 16. Priority order

### P0 — runtime correctness

1. Preserve v3e.
2. Map remaining native modes.
3. Implement Off/Auto/Dynamic through the proven dispatcher architecture.
4. Run the regression matrix.
5. Test a second native Streamline MFG title, with Forza as a strong candidate.
6. Only then consider `runtime_verified=true`.
7. Update final app/runtime provenance only after validation.

### P1 — NR integration

1. Replace partial NR cherry-pick with complete chosen Proton-working NR path.
2. Preserve native y4my MFG.
3. A/B test MFG after NR changes.
4. Cold-start test NR acceptance.

### P1 — lifecycle hardening

1. Deep Clean state normalization.
2. Install -> Uninstall -> Install integration test.
3. Steam Verify / external deletion recovery tests.
4. Cache self-healing regression tests.
5. Improve misleading adoption/conflict messaging.

### P2 — product/UI

Implement Section 15 without changing runtime architecture as collateral work.

---

## 17. Do-not-regress checklist

1. Keep cached game-facing DLSS-G SetOptions permanently synthetic.
2. Keep cached GetState synthetic unless a controlled experiment explicitly changes it.
3. Never directly forward the cached game callback to real DLSS-G.
4. Never restore v3c's SetConstants -> `hkslDLSSGSetOptions()` re-entry.
5. Do not add a second bridge-triggered raw DLSS-G SetOptions call.
6. Consume native request state through the existing OptiScaler DLSS-G output path.
7. Preserve explicit interpolation-override precedence.
8. Preserve MFG unlock and max-count behavior.
9. Keep NR out of MFG validation.
10. Do not chase Reflex/RSYNC theories without new evidence.
11. Keep `runtime_verified=false` until controlled validation is finished.
12. Do not publish final app runtime provenance before behavior is verified.
13. Do not silently overwrite unrelated local work.
14. Use one conceptual variable per runtime experiment.
15. Preserve the golden v3e commit, tag, DLL, hash, and successful log.
16. Do not make Enabler a dependency/fallback again.
17. Preserve adoption lifecycle fixes.
18. Preserve verified cache rebuilding; never "fix" drift by trusting it.
19. Keep RTXForge Linux/Bazzite/Proton-focused.
20. Keep MFG and NR separable internally.
21. Preserve Forza's exact known game-side `winmm.dll`; do not generalize that exception to arbitrary proxy-shaped DLLs.
22. Remember the actual local GNOME AppImage path when testing rebuilt app versions.

---

## 18. Worker startup procedure

At the start of a new worker session:

```bash
cd ~/Repos/RTXForge
git fetch origin
git status --short
git branch --show-current
git rev-parse HEAD

cd ~/Repos/RTXForge-MFG
git fetch origin
git status --short
git branch --show-current
git rev-parse HEAD
git tag --points-at HEAD
```

Then:

1. Read this file completely.
2. Inspect current repo state before assuming any handoff HEAD is still current.
3. If RTXForge-MFG moved past v3e, read every intervening commit before editing.
4. Confirm the golden tag still resolves to the v3e checkpoint.
5. Do not redo AppImage v3e integration or rediscover the Forza proxy conflict; those are already handled.
6. Continue the highest-priority unfinished item.
7. Do not ask the user to repeat context already recorded here.
8. Never claim runtime success without a real game test.

---

## 19. Current mission in one sentence

**Finish and validate native MFG menu semantics around the working v3e bridge, then use Forza Horizon 6 as an important cross-game validation target, while preserving the rule that the game's Streamline instance supplies control state and OptiScaler's own DLSS-G instance performs the real rendering.**
