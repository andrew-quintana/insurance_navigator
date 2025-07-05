#!/usr/bin/env -S deno run --allow-read --allow-env --allow-net

import { join } from "https://deno.land/std/path/mod.ts";
import { parse } from "https://deno.land/std/dotenv/mod.ts";
import { ENV_TYPES } from "../supabase/functions/_shared/environment.ts";

interface EnvComparison {
  missingInDashboard: string[];
  missingInLocal: string[];
  different: { key: string; local: string; dashboard: string; }[];
}

async function readEnvFile(environment: string): Promise<Record<string, string>> {
  try {
    const envPath = join(Deno.cwd(), `.env.${environment}`);
    const content = await Deno.readTextFile(envPath);
    return parse(content);
  } catch (error) {
    console.error(`Error reading .env.${environment}:`, error);
    return {};
  }
}

async function getDashboardEnvs(projectRef: string, environment: string): Promise<Record<string, string>> {
  // Note: This is a placeholder. In reality, you would:
  // 1. Use Supabase Management API to fetch environment variables
  // 2. Require authentication via SUPABASE_ACCESS_TOKEN
  // 3. Handle pagination and error cases
  
  const response = await fetch(
    `https://api.supabase.com/v1/projects/${projectRef}/config/environments/${environment}`,
    {
      headers: {
        'Authorization': `Bearer ${Deno.env.get('SUPABASE_ACCESS_TOKEN')}`,
      }
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch dashboard envs: ${response.statusText}`);
  }

  return response.json();
}

function compareEnvs(
  local: Record<string, string>,
  dashboard: Record<string, string>
): EnvComparison {
  const result: EnvComparison = {
    missingInDashboard: [],
    missingInLocal: [],
    different: []
  };

  // Check for missing or different values
  for (const [key, localValue] of Object.entries(local)) {
    if (!(key in dashboard)) {
      result.missingInDashboard.push(key);
    } else if (dashboard[key] !== localValue) {
      result.different.push({
        key,
        local: localValue,
        dashboard: dashboard[key]
      });
    }
  }

  // Check for values in dashboard but not in local
  for (const key of Object.keys(dashboard)) {
    if (!(key in local)) {
      result.missingInLocal.push(key);
    }
  }

  return result;
}

async function main() {
  const projectRef = Deno.env.get('SUPABASE_PROJECT_REF');
  if (!projectRef) {
    throw new Error('SUPABASE_PROJECT_REF environment variable is required');
  }

  const accessToken = Deno.env.get('SUPABASE_ACCESS_TOKEN');
  if (!accessToken) {
    throw new Error('SUPABASE_ACCESS_TOKEN environment variable is required');
  }

  for (const environment of ENV_TYPES) {
    console.log(`\nComparing ${environment} environment:`);
    console.log('----------------------------------------');

    const localEnv = await readEnvFile(environment);
    const dashboardEnv = await getDashboardEnvs(projectRef, environment);
    const comparison = compareEnvs(localEnv, dashboardEnv);

    if (comparison.missingInDashboard.length > 0) {
      console.log('\nMissing in Supabase dashboard:');
      comparison.missingInDashboard.forEach(key => console.log(`  - ${key}`));
    }

    if (comparison.missingInLocal.length > 0) {
      console.log('\nMissing in local .env file:');
      comparison.missingInLocal.forEach(key => console.log(`  - ${key}`));
}

    if (comparison.different.length > 0) {
      console.log('\nDifferent values:');
      comparison.different.forEach(({ key }) => 
        console.log(`  - ${key} (values differ)`)
      );
    }

    if (
      comparison.missingInDashboard.length === 0 &&
      comparison.missingInLocal.length === 0 &&
      comparison.different.length === 0
    ) {
      console.log('✓ All environment variables match');
    }
  }
}

if (import.meta.main) {
  main().catch(console.error);
} 