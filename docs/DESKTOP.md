# RTXForge Desktop — GNOME preview 0.2.0

Extract the full package, then double-click **RUN RTXFORGE GUI**. The terminal interface remains available as **RUN RTXFORGE**.

The GNOME app uses GTK 4 and libadwaita, follows the desktop's light/dark preference and accent, and runs its installer work away from the GTK main thread. All file operations remain sequential. The animation never starts a second installer.

## Using the app

1. Choose a Steam library or add an individual game folder.
2. Choose MFG Only or NR + MFG, and Install/update, Repair/verify, or Remove owned files.
3. Search and select games with checkboxes. Select visible affects only the currently filtered list.
4. Click Review. Payload preparation and file checks run with visible activity.
5. Review ready and excluded games, then click Apply reviewed changes. This is the only write confirmation.

The optional adoption switch is for recognized existing OptiScaler installations without an ownership record. Conflicts still protect unrelated loaders. The Recovery button lists recorded batches and cleanups; each restoration has its own review. Cleanup retains the explicit global NR/DLSS5 action, with all-candidate verified backups before removal.

The app shows the recovery record on completion. Activity details retain errors and recent progress. Closing is blocked during an operation so an installation cannot be silently abandoned. If an operation fails, inspect Recovery before retrying an interrupted batch.

## Requirements and current limits

- This first release targets **Bazzite GNOME desktop**. It uses the already-installed host Python 3, PyGObject, GTK 4 (4.10+) and libadwaita (1.4+), plus the existing 7-Zip dependency for payload preparation.
- Storage is still explicitly configured by `provider.json`, including the Games mount and UUID. No system packages or global graphics settings are changed by the GUI.
- The package includes the same verified custom panel DLL as the CLI package. Source checkouts use an imported loader or the optional packaged `bundled-loader` directory.
- This is a native GNOME application, not a Flatpak yet. SteamOS/KDE distribution requires packaging its GTK dependencies, or the later native KDE frontend. No SteamOS-wide compatibility claim is made for this preview.
- Native WinUI 3 and a Windows-compatible storage/launch adapter are not implemented yet.
- Launch overrides are not written automatically. Existing game setup requirements still apply. Installer success does not establish in-game graphics compatibility.

## Implementation sequence

1. **GNOME — implemented here:** real installer UI, live progress, selection/review/apply, repair/removal, rollback, cleanup and recovery.
2. **KDE Plasma / SteamOS — next:** native Qt 6/Kirigami frontend and Linux distribution packaging, preserving the same operation contracts.
3. **Windows — final:** modern WinUI 3 packaged binary, a narrow process interface to the engine, and a Windows storage adapter. Preserve the source/configuration behavior rather than cloning transaction logic into each UI.

`gui/rtxforge_gtk.py` owns GTK widgets. `scripts/desktop_service.py` owns toolkit-independent desktop operations. `scripts/planning.py` and `scripts/transactions.py` remain authoritative for file planning and mutation. Structured progress callbacks in `scripts/ui.py` let a desktop consume engine progress without scraping terminal output.

## Verification

- Native window smoke: library, selection, asynchronous progress delivery, review, back navigation, and disabled writes in preview mode.
- Rendered and inspected library and review screenshots on the Bazzite host.
- Sequential disposable-fixture check: read-only review, blocked exclusion, explicit apply, recovery, progress events and preserved save controls.
- No installed games modified or launched for this work. KDE, Flatpak and WinUI 3 have not been tested or delivered.

For a safe visual preview: `bash 'RTXForge GUI.sh' --demo`. Developer smoke: `bash 'RTXForge GUI.sh' --smoke-test` (creates screenshots under `dist`, uses demonstration rows, exits automatically).

Framework references: [libadwaita](https://gnome.pages.gitlab.gnome.org/libadwaita/doc/main/) and [PyGObject threading](https://gnome.pages.gitlab.gnome.org/pygobject/guide/threading.html).
