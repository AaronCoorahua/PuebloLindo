"use client";

import { ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

type AccessFormProps = {
  nextPath: string;
};

export function AccessForm({ nextPath }: AccessFormProps) {
  const router = useRouter();
  const [pin, setPin] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const value = pin.trim();
    if (!/^\d{4}$/.test(value)) {
      setError("El PIN debe tener 4 digitos.");
      return;
    }

    try {
      setLoading(true);
      const response = await fetch("/api/access/unlock", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ pin: value }),
      });

      const payload = (await response.json()) as { error?: string };
      if (!response.ok) {
        setError(payload.error || "No se pudo validar el PIN.");
        return;
      }

      router.replace(nextPath);
      router.refresh();
    } catch {
      setError("No se pudo validar el PIN. Intentalo de nuevo.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-8">
      <Card className="w-full max-w-md border-[var(--sand-400)] bg-white shadow-lg">
        <CardHeader>
          <div className="mb-3 inline-flex h-10 w-10 items-center justify-center rounded-full bg-[var(--brand-100)] text-[var(--brand-700)]">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <CardTitle className="text-2xl text-[var(--brand-700)]">Acceso protegido</CardTitle>
          <CardDescription>Ingresa el PIN de 4 digitos para acceder al dashboard.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={onSubmit}>
            <div className="space-y-1.5">
              <label className="text-sm font-semibold text-[var(--ink-700)]" htmlFor="pin">
                PIN
              </label>
              <Input
                id="pin"
                type="password"
                inputMode="numeric"
                maxLength={4}
                autoComplete="one-time-code"
                value={pin}
                onChange={(event) => setPin(event.target.value.replace(/\D/g, "").slice(0, 4))}
                placeholder="0000"
              />
            </div>

            {error && <p className="rounded-md bg-[#fde8e8] px-3 py-2 text-sm text-[#8d2828]">{error}</p>}

            <Button className="w-full" type="submit" disabled={loading}>
              {loading ? "Validando..." : "Entrar"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
