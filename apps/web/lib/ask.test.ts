import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const idb = new Map<string, unknown>();
vi.mock("idb-keyval", () => ({
  createStore: () => "store",
  get: async (k: string) => idb.get(k),
  set: async (k: string, v: unknown) => void idb.set(k, v),
  del: async (k: string) => void idb.delete(k),
}));

const ANSWER = {
  covered: true,
  answer: "యూరియా 45 కిలోల బస్తా ₹266.50.",
  sources: [{ id: "fertilizer.bag_prices", title: "MRP", url: "https://pib.gov.in/x", needs_verification: false }],
  used_todays_weather: false,
  remaining_today: 9,
  helpline: { display: "1800-180-1551", tel: "tel:18001801551" },
};

function fakeApi(ask: () => Response) {
  const calls: { url: string; init: RequestInit }[] = [];
  vi.stubGlobal("fetch", async (url: string, init: RequestInit = {}) => {
    calls.push({ url, init });
    const path = new URL(url).pathname;
    if (path === "/v1/devices") return Response.json({ user_id: "a".repeat(32), device_secret: "s".repeat(43) }, { status: 201 });
    if (path === "/v1/sessions") return Response.json({ token: "t", expires_at: new Date(Date.now() + 3.6e6).toISOString() });
    return ask();
  });
  return calls;
}

async function fresh() {
  vi.resetModules();
  return import("./ask");
}

beforeEach(() => {
  idb.clear();
  vi.stubGlobal("navigator", { onLine: true });
});
afterEach(() => vi.unstubAllGlobals());

describe("askBody", () => {
  it("sends the question, language and only the context there is", async () => {
    const { askBody } = await fresh();
    expect(askBody("  ఎంత?  ", "te", {})).toEqual({ question: "ఎంత?", lang: "te", water: "rainfed" });
    expect(askBody("q?", "en", { lat: 18.24, lon: 79.78, crop: "cotton", water: "borewell" })).toEqual({
      question: "q?", lang: "en", lat: 18.24, lon: 79.78, crop: "cotton", water: "borewell",
    });
    expect(askBody("x".repeat(400), "en", {}).question).toHaveLength(300);
  });
});

describe("askRythu", () => {
  it("asks with this phone's token (making the device account on first use)", async () => {
    const calls = fakeApi(() => Response.json(ANSWER));
    const { askRythu } = await fresh();
    const r = await askRythu("యూరియా ధర?", "te", { crop: "paddy" });
    expect(r).toEqual({ kind: "answer", out: ANSWER });
    const ask = calls.find((c) => c.url.endsWith("/v1/assistant/ask"))!;
    expect(ask.init.method).toBe("POST");
    expect((ask.init.headers as Record<string, string>).Authorization).toBe("Bearer t");
    expect(JSON.parse(ask.init.body as string)).toMatchObject({ question: "యూరియా ధర?", crop: "paddy" });
    expect(calls.some((c) => c.url.endsWith("/v1/devices"))).toBe(true);
  });

  it("names every way it can go wrong", async () => {
    const cases: [() => Response, string][] = [
      [() => Response.json({ code: "rate_limited" }, { status: 429 }), "limit"],
      [() => Response.json({ code: "assistant_off" }, { status: 503 }), "off"],
      [() => Response.json({ code: "unavailable" }, { status: 503 }), "unavailable"],
      [() => new Response("boom", { status: 500 }), "unavailable"],
    ];
    for (const [res, kind] of cases) {
      fakeApi(res);
      const { askRythu } = await fresh();
      expect((await askRythu("why?", "en", {})).kind).toBe(kind);
    }
  });

  it("doesn't try without internet", async () => {
    vi.stubGlobal("navigator", { onLine: false });
    const calls = fakeApi(() => Response.json(ANSWER));
    const { askRythu } = await fresh();
    expect(await askRythu("why?", "en", {})).toEqual({ kind: "offline" });
    expect(calls).toEqual([]);
  });

  it("canAsk needs a real question", async () => {
    const { canAsk } = await fresh();
    expect([canAsk("  "), canAsk("ab"), canAsk("abc"), canAsk("x".repeat(301))]).toEqual([false, false, true, false]);
  });
});
