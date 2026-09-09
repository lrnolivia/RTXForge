# RTXForge

**GeForce tools, built for Linux.** A colorful batch installer for the supplied Bazzite v3 headless OptiScaler stack, rewritten in Python with explicit previews, backups and rollback.

## Native GNOME desktop

**0.3.1** separates the NR payload from the protected headless MFG pipeline, pins the patched NR model, filters Steam tools and apps, fixes full-resolution artwork sizing, restores vivid green accents, and samples each game’s artwork for its card and details accents. Changing package providers or deployment methods should use a full uninstall/reinstall. Proton NR reliability remains unverified.

**0.3.0** adds a unified poster library, automatic keyless SteamGridDB covers, metadata, profile buttons, floating action panels, one-click whole-library install/uninstall and expanded settings. It uses solid colors and defaults to tall posters; capsules and list views are available. Hardware prerequisites are checked before installation.

Extract and double-click **RUN RTXFORGE GUI**. See [desktop guide](docs/DESKTOP.md). The custom repository option is a future UI placeholder only.

## Run the CLI

Extract the release ZIP and double-click **RUN RTXFORGE**. Or run:

```bash
bash '/home/loew/Repos/RTXForge/START HERE.sh'
```

Choose Install / update, choose a route, then select several game codes or type `ALL`. Preparation runs automatically with visible progress. Review the proposed changes and answer `y` to the single final confirmation. Close the selected games first. Payloads download on first use and are verified before installation. Python 3 and a 7-Zip command are required; the desktop launcher opens an installed terminal.

| Route | Behavior |
|---|---|
| NR + MFG | NR enabled at installation/startup, plus headless MFG. |
| MFG Only | Headless MFG, without the NR DLL or NR forwarder. |

There is no NR-only route. The v3 NR profile uses WorkingScale 0.70, DualFeature enabled and Before Upscaling disabled. Existing tuning is retained after profile migration; selecting NR + MFG always turns NR on before the next launch.

**Panel fix built:** the 0.1.3 ZIP includes the verified RTXForge Windows loader. `[RTXForge] NrPanel=0` hides the NR panel for MFG Only; `1` displays it for NR + MFG. GitHub compilation and DLL identity checks passed; in-game behavior still needs verification.

## Recovery and advanced cleanup

The menu includes repair, removal of owned files, batch rollback, **global DLSS5 cleanup**, and cleanup restoration. Global cleanup is retained as a separate advanced action. It previews the two NR filenames and `_DLSS5_Backup` directories, verifies recovery copies of every candidate before removal, and uses one yes/no confirmation. Recovery storage and Ada-Lab are excluded. It can affect NR installations outside RTXForge: review the candidate list.

The default global scan covers the configured Games mount. Additional library roots can be supplied explicitly:

```bash
./rtxforge cleanup --roots /path/to/library --dry-run
./rtxforge cleanup --roots /path/to/library
./rtxforge restore-cleanup --cleanup-record /path/printed/after/cleanup.json
```

Batch installation stops on a failure and records completed and interrupted targets for rollback. New external changes block rollback instead of being overwritten. Keep the printed records and recovery files.

## Explicit or mixed-route batches

Create a JSON file such as:

```json
[
  {"game": "/path/to/Game A", "exe": "Game.exe", "mode": "nr-mfg"},
  {"game": "/path/to/Game B", "exe": "bin/Game.exe", "mode": "mfg-only"}
]
```

```bash
./rtxforge prepare --mode nr-mfg
./rtxforge install --targets targets.json --dry-run --details
./rtxforge install --targets targets.json
```

Recognized existing installations can be adopted with `--adopt-existing`; the final yes/no prompt states that adoption is included. Conflicting unrelated injectors still block that game. In the interactive menu, blocked games are clearly listed as excluded. One final yes/no confirmation applies only the ready games. Use `--help` for repair, uninstall, batch-record rollback and explicit noninteractive confirmation options.

Native game DLSS/Streamline files and launch options are not globally rewritten. The preview gives the required Proton DLL override; merge it with existing launch options manually. Native frame-generation evidence is required for either route, and detected anti-cheat blocks automatic selection.

## Storage and portability

This delivered configuration is pinned to Lauren's Btrfs Games drive and its UUID. Cache, backups and journals live in `/var/mnt/Games/Ada-Lab/RTXForge`, with a 100 GiB reserve. No fallback to the system drive is allowed. Another machine must explicitly configure `provider.json` (mount, UUID, root beneath that mount's `Ada-Lab`, and reserve) or pass `--provider` with an adapted file. The storage adapter is separate from the reusable installer core. Native Windows operation and Flatpak packaging are future work.

The original 1.6 implementation remains preserved in the prior project; `preserved-1.6.json` records its location and archive hash for the future native app. It is not the active installer.

The active build workflow is `.github/workflows/windows-build.yml`; the bounded source patch is `build/patch_panel.py`. A downloaded build artifact can be imported with `./rtxforge import-loader --loader /path/to/extracted/artifact`. This prepares future installations; existing games must be explicitly updated.

See [audit and verification](docs/AUDIT.md) and [source provenance](docs/PROVENANCE.md). Installer checks passed on disposable fixtures; in-game behavior has not been verified by this rewrite.

Activity indicators show scanning, payload preparation, per-game checks, backups/installation and recovery, with elapsed time and game counts. Plain terminals receive start/completion lines instead of animation. Noninteractive command-line confirmation flags remain available for scripts.
