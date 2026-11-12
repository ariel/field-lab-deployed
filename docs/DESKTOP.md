# Desktop apps

After activating and configuring Field Lab, install its four local Desktop apps:

```sh
bash deploy/bootstrap.sh desktop
```

Use `--home "/your/application/home"` consistently for a nondefault installation. `--desktop "/chosen/existing/folder"` installs the shortcuts elsewhere; the folder must exist and be outside the application home. This command builds the apps locally and installs shortcuts. It does not open OffShoot, start a transfer, run AI or touch CCC during installation.

Double-click an app in Finder:

| App | Action |
| --- | --- |
| **Field Lab Ingest** | Checks the configured destination is mounted, opens OffShoot and starts/resumes AI processing. Offers eligible mounted cards as OffShoot sources. Review the destination and preset in OffShoot before adding transfers. |
| **Field Lab Library** | Starts/resumes AI, waits for the local library endpoint and opens it in the default browser. |
| **Field Lab AI Progress** | Starts/resumes AI and opens the native progress window. |
| **Field Lab Stop AI** | Stops AI safely; pending work reconciles on the next start. It does not stop OffShoot or CCC. |

Keep Field Lab Ingest open to be offered newly mounted cards. The picker lists mount paths, supports multiple selections and excludes the configured destination. Select **Skip** to leave OffShoot unchanged. Cards successfully added by Field Lab stay out of the picker across launcher restarts while OffShoot is still running. Field Lab clears that history for cards it sees unmount and when OffShoot restarts. If you remove a card manually from Sources, you can add it again directly in OffShoot. Quit it from the Dock to stop watching. Setting sources may replace the current OffShoot source selection.

The apps use native AppleScript applets and native failure alerts. They do not open Terminal. Icons are obtained from the Mac's installed system resources; no OffShoot icon or proprietary application binary is redistributed. They are compiled and ad hoc signed on the recipient Mac, not shipped as notarized downloadable applications.

Each shortcut points to a managed app generation under `shared/runtime/desktop-apps`. The app calls the stable application `run` launcher, which resolves the currently active release. Updating Field Lab does not require changing the shortcut's executable paths. Running `desktop` again refreshes managed app generations and restores a missing shortcut. Older generations are retained; no application cleanup is performed automatically.

The installer refuses to replace an existing unrelated file, app or symlink with one of these names. It checks all four names before publishing. Rename the conflicting unrelated item yourself or choose another shortcut folder; do not delete user content to force installation. Ownership records are persisted before shortcuts are created so an interrupted installation can resume safely.

A missing drive or service startup error produces a native alert. Reconnect the configured destination and retry, or inspect AI Progress/status with Codex. Opening Ingest does not call Add Transfers, reset preferences, select a source card without confirmation or authorize card erasure. CCC remains a separately configured/validated task.

Development tests compile, sign, verify and decompile all four real app bundles in a temporary Desktop folder, including a home path with spaces, Unicode, quotes and shell characters. They also cover ownership conflicts, interruption/retry, release switching and dispatcher behavior with mocked apps. They never launch those applets or change the actual Desktop. The first-install acceptance still needs a real double-click test on the recipient Mac.
