# DLSS-Unlocked NR layer

The NR source is the pinned DLSS-Unlocked v0.3.0 standalone release. Its upstream instructions describe the root forwarder and patched model beside the game executable, with the private NR runtime/plugin below OptiScaler/streamline. See https://github.com/ShyVortex/dlss-unlocked/tree/v0.3.0 .

RTXForge now takes all four NR-specific binaries from that archive, each with a pinned SHA256. The patched root model and the stock private model are intentionally distinct. The y4my MFG core, native Streamline MFG plugins, SR/RR/G runtimes and game-native files do not come from the standalone MFG defaults. No Enabler, nvngx.ini, or FSR3 bridge is selected.

The forwarder exports the symbols consumed by y4my's NR backend. Export-name matching is static evidence, not ABI or runtime proof. The native MFG menu changes are a separate fork delta. NR startup activation is explicit, direct-driver proxy mode is disabled, and the root proxy Wine override remains part of the install review. RTXForge does not silently rewrite launch options.

Unresolved acceptance: cold-start a supported title under Proton Experimental; confirm NR initialization and output while native Streamline MFG remains active and performance is unchanged. Do not infer visual success from file hashes. No Windows-only runtime gate is implemented.
