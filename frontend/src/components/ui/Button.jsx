// El destello (before:) recorre el botón al pasar el mouse.
const SHINE =
  "relative overflow-hidden before:pointer-events-none before:absolute before:inset-0 before:-translate-x-full before:bg-linear-to-r before:from-transparent before:via-white/30 before:to-transparent before:transition-transform before:duration-700 hover:before:translate-x-full"

const VARIANTS = {
  primary:
    `${SHINE} bg-primary text-white shadow-card shadow-primary/20 hover:-translate-y-0.5 hover:bg-primary-hover hover:shadow-lg hover:shadow-primary/30 active:translate-y-0 active:scale-[0.97] disabled:translate-y-0 disabled:bg-primary/50`,
  secondary:
    "border border-line bg-surface text-ink hover:-translate-y-0.5 hover:border-primary/40 hover:bg-surface-2 hover:shadow-card active:translate-y-0 active:scale-[0.97]",
  ghost: "text-ink-2 hover:bg-surface-2 hover:text-ink active:scale-[0.97]",
  danger: "bg-danger text-white hover:bg-danger/90 active:scale-[0.97]",
}

const SIZES = {
  sm: "min-h-9 px-3 text-sm gap-1.5",
  md: "min-h-11 px-4 text-sm gap-2",
  lg: "min-h-12 px-6 text-body gap-2",
  icon: "size-11 justify-center",
}

export default function Button({
  variant = "primary",
  size = "md",
  as: Component = "button",
  className = "",
  children,
  ...props
}) {
  return (
    <Component
      className={`inline-flex cursor-pointer items-center justify-center rounded-lg font-semibold transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-60 ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
      {...(Component === "button" && !props.type ? { type: "button" } : {})}
      {...props}
    >
      {children}
    </Component>
  )
}
