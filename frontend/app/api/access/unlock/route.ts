import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const ACCESS_COOKIE = "pl_access_ok";

export async function POST(request: NextRequest) {
  const configuredPin = process.env.FRONTEND_ACCESS_PIN?.trim();
  if (!configuredPin) {
    return NextResponse.json(
      {
        ok: false,
        error: "PIN no configurado en FRONTEND_ACCESS_PIN.",
      },
      { status: 503 }
    );
  }

  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json({ ok: false, error: "Payload invalido." }, { status: 400 });
  }

  const pin =
    payload && typeof payload === "object" && "pin" in payload && typeof payload.pin === "string"
      ? payload.pin.trim()
      : "";

  if (!/^\d{4}$/.test(pin)) {
    return NextResponse.json({ ok: false, error: "El PIN debe tener 4 digitos." }, { status: 400 });
  }

  if (pin !== configuredPin) {
    return NextResponse.json({ ok: false, error: "PIN incorrecto." }, { status: 401 });
  }

  const response = NextResponse.json({ ok: true });
  response.cookies.set(ACCESS_COOKIE, "1", {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 60 * 8,
  });

  return response;
}
