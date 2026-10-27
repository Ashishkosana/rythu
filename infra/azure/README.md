# Rythu on Azure — one-time setup runbook

Everything below runs in **Azure Cloud Shell** (portal → `>_` icon → Bash). It has `az`, `git` and `gh`
preinstalled. Commands are copy-paste; replace `<…>` placeholders. Nothing here costs money beyond the
pilot's near-zero usage, and a budget alert emails you at $4 (80 % of $5).

What `main.bicep` creates in one resource group: a Flex Consumption Function App (Python 3.12, managed
identity), a storage account with **shared-key access disabled** (identity-only: no keys exist to leak),
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
         Microsoft.ManagedIdentity Microsoft.Consumption; do az provider register --namespace $p; done
```

Pick a region that appears in **both** lists, preferring `centralindia` or `southindia` (closest to
Telangana). If **no** region is in both, or step 1 fails with "Flex Consumption … not enabled/supported
for this subscription", stop and say so — the fallback is ADR 0001 option 2 (Container Apps); the app code
(plain ASGI) does not change.

## 1. Create the infrastructure (≈ 5 minutes)

```bash
git clone https://github.com/Ashishkosana/rythu && cd rythu
git checkout rearch/s6-azure-foundation      # until this work is merged to main
REGION=<region from step 0>
RG=rg-rythu-dev
az group create -n $RG -l $REGION

# Preview first — read what it will create:
az deployment group what-if -g $RG -f infra/azure/main.bicep \
  -p location=$REGION env=dev budgetContactEmail=<your email>

az deployment group create -g $RG -n rythu-dev -f infra/azure/main.bicep \
  -p location=$REGION env=dev budgetContactEmail=<your email> \
  --query properties.outputs -o jsonc
```

If it fails **only** on the budget (some subscription types don't support Cost Management budgets),
re-run the last command with `deployBudget=false` added and set a spending alert in the portal instead.

## 2. Allow GitHub to deploy code — to this Function App only

```bash
out() { az deployment group show -g $RG -n rythu-dev --query "properties.outputs.$1.value" -o tsv; }
az role assignment create --assignee-object-id "$(out deployPrincipalId)" \
  --assignee-principal-type ServicePrincipal \
  --role "Website Contributor" --scope "$(out functionAppId)"
```

The deploy identity can push code to the app and nothing else: it cannot read data, change other
resources, or grant permissions. Infrastructure changes stay a human step (this runbook).

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
```

(Without `gh`: GitHub → repo → Settings → Environments → New `dev`; Settings → Secrets and variables →
Actions → **Variables** tab → add the five names with the values printed by step 1.)

## 4. Deploy

`.github/workflows/deploy-azure.yml` deploys automatically **after CI passes on `main`**, and can be run by
hand from the Actions tab. GitHub only runs these triggers from workflow files on the default branch, so
the first deploy happens once this work is merged to `main`. The workflow packages
`services/weather` (`scripts/package_functions.sh`), logs in with OIDC, deploys with a remote build, then
smoke-tests `/healthz`, `/v1/weather` and the coverage 400 against the live URL.

## Operating it

| Task | How |
| --- | --- |
| See logs | App Insights → Logs: `traces \| extend d = parse_json(message) \| where d.event == "weather.request"` |
| Errors only | `traces \| extend d = parse_json(message) \| where d.level == "ERROR"` |
| Roll back | Actions → Deploy (Azure) → re-run the last good run (each run deploys one tested commit) |
| Change infra | edit `main.bicep`, run step 1's `what-if`, then `create` again (idempotent) |
| Cost | Portal → Cost Management; the budget emails at 80 % actual / 100 % forecast |
| Tear down | `az group delete -n rg-rythu-dev` (deletes everything in this runbook) |
