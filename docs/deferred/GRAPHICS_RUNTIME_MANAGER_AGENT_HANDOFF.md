# Graphics Runtime Manager — Agent Architecture Handoff

## Mission

Evolve the current **NR + native NVIDIA MFG** application into a distributable, cross-platform graphics-runtime manager.

The project already has:

- a core install/uninstall engine
- a GNOME-native GUI
- OptiScaler package retrieval from a public upstream repository
- a current focus on DLSS Neural Rendering and native NVIDIA Multi Frame Generation
- an architecture intended to support KDE Plasma and Windows later

The long-term target is:

> One reusable core engine that can discover, download, verify, install, upgrade, back up, restore, and manage graphics runtimes on a per-game basis across Linux and Windows.

Do not turn the project into separate per-desktop implementations.

---

# 1. Core Architecture

Keep the runtime-management engine independent from every GUI.

```text
Core Engine
├── Game discovery
├── Runtime detection
├── Version resolution
├── Download providers
├── Hash/signature verification
├── Backup/restore
├── Transactional install/uninstall
├── Per-game compatibility profiles
├── Logging/diagnostics
├── Steam launch-option management
└── Rollback/recovery

Frontends
├── GNOME
├── KDE Plasma
├── Windows
└── COSMIC later if justified
```

All frontends should call the same engine/API/CLI surface.

Never duplicate install logic inside the GUI.

---

# 2. Linux Desktop Strategy

## First-class: GNOME

Continue treating GNOME as a native first-class frontend.

Preferred conventions:

- GTK
- libadwaita
- Wayland-first behavior
- XDG-compliant paths/config
- GNOME-native interaction patterns

## First-class: KDE Plasma

Build a native KDE frontend later.

Preferred conventions:

- Qt
- QML/Kirigami where appropriate
- Wayland-first behavior
- native Plasma interaction patterns

Do not make KDE merely a skin over the GNOME frontend.

## Windows

Build a native Windows frontend over the exact same engine.

Windows-specific differences belong in a platform adapter, not a second engine.

## Keep COSMIC on the roadmap

COSMIC is the main additional Linux DE worth considering as a first-class frontend later.

Do not prioritize it until demand justifies the maintenance cost.

## Do not build dedicated frontends for

- Cinnamon
- Xfce
- MATE
- Budgie
- Pantheon
- LXQt
- Deepin
- UKUI

The GTK or Qt frontend should cover these environments where practical.

## Do not build separate frontends for compositors/window managers

Examples:

- Hyprland
- Sway
- Niri
- River
- i3

Treat these as compatibility targets.

The Linux application must not assume GNOME Shell or KDE services exist.

---

# 3. Platform Adapter Model

Use adapters instead of scattering OS-specific branches throughout the codebase.

```text
PlatformAdapter
├── LinuxAdapter
│   ├── Steam discovery
│   ├── Proton-prefix discovery
│   ├── launch-option management
│   ├── Wine DLL overrides
│   ├── DXVK/vkd3d awareness
│   └── Bazzite/immutable-safe behavior
│
└── WindowsAdapter
    ├── Steam discovery
    ├── registry access
    ├── permissions/elevation
    ├── native DLL deployment
    ├── file-lock/process handling
    └── Windows path handling
```

The GUI should not know the low-level mechanics.

---

# 4. Product Direction

Do not stop at “OptiScaler installer.”

The target product identity is:

> **Cross-platform graphics-runtime manager**

Possible managed families:

- OptiScaler
- NVIDIA DLSS Super Resolution
- NVIDIA Ray Reconstruction
- NVIDIA DLSS-G / native Frame Generation
- NVIDIA DLSS Neural Rendering
- NVIDIA Streamline
- related NVIDIA runtime components
- game-specific compatibility layers
- per-game launch configuration

Current project priority remains:

> **DLSS Neural Rendering + native NVIDIA MFG on Bazzite/Proton**

---

# 5. Provider Architecture

