
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.profile_data import Text150, Text200


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
    categoria: str | None = Field(default=None, max_length=50, description="Categoría explícita o proporcionada por la aplicación.")
    titulo_normalizado: str = Field(default="", max_length=150, description="Título corto basado solo en la publicación.")
    resumen: str = Field(default="", max_length=2000, description="Resumen fiel de lo que el equipo busca.")
    habilidades_obligatorias: list[Text150] = Field(default_factory=list, max_length=100, description="Capacidades exigidas al candidato; 'imprescindible' y 'necesitamos saber' van aquí, no en restricciones.")
    habilidades_deseables: list[Text150] = Field(default_factory=list, max_length=100, description="Capacidades valoradas pero opcionales; 'se valora' e 'ideal' van aquí.")
    roles_buscados: list[Text150] = Field(default_factory=list, max_length=100, description="Funciones o posiciones que faltan y se buscan; nunca integrantes ya presentes.")
    intereses_relacionados: list[Text200] = Field(default_factory=list, max_length=100, description="Temas o actividades relevantes sin afirmar habilidad.")
    restricciones_explicitas: list[Text200] = Field(default_factory=list, max_length=100, description="Condiciones logísticas o de participación declaradas, como lugar u horario; no habilidades.")
