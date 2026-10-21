import { useRef } from "react"
import { ChevronLeft, ChevronRight } from "lucide-react"

/**
 * Carrusel horizontal con scroll-snap. En táctil se desliza;
 * en escritorio muestra flechas.
 */
export default function Carousel({ label, children }) {
  const ref = useRef(null)
  const scroll = (dir) => {
    const el = ref.current
    el.scrollBy({ left: dir * el.clientWidth * 0.85, behavior: "smooth" })
  }

  return (
    <div className="relative" role="region" aria-roledescription="carrusel" aria-label={label}>
      <div
        ref={ref}
        className="-mx-4 flex snap-x snap-mandatory scroll-px-4 gap-4 overflow-x-auto px-4 pt-1 pb-3 [scrollbar-width:none] sm:mx-0 sm:scroll-px-0 sm:px-0 [&::-webkit-scrollbar]:hidden"
      >
        {children}
      </div>
      <div className="mt-3 hidden justify-end gap-2 sm:flex">
        <ArrowButton onClick={() => scroll(-1)} label="Anterior">
          <ChevronLeft className="size-5" />
        </ArrowButton>
        <ArrowButton onClick={() => scroll(1)} label="Siguiente">
          <ChevronRight className="size-5" />
        </ArrowButton>
      </div>
    </div>
  )
}

export function CarouselItem({ children }) {
  return <div className="w-[85%] max-w-[360px] shrink-0 snap-start sm:w-[340px]">{children}</div>
}

function ArrowButton({ onClick, label, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      className="grid size-10 cursor-pointer place-items-center rounded-full border border-line bg-surface text-ink shadow-card transition-colors hover:bg-surface-2"
    >
      <span aria-hidden="true">{children}</span>
    </button>
  )
}
