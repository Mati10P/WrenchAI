import type { Status } from "./api";

export const labels: Record<Status, string> = {
  OPEN: "Pendiente",
  IN_PROGRESS: "En reparación",
  RESOLVED: "Resuelta",
};
export const date = (value: string) =>
  new Intl.DateTimeFormat("es-UY", { dateStyle: "medium" }).format(
    new Date(value),
  );
export const km = (value: number | null) =>
  value === null ? "Sin kilometraje" : `${value.toLocaleString("es-UY")} km`;
export const route = (vehicle?: string, incident?: string) =>
  `#/vehicles${vehicle ? "/" + vehicle : ""}${incident ? "/incidents/" + incident : ""}`;
