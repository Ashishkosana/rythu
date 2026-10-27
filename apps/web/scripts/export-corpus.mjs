// Export the app's verified content (fertilizer doses + bag prices, pest guide, crop guides, schemes,
// helplines) for "Ask Rythu" (S17), which may answer ONLY from it. The API adds its own crop calendar.
// One source of truth: the assistant can never say something these screens don't.
//   node --experimental-strip-types scripts/export-corpus.mjs          write
//   node --experimental-strip-types scripts/export-corpus.mjs --check  CI: fail if the committed copy is stale

import { readFileSync, writeFileSync } from "node:fs";
import { BAG_PRICES, CROP_DOSES, PRICES_AS_OF, UREA_BAG_KG, BAG_KG } from "../lib/agronomy.ts";
import { CROP_GUIDES } from "../lib/crops.ts";
import { CYBER_CRIME, KISAN_CALL_CENTRE } from "../lib/helplines.ts";
import { PESTS } from "../lib/pests.ts";
import { SCHEMES } from "../lib/schemes.ts";

const OUT = new URL("../../../services/weather/src/rythu_weather/content/web_content.json", import.meta.url);

const lines = (...xs) => xs.filter(Boolean).join("\n");
const item = (id, kind, title, text, source, needsVerification = false) => ({
  id, kind, title, text, source, needs_verification: needsVerification,
});

export function corpus() {
  return [
    ...CROP_DOSES.map((d) =>
      item(`fertilizer.${d.key}`, "fertilizer", `Fertilizer dose: ${d.name_en} / ${d.name_te}`, lines(
        `N:P2O5:K2O per acre = ${d.n} : ${d.p} : ${d.k} kg (source figure: ${d.original}).`,
        `Split / timing (te): ${d.splits_te}`,
        `Bags: urea ${UREA_BAG_KG} kg, DAP and MOP ${BAG_KG} kg. The app's calculator converts the dose to bags (DAP's nitrogen is subtracted before sizing urea).`,
        `Confidence: ${d.confidence}. A soil test (Soil Health Card) changes the real need; confirm with the AEO.`,
      ), d.source, d.needsVerification)),
    item("fertilizer.bag_prices", "price", "What a fertilizer bag should cost (MRP)", lines(
      ...BAG_PRICES.map((p) => `${p.name_en} / ${p.name_te}, ${p.bagKg} kg bag: ${
        p.rupees === null ? "company-set; read the MRP printed on the bag" : `${p.fixed ? "" : "about "}₹${p.rupees}${p.fixed ? " (fixed by the government)" : " (company-set; check the bag)"}`}.`),
      `Never pay more than the MRP printed on the bag, and always take the bill. Selling above MRP is an offence (Fertiliser Control Order 1985).`,
      `Overcharged: complain with the bill to the Mandal Agriculture Officer (MAO) / AEO, or call the free Kisan Call Centre ${KISAN_CALL_CENTRE.display}.`,
      `Prices as of ${PRICES_AS_OF}.`,
    ), BAG_PRICES[0].sources[0]),
    ...PESTS.map((p) =>
      item(`pest.${p.key}`, "pest", `Pest: ${p.name_en} / ${p.name_te} on ${p.crop_te}`, lines(
        `Symptoms (te): ${p.symptom_te}`,
        `When to act — threshold (te): ${p.threshold_te}`,
        `First, without chemicals (te): ${p.ipmFirst_te}`,
        `Only above the threshold (te): ${p.chemical_te}`,
        `Before any spray: photograph it and confirm with the AEO / Kisan Call Centre.`,
      ), p.source, p.needsVerification)),
    ...CROP_GUIDES.map((c) =>
      item(`crop.${c.key}`, "crop", `Crop guide: ${c.name_en} / ${c.name_te}`, lines(
        `Season: ${c.season_en} / ${c.season_te}`,
        `Water: ${c.water_en} / ${c.water_te}`,
        `Sowing: ${c.sow_en} / ${c.sow_te}`,
        ...c.tips_en.map((t, i) => `Tip: ${t} / ${c.tips_te[i] ?? ""}`),
      ), c.source)),
    ...SCHEMES.map((s) =>
      item(`scheme.${s.key}`, "scheme", `Scheme: ${s.name_en} / ${s.name_te}`, lines(
        `Level: ${s.level}. Status: ${s.status}${s.status_as_of ? ` (as of ${s.status_as_of})` : ""}.`,
        `What: ${s.what_en} / ${s.what_te}`,
        `Who: ${s.who_en} / ${s.who_te}`,
        `How: ${s.how_en} / ${s.how_te}`,
        s.honesty_en && `Note: ${s.honesty_en} / ${s.honesty_te ?? ""}`,
        `Official site: ${s.url}`,
      ), s.url, s.status === "verify" || s.status === "at_risk")),
    item("help.kisan_call_centre", "help", "Kisan Call Centre (free expert advice)",
      `Free call ${KISAN_CALL_CENTRE.display}, 6 am to 10 pm, Telugu spoken: agriculture graduates answer crop, pest and scheme questions. Or ask the village AEO / Rythu Vedika.`,
      KISAN_CALL_CENTRE.source),
    item("help.cyber_fraud", "help", "Scams: fake apps and fraud calls",
      `Never install an APK file sent on WhatsApp or SMS, even if it says PM-Kisan. Install apps only from the Play Store. Never share an OTP or UPI PIN. If cheated, call ${CYBER_CRIME.display} at once or report on cybercrime.gov.in.`,
      CYBER_CRIME.source),
  ];
}

const json = JSON.stringify(corpus(), null, 1) + "\n";
if (process.argv.includes("--check")) {
  let committed = "";
  try { committed = readFileSync(OUT, "utf8"); } catch { /* missing counts as stale */ }
  if (committed !== json) {
    console.error("web_content.json is stale: run `npm run gen:corpus` in apps/web and commit it");
    process.exit(1);
  }
  console.log("corpus up to date");
} else {
  writeFileSync(OUT, json);
  console.log(`corpus: ${corpus().length} items → ${OUT.pathname}`);
}
