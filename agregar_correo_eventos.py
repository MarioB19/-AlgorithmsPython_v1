import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Inicializar la aplicación Firebase
cred = credentials.Certificate('voluntred-9b82e-firebase-adminsdk-xe4ed-cddbd4b29e.json')
firebase_admin.initialize_app(cred)



db = firestore.client()

def actualizar_eventos_con_correo_ong():
    eventos_ref = db.collection('eventos')
    asociaciones_ref = db.collection('asociacion')

    # Recorrer todos los documentos en la colección 'eventos'
    for evento_doc in eventos_ref.stream():
        evento = evento_doc.to_dict()
        uid_ong = evento.get('uidONG')

        if uid_ong:
            # Obtener el documento de la asociación correspondiente
            asociacion_doc = asociaciones_ref.document(uid_ong).get()
            if asociacion_doc.exists:
                asociacion = asociacion_doc.to_dict()
                correo_electronico = asociacion.get('correoElectronico')

                if correo_electronico:
                    # Actualizar el documento del evento con el correo electrónico de la ONG
                    eventos_ref.document(evento_doc.id).update({
                        'correoElectronicoONG': correo_electronico
                    })
                    print(f"Evento actualizado: {evento_doc.id} con correoElectronicoONG: {correo_electronico}")
                else:
                    print(f"No se encontró correoElectronico para la asociación: {uid_ong}")
            else:
                print(f"No se encontró la asociación con UID: {uid_ong}")
        else:
            print(f"El evento {evento_doc.id} no tiene asociado un uidONG")

# Ejecutar la función
actualizar_eventos_con_correo_ong()
