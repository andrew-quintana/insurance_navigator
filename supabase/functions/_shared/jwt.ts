import { create, verify, Payload } from "https://deno.land/x/djwt@v3.0.1/mod.ts";
import { edgeConfig } from "./environment.ts";

export interface JWTPayload extends Payload {
  sub: string;
  role: string;
  exp?: number;
  [key: string]: unknown;
}

function getJwtSecret(): string {
  const secret = Deno.env.get('SUPABASE_JWT_SECRET') || Deno.env.get('JWT_SECRET');
  if (!secret) {
    throw new Error('JWT secret not found in environment');
  }
  const strippedSecret = secret.replace(/^["']|["']$/g, '');
  console.log('JWT Secret:', {
    original: secret,
    stripped: strippedSecret
  });
  return strippedSecret;
}

export async function createServiceRoleJWT(): Promise<string> {
  return await createJWT({
    sub: "service_role",
    role: "service_role",
    exp: Math.floor(Date.now() / 1000) + 3600
  });
}

export async function createUserJWT(userId: string): Promise<string> {
  return await createJWT({
    sub: userId,
    role: "authenticated",
    exp: Math.floor(Date.now() / 1000) + 3600
  });
}

export async function createJWT(payload: JWTPayload): Promise<string> {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(getJwtSecret()),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );

  return await create({ alg: "HS256", typ: "JWT" }, payload, key);
}

export async function verifyJWT(token: string): Promise<JWTPayload> {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(getJwtSecret()),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["verify"]
  );

  const result = await verify(token, key);
  return result[1] as JWTPayload;
} 