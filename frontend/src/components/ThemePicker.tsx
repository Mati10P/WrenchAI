import { useEffect, useState } from "react";
import { Sun, Moon, Monitor } from "lucide-react";
import { Button } from "./ui/button";
type Theme = "light" | "dark" | "system";
export function ThemePicker() {
  const [theme, setTheme] = useState<Theme>(() => {
    try {
      const saved = localStorage.getItem("wrenchai.theme");
      return saved === "light" || saved === "dark" ? saved : "system";
    } catch {
      return "system";
    }
  });
  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const apply = () => {
      const dark = theme === "dark" || (theme === "system" && media.matches);
      document.documentElement.classList.toggle("dark", dark);
      document.documentElement.style.colorScheme = dark ? "dark" : "light";
    };
    apply();
    media.addEventListener("change", apply);
    try {
      localStorage.setItem("wrenchai.theme", theme);
    } catch {
      /* optional preference */
    }
    return () => media.removeEventListener("change", apply);
  }, [theme]);
  return (
    <div className="theme-picker">
      <span>Apariencia</span>
      <div role="group" aria-label="Tema de la interfaz">
        {(
          [
            { id: "light", label: "Claro", icon: Sun },
            { id: "dark", label: "Oscuro", icon: Moon },
            { id: "system", label: "Sistema", icon: Monitor },
          ] as const
        ).map(({ id, label, icon: Symbol }) => (
          <Button
            key={id}
            variant="ghost"
            size="icon"
            aria-label={label}
            aria-pressed={theme === id}
            title={label}
            onClick={() => setTheme(id)}
          >
            <Symbol size={15} />
          </Button>
        ))}
      </div>
    </div>
  );
}
