import firebase_admin
from firebase_admin import credentials, messaging, firestore

# Inicializa la aplicación de Firebase solo una vez
cred = credentials.Certificate('voluntred-9b82e-firebase-adminsdk-xe4ed-cddbd4b29e.json')
firebase_admin.initialize_app(cred)


db = firestore.client()

def get_token_fcm(uid_voluntario):
    # Busca documentos en la colección 'voluntarios' donde 'uidVoluntario' es igual al proporcionado
    voluntarios_ref = db.collection('voluntarios')
    query_ref = voluntarios_ref.where('uidVoluntario', '==', uid_voluntario).limit(1)
    docs = query_ref.stream()

    for doc in docs:
        # Suponiendo que 'tokenFCM' es un campo en los documentos de la colección 'voluntarios'
        token_fcm = doc.to_dict().get('tokenFCM', None)
        if token_fcm:
            return token_fcm
    
    return "" 


def send_fcm_notification(uid, title, body):

    token = get_token_fcm(uid)

    if(token == ""):
        return ("No hay token FCM asociado", 200)
    
    # Crear mensaje
    try:
    # Creación del mensaje
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=token,
        )

        # Envío del mensaje
        response = messaging.send(message)
        print('Mensaje enviado con éxito:', response)

    except messaging.FirebaseError as e:
        # Manejo de errores relacionados con Firebase
        print(f'Ha ocurrido un error al enviar el mensaje: {e}')
    except Exception as e:
        # Manejo de cualquier otro error
        print(f'Ha ocurrido un error inesperado: {e}')






print(send_fcm_notification("PgpqNGgGXEa7X4vnq9HPU90f5Jz2", "Prueba noti" , "ok"))