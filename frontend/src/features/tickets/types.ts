export type TicketStatus = "open" | "closed";

export type Ticket = {
  id: string;
  user_phone: string;
  status: TicketStatus;
  area: string;
  title: string;
  summary: string;
  created_at: string;
  updated_at: string;
  last_activity_at: string;
  closed_by?: string | null;
  closed_message?: string | null;
  wa_link: string;
};

export type TicketListResponse = {
  items: Ticket[];
  total: number;
  limit: number;
  offset: number;
};

export type CloseTicketPayload = {
  mensaje_cierre: string;
  atendedor: string;
};

export type CloseTicketResponse = {
  ticket: Ticket;
  notification_sent: boolean;
  notification_error: string | null;
};
