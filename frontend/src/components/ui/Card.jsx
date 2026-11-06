export default function Card({ as: Component = "div", interactive = false, className = "", children, ...props }) {
  return (
    <Component
      className={`rounded-2xl border border-line bg-surface shadow-card ${
        interactive ? "transition-all duration-300 hover:-translate-y-1 hover:border-primary/40 hover:shadow-pop hover:shadow-primary/10" : ""
      } ${className}`}
      {...props}
    >
      {children}
    </Component>
  )
}
