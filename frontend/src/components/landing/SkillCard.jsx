import Avatar from "../ui/Avatar"
import SkillChip from "../ui/SkillChip"

export default function SkillCard({ name, role, skills }) {
  return (
    <article className="flex h-full flex-col gap-4 rounded-2xl border border-line bg-surface p-5 shadow-card transition-all duration-200 hover:-translate-y-0.5 hover:shadow-pop">
      <div className="flex items-center gap-3">
        <Avatar name={name} size="lg" />
        <div className="min-w-0">
          <h3 className="truncate font-semibold text-ink">{name}</h3>
          <p className="truncate text-sm text-ink-2">{role}</p>
        </div>
      </div>
      <ul className="flex flex-wrap gap-1.5" aria-label={`Fortalezas de ${name}`}>
        {skills.map((skill) => (
          <li key={skill}>
            <SkillChip>{skill}</SkillChip>
          </li>
        ))}
      </ul>
    </article>
  )
}
