"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchAllTickets } from "./api";
import type { Ticket, TicketStatus } from "./types";

type TicketState = {
  loading: boolean;
  error?: string;
  items: Ticket[];
  total: number;
};

export function useTickets(status: TicketStatus) {
  const [state, setState] = useState<TicketState>({ loading: true, items: [], total: 0 });

  const reload = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: undefined }));

    try {
      const response = await fetchAllTickets(status);
      setState({ loading: false, items: response.items, total: response.total });
    } catch (error) {
      setState({
        loading: false,
        items: [],
        total: 0,
        error: error instanceof Error ? error.message : "No se pudieron cargar los tickets",
      });
    }
  }, [status]);

  useEffect(() => {
    let isCancelled = false;

    async function load() {
      try {
        const response = await fetchAllTickets(status);
        if (isCancelled) {
          return;
        }
        setState({ loading: false, items: response.items, total: response.total });
      } catch (error) {
        if (isCancelled) {
          return;
        }
        setState({
          loading: false,
          items: [],
          total: 0,
          error: error instanceof Error ? error.message : "No se pudieron cargar los tickets",
        });
      }
    }

    load();

    return () => {
      isCancelled = true;
    };
  }, [status]);

  return useMemo(
    () => ({
      loading: state.loading,
      error: state.error,
      tickets: state.items,
      total: state.total,
      reload,
    }),
    [reload, state.error, state.items, state.loading, state.total]
  );
}
