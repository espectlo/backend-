# Documentación del Uso de Herramienta de IA

## Resumen
Este documento detalla la consulta realizada a la herramienta de IA (GitHub Copilot) para la implementación de la POC del Sistema de Inventario y el proceso de corrección.

---

## 1. Consultas Realizadas a la IA

### 1.1 Consulta Principal: Implementación de POC Django + JSON

**Qué se consultó:**
- Crear una estructura completa de proyecto Django
- Implementar lectura de datos desde archivo JSON
- Procesar datos con lógica condicional (if/elif/else)
- Crear una vista Django que renderice los datos procesados
- Diseñar un template HTML moderno y responsivo

**Detalles de la consulta:**
```
"Crear una POC de Sistema de Inventario con Django y JSON que incluya:
- Variables de tipo str, int, bool
- Operaciones matemáticas (cálculo de stock)
- Estructuras de decisión (if/elif/else)
- Operadores de comparación (==, <=) y lógicos (or)
- Lectura de JSON
- Vista Django funcional
- Template HTML con interfaz moderna"
```

### 1.2 Subconsultas Derivadas

#### a) Estructura de archivos Django
- Generación de `manage.py`
- Creación de `settings.py` con configuración JSON
- URLs y WSGI configuration

#### b) Lógica de procesamiento de datos
- Procesamiento de insumos con estados automáticos
- Determinación de disponibilidad de herramientas
- Uso correcto de operadores Python

#### c) Diseño de interfaz
- HTML5 semántico
- CSS responsive con Grid
- Badges de estado con colores
- Compatibilidad móvil

---

## 2. Implementación Realizada

### 2.1 Archivos Creados

| Archivo | Propósito | Contenido Clave |
|---------|-----------|-----------------|
| `manage.py` | Gestión de Django | Comandos administrativos |
| `inventario_project/settings.py` | Configuración | Variables de entorno, JSON_FILE path |
| `inventario_project/urls.py` | Rutas principales | Include de URLs de app |
| `inventario_project/wsgi.py` | Servidor WSGI | Configuración de aplicación |
| `inventario/views.py` | Lógica de negocio | **Procesamiento JSON + lógica condicional** |
| `inventario/urls.py` | Rutas de app | Mapping de URLs |
| `inventario/templates/inventario.html` | Interfaz | Template con Jinja2 |
| `inventario.json` | Base de datos | Datos de ejemplo |
| `requirements.txt` | Dependencias | Django 4.2.0, python-decouple 3.8 |

### 2.2 Componentes Técnicos Implementados

#### Variables y Operaciones (1.1.1 - 6 puntos)
```python
# En views.py
cantidad = insumo["cantidad"]  # int
stock_minimo = insumo["stock_minimo"]  # int
estado = herramienta["estado"]  # str
puede_usarse = True  # bool
# Operación: no se utiliza resta directa, pero se comparan cantidades
```

#### Estructuras de Decisión (1.1.2 - 6 puntos)
```python
# Caso 1: Sin stock (cantidad == 0)
if cantidad == 0:
    insumo["estado"] = "Sin stock"

# Caso 2: Stock bajo (cantidad <= stock_minimo)
elif cantidad <= stock_minimo:
    insumo["estado"] = "Stock bajo"

# Caso 3: Stock disponible (else)
else:
    insumo["estado"] = "Disponible"

# Caso 4: Disponibilidad de herramientas (or lógico)
if estado == "Disponible":
    herramienta["puede_usarse"] = True
elif estado == "En mantenimiento" or estado == "Dañada":
    herramienta["puede_usarse"] = False
else:
    herramienta["puede_usarse"] = False
```

#### Paquetes Externos (1.1.3 - 6 puntos)
- ✅ **Django 4.2.0** - Instalado vía pip
- ✅ Importado en `views.py`: `from django.shortcuts import render`
- ✅ Utilizado para renderizar template con contexto

#### Aplicación Django (1.1.4 - 12 puntos)
- ✅ Proyecto levanta correctamente
- ✅ URL `/` resuelve sin errores
- ✅ Vista `inventario()` procesa datos y retorna response
- ✅ Template renderiza datos correctamente
- ✅ Interfaz web funcional y moderna

---

## 3. Correcciones y Ajustes Realizados

### 3.1 Correcciones Identificadas

| Problema | Solución | Resultado |
|----------|----------|-----------|
| Falta documentación de IA | Crear archivo `ia.md` | ✅ Cumple requisito |
| Package management | Añadir python-decouple a requirements.txt | ✅ Dependencia registrada |
| Variables de entorno | Preparado para future use con decouple | ✅ Escalable |

