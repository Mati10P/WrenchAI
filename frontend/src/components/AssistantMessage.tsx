import type { Reply } from "../api";

export function AssistantMessage({ reply }: { reply: Reply }) {
  return (
    <article
      className={`assistant-message ${reply.safety_warning ? "safety-message" : ""}`}
    >
      <strong>
        {reply.safety_warning ? "Aviso de seguridad de WrenchAI" : "WrenchAI"}
      </strong>
      {!reply.safety_warning && (
        <small className="reply-model">{reply.model}</small>
      )}
      <p>{reply.content.summary}</p>
      {(
        [
          ["Posibles causas", reply.content.hypotheses],
          ["Para entender mejor", reply.content.questions],
          ["Observaciones sugeridas", reply.content.checks],
        ] as const
      ).map(
        ([title, items]) =>
          items.length > 0 && (
            <section key={title}>
              <h3>{title}</h3>
              <ul>
                {items.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            </section>
          ),
      )}
      {!reply.safety_warning && (
        <small>
          {reply.sources.length
            ? "Fuentes utilizadas"
            : "Sin respaldo documental recuperado. Orientación general; no confirma una causa ni que sea seguro circular."}
        </small>
      )}
      {reply.sources.map((source) => (
        <details className="source" key={source.id}>
          <summary>
            {source.title} ·{" "}
            {(source.pages?.length ?? 1) > 1 ? "páginas PDF" : "página PDF"}{" "}
            {(source.pages ?? [source.page]).join(", ")}
          </summary>
          <p>{source.text}</p>
          {source.language === "pt" && (
            <small>Texto original en portugués.</small>
          )}
          {source.scope && <p className="muted">Alcance: {source.scope}</p>}
        </details>
      ))}
    </article>
  );
}