Introduce source/download providers.

```text
Providers
├── OptiScalerProvider
├── NvidiaStreamlineProvider
├── NvidiaDlssSrProvider
├── NvidiaDlssRrProvider
├── NvidiaDlssGProvider
├── NvidiaDlssNrProvider
└── CommunityFallbackProvider
```

Providers should return structured metadata to the core rather than directly modifying games.

Example:

```json
{
  "component": "streamline",
  "version": "2.x",
  "source": "nvidia",
  "source_type": "official",
  "download_url": "...",
  "archive_sha256": "...",
  "files": [
    {
      "name": "sl.interposer.dll",
      "sha256": "..."
    }
  ]
}
```

---

# 6. Official-Upstream-First Policy

Do not treat “available on GitHub” as equivalent to “safe to redistribute.”

Preferred source order:

1. official NVIDIA source
2. official NVIDIA GitHub release
3. official NVIDIA SDK/package endpoint
4. intended project-owned upstream
5. community mirror only as an explicit fallback

The default path for proprietary NVIDIA binaries should be:

> **download directly from NVIDIA or another official upstream at runtime**

rather than bundling/rehosting those binaries in this project's own release packages.

---

# 7. Do Not Become a DLL Host Unnecessarily

Preferred deployment flow:

```text
User selects component/version
        ↓
Provider resolves official upstream
        ↓
App downloads package
        ↓
App verifies hashes/signatures
        ↓
App stages required files
        ↓
App fingerprints game originals
        ↓
App creates backup/transaction
        ↓
App deploys
        ↓
App validates
```

The project should primarily distribute:

- metadata
- source definitions
- compatibility rules
- hashes
- version mappings
- install logic
- rollback manifests

Avoid rehosting proprietary binary payloads unless redistribution rights are clearly established.

---

# 8. Metadata-Driven Runtime Catalog

Maintain a machine-readable runtime catalog.

Example:

```json
{
  "streamline": {
    "2.x": {
      "source": "nvidia",
      "release": "v2.x",
      "archive_sha256": "...",
      "files": {
        "sl.interposer.dll": "...",
        "sl.common.dll": "...",
        "sl.dlss.dll": "...",
        "sl.dlss_g.dll": "..."
      }
    }
  }
}
```

Prefer keeping this catalog independently updateable from the full application when practical.

Benefits:

- reproducible installs
- integrity checking
- provenance
- smaller app releases
- easy version discovery
- easier rollback
- no unnecessary proprietary hosting

---

# 9. NVIDIA Streamline Provider

Treat Streamline as a first-class managed provider.

The provider should:

1. query NVIDIA's official release source
2. discover versions
3. download an official package
4. fingerprint included binaries
5. expose available components to the engine
6. allow exact-version selection
7. preserve game originals
8. support full rollback

Do not assume every game should use the newest Streamline.

Use per-game compatibility policy.

---

# 10. Model DLSS as Separate Components

Do not represent “DLSS” as one single runtime.

```text
NVIDIA DLSS
├── Super Resolution
├── Ray Reconstruction
├── DLSS-G / Frame Generation
├── Neural Rendering
└── Streamline integration
```

Each component needs its own:

- version
- source
- hash
- installed path
- original game version
- compatibility rules
- rollback state

---

# 11. OptiScaler Provider

Keep OptiScaler independent from NVIDIA providers.

The provider should support:

- release discovery
- stable/pre-release/nightly distinction
- exact commit/tag identity
- archive hashes where possible
- fork identity
- pinning
- rollback

Do not silently switch a user's installation between OptiScaler forks.

---

# 12. Source Trust Levels

Expose provenance.

Example:

```text
Official
✓ NVIDIA upstream
✓ Hash/signature verified

Project upstream
✓ Intended OptiScaler release source
✓ Hash verified

Community
⚠ Third-party source
⚠ Never selected automatically
```

Never silently downgrade from an official source to a community mirror.

---

# 13. Integrity Verification

