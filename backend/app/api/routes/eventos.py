from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.models.evento import Evento
from app.models.participante import ParticipanteEvento
from app.models.usuario import Usuario
from app.schemas.evento import EventoCreate, EventoOut, EventoUpdate

router = APIRouter(prefix="/eventos", tags=["Eventos y Convocatorias"])


def _evento_con_nombre_creador(evento: Evento, nombre_creador: str, participantes=None):
    datos = {
        columna.name: getattr(evento, columna.name)
        for columna in Evento.__table__.columns
    }
    datos["creador_nombre"] = nombre_creador
    if participantes is not None:
        asignaciones = {
            participante.rol.strip().casefold(): str(participante.id_usuario)
            for participante in participantes
            if participante.rol
        }
        detalles = dict(datos["detalles_especificos"] or {})
        requisitos = dict(datos["requisitos_ia"] or {})
        roles = detalles.get("roles")
        if not isinstance(roles, list):
            roles = requisitos.get("roles", [])
        if isinstance(roles, list):
            roles_actualizados = []
            for rol in roles:
                if not isinstance(rol, dict):
                    roles_actualizados.append(rol)
                    continue
                nombre_rol = rol.get("nombre")
                id_integrante = (
                    asignaciones.get(nombre_rol.strip().casefold())
                    if isinstance(nombre_rol, str) else None
                )
                roles_actualizados.append({
                    **rol,
                    "cubiertoPor": id_integrante or rol.get("cubiertoPor"),
                })
            detalles["roles"] = roles_actualizados
            requisitos["roles"] = roles_actualizados
            datos["detalles_especificos"] = detalles
            datos["requisitos_ia"] = requisitos
    return datos


@router.post("/", response_model=EventoOut, status_code=status.HTTP_201_CREATED)
def crear_evento(evento: EventoCreate, db: Session = Depends(get_db)):
    creador = db.query(Usuario).filter(Usuario.id_usuario == evento.creador_id).first()
    if not creador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario creador especificado no existe."
        )

    nuevo_evento = Evento(
        creador_id=evento.creador_id,
        titulo=evento.titulo,
        categoria_principal=evento.categoria_principal,
        descripcion_libre=evento.descripcion_libre,
        detalles_especificos=evento.detalles_especificos or {},
        requisitos_ia=evento.requisitos_ia or {},
        embedding_requisitos={}
    )

    db.add(nuevo_evento)
    db.commit()
    db.refresh(nuevo_evento)
    return _evento_con_nombre_creador(nuevo_evento, creador.nombre)


@router.get("/", response_model=List[EventoOut])
def listar_eventos(
    categoria_principal: Optional[str] = Query(None, description="Filtrar por categoría (ej. Academico, Deportivo, Social, Hackathon)"),
    estado: Optional[str] = Query(None, description="Filtrar por estado (ej. Abierto, Finalizado)"),
    db: Session = Depends(get_db)
):
    query = db.query(Evento, Usuario.nombre).join(
        Usuario, Usuario.id_usuario == Evento.creador_id
    )
    if categoria_principal:
        query = query.filter(Evento.categoria_principal == categoria_principal)
    if estado:
        query = query.filter(Evento.estado == estado)
    
    return [
        _evento_con_nombre_creador(evento, nombre_creador)
        for evento, nombre_creador in query.all()
    ]


@router.get("/{id_evento}", response_model=EventoOut)
def obtener_evento(id_evento: int, db: Session = Depends(get_db)):
    resultado = db.query(Evento, Usuario.nombre).join(
        Usuario, Usuario.id_usuario == Evento.creador_id
    ).filter(Evento.id_evento == id_evento).first()
    if not resultado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado."
        )
    evento, nombre_creador = resultado
    participantes = db.query(ParticipanteEvento).filter(
        ParticipanteEvento.id_evento == id_evento
    ).all()
    return _evento_con_nombre_creador(evento, nombre_creador, participantes)


@router.put("/{id_evento}", response_model=EventoOut)
def actualizar_evento(
    id_evento: int,
    cambios: EventoUpdate,
    usuario_id: int,
    db: Session = Depends(get_db),
):
    evento = db.query(Evento).filter(Evento.id_evento == id_evento).first()
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado.",
        )
    if evento.creador_id != usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo quien creó el evento puede editarlo.",
        )
    if cambios.categoria_principal not in {"Academico", "Personal"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El tipo de proyecto no es válido.",
        )

    participantes = db.query(ParticipanteEvento).filter(
        ParticipanteEvento.id_evento == id_evento
    ).all()
    if len(participantes) + 1 > cambios.integrantes:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El número de integrantes no puede ser menor que las personas que ya forman parte del equipo.",
        )

    detalles = dict(cambios.detalles_especificos)
    requisitos = dict(cambios.requisitos_ia)
    roles = detalles.get("roles")
    if not isinstance(roles, list):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La lista de roles no es válida.",
        )
    if any(
        not isinstance(rol, dict)
        or not isinstance(rol.get("nombre"), str)
        or not rol["nombre"].strip()
        for rol in roles
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cada rol debe tener un nombre válido.",
        )
    roles_por_nombre = {
        rol["nombre"].strip().casefold()
        for rol in roles
    }
    roles_asignados = {participante.rol.strip().casefold() for participante in participantes if participante.rol}
    roles_eliminados = roles_asignados - roles_por_nombre
    if roles_eliminados:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No puedes quitar un rol que ya tiene un integrante asignado.",
        )

    detalles["tipo"] = "personal" if cambios.categoria_principal == "Personal" else "academico"
    detalles["integrantes"] = cambios.integrantes
    detalles["fechaLimite"] = detalles.get("fechaLimite") or None
    requisitos["roles"] = roles

    evento.categoria_principal = cambios.categoria_principal
    evento.descripcion_libre = cambios.descripcion_libre
    evento.detalles_especificos = detalles
    evento.requisitos_ia = requisitos
    db.commit()
    db.refresh(evento)

    creador = db.query(Usuario).filter(Usuario.id_usuario == evento.creador_id).first()
    if not creador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No encontramos a la persona creadora del evento.",
        )
    return _evento_con_nombre_creador(evento, creador.nombre)