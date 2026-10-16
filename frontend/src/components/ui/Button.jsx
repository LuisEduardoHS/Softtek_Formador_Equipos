const VARIANTS = {
  primary:
    "bg-primary text-white shadow-card hover:bg-primary-hover active:scale-[0.98] disabled:bg-primary/50",
  secondary:
    "border border-line bg-surface text-ink hover:bg-surface-2 active:scale-[0.98]",
  ghost: "text-ink-2 hover:bg-surface-2 hover:text-ink",
  danger: "bg-danger text-white hover:bg-danger/90 active:scale-[0.98]",
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
      className={`inline-flex cursor-pointer items-center justify-center rounded-lg font-semibold transition-all duration-150 disabled:cursor-not-allowed disabled:opacity-60 ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
      {...(Component === "button" && !props.type ? { type: "button" } : {})}
      {...props}
    >
      {children}
    </Component>
  )
}
