# RTXForge

**GeForce tools, built for Linux.** RTXForge is a Linux/Bazzite/Proton graphics-runtime manager for modern NVIDIA DLSS features, with verified payloads, explicit previews, backups, rollback, and per-game compatibility handling.

> **Worker / development context:** read [`WORKER_CONTEXT.md`](WORKER_CONTEXT.md) before changing runtime architecture, package providers, adoption state, cache behavior, or the current UI backlog.

## Current direction

RTXForge is a Linux application distributed as an AppImage. There is no active Windows client.

The preferred MFG route is:

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

DLSS Enabler / `nvngxfg` is **not** the preferred route, hidden dependency, or automatic fallback.

NR remains a separate track. The target is the complete Proton-working NR route from DLSS-Unlocked, integrated without replacing or destabilizing the known-good MFG path.

## Native MFG menu milestone

The active runtime fork is:

- `lrnolivia/RTXForge-MFG`
- branch: `rtxforge-proton`
- known-working checkpoint: `deca7b7a8f1953de3cf6fe2731ede440b3ddaadf`
- tag: `RTXForge-NativeMFG-v3e-working`

In The Outer Worlds 2 on an RTX 4070 under Proton, v3e proved that the game's native **2X / 3X / 4X** selector can control OptiScaler's real DLSS-G generated-frame count:

```text
2X -> 1 generated frame
3X -> 2 generated frames
4X -> 3 generated frames
```

Repeated live transitions worked without a fatal error or DLSS-G SetOptions error.

This is **not yet full runtime verification**. Off/Auto/Dynamic semantics and the broader regression matrix still need to be completed, so `runtime_verified=false` remains correct.

The key implementation rule is that the game's early cached `slDLSSGSetOptions` callback stays permanently synthetic. Native requests are captured as control state and consumed by OptiScaler's existing `DLSSG_Dx12::Dispatch()` path. Do not re-enter real DLSS-G from the cached callback or from `hkslSetConstants()`.

## Native GNOME desktop

The desktop app provides a unified game library with install profiles, artwork, metadata, package preparation, backups, rollback, repair, uninstall, cleanup, and per-game status.

Current product/UI backlog and worker priorities are maintained in [`WORKER_CONTEXT.md`](WORKER_CONTEXT.md).

## Install profiles

| Route | Behavior |
|---|---|
| **NR + MFG** | Native Streamline / Ada MFG plus the selected NR layer. |
| **MFG Only** | Native Streamline / Ada MFG with NR disabled and no NR payload. |

There is no NR-only route.

## Run the desktop app

Extract the release and double-click **RUN RTXFORGE GUI**.

See the [desktop guide](docs/DESKTOP.md).

## Run the CLI

Extract the release and double-click **RUN RTXFORGE**, or run:

```bash
bash '/home/loew/Repos/RTXForge/START HERE.sh'
```

Choose Install / update, choose a route, then select game codes or `ALL`. Preparation runs automatically with visible progress. Review the proposed changes and answer the single final confirmation. Close selected games before applying changes.

Payloads download on first use and are verified before installation. Python 3 and a 7-Zip-compatible command are required.

## Install / uninstall lifecycle

RTXForge determines install state from what exists **now**, not merely from historical metadata.

Expected states:

```text
CLEAN
No recognizable OptiScaler install
No active RTXForge-managed stack
-> Fresh Install allowed

MANAGED
RTXForge manifest + managed files present
-> Repair / Change Profile / Uninstall allowed

EXTERNAL
Recognizable OptiScaler proxy + INI present
No valid RTXForge ownership
-> Adoption may be offered
```

A completed RTXForge Uninstall must return the game to `CLEAN`. A historical record alone must never force adoption.

The adoption hotfix is implemented: clean post-uninstall games can be installed again, and adoption is offered only when a recognizable external OptiScaler proxy **and** INI are currently present.

## Prepared-package cache self-healing

Prepared package payloads are disposable derived cache.

If payload listing/hash/manifest state drifts, RTXForge does **not** accept the drift. It discards only the invalid derived payload/manifest, re-verifies the pinned source archive, rebuilds the payload, regenerates `files.json`, verifies the result, and continues.

Readonly/dry-run mode remains non-mutating and reports that a normal Prepare/Install is required to repair stale cache.

## Recovery and advanced cleanup

RTXForge includes repair, owned-file removal, batch rollback, global DLSS5 cleanup, and cleanup restoration.

Global cleanup previews the candidate NR files and `_DLSS5_Backup` directories and verifies recovery copies before removal. Recovery storage and Ada-Lab are excluded.

Additional roots can be supplied explicitly:

```bash
./rtxforge cleanup --roots /path/to/library --dry-run
./rtxforge cleanup --roots /path/to/library
./rtxforge restore-cleanup --cleanup-record /path/printed/after/cleanup.json
```

Batch installation stops on failure and records completed/interrupted targets for rollback. New external changes block rollback instead of being overwritten.

## Explicit or mixed-route batches

Example target file:

```json
[
  {"game": "/path/to/Game A", "exe": "Game.exe", "mode": "nr-mfg"},
  {"game": "/path/to/Game B", "exe": "bin/Game.exe", "mode": "mfg-only"}
]
```

Then:

```bash
./rtxforge prepare --mode nr-mfg
./rtxforge install --targets targets.json --dry-run --details
./rtxforge install --targets targets.json
```

Recognized external installations can be adopted with `--adopt-existing`. Conflicting unrelated injectors still block the affected game.

## Game-native files and Streamline

RTXForge does not globally rewrite native game DLSS/Streamline files or launch options.

It uses its own private runtime under `OptiScaler/streamline` for DLSS-G output while leaving game-native Streamline files untouched. The preview shows the Proton DLL override that must be merged with existing launch options.

Native frame-generation evidence is required for automatic selection, and detected anti-cheat blocks automatic selection.

## Storage and portability

The delivered development configuration is pinned to Lauren's Btrfs Games drive. Cache, backups, and journals live under:

```text
/var/mnt/Games/Ada-Lab/RTXForge
```

with a 100 GiB reserve and no fallback to the system drive.

Other machines must explicitly configure `provider.json` or pass `--provider` with an adapted provider file.

The storage adapter is separate from the reusable installer core.

## Runtime provenance

RTXForge-MFG CI builds the PE runtime for Proton. A downloaded build artifact can be imported with:

```bash
./rtxforge import-loader --loader /path/to/extracted/artifact
```

Importing a runtime prepares future installations; existing games must still be explicitly updated.

Compilation, metadata verification, binary identity checks, and deployment do **not** by themselves prove runtime behavior. Controlled game testing remains required.

See [audit and verification](docs/AUDIT.md) and [source provenance](docs/PROVENANCE.md).
