"use client";

import { BarChart3, Layers3, RefreshCcw, TicketCheck, TicketX } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchAllTickets, fetchTickets } from "@/features/tickets/api";
import type { Ticket } from "@/features/tickets/types";

type ReportsState = {
  loading: boolean;
  error?: string;
  openTotal: number;
  closedTotal: number;
  allTickets: Ticket[];
};

function buildAreaCounts(items: Ticket[]): Array<{ area: string; count: number }> {
  const counts = new Map<string, number>();

  for (const ticket of items) {
    const key = ticket.area?.trim() || "otros";
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }

  return Array.from(counts.entries())
    .map(([area, count]) => ({ area, count }))
    .sort((a, b) => b.count - a.count || a.area.localeCompare(b.area));
}

export default function ReportsPage() {
  const [state, setState] = useState<ReportsState>({
    loading: true,
    openTotal: 0,
    closedTotal: 0,
    allTickets: [],
  });

  const fetchReportData = useCallback(async () => {
    const [openResponse, closedResponse, allResponse] = await Promise.all([
      fetchTickets("open", 1, 0),
      fetchTickets("closed", 1, 0),
      fetchAllTickets(undefined),
    ]);
    return {
      openTotal: openResponse.total,
      closedTotal: closedResponse.total,
      allTickets: allResponse.items,
    };
  }, []);

  const loadReports = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: undefined }));

    try {
      const data = await fetchReportData();
      setState({ loading: false, ...data });
    } catch (error) {
      setState({
        loading: false,
        openTotal: 0,
        closedTotal: 0,
        allTickets: [],
        error: error instanceof Error ? error.message : "No se pudieron cargar los reportes",
      });
    }
  }, [fetchReportData]);

  useEffect(() => {
    let isCancelled = false;

    async function initialLoad() {
      try {
        const data = await fetchReportData();
        if (isCancelled) {
          return;
        }
        setState({ loading: false, ...data });
      } catch (error) {
        if (isCancelled) {
          return;
        }
        setState({
          loading: false,
          openTotal: 0,
          closedTotal: 0,
          allTickets: [],
          error: error instanceof Error ? error.message : "No se pudieron cargar los reportes",
        });
      }
    }

    void initialLoad();

    return () => {
      isCancelled = true;
    };
  }, [fetchReportData]);

  const areaCounts = useMemo(() => buildAreaCounts(state.allTickets), [state.allTickets]);

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-[var(--sand-300)] bg-white p-5 shadow-sm md:p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-2xl text-[var(--brand-700)] md:text-3xl">Reportes</h2>
            <p className="mt-2 text-sm text-[var(--ink-600)]">
              GETs simples de tickets abiertos, tickets cerrados y conteo de tickets por area.
            </p>
          </div>
          <Button variant="outline" onClick={loadReports}>
            <RefreshCcw className="h-4 w-4" />
            Recargar
          </Button>
        </div>
      </section>

      {state.error && (
        <Card>
          <CardContent className="pt-5">
            <p className="text-sm text-[#8d2828]">{state.error}</p>
          </CardContent>
        </Card>
      )}

      <section className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardDescription className="flex items-center gap-2">
              <TicketCheck className="h-4 w-4" />
              Tickets abiertos
            </CardDescription>
            <CardTitle className="text-3xl text-[var(--brand-700)]">{state.loading ? "..." : state.openTotal}</CardTitle>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader>
            <CardDescription className="flex items-center gap-2">
              <TicketX className="h-4 w-4" />
              Tickets cerrados
            </CardDescription>
            <CardTitle className="text-3xl text-[var(--brand-700)]">{state.loading ? "..." : state.closedTotal}</CardTitle>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader>
            <CardDescription className="flex items-center gap-2">
              <Layers3 className="h-4 w-4" />
              Total tickets
            </CardDescription>
            <CardTitle className="text-3xl text-[var(--brand-700)]">
              {state.loading ? "..." : state.openTotal + state.closedTotal}
            </CardTitle>
          </CardHeader>
        </Card>
      </section>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-[var(--brand-700)]">
            <BarChart3 className="h-5 w-5" />
            Conteo de tickets por area
          </CardTitle>
          <CardDescription>Resumen agregado de tickets por area</CardDescription>
        </CardHeader>
        <CardContent>
          {state.loading && <p className="text-sm text-[var(--ink-600)]">Cargando conteos por area...</p>}

          {!state.loading && areaCounts.length === 0 && (
            <p className="text-sm text-[var(--ink-600)]">No hay tickets para calcular conteos.</p>
          )}

          {!state.loading && areaCounts.length > 0 && (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {areaCounts.map((item) => (
                <div key={item.area} className="rounded-lg border border-[var(--sand-300)] bg-[var(--sand-200)] p-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--brand-700)]">{item.area}</p>
                  <div className="mt-2 flex items-center justify-between">
                    <span className="text-sm text-[var(--ink-700)]">Tickets</span>
                    <Badge variant="secondary">{item.count}</Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
