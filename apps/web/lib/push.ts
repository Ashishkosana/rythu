// Rain / field-task alerts on this phone (S14). Needs the server copy to be on (the server must know
// the village and crop to decide what to send), the phone's permission, and a push subscription that
// the server keeps. Turning the server copy off, or deleting the data, turns alerts off too.

import { ApiUnavailable, getJson } from "./api";
import { authedFetch } from "./device";
import { syncConsent } from "./prefs";

const ALERTS_KEY = "rythu.alerts";

export type AlertsResult = "on" | "off" | "needs_consent" | "blocked" | "unsupported" | "failed";

export function pushSupported(): boolean {
  return (
    typeof window !== "undefined" &&
    "serviceWorker" in navigator &&
    "PushManager" in window &&
    "Notification" in window
  );
}

/** base64url → bytes (what PushManager.subscribe wants for applicationServerKey). Pure. */
export function urlBase64ToBytes(b64url: string): Uint8Array<ArrayBuffer> {
  const b64 = (b64url + "=".repeat((4 - (b64url.length % 4)) % 4)).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(b64);
  const out = new Uint8Array(new ArrayBuffer(raw.length));
  for (let i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
  return out;
}

function remember(on: boolean): void {
  try {
    if (on) window.localStorage.setItem(ALERTS_KEY, "on");
    else window.localStorage.removeItem(ALERTS_KEY);
  } catch {
    /* non-fatal */
  }
}

/** What the switch should show: on only if we turned it on AND the phone still allows it. */
export function alertsState(): AlertsResult {
  if (!pushSupported()) return "unsupported";
  if (Notification.permission === "denied") return "blocked";
  try {
    return window.localStorage.getItem(ALERTS_KEY) === "on" && Notification.permission === "granted" ? "on" : "off";
  } catch {
    return "off";
  }
}

export async function enableAlerts(): Promise<AlertsResult> {
  if (!pushSupported()) return "unsupported";
  if (!syncConsent()) return "needs_consent";
  const permission = await Notification.requestPermission();
  if (permission !== "granted") return permission === "denied" ? "blocked" : "off";
  try {
    const { res, body } = await getJson("/v1/push/key");
    const key = (body as { public_key?: string } | null)?.public_key;
    if (!res.ok || !key) throw new ApiUnavailable(`push key ${res.status}`);
    const reg = await navigator.serviceWorker.ready;
    const sub =
      (await reg.pushManager.getSubscription()) ??
      (await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: urlBase64ToBytes(key) }));
    const json = sub.toJSON();
    const put = await authedFetch(
      "/v1/me/push-subscriptions",
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ endpoint: json.endpoint, keys: { p256dh: json.keys?.p256dh, auth: json.keys?.auth } }),
      },
      { create: true },
    );
    if (put.status !== 204) throw new ApiUnavailable(`subscribe ${put.status}`);
    remember(true);
    return "on";
  } catch (err) {
    console.error("alerts: could not subscribe", err);
    return "failed";
  }
}

/** Stop alerts on this phone: tell the server (best effort), then drop the subscription locally. */
export async function disableAlerts({ tellServer = true }: { tellServer?: boolean } = {}): Promise<AlertsResult> {
  remember(false);
  if (!pushSupported()) return "off";
  try {
    const reg = await navigator.serviceWorker.ready;
    const sub = await reg.pushManager.getSubscription();
    if (!sub) return "off";
    if (tellServer) {
      const q = new URLSearchParams({ endpoint: sub.endpoint });
      await authedFetch(`/v1/me/push-subscriptions?${q.toString()}`, { method: "DELETE" }, { create: false }).catch(
        () => undefined, // offline: unsubscribing below already stops delivery to this phone
      );
    }
    await sub.unsubscribe();
  } catch {
    /* already gone */
  }
  return "off";
}
