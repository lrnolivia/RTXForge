CURRENT RUNTIME PRIORITY — 0.4.2+

TARGET STACK — THIS IS THE NEW SOURCE OF TRUTH

RTXForge should converge on one combined runtime stack:

```text
MFG
Game native Streamline DLSS-G
        ↓
y4my4my4m OptiScaler core
        ↓
native NVIDIA DLSS-G output
        ↓
Ada MFG unlock
        ↓
Blackwell kernels

NR
DLSS-Unlocked complete Proton-working NR route
        ↓
use its NR-specific Proton plumbing as a complete unit
        ↓
forwarder + patched NR runtime + required layout/config/dependencies
```

Required MFG configuration:

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

IMPLEMENTATION RULES

- Native Streamline DLSS-G is the preferred and default MFG route.
- y4my remains the OptiScaler/MFG core because its Ada MFG unlock and Blackwell-kernel path are the pieces we want.
- Do NOT route normal MFG through `nvngxfg`.
- Do NOT use Artur / DLSS Enabler Headless in the preferred stack.
- Do NOT install Enabler as a hidden default dependency.
- Enabler is not part of the target architecture. If retained anywhere during transition/testing, it must be clearly isolated as legacy/experimental fallback and never selected automatically.
- Cyberpunk is the key proof case: native Streamline behaves normally; Enabler causes severe performance loss.
- NR must stop being a partial cherry-pick. The desired NR implementation is the COMPLETE DLSS-Unlocked Proton-working NR route, not just its patched `nvngx_dlssnr.dll`.
- Import all NR-specific pieces DLSS-Unlocked requires for Proton: forwarder, patched runtime, file placement/layout, proxy behavior, config, required Streamline/runtime dependencies, and Proton-specific loading expectations.
- Do not wholesale import DLSS-Unlocked's MFG defaults if they would re-enable `nvngxfg` / Enabler. Take its full NR path while preserving y4my native Streamline MFG.
- MFG and NR should remain separable in RTXForge internally so NR can be repaired/replaced without rewriting the known-good MFG route.

CURRENT CODE STATUS / IMPORTANT GAP

The present 0.4.2-era code already has the desired native Streamline MFG direction, but its NR path is still only partially migrated:

```text
CURRENT NR COMPOSITION
y4my OptiScaler core
+ y4my NR forwarder
+ DLSS-Unlocked patched nvngx_dlssnr.dll
```

That is NOT yet the final target.

The worker should replace the partial NR composition with:

```text
FINAL NR COMPOSITION
DLSS-Unlocked complete Proton-working NR route
+ y4my native Streamline MFG route left untouched
```

Do not change the MFG route while doing this.

TARGET RESULT

```text
Bazzite / Proton
MFG ✓  native Streamline / y4my
NR  ✓  DLSS-Unlocked complete Proton NR route
```

If DLSS-Unlocked's NR route requires files that overlap with the y4my MFG stack, merge only the minimum overlapping pieces necessary and prove with A/B tests that MFG performance and menu exposure remain intact.

---


P0 INSTALL / UNINSTALL ADOPTION LIFECYCLE — IMPLEMENTED HOTFIX

Observed behavior:

```text
1. User runs RTXForge Uninstall.
2. RTXForge correctly removes the managed OptiScaler/runtime files.
3. User later selects MFG or NR + MFG again.
4. Every previously managed game fails with:
   "Adoption requires a recognizable OptiScaler proxy and INI"
```

This is a state-machine bug, not a reason to manually restore DLLs.

Expected lifecycle states:

```text
CLEAN
No recognizable OptiScaler install
No active RTXForge-managed stack
→ Fresh Install allowed

MANAGED
RTXForge manifest + managed files present
→ Repair / Change Profile / Uninstall allowed

EXTERNAL
Recognizable OptiScaler proxy + INI present
No valid RTXForge managed-state ownership
→ Adoption may be offered
```

A game that has just completed RTXForge Uninstall must transition to:

```text
CLEAN
```

not:

```text
ADOPTION REQUIRED
```

INSTALL DECISION RULE

The install path should be based on the files/state that exist NOW, not only historical metadata.

Required logic:

```python
if managed_install_present:
    update_or_repair()

elif recognizable_external_proxy_present and recognizable_external_ini_present:
    offer_adoption()

else:
    fresh_install()
```

Do NOT do this:

```python
if game_was_managed_before:
    adopt()
```

Do NOT require adoption because stale historical metadata says RTXForge previously touched the game.

DEFENSIVE FALLBACK

Even if stale metadata survives unexpectedly:

```text
adoption requested
+
no recognizable proxy
or
no recognizable INI
```

must not hard-fail the install.

Instead:

```text
clear stale adoption state
rescan
fall back to Fresh Install
```

This protects against:

```text
RTXForge Uninstall
Deep Clean
manual file deletion
Steam Verify
restored game backups
external cleanup tools
game updates replacing runtime files
```

UNINSTALL MUST CLEAR MANAGED STATE

A successful Uninstall must:

```text
remove RTXForge-managed runtime/proxy files
remove or retire the active managed-install manifest
clear installed profile
clear adoption flag/state
clear stale runtime-route/provider state
clear stale "managed" markers that would force adoption
rescan the game directory
recompute installation state from disk
refresh the UI immediately
```

Expected UI after uninstall:

