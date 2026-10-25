import type { Detail, Incident, Vehicle } from "../api";

export type Editor =
  | { type: "vehicle"; vehicle?: Vehicle }
  | { type: "incident"; incident?: Incident }
  | { type: "resolution" }
  | { type: "delete"; vehicle: Vehicle };

export function EditorFields({
  editor,
  detail,
}: {
  editor: Editor;
  detail: Detail | null;
}) {
  return (
    <>
      {editor.type === "vehicle" ? (
        <>
          <p className="form-intro">
            Empezá por un nombre. Dejá vacíos los datos que no conozcas.
          </p>
          <label>
            Nombre del vehículo
            <input
              name="name"
              required
              maxLength={100}
              defaultValue={editor.vehicle?.name}
              placeholder="Por ejemplo, Gol del taller"
              autoFocus
            />
          </label>
          <div className="form-grid">
            <label>
              Marca <small>Opcional</small>
              <input
                name="make"
                maxLength={60}
                defaultValue={editor.vehicle?.make || ""}
              />
            </label>
            <label>
              Modelo <small>Opcional</small>
              <input
                name="model"
                maxLength={80}
                defaultValue={editor.vehicle?.model || ""}
              />
            </label>
            <label>
              Año <small>Opcional</small>
              <input
                name="year"
                type="number"
                min={1886}
                max={2100}
                step={1}
                defaultValue={editor.vehicle?.year || ""}
              />
            </label>
          </div>
          <label>
            Kilometraje actual
            <input
              name="mileage"
              type="number"
              min={0}
              max={10000000}
              step={1}
              defaultValue={editor.vehicle?.mileage ?? ""}
              placeholder="Si lo conocés"
            />
          </label>
          <label>
            Modificaciones
            <textarea
              name="modifications"
              rows={3}
              maxLength={10000}
              defaultValue={editor.vehicle?.modifications || ""}
              placeholder="Qué cambiaste respecto del auto original"
            />
          </label>
          <details>
            <summary>Datos técnicos opcionales</summary>
            <label>
              Manual de referencia
              <select
                name="manual_reference"
                defaultValue={editor.vehicle?.manual_reference || ""}
              >
                <option value="">Usar los datos registrados del auto</option>
                <option value="gol-g2-1600-mi-1998-factory">
                  Gol G2 1.6 MI 1998 de fábrica
                </option>
              </select>
              <small>
                El manual describe el auto original. Las modificaciones se
                tienen en cuenta al responder.
              </small>
            </label>
            <div className="form-grid">
              <label>
                Combustible <small>Opcional</small>
                <input
                  name="fuel"
                  maxLength={40}
                  defaultValue={editor.vehicle?.fuel || ""}
                  placeholder="Si lo conocés"
                />
              </label>
              <label>
                Código de motor <small>Opcional</small>
                <input
                  name="engine_code"
                  maxLength={40}
                  defaultValue={editor.vehicle?.engine_code || ""}
                />
              </label>
              <label>
                Mercado / país <small>Opcional</small>
                <input
                  name="market"
                  maxLength={60}
                  defaultValue={editor.vehicle?.market || ""}
                />
              </label>
            </div>
          </details>
          <label>
            Notas <small>Opcional</small>
            <textarea
              name="notes"
              rows={2}
              maxLength={10000}
              defaultValue={editor.vehicle?.notes || ""}
            />
          </label>
        </>
      ) : editor.type === "incident" ? (
        <>
          <p className="form-intro">
            Contá lo que observaste. No necesitás conocer la causa.
          </p>
          <label>
            Título de la avería
            <input
              name="title"
              required
              maxLength={160}
              defaultValue={editor.incident?.title}
              placeholder="Por ejemplo, pérdida recurrente de refrigerante"
              autoFocus
            />
          </label>
          <label>
            Qué pasó
            <textarea
              name="description"
              required
              maxLength={10000}
              rows={4}
              defaultValue={editor.incident?.description}
              placeholder="Cuándo apareció, qué notaste y en qué condiciones."
            />
          </label>
          <label>
            Síntomas observados <small>Uno por línea · hasta 30</small>
            <textarea
              name="symptoms"
              rows={3}
              defaultValue={editor.incident?.symptoms.join("\n")}
              placeholder="Nivel que vuelve a bajar&#10;Mancha debajo del vehículo"
            />
          </label>
          <label>
            Kilometraje <small>Opcional</small>
            <input
              name="mileage"
              type="number"
              min={0}
              max={10000000}
              step={1}
              defaultValue={editor.incident?.mileage ?? ""}
              placeholder="En kilómetros"
            />
          </label>
        </>
      ) : editor.type === "resolution" ? (
        <>
          <p className="form-intro">
            Dejá constancia del trabajo realizado y el resultado. Esto cerrará
            la avería.
          </p>
          <label>
            Qué se hizo y cómo quedó
            <textarea
              name="resolution"
              required
              rows={6}
              maxLength={10000}
              defaultValue={detail?.resolution || ""}
              placeholder="Reparación realizada, comprobaciones y resultado observado."
              autoFocus
            />
          </label>
        </>
      ) : (
        <>
          <p>
            Vas a eliminar <strong>{editor.vehicle.name}</strong>. Esta acción
            no se puede deshacer.
          </p>
          <p className="muted">
            Si tiene averías registradas, el vehículo se conservará y la
            eliminación no se realizará.
          </p>
        </>
      )}
    </>
  );
}
