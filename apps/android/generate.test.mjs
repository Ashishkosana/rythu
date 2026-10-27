// Runs the real generator against the built site (apps/web/out) and checks what Android will see.
//   node --test
import assert from "node:assert/strict";
import { existsSync, mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { PLACEHOLDER_HOST, generate, manifestFor } from "./generate.mjs";

const committed = JSON.parse(readFileSync(new URL("twa-manifest.json", import.meta.url), "utf8"));

test("a release build refuses the placeholder host; versions come from CI", () => {
  assert.throws(() => manifestFor({ ...committed, host: PLACEHOLDER_HOST }, { release: true }), /real host/);
  const m = manifestFor(committed, { env: { RYTHU_VERSION_CODE: "42", RYTHU_VERSION_NAME: "1.0.42" } });
  assert.equal(m.appVersionCode, 42);
  assert.equal(m.appVersion, "1.0.42");
  assert.throws(() => manifestFor(committed, { env: { RYTHU_VERSION_CODE: "x" } }), /appVersionCode/);
});

test("the generated app opens the site full screen, with notifications and our icons", async () => {
  const dir = mkdtempSync(join(tmpdir(), "rythu-twa-"));
  const json = await generate(dir);
  const gradle = readFileSync(join(dir, "app/build.gradle"), "utf8");
  assert.match(gradle, new RegExp(`applicationId "${json.packageId.replaceAll(".", "\\.")}"`));
  assert.match(gradle, new RegExp(`hostName: '${json.host.replaceAll(".", "\\.")}'`));
  assert.match(gradle, /enableNotifications: true/);
  assert.match(gradle, /targetSdkVersion 36/); // Play's 2026 target-API floor
  assert.match(gradle, /minSdkVersion 24/); // androidbrowserhelper 2.7.4 needs ≥ 24; 21 fails the manifest merge
  const androidManifest = readFileSync(join(dir, "app/src/main/AndroidManifest.xml"), "utf8");
  assert.match(androidManifest, /android\.permission\.POST_NOTIFICATIONS/);
  for (const f of ["mipmap-xxxhdpi/ic_launcher.png", "mipmap-xxxhdpi/ic_maskable.png", "drawable-xxxhdpi/ic_notification_icon.png"]) {
    assert.ok(existsSync(join(dir, "app/src/main/res", f)), f);
  }
  const webManifest = JSON.parse(readFileSync(join(dir, "app/src/main/res/raw/web_app_manifest.json"), "utf8"));
  assert.equal(webManifest.short_name, "Rythu");
});
