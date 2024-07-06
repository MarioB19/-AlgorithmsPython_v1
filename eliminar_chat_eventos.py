import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from dateutil import parser
from datetime import datetime
import pytz
import warnings



# Inicializa la aplicación de Firebase con tus credenciales
cred = credentials.Certificate('voluntred-9b82e-firebase-adminsdk-xe4ed-cddbd4b29e.json')
firebase_admin.initialize_app(cred)
warnings.filterwarnings("ignore")


db = firestore.client()


def convertir_date_time(fecha_str, hora_fin_str, tz):
    datetime_str = f"{fecha_str} {hora_fin_str}"
    # Asegurarse de que el día se interprete primero
    evento_datetime = parser.parse(datetime_str, dayfirst=True).replace(tzinfo=tz)
    return evento_datetime



def eliminar_chat_y_mensajes(uid):
    # Obtener la referencia del documento
    doc_ref = db.collection('chat_evento').document(uid)

    # Borrar las subcolecciones
    subcolecciones = doc_ref.collections()
    for subcolección in subcolecciones:
        for subdocumento in subcolección.stream():
            subdocumento.reference.delete()

    # Borrar el documento principal
    doc_ref.delete()
    print(f"El documento con UID {uid} y todas sus subcolecciones han sido eliminados.")




def convertir_date_time(fecha_str, hora_fin_str, tz):
    # Especificar el formato exacto de la fecha y la hora
    formato_fecha = "%d/%m/%Y"  # día/mes/año
    formato_hora = "%I:%M %p"   # hora:minuto AM/PM
    datetime_str = f"{fecha_str} {hora_fin_str}"

    # Convertir la cadena de fecha y hora al objeto datetime
    evento_datetime = datetime.strptime(datetime_str, f"{formato_fecha} {formato_hora}")
    evento_datetime = evento_datetime.replace(tzinfo=tz)

    return evento_datetime

def eliminar_chat_eventos():
    tz = pytz.timezone('America/Mexico_City')
    mexico_time = datetime.now(tz)

    # Referencia a la colección
    eventos_ref = db.collection('eventos')
    
    # Aplicar filtros usando where
    query = eventos_ref.where('estado', '==', 'Pasado').where('chatActivo', '==', True)

    # Obtener los documentos que cumplen con los filtros
    results = query.stream()

    # Revisar cada evento y actualizar si es necesario
    for doc in results:
        data = doc.to_dict()

        fecha_str = data["date"]  # dd/mm/yy
        hora_fin_str = data["timeFin"] # hh:mm AM/PM

     
        evento_datetime = convertir_date_time(fecha_str,hora_fin_str,tz)

        # Calculamos la diferencia entre la fecha actual y la fecha del evento
        diferencia = mexico_time - evento_datetime
        print(f"Evento ID {doc.id}")
        print(diferencia)

        # Verificar si la diferencia de tiempo es de 7 días o más
        if diferencia.days >= 7:
            uid_chat = data['uidChat']


            # Actualizar el estado del evento en Firestore
            doc.reference.update({'chatActivo': False, 'uidChat': ''})
            eliminar_chat_y_mensajes(uid_chat)

            print(f"Evento ID {doc.id} ha sido actualizado a 'Inactivo' debido a que la diferencia de días es {diferencia.days}")

eliminar_chat_eventos()