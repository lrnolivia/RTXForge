# RTXForge Worker Context

**Canonical development source of truth — 2026-09-10**

This file replaces the old overlapping `rtxforgenotes.md`, `update.md`, and temporary Astra handoff as the single worker-facing context document.

Read this file completely before changing RTXForge or RTXForge-MFG.

---

## 1. Current repositories and local source of truth

The temporary `-online` clones were used to refresh the normal local repositories and were then deleted.

Use these paths:

```text
~/Repos/RTXForge
~/Repos/RTXForge-MFG
```

### RTXForge

```text
Repository: lrnolivia/RTXForge
Branch: main
Known online HEAD at handoff: 3212375991dc8c4f41aa8f10a5eb01b97a8c4987
Tag at that point: v0.4.3
Commit: Restore F icon and deliver first Forge notes library polish
```

RTXForge is the Linux application, installer, package manager, game library, UI, backup/rollback layer, and runtime-orchestration repository.

### RTXForge-MFG

```text
Repository: lrnolivia/RTXForge-MFG
Branch: rtxforge-proton
Working v3e commit:
deca7b7a8f1953de3cf6fe2731ede440b3ddaadf

Tag:
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

Live DLL SHA256:
95580ebc7d2f562d6d99cd798587f757a51cd7bd52e24b0895c42414c3a3c2e8

Game:
The Outer Worlds 2

GPU:
RTX 4070

Status:
- Native 2X works
- Native 3X works
- Native 4X works
- repeated 2X -> 3X -> 4X transitions work
- no fatal observed in the successful run
- no DLSS-G SetOptions error observed in the successful run
- Off/Auto/Dynamic not fully implemented
- runtime_verified=false
```

Do not destroy or repoint the golden tag while active runtime work continues.

---

## 2. Product scope

RTXForge is a **Linux/Bazzite/Proton application** distributed as an AppImage.

The old Windows-client direction is retired.

Current platform direction:

```text
Linux / Bazzite / Proton
GNOME first
KDE integration may follow
Windows client: not active
```

The application should remain a Linux-native manager rather than turning into a cross-platform runtime injector during this work.

---

## 3. Target runtime stack

RTXForge should converge on one combined architecture while keeping MFG and NR separable internally.

### MFG

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

Required baseline:

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
- Do not make DLSS Enabler / Artur Headless a hidden dependency.
- Enabler is not an automatic fallback.
- If retained during transition/testing, isolate it clearly as legacy/experimental only.
- Cyberpunk 2077 remains an important proof case: the native Streamline route behaved normally, while the Enabler route exposed MFG but caused severe performance loss.
- Preserve MFG when changing NR.

### NR

The current 0.4.x-era NR composition is incomplete.

Current partial composition:

```text
y4my OptiScaler core
+ y4my NR forwarder
+ DLSS-Unlocked patched nvngx_dlssnr.dll
```

Target composition:

```text
DLSS-Unlocked complete Proton-working NR route
+ y4my native Streamline MFG route left untouched
```

The worker must not treat "copy the patched NR DLL" as the complete NR integration.

Bring over whatever NR-specific Proton plumbing the chosen DLSS-Unlocked path actually requires as a unit, including where applicable:

- forwarder
- patched NR runtime
- required file layout
- proxy/loading behavior
- configuration
- required runtime/Streamline dependencies
- Proton-specific loading expectations

Do **not** wholesale import DLSS-Unlocked MFG defaults if they would restore `nvngxfg` / Enabler as the generator.

If NR files overlap with the MFG stack, merge only the minimum required overlap and A/B test that native MFG performance and native menu exposure remain intact.

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

The Outer Worlds 2 now exposes its native:

```text
2X
3X
4X
```

and v3e makes those selections control OptiScaler's real DLSS-G output:

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

with no fatal and no `Couldn't set DLSSG options` error in the captured result.

This is the first confirmed working native-menu control path.

### Important limitation

This does **not** make the entire runtime production-verified.

Keep:

```text
runtime_verified=false
```

until the remaining mode semantics and regression matrix are completed.

---

## 5. Winning architecture — do not redesign casually

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
        | translate native control request into
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
- exposes enough MFG capability to reveal native 2X/3X/4X on the explicitly enabled RTXForge Ada route
- initial capability exposure is intentionally capped to the required native range rather than blindly mirroring every unlocked internal maximum

v3e also adds a consume helper so a generation handled by the output dispatcher is not unexpectedly consumed later by the old hook-side bridge path.

