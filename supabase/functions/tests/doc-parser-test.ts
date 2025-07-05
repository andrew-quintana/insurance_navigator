/// <reference lib="deno.ns" />
import { assertEquals } from "https://deno.land/std@0.208.0/testing/asserts.ts";

Deno.test("doc-parser endpoint test", async () => {
  const response = await fetch("http://127.0.0.1:54321/functions/v1/doc-parser", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      documentId: "test-doc-1",
      storagePath: "test/sample.pdf"
    })
  });

  console.log("Response status:", response.status);
  const data = await response.text();
  console.log("Response body:", data);
}); 