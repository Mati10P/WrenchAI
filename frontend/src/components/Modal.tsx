import { useEffect, useRef, useId } from "react";
import type { ReactNode } from "react";
import { Icon } from "./Icon";

export function Modal({
  title,
  children,
  close,
}: {
  title: string;
  children: ReactNode;
  close: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const headingId = useId();
  useEffect(() => {
    const dialog = ref.current!;
    dialog.showModal();
    dialog.querySelector<HTMLElement>("input, textarea, select")?.focus();
    return () => dialog.close();
  }, []);
  return (
    <dialog
      ref={ref}
      onCancel={(event) => {
        event.preventDefault();
        close();
      }}
      aria-labelledby={headingId}
    >
      <div className="modal-heading">
        <h2 id={headingId}>{title}</h2>
        <button
          className="icon-button"
          onClick={close}
          aria-label="Cerrar formulario"
        >
          <Icon name="close" />
        </button>
      </div>
      {children}
    </dialog>
  );
}
