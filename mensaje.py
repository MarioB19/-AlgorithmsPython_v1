import pywhatkit
import re
import time

# Lista de estudiantes con sus nombres y números en formato de diccionario
estudiantes = [
                ]

# Función para crear un mensaje personalizado

def crear_mensaje(nombre):
    # Personaliza el mensaje como quieras aquí
    mensaje = f"""
    Lorem Ipsum
    """
    return mensaje


# Preparar los mensajes
for estudiante in estudiantes:

    estudiante['mensaje'] = crear_mensaje(estudiante['nombre'])

# Suponiendo que quieres enviar los mensajes uno tras otro
for estudiante in estudiantes:
    try:
        # Intenta enviar el mensaje
        pywhatkit.sendwhatmsg_instantly(
            estudiante['numero'], estudiante['mensaje'], wait_time=20)
        print(f"Mensaje programado para { estudiante['nombre']} al número {estudiante['numero']}")
    except Exception as e:
        # Aquí se maneja la excepción, imprimiendo un mensaje de error
        print(f"Ocurrió un error al enviar el mensaje a {estudiante['nombre']} al número {estudiante['numero']}. Error: {e}")

    time.sleep(10)  # Ajusta este tiempo según sea necesario