Every provider should support as much of the following as applies:

- SHA-256
- archive hashes
- expected file manifests
- PE/file-version inspection
- Authenticode validation for signed Windows binaries
- source/release identity

Store at minimum:

```text
component
version
provider
source URL
archive hash
file hashes
file versions
target game
install timestamp
transaction ID
```

---

# 14. Transactional Install Engine

Every runtime change should be transactional.

```text
Discover
↓
Preflight
↓
Fingerprint current game files
↓
Backup
↓
Download
↓
Verify
↓
Stage
↓
Deploy
↓
Validate
↓
Commit
```

If any step fails:

```text
Rollback
```

Never leave a game with a half-installed runtime stack.

---

# 15. Backup / Restore Model

Backups should be deterministic and per-game.

Record:

- original filename
- original path
- original hash
- original version
- replacement hash/version
- provider/source
- transaction ID

Support:

- restore original game files
- restore previous managed version
- uninstall current managed stack
- verify current state

---

# 16. Per-Game Compatibility Intelligence

This should become a defining feature.

Example profile:

```json
{
  "game": "Cyberpunk 2077",
  "preferred": {
    "dlss_sr": "310.x",
    "ray_reconstruction": "310.x",
    "dlss_g": "310.x",
    "streamline": "2.x",
    "neural_rendering": "310.x"
  },
  "rules": {
    "replace_streamline": true,
    "proxy": "dxgi.dll",
    "proton_dll_override": "dxgi=n,b"
  }
}
```

Do not globally force one DLL arrangement across the entire library.

---

# 17. UI Direction

Present the application as a per-game runtime manager.

Example:

```text
Cyberpunk 2077

DLSS SR              310.x   ✓ Current
Ray Reconstruction   310.x   ✓ Current
DLSS-G               310.x   ✓ Current
Streamline            2.x    ✓ Current
Neural Rendering     310.x   ✓ Installed

[ Upgrade ]
[ Change Version ]
[ Verify ]
[ Restore Game Defaults ]
```

Hide raw DLL complexity from the default UI.

---

# 18. Advanced View

Advanced users should be able to inspect:

- exact file paths
- installed DLL versions
- hashes
- provider/source
- active OptiScaler proxy
- OptiScaler fork/version
- Proton launch options
- Wine DLL overrides
- Streamline replacement state
- backup/transaction state

---

# 19. Linux / Proton Requirements

The engine should understand:

- Steam library locations
- Proton prefixes
- Proton Experimental
- custom Proton versions
- Steam launch options
- Wine DLL overrides
- DXVK
- vkd3d-proton
- Wayland
- immutable Linux distributions

Prefer:

1. game-local changes
2. user-space config
3. Steam launch options
4. prefix-local changes

Avoid system-wide intervention unless genuinely required.

---

# 20. Bazzite Policy

Treat Bazzite as a primary Linux target.

Prefer:

- game-local deployment
- user-space configuration
- per-game Wine overrides
- Steam launch options
- reversible operations

Avoid:

- unnecessary root usage
- modifying the immutable base image
- distro-wide DLL hacks

---

# 21. Windows Policy

Use the same transaction engine on Windows.

Platform-specific code may handle:

- registry access
- native Steam paths
- elevation
- file locks
- running-game detection
- Windows path semantics

Do not fork the runtime-management architecture.

---

# 22. Licensing / Redistribution Guardrail

Critical rule:

> **Publicly downloadable does not automatically mean legally safe to rehost.**

Before bundling or mirroring proprietary NVIDIA binaries:

1. inspect the applicable license
2. confirm redistribution rights
3. confirm whether this tool's specific use case is covered
4. document any obligations
5. obtain clarification from NVIDIA when needed

Until confirmed:

- prefer official runtime downloads
- do not bundle NVIDIA DLLs by default
- do not mirror them on project infrastructure unnecessarily

---

# 23. Licensing Question to Resolve Before Broad Distribution

