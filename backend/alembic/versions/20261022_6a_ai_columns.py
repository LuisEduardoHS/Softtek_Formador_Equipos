"""Add reviewed AI data and embedding provenance without rewriting existing rows.

Revision ID: 20261022_6a
Revises:
"""

from alembic import op
import sqlalchemy as sa

revision = "20261022_6a"
down_revision = None
branch_labels = None
depends_on = None


def _add_missing(table: str, columns: list[sa.Column]) -> None:
    existing = {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table)}
    for column in columns:
        if column.name not in existing:
            op.add_column(table, column)


def upgrade():
    _add_missing("perfiles_usuarios", [
        sa.Column("nombre_mostrar", sa.String(100)),
        sa.Column("resumen_publico_ia", sa.Text()),
        sa.Column("perfil_estructurado_ia", sa.JSON()),
        sa.Column("embedding_perfil", sa.JSON()),
        sa.Column("perfil_borrador_ia", sa.JSON()),
        sa.Column("perfil_estado_ia", sa.String(32)),
        sa.Column("perfil_fuente_revision", sa.String(64)),
        sa.Column("perfil_embedding_model", sa.String(100)),
        sa.Column("perfil_embedding_pipeline", sa.String(60)),
        sa.Column("perfil_embedding_fuente_revision", sa.String(64)),
        sa.Column("perfil_confirmado_at", sa.DateTime()),
        sa.Column("perfil_procesado_at", sa.DateTime()),
    ])
    _add_missing("eventos", [
        sa.Column("requisitos_borrador_ia", sa.JSON()),
        sa.Column("estado_ia", sa.String(32)),
        sa.Column("requisitos_fuente_revision", sa.String(64)),
        sa.Column("embedding_model", sa.String(100)),
        sa.Column("embedding_pipeline", sa.String(60)),
        sa.Column("embedding_fuente_revision", sa.String(64)),
        sa.Column("requisitos_confirmados_at", sa.DateTime()),
        sa.Column("procesado_at", sa.DateTime()),
    ])


def downgrade():
    raise RuntimeError("La reversión automática borraría datos IA; restaurar mediante un plan de respaldo.")
