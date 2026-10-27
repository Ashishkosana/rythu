#!/usr/bin/env python3
"""CDK app entrypoint for Rythu infrastructure."""

from __future__ import annotations

import aws_cdk as cdk

from rythu_infra.weather_stack import WeatherStack

app = cdk.App()

MUMBAI = cdk.Environment(region="ap-south-1")  # closest AWS region to Telangana

WeatherStack(
    app,
    "RythuWeather",
    env=MUMBAI,
    description="Rythu weather slice: Open-Meteo proxy + farming-read on Lambda + DynamoDB cache",
)
# The Cognito AuthStack ("RythuAuth") was removed in S13: device accounts on Azure replace it
# (docs/architecture/adr/0004). A pool deployed earlier is not touched by removing it here; it is
# deleted with the rest of AWS in S10 (`cdk destroy`, with explicit approval).
app.synth()
