export function Icon({
  name,
  size = 20,
}: {
  name:
    | "wrench"
    | "car"
    | "grid"
    | "plus"
    | "arrow"
    | "check"
    | "search"
    | "close"
    | "tool";
  size?: number;
}) {
  const paths = {
    wrench: (
      <>
        <path d="m14.6 6.4 3 3a6 6 0 0 1-7.2 7.2L5 22l-3-3 5.4-5.4a6 6 0 0 1 7.2-7.2Z" />
        <path d="m14.6 6.4 4-4 3 3-4 4" />
      </>
    ),
    car: (
      <>
        <path d="m5 7 2-4h10l2 4 2 3v8h-3v-3H6v3H3v-8Z" />
        <path d="M5 7h14M3 11h18M7 12v2m10-2v2" />
      </>
    ),
    grid: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </>
    ),
    plus: <path d="M12 5v14M5 12h14" />,
    arrow: <path d="m9 5 7 7-7 7" />,
    check: <path d="m5 12 4 4L19 6" />,
    search: (
      <>
        <circle cx="10" cy="10" r="6" />
        <path d="m15 15 5 5" />
      </>
    ),
    close: <path d="m6 6 12 12M18 6 6 18" />,
    tool: (
      <>
        <path d="m4 20 11-11m-4-5 9 9M14 2l8 8-5 5-8-8Z" />
        <path d="m2 18 4 4" />
      </>
    ),
  };
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  );
}