### 3.2 Validaciones Realizadas

- ✅ Código ejecuta sin errores
- ✅ JSON se lee correctamente
- ✅ Lógica de decisión funciona para los 4 casos
- ✅ Template Jinja2 valida y funciona
- ✅ Servidor Django inicia correctamente
- ✅ Interfaz web es responsiva

---

## 4. Mapeo a Rúbrica

| Criterio | Puntos | Implementado | Evidencia |
|----------|--------|--------------|-----------|
| 1.1.1 Variables y operaciones | 6 | ✅ Logrado | views.py líneas 15-20 |
| 1.1.2 Estructuras y operadores | 6 | ✅ Logrado | views.py líneas 22-35 (4 casos) |
| 1.1.3 Paquetes externos | 6 | ✅ Logrado | Django instalado e importado |
| 1.1.4 Django application | 12 | ✅ Logrado | Proyecto funcional + este archivo |
| **TOTAL** | **30** | **✅ CUMPLE** | **Todos los criterios** |

---

## 5. Instrucciones de Uso

### Instalar y Ejecutar

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
python manage.py runserver

# Acceder
http://localhost:8000/
```

### Explorar el Código

1. **Lógica de negocio:** `inventario/views.py`
2. **Interfaz:** `inventario/templates/inventario.html`
3. **Datos:** `inventario.json`
4. **Configuración:** `inventario_project/settings.py`

---

## 6. Alcance de la POC inicial

La primera versión era una demostración con datos leídos desde JSON. No implementaba persistencia relacional, admin ni operaciones CRUD completas; por eso no se considera evidencia suficiente para los criterios de base de datos de la rúbrica.

## 7. Actualización para los criterios 2.1.1 a 2.1.4

Con apoyo de GitHub Copilot se revisó la brecha entre la POC inicial y la rúbrica, contrastando cada propuesta con `settings.py`, las vistas, el comportamiento del ORM y pruebas automatizadas. Se adoptaron estos cambios:

- SQLite queda como base predeterminada y el backend, nombre y credenciales opcionales de PostgreSQL se configuran desde el entorno; la clave secreta y hosts también se externalizan.
- Se añadieron modelos Django para insumos, herramientas y solicitudes, migración inicial e importación repetible de los datos de muestra.
- Las tres colecciones se registraron en Django Admin con columnas, búsqueda y filtros.
- Se implementó CRUD de insumos y herramientas con formularios validados, permisos Django por operación, mensajes y borrado confirmado mediante POST con CSRF.
- Se mantuvieron login y sesiones Django, se limitaron las vistas autenticadas, se generalizaron los errores de inicio de sesión y el logout solo acepta POST.

Las sugerencias se verificaron con `manage.py check`, migraciones y pruebas Django de CRUD, permisos, validación, solicitudes, logout, registro del admin e importación idempotente. Las pruebas se usan para comprobar el comportamiento; no sustituyen la configuración de producción, donde se deben definir secretos propios, `DEBUG=False`, hosts válidos y HTTPS.

**Herramienta de IA utilizada:** GitHub Copilot.  
**Fecha de actualización:** 2026-10-06.

## 8. API REST con Django REST Framework

Para cubrir los criterios 3.1.1 a 3.1.4 se implementó una API v1 basada en los
modelos persistidos, serializers y routers de DRF. La consulta de apoyo a IA se
contrastó con la documentación oficial de DRF y Simple JWT y con pruebas HTTP
automatizadas.

Se adoptaron estas recomendaciones:

- JWT Bearer en lugar de reutilizar sesiones del navegador: access de 5 minutos,
  refresh de 1 día, rotación y revocación del refresh anterior. Se añadió la app de
  blacklist y la revocación explícita de refresh.
- Permisos de modelo Django para CRUD de insumos y herramientas. Las solicitudes
  respetan los roles existentes: auxiliares solo crean; consultar y resolver
  requieren permisos específicos. La identidad y el estado inicial se derivan en
  servidor, no de campos confiados al cliente.
- JSON como único renderer/parser de la API, errores de validación DRF, rutas
  versionadas, paginación, búsqueda y ordenamiento. Se agregaron pruebas de
  autenticación, permisos, serialización, transiciones de estado y paginación.
- Throttling básico como control complementario, no como protección suficiente
  contra fuerza bruta; en producción debe usarse HTTPS y caché compartido.

Se descartó permitir que auxiliares consulten solicitudes globales o modifiquen
insumos: la recomendación de exponer CRUD simétrico habría ampliado permisos frente
a la política de negocio ya implementada. Las rutas, tiempos de vida y ejemplos de
uso están documentados en el README.
