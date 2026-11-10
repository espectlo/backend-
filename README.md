# Sistema de Inventario - Django y SQLite

**Autor:** Cristobal Rojas

Sistema de gestión de inventario con Django ORM y SQLite. El archivo `inventario.json` se conserva como fuente para cargar los datos de ejemplo.

## 📋 Requisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

## 🚀 Instalación y Ejecución

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar el entorno

```bash
copy .env.example .env
```

Edita `.env` y define una `SECRET_KEY` privada (puedes generarla con `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`). Para desarrollo, `DEBUG=True` y SQLite están configurados por defecto. En producción define `DEBUG=False`, una clave segura, `ALLOWED_HOSTS` y una base de datos disponible. SQLite no usa usuario ni contraseña; para PostgreSQL configura `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` y `DB_PORT`.

### 3. Crear esquema y cargar datos de ejemplo

```bash
python manage.py migrate
python manage.py importar_json
python manage.py createsuperuser
```

`importar_json` puede ejecutarse nuevamente sin duplicar insumos, herramientas ni el historial de solicitudes. El archivo `.env` y la base SQLite local no deben publicarse.

### 4. Ejecutar el servidor Django

```bash
python manage.py runserver
```

El servidor se iniciará en `http://localhost:8000/`

### 5. Acceder a la aplicación

Abre tu navegador web y ve a:
```
http://localhost:8000/
```

El administrador está disponible en `http://localhost:8000/admin/`. Inicia sesión con el superusuario creado anteriormente.

### Cuentas de prueba

| Cuenta | Usuario | Contraseña |
|---|---|---|
| Prueba 1 | `prueba1` | `123456` |
| Prueba 2 | `prueba2` |`  123456789 ` |
| Administrador | `admin` | ` 3410m2912` |

`prueba1 / 123456` es una credencial débil y debe usarse solo en una base local de pruebas; crea la cuenta `prueba1` si aún no existe. Las contraseñas actuales de `prueba2` y `admin` no se pueden recuperar desde Django ni se guardan en este README. Asígnalas o cámbialas de forma interactiva, sin poner la clave en el historial de comandos:

```bash
python manage.py changepassword prueba2
python manage.py changepassword admin
```

No reutilices estas cuentas ni contraseñas en producción.

### Permisos, roles y auditoría

Ejecuta `python manage.py configurar_roles` para crear el grupo `Auxiliares`, asignar a los usuarios existentes permisos de consulta de stock y creación de solicitudes, crear el superusuario `admin` e importar el historial de `accesos.json`. El comando es repetible. Auxiliares no puede editar stock ni consultar las solicitudes globales; solo el administrador ve y gestiona solicitudes.

Por seguridad, `admin` se crea sin contraseña utilizable. Configúrala localmente con `python manage.py changepassword admin`; no se almacena ni distribuye una clave compartida. El admin permite revisar el registro de auditoría, que guarda hora, usuario, IP, consultas de stock, login/logout, intentos fallidos, pedidos y cambios con valores anteriores/nuevos. `RegistroAuditoria` y el registro nativo de acciones de Django son de solo lectura para revisar quién modificó objetos, cuentas y grupos.

### Verificación

```bash
python manage.py check
python manage.py test inventario
```

### API REST (v1)

La API usa Django REST Framework con rutas versionadas por namespace, respuestas y
solicitudes JSON, paginación de 20 elementos (ajustable hasta 100), búsqueda y ordenamiento.
Los endpoints de recursos requieren JWT. Para obtener un par de tokens:

```http
POST /api/v1/auth/token/
Content-Type: application/json

{"username": "usuario", "password": "contraseña"}
```

Envía el token de acceso como `Authorization: Bearer <access>`. El access token dura
5 minutos; el refresh dura 1 día, rota al renovarse y el token anterior queda en
lista de bloqueo. Se puede renovar con `POST /api/v1/auth/token/refresh/` y revocar
un refresh token con `POST /api/v1/auth/token/blacklist/`, enviando `{"refresh": "..."}`.
Ejecuta `python manage.py migrate` para crear las tablas de lista de bloqueo.

| Recurso | Ruta | Acceso |
|---|---|---|
| Insumos | `/api/v1/insumos/` | Permisos Django `view/add/change/delete_insumo` |
| Herramientas | `/api/v1/herramientas/` | Permisos Django `view/add/change/delete_herramienta` |
| Solicitudes | `/api/v1/solicitudes/` | Auxiliares pueden crear; usuarios con permiso `view_solicitud` pueden consultar; `change_solicitud` permite resolver |

Los recursos de inventario implementan GET, POST, PUT, PATCH y DELETE. Las
solicitudes se crean como pendientes a nombre del usuario autenticado; no se aceptan
identidad, estado ni nombre de insumo enviados por el cliente. Un usuario con permiso
de cambio puede resolver una solicitud con PATCH del recurso o
`POST /api/v1/solicitudes/{id}/resolver/`, incluyendo estado `Aprobado` o `Rechazado`
y una justificación no vacía. Las listas usan `?search=...`, `?ordering=nombre` y
`?page=2`.

