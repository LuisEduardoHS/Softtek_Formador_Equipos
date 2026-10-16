export default function Card({ as: Component = "div", interactive = false, className = "", children, ...props }) {
  return (
    <Component
      className={`rounded-2xl border border-line bg-surface shadow-card ${
        interactive ? "transition-all duration-200 hover:-translate-y-0.5 hover:shadow-pop" : ""
      } ${className}`}
      {...props}
    >
      {children}
    </Component>
  )
}