---

## 7. Why the earlier experiments matter

Do not repeat these dead ends without new evidence.

### v2 / v2a — failed

Experiment:
- early synthetic callbacks later forward/switch into real DLSS-G callbacks

Result:
- fatal

Meaning:
- TOW2 does not tolerate that cached-pointer lifecycle transition safely.

### v2b — safe boot base

Experiment:
- cached GetState and SetOptions remain synthetic permanently

Result:
- full boot

Meaning:
- permanent synthetic callbacks are the safe foundation.

### v2c — selector mapping proof

Experiment:
- permanent synthetic callbacks plus request capture

Result:
- boot
- selector mapping proven:

```text
2X -> 1
3X -> 2
4X -> 3
```

### v3 — wrong consumer

Experiment:
- consume bridge from normal `hkslDLSSGSetOptions`

Result:
- no useful consumer hit

### v3a — wrong consumer probe

Experiment:
- probe DLSS-G evaluation path

Result:
- no useful consumer hit

### v3b — useful diagnostic, not apply proof

Experiment:
- canary in `hkslSetConstants`

Result:
- every pending generation was visible

Meaning:
- `SetConstants` could observe bridge state.

It did **not** prove DLSS-G was safe to re-enter there.

### v3c — failed apply and important boundary

Experiment:
- after SetConstants saw a pending generation, call `hkslDLSSGSetOptions()`

Result:
- fatal before main menu

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

The unlock itself had already succeeded, so do not blame `MfgUnlock::TryApply()` for this failure without new evidence.

### v3d — correct consumer identified

Experiment:
- remove v3c re-entry
- observe bridge from `DLSSG_Dx12::Dispatch()`

Result:
- every pending native generation appeared in OptiScaler's actual DLSS-G output dispatcher
- source viewport `1`
- OptiScaler output viewport `0`
- `_maxInterpolationCount=5`
- configured output count remained `1`

The viewport difference is valid: the game-native instance is the control source; OptiScaler's own instance is the output generator.

### v3e — working apply

Instead of making a new Streamline call:

1. Read the newest native bridge generation inside `DLSSG_Dx12::Dispatch()`.
2. For native `sl::DLSSGMode::eOn`:
   - take `numFramesToGenerate`
   - preserve explicit interpolation override precedence
   - clamp the count
   - write the value to `FGDLSSGInterpolationCount` using `set_volatile_value()`
3. Mark that generation consumed.
4. Let the existing dispatcher continue normally.
5. Existing code updates `_framesToInterpolate`, builds `sl::DLSSGOptions`, and makes its normal raw `StreamlineProxy::DLSSGSetOptions()` call.

No second DLSS-G call is introduced.

That is why v3e works where v3c did not.

---

## 8. Current v3e repository changes

The v3e commit changes four files.

### `.github/workflows/rtxforge-proton.yml`

Runtime capability advanced to:

```text
RTXForge.NativeMfgMenu.v3e
```

### `OptiScaler/framegen/dlssg/DLSSG_Dx12.cpp`

v3e:

- reads native bridge state from inside the real OptiScaler DLSS-G dispatcher
- applies only ordinary native `eOn` requests in the current experiment
- reads native `numFramesToGenerate`
- preserves `FGDLSSGOverrideInterpolationCount` precedence
- clamps the requested count
- writes it via `FGDLSSGInterpolationCount.set_volatile_value(...)`
- consumes the generation
- leaves the existing raw DLSS-G output call intact

Non-`eOn` modes are currently logged/handled without fully translating their semantics.

### `OptiScaler/hooks/Streamline_Hooks.cpp`

Adds the bridge consumption helper:

```cpp
void StreamlineHooks::consumeNativeDlssgRequest(uint64_t generation)
```

It only marks the generation consumed if that generation is still current.

### `OptiScaler/hooks/Streamline_Hooks.h`

Declares the consume helper.

The read-only bridge snapshot helper introduced for the v3d probe remains part of the path.

---

## 9. Immediate Astra mission

Continue from **v3e**.

Do not reopen the old "how do we make 2X/3X/4X work?" problem unless an actual regression appears.

The immediate goal is:

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
modify the state/options that the existing dispatcher is already about to send
        ↓
