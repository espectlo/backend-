from functools import wraps
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.views.decorators.http import require_POST
from django.core.serializers.json import DjangoJSONEncoder
from tabulate import tabulate
from .forms import HerramientaForm, InsumoForm
from .auditoria import registrar_accion
from .models import Herramienta, Insumo, RegistroAuditoria, Solicitud
import json


def auxiliar_requerido(view):
    @wraps(view)
    def wrapped_view(request, *args, **kwargs):
        if not request.user.groups.filter(name='Auxiliares').exists():
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapped_view


@login_required
def dashboard(request):
    """
    Vista del dashboard principal después de iniciar sesión.
    Muestra el menú de opciones: Insumos, Herramientas, Maquinaria y Solicitudes.
    """
    from datetime import date
    
    # Obtener la fecha actual formateada
    today = date.today()
    dia_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    fecha_formateada = f"{dia_semana[today.weekday()]} {today.day} de {['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'][today.month - 1]} de {today.year}"
    
    return render(
        request,
        'dashboard.html',
        {
            'current_date': fecha_formateada,
            'user': request.user,
            'es_auxiliar': request.user.groups.filter(name='Auxiliares').exists(),
        }
    )


@login_required
def vista_insumos(request):
    """
    Vista que muestra solo los INSUMOS.
    """
    registrar_accion(request, 'consultar_stock_insumos', 'Insumos')
    return render(
        request,
        "insumos.html",
        {
            "insumos": Insumo.objects.all()
        }
    )


@login_required
def vista_herramientas(request):
    """
    Vista que muestra solo las HERRAMIENTAS.
    """
    registrar_accion(request, 'consultar_stock_herramientas', 'Herramientas')
    return render(
        request,
        "herramientas.html",
        {
            "herramientas": Herramienta.objects.all()
        }
    )


@login_required
def inventario(request):
    """
    Vista principal que carga el inventario desde JSON,
    procesa los datos y los pasa al template.
    """
    
    insumos = Insumo.objects.all()
    herramientas = Herramienta.objects.all()
    registrar_accion(request, 'consultar_inventario', 'Inventario')

    # Generar tabla de insumos con tabulate
    tabla_insumos = tabulate(
        [
            {'nombre': item.nombre, 'cantidad': item.cantidad,
             'stock_minimo': item.stock_minimo, 'estado': item.estado}
            for item in insumos
        ],
        headers="keys",
        tablefmt="grid",
        showindex=False
    )

    # Pasar datos al template
    return render(
        request,
        "inventario.html",
        {
            "insumos": insumos,
            "herramientas": herramientas,
            "tabla_insumos": tabla_insumos
        }
    )


