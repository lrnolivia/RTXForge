# Source provenance

RTXForge builds from the user-supplied `OptiScaler-NR-MFG-BAZZITE-v3.0-STABLE-HEADLESS-PROTON-DOUBLE-CLICK.zip`.

SHA-256: `3767da35b0756638c1741b181deaa9a0668c1962bc828e346dbb364a4a15cd00`.

Read-only library discovery and the desktop launcher derive from that supplied release. Transaction helpers derive from the preserved local 1.6 work. New orchestration, profiles, payload handling and cleanup are maintained here. No new blanket license is asserted over third-party code.

Upstream binaries retain their own licenses and notices:

- [y4my OptiScaler fork](https://github.com/y4my4my4m/OptiScaler_DLSSNR_Multipass_MFG), pinned to commit `7b7220bbb4994a9c8ae60cfc75a44cb67995efb8` and release `v10.0.0-dev-fork-y4my4my4m-v4`.
- [dlss-unlocked](https://github.com/ShyVortex/dlss-unlocked/releases/tag/v0.3.0), version 0.3.0, supplies the separately pinned NR forwarder, patched root model, private NR runtime and NR Streamline plugin. Enabler components are excluded.

`provider.json` contains the exact archive hashes, y4my core identity, native Streamline/DLSS-G route policy and NR member SHA256 identities. DLL payloads are downloaded from upstream rather than included in the RTXForge source archive. This project is not an NVIDIA product or endorsement.
