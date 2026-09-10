# RTXForge 0.4.0 — Bazzite desktop app

This build targets Bazzite 44 GNOME x86_64 and uses its installed Python, GTK4/libadwaita, NVIDIA tools and 7-Zip. It is not a universal Linux binary. The AppImage format follows the official type-2 runtime design: https://docs.appimage.org/reference/architecture.html

Open RTXForge from the app menu after installation. To install a downloaded build, open the executable AppImage, then choose Settings → Install / update this build. Alternatively run the AppImage with `--install`.

The app is copied to `$XDG_DATA_HOME/rtxforge/application/RTXForge.AppImage` (normally `~/.local/share/rtxforge/application/`). This survives Bazzite system updates and deleting the downloaded file. Each replacement retains `RTXForge.previous.AppImage`. The app menu always points to the current copy. No GitHub publishing or background update service is required yet.

Application updates do not deploy graphics files into games. Game installs, repairs and uninstall actions remain explicit. Engine payloads, artwork, settings and transaction backups stay at the existing configured storage location on Games. The current provider configuration remains specific to this machine's pinned Games drive.

This build adds main-library view buttons, padded icon controls, responsive artwork sizing, and artwork-led details panels with direct per-game actions. It retains the 0.3.1 MFG/NR engine. Full DLSS-Unlocked NR migration is still pending.

Build: `python3 packaging/build_appimage.py`. The upstream AppImage runtime is pinned by release URL and SHA256 in `packaging/runtime.json`.