existing raw StreamlineProxy::DLSSGSetOptions()
```

### C. Preserve explicit override precedence

An explicit RTXForge / OptiScaler interpolation override must continue to win over the native game multiplier.

v3e already preserves this for native `eOn`.

### D. Keep one conceptual variable per experiment

Do not simultaneously:
- alter mode translation
- alter callback lifetime
- alter MFG unlock behavior
- alter NR
- alter Reflex behavior
- alter output route

Change one thing, build it, test it, preserve the log.

---

## 10. Validation required before `runtime_verified=true`

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

After TOW2 is stable, test the same architecture in at least one additional native Streamline MFG game before calling the bridge generically validated.

Only after the controlled matrix succeeds should app/runtime provenance move to:

```text
runtime_verified=true
```

---

## 11. Runtime experiment discipline

For each RTXForge-MFG experiment:

```text
verify exact source HEAD
        ↓
change one conceptual variable
        ↓
git diff --check
        ↓
commit
        ↓
push
        ↓
identify the exact GitHub Actions run for that commit
        ↓
download the exact artifact
        ↓
verify:
  - PE / MZ identity
  - fork_commit
  - declared capability
  - SHA256
  - compiled marker
        ↓
back up live dxgi.dll
        ↓
deploy exact artifact
        ↓
verify live SHA256
        ↓
test
        ↓
preserve relevant log
```

A successful compile, CI run, metadata match, or deployment is **not** runtime success.

Do not mark success until a real game test proves the behavior.

---

## 12. App state that must be preserved

### Adoption lifecycle hotfix — implemented

Previous bug:

```text
Install
-> Uninstall
-> install again
-> stale historical state forced "Adoption requires a recognizable OptiScaler proxy and INI"
```

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

Install decisions must follow what is on disk now.

Correct decision shape:

```python
if managed_install_present:
    update_or_repair()
elif recognizable_external_proxy_present and recognizable_external_ini_present:
    offer_adoption()
else:
    fresh_install()
```

Never do:

```python
if game_was_managed_before:
    adopt()
```

Implemented behavior to preserve:

- "Recognize previous installs" no longer forces adoption on a clean game.
- Adoption requires a recognizable external proxy and INI that exist now.
- Clean post-uninstall games fall through to Fresh Install.
- Incomplete external installs are not silently adopted.
- CLI says `ADOPT` only when adoption actually occurred.
- Focused regression tests cover clean fresh install, recognizable external adoption, and incomplete external state.

Still desired:

- Deep Clean should explicitly normalize/refresh managed state after completion.
- Add a real Install -> Uninstall -> Install integration fixture.
- Add Steam Verify / externally removed managed-files integration coverage.

### Package-cache self-healing — implemented

Prepared payload cache is disposable derived state.

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

partial extraction without manifest
-> discard partial derived extraction
-> rebuild from pinned source
```

Security rule:

> Self-healing must never mean accepting drift.

A bad pinned source archive still causes refusal.

Readonly/dry-run:

```text
invalid prepared cache
-> explain that normal Prepare/Install is required
-> do not mutate cache
```

Still desired regression coverage:

- listing drift rebuilds automatically
- partial extraction without manifest rebuilds automatically
- readonly mode reports drift without modifying files
- regenerated manifest verifies exactly

---

## 13. Cleaned product and UI backlog

These are product requirements, not instructions to destabilize the runtime while v3e validation is active.

Finish runtime validation first unless a separate worker is explicitly assigned UI work.

### A. Library cards and details

Improve the game cards/details so users can understand a game's RTXForge state at a glance.

Desired direction:

- Remove unnecessary padding around hero artwork; use intentional gutters rather than inset imagery.
- Use the game's/accent color more strongly in the detail panel, including darker and brighter tonal variants rather than one flat accent.
- Make profile/status badges universal and visually consistent across all games:
  - `NR + MFG`
  - `MFG`
  - `Unavailable`
  - other stable status classes as needed
- Show more useful applied-state information directly on cards/details:
  - installed profile
  - active fixes
  - compatibility/profile notes
  - runtime status
  - test status
- Genre may be shown as small pills, but do not assume genre is the most useful secondary metadata. Prefer metadata that helps the user understand compatibility and configuration.
- Add game description where it improves the details view without overwhelming the library.
- Add **Open Directory**.
- Add **Launch Game**.
- Hide SteamGridDB attribution behind a small unobtrusive credit/info pill rather than dedicating prominent card space to it.
- Improve Non-Steam metadata by matching titles to likely Steam App IDs when confidence is high enough, so artwork/metadata do not default to generic "Non-Steam Game".

### B. Install-profile controls

