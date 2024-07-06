import firebase_admin
from firebase_admin import credentials, firestore
from random import randint, sample
from datetime import datetime

# Inicializar la aplicación de Firebase
cred = credentials.Certificate('voluntred-9b82e-firebase-adminsdk-xe4ed-cddbd4b29e.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

def eliminar_eventos_pasados():
    # Consultar todos los documentos en la colección 'eventos' donde el estado es 'Pasado'
    eventos_pasados = db.collection('eventosPrueba').where('estado', '==', 'Pasado').where('uidONG', '==', 'AlgoritmoPrediccion').stream()

    # Eliminar cada documento encontrado
    for evento in eventos_pasados:
        doc_ref = db.collection('eventosPrueba').document(evento.id)
        doc_ref.delete()
        print(f"Eliminado evento con ID: {evento.id}")

def generate_random_time():
    hour = randint(1, 12)
    minutes = randint(0, 59)
    ampm = ['AM', 'PM'][randint(0, 1)]
    return f"{str(hour).zfill(2)}:{str(minutes).zfill(2)} {ampm}"

def generate_time_pair():
    start_time = generate_random_time()
    end_time = generate_random_time()
    format = '%I:%M %p'

    while datetime.strptime(end_time, format) <= datetime.strptime(start_time, format):
        end_time = generate_random_time()

    return start_time, end_time

def generate_random_date():
    day = randint(1, 28)
    month = randint(1, 12)
    year = randint(2020, 2024)
    return f"{str(day).zfill(2)}/{str(month).zfill(2)}/{year}"

def generate_random_ods_tags():
    all_tags = [str(i) for i in range(1, 9)] + [str(i) for i in range(13, 16)]
    num_tags = randint(1, 5)
    return sample(all_tags, num_tags)

def insert_random_event():
    timeInicio, timeFin = generate_time_pair()
    registeredPeopleCount = randint(10, 40)  # Generar un conteo aleatorio de personas registradas
    event = {
        'timeInicio': timeInicio,
        'timeFin': timeFin,
        'date': generate_random_date(),
        'odsTags': generate_random_ods_tags(),
        'uidChat': 'AlgoritmoPrediccion',
        'uidONG': 'AlgoritmoPrediccion',
        'estado': "Pasado",
        'registeredPeopleCount': registeredPeopleCount  # Agregar el campo con el valor generado
    }
    # Insertar el evento y obtener la referencia del documento creado
    doc_ref = db.collection('eventosPrueba').add(event)[1].get().reference
    # Actualizar el documento con el uidEvento igual a la ID del documento
    doc_ref.update({'uidEvento': doc_ref.id})
    print(f"Evento insertado con ID: {doc_ref.id}")

def insert_multiple_random_events(number_of_events):
    for _ in range(number_of_events):
        insert_random_event()
    print(f"{number_of_events} eventos insertados.")



insert_multiple_random_events(300)