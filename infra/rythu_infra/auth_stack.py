"""CDK stack for Rythu email auth (AWS Cognito).

Guest-first: the app works with no account; login only ADDS cross-device sync.
Email + password with an emailed verification code. A public SPA app client (no
secret) is used so the browser can talk to Cognito directly via SRP. A mutable
``custom:place`` attribute is defined up front so the saved village can sync later
without recreating the pool.

DEPLOY: `cd infra && source .venv/bin/activate && AWS_PROFILE=personal cdk deploy RythuAuth`
Verification emails use Cognito's default sender (fine for the pilot's low volume);
switch to SES before real scale.
"""

from __future__ import annotations

from aws_cdk import CfnOutput, RemovalPolicy, Stack
from aws_cdk import aws_cognito as cognito
from constructs import Construct


class AuthStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: object) -> None:
        super().__init__(scope, construct_id, **kwargs)

        pool = cognito.UserPool(
            self,
            "RythuUserPool",
            user_pool_name="rythu-users",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True),
            ),
            # Saved village (lat/lon/place JSON) for cross-device sync — defined now
            # so we never have to recreate the pool to add it.
            custom_attributes={"place": cognito.StringAttribute(mutable=True, max_len=2048)},
            # Farmer-friendly: 8 chars, a letter + a number — no symbol/case gymnastics.
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_digits=True,
                require_uppercase=False,
                require_symbols=False,
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            user_verification=cognito.UserVerificationConfig(
                email_subject="మీ Rythu కోడ్ · Your Rythu code",
                email_body="మీ ధృవీకరణ కోడ్: {####}  ·  Your Rythu verification code is {####}",
                email_style=cognito.VerificationEmailStyle.CODE,
            ),
            removal_policy=RemovalPolicy.DESTROY,  # pilot — recreatable
        )

        # Public SPA client: no secret, SRP auth (amazon-cognito-identity-js).
        client = pool.add_client(
            "RythuWebClient",
            auth_flows=cognito.AuthFlow(user_srp=True),
            prevent_user_existence_errors=True,
            generate_secret=False,
            access_token_validity=None,
        )

        CfnOutput(self, "UserPoolId", value=pool.user_pool_id)
        CfnOutput(self, "UserPoolClientId", value=client.user_pool_client_id)