This application installs runtime components into third-party games.

That is not necessarily identical to a game developer shipping an NVIDIA SDK component inside their own application.

Before a commercial or broad public release, confirm that the applicable NVIDIA licenses permit this deployment model.

Do not assume ordinary SDK redistribution language automatically covers it.

---

# 24. Community Mirrors

Community providers may exist later only as optional fallbacks.

Rules:

- never use automatically while an official source works
- visibly identify third-party provenance
- verify against known-good hashes where possible
- require explicit user opt-in

---

# 25. Version Resolution

Providers should support:

- latest stable
- latest pre-release
- exact version
- pinned version
- known-good per-game version

Newest must not automatically mean recommended.

---

# 26. Update Engine

The app should eventually distinguish:

```text
Installed
Available
Recommended
```

Example:

```text
DLSS SR
Installed:   310.8
Available:   310.9
Recommended: 310.8
```

A compatibility-aware recommendation is more useful than “update everything.”

---

# 27. Safe Defaults

Default behavior should favor:

- official sources
- known-good versions
- per-game recommendations
- automatic backup
- one-click rollback
- minimal manual work
- native NVIDIA implementations for the current project scope

Experimental versions should be opt-in.

---

# 28. Product Differentiation

Do not position this merely as:

> a DLSS DLL updater

Position it as:

> **A cross-platform graphics-runtime manager for Windows and Linux/Proton.**

Key differentiators:

- per-game compatibility intelligence
- provenance
- integrity verification
- transactional deployment
- rollback
- native Linux/Windows support
- OptiScaler management
- Streamline management
- individual DLSS-component management
- NR + native NVIDIA MFG management
- Proton-specific automation
- native desktop frontends

---

# 29. Development Order

## Phase 1 — Stabilize current scope

- core install/uninstall engine
- GNOME frontend
- OptiScaler provider
- DLSS NR
- native NVIDIA MFG
- Bazzite/Proton reliability
- backup/restore

## Phase 2 — Formalize provider abstraction

- source metadata
- version resolver
- hashes
- download staging
- transaction integration

## Phase 3 — Add NVIDIA Streamline provider

## Phase 4 — Add individual NVIDIA DLSS providers

## Phase 5 — Add per-game compatibility profiles/recommendations

## Phase 6 — Build KDE Plasma frontend

## Phase 7 — Build Windows frontend

## Phase 8 — Evaluate COSMIC frontend based on demand

---

# 30. Non-Goals

Do not:

- build a dedicated app for every Linux DE
- duplicate core logic across GUIs
- globally upgrade every game to the newest DLL
- depend on random binary mirrors
- rehost proprietary NVIDIA binaries without clear rights
- model DLSS/Streamline/NR/MFG as one undifferentiated blob
- modify Bazzite's immutable base unnecessarily
- perform installs without rollback metadata

---

# 31. Implementation Hierarchy

Preserve this order:

```text
Core engine
↓
Provider abstraction
↓
Per-game policy
↓
Platform adapters
↓
Native frontends
```

Never reverse this hierarchy.

---

# 32. Product Vision

For every supported game, the application should be able to answer:

```text
What graphics runtimes are installed?
Which versions are installed?
Where did they come from?
Are they official?
Are their hashes valid?
Are they known-good for this game?
Is a newer version available?
Is the newer version actually recommended?
What files will change?
Can the change be undone instantly?
```

The application should own that complexity.

The user should not need to manually manage DLLs.

---

# Final Directive

Continue building this project as:

> **one cross-platform graphics-runtime-management engine with native frontends, official-upstream-first package retrieval, integrity verification, transactional deployment, per-game compatibility intelligence, and complete rollback.**

Current priority:

> **DLSS Neural Rendering + native NVIDIA MFG on Bazzite/Proton.**

Future expansion:

> **NVIDIA Streamline and other DLSS runtime upgrades through official provider-backed downloads rather than unnecessary project-hosted proprietary binaries.**
