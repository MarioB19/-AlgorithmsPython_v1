
from datetime import datetime
import pytz
import firebase_admin
from firebase_admin import credentials, firestore

# Inicializar la aplicación de Firebase
cred = credentials.Certificate('voluntred-9b82e-firebase-adminsdk-xe4ed-cddbd4b29e.json')
firebase_admin.initialize_app(cred)

db = firestore.client()


def borrar_mensajes_chat_amigos():
    # Iterar sobre cada documento en la colección 'chat_amigos'
    chat_amigos_ref = db.collection('chat_amigos')
    chats = chat_amigos_ref.stream()

    for chat in chats:
        # Obtener la referencia de la subcolección 'mensajes' para el documento actual
        mensajes_ref = chat_amigos_ref.document(chat.id).collection('mensajes')
        
        # Recuperar todos los documentos dentro de la subcolección 'mensajes'
        mensajes = mensajes_ref.stream()
        
        # Borrar cada documento dentro de la subcolección 'mensajes'
        for mensaje in mensajes:
            mensajes_ref.document(mensaje.id).delete()



def eliminar_chat_amigos():
# Definir la zona horaria, por ejemplo, la zona horaria de México
    tz = pytz.timezone('America/Mexico_City')

       # Obtener la fecha y hora actual en la zona horaria especificada
    ahora = datetime.now(tz)
    
    # Verificar si hoy es lunes
    if ahora.weekday() != 0:  # 0 corresponde a lunes
        # Es lunes, ejecutar la función
        borrar_mensajes_chat_amigos()
    else:
        # No es lunes
        print("Hoy no es lunes. No se ejecuta la función.")



