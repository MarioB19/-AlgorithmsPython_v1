import firebase_admin
from firebase_admin import credentials, firestore

from collections import OrderedDict
from dateutil.relativedelta import relativedelta


from random import randint, sample
from datetime import datetime
import pytz

# Inicializar la aplicación de Firebase
cred = credentials.Certificate('voluntred-9b82e-firebase-adminsdk-xe4ed-cddbd4b29e.json')
firebase_admin.initialize_app(cred)
db = firestore.client()




def obtener_horas_voluntarios(anio, mes, tz):

    # Primer día del mes en la zona horaria especificada
    inicio_mes = datetime(anio, mes, 1, tzinfo=tz)
    # Último día del mes en la zona horaria especificada
    if mes == 12:  # Si es diciembre, el siguiente mes es enero del próximo año
        fin_mes = datetime(anio + 1, 1, 1, tzinfo=tz)
    else:
        fin_mes = datetime(anio, mes + 1, 1, tzinfo=tz)

    # Realizar la consulta usando un CollectionGroup
    asistencias = db.collection_group('voluntariosInscritos')\
        .where('Asistencia', '==', True)\
        .where('date', '>=', inicio_mes)\
        .where('date', '<', fin_mes)\
        .stream()

    # Inicializar un diccionario para acumular las horas
    voluntarios_horas_aportadas = {}

    # Procesar los documentos resultantes
    for asistencia in asistencias:
        band = False
        doc = asistencia.to_dict()

        uid_voluntario = doc.get("uidVoluntario")
        horas = doc.get('horasRealizadas', 0)  # Asumiendo que cada asistencia tiene un campo 'horas'

        if uid_voluntario in voluntarios_horas_aportadas:
            voluntarios_horas_aportadas[uid_voluntario] += horas
        else:
            voluntarios_horas_aportadas[uid_voluntario] = horas

    return voluntarios_horas_aportadas





def ranking():

    # Define la zona horaria de México
    tz = pytz.timezone('America/Mexico_City')

    # Obtener el timestamp actual en la zona horaria de México
    mexico_time = datetime.now(tz)

    #Verificar si hoy NO es el primer día del mes
    if mexico_time.day != 1:
        return ('Hoy no es el primer día del mes.', 200)

    mes_anterior = mexico_time - relativedelta(months=1)
    mes = mes_anterior.month
    anio = mes_anterior.year

    # Paso 1: Obtener todos los voluntarios y sus horas aportadas
    voluntarios = db.collection('voluntarios').stream()

    #Restablecer horas aportadas a 0
    voluntarios_horas_aportadas = {voluntario.id: 0 for voluntario in voluntarios}

    # Uso de la función para obtener las horas aportadas de los voluntarios en el mes actual
    horas_aportadas = obtener_horas_voluntarios(anio, mes, tz)

    # Actualizar las horas aportadas en el diccionario voluntarios_horas_aportadas
    for uid, horas in horas_aportadas.items():
        if uid in voluntarios_horas_aportadas:
            voluntarios_horas_aportadas[uid] = horas
   
        # Supongamos que voluntarios_horas_aportadas ya está definido y lleno de datos
    voluntarios_ordenados = OrderedDict(sorted(voluntarios_horas_aportadas.items(), key=lambda x: x[1], reverse=True))

    # Asignar posiciones teniendo en cuenta horas compartidas
    posicion_actual = 1
    horas_anterior = None
    voluntarios_con_posiciones = []

    for uid, horas in voluntarios_ordenados.items():
        if horas != horas_anterior:
            horas_anterior = horas
            posicion_actual = len(voluntarios_con_posiciones) + 1
        voluntarios_con_posiciones.append({'uid': uid, 'horas': horas, 'posicion': posicion_actual})

    # Crear y subir un documento nuevo con un ID generado automáticamente
    doc_ref = db.collection('ranking').document()  # Firestore generará un ID único aquí
    doc_ref.set({
        'voluntarios': voluntarios_con_posiciones,
        'date': firestore.SERVER_TIMESTAMP  # Esto establece la fecha de creación al momento actual
    })


    return("ok", 200)



print(ranking())



