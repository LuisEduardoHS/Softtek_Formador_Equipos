import SkillCard from "./SkillCard"

export default function SkillShowcase({ profiles }) {
  return (
    <section id="estudiantes" className="mx-auto max-w-6xl scroll-mt-20 px-4 pb-20 sm:px-8">
      <div className="mb-8 max-w-2xl">
        <h2 className="text-h1 font-bold">Talento de todas las carreras</h2>
        <p className="mt-2 text-ink-2">Diseño, ingeniería, administración, psicología… Cada perfil suma algo que a otro equipo le falta.</p>
      </div>
      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {profiles.map((profile, i) => (
          <li key={profile.name} className="animate-fade-up" style={{ animationDelay: `${i * 60}ms` }}>
            <SkillCard {...profile} />
          </li>
        ))}
      </ul>
    </section>
  )
}
