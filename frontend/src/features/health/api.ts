import type { components, operations } from "@/lib/api/generated";
import { getJson } from "@/lib/api/client";

export type HealthResponse = components["schemas"]["HealthResponse"];
export type HelloResponse =
  operations["root__get"]["responses"][200]["content"]["application/json"];

export function fetchHealth(): Promise<HealthResponse> {
  return getJson<HealthResponse>("/health");
}

export function fetchHello(): Promise<HelloResponse> {
  return getJson<HelloResponse>("/");
}
