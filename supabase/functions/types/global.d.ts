/// <reference no-default-lib="true" />
/// <reference lib="deno.window" />
/// <reference lib="dom" />

interface Performance {
  memory?: {
    usedJSHeapSize: number;
    totalJSHeapSize: number;
    jsHeapSizeLimit: number;
  };
} 