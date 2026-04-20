"use client";

import { ArrowUpRight, FileClock, RefreshCcw } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useTickets } from "@/features/tickets/hooks";

function formatDate(value: string): string {
  return new Date(value).toLocaleString("es-PE", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export default function HistoryPage() {
  const { loading, error, tickets, total, reload } = useTickets("closed");

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-[var(--sand-300)] bg-white/90 p-5 shadow-sm md:p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-2xl text-[var(--brand-700)] md:text-3xl">Auditoria de tickets cerrados</h2>
            <p className="mt-2 text-sm text-[var(--ink-600)]">
              Historial de cierre con trazabilidad por ticket y acceso directo a la conversacion.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="secondary">{total} cerrados</Badge>
            <Button variant="outline" onClick={reload}>
              <RefreshCcw className="h-4 w-4" />
              Recargar
            </Button>
          </div>
        </div>
      </section>

      {loading && (
        <Card>
          <CardContent className="pt-5">
            <p className="text-sm text-[var(--ink-600)]">Cargando historial...</p>
          </CardContent>
        </Card>
      )}

      {!loading && error && (
        <Card>
          <CardContent className="pt-5">
            <p className="text-sm text-[#8d2828]">{error}</p>
          </CardContent>
        </Card>
      )}

      {!loading && !error && tickets.length === 0 && (
        <Card>
          <CardContent className="pt-5">
            <p className="text-sm text-[var(--ink-600)]">Aun no hay tickets cerrados para mostrar.</p>
          </CardContent>
        </Card>
      )}

      {!loading && !error && tickets.length > 0 && (
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {tickets.map((ticket) => (
            <Card key={ticket.id} className="h-full">
              <CardHeader>
                <div className="flex items-center justify-between gap-2">
                  <CardTitle className="text-lg">{ticket.title?.trim() || ticket.area}</CardTitle>
                  <Badge>{ticket.status}</Badge>
                </div>
                <CardDescription>Ticket ID: {ticket.id}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm text-[var(--ink-700)]">
                  <strong>Cerrado por:</strong> {ticket.closed_by?.trim() || "Sin registrar"}
                </p>
                <p className="text-sm text-[var(--ink-700)]">
                  <strong>Mensaje de cierre:</strong> {ticket.closed_message?.trim() || "Sin registrar"}
                </p>
                <p className="text-sm text-[var(--ink-700)]">
                  <strong>Resumen:</strong> {ticket.summary}
                </p>
                <p className="flex items-center gap-2 text-xs text-[var(--ink-500)]">
                  <FileClock className="h-4 w-4" />
                  Cerrado/actualizado: {formatDate(ticket.updated_at)}
                </p>

                <a
                  href={ticket.wa_link}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 rounded-md border border-[var(--sand-400)] bg-[var(--sand-100)] px-3 py-1.5 text-xs font-medium text-[var(--ink-800)] hover:bg-[var(--sand-200)]"
                >
                  Ver conversacion
                  <ArrowUpRight className="h-3.5 w-3.5" />
                </a>
              </CardContent>
            </Card>
          ))}
        </section>
      )}
    </div>
  );
}
