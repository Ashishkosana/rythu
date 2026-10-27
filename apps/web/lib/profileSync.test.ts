import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { buildProfile } from "./profileSync";

// In-memory stand-ins: IndexedDB (idb-keyval) and the bits of `window` that prefs.ts uses.
const idb = new Map<string, unknown>();
vi.mock("idb-keyval", () => ({
  createStore: () => "store",
  get: async (k: string) => idb.get(k),
  set: async (k: string, v: unknown) => void idb.set(k, v),
  del: async (k: string) => void idb.delete(k),
}));

function fakeWindow() {
  const data = new Map<string, string>();
  return {
    localStorage: {
      getItem: (k: string) => data.get(k) ?? null,
      setItem: (k: string, v: string) => void data.set(k, v),
      removeItem: (k: string) => void data.delete(k),
    },
    dispatchEvent: () => true,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
  };
}

/** A tiny fake API: records each request and answers from a script. */
type Handler = (req: { method: string; path: string; headers: Record<string, string>; body: string | null }) => Response;
function fakeApi(handler: Handler) {
  const calls: { method: string; path: string; headers: Record<string, string>; body: string | null }[] = [];
  vi.stubGlobal("fetch", async (url: string, init: RequestInit = {}) => {
    const req = {
      method: init.method ?? "GET",
      path: new URL(url).pathname,
      headers: Object.fromEntries(Object.entries((init.headers ?? {}) as Record<string, string>)),
      body: (init.body as string | undefined) ?? null,
    };
    calls.push(req);
    return handler(req);
  });
  return calls;
}

const CREDS = { user_id: "a".repeat(32), device_secret: "s".repeat(43) };
const SESSION = { token: "t1", expires_at: new Date(Date.now() + 3_600_000).toISOString() };

/** The happy server: registers, opens sessions, stores the profile with a version counter. */
function happyServer() {
  let version = 0;
  let stored: string | null = null;
  return (req: Parameters<Handler>[0]): Response => {
    if (req.path === "/v1/devices") return Response.json(CREDS, { status: 201 });
    if (req.path === "/v1/sessions") return Response.json(SESSION);
    if (req.path === "/v1/me/profile" && req.method === "PUT") {
      const ifMatch = req.headers["If-Match"];
      const create = req.headers["If-None-Match"] === "*";
      if ((create && stored !== null) || (!create && ifMatch !== `W/"${version}"`)) {
        return Response.json({ code: "precondition_failed" }, { status: 412 });
      }
      stored = req.body;
      version += 1;
      return new Response(req.body, { status: 200, headers: { ETag: `W/"${version}"` } });
    }
    if (req.path === "/v1/me/profile") {
      return stored ? new Response(stored, { headers: { ETag: `W/"${version}"` } }) : Response.json({}, { status: 404 });
    }
    if (req.path === "/v1/me" && req.method === "DELETE") return new Response(null, { status: 204 });
    return Response.json({}, { status: 500 });
  };
}

async function freshModules() {
  vi.resetModules();
  const prefs = await import("./prefs");
  const sync = await import("./profileSync");
  return { prefs, sync };
}

beforeEach(() => {
  idb.clear();
  vi.stubGlobal("window", fakeWindow());
});
afterEach(() => vi.unstubAllGlobals());

describe("buildProfile", () => {
  it("sends only what alerts need, and nothing outside coverage", () => {
    const place = { lat: 18.2378, lon: 79.775, place: "  రేగొండ, Bhupalpally  " };
    expect(buildProfile({ place, crop: "paddy", water: null, lang: null })).toEqual({
      village: { name: "రేగొండ, Bhupalpally", lat: 18.2378, lon: 79.775 },
      crop: "paddy",
      water: "rainfed",
      lang: "te",
      fields: [],
    });
    expect(buildProfile({ place: { lat: 13.08, lon: 80.27, place: "Chennai" }, crop: null, water: "tank", lang: "en" }).village).toBeNull();
    expect(buildProfile({ place: { ...place, place: "x".repeat(200) }, crop: null, water: null, lang: null }).village?.name).toHaveLength(80);
  });
});

describe("buildProfile fields", () => {
  it("sends fields in the server's date window and keeps stale ones on the phone only", () => {
    const f = (id: string, reference_date: string) => ({ id, name: " East ", crop: "cotton" as const, reference_date });
    const out = buildProfile({
      place: null, crop: null, water: null, lang: null, today: "2026-10-27",
      fields: [f("aaaaaa", "2026-06-20"), f("bbbbbb", "2025-09-01"), f("cccccc", "2026-12-26"), f("dddddd", "2026-12-27")],
    });
    expect(out.fields).toEqual([
      { id: "aaaaaa", name: "East", crop: "cotton", reference_date: "2026-06-20" },
      { id: "cccccc", name: "East", crop: "cotton", reference_date: "2026-12-26" }, // exactly 60 days ahead
    ]);
  });
});

