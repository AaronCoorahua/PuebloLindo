export type TicketStatus = "open" | "closed";

export type Ticket = {
  id: string;
  user_phone: string;
  status: TicketStatus;
  area: string;
  summary: string;
  created_at: string;
  updated_at: string;
  last_activity_at: string;
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
