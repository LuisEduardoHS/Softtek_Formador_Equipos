
from pydantic import BaseModel, ConfigDict, Field, field_validator


class _CleanSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("*", mode="after")
    @classmethod
    def clean_lists(cls, value):
        if isinstance(value, list):
            cleaned = []
            seen = set()
            for item in value:
                item = " ".join(item.split())
                if item and item.casefold() not in seen:
                    cleaned.append(item)
                    seen.add(item.casefold())
            return cleaned
        return value


class StructuredProfile(_CleanSchema):
    habilidades: list[str] = Field(
        default_factory=list,
        description="Habilidades que el usuario afirma tener."
    )

    intereses: list[str] = Field(
        default_factory=list,
        description="Temas o actividades de interés."
    )

    areas_mejora: list[str] = Field(
        default_factory=list,
        description="Conocimientos que desea desarrollar."
    )

    experiencia: list[str] = Field(
        default_factory=list,
        description="Experiencias mencionadas explícitamente."
    )

    resumen_publico: str = Field(
        description="Resumen breve y fiel al perfil del usuario."
    )


class StructuredEventRequirements(_CleanSchema):
    categoria: str | None = Field(default=None, description="Categoría explícita o proporcionada por la aplicación.")
    titulo_normalizado: str = Field(default="", description="Título corto basado solo en la publicación.")
    resumen: str = Field(default="", description="Resumen fiel de lo que el equipo busca.")
    habilidades_obligatorias: list[str] = Field(default_factory=list, description="Capacidades exigidas al candidato; 'imprescindible' y 'necesitamos saber' van aquí, no en restricciones.")
    habilidades_deseables: list[str] = Field(default_factory=list, description="Capacidades valoradas pero opcionales; 'se valora' e 'ideal' van aquí.")
    roles_buscados: list[str] = Field(default_factory=list, description="Funciones o posiciones que faltan y se buscan; nunca integrantes ya presentes.")
    intereses_relacionados: list[str] = Field(default_factory=list, description="Temas o actividades relevantes sin afirmar habilidad.")
    restricciones_explicitas: list[str] = Field(default_factory=list, description="Condiciones logísticas o de participación declaradas, como lugar u horario; no habilidades.")
