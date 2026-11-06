import { useEffect, useRef, useState } from "react"

const supported = typeof IntersectionObserver !== "undefined"

/** Devuelve [ref, visible]; visible pasa a true la primera vez que el elemento entra en pantalla. */
export default function useInView({ threshold = 0.15, rootMargin = "0px 0px -40px 0px" } = {}) {
  const ref = useRef(null)
  const [visible, setVisible] = useState(!supported)

  useEffect(() => {
    const el = ref.current
    if (!el || !supported) return undefined
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true)
          observer.disconnect()
        }
      },
      { threshold, rootMargin },
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [threshold, rootMargin])

  return [ref, visible]
}
