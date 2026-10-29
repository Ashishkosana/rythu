# Rythu — decision register

_Written 2026-10-29, after the first working deploy. One page with every choice that shapes the app: what
was chosen, why, what else was possible, and what changing it would cost. The five ADRs in `adr/` hold the
long form of D1, D4, D7, D9 and D12. Fill in **Your call** (keep / change to … / revisit when …); a change
becomes a PR, and a big one gets its own ADR._

Cost to change: **low** = a setting or a few lines · **medium** = a PR of a day or two · **high** = a
migration, or something users or Google would notice.

## Product and audience

| # | Decision | Why | Alternatives | Cost to change | Your call |
| --- | --- | --- | --- | --- | --- |
| P1 | Telugu first, English second; simple words, large text, icons; answers read aloud | First user is a Telangana farmer; low literacy and new-to-smartphone users (`farmer-needs-research.md`) | Hindi / other states; English-first | medium (strings are in `lib/`, content files per language) | |
| P2 | Telangana only; the API answers 400 outside it | Crop rules, doses, prices and schemes are checked for Telangana | All India (needs per-state content) | high (content, not code) | |
| P3 | Five Kharif crops: paddy, cotton, maize, red gram, chilli | Main crops of the pilot area | Add Rabi crops, vegetables | medium per crop (calendar, rules, guides) | |
| P4 | No sign-up: the phone gets an anonymous identity | Zero friction, minimal personal data (ADR 0004) | Phone OTP; Google/email | medium; losing the phone loses the profile today | |
| P5 | Only checked content: doses, prices, pests and schemes cite PJTSAU / ICAR / government sources, and items still to verify are marked | Wrong farm advice does real harm | Broader "general" advice | — (a principle) | |

## Architecture

| # | Decision | Why | Alternatives | Cost to change | Your call |
| --- | --- | --- | --- | --- | --- |
| D1 | One Python service (FastAPI) on Azure Functions Flex Consumption, with timers and a queue in the same app | One developer, ≈ $0/month, needs both HTTP and background jobs (ADR 0001) | Container Apps; App Service B1 (≈ $13/month, always warm) | medium (the app is plain FastAPI; only `function_app.py` is Azure-specific) | |
| D2 | Hexagonal layout: pure `domain/` (rules, calendar), `adapters/` for the outside world, `app/` wires them | Rules testable without network; swap providers without touching rules | Flat service | — | |
| D3 | Website is a static export of Next.js, served from an Azure Storage static website (norwayeast) | Static Web Apps isn't allowed in any student-subscription region (found during deploy, PR #36) | Static Web Apps on a paid subscription; Cloudflare Pages / GitHub Pages (free, outside Azure) | low–medium (any static host; Android is tied to the host, see A2) | |
| D4 | Storage: Azure Table Storage (forecast cache, users, budget counters) | Key lookups only, pennies, same account Functions needs (ADR 0002) | Cosmos DB (region-limited on student plans); Postgres (costs) | high (data migration) | |
| D5 | Region norwayeast; dev only, prod gated behind `AZURE_PROD_ENABLED` | Student policy allows 5 regions; Flex Consumption is available there | westus etc. (similar latency to India, ~150–250 ms) | medium (new resource group, redeploy) | |
| D6 | Secrets in Key Vault, read by the app's managed identity; push signing happens inside Key Vault | No keys in config or code | App settings (simpler, weaker) | — | |
| D7 | Client data: TanStack Query cached in IndexedDB; offline shows the last forecast with its age | First screen < 3 s on 3G, works offline (ADR 0003) | SWR; server rendering | medium | |
| D8 | Deploy: GitHub Actions with OIDC (no stored Azure password); every deploy ends with a smoke test of the live app | Safe, repeatable; caught 3 real bugs this week | Manual `az` deploys | — | |

## Weather and alerts

