from .models import RegistroAuditoria


def registrar_accion(request, accion, objeto='', detalle=None, usuario=None):
    actor = usuario or getattr(request, 'user', None)
    username = actor.get_username() if actor and actor.is_authenticated else 'Anónimo'
    direccion_ip = request.META.get('REMOTE_ADDR') if request else None
    return RegistroAuditoria.objects.create(
        usuario=actor if actor and actor.is_authenticated else None,
        usuario_nombre=username,
        accion=accion,
        objeto=str(objeto)[:120],
        detalle=detalle or {},
        direccion_ip=direccion_ip,
    )