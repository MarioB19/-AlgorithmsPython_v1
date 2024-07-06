


import firebase_admin
from firebase_admin import credentials, firestore


cred = credentials.Certificate('voluntred-9b82e-firebase-adminsdk-xe4ed-cddbd4b29e.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

def eliminar_insignias():
    voluntarios = db.collection('voluntarios').stream()

    for voluntario in voluntarios:
        voluntario_ref = db.collection('voluntarios').document(voluntario.id)
        voluntario_ref.update({'insignia': ''})



