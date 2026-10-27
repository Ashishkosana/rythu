import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const idb = new Map<string, unknown>();
vi.mock("idb-keyval", () => ({
  createStore: () => "store",
  get: async (k: string) => idb.get(k),
  set: async (k: string, v: unknown) => void idb.set(k, v),
  del: async (k: string) => void idb.delete(k),
}));

/** A browser with push: Notification permission, a service worker registration with a PushManager. */
function fakeBrowser(permission: NotificationPermission, answer: NotificationPermission = permission) {
  const data = new Map<string, string>();
  const unsubscribe = vi.fn(async () => true);
  let current: { endpoint: string; toJSON: () => unknown; unsubscribe: typeof unsubscribe } | null = null;
  const subscribe = vi.fn(async (opts: { applicationServerKey: Uint8Array }) => {
    current = {
      endpoint: "https://fcm.googleapis.com/fcm/send/phone",
      toJSON: () => ({ endpoint: "https://fcm.googleapis.com/fcm/send/phone", expirationTime: null, keys: { p256dh: "P".repeat(87), auth: "A".repeat(22) } }),
      unsubscribe,
    };
    void opts;
    return current;
  });
  const notification = Object.assign(function Notification() {}, {
    permission,
    requestPermission: vi.fn(async () => answer),
  });
  vi.stubGlobal("window", {
    localStorage: {
      getItem: (k: string) => data.get(k) ?? null,
      setItem: (k: string, v: string) => void data.set(k, v),
      removeItem: (k: string) => void data.delete(k),
    },
    dispatchEvent: () => true,
    PushManager: function PushManager() {},
    Notification: notification,
  });
  vi.stubGlobal("Notification", notification);
  vi.stubGlobal("navigator", {
    serviceWorker: { ready: Promise.resolve({ pushManager: { subscribe, getSubscription: async () => current } }) },
  });
  return { subscribe, unsubscribe, notification, data };
}

function fakeApi() {
  const calls: { method: string; url: string; body: string | null }[] = [];
  vi.stubGlobal("fetch", async (url: string, init: RequestInit = {}) => {
    calls.push({ method: init.method ?? "GET", url, body: (init.body as string) ?? null });
    const path = new URL(url).pathname;
    if (path === "/v1/push/key") return Response.json({ public_key: "BAEC" });
    if (path === "/v1/devices") return Response.json({ user_id: "a".repeat(32), device_secret: "s".repeat(43) }, { status: 201 });
    if (path === "/v1/sessions") return Response.json({ token: "t", expires_at: new Date(Date.now() + 3.6e6).toISOString() });
    return new Response(null, { status: 204 });
  });
  return calls;
}

async function fresh() {
  vi.resetModules();
  return { push: await import("./push"), prefs: await import("./prefs") };
}

beforeEach(() => idb.clear());
afterEach(() => vi.unstubAllGlobals());

describe("urlBase64ToBytes", () => {
  it("decodes base64url with or without padding", async () => {
    const { push } = await fresh();
    expect(Array.from(push.urlBase64ToBytes("BAEC"))).toEqual([4, 1, 2]);
    expect(Array.from(push.urlBase64ToBytes("_-8"))).toEqual([255, 239]);
  });
});

describe("enableAlerts", () => {
  it("needs the server copy first", async () => {
    fakeBrowser("default");
    const calls = fakeApi();
    const { push } = await fresh();
    expect(await push.enableAlerts()).toBe("needs_consent");
    expect(calls).toEqual([]);
  });

  it("respects a refusal and a phone-level block", async () => {
    const { notification } = fakeBrowser("default", "denied");
    fakeApi();
    const { push, prefs } = await fresh();
    prefs.setSyncConsent(true);
    expect(await push.enableAlerts()).toBe("blocked");
    expect(notification.requestPermission).toHaveBeenCalledOnce();
  });

  it("subscribes with the server's key and sends only endpoint + keys", async () => {
    const { subscribe } = fakeBrowser("default", "granted");
    const calls = fakeApi();
    const { push, prefs } = await fresh();
    prefs.setSyncConsent(true);
    expect(await push.enableAlerts()).toBe("on");
    expect(Array.from(subscribe.mock.calls[0]![0].applicationServerKey)).toEqual([4, 1, 2]);
    const put = calls.find((c) => c.method === "PUT")!;
    expect(new URL(put.url).pathname).toBe("/v1/me/push-subscriptions");
    expect(JSON.parse(put.body!)).toEqual({
      endpoint: "https://fcm.googleapis.com/fcm/send/phone",
      keys: { p256dh: "P".repeat(87), auth: "A".repeat(22) }, // no expirationTime: the API is strict
    });
    expect(push.alertsState()).toBe("off"); // permission is still "default" on this fake
  });
});

describe("disableAlerts", () => {
  it("tells the server, then unsubscribes the phone", async () => {
    const { unsubscribe } = fakeBrowser("default", "granted");
    const calls = fakeApi();
    const { push, prefs } = await fresh();
    prefs.setSyncConsent(true);
    await push.enableAlerts();
    calls.length = 0;
    expect(await push.disableAlerts()).toBe("off");
    const del = calls.find((c) => c.method === "DELETE")!;
    expect(new URL(del.url).searchParams.get("endpoint")).toBe("https://fcm.googleapis.com/fcm/send/phone");
    expect(unsubscribe).toHaveBeenCalledOnce();
  });

  it("turning the server copy off turns alerts off too", async () => {
    const { unsubscribe } = fakeBrowser("default", "granted");
    fakeApi();
    const { push, prefs } = await fresh();
    prefs.setSyncConsent(true);
    await push.enableAlerts();
    const sync = await import("./profileSync");
    await sync.setConsent(false);
    expect(unsubscribe).toHaveBeenCalledOnce();
  });
});
