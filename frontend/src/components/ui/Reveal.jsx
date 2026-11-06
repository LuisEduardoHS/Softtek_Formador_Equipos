import useInView from "../../hooks/useInView"

/**
 * Aparición animada al hacer scroll.
 * - from: "up" | "left" | "right" | "zoom"
 * - delay: retraso en ms (útil para escalonar elementos de una lista)
 */
export default function Reveal({ as: Component = "div", from = "up", delay = 0, className = "", style, children, ...props }) {
  const [ref, visible] = useInView()
  return (
    <Component
      ref={ref}
      data-from={from}
      className={`reveal ${visible ? "is-visible" : ""} ${className}`}
      style={{ "--reveal-delay": `${delay}ms`, ...style }}
      {...props}
    >
      {children}
    </Component>
  )
}