| # | Decision | Why | Alternatives | Cost to change | Your call |
| --- | --- | --- | --- | --- | --- |
| W1 | Forecast source: Open-Meteo (free, no key) | Free, good model mix, no signup | IMD (official, harder API); paid providers | medium (one adapter) | |
| W2 | Pre-warm every farmer's cell every 20 min; forecast at most ~30 min old | Farmers never wait for the upstream call | Fetch on demand only | low (`schedule` in `function_app.py`) | |
| W3 | At most 120 on-demand upstream calls/hour, 60 pre-warmed cells | Protects Open-Meteo's ~10k/day free quota from spikes or abuse | Higher caps | low (settings) | |
| W4 | Alerts at 06:45, 12:45 and 17:45 IST; never at night | Before field work, midday, evening planning | Other times; instant alerts | low | |
| W5 | Alert types: rain before spraying, spray windows, dry spell (rainfed vs irrigated), crop-calendar tasks; each sent once | Most common losses in the research | More or fewer types | low–medium per rule | |
| W6 | At most 30 new devices/hour | Stops someone scripting sign-ups | Higher; CAPTCHA | low (setting) | |

## Ask Rythu (AI question helper)

| # | Decision | Why | Alternatives | Cost to change | Your call |
| --- | --- | --- | --- | --- | --- |
| Q1 | **Off** until you add an Anthropic key and set `RYTHU_ASSISTANT_ENABLED=true` | Costs money per question; needs your decision | — | low | |
| Q2 | Answers only from Rythu's own checked content; anything else → "call the Kisan Call Centre 1800-180-1551"; health emergencies → 108 first | Free-form chatbots give unsafe farm advice | Open chatbot | medium | |
| Q3 | Model `claude-opus-5-5` at low effort | Best Telugu and instruction-following; low effort keeps cost down | Sonnet or Haiku (cheaper; test with the 17 eval cases first) | low (`RYTHU_ASSISTANT_MODEL`) | |
| Q4 | 10 questions per phone per day, 200 for everyone per day | Caps the bill even if someone abuses it | Other limits | low (settings) | |

## Android and Play Store

| # | Decision | Why | Alternatives | Cost to change | Your call |
| --- | --- | --- | --- | --- | --- |
| A1 | Trusted Web Activity: the app is the website in a thin Android shell | Web updates reach users without a Play review (ADR 0005) | Capacitor; native app | high | |
| A2 | Tied to `stwebdev5lwqnva5y6yym.z1.web.core.windows.net` (the dev site) | The only deployed site today | A custom domain or a prod site — **decide before the first Play upload**; changing later means a new upload | low now, high after release | **Keep the dev site for now** (2026-10-29). A move after the Play release needs a new upload. |
| A3 | Package id `io.github.ashishkosana.rythu` | Unique without owning a domain | Your own domain's id | **permanent once on Play** | **Keep** (2026-10-29) |
| A4 | Min Android 7.0 (API 24), target API 36 | Required by the Android browser helper; Play's 2026 rule | — | — | |

## Money and limits

| # | Decision | Why | Alternatives | Cost to change | Your call |
| --- | --- | --- | --- | --- | --- |
| M1 | Budget alert at $5/month on the resource group | Student credit is $100/year | Higher/lower | low (Bicep param) | |
| M2 | Logs kept 30 days | Enough to debug; costs nothing extra | Longer (costs) | low | |
| M3 | AWS: unused, still to delete (`aws-retirement.md`) | Nothing calls it; it may still bill | Keep | each delete needs your OK | |

## Not built yet (waiting on you)

| # | What | Needs |
| --- | --- | --- |
| N1 | Mandi prices with MSP comparison (S15) | Your data.gov.in API key |
| N2 | Play Store release | Play Console account ($25), upload key, decisions A2 and A3 |
| N3 | Ask Rythu live | Anthropic key, decision Q1 |
| N4 | Production environment | Your go-ahead; same Bicep with `env=prod` |
