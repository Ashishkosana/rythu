import { describe, expect, it } from "vitest";
import { pickVoice, weatherSpeech } from "./speak";

type V = { lang: string; name: string };
const mk = (langs: string[]): V[] => langs.map((l, i) => ({ lang: l, name: `v${i}` }));

describe("pickVoice", () => {
  it("prefers exact te-IN for Telugu", () => {
    const v = pickVoice(mk(["en-US", "te-IN", "hi-IN"]) as never, "te");
    expect(v?.lang).toBe("te-IN");
  });
  it("falls back to base language (te) when no exact locale", () => {
    const v = pickVoice(mk(["en-US", "te_IN"]) as never, "te"); // underscore normalized
    expect(v?.lang).toBe("te_IN");
  });
  it("returns null when no matching voice exists", () => {
    expect(pickVoice(mk(["fr-FR", "de-DE"]) as never, "te")).toBeNull();
  });
  it("prefers en-IN for English", () => {
    const v = pickVoice(mk(["en-US", "en-IN"]) as never, "en");
    expect(v?.lang).toBe("en-IN");
  });
});

describe("weatherSpeech", () => {
  it("builds a plain Telugu sentence with chance, verdict, and temperature", () => {
    const s = weatherSpeech({ place: "రేగొండ · Regonda", chance: 60, temp: 30.4, wet: true });
    expect(s).toContain("రేగొండ");
    expect(s).toContain("60 శాతం");
    expect(s).toContain("వర్షం రావచ్చు");
    expect(s).toContain("30 డిగ్రీలు");
  });
  it("says low-chance when dry", () => {
    expect(weatherSpeech({ place: "X", chance: 10, temp: 33, wet: false })).toContain(
      "వర్షం అవకాశం తక్కువ",
    );
  });
  it("handles missing data honestly", () => {
    const s = weatherSpeech({ place: "", chance: null, temp: null, wet: false });
    expect(s).toContain("అందుబాటులో లేదు");
  });
});
