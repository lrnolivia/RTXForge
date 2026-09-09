# v3 audit and rewrite

Audited the supplied v3 Python source, launcher, package manifests, and pinned upstream source. The bundled opaque launcher was not executed during inspection. Extracted archive members were checked for traversal, links, duplicates and oversized entries.

| Baseline finding | RTXForge decision |
|---|---|
| NR initially disabled | NR + MFG explicitly writes Enabled=true at install; no in-game toggle required to initialize it. |
| NR-only and fallback branches | Removed. Both routes require native frame-generation evidence. |
| One-at-a-time workflow | Explicit batch selection, all-target preflight, sequential transactional application. |
| Late manifest writes and unjournaled repair | Each target uses backups, before/after hashes and a recoverable transaction journal; batch records track partial completion. |
| Broad injector/addon moves | Conflicts block; exact owned files are handled with recovery copies. |
| Global NR unlink and backup-tree deletion | Retained at user request as a separate previewed action, with verified recovery copies before any removal and explicit confirmation. |
| Native-provider restore from historical mappings | Not imported; native files remain protected. |
| Size-only NR selection and duplicate archive members | Authenticate pinned archive and select the exact root NR member. |
| NR panel called unconditionally | Deferred at user request. Stock inactive panel remains in MFG Only; optional source patch retained. |
| Changing downloaded releases | Versioned provider manifest pins release, hashes and headless Git blob identities. Upgrades are explicit. |

The v3 profile is preserved: headless Artur route; Ada MFG unlock and kernels; automatic interpolation/reflex markers; forced DMFG disabled; flip metering/reflex sync disabled. NR starts enabled with WorkingScale 0.70, DualFeature=true, PreUpscale=false, one pass and the baseline sharpness profile. Already-migrated user tuning survives subsequent installs.

## Verification on 2026-09-09 UTC

- Real pinned upstream archive, headless module and NR model downloaded and verified successfully.
- Six production-path fixture checks passed at 06:38 UTC: mixed routes and startup NR; route-switch rollback; tuning preservation; interrupted-write recovery; conflicting/duplicate target refusal; owned uninstall/rollback with unchanged native-file/save controls.
- Focused global cleanup check passed at 06:43 UTC: recovery of files and empty directories, external drift refusal, unrelated-file preservation, and lab/recovery scan exclusion.
- No installed game was modified or launched. These are installer checks, not graphics/runtime proof.

Local reports:

- `/var/mnt/Games/Ada-Lab/RTXForge/verification/26645fa15e3d491d927bd910e87d00bd/result.json`
- `/var/mnt/Games/Ada-Lab/RTXForge/verification/567bdde37ced4870bb42cf0c5ab6d504/result.json`

## Remaining limits

The stock NR panel is visible in MFG Only. Windows build files are deliberately inactive. Linux storage defaults are machine-specific configuration, with no general Windows storage adapter yet. The installer does not set launch options automatically or establish game compatibility from successful file deployment. A batch is recoverable per target, not an all-games atomic transaction. Stale operation locks require inspection of recovery state before manual removal.

## Panel build activated

At the user’s subsequent request, `.github/workflows/windows-build.yml` now builds the bounded patch on Windows 2022 from the same pinned upstream commit. The historical deferred status above describes the initial release. The patch reads `[RTXForge] NrPanel` once when the panel would first render; subsequent in-game NR effect toggles do not change panel visibility. Missing settings preserve upstream visibility. Import verifies build policy, upstream commit, SHA-256 and the embedded policy marker. Runtime panel behavior still requires game verification.

## Repair crash correction

Legacy manifest import referenced `re.fullmatch` without importing `re`, causing a NameError after game selection. The missing import is fixed. Focused Linux and Windows legacy-manifest regression checks pass. Unexpected menu exceptions now retain the traceback and return to the menu rather than closing the terminal.

## Report-driven correction and panel result

The user's 0.1.1 report exposed overbroad conflict checks: RenoDX attribution text was treated as an injector, as were native dependencies under other executables and engine folders. Conflict checks now examine active binaries beside the selected executable. Identified Microsoft Windows Image Helper DLLs are preserved and fingerprinted as inputs. Unknown adjacent loaders still block. The interactive menu can explicitly exclude blocked games with SKIP before presenting a new APPLY preview.

A read-only repair preflight against all 19 exact targets in the report completed: 18 ready, Forza Horizon 6 blocked by its third-party winmm.dll. No game files were written. A focused regression verified preservation of attribution text, native dependency subdirectories and identified Microsoft dbghelp.dll, while an unknown winmm.dll still blocks.

GitHub Windows build 34320885964 succeeded. The artifact archive hash, x64 PE identity, embedded policy marker and DLL hash were verified; see panel-build.json. The loader was imported into RTXForge's prepared cache and bundled with 0.1.2. No installed game received it automatically.

## 0.1.3 interaction update

Added animated activity and elapsed time around long operations, with per-game batch counts and plain-terminal fallback. Removed the preparation prompt and separate SKIP confirmation. Excluded games are listed explicitly; the interactive batch now has one final yes/no confirmation. Cleanup and recovery also use yes/no. Command-line confirmation flags retain their existing contract. Focused checks covered default cancellation, progress completion/error cleanup and animated terminal output. No game operations were run for this UI change.
