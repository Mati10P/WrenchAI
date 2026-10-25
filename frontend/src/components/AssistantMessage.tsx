import type { Reply } from "../api";
import { useState } from "react";

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
      {!reply.safety_warning && reply.content.blocks?.length ? (
        reply.content.blocks.map((block, index) => {
          if (block.type === "paragraph")
            return (
              <div className="answer-paragraph" key={index}>
                <p>{block.text}</p>
                {block.source_ids.map((id) => {
                  const source = reply.sources.find((s) => s.id === id);
                  if (!source) return null;
                  return (
                    <a
                      className="paragraph-source"
                      key={id}
                      href={
                        source.evidence_kind === "original_page_image"
                          ? `/api/manual-pages/${encodeURIComponent(id)}`
                          : `#source-${reply.message_id}-${id}`
                      }
                      target={
                        source.evidence_kind === "original_page_image"
                          ? "_blank"
                          : undefined
                      }
                      rel="noreferrer"
                    >
                      {source.evidence_kind === "original_page_image"
                        ? `Ver página PDF ${source.page}`
                        : `Fuente: ${source.title}`}
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
      {!reply.safety_warning && (
        <small>
          {reply.sources.length
            ? "Fuentes utilizadas"
            : "Sin respaldo documental recuperado. Orientación general; no confirma una causa ni que sea seguro circular."}
        </small>
      )}
      {reply.sources.map((source) => (
        <details
          className="source"
          key={source.id}
          id={`source-${reply.message_id}-${source.id}`}
        >
          <summary>
            {source.title} ·{" "}
            {(source.pages?.length ?? 1) > 1 ? "páginas PDF" : "página PDF"}{" "}
            {(source.pages ?? [source.page]).join(", ")}
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
          {source.language === "pt" && (
            <small>Texto original en portugués.</small>
          )}
          {source.scope && <p className="muted">Alcance: {source.scope}</p>}
        </details>
      ))}
    </article>
  );
}
