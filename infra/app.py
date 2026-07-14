#!/usr/bin/env python3
"""CDK app entrypoint for Rythu infrastructure."""

from __future__ import annotations

import aws_cdk as cdk

from rythu_infra.weather_stack import WeatherStack

app = cdk.App()
WeatherStack(
    app,
    "RythuWeather",
    # Mumbai — the AWS region closest to Telangana. Account is resolved at deploy time.
    env=cdk.Environment(region="ap-south-1"),
    description="Rythu weather slice: Open-Meteo proxy + farming-read on Lambda + DynamoDB cache",
)
app.synth()