describe("syncProfile", () => {
  it("sends nothing at all without consent", async () => {
    const { prefs, sync } = await freshModules();
    const calls = fakeApi(happyServer());
    prefs.savePlace({ lat: 18.2378, lon: 79.775, place: "Regonda" });
    expect((await sync.syncProfile()).state).toBe("off");
    expect(calls).toEqual([]);
    expect(idb.size).toBe(0); // no account was made either
  });

  it("with consent: registers once, creates, then updates only on change", async () => {
    const { prefs, sync } = await freshModules();
    const calls = fakeApi(happyServer());
    prefs.savePlace({ lat: 18.2378, lon: 79.775, place: "Regonda" });
    expect((await sync.setConsent(true)).state).toBe("saved");
    expect(calls.map((c) => `${c.method} ${c.path}`)).toEqual(["POST /v1/devices", "POST /v1/sessions", "PUT /v1/me/profile"]);
    expect(calls[2]!.headers).toMatchObject({ "If-None-Match": "*", Authorization: "Bearer t1" });

    calls.length = 0;
    await sync.syncProfile();
    expect(calls).toEqual([]); // nothing changed → nothing sent

    prefs.saveCrop("cotton");
    await sync.syncProfile();
    expect(calls.map((c) => `${c.method} ${c.path}`)).toEqual(["PUT /v1/me/profile"]); // token reused
    expect(calls[0]!.headers["If-Match"]).toBe('W/"1"');
    expect(JSON.parse(calls[0]!.body!).crop).toBe("cotton");
  });

  it("after a version conflict it re-reads the server's version and writes again", async () => {
    const { prefs, sync } = await freshModules();
    const server = happyServer();
    const calls = fakeApi(server);
    prefs.setSyncConsent(true);
    prefs.saveSyncState({ etag: 'W/"99"', synced: null }); // stale: someone else wrote since
    // The server already holds a profile at version 1.
    server({ method: "PUT", path: "/v1/me/profile", headers: { "If-None-Match": "*" }, body: '{"lang":"en"}' });
    expect((await sync.syncProfile()).state).toBe("saved");
    const writes = calls.filter((c) => c.method === "PUT").map((c) => c.headers["If-Match"]);
    expect(writes).toEqual(['W/"99"', 'W/"1"']);
  });

  it("if the server forgot this phone, it drops the old account and makes a new one", async () => {
    const { prefs, sync } = await freshModules();
    idb.set("credentials", { user_id: "b".repeat(32), device_secret: "old".repeat(15) });
    let sessions = 0;
    const server = happyServer();
    const calls = fakeApi((req) => {
      if (req.path === "/v1/sessions" && sessions++ === 0) return Response.json({ code: "unauthorized" }, { status: 401 });
      return server(req);
    });
    prefs.setSyncConsent(true);
    expect((await sync.syncProfile()).state).toBe("saved");
    expect(calls.map((c) => `${c.method} ${c.path}`)).toEqual([
      "POST /v1/sessions", "POST /v1/devices", "POST /v1/sessions", "PUT /v1/me/profile",
    ]);
    expect(idb.get("credentials")).toEqual(CREDS);
  });

  it("an unreachable server is a quiet failure, retried later", async () => {
    const { prefs, sync } = await freshModules();
    vi.stubGlobal("fetch", async () => Promise.reject(new TypeError("offline")));
    prefs.setSyncConsent(true);
    expect((await sync.syncProfile()).state).toBe("failed");
  });
});

describe("deleteServerData", () => {
  it("erases the server copy, forgets the account and turns consent off", async () => {
    const { prefs, sync } = await freshModules();
    const calls = fakeApi(happyServer());
    await sync.setConsent(true);
    expect((await sync.deleteServerData())).toBe(true);
    expect(calls.at(-1)).toMatchObject({ method: "DELETE", path: "/v1/me" });
    expect(idb.has("credentials")).toBe(false);
    expect(prefs.syncConsent()).toBe(false);
  });

  it("keeps the account if the server could not be reached, so it can be retried", async () => {
    const { prefs, sync } = await freshModules();
    fakeApi(happyServer());
    await sync.setConsent(true);
    vi.stubGlobal("fetch", async () => Promise.reject(new TypeError("offline")));
    expect(await sync.deleteServerData()).toBe(false);
    expect(idb.has("credentials")).toBe(true);
    expect(prefs.syncConsent()).toBe(false); // but nothing more is uploaded meanwhile
  });
});
