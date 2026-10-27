import { afterEach, describe, expect, it, vi } from "vitest";
import { MAX_LISTEN_MS, listen, recognitionSupported } from "./listen";

class FakeRecognition {
  static last: FakeRecognition;
  lang = "";
  interimResults = true;
  maxAlternatives = 5;
  continuous = true;
  onresult: ((e: unknown) => void) | null = null;
  onerror: ((e: { error: string }) => void) | null = null;
  onend: (() => void) | null = null;
  started = false;
  constructor() {
    FakeRecognition.last = this;
  }
  start() {
    this.started = true;
  }
  stop() {
    this.onend?.();
  }
  abort() {}
  say(...words: string[]) {
    this.onresult?.({ results: words.map((w) => [{ transcript: w }]) });
    this.onend?.();
  }
}

afterEach(() => vi.unstubAllGlobals());

describe("listen", () => {
  it("is offered only where the phone can do it", () => {
    vi.stubGlobal("window", {});
    expect(recognitionSupported()).toBe(false);
    vi.stubGlobal("window", { webkitSpeechRecognition: FakeRecognition });
    expect(recognitionSupported()).toBe(true);
  });

  it("listens once in Telugu and returns the words", async () => {
    vi.stubGlobal("window", { webkitSpeechRecognition: FakeRecognition });
    const { result } = listen("te");
    const rec = FakeRecognition.last;
    expect([rec.lang, rec.interimResults, rec.continuous, rec.started]).toEqual(["te-IN", false, false, true]);
    rec.say("వరికి", " ఎంత యూరియా ");
    expect(await result).toEqual({ kind: "text", text: "వరికి  ఎంత యూరియా" });
  });

  it("tells silence, a refused microphone and a failure apart", async () => {
    vi.stubGlobal("window", { SpeechRecognition: FakeRecognition });
    const cases: [string | null, string][] = [[null, "nothing"], ["no-speech", "nothing"], ["not-allowed", "blocked"], ["network", "failed"]];
    for (const [error, kind] of cases) {
      const { result } = listen("en");
      if (error) FakeRecognition.last.onerror?.({ error });
      FakeRecognition.last.onend?.();
      expect((await result).kind).toBe(kind);
    }
  });
});

describe("listen never hangs", () => {
  it("settles after the cap, and soon after a stop the recogniser ignores", async () => {
    vi.useFakeTimers();
    class Silent extends FakeRecognition {
      stop() {} // a recogniser that never reports back
    }
    vi.stubGlobal("window", { SpeechRecognition: Silent });
    const capped = listen("te");
    await vi.advanceTimersByTimeAsync(MAX_LISTEN_MS + 1_000);
    expect(await capped.result).toEqual({ kind: "nothing" });
    const stopped = listen("te");
    stopped.stop();
    await vi.advanceTimersByTimeAsync(1_000);
    expect(await stopped.result).toEqual({ kind: "nothing" });
    vi.useRealTimers();
  });
});
