import type { Incident } from "../api";
import { date } from "../presentation";

// Sum integer cents so 0.10 + 0.20 stays exactly 0.30.
function cents(value: string): bigint {
  const [whole, fraction = ""] = value.split(".");
  return BigInt(whole) * 100n + BigInt(fraction.padEnd(2, "0"));
}
function money(value: bigint): string {
  return `${(value / 100n).toLocaleString("es-UY")},${(value % 100n).toString().padStart(2, "0")}`;
}

export function TodoTable({
  items,
  busy,
  toggle,
  edit,
  chat,
}: {
  items: Incident[];
  busy: boolean;
  toggle: (item: Incident) => Promise<void>;
  edit: (item: Incident) => void;
  chat: (item: Incident) => void;
}) {
  const total = items.reduce(
    (sum, item) => sum + (item.cost === null ? 0n : cents(item.cost)),
    0n,
  );
  const missing = items.filter((item) => item.cost === null).length;
  return (
    <>
      <div
        className="todo-sheet"
        role="region"
        aria-label="Tabla de to-dos"
        tabIndex={0}
      >
        <table>
          <thead>
            <tr>
              <th scope="col" aria-label="Completado">
                ✓
              </th>
              <th scope="col">Fecha</th>
              <th scope="col">Descripción</th>
              <th scope="col">Kilómetros</th>
              <th scope="col">Costo</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr
                key={item.id}
                className={item.status === "RESOLVED" ? "is-done" : ""}
              >
                <td>
                  <input
                    type="checkbox"
                    checked={item.status === "RESOLVED"}
                    disabled={busy}
                    aria-label={`Completar: ${item.title}`}
                    onChange={() => void toggle(item)}
                  />
                </td>
                <td>
                  <button
                    className="sheet-cell"
                    disabled={busy}
                    aria-label={`Editar fecha: ${item.title}`}
                    onClick={() => edit(item)}
                  >
                    {item.performed_on
                      ? date(item.performed_on + "T12:00:00")
                      : "—"}
                  </button>
                </td>
                <td className="description-cell">
                  <button
                    className="sheet-cell todo-title"
                    disabled={busy}
                    onClick={() => edit(item)}
                  >
                    {item.title}
                  </button>
                  {item.work_notes && <p>{item.work_notes}</p>}
                  <button
                    className="quiet"
                    disabled={busy}
                    onClick={() => chat(item)}
                  >
                    Abrir chat
                  </button>
                </td>
                <td className="numeric">
                  <button
                    className="sheet-cell"
                    disabled={busy}
                    aria-label={`Editar kilómetros: ${item.title}`}
                    onClick={() => edit(item)}
                  >
                    {item.work_mileage === null
                      ? "—"
                      : item.work_mileage.toLocaleString("es-UY")}
                  </button>
                </td>
                <td className="numeric">
                  <button
                    className="sheet-cell"
                    disabled={busy}
                    aria-label={`Editar costo: ${item.title}`}
                    onClick={() => edit(item)}
                  >
                    {item.cost === null ? "—" : money(cents(item.cost))}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <th scope="row" colSpan={4}>
                Total gastado
              </th>
              <td className="numeric">{money(total)}</td>
            </tr>
          </tfoot>
        </table>
      </div>
      <p className="sheet-help">
        Tocá una celda para editar. Fecha y kilómetros corresponden al trabajo.
        Costos pagados en una misma moneda, incluidos los pendientes.
        {missing > 0 && ` ${missing} ítem(s) sin costo cargado.`}
      </p>
    </>
  );
}
