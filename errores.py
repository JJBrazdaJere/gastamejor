"""Excepciones propias del sistema.

Usar excepciones (en vez de imprimir y devolver None) permite que la MISMA
logica sirva para el menu de consola, para los tests y para una futura
interfaz web (Django) o de escritorio. Cada capa decide como informar.
"""


class ErrorAplicacion(Exception):
    """Error de negocio. El mensaje esta pensado para mostrarse al usuario."""


class ErrorValidacion(ErrorAplicacion):
    """Datos invalidos ingresados (campos vacios, numeros mal, etc.)."""


class ErrorNoEncontrado(ErrorAplicacion):
    """El registro buscado no existe (una operacion no afecto ninguna fila)."""


class ErrorUnico(ErrorAplicacion):
    """Se intento cargar un valor que ya existe (ej: email duplicado)."""


class ErrorClaveForanea(ErrorAplicacion):
    """Se referencia un registro inexistente, o no se puede borrar por dependencias."""


class ErrorBaseDatos(ErrorAplicacion):
    """Fallo inesperado al comunicarse con PostgreSQL."""
