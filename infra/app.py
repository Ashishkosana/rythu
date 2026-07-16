#!/usr/bin/env python3
"""CDK app entrypoint for Rythu infrastructure."""

from __future__ import annotations

import aws_cdk as cdk

from rythu_infra.auth_stack import AuthStack
from rythu_infra.weather_stack import WeatherStack

app = cdk.App()

MUMBAI = cdk.Environment(region="ap-south-1")  # closest AWS region to Telangana

WeatherStack(
    app,
    "RythuWeather",
    env=MUMBAI,
    description="Rythu weather slice: Open-Meteo proxy + farming-read on Lambda + DynamoDB cache",
)
AuthStack(
    app,
    "RythuAuth",
    env=MUMBAI,
    description="Rythu email auth: Cognito user pool (guest-first, optional login)",
)
app.synth()
