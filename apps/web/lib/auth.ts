// Email auth via AWS Cognito (client-side, SRP). Guest-first: the app works with
// no account; these functions are only used from the Account screen. Wraps the
// callback-style SDK in promises. The pure validators are unit-tested; the network
// calls are not (they need a live pool).
//
// Pool IDs come from NEXT_PUBLIC_ env vars — Next inlines them into the client
// bundle at build. Until they're set (before the Cognito stack is deployed),
// authConfigured() is false and the UI shows a graceful "coming soon" state.

import {
  CognitoUser,
  CognitoUserAttribute,
  CognitoUserPool,
  AuthenticationDetails,
} from "amazon-cognito-identity-js";

const POOL_ID = process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID;
const CLIENT_ID = process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID;

export function authConfigured(): boolean {
  return Boolean(POOL_ID && CLIENT_ID);
}

function getPool(): CognitoUserPool {
  if (!POOL_ID || !CLIENT_ID) throw new Error("Auth not configured");
  return new CognitoUserPool({ UserPoolId: POOL_ID, ClientId: CLIENT_ID });
}

// ── Pure validators (tested) ──────────────────────────────────────────────
export function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
}

/** Matches the Cognito pool policy: ≥8 chars, a lowercase letter, and a digit. */
export function passwordProblem(pw: string): string | null {
  if (pw.length < 8) return "కనీసం 8 అక్షరాలు · At least 8 characters";
  if (!/[a-z]/.test(pw)) return "ఒక చిన్న అక్షరం (a-z) · One lowercase letter";
  if (!/[0-9]/.test(pw)) return "ఒక సంఖ్య (0-9) · One number";
  return null;
}

/** Turn Cognito's error codes into short, friendly Telugu+English text. */
export function friendlyError(err: unknown): string {
  const name = (err as { name?: string; code?: string })?.name || (err as { code?: string })?.code || "";
  switch (name) {
    case "UsernameExistsException":
      return "ఈ ఇమెయిల్ ఇప్పటికే ఉంది · Email already registered";
    case "NotAuthorizedException":
      return "ఇమెయిల్ లేదా పాస్‌వర్డ్ తప్పు · Wrong email or password";
    case "UserNotConfirmedException":
      return "ముందుగా ఇమెయిల్ ధృవీకరించండి · Please verify your email first";
    case "CodeMismatchException":
      return "కోడ్ తప్పు · Wrong code";
    case "ExpiredCodeException":
      return "కోడ్ గడువు ముగిసింది · Code expired";
    case "UserNotFoundException":
      return "ఖాతా కనబడలేదు · Account not found";
    default:
      return (err as { message?: string })?.message || "ఏదో తప్పు జరిగింది · Something went wrong";
  }
}

// ── Cognito flows (promisified) ───────────────────────────────────────────
export function signUp(email: string, password: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const attrs = [new CognitoUserAttribute({ Name: "email", Value: email.trim() })];
    getPool().signUp(email.trim(), password, attrs, [], (err) => (err ? reject(err) : resolve()));
  });
}

export function confirm(email: string, code: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const user = new CognitoUser({ Username: email.trim(), Pool: getPool() });
    user.confirmRegistration(code.trim(), true, (err) => (err ? reject(err) : resolve()));
  });
}

export function resendCode(email: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const user = new CognitoUser({ Username: email.trim(), Pool: getPool() });
    user.resendConfirmationCode((err) => (err ? reject(err) : resolve()));
  });
}

export function signIn(email: string, password: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const user = new CognitoUser({ Username: email.trim(), Pool: getPool() });
    const details = new AuthenticationDetails({ Username: email.trim(), Password: password });
    user.authenticateUser(details, {
      onSuccess: () => resolve(),
      onFailure: (err) => reject(err),
    });
  });
}

export function signOut(): void {
  if (!authConfigured()) return;
  getPool().getCurrentUser()?.signOut();
}

/** Resolve the signed-in user's email, or null if not signed in. */
export function currentEmail(): Promise<string | null> {
  return new Promise((resolve) => {
    if (!authConfigured()) return resolve(null);
    const user = getPool().getCurrentUser();
    if (!user) return resolve(null);
    user.getSession((err: Error | null, session: { isValid: () => boolean } | null) => {
      if (err || !session || !session.isValid()) return resolve(null);
      user.getUserAttributes((aErr, attrs) => {
        if (aErr || !attrs) return resolve(user.getUsername());
        const email = attrs.find((a) => a.getName() === "email")?.getValue();
        resolve(email || user.getUsername());
      });
    });
  });
}
