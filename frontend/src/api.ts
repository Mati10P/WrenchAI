export type Status = "OPEN" | "IN_PROGRESS" | "RESOLVED";
export type VehicleInput = {
  name: string;
  make: string | null;
  model: string | null;
  year: number | null;
  fuel: string | null;
  engine_code: string | null;
  market: string | null;
  notes: string | null;
  mileage: number | null;
  modifications: string | null;
};
export type Vehicle = VehicleInput & { id: string; created_at: string };
export type IncidentInput = {
  title: string;
  description: string;
  symptoms: string[];
  mileage: number | null;
};
export type Incident = IncidentInput & {
  id: string;
  vehicle_id: string;
  status: Status;
  resolution: string | null;
  created_at: string;
  resolved_at: string | null;
  work_notes: string | null;
  performed_on: string | null;
  work_mileage: number | null;
  cost: string | null;
};
export type Measurement = {
  id: string;
  name: string;
  value: string;
  unit: string;
  conditions: string | null;
  observed_at: string;
};
export type Detail = Incident & { measurements: Measurement[] };
export type Message = {
  id: string;
  incident_id: string;
  content: string;
  created_at: string;
};

export type Reply = {
  message_id: string;
  incident_id: string;
  model: string;
  safety_warning: string | null;
  created_at: string;
  content: {
    summary: string;
    hypotheses: string[];
    questions: string[];
    checks: string[];
    citation_ids: string[];
  };
  sources: { id: string; title: string; page: number; text: string }[];
};
export type AssistantStatus = {
  configured: boolean;
  approved_passages: number;
  corpus_valid: boolean;
  web_search: boolean;
};

export async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  let response: Response;
  try {
    response = await fetch("/api" + path, {
      ...options,
      headers: { "Content-Type": "application/json", ...options.headers },
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError")
      throw error;
    throw new Error(
      "No pudimos conectar. Verificá que la aplicación esté en funcionamiento y volvé a intentar.",
    );
  }
  if (!response.ok) {
    if (path.endsWith("/reply")) {
      const body = await response.json().catch(() => null);
      throw new Error(
        typeof body?.detail === "string"
          ? body.detail
          : "La respuesta no se pudo generar. El mensaje está guardado; podés reintentar.",
      );
    }

    if (response.status === 409)
      throw new Error(
        "No se pudo guardar este cambio porque entra en conflicto con el registro actual. Actualizá la página antes de intentarlo de nuevo.",
      );
    if (response.status === 404)
      throw new Error(
        "Este registro ya no está disponible. Volvé al taller para actualizar la lista.",
      );
    if (response.status === 422) {
      const payload = await response.json().catch(() => null);
      const names: Record<string, string> = {
        name: "nombre",
        title: "título",
        description: "descripción",
        symptoms: "síntomas",
        mileage: "kilometraje",
        value: "valor de la medición",
        unit: "unidad",
        resolution: "resolución",
        year: "año",
        conditions: "condiciones",
        engine_code: "código de motor",
        fuel: "combustible",
        market: "mercado",
        make: "marca",
        model: "modelo",
        notes: "notas",
      };
      const field = payload?.detail?.[0]?.loc?.at(-1);
      throw new Error(
        `Revisá ${names[field] ? "el campo «" + names[field] + "»" : "los datos ingresados"}. El valor está vacío o supera el formato o límite permitido.`,
      );
    }
    throw new Error(
      "No pudimos completar la operación. Tus cambios no se confirmaron; volvé a intentar.",
    );
  }
  return response.status === 204 ? (undefined as T) : response.json();
}

export async function listAll<T>(
  path: string,
  signal: AbortSignal,
): Promise<T[]> {
  const items: T[] = [];
  for (let offset = 0; ; offset += 100) {
    const page = await request<T[]>(`${path}?limit=100&offset=${offset}`, {
      signal,
    });
    items.push(...page);
    if (page.length < 100) return items;
  }
}

export const json = (method: string, body?: unknown): RequestInit => ({
  method,
  body: body === undefined ? undefined : JSON.stringify(body),
});
export const incidentInput = (item: Incident): IncidentInput => ({
  title: item.title,
  description: item.description,
  symptoms: item.symptoms,
  mileage: item.mileage,
});