Los throttles configurados limitan el ritmo de peticiones, pero no sustituyen
controles especializados contra fuerza bruta. En producción, sirve la API sobre
HTTPS, protege las claves y configura un caché compartido para que el throttling se
aplique de forma consistente entre procesos.

La configuración sigue las guías oficiales de DRF para
[serializadores](https://www.django-rest-framework.org/api-guide/serializers/),
[routers](https://www.django-rest-framework.org/api-guide/routers/),
[permisos](https://www.django-rest-framework.org/api-guide/permissions/),
[paginación](https://www.django-rest-framework.org/api-guide/pagination/) y
[versionado](https://www.django-rest-framework.org/api-guide/versioning/), y la guía de
[Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/).

## 📁 Estructura del Proyecto

```
niu backend/
├── manage.py                           # Comando administrativo de Django
├── requirements.txt                    # Dependencias del proyecto
├── inventario.json                     # Datos de ejemplo para importar
│
├── inventario_project/                 # Configuración principal de Django
│   ├── __init__.py
│   ├── settings.py                     # Configuración de la aplicación
│   ├── urls.py                         # Rutas principales
│   ├── wsgi.py                         # Configuración WSGI
│   └── asgi.py                         # Configuración ASGI
│
└── inventario/                         # Aplicación principal
    ├── __init__.py
    ├── models.py                       # Colecciones persistidas con Django ORM
    ├── admin.py                        # Gestión administrativa de colecciones
    ├── views.py                        # Vistas autenticadas y operaciones CRUD
    ├── urls.py                         # Rutas de la aplicación
    └── templates/
        └── inventario.html             # Plantilla HTML (interfaz web)
```

## 🎯 Funcionalidades Implementadas

### Conceptos Programáticos Demostrando (POC):

✅ **Variables y operaciones**
- Variables de tipo string, int y boolean
- Operaciones matemáticas (resta para calcular stock)

✅ **Estructuras de decisión**
- `if`, `elif`, `else`
- Operadores de comparación: `==`, `<=`
- Operadores lógicos: `or`
- Bucles: `for`

✅ **Persistencia**
- Colecciones de insumos, herramientas y solicitudes almacenadas en SQLite
- Importación repetible de datos de ejemplo desde `inventario.json`

✅ **Framework Django**
- Vista (view) que procesa datos
- Ruta (URL) configurada
- Template HTML para visualización

### Funcionalidades de Negocio:

**Para Auxiliares:**
- Ver insumos disponibles
- Consultar cantidad de materiales
- Conocer estado del stock (Disponible, Stock bajo, Sin stock)
- Ver estado de herramientas
- Saber si una herramienta puede utilizarse

**Para Jefes:**
- Visualizar todo el inventario
- Ver información de mantenimientos y tratamientos

## 📊 Datos de Ejemplo

### Insumos
- Guantes (50 unidades)
- Mascarillas (5 unidades)
- Desinfectante (0 unidades)

### Herramientas
- Taladro (Disponible)
- Martillo (En mantenimiento)
- Destornillador (Dañada)

## 🔄 Flujo de Procesamiento

1. **Carga inicial:** `manage.py importar_json` lleva los datos de ejemplo del JSON a la base de datos
2. **Persistencia y procesamiento:**
   - Insumos: Se determina automáticamente si están "Sin stock", "Stock bajo" o "Disponibles"
   - Herramientas: Se determina si pueden utilizarse según su estado
3. **Visualización:** Los datos procesados se muestran en una interfaz web moderna

## 💾 Archivo JSON

El archivo `inventario.json` contiene:

```json
{
    "insumos": [
        {
            "id": 1,
            "nombre": "Producto",
            "cantidad": 50,
            "stock_minimo": 10
        }
    ],
    "herramientas": [
        {
            "id": 1,
            "nombre": "Herramienta",
            "estado": "Disponible",
            "tratamiento": "Ninguno"
        }
    ]
}
```

Puedes editar directamente este archivo para agregar más insumos o herramientas.

## 🎨 Interfaz Web

La aplicación cuenta con una interfaz moderna y responsive:
- Diseño en tarjetas (cards)
- Colores según estado (verde disponible, naranja bajo stock, rojo sin stock)
- Responsive para dispositivos móviles
- Badges informativos

## 📝 Notas

- El JSON se usa solo como fuente de datos inicial; las operaciones de la aplicación se guardan en la base relacional
- Antes de desplegar, usar `DEBUG=False`, HTTPS y variables de entorno con credenciales y una `SECRET_KEY` propia

## Evidencia de apoyo con IA

El archivo `ia.md` documenta las orientaciones de GitHub Copilot utilizadas y el contraste realizado con el código, las validaciones de Django y las pruebas automatizadas. Se ajustaron las sugerencias para proteger el cierre de sesión con POST, verificar permisos por modelo y evitar confiar en el nombre de insumo enviado por el navegador.


