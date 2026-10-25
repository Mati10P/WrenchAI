import type { Reply } from "../api";
import { useState } from "react";

function sourceLabel(source: Reply["sources"][number]) {
  return source.evidence_kind === "verified_web_page"
    ? `${source.title} · Fuente web del fabricante`
    : `${source.title} · ${(source.pages?.length ?? 1) > 1 ? "páginas PDF" : "página PDF"} ${(source.pages ?? [source.page]).join(", ")}`;
}

function ManualFigure({
  figureId,
  caption,
  source,
  digest,
}: {
  figureId: string;
  caption: string;
  source: Reply["sources"][number];
  digest: string;
}) {
  const [failed, setFailed] = useState(false);
  const page = `/api/manual-pages/${encodeURIComponent(source.id)}`;
  return (
    <figure className="manual-figure">
      {failed ? (
        <p>
          La ilustración no está disponible. Podés consultar la página completa.
        </p>
      ) : (
        <a
          href={page}
          target="_blank"
          rel="noreferrer"
          aria-label={`Abrir página ${source.page} del manual`}
        >
          <img
            src={`/api/manual-figures/${encodeURIComponent(figureId)}?sha256=${encodeURIComponent(digest)}`}
            alt={caption}
            loading="lazy"
            onError={() => setFailed(true)}
          />
        </a>
      )}
      <figcaption>
        {caption}
        <br />
        <a href={page} target="_blank" rel="noreferrer">
          {source.title} · Ver página PDF {source.page}
        </a>
      </figcaption>
    </figure>
  );
}

export function AssistantMessage({ reply }: { reply: Reply }) {
  const groups = new Map<
    string,
    { source: Reply["sources"][number]; ids: string[] }
  >();
  for (const source of reply.sources) {
    const key = `${source.document?.id ?? source.title}:${(source.pages ?? [source.page]).join(",")}`;
    const group = groups.get(key);
    if (group) {
      group.ids.push(source.id);
      if (source.evidence_kind === "original_page_image") group.source = source;
    } else groups.set(key, { source, ids: [source.id] });
  }
  const references = [...groups.values()];
  const shownReferences = new Set<number>();
  return (
    <article
      className={`assistant-message ${reply.safety_warning ? "safety-message" : ""}`}
    >
      <strong>
        {reply.safety_warning ? "Aviso de seguridad de WrenchAI" : "WrenchAI"}
      </strong>
      {!reply.safety_warning && reply.model.startsWith("gemini-") && (
        <small className="reply-model">{reply.model}</small>
      )}
      {!reply.safety_warning && reply.content.blocks?.length ? (
        reply.content.blocks.map((block, index) => {
          if (block.type === "paragraph")
            return (
              <div className="answer-paragraph" key={index}>
                <p>{block.text}</p>
                {block.source_ids.map((id) => {
                  const reference = references.findIndex((r) =>
                    r.ids.includes(id),
                  );
                  if (reference < 0 || shownReferences.has(reference))
                    return null;
                  shownReferences.add(reference);
                  const source = references[reference].source;
                  return (
                    <a
                      className="paragraph-source"
                      key={id}
                      href={`#source-${reply.message_id}-${source.id}`}
                      aria-label={`Fuente ${reference + 1}: ${sourceLabel(source)}`}
                      title={sourceLabel(source)}
                      onClick={(event) => {
                        event.preventDefault();
                        const details = document.getElementById(
                          `source-${reply.message_id}-${source.id}`,
                        );
                        if (details instanceof HTMLDetailsElement) {
                          details.open = true;
                          details.scrollIntoView({
                            block: "nearest",
                            behavior: "smooth",
                          });
                        }
                      }}
                    >
                      [{reference + 1}]
                    </a>
                  );
                })}
              </div>
            );
          const source = reply.sources.find((s) =>
            s.figures?.some((f) => f.id === block.figure_id),
          );
          return source ? (
            <ManualFigure
              key={index}
              source={source}
              figureId={block.figure_id}
              digest={
                source.figures!.find((f) => f.id === block.figure_id)!
                  .image_sha256
              }
              caption={block.caption}
            />
          ) : null;
        })
      ) : (
        <p>{reply.content.summary}</p>
      )}
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
      {!reply.safety_warning &&
        (reply.sources.length > 0 || reply.model.startsWith("gemini-")) && (
          <small>
            {reply.sources.length
              ? "Fuentes utilizadas"
              : "Sin respaldo documental recuperado. Orientación general; no confirma una causa ni que sea seguro circular."}
          </small>
        )}
      {references.map(({ source }, index) => (
        <details
          className="source"
          key={source.id}
          id={`source-${reply.message_id}-${source.id}`}
        >
          <summary>
            [{index + 1}] {sourceLabel(source)}
          </summary>
          <p>{source.text}</p>
          {source.document && (
            <p className="muted">
              Documento: {source.document.title}
              {source.document.author
                ? ` · ${source.document.author}`
                : " · Autoría no verificada"}
            </p>
          )}
          {source.evidence_kind === "original_page_image" && (
            <a
              href={`/api/manual-pages/${encodeURIComponent(source.id)}`}
              target="_blank"
              rel="noreferrer"
            >
              Ver página original
            </a>
          )}
          {source.evidence_kind === "verified_web_page" &&
            source.url?.startsWith("https://") && (
              <p>
                <a href={source.url} target="_blank" rel="noreferrer">
                  Abrir fuente web consultada
                </a>
                {source.retrieved_at && (
                  <small>
                    {" "}
                    · Consultada el{" "}
                    {new Date(source.retrieved_at).toLocaleDateString("es-UY")}
                  </small>
                )}
              </p>
            )}
          {source.language === "pt" && (
            <small>Texto original en portugués.</small>
          )}
          {source.scope && <p className="muted">Alcance: {source.scope}</p>}
        </details>
      ))}
      {reply.sources.find((s) => s.search_suggestions)?.search_suggestions && (
        <iframe
          title="Sugerencias de búsqueda de Google"
          sandbox="allow-popups allow-popups-to-escape-sandbox"
          referrerPolicy="no-referrer"
          style={{ border: 0, width: "100%", height: 160 }}
          srcDoc={
            "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'; img-src https: data:;\">" +
            reply.sources.find((s) => s.search_suggestions)!.search_suggestions
          }
        />
      )}
    </article>
  );
}
