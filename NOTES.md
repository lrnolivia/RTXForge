# rtxForge Notes

**User-editable scratchpad / active inbox**

Put anything here that you want the rtxForge project manager or worker to notice.

No special formatting is required.

`WORKER_CONTEXT.md` is the canonical source of truth.

Workers must read this file at startup and process it before closeout.

Optional prefixes if useful:

```text
PRODUCTION:
NIGHTFALL:
SHARED:
UI:
GAME:
```

Lauren’s 2026-09-14 instruction selects two providers: y4my Multipass and DLSS-Unlocked. This supersedes the one-provider directive. Historical Nightfall material remains reference.

---

## Inbox

<!--
Add whatever you want below this line.

Examples:

- Avatar broke after X.
- I hate this button layout.
- Look at <link>.
- Maybe call the next release Calibrations.
- Test this on Gamescope.
-->



---

## Worker processing rule

```text
durable fact
-> verify if needed
-> fold into WORKER_CONTEXT.md
-> remove from Inbox once safely represented

real task / requirement
-> capture in the live task/priority system
-> remove once safely represented

resolved / obsolete
-> remove

ambiguous user note
-> leave it here
```

Do not silently delete an ambiguous note.

Keep this file small enough that the user can use it as an actual scratchpad.
