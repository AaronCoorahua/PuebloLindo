"use client";

import { ArrowUpRight, MessageSquare, RefreshCcw, UserRoundCheck, X } from "lucide-react";
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

function getTicketTitle(ticket: Ticket): string {
  const apiTitle = ticket.title?.trim();
  if (apiTitle) {
    return apiTitle;
  }
  return getMotivo(ticket.summary);
}

function getSummaryPreview(summary: string): string {
  const cleaned = summary.trim();
  if (!cleaned) {
    return "Sin resumen disponible";
  }
  return cleaned.split("|")[0]?.trim() || cleaned;
}

export default function HomePage() {
  const { loading, error, tickets, total, reload } = useTickets("open");

  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);
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

  const selectedTicket = useMemo(
    () => tickets.find((ticket) => ticket.id === selectedTicketId) ?? null,
    [selectedTicketId, tickets]
  );

  function openTicketPanel(ticket: Ticket) {
    setSelectedTicketId(ticket.id);
    setActionError(undefined);
  }

  function closeTicketPanel() {
    setSelectedTicketId(null);
    setActionError(undefined);
  }

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

      setSelectedTicketId(null);
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
                <CardContent className="pt-5">
                  {areaTickets.length === 0 && (
                    <div className="rounded-lg border border-dashed border-[var(--sand-400)] bg-white p-4 text-sm text-[var(--ink-500)]">
                      Todo al dia en {AREA_LABELS[area]}.
                    </div>
                  )}

                  {areaTickets.length > 0 && (
                    <div className="max-h-[460px] space-y-3 overflow-y-auto pr-1">
                      {areaTickets.map((ticket) => {
                        const ticketTitle = getTicketTitle(ticket);
                        const isSelected = selectedTicketId === ticket.id;

                        return (
                          <button
                            key={ticket.id}
                            type="button"
                            onClick={() => openTicketPanel(ticket)}
                            className={`w-full rounded-md border bg-white p-3 text-left shadow-[0_2px_8px_rgba(42,10,102,0.08)] transition hover:-translate-y-[1px] hover:shadow-[0_4px_12px_rgba(42,10,102,0.12)] ${
                              isSelected ? "border-[var(--brand-600)]" : "border-[#ddd9eb]"
                            }`}
                          >
                            <div className="mb-2 flex items-center justify-between gap-2">
                              <Badge variant="outline">#{ticket.id.slice(0, 8)}</Badge>
                              <span className="text-xs text-[var(--ink-500)]">
                                {new Date(ticket.updated_at).toLocaleString("es-PE")}
                              </span>
                            </div>
                            <p className="line-clamp-2 text-base font-semibold text-[var(--brand-700)]">{ticketTitle}</p>
                            <div className="mt-3 h-[3px] rounded-full bg-[var(--accent-500)]/75" />
                          </button>
                        );
                      })}
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </section>
      )}

      {selectedTicket && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/35 backdrop-blur-[1px]">
          <section className="h-full w-full max-w-xl overflow-y-auto border-l border-[var(--sand-300)] bg-white p-5 shadow-2xl md:p-6">
            <div className="mb-4 flex items-start justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.14em] text-[var(--ink-500)]">Detalle de ticket</p>
                <h3 className="mt-1 text-xl font-bold text-[var(--brand-700)]">{getTicketTitle(selectedTicket)}</h3>
              </div>
              <button
                type="button"
                className="rounded-md border border-[var(--sand-300)] p-2 text-[var(--ink-700)] hover:bg-[var(--sand-200)]"
                onClick={closeTicketPanel}
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2 rounded-lg border border-[var(--sand-300)] bg-[var(--sand-200)] p-3 text-sm">
              <p>
                <strong>ID:</strong> {selectedTicket.id}
              </p>
              <p>
                <strong>Area:</strong> {selectedTicket.area}
              </p>
              <p className="col-span-2">
                <strong>Actualizado:</strong> {new Date(selectedTicket.updated_at).toLocaleString("es-PE")}
              </p>
            </div>

            <div className="mt-4 rounded-lg border border-[var(--sand-300)] bg-white p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--ink-500)]">Resumen</p>
              <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-[var(--ink-800)]">
                {getSummaryPreview(selectedTicket.summary)}
              </p>
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              <a
                href={selectedTicket.wa_link}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 rounded-md border border-[var(--accent-500)]/50 bg-[#fff8f4] px-3 py-2 text-sm font-medium text-[var(--accent-500)] hover:bg-[#ffece2]"
              >
                <MessageSquare className="h-4 w-4" />
                Conversacion
                <ArrowUpRight className="h-4 w-4" />
              </a>
            </div>

            <div className="mt-5 space-y-2 rounded-lg border border-[var(--sand-300)] bg-white p-4">
              <p className="text-sm font-semibold text-[var(--ink-800)]">Cerrar ticket</p>

              <label className="block text-xs font-medium text-[var(--ink-700)]">Atendedor</label>
              <Input
                value={atendedor}
                onChange={(event) => setAtendedor(event.target.value)}
                placeholder="Ej: Aaron Coorahua"
              />

              <label className="block text-xs font-medium text-[var(--ink-700)]">Mensaje de cierre</label>
              <Textarea
                value={mensajeCierre}
                onChange={(event) => setMensajeCierre(event.target.value)}
                placeholder="Detalle final para el usuario"
              />

              <Button className="w-full" onClick={() => handleCloseTicket(selectedTicket)} disabled={isSubmitting}>
                <UserRoundCheck className="h-4 w-4" />
                {isSubmitting ? "Procesando..." : "Cerrar y notificar"}
              </Button>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
