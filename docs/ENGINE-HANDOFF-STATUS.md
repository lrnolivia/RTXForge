# Engine integration — 0.5.0

Current implementation: `engine/rtxengine.py`, derived from the supplied Handoff 188 RC1.38 archive; original hashes in `engine/SOURCE.json`. Original extracted source remains locally under ignored `engine/imported-rc1.38/`.

Both desktop and terminal frontends select complete providers from `providers/lock.json`. The latest user instruction supersedes historical single-provider guidance. The old custom runtime is preserved as history, not shipped.

Corrected startup route: FrameGen Enabled=false, FGInput=nofg, FGOutput=nofg. Upstream initializes a selected DLSSG output independently of Enabled, so RC1.38 was not truly dormant. Ada unlock and NR startup activation are separately explicit.

New payloads refuse root native DLSS/Streamline replacements. Restore refuses removing a native root NVIDIA/Streamline DLL if no original backup was recorded. Launch-option restoration remains scoped to recorded engine changes.

The user reported all games lost native 2× after a previous uninstall. Available receipts did not establish the cause; Cyberpunk's native DLLs were present during read-only inspection. No games have been repaired, redeployed or launched by this development task. Validate launch/native 2×, then NR and native MFG with user testing. Do not label source-level or fixture checks as game verification.
