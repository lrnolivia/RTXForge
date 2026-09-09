# RTXForge 0.3.0 — GNOME library

Extract the ZIP and double-click **RUN RTXFORGE GUI**. The CLI is still available.

- Unified Steam and added-folder library; tall posters by default.
- Keyless SteamGridDB artwork, Steam metadata and artwork fallback, local caching, creator attribution in game details. No account, API key or credential is required.
- Solid neutral colors. Settings switch between posters, wide capsules and list, and change artwork size, dark preference, default profile, cache lifetime, request timeout, metadata and recognition of previous installs.
- Profile buttons replace dropdowns. Selected actions use floating review panels.
- **Install entire library** and **Uninstall entire library** are immediate one-click operations: they prepare and apply wherever possible, reporting skipped games. They cover all libraries regardless of search or filter. Backups and drift checks remain enabled. Uninstall removes identified OptiScaler components, not the games or saves.
- **Select all** selects every game, including games hidden by a filter. Ineligible installs are skipped during checks.
- Settings includes Undo previous changes and the retained global NR cleanup.
- Hardware detection checks x86-64 Linux, an accessible NVIDIA driver, a GeForce RTX 40/50-series GPU and 7-Zip. Install/repair is unavailable if those prerequisites cannot be verified; uninstall remains available. Hardware success is not runtime proof for any particular game.
- The custom repository controls in Settings are disabled UI placeholders only. No custom-repository interpretation or switching is implemented.

GTK 4.10+, libadwaita 1.5+ and PyGObject are required. This is the GNOME build; KDE-native, Flatpak distribution and WinUI 3 remain later stages. State/cache/backups continue using the configured Games-drive storage in provider.json.

SteamGridDB artwork uses its website's anonymous public search endpoints, verified live without authentication. Those website interfaces can change; failures fall back to Steam or a placeholder and never block installation. Network requests are bounded; metadata never drives installation or executable selection. Covers are fetched at runtime, not redistributed in this ZIP.

The verified custom loader still hides the NR panel in MFG Only. NR + MFG starts NR enabled and retains the panel.

Verification was limited to syntax, GUI rendering/navigation and existing desktop fixture checks. Six actual title posters were retrieved from SteamGridDB with no credentials. No installed games were modified. Extended testing was deliberately deferred at the user's request.

The graphics-runtime-manager handoff is archived under docs/deferred and explicitly **not active work**.
