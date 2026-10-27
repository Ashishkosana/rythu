# Rythu on Azure — one-time setup runbook

Everything below runs in **Azure Cloud Shell** (portal → `>_` icon → Bash). It has `az`, `git` and `gh`
preinstalled. Commands are copy-paste; replace `<…>` placeholders. Nothing here costs money beyond the
pilot's near-zero usage, and a budget alert emails you at $4 (80 % of $5).

What `main.bicep` creates in one resource group: a Storage static website for the web app, a Flex
Consumption Function App (Python 3.12, managed identity) for the API, a Key Vault holding the
device-token signing key (generated at deploy time, readable only by the app's identity) and the Web
Push signing key (non-exportable; the app may only ask Key Vault to sign), an `alerts` queue, a storage account with **shared-key access disabled** (identity-only: no keys exist to leak),
the `forecast` table, Application Insights + Log Analytics with a 0.1 GB/day cap, a budget alert, and a
user-assigned identity that GitHub Actions can log in as via OIDC (no stored secret).

## 0. Pre-flight: can this subscription run it? (2 minutes)

```bash
# Regions your Azure for Students subscription may deploy to (policy):
az policy assignment list --query "[?contains(displayName,'region') || contains(displayName,'location')].parameters" -o json
# Regions that offer Flex Consumption:
az functionapp list-flexconsumption-locations --query "[].name" -o tsv
# Register the resource providers this template uses (safe to re-run):
for p in Microsoft.Web Microsoft.Storage Microsoft.Insights Microsoft.OperationalInsights \
         Microsoft.ManagedIdentity Microsoft.Consumption Microsoft.KeyVault; do az provider register --namespace $p; done
```

Pick a region that appears in **both** lists, preferring `centralindia` or `southindia` (closest to
Telangana; an Azure for Students policy may offer neither — `norwayeast` is the nearest of the usual
five). Everything, the website included, goes in that one region. If **no** region is in both, or step 1 fails with "Flex Consumption … not enabled/supported
for this subscription", stop and say so — the fallback is ADR 0001 option 2 (Container Apps); the app code
(plain ASGI) does not change.

## 1. Create the infrastructure (≈ 5 minutes)

```bash
git clone https://github.com/Ashishkosana/rythu && cd rythu
REGION=norwayeast                              # from step 0
EMAIL="you@example.com"                        # budget alerts go here — keep the quotes
RG=rg-rythu-dev
az group create -n $RG -l $REGION

# Preview first — read what it will create:
az deployment group what-if -g $RG -f infra/azure/main.bicep \
  -p location=$REGION env=dev budgetContactEmail="$EMAIL"

az deployment group create -g $RG -n rythu-dev -f infra/azure/main.bicep \
  -p location=$REGION env=dev budgetContactEmail="$EMAIL" \
  --query properties.outputs -o jsonc

# Turn the web storage account into a website (one time; not settable from Bicep):
out() { az deployment group show -g $RG -n rythu-dev --query "properties.outputs.$1.value" -o tsv; }
az storage blob service-properties update --account-name "$(out webAppName)" \
  --static-website --index-document index.html --404-document 404.html -o none
```

If it fails **only** on the budget (some subscription types don't support Cost Management budgets),
re-run the last command with `deployBudget=false` added and set a spending alert in the portal instead.

## 2. Allow GitHub to deploy code — to these two apps only

```bash
az role assignment create --assignee-object-id "$(out deployPrincipalId)" \
  --assignee-principal-type ServicePrincipal \
  --role "Website Contributor" --scope "$(out functionAppId)"
az role assignment create --assignee-object-id "$(out deployPrincipalId)" \
  --assignee-principal-type ServicePrincipal \
  --role "Storage Blob Data Contributor" --scope "$(out webAppId)"
```

The deploy identity can push code to the two apps and nothing else: it cannot read data, change other
resources, or grant permissions. Infrastructure changes stay a human step (this runbook). It uploads the
website with its Entra ID login, so no storage key or token is ever stored in GitHub.

## 3. Tell GitHub where to deploy (repository variables, not secrets — none of these are credentials)

```bash
gh auth login                                   # once, in Cloud Shell
REPO=Ashishkosana/rythu
gh api -X PUT repos/$REPO/environments/dev      # the GitHub Environment the OIDC trust is bound to
gh variable set AZURE_CLIENT_ID       -R $REPO --body "$(out deployClientId)"
gh variable set AZURE_TENANT_ID       -R $REPO --body "$(az account show --query tenantId -o tsv)"
gh variable set AZURE_SUBSCRIPTION_ID -R $REPO --body "$(az account show --query id -o tsv)"
gh variable set AZURE_FUNCTIONAPP_NAME -R $REPO --body "$(out functionAppName)"
gh variable set AZURE_FUNCTIONAPP_URL  -R $REPO --body "$(out functionAppUrl)"
gh variable set AZURE_STATICWEBAPP_NAME -R $REPO --body "$(out webAppName)"
gh variable set AZURE_STATICWEBAPP_URL  -R $REPO --body "$(out webAppUrl)"
```

(Without `gh`: GitHub → repo → Settings → Environments → New `dev`; Settings → Secrets and variables →
Actions → **Variables** tab → add the seven names with the values printed by step 1.)

## 4. Deploy

`.github/workflows/deploy-azure.yml` deploys automatically **after CI passes on `main`**, and can be run by
hand from the Actions tab. GitHub only runs these triggers from workflow files on the default branch, so
the first deploy happens once this work is merged to `main`. The workflow packages
`services/weather` (`scripts/package_functions.sh`), logs in with OIDC, deploys with a remote build, then
smoke-tests `/healthz`, `/v1/weather` and the coverage 400 against the live URL. A second job builds the
web app's static export against that API URL (`NEXT_PUBLIC_API_BASE`), checks the JS budget, uploads
`apps/web/out` to the Storage static website and smoke-tests the page, its CSP and the service worker headers.
Open the `AZURE_STATICWEBAPP_URL` on a phone: that is the app.

## 5. Ask Rythu (optional — this one costs money)

Ask Rythu (S17) answers farmers' questions with Claude, only from Rythu's own checked content. It ships
**off**: it needs both the switch and an Anthropic API key, and neither is set by default.

1. Create an API key at console.anthropic.com and set a **monthly spend limit** there too — a second
   ceiling above the app's own (10 questions per phone per day, 200 per day in total).
2. Put the key in Key Vault — never in a parameter, a file in the repo or a GitHub secret. Writing a
   secret needs a data-plane role on the vault (it uses RBAC):
   ```bash
   VAULT=<keyVaultName from step 1's output>
   az role assignment create --role "Key Vault Secrets Officer" --assignee "$(az ad signed-in-user show --query id -o tsv)" \
     --scope "$(az keyvault show -n $VAULT --query id -o tsv)"
   read -rs KEY && az keyvault secret set --vault-name $VAULT --name anthropic-api-key --value "$KEY" -o none && unset KEY
   ```
3. Optional but cheap: run the eval first (17 questions, a few US cents each), from `services/weather`:
   `RYTHU_ANTHROPIC_API_KEY=... uv run python scripts/eval_assistant.py --yes-spend`. Read
   `evals/runs/<time>/summary.json`: pass rate, cost per answer, cache-read share.
4. Switch it on: re-run step 1's `create` with `-p assistantEnabled=true` (the parameter is the durable
   setting; a later deploy without it switches the assistant off again).

Model and effort come from `RYTHU_ASSISTANT_MODEL` (default `claude-opus-5-5`) and
`RYTHU_ASSISTANT_EFFORT` (default `low`); quotas from `RYTHU_ASSISTANT_PER_DEVICE_PER_DAY` and
`RYTHU_ASSISTANT_DAILY_CAP` (`services/weather/src/rythu_weather/app/settings.py`).

## 6. Production (S10) — when the pilot outgrows dev

The same template with `env=prod`, in its own resource group, deployed by the same workflow **after**
dev has passed its smoke tests and **after you approve** it. Prod has its own deploy identity, trusted
only for the GitHub Environment `prod`, so a dev run can never touch prod.

```bash
RG=rg-rythu-prod
az group create -n $RG -l $REGION
az deployment group create -g $RG -n rythu-prod -f infra/azure/main.bicep \
  -p location=$REGION env=prod budgetContactEmail="$EMAIL"
az storage blob service-properties update --account-name "$(az deployment group show -g $RG -n rythu-prod --query properties.outputs.webAppName.value -o tsv)" \
  --static-website --index-document index.html --404-document 404.html -o none
out() { az deployment group show -g $RG -n rythu-prod --query "properties.outputs.$1.value" -o tsv; }
# step 2's two role assignments, with these outputs (out deployPrincipalId, out functionAppId, out webAppId)
gh api -X PUT repos/$REPO/environments/prod
for v in "AZURE_CLIENT_ID $(out deployClientId)" "AZURE_FUNCTIONAPP_NAME $(out functionAppName)" \
         "AZURE_FUNCTIONAPP_URL $(out functionAppUrl)" "AZURE_STATICWEBAPP_NAME $(out webAppName)" \
         "AZURE_STATICWEBAPP_URL $(out webAppUrl)"; do
  set -- $v; gh variable set "$1" --env prod -R $REPO --body "$2"   # ON THE ENVIRONMENT, not the repo
done
gh variable set AZURE_PROD_ENABLED -R $REPO --body true
```

Then GitHub → Settings → Environments → `prod` → **Required reviewers**: add yourself, so every prod
deploy waits for your click. Prod variables must be set on the `prod` environment: anything missing
there would fall back to the repository's dev value, so each deploy job first checks that the app name
it is about to deploy to contains `-prod-` and stops otherwise. Point the Android app at the prod host
(`apps/android/twa-manifest.json`) before the Play release; Ask Rythu stays off in prod until you set
`assistantEnabled=true` there too.

## Operating it

| Task | How |
| --- | --- |
| See logs | App Insights → Logs: `traces \| extend d = parse_json(message) \| where d.event == "weather.request"` |
| Errors only | `traces \| extend d = parse_json(message) \| where d.level == "ERROR"` |
| Roll back | Actions → Deploy (Azure) → re-run the last good run (each run deploys one tested commit) |
| Web app CSP | a `<meta>` tag in every page, generated per build (`apps/web/scripts/postbuild.mjs`); the Storage website sends no custom headers |
| Change infra | edit `main.bicep`, run step 1's `what-if`, then `create` again (idempotent) |
| Cost | Portal → Cost Management; the budget emails at 80 % actual / 100 % forecast |
| Alerts not arriving | App Insights: `traces \| where message has "alerts."` (evaluated / delivered / retry / refused); failed messages land in the `alerts-poison` queue after 5 tries |
| Rotate the token key | re-run step 1's `create` (each deployment draws a new key; phones re-authenticate silently) |
| Accounts say "unavailable" | App Insights: `traces \| where message has "accounts.disabled"` — the reason names the fix (usually the Key Vault role still propagating after a first deploy: restart the app a few minutes later) |
| Stop Ask Rythu now | `az functionapp config appsettings set -g rg-rythu-dev -n <api app> --settings RYTHU_ASSISTANT_ENABLED=false` (the kill switch; the app restarts in seconds and the screen offers the Kisan Call Centre). Make it stick with `-p assistantEnabled=false` on the next `create` |
| Ask Rythu spend | `traces \| extend d = parse_json(message) \| where d.event == "assistant.answered" \| summarize answers = count(), usd = sum(todouble(d.cost_usd)), covered = countif(tobool(d.covered)) by bin(timestamp, 1d)` |
| Ask Rythu off unexpectedly | `traces \| where message has "assistant.disabled"` — the reason names the fix (no secret yet, or the Key Vault role still propagating) |
| Tear down | `az group delete -n rg-rythu-dev` (deletes everything in this runbook). The Key Vault stays soft-deleted for 7 days and keeps its name: `az keyvault purge -n <name>` to recreate sooner |
