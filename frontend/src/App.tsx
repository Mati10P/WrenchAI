import { Fragment, useEffect, useLayoutEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { request, listAll, json } from "./api";
import type {
  Vehicle,
  VehicleInput,
  Incident,
  Detail,
  Message,
  Reply,
  AssistantStatus,
} from "./api";
import { date, km, route } from "./presentation";
import { AssistantMessage } from "./components/AssistantMessage";
import { TodoTable } from "./components/TodoTable";
import { Icon } from "./components/Icon";
import { Modal } from "./components/Modal";
import { EditorFields } from "./components/EditorFields";
import type { Editor } from "./components/EditorFields";

import { Button } from "./components/ui/button";
import { Badge } from "./components/ui/badge";
import { ThemePicker } from "./components/ThemePicker";
import {
  MessageSquare,
  ListChecks,
  CarFront,
  ChevronRight,
  BookOpen,
  ArrowUpRight,
  Gauge,
  CircleHelp,
} from "lucide-react";

type Panel = "auto" | "tasks" | "chats";
type Form = Editor | { type: "task"; item?: Incident; complete?: boolean };

export default function App() {
  const [hash, setHash] = useState(window.location.hash);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [replies, setReplies] = useState<Reply[]>([]);
  const [assistantStatus, setAssistantStatus] =
    useState<AssistantStatus | null>(null);
  const [chosenModel, setChosenModel] = useState(() => {
    try {
      return localStorage.getItem("wrenchai.model") || "";
    } catch {
      return "";
    }
  });
  const modelOptions = assistantStatus?.models || [];
  const effectiveModel = modelOptions.some((m) => m.id === chosenModel)
    ? chosenModel
    : modelOptions.some((m) => m.id === assistantStatus?.default_model)
      ? assistantStatus?.default_model
      : modelOptions[0]?.id;
  const [replyBusy, setReplyBusy] = useState(false);
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
  useLayoutEffect(() => {
    const resize = () => {
      const field = composer.current;
      if (!field) return;
      field.style.height = "0px";
      field.style.height = `${Math.min(Math.max(field.scrollHeight, 36), 144)}px`;
    };
    resize();
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, [draft]);
  const parts = hash.replace(/^#\/?/, "").split("/");
  const vehicleId = parts[0] === "vehicles" ? parts[1] : undefined;
  const incidentId = parts[2] === "incidents" ? parts[3] : undefined;
  const active =
    vehicles.find((v) => v.id === vehicleId) ||
    (!vehicleId ? vehicles[0] : undefined);

  useEffect(() => {
    const controller = new AbortController();
    request<AssistantStatus>("/assistant/status", { signal: controller.signal })
      .then(setAssistantStatus)
      .catch(() => setAssistantStatus(null));
    return () => controller.abort();
  }, [revision]);

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
    setReplies([]);
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
          listAll<Reply>(`/incidents/${incidentId}/replies`, abort.signal),
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
          setReplies(chat[2]);
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
  }, [messages.length, replies.length, detail?.id]);

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
      setReplyBusy(true);
      try {
        await request<Reply>(
          `/messages/${message.id}/reply`,
          json("POST", { model: effectiveModel }),
        );
      } catch (e) {
        setNotice(
          e instanceof Error
            ? e.message
            : "No se pudo generar la respuesta. El mensaje quedó guardado.",
        );
      } finally {
        setReplyBusy(false);
        setRevision((v) => v + 1);
      }
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
  async function retryReply(message: Message) {
    if (busy) return;
    setBusy(true);
    setReplyBusy(true);
    setNotice("");
    try {
      await request<Reply>(
        `/messages/${message.id}/reply`,
        json("POST", { model: effectiveModel }),
      );
    } catch (e) {
      setNotice(
        e instanceof Error ? e.message : "No se pudo generar la respuesta.",
      );
    } finally {
      setBusy(false);
      setReplyBusy(false);
      setRevision((v) => v + 1);
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
          manual_reference: (str("manual_reference") ||
            null) as VehicleInput["manual_reference"],
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
      } else if (editor.type === "task" && active) {
        const payload = {
          title: str("title"),
          description: str("description"),
          completed: data.get("completed") === "on",
          work_notes: str("work_notes") || null,
          performed_on: str("performed_on") || null,
          cost: str("cost") ? str("cost").replace(",", ".") : null,
          work_mileage: str("work_mileage")
            ? Number(str("work_mileage"))
            : null,
        };
        await request(
          editor.item
            ? `/incidents/${editor.item.id}/task`
            : `/vehicles/${active.id}/tasks`,
          json(editor.item ? "PUT" : "POST", payload),
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
  async function toggle(item: Incident) {
    if (busy) return;
    if (item.status !== "RESOLVED" && !item.work_notes) {
      open({ type: "task", item, complete: true });
      return;
    }
    setBusy(true);
    setNotice("");
    try {
      await request(
        `/incidents/${item.id}/task-state`,
        json("PATCH", { completed: item.status !== "RESOLVED" }),
      );
      setRevision((v) => v + 1);
    } catch (e) {
      setNotice(
        e instanceof Error ? e.message : "No se pudo cambiar la tarea.",
      );
    } finally {
      setBusy(false);
    }
  }
  const list =
    panel === "tasks"
      ? [...incidents].sort(
          (a, b) =>
            Number(a.status === "RESOLVED") - Number(b.status === "RESOLVED") ||
            (b.performed_on || b.created_at).localeCompare(
              a.performed_on || a.created_at,
            ),
        )
      : incidents;

  return (
    <div className="chat-app">
      <a
        className="skip-link"
        href="#main-content"
        onClick={(event) => {
          event.preventDefault();
          document.getElementById("main-content")?.focus();
        }}
      >
        Ir al contenido
      </a>
      <aside className="sidebar" aria-label="Navegación principal">
        <button
          className="brand"
          disabled={busy}
          onClick={() => navigate(active?.id)}
          aria-label="WrenchAI, inicio"
        >
          <span className="brand-mark">
            <Icon name="wrench" size={21} />
          </span>{" "}
          Wrench<span>AI</span>
        </button>
        <span className="workspace-label">TU ESPACIO DE MECÁNICA</span>
        <Button
          className="new-chat"
          disabled={busy || !active}
          onClick={() => navigate(active?.id)}
        >
          <Icon name="plus" size={17} /> Nuevo chat{" "}
          <span className="button-end">↗</span>
        </Button>
        <nav className="side-nav">
          <Button
            variant="ghost"
            className={!panel ? "nav-active" : ""}
            disabled={busy}
            onClick={() => {
              setPanel(null);
              composer.current?.focus();
            }}
          >
            <MessageSquare size={18} /> Asistente
          </Button>
          <Button
            variant="ghost"
            disabled={busy}
            onClick={() => setPanel("auto")}
          >
            <CarFront size={18} /> Mi auto
          </Button>
          <Button
            variant="ghost"
            disabled={busy || !active}
            onClick={() => setPanel("tasks")}
          >
            <ListChecks size={18} /> Pendientes y trabajos{" "}
            <Badge variant="secondary">
              {incidents.filter((i) => i.status !== "RESOLVED").length}
            </Badge>
          </Button>
        </nav>
        <div className="sidebar-history">
          <div className="section-label">
            CONVERSACIONES{" "}
            <button
              className="history-all"
              disabled={busy || !active}
              onClick={() => setPanel("chats")}
              aria-label="Ver todas las conversaciones"
            >
              <ArrowUpRight size={15} />
            </button>
          </div>
          {!incidents.length ? (
            <p className="history-empty">Tus consultas van a aparecer acá.</p>
          ) : (
            incidents.slice(0, 7).map((item) => (
              <button
                key={item.id}
                className={`history-item ${incidentId === item.id ? "current" : ""}`}
                disabled={busy}
                onClick={() => navigate(active?.id, item.id)}
              >
                <MessageSquare size={14} />
                <span>{item.title}</span>
              </button>
            ))
          )}
        </div>
        <div className="sidebar-bottom">
          <div className="sidebar-note">
            <BookOpen size={18} />
            <div>
              <strong>Del manual a tu taller.</strong>
              <p>Fuentes a mano, en cada consulta.</p>
            </div>
          </div>
          <button
            className="vehicle-card"
            disabled={busy}
            onClick={() => setPanel("auto")}
          >
            <span className="vehicle-avatar">
              <CarFront size={20} />
            </span>
            <span>
              <strong>{active?.name || "Tu próximo proyecto"}</strong>
              <small>
                {active ? km(active.mileage) : "Agregá tu primer auto"}
              </small>
            </span>
            <ChevronRight size={15} />
          </button>
          <ThemePicker />
        </div>
      </aside>
      <div className="main-workspace">
        <header className="chat-header">
          <div className="page-breadcrumb">
            <span>Mi taller</span>
            <ChevronRight size={14} />
            <strong>Asistente</strong>
          </div>
          <div className="header-actions">
            <Badge variant="outline" className="local-badge">
              Espacio local
            </Badge>
            <Button
              variant="outline"
              size="sm"
              disabled={busy}
              onClick={() => setPanel("auto")}
            >
              <CarFront size={16} />
              <span>Mi auto</span>
            </Button>
          </div>
        </header>
        <main className="conversation" id="main-content" tabIndex={-1}>
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
              <p role="alert">
                No encontramos este auto. Elegí otro en Mi auto.
              </p>
            ) : loadingChat ? (
              <p role="status">Cargando conversación…</p>
            ) : !detail ? (
              <div className="welcome">
                <div className="welcome-eyebrow">
                  <span className="status-dot" /> TU COPILOTO DE MECÁNICA
                </div>
                <h1>
                  Conocé tu auto.
                  <br />
                  <span>Resolvé con confianza.</span>
                </h1>
                <p>
                  Un ruido nuevo, una duda o el próximo service.
                  <br className="desktop-break" /> Empezá por lo que notás. Lo
                  pensamos juntos.
                </p>
                {!active ? (
                  <Button onClick={() => open({ type: "vehicle" })}>
                    <Icon name="plus" size={17} /> Agregar mi auto
                  </Button>
                ) : (
                  <div className="suggestions">
                    {[
                      {
                        icon: <Gauge size={20} />,
                        title: "Algo no anda bien",
                        hint: "Ruidos, vibraciones o pérdida de potencia",
                        prompt:
                          "Noto un ruido extraño en el auto. ¿Qué datos necesitás para orientarme?",
                      },
                      {
                        icon: <Icon name="tool" size={20} />,
                        title: "Planificar un service",
                        hint: "Prepará el próximo mantenimiento",
                        prompt:
                          "Quiero planificar el próximo mantenimiento. ¿Qué información necesitás de mi auto?",
                      },
                      {
                        icon: <CircleHelp size={20} />,
                        title: "Entender mi auto",
                        hint: "Consultá una pieza o un procedimiento",
                        prompt:
                          "Quiero entender mejor un componente de mi auto. ¿Podés ayudarme a encontrarlo en el manual?",
                      },
                    ].map((item) => (
                      <button
                        key={item.title}
                        className="suggestion"
                        onClick={() => {
                          setDraft(item.prompt);
                          composer.current?.focus();
                        }}
                      >
                        <span className="suggestion-icon">{item.icon}</span>
                        <strong>{item.title}</strong>
                        <span>{item.hint}</span>
                        <ArrowUpRight className="suggestion-arrow" size={16} />
                      </button>
                    ))}
                  </div>
                )}
                <div className="welcome-footnote">
                  <BookOpen size={14} /> Contexto de tu auto · Historial de
                  trabajos · Fuentes documentales
                </div>
              </div>
            ) : (
              <div className="messages" aria-label="Conversación">
                <div className="conversation-date">
                  {date(detail.created_at)}
                </div>
                {messages[0]?.content !== detail.description && (
                  <div className="user-message">
                    <span>Registro anterior</span>
                    <p>{detail.description}</p>
                  </div>
                )}
                {messages.map((message) => (
                  <Fragment key={message.id}>
                    <div className="user-message">
                      <span>Vos</span>
                      <p>{message.content}</p>
                    </div>
                    {replies
                      .filter((r) => r.message_id === message.id)
                      .map((reply) => (
                        <AssistantMessage
                          key={reply.message_id}
                          reply={reply}
                        />
                      ))}
                  </Fragment>
                ))}
                {replyBusy && (
                  <p role="status" className="thinking">
                    WrenchAI está preparando una respuesta…
                  </p>
                )}
                {!replyBusy &&
                  messages.length > 0 &&
                  !replies.some(
                    (r) => r.message_id === messages[messages.length - 1].id,
                  ) && (
                    <button
                      className="quiet"
                      disabled={busy}
                      onClick={() =>
                        void retryReply(messages[messages.length - 1])
                      }
                    >
                      Generar respuesta
                    </button>
                  )}
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
                    onClick={() =>
                      open({ type: "task", item: detail, complete: true })
                    }
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
              {!assistantStatus
                ? "No se pudo comprobar la disponibilidad del asistente."
                : !assistantStatus.configured
                  ? "Falta configurar Gemini. Tus mensajes se guardan; podrás generar las respuestas cuando esté conectado."
                  : !assistantStatus.corpus_valid
                    ? "La configuración documental necesita revisión."
                    : assistantStatus.manual_library?.available &&
                        active?.manual_reference
                      ? `${assistantStatus.manual_library.pages} páginas disponibles en ${assistantStatus.manual_library.manuals} manuales. Consultamos los temas pertinentes${assistantStatus.web_search ? " y buscamos documentación del fabricante cuando falta información" : ""}.`
                      : assistantStatus.approved_passages === 0
                        ? "Gemini configurado. Aún no hay manuales habilitados: las respuestas serán orientación general, sin búsqueda web."
                        : active?.manual_reference
                          ? "Consultamos los manuales del Gol de fábrica. Gemini tiene en cuenta tus modificaciones; las fuentes utilizadas aparecen en cada respuesta."
                          : "Gemini configurado. Las fuentes compatibles utilizadas aparecen junto a cada respuesta."}
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
                rows={1}
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
              <div className="composer-actions">
                <span className="composer-context">
                  <Icon name="wrench" size={14} /> Asistente de mecánica
                </span>
                <label className="model-picker">
                  <select
                    aria-label="Modelo de IA"
                    value={effectiveModel || ""}
                    disabled={busy || replyBusy || !modelOptions.length}
                    onChange={(event) => {
                      setChosenModel(event.target.value);
                      try {
                        localStorage.setItem(
                          "wrenchai.model",
                          event.target.value,
                        );
                      } catch {
                        /* optional preference */
                      }
                    }}
                  >
                    {!modelOptions.length && (
                      <option value="">Cargando modelos…</option>
                    )}
                    {modelOptions.map((model) => (
                      <option key={model.id} value={model.id}>
                        {model.label.split(" · ")[0]}
                      </option>
                    ))}
                  </select>
                </label>
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
              </div>
            </form>
            <p className="composer-hint">
              La orientación del asistente no reemplaza una revisión
              profesional. · Enter para enviar
            </p>
          </div>
        </main>
      </div>
      {panel && (
        <Modal
          title="Mi auto"
          wide={panel === "tasks"}
          close={() => {
            if (!busy) setPanel(null);
          }}
        >
          <nav className="menu-tabs" aria-label="Información del auto">
            {(
              [
                ["auto", "Datos"],
                ["tasks", "To-do"],
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
                    <dt>Marca</dt>
                    <dd>{active.make || "Sin completar"}</dd>
                    <dt>Modelo</dt>
                    <dd>{active.model || "Sin completar"}</dd>
                    <dt>Año</dt>
                    <dd>{active.year ?? "Sin completar"}</dd>
                    <dt>Kilometraje</dt>
                    <dd>{km(active.mileage)}</dd>
                    <dt>Modificaciones</dt>
                    <dd>
                      {active.modifications ||
                        "Todavía no registraste modificaciones."}
                    </dd>
                    <dt>Referencia documental</dt>
                    <dd>
                      {active.manual_reference
                        ? "Gol G2 1.6 MI 1998 de fábrica"
                        : "Datos registrados del vehículo"}
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
              {panel === "tasks" && (
                <>
                  <p className="muted">
                    Pendientes arriba, trabajos completados abajo. Marcá el
                    check cuando termines.
                  </p>
                  <button
                    className="primary"
                    disabled={!active || busy}
                    onClick={() => open({ type: "task" })}
                  >
                    Agregar to-do
                  </button>
                </>
              )}
              {notice && (
                <p role="alert" className="form-error">
                  {notice}
                </p>
              )}
              {loadingChat ? (
                <p role="status">Cargando…</p>
              ) : error ? (
                <p role="alert">{error}</p>
              ) : !list.length ? (
                <p className="empty-list">
                  {panel === "tasks"
                    ? "Todavía no hay to-dos. Agregá uno o describí el problema en el chat."
                    : "Tu primera conversación empieza escribiendo en el chat."}
                </p>
              ) : panel === "tasks" ? (
                <TodoTable
                  items={list}
                  busy={busy}
                  toggle={toggle}
                  edit={(item) => open({ type: "task", item })}
                  chat={(item) => navigate(active?.id, item.id)}
                />
              ) : (
                <div className="record-list">
                  {list.map((item) => (
                    <button
                      key={item.id}
                      disabled={busy}
                      onClick={() => navigate(active?.id, item.id)}
                    >
                      <strong>{item.title}</strong>
                      <span>{date(item.created_at)}</span>
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
              : editor.type === "task"
                ? "Detalles del to-do"
                : "¿Cómo lo resolviste?"
          }
          close={() => {
            if (!busy) setEditor(null);
          }}
        >
          <form onSubmit={save}>
            {editor.type === "task" ? (
              <>
                <label>
                  Descripción del to-do
                  <input
                    name="title"
                    required
                    maxLength={160}
                    defaultValue={editor.item?.title}
                    placeholder="Por ejemplo, cambiar filtro de aire"
                  />
                </label>
                <label>
                  Detalles
                  <textarea
                    name="description"
                    required
                    rows={3}
                    maxLength={10000}
                    defaultValue={editor.item?.description}
                    placeholder="Qué querés hacer o qué problema hay"
                  />
                </label>
                <label className="check-label">
                  <input
                    type="checkbox"
                    name="completed"
                    defaultChecked={
                      editor.complete ?? editor.item?.status === "RESOLVED"
                    }
                  />
                  Trabajo completado
                </label>
                <label>
                  Qué se hizo y cómo quedó
                  <textarea
                    name="work_notes"
                    rows={3}
                    maxLength={10000}
                    defaultValue={
                      editor.item?.work_notes || editor.item?.resolution || ""
                    }
                    placeholder="Completá este detalle al marcar la tarea como hecha"
                  />
                </label>
                <div className="form-grid">
                  <label>
                    Fecha del trabajo
                    <input
                      name="performed_on"
                      type="date"
                      defaultValue={editor.item?.performed_on || ""}
                    />
                  </label>
                  <label>
                    Kilómetros al realizarlo
                    <input
                      name="work_mileage"
                      type="number"
                      min={0}
                      max={10000000}
                      step={1}
                      defaultValue={editor.item?.work_mileage ?? ""}
                    />
                  </label>
                  <label>
                    Costo pagado
                    <input
                      name="cost"
                      inputMode="decimal"
                      defaultValue={editor.item?.cost ?? ""}
                      placeholder="0,00"
                      pattern="[0-9]+([.,][0-9]{1,2})?"
                    />
                    <small>
                      Hasta 2 decimales. Usá la misma moneda en todos los ítems.
                    </small>
                  </label>
                </div>
              </>
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
