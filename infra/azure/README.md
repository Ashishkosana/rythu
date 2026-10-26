# Rythu on Azure — one-time setup runbook

Everything below runs in **Azure Cloud Shell** (portal → `>_` icon → Bash). It has `az`, `git` and `gh`
preinstalled. Commands are copy-paste; replace `<…>` placeholders. Nothing here costs money beyond the
pilot's near-zero usage, and a budget alert emails you at $4 (80 % of $5).

What `main.bicep` creates in one resource group: a Static Web App (Free) for the web app, a Flex
Consumption Function App (Python 3.12, managed identity) for the API, a Key Vault holding the
device-token signing key (generated at deploy time, readable only by the app's identity), a storage account with **shared-key access disabled** (identity-only: no keys exist to leak),
the `forecast` table, Application Insights + Log Analytics with a 0.1 GB/day cap, a budget alert, and a
user-assigned identity that GitHub Actions can log in as via OIDC (no stored secret).

## 0. Pre-flight: can this subscription run it? (2 minutes)

```bash
# Regions your Azure for Students subscription may deploy to (policy):
az policy assignment list --query "[?contains(displayName,'region') || contains(displayName,'location')].parameters" -o json
# Regions that offer Flex Consumption:
az functionapp list-flexconsumption-locations --query "[].name" -o tsv
# Static Web Apps runs its control plane in: eastasia westeurope eastus2 centralus westus2
# Register the resource providers this template uses (safe to re-run):
for p in Microsoft.Web Microsoft.Storage Microsoft.Insights Microsoft.OperationalInsights \
         Microsoft.ManagedIdentity Microsoft.Consumption Microsoft.KeyVault; do az provider register --namespace $p; done
```

Pick a region that appears in **both** lists, preferring `centralindia` or `southindia` (closest to
Telangana). For the web app, pick the first of `eastasia westeurope eastus2 centralus westus2` that your
policy allows (its pages are served from a global edge either way; this only places its control plane). If **no** region is in both, or step 1 fails with "Flex Consumption … not enabled/supported
for this subscription", stop and say so — the fallback is ADR 0001 option 2 (Container Apps); the app code
(plain ASGI) does not change.

## 1. Create the infrastructure (≈ 5 minutes)

```bash
git clone https://github.com/Ashishkosana/rythu && cd rythu
git checkout rearch/s7-onward                # until this work is merged to main
REGION=<region from step 0>
WEB_REGION=<Static Web Apps region from step 0>
RG=rg-rythu-dev
az group create -n $RG -l $REGION

# Preview first — read what it will create:
az deployment group what-if -g $RG -f infra/azure/main.bicep \
  -p location=$REGION webLocation=$WEB_REGION env=dev budgetContactEmail=<your email>

az deployment group create -g $RG -n rythu-dev -f infra/azure/main.bicep \
  -p location=$REGION webLocation=$WEB_REGION env=dev budgetContactEmail=<your email> \
  --query properties.outputs -o jsonc
```

If it fails **only** on the budget (some subscription types don't support Cost Management budgets),
re-run the last command with `deployBudget=false` added and set a spending alert in the portal instead.

## 2. Allow GitHub to deploy code — to these two apps only

```bash
out() { az deployment group show -g $RG -n rythu-dev --query "properties.outputs.$1.value" -o tsv; }
az role assignment create --assignee-object-id "$(out deployPrincipalId)" \
  --assignee-principal-type ServicePrincipal \
  --role "Website Contributor" --scope "$(out functionAppId)"
az role assignment create --assignee-object-id "$(out deployPrincipalId)" \
  --assignee-principal-type ServicePrincipal \
  --role "Contributor" --scope "$(out webAppId)"
```

The deploy identity can push code to the two apps and nothing else: it cannot read data, change other
resources, or grant permissions. Infrastructure changes stay a human step (this runbook). On the Static
Web App it reads the deployment token at deploy time, so no token is ever stored in GitHub.

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
`apps/web/out` to the Static Web App and smoke-tests the page, its CSP and the service worker headers.
Open the `AZURE_STATICWEBAPP_URL` on a phone: that is the app.

## Operating it

| Task | How |
| --- | --- |
| See logs | App Insights → Logs: `traces \| extend d = parse_json(message) \| where d.event == "weather.request"` |
| Errors only | `traces \| extend d = parse_json(message) \| where d.level == "ERROR"` |
| Roll back | Actions → Deploy (Azure) → re-run the last good run (each run deploys one tested commit) |
| Web app headers / CSP | generated per build into `staticwebapp.config.json` (`apps/web/scripts/postbuild.mjs`) |
| Change infra | edit `main.bicep`, run step 1's `what-if`, then `create` again (idempotent) |
| Cost | Portal → Cost Management; the budget emails at 80 % actual / 100 % forecast |
| Rotate the token key | re-run step 1's `create` (each deployment draws a new key; phones re-authenticate silently) |
| Accounts say "unavailable" | App Insights: `traces \| where message has "accounts.disabled"` — the reason names the fix (usually the Key Vault role still propagating after a first deploy: restart the app a few minutes later) |
| Tear down | `az group delete -n rg-rythu-dev` (deletes everything in this runbook). The Key Vault stays soft-deleted for 7 days and keeps its name: `az keyvault purge -n <name>` to recreate sooner |
