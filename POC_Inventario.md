# Sistema de Inventario y Necesidades de Materiales

## 1. Planteamiento del problema

Actualmente, el personal de auxiliares no siempre tiene conocimiento de los insumos disponibles para realizar sus labores. Esto dificulta saber rápidamente qué materiales se encuentran disponibles y cuáles necesitan ser solicitados.

Además, existe poca claridad respecto al estado y tratamiento de las herramientas disponibles. Los auxiliares pueden no saber si una herramienta está disponible, en mantenimiento, dañada o qué tratamiento se le ha realizado.

Esta situación puede generar:

- Pérdida de tiempo al buscar información sobre materiales.
- Solicitudes innecesarias de insumos.
- Falta de control sobre las cantidades disponibles.
- Dificultades para conocer el estado de las herramientas.
- Falta de información sobre tratamientos y mantenimientos.
- Problemas de comunicación entre auxiliares y jefaturas.

Por lo tanto, se identifica la necesidad de contar con un sistema centralizado que permita consultar y administrar la información relacionada con los insumos y herramientas.

---

## 2. Solución propuesta

Se propone desarrollar un **sistema web de inventario y necesidades de materiales** utilizando **Python y Django**.

El sistema permitirá centralizar la información de los insumos y herramientas para que pueda ser consultada desde distintos computadores.

### Auxiliares

Los auxiliares podrán:

- Consultar los insumos disponibles.
- Ver las cantidades actuales.
- Saber si existe stock bajo.
- Consultar las herramientas disponibles.
- Ver el estado de las herramientas.
- Consultar los tratamientos o mantenimientos realizados.

### Jefes

Los jefes podrán:

- Consultar el inventario.
- Registrar nuevos insumos.
- Modificar cantidades.
- Registrar herramientas.
- Modificar el estado de una herramienta.
- Registrar tratamientos o mantenimientos.

### Arquitectura inicial

Para la prueba de concepto se utilizará un archivo JSON como almacenamiento:

```text
Django
   |
   v
JSON
   |
   +--------+
   |        |
   v        v
Insumos  Herramientas
```

Posteriormente, en la versión definitiva, el archivo JSON podrá ser reemplazado por una base de datos SQL:

```text
Django
   |
   v
Base de datos SQL
   |
   +-------------+-------------+
   |             |             |
Insumos     Herramientas   Solicitudes
```

---

## 3. Priorización MoSCoW

### Must Have — Debe tener

Estas funcionalidades son necesarias para que la solución cumpla con su objetivo principal.

| Funcionalidad | Descripción |
|---|---|
| Visualizar inventario | Permitir que los auxiliares consulten los materiales disponibles. |
| Consultar cantidad | Mostrar la cantidad disponible de cada insumo. |
| Registrar insumos | Permitir mantener un registro de los materiales existentes. |
| Registrar herramientas | Mantener información de las herramientas disponibles. |
| Consultar estado | Mostrar si una herramienta está disponible, dañada o en mantenimiento. |
| Registrar tratamiento | Permitir conocer el tratamiento o mantenimiento realizado a una herramienta. |
| Registrar entradas y salidas | Mantener actualizado el inventario. |
| Acceso web | Permitir consultar el sistema desde diferentes computadores. |

### Should Have — Debería tener

Son funcionalidades importantes, pero el sistema puede funcionar inicialmente sin ellas.

| Funcionalidad | Descripción |
|---|---|
| Solicitud de materiales | Permitir que los auxiliares soliciten insumos desde el sistema. |
| Historial de movimientos | Registrar las entradas y salidas realizadas. |
| Historial de mantenimiento | Mantener un historial de tratamientos realizados a cada herramienta. |
| Alertas de stock bajo | Avisar cuando un insumo llegue al stock mínimo. |
| Roles de usuario | Diferenciar las funciones de auxiliares y jefes. |

### Could Have — Podría tener

Son mejoras que pueden incorporarse posteriormente.

| Funcionalidad | Descripción |
|---|---|
| Reportes | Generar reportes del inventario y movimientos. |
| Exportación a Excel/PDF | Permitir descargar información del inventario. |
| Buscador | Facilitar la búsqueda de insumos y herramientas. |
| Código QR | Permitir consultar rápidamente la información de una herramienta. |

### Won't Have — No tendrá inicialmente

Estas funcionalidades quedan fuera del alcance de la primera versión.

| Funcionalidad | Motivo |
|---|---|
| Aplicación móvil | El sistema web permite cumplir inicialmente con el objetivo. |
| Notificaciones por WhatsApp/SMS | No son necesarias para validar la solución. |
| Inteligencia artificial | No es necesaria para resolver la problemática principal. |
| Integración con otros sistemas | Puede implementarse en futuras versiones. |

---

## 4. Prueba de Concepto (POC) con JSON

### 4.1. Objetivo de la POC

La prueba de concepto tiene como objetivo demostrar que es posible implementar una versión inicial del sistema utilizando Django y JSON, sin utilizar todavía una base de datos SQL.

La POC permitirá demostrar:

- Uso de variables.
- Operaciones matemáticas.
- Estructuras de decisión.
- Operadores de comparación y lógicos.
- Uso de Django.
- Lectura de información desde JSON.
- Visualización de la información mediante una página web.

### 4.2. Archivo `inventario.json`

