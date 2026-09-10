# Active direction — 2026-09-10

RTXForge is a Linux/Bazzite/Proton application, distributed as an AppImage.
The active requirements are in rtxforgenotes.md. The prior Windows client and OS-gated NR proposals are retired.

The MFG runtime fork is lrnolivia/RTXForge-MFG, based on y4my commit 7b7220bbb4994a9c8ae60cfc75a44cb67995efb8. Use native Streamline DLSS-G input, real NVIDIA DLSS-G output, Ada unlock and Blackwell kernels. Native game multiplier selections pass through. Initial capability exposure is capped at 4X. Enabler is not a dependency or fallback.

NR is a separately pinned DLSS-Unlocked Proton layer. Preserve MFG when changing NR. Binary deployment and static checks do not prove runtime success. Native game menu and NR acceptance require a controlled cold-start game check.

Preserve the adoption lifecycle and verified derived-cache rebuilding. Publish the handoff build first, then the Forge notes UI/reporting work. Do not ship temporary handoffs.
