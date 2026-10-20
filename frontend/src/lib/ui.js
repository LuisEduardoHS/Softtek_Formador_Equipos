export const NIVELES = [
  ["basico", "Básico"],
  ["intermedio", "Intermedio"],
  ["avanzado", "Avanzado"],
]

// Clases compartidas para inputs, selects y textareas
export const inputCls = (error) =>
  `w-full min-h-11 rounded-lg border bg-surface px-3 text-sm text-ink outline-none transition-shadow placeholder:text-ink-2 focus:ring-3 ${
    error ? "border-danger focus:ring-danger/15" : "border-line focus:border-primary focus:ring-primary/15"
  }`
