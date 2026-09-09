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
