"use client";

import { ArrowUpRight, CircleSlash, MessageSquare, RefreshCcw, UserRoundCheck } from "lucide-react";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { closeTicket } from "@/features/tickets/api";
import { useTickets } from "@/features/tickets/hooks";
import type { Ticket } from "@/features/tickets/types";

const AREA_ORDER = ["soporte_tecnico", "pagos", "envios", "reclamos", "ventas", "otros"] as const;

const AREA_LABELS: Record<string, string> = {
  soporte_tecnico: "SOPORTE TECNICO",
  pagos: "PAGOS",
  envios: "ENVIOS",
  reclamos: "RECLAMOS",
  ventas: "VENTAS",
  otros: "OTROS",
};

function getMotivo(summary: string): string {
  const cleaned = summary.trim();
  if (!cleaned) {
    return "Sin detalle";
  }
  const firstChunk = cleaned.split("|")[0]?.trim() || cleaned;
  return firstChunk.replace(/^cliente reporta:\s*/i, "");
}

export default function HomePage() {
  const { loading, error, tickets, total, reload } = useTickets("open");

  const [expandedTicketId, setExpandedTicketId] = useState<string | null>(null);
  const [atendedor, setAtendedor] = useState("");
  const [mensajeCierre, setMensajeCierre] = useState("");
  const [actionError, setActionError] = useState<string | undefined>();
  const [actionMessage, setActionMessage] = useState<string | undefined>();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const groupedTickets = useMemo(() => {
    const groups: Record<string, Ticket[]> = {
      soporte_tecnico: [],
      pagos: [],
      envios: [],
      reclamos: [],
      ventas: [],
      otros: [],
    };

    for (const ticket of tickets) {
      const areaKey = AREA_ORDER.includes(ticket.area as (typeof AREA_ORDER)[number]) ? ticket.area : "otros";
      groups[areaKey].push(ticket);
    }

    return groups;
  }, [tickets]);

  async function handleCloseTicket(ticket: Ticket) {
    setActionError(undefined);
    setActionMessage(undefined);

    if (!atendedor.trim() || !mensajeCierre.trim()) {
      setActionError("Completa atendedor y mensaje de cierre antes de cerrar el ticket.");
      return;
    }

    try {
      setIsSubmitting(true);
      const response = await closeTicket(ticket.id, {
        atendedor: atendedor.trim(),
        mensaje_cierre: mensajeCierre.trim(),
      });

      if (response.notification_sent) {
        setActionMessage(`Ticket ${ticket.id} cerrado y notificado al usuario.`);
      } else {
        setActionMessage(`Ticket ${ticket.id} cerrado, pero no se pudo notificar al usuario.`);
      }

      setExpandedTicketId(null);
      setAtendedor("");
      setMensajeCierre("");
      await reload();
    } catch (submitError) {
      setActionError(submitError instanceof Error ? submitError.message : "No se pudo cerrar el ticket.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-[var(--sand-300)] bg-white p-5 shadow-sm md:p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-2xl text-[var(--brand-700)] md:text-3xl">Gestion Operativa</h2>
            <p className="mt-2 text-sm text-[var(--ink-600)]">
              Vista kanban por area para priorizar y cerrar casos con notificacion al cliente.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="secondary">{total} abiertos</Badge>
            <Button variant="outline" onClick={reload}>
              <RefreshCcw className="h-4 w-4" />
              Recargar
            </Button>
          </div>
        </div>
        {actionMessage && <p className="mt-4 rounded-md bg-[var(--brand-100)] px-3 py-2 text-sm text-[var(--brand-800)]">{actionMessage}</p>}
        {actionError && <p className="mt-4 rounded-md bg-[#fbe4e4] px-3 py-2 text-sm text-[#8d2828]">{actionError}</p>}
      </section>

      {loading && (
        <Card>
          <CardContent className="pt-5">
            <p className="text-sm text-[var(--ink-600)]">Cargando tickets abiertos...</p>
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

      {!loading && !error && (
        <section className="grid gap-4 xl:grid-cols-3">
          {AREA_ORDER.map((area) => {
            const areaTickets = groupedTickets[area];

            return (
              <Card key={area} className="flex h-full flex-col border-[var(--sand-400)] bg-transparent shadow-none">
                <CardHeader className="border-b border-[var(--sand-300)] bg-[#f6f7fc]">
                  <div className="flex items-center justify-between gap-2">
                    <CardTitle className="text-xs font-bold tracking-[0.12em] text-[var(--brand-700)]">{AREA_LABELS[area]}</CardTitle>
                    <Badge variant="outline">{areaTickets.length}</Badge>
                  </div>
                  <CardDescription>{areaTickets.length === 1 ? "1 Ticket" : `${areaTickets.length} Tickets`}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 pt-5">
                  {areaTickets.length === 0 && (
                    <div className="rounded-lg border border-dashed border-[var(--sand-400)] bg-white p-4 text-sm text-[var(--ink-500)]">
                      Todo al dia en {AREA_LABELS[area]}.
                    </div>
                  )}

                  {areaTickets.map((ticket) => {
                    const expanded = expandedTicketId === ticket.id;
                    const ticketMotivo = getMotivo(ticket.summary);

                    return (
                      <article
                        key={ticket.id}
                        className="rounded-md border border-[#ddd9eb] bg-white p-3 shadow-[0_2px_8px_rgba(42,10,102,0.08)]"
                      >
                        <div className="mb-2 flex items-center justify-between gap-2">
                          <Badge variant="outline">#{ticket.id.slice(0, 8)}</Badge>
                          <span className="text-xs text-[var(--ink-500)]">
                            {new Date(ticket.updated_at).toLocaleString("es-PE")}
                          </span>
                        </div>

                        <div className="space-y-2 text-sm">
                          <p className="line-clamp-2 text-base font-semibold text-[var(--brand-700)]">
                            {ticketMotivo}
                          </p>
                          <p className="text-sm text-[var(--ink-700)]">
                            <strong className="text-[var(--ink-800)]">Resumen:</strong> {ticket.summary}
                          </p>
                        </div>

                        <div className="mt-3 flex flex-wrap gap-2">
                          <a
                            href={ticket.wa_link}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 rounded-md border border-[var(--accent-500)]/50 bg-[#fff8f4] px-3 py-1.5 text-xs font-medium text-[var(--accent-500)] hover:bg-[#ffece2]"
                          >
                            <MessageSquare className="h-3.5 w-3.5" />
                            Conversacion
                            <ArrowUpRight className="h-3.5 w-3.5" />
                          </a>

                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => {
                              setExpandedTicketId(expanded ? null : ticket.id);
                              setActionError(undefined);
                            }}
                          >
                            <CircleSlash className="h-4 w-4" />
                            Cerrar ticket
                          </Button>
                        </div>

                        {expanded && (
                          <div className="mt-3 space-y-2 rounded-md border border-[var(--sand-300)] bg-white p-3">
                            <label className="block text-xs font-medium text-[var(--ink-700)]">Atendedor</label>
                            <Input
                              value={atendedor}
                              onChange={(event) => setAtendedor(event.target.value)}
                              placeholder="Ej: Aaron Coorahua"
                            />

                            <label className="block text-xs font-medium text-[var(--ink-700)]">mensaje_cierre</label>
                            <Textarea
                              value={mensajeCierre}
                              onChange={(event) => setMensajeCierre(event.target.value)}
                              placeholder="Detalle final para el usuario"
                            />

                            <Button
                              className="w-full"
                              onClick={() => handleCloseTicket(ticket)}
                              disabled={isSubmitting}
                            >
                              <UserRoundCheck className="h-4 w-4" />
                              {isSubmitting ? "Cerrando..." : "Confirmar cierre"}
                            </Button>
                          </div>
                        )}

                        <div className="mt-3 h-[3px] rounded-full bg-[var(--accent-500)]/75" />
                      </article>
                    );
                  })}
                </CardContent>
              </Card>
            );
          })}
        </section>
      )}
    </div>
  );
}
