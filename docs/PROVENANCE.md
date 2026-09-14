# Provenance

Current provider sources, exact release URLs, branch commits and archive hashes are recorded in `providers/lock.json` (checked 2026-09-14). y4my is pinned to v4 / 7b7220bbb499; DLSS-Unlocked to NR-v0.8.6 / 00fbc5873363. Neither is marked runtime-verified.

The transaction engine derives from the user-supplied RC1.38 archive. Original source/archive hashes and adaptation location are in `engine/SOURCE.json`. The AppImage packages this source and the desktop adapter; provider DLLs are downloaded and verified separately. Upstream license files are retained with provider payloads.

`provider.json` also retains legacy desktop compatibility and storage fields. Its historical runtime/NR fields do not select the 0.5.0 installation payload; `providers/lock.json` does. Historical custom runtime tags, logs and release documents remain historical evidence.
