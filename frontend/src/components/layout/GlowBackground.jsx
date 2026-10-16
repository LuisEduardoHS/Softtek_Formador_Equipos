/**
 * Fondo con brillos azules en las esquinas (composición del diseño de Figma
 * «Crear tu cuenta»), adaptado a la paleta: tenue en modo claro y más
 * presente en modo oscuro.
 */
const GLOWS = [
  "-top-40 -left-40",
  "-top-40 -right-40",
  "-bottom-40 -right-40",
  "-bottom-40 -left-52",
]

export default function GlowBackground({ children, className = "" }) {
  return (
    <div className={`relative flex min-h-dvh flex-col overflow-hidden bg-canvas ${className}`}>
      <div aria-hidden="true" className="pointer-events-none absolute inset-0">
        {GLOWS.map((pos) => (
          <span
            key={pos}
            className={`absolute size-[26rem] rounded-full bg-primary/10 blur-[110px] dark:bg-primary/30 ${pos}`}
          />
        ))}
      </div>
      <div className="relative flex flex-1 flex-col">{children}</div>
    </div>
  )
}
