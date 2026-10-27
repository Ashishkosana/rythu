# Rythu for Android (Trusted Web Activity)

The Play Store app is a thin Android shell around the website ([ADR 0005](../../docs/architecture/adr/0005-android-trusted-web-activity.md)):
it opens the site full screen in Chrome, and web push alerts arrive as the app's own notifications.
Web changes reach phones without a Play release; only changes to the shell (name, icons, colours,
package) need a new upload.

| File | What it is |
|---|---|
| `twa-manifest.json` | The one source for the app: package id, host, colours, icons, signing-key fingerprints (Bubblewrap's format) |
| `generate.mjs` | Generates the Gradle project into `build/project/` with `@bubblewrap/core` — offline, icons and web manifest read from `../web/out` |
| `generate.test.mjs` | Runs the real generator and checks host, notifications, icons, target SDK |
| `../../.github/workflows/android.yml` | Builds every change (unsigned check); run by hand for a signed release `.aab` |

The site publishes the matching Digital Asset Links file (`/.well-known/assetlinks.json`) from the same
`twa-manifest.json` — see `apps/web/scripts/build-lib.mjs` `assetLinks()`.

```bash
cd apps/web && npm run build          # the generator reads icons + manifest from out/
cd ../android && npm ci && npm test   # generator checks
node generate.mjs                     # → build/project (needs JDK 17 + Android SDK to build)
cd build/project && ./gradlew bundleRelease
```

The Android SDK is not reachable from the cloud dev container (dl.google.com is blocked), so Gradle
runs only in GitHub Actions — `ubuntu-latest` ships the SDK.

`npm audit` reports advisories in `@bubblewrap/core`'s dependencies (extract-zip, googleapis,
node-forge, jimp/file-type; 1.27.0 is the latest, no fix yet). None is reached: the generator only
decodes our own committed PNGs — it never unzips (that is Bubblewrap's JDK/SDK installer), talks to Play
(googleapis) or verifies signatures (node-forge). It is a build-time tool on trusted input and nothing
from it ships in the app. Re-check when Bubblewrap releases.

## Play runbook (your steps)

Facts checked 2026-10-27: new personal developer accounts must run a **closed test with ≥ 12 testers
opted in for 14 days** before production ([Play Console Help](https://support.google.com/googleplay/android-developer/answer/14151465));
new apps must **target API 36** from 31 Aug 2026 ([Android docs](https://developer.android.com/google/play/requirements/target-sdk)) — the
generated project does.

1. **Decide the package id — it is permanent on Play.** `twa-manifest.json` has
   `io.github.ashishkosana.rythu` (unique without owning a domain). Change it now or never.
2. **Deploy the site** (`infra/azure/README.md`) and note its host, e.g. `nice-sea-0a1b2c3d4.azurestaticapps.net`.
   A custom domain is optional; the app is tied to whatever host you put here, and changing it later
   means a new upload.
3. **Set the host**: replace `replace-me.azurestaticapps.net` everywhere in `twa-manifest.json`
   (`host` and the four URLs). Commit. A release build refuses the placeholder.
4. **Create the upload key** on your own computer and keep it safe (with Play App Signing, Google holds
   the real signing key; a lost upload key can be reset through Play support):
   ```bash
   keytool -genkeypair -v -keystore upload.keystore -alias upload -keyalg RSA -keysize 2048 -validity 10000
   base64 -w0 upload.keystore     # macOS: base64 -i upload.keystore
   ```
   Add three repository secrets (GitHub → Settings → Secrets and variables → Actions):
   `ANDROID_UPLOAD_KEYSTORE_B64` (the base64 text), `ANDROID_UPLOAD_KEYSTORE_PASSWORD`, `ANDROID_UPLOAD_KEY_PASSWORD`.
   The alias must be `upload`.
5. **Build a release**: GitHub → Actions → *android* → *Run workflow* (on `main`). Download the
   `rythu-<n>-aab` artifact. The version code is the run number, so each release is higher than the last.
6. **Play Console** ($25 once): create the app — name *Rythu*, default language Telugu (te-IN), app,
   free. Then *App content*:
   - Privacy policy: `https://<host>/privacy/`
   - Ads: no. App access: everything works without an account.
   - Target audience: 18+. Content rating: complete the questionnaire (no objectionable content).
   - Government information: Rythu shows public scheme information but is **not** a government app —
     say so in the store description and link the official sources (the Schemes screen does).
   - Data safety — a starting point drawn from `/privacy/`; check it against the code before you submit:
     - *Location → Approximate location*: collected (weather for the chosen place; a GPS fix is
       rounded to ~1 km on the phone), not shared, required for the core feature.
     - *Device or other IDs*: the random account id — only if the farmer turns on the server copy;
       optional; app functionality.
     - *App activity → Other user-generated content*: field names (server copy; optional) and Ask Rythu
       questions (sent to the server and Anthropic to answer, not stored by Rythu; Anthropic deletes
       within 30 days; optional).
     - Voice: a spoken question is turned into text by Chrome / Google's speech service, not by Rythu —
       Rythu receives text only.
     - Encrypted in transit: yes. Deletion: yes, in the app (*My data → Delete my data from Rythu's server*).
     - Not shared: Azure, Google push and Open-Meteo act as service providers.
7. **Internal testing** (no review wait): *Test and release → Internal testing* → create a release,
   upload the `.aab` (Play App Signing is on by default) → add your father's Gmail as a tester → send
   him the opt-in link. He installs from the Play Store.
8. **Link the app to the site** (removes the browser bar): *Test and release → App integrity → App signing*
   → copy the **App signing key certificate SHA-256**. Add it to `fingerprints` in `twa-manifest.json`:
   ```json
   "fingerprints": [{ "name": "play-app-signing", "value": "AB:CD:…" }]
   ```
   Commit and let the web deploy run (its smoke test then checks `/.well-known/assetlinks.json`). Check
   Google sees it:
   `https://digitalassetlinks.googleapis.com/v1/statements:list?source.web.site=https://<host>&relation=delegate_permission/common.handle_all_urls`
   Until this is done the app still works, with a URL bar on top.
9. **On the phone**: open Rythu → no URL bar → *My data* → turn on the server copy and alerts → allow
   notifications. A rain alert should arrive with the sprout icon.
10. **Closed test → production**: create a closed testing track, upload the same bundle, invite ≥ 12
    testers (aim for ~15 — guides report the 14 days restart if opted-in testers drop below 12), wait 14 days, then
    apply for production access in Play Console.

Updating the shell later (icons, colours, name): edit `twa-manifest.json` or the web manifest, run the
*android* workflow, upload the new `.aab`. Web-only changes need none of this.
