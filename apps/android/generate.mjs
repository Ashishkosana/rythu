// Generate the Android app (a Trusted Web Activity) from twa-manifest.json into build/project/, then
// build it with Gradle. No network: icons and the web manifest are read from the built site
// (apps/web/out — run `npm run build` there first), never downloaded from the live host.
//   node generate.mjs              check build: any host, placeholder allowed
//   node generate.mjs --release    refuses the placeholder host; version from RYTHU_VERSION_CODE/NAME

import { mkdirSync, readFileSync, rmSync } from "node:fs";
import { extname } from "node:path";
import { fileURLToPath } from "node:url";
import bubblewrap from "@bubblewrap/core";

const { ConsoleLog, TwaGenerator, TwaManifest, fetchUtils } = bubblewrap;

export const PLACEHOLDER_HOST = "replace-me.azurestaticapps.net";
const SITE = new URL("../web/out/", import.meta.url);
const TYPES = { ".png": "image/png", ".webmanifest": "application/manifest+json", ".json": "application/json" };

/** The TWA manifest JSON for this build: the committed file, with release checks and version overrides. */
export function manifestFor(json, { release = false, env = {} } = {}) {
  if (release && json.host === PLACEHOLDER_HOST) {
    throw new Error("twa-manifest.json: set `host` (and the URLs that use it) to the site's real host first");
  }
  const out = { ...json };
  if (env.RYTHU_VERSION_CODE) out.appVersionCode = Number(env.RYTHU_VERSION_CODE);
  if (env.RYTHU_VERSION_NAME) out.appVersion = env.RYTHU_VERSION_NAME;
  if (!Number.isInteger(out.appVersionCode) || out.appVersionCode < 1) {
    throw new Error(`bad appVersionCode ${JSON.stringify(out.appVersionCode)}`);
  }
  return out;
}

/** Serve the TWA host's URLs from the built site; refuse everything else. */
function localFetch(host) {
  return async (input) => {
    const url = new URL(String(input));
    if (url.host !== host.toLowerCase()) throw new Error(`generate: refusing to fetch ${url} — only the built site is read`);
    try {
      const body = readFileSync(new URL("." + url.pathname, SITE));
      const type = TYPES[extname(url.pathname)] ?? "application/octet-stream";
      return new Response(body, { status: 200, headers: { "content-type": type } });
    } catch {
      return new Response("not in apps/web/out", { status: 404 });
    }
  };
}

export async function generate(target, options = {}) {
  const json = manifestFor(JSON.parse(readFileSync(new URL("twa-manifest.json", import.meta.url), "utf8")), options);
  fetchUtils.fetch = localFetch(json.host);
  rmSync(target, { recursive: true, force: true });
  mkdirSync(target, { recursive: true });
  await new TwaGenerator().createTwaProject(target, new TwaManifest(json), new ConsoleLog("generate"));
  return json;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const release = process.argv.includes("--release");
  const target = fileURLToPath(new URL("build/project/", import.meta.url));
  const json = await generate(target, { release, env: process.env });
  console.log(`generate: ${json.packageId} ${json.appVersion} (${json.appVersionCode}) for https://${json.host} → ${target}`);
}
