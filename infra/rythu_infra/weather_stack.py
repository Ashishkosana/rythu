"""CDK stack for the Rythu weather slice.

  API Gateway (HTTP API)  ──GET /weather──▶  Lambda (rythu_weather.app.handler)
                                                   │
                                                   ▼
                                       DynamoDB (forecast cache, TTL)

DEPLOY NOTE: the Lambda asset is the pure service source only; the httpx dependency is not
bundled here. Before `cdk deploy`, add it via a Lambda layer or switch to a bundling
construct (e.g. aws-lambda-python-alpha PythonFunction). `cdk synth` works as-is.
"""

from __future__ import annotations

from pathlib import Path

from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
)
from aws_cdk import (
    aws_apigatewayv2 as apigwv2,
)
from aws_cdk import (
    aws_apigatewayv2_integrations as integrations,
)
from aws_cdk import (
    aws_dynamodb as dynamodb,
)
from aws_cdk import (
    aws_lambda as lambda_,
)
from constructs import Construct

# repo-root/services/weather/src → the folder whose top level is the `rythu_weather` package
SERVICE_SRC = Path(__file__).resolve().parents[2] / "services" / "weather" / "src"


class WeatherStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: object) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cache = dynamodb.Table(
            self,
            "ForecastCache",
            partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,  # free-tier friendly
            time_to_live_attribute="ttl",  # auto-expire stale forecasts
            removal_policy=RemovalPolicy.DESTROY,  # dev/pilot — cache is disposable
        )

        weather_fn = lambda_.Function(
            self,
            "WeatherFn",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="rythu_weather.app.handler.handler",
            code=lambda_.Code.from_asset(str(SERVICE_SRC)),
            timeout=Duration.seconds(15),
            memory_size=256,
            environment={"RYTHU_CACHE_TABLE": cache.table_name},
        )
        cache.grant_read_write_data(weather_fn)

        api = apigwv2.HttpApi(self, "WeatherApi", api_name="rythu-weather")
        api.add_routes(
            path="/weather",
            methods=[apigwv2.HttpMethod.GET],
            integration=integrations.HttpLambdaIntegration("WeatherIntegration", weather_fn),
        )

        CfnOutput(self, "ApiUrl", value=api.api_endpoint)
        CfnOutput(self, "CacheTable", value=cache.table_name)
