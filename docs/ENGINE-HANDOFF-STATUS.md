# Proton runtime implementation

The temporary handoff has been translated into these durable requirements:

1. Keep native Streamline DLSS-G input/output, Ada MFG unlock and Blackwell kernels; exclude Enabler.
2. Advertise up to three generated frames (4X) at early capability query and preserve this ceiling in the native state path. Never overwrite the game's multiplier selection. Keep struct-version bounds.
3. Pin and ship the compiled fork DLL, not just the source patch.
4. Compose the separate DLSS-Unlocked NR layer without substituting its MFG defaults. Verify each member by SHA256.
5. Preserve clean/managed/external install state handling, rollback and derived-cache self-repair.
6. Keep Linux AppImage product scope. No Windows client or Windows-only NR gate.

Runtime acceptance remains distinct: cold-start a selected supported title under Proton, check native 2X/3X/4X settings and actual MFG output, confirm no Enabler and no regression, then assess NR. No unattended game fleet deployment is authorized by source work.

The next release addresses the remaining UI, per-game notes, diagnostics, reports and launch/test requests in rtxforgenotes.md.