- Put **NR + MFG** before **MFG**.
- Make the active profile selection significantly more obvious.
- Consider centering the profile controls if it improves hierarchy.
- Match profile-toggle backgrounds to the visual language chosen for each profile/status class.
- Keep profile/status colors consistent across cards, filters, and detail panels.

### C. Library density and scrolling

- Reduce the size and spacing of library-view pills.
- The default library density should show roughly **2 to 2.5 poster rows** in the usable viewport.
- The large header should condense/collapse as the user scrolls the library, preserving access to core controls without consuming poster space.
- Avoid oversized permanent chrome.

### D. Progress/status presentation

The current full-width status bar is disliked.

Explore:

- a smaller floating progress/status surface
- a compact progress bar
- tasteful icon animation for active operations
- clear elapsed time and counts without taking over the width of the window

Do not trade clarity for decorative motion.

### E. Integrated game testing

Add a **Test** workflow designed specifically for troubleshooting installed profiles.

Desired behavior:

1. User chooses **Test** on a game.
2. RTXForge records the test start and relevant current configuration/runtime identity.
3. RTXForge launches the game.
4. RTXForge captures/collects relevant logs while that launched test session is active.
5. Logging/session capture stops when the tested game closes.
6. The result is stored against that game for later troubleshooting.
7. A support ZIP can be exported containing the test record and collected logs.

Investigate whether this can survive a Desktop -> Game Mode transition.

If feasible, offer a launch/test target such as:

```text
Desktop
Game Mode / Gamescope
```

Do not promise automatic reboot/session switching until the mechanism is actually proven.

### F. Troubleshooting notes and "bench" workflow

Each game should be able to retain troubleshooting context:

- user notes
- detected/recorded test failures
- last tested runtime/profile
- relevant logs
- current disposition

Support a **Bench** concept for games that should temporarily stop receiving active experimentation.

Possible behavior:

```text
Problem detected / user marks issue
        ↓
offer restore/rollback
        ↓
Bench game
        ↓
keep notes + logs + last-known state
        ↓
exclude from normal "working" view / bulk changes as appropriate
```

Do not automatically restore or bench without a clear user action.

### G. Library Status / Reports

Add a report surface in Settings or another appropriate top-level area that summarizes:

- working games
- untested games
- benched/problem games
- current installed profile
- test status
- user notes
- most recent relevant log/test
- runtime version/capability where useful

Allow exporting a troubleshooting ZIP containing the selected report/log evidence.

The report should help answer:

> "Which games are good, which are broken, what did I try, and what runtime/profile was involved?"

rather than acting as a generic analytics dashboard.

---

## 14. Backlog priority

Unless the task is explicitly delegated differently:

### P0 — runtime correctness

1. Preserve v3e.
2. Map remaining native modes.
3. Implement Off/Auto/Dynamic through the proven dispatcher architecture.
4. Run the regression matrix.
5. Test a second native Streamline MFG title.
6. Only then consider `runtime_verified=true`.
7. Update RTXForge runtime provenance only after validation.

### P1 — NR integration

1. Replace partial NR cherry-pick with the complete chosen Proton-working NR path.
2. Preserve native y4my MFG.
3. A/B test MFG after NR changes.
4. Cold-start test NR acceptance.

### P1 — lifecycle hardening

1. Deep Clean state normalization.
2. Install -> Uninstall -> Install integration test.
3. Steam Verify / external deletion recovery tests.
4. Cache self-healing regression tests.

### P2 — product/UI

Implement the cleaned backlog in Section 13 without changing the runtime architecture as collateral work.

---

## 15. Do-not-regress checklist

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

---

## 16. Worker startup procedure

At the start of a new worker session:

```bash
cd ~/Repos/RTXForge
git status --short
git branch --show-current
git rev-parse HEAD

cd ~/Repos/RTXForge-MFG
git status --short
git branch --show-current
git rev-parse HEAD
git tag --points-at HEAD
```

Then:

1. Read this file completely.
2. Inspect current repo state before assuming the handoff HEAD is still current.
3. If RTXForge-MFG has moved past v3e, read every intervening commit before editing.
4. Confirm the golden tag still resolves to the v3e checkpoint.
5. Continue the highest-priority unfinished item.
6. Do not ask the user to repeat context already recorded here.
7. Never claim runtime success without a real game test.

---

## 17. Current mission in one sentence

**Finish and validate native MFG menu semantics around the working v3e bridge, while preserving the rule that the game's Streamline instance supplies control state and OptiScaler's own DLSS-G instance performs the real rendering.**
