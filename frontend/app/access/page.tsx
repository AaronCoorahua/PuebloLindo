import { AccessForm } from "./access-form";

type AccessPageProps = {
  searchParams: Promise<{ next?: string | string[] }>;
};

function sanitizeNextPath(value: string | string[] | undefined): string {
  const raw = Array.isArray(value) ? value[0] : value;
  if (!raw || !raw.startsWith("/") || raw.startsWith("//")) {
    return "/home";
  }
  return raw;
}

export default async function AccessPage({ searchParams }: AccessPageProps) {
  const params = await searchParams;
  const nextPath = sanitizeNextPath(params.next);
  return <AccessForm nextPath={nextPath} />;
}
