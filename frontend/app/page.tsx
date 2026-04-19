"use client";

import { useBackendStatus } from "@/features/health/hooks";

export default function Home() {
  const { loading, healthStatus, helloMessage, error } = useBackendStatus();

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-3xl flex-col justify-center gap-6 px-6 py-12">
      <h1 className="text-3xl font-semibold">PuebloLindo Frontend</h1>
      <p className="text-sm text-gray-600">
        Verificacion de integracion con backend FastAPI usando contrato OpenAPI.
      </p>

      <section className="rounded-lg border border-gray-200 p-5">
        {loading && <p>Consultando backend...</p>}

        {!loading && error && <p className="text-red-600">Error: {error}</p>}

        {!loading && !error && (
          <div className="space-y-2">
            <p>
              <strong>GET /health:</strong> {healthStatus}
            </p>
            <p>
              <strong>GET /:</strong> {helloMessage}
            </p>
          </div>
        )}
      </section>
    </main>
  );
}