def login_view(request):
    """
    Vista de login que autentica usuarios.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # Validar que los campos no estén vacíos
        if not username:
            messages.error(request, '⚠️ Por favor ingresa tu usuario')
            return render(request, 'login.html')
        
        if not password:
            messages.error(request, '⚠️ Por favor ingresa tu contraseña')
            return render(request, 'login.html')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            registrar_accion(request, 'inicio_sesion', 'Sesión', usuario=user)
            messages.success(request, f'✅ ¡Bienvenido {username}!')
            return redirect('dashboard')
        else:
            registrar_accion(
                request,
                'fallo_inicio_sesion',
                username,
                {'usuario_intentado': username},
            )
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'login.html')


@require_POST
def logout_view(request):
    """
    Vista de logout que cierra la sesión del usuario.
    """
    if request.method == 'POST':
        registrar_accion(request, 'cierre_sesion', 'Sesión')
        logout(request)
        messages.success(request, '¡Sesión cerrada correctamente!')
    return redirect('login')


@login_required
@permission_required('inventario.add_solicitud', raise_exception=True)
@auxiliar_requerido
@require_POST
def solicitar_insumo(request):
    """
    Vista que maneja la solicitud de más cantidad de un insumo.
    """
    if request.method == 'POST':
        try:
            cantidad = int(request.POST.get('cantidad', '0'))
            insumo = get_object_or_404(Insumo, pk=request.POST.get('insumo_id'))
            if cantidad <= 0:
                raise ValueError
            solicitud = Solicitud.objects.create(
                usuario=request.user,
                usuario_nombre=request.user.get_username(),
                insumo=insumo,
                insumo_nombre=insumo.nombre,
                cantidad_solicitada=cantidad,
            )
            registrar_accion(
                request,
                'crear_solicitud',
                solicitud,
                {'insumo': insumo.nombre, 'cantidad': cantidad},
            )
            messages.success(request, f'Solicitud registrada: {cantidad} unidades de "{insumo.nombre}".')
        except (ValueError, TypeError):
            messages.error(request, 'La cantidad debe ser un número entero mayor que cero.')
    
    return redirect('inventario')


@login_required
@permission_required('inventario.view_solicitud', raise_exception=True)
def ver_solicitudes(request):
    """
    Vista que muestra todas las solicitudes realizadas.
    """
    registrar_accion(request, 'consultar_solicitudes', 'Solicitudes')
    solicitudes = Solicitud.objects.select_related('usuario', 'insumo')
    return render(
        request,
        'solicitudes.html',
        {
            'solicitudes': solicitudes,
            'total_solicitudes': solicitudes.count(),
            'solicitudes_pendientes': solicitudes.filter(
                estado=Solicitud.Estado.PENDIENTE
            ).count(),
            'puede_resolver': request.user.has_perm('inventario.change_solicitud'),
        }
    )


@login_required
@permission_required('inventario.change_solicitud', raise_exception=True)
@require_POST
def resolver_solicitud(request, pk):
    solicitud = get_object_or_404(Solicitud, pk=pk)
    estado = request.POST.get('estado')
    justificacion = request.POST.get('justificacion', '').strip()

    if solicitud.estado != Solicitud.Estado.PENDIENTE:
        messages.error(request, 'Esta solicitud ya fue resuelta.')
        return redirect('ver_solicitudes')

    if estado not in (Solicitud.Estado.APROBADA, Solicitud.Estado.RECHAZADA):
        messages.error(request, 'Selecciona aceptar o rechazar la solicitud.')
        return redirect('ver_solicitudes')

    antes = _snapshot(solicitud)
    solicitud.estado = estado
    solicitud.justificacion = justificacion
    try:
        solicitud.full_clean()
    except ValidationError as error:
        messages.error(request, error.message_dict.get(
            'justificacion', 'Debes escribir una justificación para resolver la solicitud.'
        ))
        return redirect('ver_solicitudes')

    solicitud.save(update_fields=['estado', 'justificacion'])
    accion = (
        'aprobar_solicitud'
        if estado == Solicitud.Estado.APROBADA
        else 'rechazar_solicitud'
    )
    registrar_accion(
        request,
        accion,
        solicitud,
        {'antes': antes, 'despues': _snapshot(solicitud)},
    )
    decision = 'aceptada' if estado == Solicitud.Estado.APROBADA else 'rechazada'
    messages.success(request, f'Solicitud {decision} y justificación registrada.')
    return redirect('ver_solicitudes')


@login_required
@permission_required('inventario.add_insumo', raise_exception=True)
def insumo_crear(request):
    return _guardar_formulario(request, InsumoForm(request.POST or None), 'vista_insumos')


@login_required
@permission_required('inventario.change_insumo', raise_exception=True)
def insumo_editar(request, pk):
    insumo = get_object_or_404(Insumo, pk=pk)
    return _guardar_formulario(
        request, InsumoForm(request.POST or None, instance=insumo), 'vista_insumos'
    )


@login_required
@permission_required('inventario.delete_insumo', raise_exception=True)
def insumo_eliminar(request, pk):
    return _eliminar(request, Insumo, pk, 'vista_insumos')


@login_required
@permission_required('inventario.add_herramienta', raise_exception=True)
def herramienta_crear(request):
    return _guardar_formulario(request, HerramientaForm(request.POST or None), 'vista_herramientas')


@login_required
@permission_required('inventario.change_herramienta', raise_exception=True)
def herramienta_editar(request, pk):
    herramienta = get_object_or_404(Herramienta, pk=pk)
    return _guardar_formulario(
        request, HerramientaForm(request.POST or None, instance=herramienta), 'vista_herramientas'
    )


@login_required
@permission_required('inventario.delete_herramienta', raise_exception=True)
def herramienta_eliminar(request, pk):
    return _eliminar(request, Herramienta, pk, 'vista_herramientas')


def _guardar_formulario(request, form, redirect_name):
    if request.method == 'POST' and form.is_valid():
        is_new = form.instance._state.adding
        previous = _snapshot(form.instance) if not is_new else None
        objeto = form.save()
        registrar_accion(
            request,
            'crear' if is_new else 'actualizar',
            objeto,
            {
                'antes': previous,
                'despues': _snapshot(objeto),
                'cambios': {
                    field: {'antes': form.initial.get(field), 'despues': form.cleaned_data[field]}
                    for field in form.changed_data
                },
            },
        )
        messages.success(request, 'Registro guardado correctamente.')
        return redirect(redirect_name)
    return render(
        request,
        'inventario/formulario.html',
        {'form': form, 'cancel_url': redirect_name},
    )


def _snapshot(obj):
    values = {
        field.name: field.value_from_object(obj)
        for field in obj._meta.concrete_fields
        if not field.primary_key
    }
    return json.loads(json.dumps(values, cls=DjangoJSONEncoder))


def _eliminar(request, model, pk, redirect_name):
    objeto = get_object_or_404(model, pk=pk)
    if request.method == 'POST':
        registrar_accion(
            request,
            'eliminar',
            objeto,
            {'registro': str(objeto)},
        )
        objeto.delete()
        messages.success(request, 'Registro eliminado correctamente.')
        return redirect(redirect_name)
    return render(
        request,
        'inventario/confirmar_eliminacion.html',
        {'objeto': objeto, 'cancel_url': redirect_name},
    )
