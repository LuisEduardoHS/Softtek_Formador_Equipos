// Tonos sobrios y distinguibles; se asignan de forma estable a partir del nombre.
const TONES = [
  "bg-sky-100 text-sky-800",
  "bg-emerald-100 text-emerald-800",
  "bg-amber-100 text-amber-800",
  "bg-rose-100 text-rose-800",
  "bg-violet-100 text-violet-800",
  "bg-teal-100 text-teal-800",
  "bg-orange-100 text-orange-800",
  "bg-indigo-100 text-indigo-800",
]

const SIZES = { xs: "size-6 text-[10px]", sm: "size-8 text-xs", md: "size-10 text-sm", lg: "size-14 text-lg", xl: "size-20 text-2xl" }

function initials(name = "") {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0])
    .join("")
    .toUpperCase()
}

function toneFor(name = "") {
  let h = 0
  for (const c of name) h = (h * 31 + c.charCodeAt(0)) >>> 0
  return TONES[h % TONES.length]
}

export default function Avatar({ name, src, size = "md", ring = false, className = "" }) {
  if (src) {
    return (
      <img
        src={src}
        alt={name}
        className={`shrink-0 rounded-full object-cover ${SIZES[size]} ${ring ? "ring-2 ring-surface" : ""} ${className}`}
      />
    )
  }
  return (
    <span
      role="img"
      aria-label={name}
      className={`inline-grid shrink-0 place-items-center rounded-full font-semibold select-none ${toneFor(name)} ${SIZES[size]} ${
        ring ? "ring-2 ring-surface" : ""
      } ${className}`}
    >
      {initials(name)}
    </span>
  )
}

export function AvatarGroup({ names, max = 4, size = "sm" }) {
  const shown = names.slice(0, max)
  const rest = names.length - shown.length
  return (
    <div className="flex -space-x-2">
      {shown.map((n) => (
        <Avatar key={n} name={n} size={size} ring />
      ))}
      {rest > 0 && (
        <span className={`inline-grid place-items-center rounded-full bg-surface-2 font-semibold text-ink-2 ring-2 ring-surface ${SIZES[size]}`}>
          +{rest}
        </span>
      )}
    </div>
  )
}
