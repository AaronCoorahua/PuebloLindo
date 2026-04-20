import { getJson, postJson } from "@/lib/api/client";

import type { CloseTicketPayload, CloseTicketResponse, TicketListResponse, TicketStatus } from "./types";

const API_PREFIX = "/api/v1";
const MAX_PAGE_SIZE = 100;

export function fetchTickets(status?: TicketStatus, limit = 100, offset = 0): Promise<TicketListResponse> {
  const safeLimit = Math.min(Math.max(limit, 1), MAX_PAGE_SIZE);
  const params = new URLSearchParams({
    limit: String(safeLimit),
    offset: String(offset),
  });

  if (status) {
    params.set("status", status);
  }

  return getJson<TicketListResponse>(`${API_PREFIX}/tickets?${params.toString()}`);
}

export async function fetchAllTickets(status?: TicketStatus): Promise<TicketListResponse> {
  const firstPage = await fetchTickets(status, MAX_PAGE_SIZE, 0);
  const items = [...firstPage.items];
  const total = firstPage.total;

  if (items.length >= total) {
    return {
      items,
      total,
      limit: MAX_PAGE_SIZE,
      offset: 0,
    };
  }

  for (let offset = items.length; offset < total; offset += MAX_PAGE_SIZE) {
    const page = await fetchTickets(status, MAX_PAGE_SIZE, offset);
    if (page.items.length === 0) {
      break;
    }
    items.push(...page.items);
  }

  return {
    items,
    total,
    limit: MAX_PAGE_SIZE,
    offset: 0,
  };
}

export function closeTicket(ticketId: string, payload: CloseTicketPayload): Promise<CloseTicketResponse> {
  return postJson<CloseTicketResponse, CloseTicketPayload>(`${API_PREFIX}/tickets/${ticketId}/close`, payload);
}