La información será almacenada inicialmente en un archivo JSON.

```json
{
    "insumos": [
        {
            "id": 1,
            "nombre": "Guantes",
            "cantidad": 50,
            "stock_minimo": 10
        },
        {
            "id": 2,
            "nombre": "Mascarillas",
            "cantidad": 5,
            "stock_minimo": 10
        },
        {
            "id": 3,
            "nombre": "Desinfectante",
            "cantidad": 0,
            "stock_minimo": 5
        }
    ],
    "herramientas": [
        {
            "id": 1,
            "nombre": "Taladro",
            "estado": "Disponible",
            "tratamiento": "Mantención preventiva"
        },
        {
            "id": 2,
            "nombre": "Martillo",
            "estado": "En mantenimiento",
            "tratamiento": "Cambio de mango"
        },
        {
            "id": 3,
            "nombre": "Destornillador",
            "estado": "Dañada",
            "tratamiento": "Requiere reparación"
        }
    ]
}
```

### 4.3. Variables y operaciones

La POC utilizará diferentes tipos de variables:

```python
nombre = "Guantes"
cantidad = 50
stock_minimo = 10
cantidad_solicitada = 5
estado = "Disponible"
puede_usarse = True
```

También se realizará una operación para calcular el stock restante:

```python
stock_restante = cantidad - cantidad_solicitada
```

Por ejemplo:

```
50 - 5 = 45
```

Esto permite demostrar el uso correcto de variables y operaciones.

### 4.4. Estructuras de decisión

La POC determinará automáticamente el estado de los insumos.

**Caso 1: Sin stock**
```python
if cantidad == 0:
    estado = "Sin stock"
```

**Caso 2: Stock bajo**
```python
elif cantidad <= stock_minimo:
    estado = "Stock bajo"
```

**Caso 3: Stock disponible**
```python
else:
    estado = "Disponible"
```

La estructura completa:

```python
if cantidad == 0:
    estado = "Sin stock"
elif cantidad <= stock_minimo:
    estado = "Stock bajo"
else:
    estado = "Disponible"
```

También se determinará si una herramienta puede utilizarse:

**Caso 4: Herramienta no disponible**
```python
if estado == "Disponible":
    puede_usarse = True
elif estado == "En mantenimiento" or estado == "Dañada":
    puede_usarse = False
else:
    puede_usarse = False
```

Con esto se utilizan: `if`, `elif`, `else`, `for`, `==`, `<=`, `or`.

### 4.5. Vista Django

El archivo `views.py` leerá el JSON y procesará la información.

```python
import json
from django.shortcuts import render


def inventario(request):

    with open("inventario.json", "r", encoding="utf-8") as archivo:
        datos = json.load(archivo)

    for insumo in datos["insumos"]:

        cantidad = insumo["cantidad"]
        stock_minimo = insumo["stock_minimo"]

        if cantidad == 0:
            insumo["estado"] = "Sin stock"

        elif cantidad <= stock_minimo:
            insumo["estado"] = "Stock bajo"

        else:
            insumo["estado"] = "Disponible"

    for herramienta in datos["herramientas"]:

        estado = herramienta["estado"]

        if estado == "Disponible":
            herramienta["puede_usarse"] = True

        elif estado == "En mantenimiento" or estado == "Dañada":
            herramienta["puede_usarse"] = False

        else:
            herramienta["puede_usarse"] = False

    return render(
        request,
        "inventario.html",
        {
            "insumos": datos["insumos"],
            "herramientas": datos["herramientas"]
        }
    )
```

### 4.6. Resultado esperado

La aplicación mostrará una página similar a:

```
========================================
       SISTEMA DE INVENTARIO
========================================

INSUMOS

Guantes
Cantidad: 50
Stock mínimo: 10
Estado: Disponible

Mascarillas
Cantidad: 5
Stock mínimo: 10
Estado: Stock bajo

Desinfectante
Cantidad: 0
Stock mínimo: 5
Estado: Sin stock


HERRAMIENTAS

Taladro
Estado: Disponible
Tratamiento: Mantención preventiva
Puede utilizarse: Sí

Martillo
Estado: En mantenimiento
Tratamiento: Cambio de mango
Puede utilizarse: No

Destornillador
Estado: Dañada
Tratamiento: Requiere reparación
Puede utilizarse: No
```

### 4.7. Relación de la POC con la rúbrica

| Criterio | Implementación en la POC | Puntaje objetivo |
|---|---|---|
| 1.1.1 Variables y operaciones | Variables `str`, `int`, `bool` y operaciones de inventario | 6 puntos |
| 1.1.2 Instrucciones, estructuras y operadores | `if`, `elif`, `else`, `for`, comparadores y `or` | 6 puntos |
| 1.1.3 Paquetes externos | Django instalado mediante pip y utilizado en la aplicación | 6 puntos |
| 1.1.4 Aplicación sencilla en Django | Proyecto funcional, URL, vista, template y resultado correcto | 12 puntos |
| **Total** | POC diseñada para cumplir los criterios | **30 puntos** |

> **Nota:** para obtener efectivamente el puntaje máximo en 1.1.2, los cuatro casos implementados deben coincidir con los cuatro casos específicos que indique el enunciado de la evaluación. Si el enunciado define otros casos, se debe adaptar esta lógica.
