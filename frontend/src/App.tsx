import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { request, listAll, json, incidentInput } from "./api";
import type { Vehicle, VehicleInput, Incident, Detail, Message } from "./api";
import { date, km, route } from "./presentation";
import { Icon } from "./components/Icon";
import { Modal } from "./components/Modal";
import { EditorFields } from "./components/EditorFields";
import type { Editor } from "./components/EditorFields";

type Panel = "auto" | "pending" | "history" | "chats";
type Form = Editor | { type: "work" };

export default function App() {
  const [hash, setHash] = useState(window.location.hash);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [panel, setPanel] = useState<Panel | null>(null);
  const [editor, setEditor] = useState<Form | null>(null);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState("");
  const [formError, setFormError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingChat, setLoadingChat] = useState(false);
  const [revision, setRevision] = useState(0);
  const retry = useRef<{ id: string; text: string; context: string } | null>(
    null,
  );
  const scrollEnd = useRef<HTMLDivElement>(null);
  const composer = useRef<HTMLTextAreaElement>(null);
  const parts = hash.replace(/^#\/?/, "").split("/");
  const vehicleId = parts[0] === "vehicles" ? parts[1] : undefined;
  const incidentId = parts[2] === "incidents" ? parts[3] : undefined;
  const active =
    vehicles.find((v) => v.id === vehicleId) ||
    (!vehicleId ? vehicles[0] : undefined);

  useEffect(() => {
    const change = () => {
      setHash(window.location.hash);
      setDraft("");
      setNotice("");
    };
    window.addEventListener("hashchange", change);
    return () => window.removeEventListener("hashchange", change);
  }, []);
  useEffect(() => {
    const abort = new AbortController();
    setLoading(true);
    listAll<Vehicle>("/vehicles", abort.signal)
      .then((items) => {
        if (!abort.signal.aborted) setVehicles(items);
      })
      .catch((e) => {
        if (!abort.signal.aborted) setError(e.message);
      })
      .finally(() => {
        if (!abort.signal.aborted) setLoading(false);
      });
    return () => abort.abort();
  }, [revision]);
  useEffect(() => {
    if (loading || vehicleId || !vehicles.length) return;
    let previous: string | null = null;
    try {
      previous = localStorage.getItem("wrenchai.vehicle");
    } catch {
      /* optional preference */
    }
    window.location.hash = route(
      vehicles.find((v) => v.id === previous)?.id || vehicles[0].id,
    );
  }, [loading, vehicles, vehicleId]);
  useEffect(() => {
    if (!active) return;
    try {
      localStorage.setItem("wrenchai.vehicle", active.id);
    } catch {
      /* optional preference */
    }
  }, [active?.id]);
  useEffect(() => {
    const abort = new AbortController();
    setIncidents([]);
    setDetail(null);
    setMessages([]);
    setError("");
    if (!active) {
      setLoadingChat(false);
      return;
    }
    setLoadingChat(true);
    const incidentList = listAll<Incident>(
      `/vehicles/${active.id}/incidents`,
      abort.signal,
    );
    const conversation = incidentId
      ? Promise.all([
          request<Detail>(`/incidents/${incidentId}`, { signal: abort.signal }),
          listAll<Message>(`/incidents/${incidentId}/messages`, abort.signal),
        ])
      : Promise.resolve(null);
    Promise.all([incidentList, conversation])
      .then(([items, chat]) => {
        if (abort.signal.aborted) return;
        if (chat && chat[0].vehicle_id !== active.id)
          throw new Error("Este chat no corresponde al auto seleccionado.");
        setIncidents(items);
        if (chat) {
          setDetail(chat[0]);
          setMessages(chat[1]);
        }
      })
      .catch((e) => {
        if (!abort.signal.aborted) setError(e.message);
      })
      .finally(() => {
        if (!abort.signal.aborted) setLoadingChat(false);
      });
    return () => abort.abort();
  }, [active?.id, incidentId, revision]);
  useEffect(() => {
    scrollEnd.current?.scrollIntoView({ block: "nearest" });
  }, [messages.length, detail?.id]);

  function navigate(id?: string, chat?: string) {
    if (busy) return;
    setPanel(null);
    setError("");
    setDraft("");
    window.location.hash = route(id, chat);
    composer.current?.focus();
  }
  function open(form: Form) {
    setFormError("");
    setEditor(form);
  }
  async function send(event: FormEvent) {
    event.preventDefault();
    if (
      !active ||
      !draft.trim() ||
      busy ||
      loadingChat ||
      error ||
      (incidentId && !detail)
    )
      return;
    const text = draft.trim();
    const context = `${active.id}/${incidentId || "new"}`;
    if (retry.current?.text !== text || retry.current.context !== context)
      retry.current = { id: crypto.randomUUID(), text, context };
    setBusy(true);
    setNotice("");
    try {
      const message = await request<Message>(
        incidentId
          ? `/incidents/${incidentId}/messages`
          : `/vehicles/${active.id}/chats`,
        json("POST", { id: retry.current.id, content: text }),
      );
      retry.current = null;
      setDraft("");
      if (!incidentId)
        window.location.hash = route(active.id, message.incident_id);
      setRevision((v) => v + 1);
    } catch (e) {
      setNotice(
        e instanceof Error
          ? e.message
          : "No se guardó el mensaje. Podés volver a enviarlo.",
      );
    } finally {
      setBusy(false);
      composer.current?.focus();
    }
  }
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editor || busy) return;
    const data = new FormData(event.currentTarget);
    const str = (name: string) => String(data.get(name) || "").trim();
    setBusy(true);
    setFormError("");
    try {
      if (editor.type === "vehicle") {
        const payload: VehicleInput = {
          name: str("name"),
          mileage: str("mileage") ? Number(str("mileage")) : null,
          modifications: str("modifications") || null,
          notes: str("notes") || null,
          make: str("make") || null,
          model: str("model") || null,
          year: str("year") ? Number(str("year")) : null,
          fuel: str("fuel") || null,
          engine_code: str("engine_code") || null,
          market: str("market") || null,
        };
        const vehicle = await request<Vehicle>(
          editor.vehicle ? `/vehicles/${editor.vehicle.id}` : "/vehicles",
          json(editor.vehicle ? "PUT" : "POST", payload),
        );
        if (!editor.vehicle) window.location.hash = route(vehicle.id);
      } else if (editor.type === "work" && active) {
        await request(
          `/vehicles/${active.id}/work`,
          json("POST", { description: str("description") }),
        );
        setPanel("history");
      } else if (editor.type === "resolution" && detail) {
        await request(
          `/incidents/${detail.id}`,
          json("PUT", {
            ...incidentInput(detail),
            status: "RESOLVED",
            resolution: str("resolution"),
          }),
        );
      }
      setEditor(null);
      setRevision((v) => v + 1);
    } catch (e) {
      setFormError(
        e instanceof Error ? e.message : "No pudimos guardar el cambio.",
      );
    } finally {
      setBusy(false);
    }
  }
  const pending = incidents.filter((i) => i.status !== "RESOLVED");
  const history = incidents.filter((i) => i.status === "RESOLVED");
  const list =
    panel === "pending" ? pending : panel === "history" ? history : incidents;

  return (
    <div className="chat-app">
      <header className="chat-header">
        <button
          className="brand"
          disabled={busy}
          onClick={() => navigate(active?.id)}
          aria-label="WrenchAI, nuevo chat"
        >
          <Icon name="wrench" />
          Wrench<span>AI</span>
        </button>
        <div className="header-actions">
          <button
            className="quiet"
            disabled={busy || !active}
            onClick={() => navigate(active?.id)}
          >
            <Icon name="plus" size={17} />
            Nuevo chat
          </button>
          <button
            className="car-button"
            disabled={busy}
            onClick={() => setPanel("auto")}
          >
            <Icon name="car" size={19} />
            Mi auto
          </button>
        </div>
      </header>
      <main className="conversation">
        <div className="context-line">
          <button
            className="quiet"
            disabled={busy}
            onClick={() => setPanel("auto")}
          >
            {active?.name || "Elegí tu auto"}
            <span> · {active ? km(active.mileage) : ""}</span>
          </button>
          <button
            className="quiet"
            disabled={busy || !active}
            onClick={() => setPanel("chats")}
          >
            Conversaciones
          </button>
        </div>
        <div className="chat-scroll">
          {loading && !vehicles.length ? (
            <p role="status">Cargando tu auto…</p>
          ) : error ? (
            <div className="error-state" role="alert">
              <p>{error}</p>
              <button
                onClick={() => {
                  setError("");
                  setRevision((v) => v + 1);
                }}
              >
                Volver a intentar
              </button>
              <button onClick={() => navigate(active?.id)}>
                Volver al chat
              </button>
            </div>
          ) : vehicleId && !active ? (
            <p role="alert">No encontramos este auto. Elegí otro en Mi auto.</p>
          ) : loadingChat ? (
            <p role="status">Cargando conversación…</p>
          ) : !detail ? (
            <div className="welcome">
              <span className="welcome-icon">
                <Icon name="wrench" size={30} />
              </span>
              <h1>¿Qué le pasa al auto?</h1>
              <p>
                Contame qué notás, cuándo pasa o qué estás intentando arreglar.
              </p>
              {!active ? (
                <button
                  className="primary"
                  onClick={() => open({ type: "vehicle" })}
                >
                  Agregar mi auto
                </button>
              ) : (
                <button
                  className="example"
                  onClick={() => {
                    setDraft(
                      "El auto se siente tosco, suena grave y no tiene potencia.",
                    );
                    composer.current?.focus();
                  }}
                >
                  “El auto se siente tosco, suena grave y no tiene potencia.”
                  <Icon name="arrow" size={16} />
                </button>
              )}
            </div>
          ) : (
            <div className="messages" aria-label="Conversación">
              <div className="conversation-date">{date(detail.created_at)}</div>
              {messages[0]?.content !== detail.description && (
                <div className="user-message">
                  <span>Registro anterior</span>
                  <p>{detail.description}</p>
                </div>
              )}
              {messages.map((message) => (
                <div className="user-message" key={message.id}>
                  <span>Vos</span>
                  <p>{message.content}</p>
                </div>
              ))}
              <p className="saved-receipt" role="status">
                <Icon name="check" size={15} />
                {messages.length
                  ? "Mensajes guardados en esta conversación."
                  : "Registro guardado."}{" "}
                {detail.status !== "RESOLVED" &&
                  "El problema está en tus pendientes."}
              </p>
              {!!detail.measurements.length && (
                <details className="chat-record">
                  <summary>
                    Mediciones guardadas ({detail.measurements.length})
                  </summary>
                  {detail.measurements.map((m) => (
                    <p key={m.id}>
                      <strong>
                        {m.name}: {m.value} {m.unit}
                      </strong>
                      <br />
                      {m.conditions}
                    </p>
                  ))}
                </details>
              )}
              {detail.resolution && (
                <div className="work-note">
                  <strong>Trabajo registrado</strong>
                  <p>{detail.resolution}</p>
                </div>
              )}
              <div className="chat-tools">
                <button
                  className="quiet"
                  disabled={busy}
                  onClick={() => open({ type: "resolution" })}
                >
                  {detail.status === "RESOLVED"
                    ? "Editar trabajo realizado"
                    : "Ya lo resolví"}
                </button>
              </div>
            </div>
          )}
          <div ref={scrollEnd} />
        </div>
        <div className="composer-area">
          <p className="availability">
            La IA todavía no está conectada. Podés guardar el problema y
            continuar el registro; aún no hay respuestas ni búsqueda en manuales
            o internet.
          </p>
          {notice && (
            <p className="form-error" role="alert">
              {notice}
            </p>
          )}
          <form className="composer" onSubmit={send}>
            <textarea
              ref={composer}
              aria-label="Mensaje"
              placeholder={
                active
                  ? "Escribí lo que le pasa al auto…"
                  : "Agregá tu auto para empezar"
              }
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              maxLength={10000}
              rows={2}
              disabled={!active || busy}
              onKeyDown={(e) => {
                if (
                  e.key === "Enter" &&
                  !e.shiftKey &&
                  !e.nativeEvent.isComposing
                ) {
                  e.preventDefault();
                  e.currentTarget.form?.requestSubmit();
                }
              }}
            />
            <button
              className="send-button"
              aria-label="Enviar mensaje"
              disabled={
                !active ||
                !draft.trim() ||
                busy ||
                loadingChat ||
                !!error ||
                (!!incidentId && !detail)
              }
              type="submit"
            >
              {busy ? "…" : "↑"}
            </button>
          </form>
          <p className="composer-hint">
            Enter para enviar · Shift + Enter para otra línea
          </p>
        </div>
      </main>
      {panel && (
        <Modal
          title="Mi auto"
          close={() => {
            if (!busy) setPanel(null);
          }}
        >
          <nav className="menu-tabs" aria-label="Información del auto">
            {(
              [
                ["auto", "Datos"],
                ["pending", "Pendientes"],
                ["history", "Trabajos"],
                ["chats", "Chats"],
              ] as const
            ).map(([key, label]) => (
              <button
                key={key}
                className={panel === key ? "selected" : ""}
                disabled={busy}
                onClick={() => setPanel(key)}
              >
                {label}
              </button>
            ))}
          </nav>
          {panel === "auto" ? (
            <>
              {!!vehicles.length && (
                <label>
                  Auto
                  <select
                    value={active?.id || ""}
                    disabled={busy}
                    onChange={(e) => {
                      window.location.hash = route(e.target.value);
                    }}
                  >
                    {vehicles.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.name}
                      </option>
                    ))}
                  </select>
                </label>
              )}
              {active && (
                <div className="car-data">
                  <h3>{active.name}</h3>
                  <p>
                    {[active.make, active.model, active.year]
                      .filter(Boolean)
                      .join(" · ")}
                  </p>
                  <dl>
                    <dt>Kilometraje</dt>
                    <dd>{km(active.mileage)}</dd>
                    <dt>Modificaciones</dt>
                    <dd>
                      {active.modifications ||
                        "Todavía no registraste modificaciones."}
                    </dd>
                    <dt>Notas</dt>
                    <dd>{active.notes || "Sin notas."}</dd>
                  </dl>
                  <button
                    className="primary"
                    onClick={() => open({ type: "vehicle", vehicle: active })}
                  >
                    Editar datos
                  </button>
                </div>
              )}
              <button
                className="quiet"
                onClick={() => open({ type: "vehicle" })}
              >
                Agregar otro auto
              </button>
            </>
          ) : (
            <>
              {panel === "pending" && (
                <p className="muted">
                  Los problemas que describís al iniciar un chat aparecen acá.
                </p>
              )}
              {panel === "history" && (
                <button
                  className="primary"
                  disabled={!active || busy}
                  onClick={() => open({ type: "work" })}
                >
                  Anotar un trabajo realizado
                </button>
              )}
              {loadingChat ? (
                <p role="status">Cargando…</p>
              ) : error ? (
                <p role="alert">{error}</p>
              ) : !list.length ? (
                <p className="empty-list">
                  {panel === "pending"
                    ? "No hay problemas pendientes."
                    : panel === "history"
                      ? "Todavía no registraste trabajos."
                      : "Tu primera conversación empieza escribiendo en el chat."}
                </p>
              ) : (
                <div className="record-list">
                  {list.map((item) => (
                    <button
                      key={item.id}
                      disabled={busy}
                      onClick={() => navigate(active?.id, item.id)}
                    >
                      <strong>{item.title}</strong>
                      <span>
                        {date(item.created_at)} ·{" "}
                        {item.status === "RESOLVED" ? "Resuelto" : "Pendiente"}
                      </span>
                      {panel === "history" && <p>{item.resolution}</p>}
                    </button>
                  ))}
                </div>
              )}
            </>
          )}
        </Modal>
      )}
      {editor && (
        <Modal
          title={
            editor.type === "vehicle"
              ? "Datos del auto"
              : editor.type === "work"
                ? "¿Qué le hiciste al auto?"
                : "¿Cómo lo resolviste?"
          }
          close={() => {
            if (!busy) setEditor(null);
          }}
        >
          <form onSubmit={save}>
            {editor.type === "work" ? (
              <label>
                Trabajo realizado
                <textarea
                  name="description"
                  required
                  maxLength={10000}
                  rows={5}
                  placeholder="Qué hiciste y cómo quedó"
                />
              </label>
            ) : (
              <EditorFields editor={editor} detail={detail} />
            )}
            {formError && (
              <p className="form-error" role="alert">
                {formError}
              </p>
            )}
            <div className="form-actions">
              <button
                type="button"
                disabled={busy}
                onClick={() => setEditor(null)}
              >
                Cancelar
              </button>
              <button type="submit" className="primary" disabled={busy}>
                {busy ? "Guardando…" : "Guardar"}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
