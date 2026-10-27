// This phone's anonymous Rythu account (ADR 0004): a random number, nothing about the farmer. Created
// when they agree to keep a copy on the server (lib/profileSync.ts), or when they ask Ask Rythu a
// question (lib/ask.ts — the daily question limit is counted per phone). Their details still stay
// on the phone unless they agree to the server copy.
//
// The device secret lives in IndexedDB; it is traded for a one-hour token kept in memory only.
// If the server no longer knows this phone (data deleted), the stale credentials are dropped and —
// only when asked to — a fresh account is made.

import { createStore, del, get, set, type UseStore } from "idb-keyval";
import { ApiUnavailable, REQUEST_TIMEOUT_MS, apiFetch } from "./api";
import type { DeviceCredentials } from "./types";

const CREDENTIALS = "credentials";
const RENEW_BEFORE_MS = 60_000;

let store: UseStore | null = null;
let token: { value: string; expiresAt: number } | null = null;

function db(): UseStore {
  store ??= createStore("rythu-device", "device"); // not the forecast cache's database
  return store;
}

/** No account on this phone (and we were not asked to make one). */
export class NoDevice extends Error {
  constructor() {
    super("no device account");
    this.name = "NoDevice";
  }
}

async function loadCredentials(): Promise<DeviceCredentials | null> {
  const c = await get<DeviceCredentials>(CREDENTIALS, db()).catch(() => undefined);
  return c && typeof c.user_id === "string" && typeof c.device_secret === "string" ? c : null;
}

async function register(): Promise<DeviceCredentials> {
  const res = await apiFetch("/v1/devices", { method: "POST" });
  if (res.status !== 201) throw new ApiUnavailable(`register ${res.status}`);
  const creds = (await res.json()) as DeviceCredentials;
  await set(CREDENTIALS, creds, db());
  return creds;
}

export async function hasDevice(): Promise<boolean> {
  return (await loadCredentials()) !== null;
}

/** A valid bearer token, registering this phone first if `create` and it has no account. */
export async function getToken({ create }: { create: boolean }): Promise<string> {
  if (token && token.expiresAt - RENEW_BEFORE_MS > Date.now()) return token.value;
  for (let attempt = 0; attempt < 2; attempt++) {
    const creds = (await loadCredentials()) ?? (create ? await register() : null);
    if (!creds) throw new NoDevice();
    const res = await apiFetch("/v1/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(creds),
    });
    if (res.ok) {
      const body = (await res.json()) as { token: string; expires_at: string };
      token = { value: body.token, expiresAt: Date.parse(body.expires_at) };
      return token.value;
    }
    if (res.status !== 401) throw new ApiUnavailable(`session ${res.status}`);
    await forgetDevice(); // the server no longer knows this phone
  }
  throw new NoDevice();
}

/** fetch() with this phone's token; one transparent retry with a fresh token on a 401. */
export async function authedFetch(
  path: string,
  init: RequestInit,
  { create, timeoutMs = REQUEST_TIMEOUT_MS }: { create: boolean; timeoutMs?: number },
): Promise<Response> {
  for (let attempt = 0; ; attempt++) {
    const value = await getToken({ create });
    const res = await apiFetch(path, { ...init, headers: { ...init.headers, Authorization: `Bearer ${value}` } }, timeoutMs);
    if (res.status !== 401 || attempt > 0) return res;
    token = null;
  }
}

/** Drop this phone's credentials (after the server data is deleted, or found gone). */
export async function forgetDevice(): Promise<void> {
  token = null;
  await del(CREDENTIALS, db()).catch(() => undefined);
}
