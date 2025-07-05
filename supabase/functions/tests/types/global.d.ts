/// <reference no-default-lib="true" />
/// <reference lib="esnext" />
/// <reference lib="dom" />

declare namespace Deno {
  export interface TestContext {
    name: string;
    step(name: string, fn: (t: TestContext) => void | Promise<void>): Promise<void>;
  }

  export function test(
    name: string,
    fn: (t: TestContext) => void | Promise<void>
  ): void;
}

declare module "std/testing/asserts.ts" {
  export function assertEquals(actual: unknown, expected: unknown, msg?: string): void;
  export function assertExists(actual: unknown, msg?: string): void;
  export function assertRejects(
    fn: () => Promise<unknown>,
    ErrorClass?: new (...args: any[]) => Error,
    msgIncludes?: string,
    msg?: string
  ): Promise<void>;
}

declare module "std/testing/types.ts" {
  export interface TestContext {
    name: string;
    step(name: string, fn: (t: TestContext) => void | Promise<void>): Promise<void>;
  }
} 