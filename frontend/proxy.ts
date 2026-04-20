import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const ACCESS_COOKIE = "pl_access_ok";
const ACCESS_ROUTE = "/access";
const ACCESS_UNLOCK_ROUTE = "/api/access/unlock";

function isPublicPath(pathname: string): boolean {
  if (pathname === ACCESS_ROUTE || pathname.startsWith(`${ACCESS_ROUTE}/`)) {
    return true;
  }

  if (pathname === ACCESS_UNLOCK_ROUTE || pathname.startsWith(`${ACCESS_UNLOCK_ROUTE}/`)) {
    return true;
  }

  if (pathname.startsWith("/_next")) {
    return true;
  }

  if (pathname === "/favicon.ico") {
    return true;
  }

  return false;
}

export function proxy(request: NextRequest) {
  const pin = process.env.FRONTEND_ACCESS_PIN?.trim();
  if (!pin) {
    return NextResponse.next();
  }

  const { pathname, search } = request.nextUrl;
  if (isPublicPath(pathname)) {
    return NextResponse.next();
  }

  const unlocked = request.cookies.get(ACCESS_COOKIE)?.value === "1";
  if (unlocked) {
    return NextResponse.next();
  }

  const redirectUrl = request.nextUrl.clone();
  redirectUrl.pathname = ACCESS_ROUTE;
  redirectUrl.search = `?next=${encodeURIComponent(`${pathname}${search}`)}`;
  return NextResponse.redirect(redirectUrl);
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)"],
};
