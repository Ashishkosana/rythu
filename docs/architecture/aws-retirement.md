# Retiring AWS (S10)

**Status (2026-10-27):** nothing in Rythu uses AWS any more. The web app is a static export on Azure
Static Web Apps calling the Azure Functions API; the AWS Amplify front end is offline; Cognito was
removed from the code in S13. What may still exist is whatever was deployed to the AWS account earlier
— and it may still cost money. This page is the checklist to find it and delete it.

**Every delete below is permanent and is yours to run** (AWS CloudShell, region `ap-south-1` unless a
step says otherwise). Nothing here has been run on your account.

**Why no 7-day dual run** (planned in S10): a dual run protects live users while traffic moves. No
farmer traffic reaches AWS — Amplify is offline and no client calls API Gateway — so there is nothing
to compare against. Step 2 checks that claim with AWS's own metrics before anything is deleted.

## 1. Inventory (read-only)

```bash
export AWS_REGION=ap-south-1
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE UPDATE_ROLLBACK_COMPLETE \
  --query "StackSummaries[].StackName"            # expect RythuWeather, maybe RythuAuth, CDKToolkit
aws lambda list-functions --query "Functions[].FunctionName"
aws dynamodb list-tables
aws apigatewayv2 get-apis --query "Items[].[Name,ApiId,ApiEndpoint]"
aws cognito-idp list-user-pools --max-results 20 --query "UserPools[].[Name,Id]"
aws logs describe-log-groups --query "logGroups[?contains(logGroupName, 'Rythu')].logGroupName"
for r in ap-south-1 us-east-1 eu-west-1; do echo "$r:"; aws amplify list-apps --region $r --query "apps[].[name,appId]"; done
aws ce get-cost-and-usage --time-period Start=2026-08-01,End=2026-10-27 --granularity MONTHLY \
  --metrics UnblendedCost --group-by Type=DIMENSION,Key=SERVICE   # what it has been costing
```

## 2. Confirm nothing uses it

```bash
API_ID=<ApiId from step 1>
aws cloudwatch get-metric-statistics --namespace AWS/ApiGateway --metric-name Count \
  --dimensions Name=ApiId,Value=$API_ID --start-time "$(date -u -d '14 days ago' +%FT%TZ)" \
  --end-time "$(date -u +%FT%TZ)" --period 86400 --statistics Sum --query "Datapoints[].[Timestamp,Sum]"
```

All zero (or empty) → safe. Anything else: something still calls the old API — find it before deleting.

## 3. Delete (each line: your explicit OK first)

| What | Command | Note |
| --- | --- | --- |
| Weather stack: API Gateway, Lambda, DynamoDB cache, its IAM role | `cd infra && cdk destroy RythuWeather` (or `aws cloudformation delete-stack --stack-name RythuWeather`) | The cache table has `RemovalPolicy.DESTROY` — it is disposable |
| Old auth stack, if listed | `aws cloudformation delete-stack --stack-name RythuAuth` | If the user pool survives the stack (a retain policy), `aws cognito-idp delete-user-pool --user-pool-id <id>` |
| Amplify app | `aws amplify delete-app --app-id <appId> --region <its region>` | Also removes its hosting and build history |
| Lambda log groups | `aws logs delete-log-group --log-group-name <name>` for each from step 1 | CloudFormation leaves auto-created log groups behind |
| CDK bootstrap (`CDKToolkit`) | empty `cdk-hnb659fds-assets-<account>-ap-south-1`, then `aws cloudformation delete-stack --stack-name CDKToolkit` | Only if nothing else in the account uses CDK |

Then check Billing the next day: AWS should read $0 for Rythu. Remove any AWS budget or alarm that was
only for Rythu.

## 4. Remove the AWS code (a commit, after step 3)

Once the stacks are gone, the AWS path is dead code and the repo should say so. One commit removes:
`infra/app.py`, `infra/rythu_infra/`, `infra/cdk.json`, `infra/pyproject.toml`, `infra/build_lambda.sh`;
the Lambda handler (`services/weather/src/rythu_weather/app/handler.py`), `DynamoDbCacheStore` (in
`adapters/cache.py`) and their tests (including the "Lambda path stays lean" guards, which then have nothing to guard); the boto3
mypy override; and the AWS sections of the READMEs — the root README's architecture section moves to
Azure. Ask for it once step 3 is done.