```text
Game
Status: Not Installed

[ NR + MFG ]
[ MFG ]
```

No adoption warning should appear unless a real, currently present external OptiScaler installation is detected.

DEEP CLEAN MUST DO THE SAME

Deep Clean should also force:

```text
clear managed/adopted state
rescan
recompute state from disk
```

It must not leave a historical database row in a state that blocks future fresh installs.

ADOPTION POLICY

Adoption is ONLY for:

```text
a currently present external OptiScaler installation
with a recognizable proxy
and a recognizable OptiScaler INI
```

Adoption is NOT for:

```text
a game RTXForge used to manage
a game that was just uninstalled
a game with only stale metadata
a game where proxy/INI files no longer exist
```

REGRESSION TESTS / STATUS

Add automated lifecycle tests for:

```text
Fresh Install
→ Uninstall
→ Fresh Install again

Fresh Install
→ Deep Clean
→ Fresh Install again

Managed Install
→ Steam Verify / files removed externally
→ Rescan
→ Fresh Install allowed

External OptiScaler present
→ Adoption offered

External OptiScaler incomplete
(proxy only or INI only)
→ No forced adoption
→ Fresh Install allowed or explicit conflict handling
```

Implemented hotfix behavior:

```text
[x] "Recognize previous installs" no longer forces adoption on a clean game.
[x] Adoption occurs only when a recognizable OptiScaler proxy + INI exist now.
[x] Clean post-uninstall games fall through to Fresh Install.
[x] Incomplete external installs are not silently adopted; normal conflict handling remains active.
[x] CLI confirmation says ADOPT only when an external install was actually adopted.
[x] Focused regression tests cover clean fresh install, recognizable external adoption, and incomplete external state.
```

Broader lifecycle hardening still desired:

```text
[ ] Deep Clean should explicitly normalize/refresh managed state after completion.
[ ] Add a full end-to-end Install → Uninstall → Install integration fixture on the real Games-backed test harness.
[ ] Add Steam Verify / externally removed managed-files integration coverage.
```

---



P0 PACKAGE CACHE SELF-HEALING — IMPLEMENTED HOTFIX

Observed failure:

```text
Failed: Preparing and verifying MFG Only
transactions.Refusal: Payload listing drift
```

Root cause:

```text
packages/<pinned-archive-sha>/files.json
```

and the derived:

```text
packages/<pinned-archive-sha>/payload/
```

had drifted apart. Because the prepared payload is reconstructible derived state, this must not block every game install forever.

Required behavior, now implemented in `scripts/packages.py`:

```text
valid payload + matching manifest
→ reuse

manifest/listing/hash/source drift
→ do NOT trust the cache
→ delete only derived payload/manifest
→ keep the pinned source archive
→ verify the pinned source archive hash
→ re-extract
→ regenerate files.json
→ verify the rebuilt payload
→ continue install

partial payload with no manifest
→ discard derived partial extraction
→ rebuild from pinned source
```

Security rule:

> Self-healing must never mean accepting drift.

The app must still verify the rebuilt payload against the pinned source. A bad cached source archive remains a refusal instead of being silently trusted.

Readonly/dry-run behavior:

```text
invalid prepared cache
→ report that Prepare/Install is required
→ do not mutate cache
```

Regression coverage:

```text
[ ] listing drift rebuilds automatically
[ ] partial extraction without manifest rebuilds automatically
[ ] readonly mode reports drift without changing files
[ ] rebuilt manifest verifies exactly
```

User-facing result:

A stale prepared runtime cache should produce a short progress/log message such as:

```text
Repairing cache   Prepared payload drift detected; rebuilding from pinned source
```

and then proceed normally instead of dumping a fatal `Payload listing drift` traceback.

---

finish the new engine and then:

no padding on the hero images in the panels, they should've have gutters. and use the accent color more in that panel. you can use darker and brighter variants of it. the SteamGridDB credits should be hidden behind a small pill button. more information about the applied mods/fixes/profiles etc should be visible on the cards. add the genre info there in small pills. maybe add game description. add buttons to open directory and as well as launch the game.

add a Test button that launches the game and automatically takes and stores logs. it should monitor the game being launched and stop taking notes once the game is closed. if possible this should persist if changing to GameMode. if possible, the launch/test options should have a toggle or option to launch in desktop mode or restart in GameScope and THEN launch. idk what's possible.

make the logs accessible in app for troubleshooting later. add notes section to mark games with issues, let the user add notes and suggest the game be restored and placed on a 'bench' until a solution is found. add a 'Library Status/Reports' option in settings to give you an overview of games that work and don't work alongside the notes the user adds. package a .zip with any logs created as well.

the MFG/Unavailable/NR + MFG tags should be universal across games so you can see which is which at glance without having to read them.

match the toggles up top background colors to whatever we decide on for their colors.

the header section should condense/collapse when you scroll the library, the default size setings should two two and a half rows of game posters at once.

i dislike the full width status bar, can we have a floating bar with a smaller progress bar? maybe more icon animations?

the library view pills shouldn't be so big or spaced out.

install profile toggles should be more obvious. maybe even centered? and lets put NR + MFG first.

match Non-Steam games to their Steam IDs to get better meta data instead of just saying "Non-Steam Game". i am also not sure that genre tags are the most relevant information to display under each game.
