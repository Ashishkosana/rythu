# Rythu — Chilli (mirchi) Rules Spec (verified)

*Derived 2026-07-13 from a research → adversarial farmer-safety verify → synthesis pass (same
rigor as `weather-slice-spec.md`). Chilli is a major Bhupalpally crop. All rules are
weather-data-only, conservative, probability-framed, product-neutral, and cited. **Vet the
thresholds + season windows with the district agri office / PJTSAU before pilot.***

Chilli gets the crop-agnostic weather rules (spray/irrigate/sow/fieldwork) **plus** these
chilli-specific reads. Seasons are disjoint Kharif+Rabi month-sets (`RuleSpec.months`).

## Active chilli rules

| id | action | months | trigger (verified) | why |
|---|---|---|---|---|
| `chilli-waterlogging-drainage` | fieldwork | all | next 3 d: any day `precip_sum ≥ 40 mm` **or** (`≥ 25 mm` **and** `prob_max ≥ 70`) | Chilli is very waterlogging-sensitive (root/collar rot). Low-regret "clear your drains". Tighter than the maize rule — chilli is **removed** from `drainage-heavy-rain-maize` so exactly one fires. |
| `chilli-heat-flowerdrop` | irrigate | 2-4, 9-12 | 2+ consecutive days `tmax ≥ 35°C` in next 7 d; **suppressed** if a qualifying day also has rain (`prob ≥ 60` or `sum ≥ 2 mm`) | Heat sheds flowers/young fruit; light early/evening irrigation eases it. Don't push irrigation into a wet window. |
| `chilli-harvest-drying-rain` | harvest | 11-3, 2-5 | next 3 d: any day `prob_max ≥ 60` **or** `sum ≥ 5 mm` | Rain rots ripe/drying red chilli (mould, price loss). Threshold lower than paddy (drying stock spoils at a few mm). Leads with the "only if already red-ripe" gate. |
| `chilli-anthracnose-humid-wet-fruiting` | **scout** | 9-11 | next 48 h: a run of **≥6 consecutive hours** `RH ≥ 85` & `20 ≤ temp ≤ 30`, **and** an actually-wet hour (`precip ≥ 0.2 mm` or a wet WMO code) | Anthracnose/fruit-rot (Colletotrichum) is the biggest weather-driven chilli disease. RH is a leaf-wetness proxy; a "go LOOK" prompt, never a spray order. |
| `chilli-thrips-dry-warm-leafcurl` | **scout** | 8-3 | next 3 d ALL dry (`sum < 2` & `prob_max < 40`, all known) & ≥1 day `tmax 28-38` & majority of daytime (09-17) hours `RH < 60` | Thrips ("murda" leaf-curl) build up in dry warm spells. Scout-only; the caveat warns the local black thrips also spreads in wet weather, so no-alert ≠ safe. |

The **`scout`** action = "go look at your crop, do not spray on a guess" — a new action so the
UI can render a distinct 🔍 card. Both scout rules lead with the crop-stage gate ("If your
chilli is carrying fruit…").

## Deferred / rejected (recorded in `DEFERRED_RULE_IDS`)

- `chilli-thrips-mite-rain-suppress-hold-spray` — **rejected**: "wait for rain to wash off
  thrips" is *false* for the now-dominant local black thrips (*Thrips parvispinus*, rain-loving);
  advising delay during an outbreak could lose the crop.
- `chilli-mite-warm-humid-leafcurl` — deferred: the warm+humid broad-mite premise is contested
  (strong studies find the opposite); would cry-wolf.
- `chilli-nursery-dampingoff-wet` — deferred: needs nursery/seedling stage the app can't see;
  RH trigger over-fires in monsoon.
- `chilli-spray-timing-rain-wind-washoff` — deferred as duplicate of the shipped
  `spray-rain-washoff` + `spray-wind-drift` (which already fire for chilli).
- `chilli-transplant-avoid-heavy-rain` — deferred as duplicate of `sow-avoid-before-washout`.

## Sources
Chilli anthracnose epidemiology (Saxena 2016, Front. Microbiol.), TNAU chilli pest/disease
portal, UC IPM + PNW pepper root/crown rot, Long Paddock capsicum heat CTT, PJTSAU pre-harvest
chilli advisory, chilli thrips/mite weather-dynamics studies. Full URLs in each rule's `sources`.
`TODO-VET`: heat cutoffs (35/40°C), drainage mm, season month-sets, and the anthracnose/thrips
thresholds need a local package-of-practices (ICAR/PJTSAU/TNAU) sign-off before pilot.
