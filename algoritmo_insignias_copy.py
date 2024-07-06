
import firebase_admin
from firebase_admin import credentials, firestore
from random import randint, sample
from datetime import datetime,  timedelta
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
from firebase_functions import https_fn
import pytz
import requests


cred = credentials.Certificate('voluntred-9b82e-firebase-adminsdk-xe4ed-cddbd4b29e.json')
firebase_admin.initialize_app(cred)


db = firestore.client()

def obtener_publicaciones_realizadas(anio, mes, tz, voluntarios):

    # Primer día del mes en la zona horaria especificada
    inicio_mes = datetime(anio, mes, 1, tzinfo=tz)
    # Último día del mes en la zona horaria especificada
    if mes == 12:  # Si es diciembre, el siguiente mes es enero del próximo año
        fin_mes = datetime(anio + 1, 1, 1, tzinfo=tz)
    else:
        fin_mes = datetime(anio, mes + 1, 1, tzinfo=tz)


    total_publicaciones_realizadas = {}

    for uid in voluntarios.keys():
        # Contar las publicaciones por uidVoluntario
        query = db.collection('publicacionesVoluntario')\
            .where('uidAutor', "==", uid)\
            .where('date', '>=', inicio_mes)\
            .where('date', '<', fin_mes)\
            .stream()

        # Contar el número de publicaciones
        numero_publicaciones = sum(1 for _ in query)
        total_publicaciones_realizadas[uid] = numero_publicaciones

    return total_publicaciones_realizadas

def obtener_asistencias_y_eventos(anio, mes, tz, voluntarios):

    # Primer día del mes en la zona horaria especificada
    inicio_mes = datetime(anio, mes, 1, tzinfo=tz)
    # Último día del mes en la zona horaria especificada
    if mes == 12:  # Si es diciembre, el siguiente mes es enero del próximo año
        fin_mes = datetime(anio + 1, 1, 1, tzinfo=tz)
    else:
        fin_mes = datetime(anio, mes + 1, 1, tzinfo=tz)

    total_eventos_asistidos = {}
    eventos_por_voluntario = {}

    for uid in voluntarios.keys():
        # Obtener los eventos asistidos por uidVoluntario
        query = db.collection_group('voluntariosInscritos')\
            .where('Asistencia', '==', True)\
            .where('uidVoluntario', "==", uid)\
            .where('date', '>=', inicio_mes)\
            .where('date', '<', fin_mes)\
            .stream()

        # Inicializa la lista de eventos para el voluntario actual
        eventos_por_voluntario[uid] = []

        # Contar el número de asistencias y acumular los uids de eventos
        numero_asistencias = 0
        for doc in query:
            numero_asistencias += 1
            evento_id = doc.get('uidEvento')  # Asumiendo que cada documento tiene un campo 'uidEvento'
            eventos_por_voluntario[uid].append(evento_id)

        total_eventos_asistidos[uid] = numero_asistencias

    return total_eventos_asistidos, eventos_por_voluntario

def obtener_posicion_ranking_norm(uidVoluntario, ranking):

    total_voluntarios = len(ranking) #Total de voluntarios en el ranking
    r = obtener_posicion(ranking,uidVoluntario) #Posicion del voluntario en el ranking


    if(r == -1):
        return 0.0
    elif(total_voluntarios-1 <= 0):
        return 0.0
    else:
        return (total_voluntarios  - r) / (total_voluntarios-1)  #Hacer peticion para que al denominador se le pueda restar 1

def obtener_eventos_asistidos_norm(uidVoluntario, eventos_asistidos):
    asistencias = eventos_asistidos.values()

    e = eventos_asistidos.get(uidVoluntario,0) #e: eventos asistidos por un voluntario el mes correspondiente
    e_max =   max(asistencias) #e_max: la máxima cantidad de eventos asistidos por un voluntario en el mes correspondiente. 
    e_min = min(asistencias )#e_min: la mínima cantidad de eventos asistidos por un voluntario en el mes correspondiente. 

    if(e_max-e_min == 0):
        return 0.0
    else:
        return  (e - e_min) / (e_max - e_min) 

def obtener_publicaciones_realizadas_norm(uidVoluntario, publicaciones_realizadas):
    numero_publicaciones = publicaciones_realizadas.values()

    p = publicaciones_realizadas.get(uidVoluntario,0) #p: publicaciones realizadas por un voluntario durante el mes correspondiente
    p_max =   max(numero_publicaciones) #p_max: es la máxima cantidad de publicaciones hechas por un voluntario en el mes correspondiente. 
    p_min = min(numero_publicaciones )#p_min: es la mínima cantidad de publicaciones hechas por un voluntario en el mes correspondiente. 

    if(p_max-p_min == 0):
        return 0.0
    else:
        return  (p - p_min) / (p_max - p_min) 

def get_document_for_current_month(anio,mes, tz,collection_path):
  
    inicio_mes = datetime(anio, mes, 1, tzinfo=tz)
    # Último día del mes en la zona horaria especificada
    if mes == 12:  # Si es diciembre, el siguiente mes es enero del próximo año
        fin_mes = datetime(anio + 1, 1, 1, tzinfo=tz)
    else:
        fin_mes = datetime(anio, mes + 1, 1, tzinfo=tz)

    # Haz la consulta para obtener los documentos del mes actual
    docs = db.collection(collection_path)\
             .where('date', '>=', inicio_mes)\
             .where('date', '<', fin_mes)\
             .get()
    
    for doc in docs:
        if doc.exists:
            # Aquí tienes el UID del documento correspondiente al mes actual
            print(f"Document ID: {doc.id}")
            return doc

def obtener_voluntarios_de_ranking(document_snapshot):
    lista_voluntarios = []
    if document_snapshot.exists:
        data = document_snapshot.to_dict()
        if 'voluntarios' in data:
            for voluntario_data in data['voluntarios']:
                voluntario = {
                    'uid': voluntario_data.get('uid'),
                    'horas': voluntario_data.get('horas'),
                    'posicion': voluntario_data.get('posicion')
                }
                lista_voluntarios.append(voluntario)
    return lista_voluntarios


def obtener_ranking(anio,mes,tz):
    doc_ref = get_document_for_current_month(anio,mes,tz, 'ranking')
    voluntarios_ranking = obtener_voluntarios_de_ranking(doc_ref)
    return ordenar_ranking(voluntarios_ranking)

def ordenar_ranking(ranking):
    # Ordenar la lista de diccionarios por la clave 'posicion' en cada diccionario
    return sorted(ranking, key=lambda item: item['posicion'])

def obtener_posicion(ranking, uid):
    # Buscar la posición del UID dado dentro de la lista de diccionarios
    for voluntario in ranking:
        if voluntario['uid'] == uid:
            return voluntario['posicion']
    return -1  # Retorna -1 si no se encuentra el UID

def obtener_datos_voluntarios():
    voluntarios = db.collection('voluntarios').stream()
    diccionario_voluntarios = {}
    for voluntario in voluntarios:
        # Asumiendo que cada documento tiene un campo 'uidVoluntario' y un campo 'insignia'
        uid = voluntario.get('uidVoluntario')
        insignia = voluntario.get('insignia')
        diccionario_voluntarios[uid] = insignia

    return diccionario_voluntarios

def calcular_puntaje(r_norm, e_norm, p_norm,o_norm):
    alpha = 0.35 #mayor impacto(0.35)
    beta = 0.20 #impacto medio (0.20)
    delta = 0.10 #impacto bajo (0.10)

    puntuacion  = (alpha * r_norm) + (alpha * e_norm) + (delta * p_norm) + (beta * o_norm) 
    return puntuacion


def procesar_puntaje(uidVoluntario, puntaje):
    insignia = ""
    if(puntaje <0.60):
        return
    
    elif(puntaje >= 0.60 and puntaje< 0.70):  #Voluntario persistente
       insignia = "https://firebasestorage.googleapis.com/v0/b/voluntred-9b82e.appspot.com/o/insignias%2FVoluntario%20Persistente.png?alt=media&token=9f730832-a7da-463d-a34c-31cb8fe885d8"

    elif(puntaje>= 0.70 and puntaje <0.80) : #Voluntario elite
        insignia = "https://firebasestorage.googleapis.com/v0/b/voluntred-9b82e.appspot.com/o/insignias%2FInsignia%20Voluntario%20de%20Elite.png?alt=media&token=02f1346d-50e1-4c20-a7f3-bfb21582e944"

    elif(puntaje>=0.80 and puntaje <0.90): #Voluntario experto
        insignia = "https://firebasestorage.googleapis.com/v0/b/voluntred-9b82e.appspot.com/o/insignias%2FInsignia%20Voluntario%20Experto.png?alt=media&token=0e97cb19-db66-45f1-8565-90ea8d2b91fb"

    elif(puntaje>= 0.90 and puntaje <=1):
        insignia = "https://firebasestorage.googleapis.com/v0/b/voluntred-9b82e.appspot.com/o/insignias%2FInsignia%20Heroe%20del%20Voluntariado.png?alt=media&token=fdb93dc5-c2ea-476f-abfc-e28f1b36f89d"

    #Subiendo insignia
    voluntario_ref = db.collection('voluntarios').document(uidVoluntario)
    voluntario_ref.update({'insignia': insignia})




        

def obtener_ods_apoyadas(uidVoluntario, eventos_asistidos):
    eventos = eventos_asistidos.get(uidVoluntario, [])
  

    resultado_ods_tags = []

    for uidEvento in eventos:
        # Obtener el documento para el uidEvento actual
        doc_ref = db.collection('eventos').document(uidEvento)
        doc = doc_ref.get()
        if doc.exists:
            # Suponiendo que cada documento tiene un campo 'odsTags' que es un array
            ods_tags = doc.get('odsTags')
  
            resultado_ods_tags.extend(ods_tags)  # Agregar los odsTags de este evento a la lista general
     

    resultado_ods_tags = list(set(resultado_ods_tags))

    return len(resultado_ods_tags)


def obtener_ods_apoyadas_norm(o):
    o_min = 0 #es la cantidad mínima de ODS que un voluntario puede apoyar (siendo 0 la cantidad mínima de ODS que puede apoyar). 
    o_max = 14 #es la cantidad máxima de ODS que el voluntario puede apoyar (siendo 14 la cantidad máxima de ODS que puede apoyar). 

    if(o_max-o_min == 0):
        return 0.0
    else:
        return (o - o_min) / (o_max - o_min)  


def enviar_notificacion(uidVoluntario,titulo, cuerpo):
    # Datos a enviar en el cuerpo de la solicitud
    datos_email = {
        "uidVoluntario": uidVoluntario,
        "titulo": f"Insignia del mes: {titulo}",
        "cuerpo": cuerpo
    }

    # Llamar a la primera API
    respuesta = requests.post(
        'https://send-notification-wrks2oq7kq-uc.a.run.app',
        json=datos_email  # Usamos el argumento json para enviar los datos
    )

    if respuesta.status_code == 200:
        print("Notificacion enviada.")
        print("Respuesta:", respuesta.text)
        return 200
    else:
        # Manejar errores o fallas en la respuesta
        print(f"Error al enviar la notificacion: {respuesta.status_code}")
        return None



def crear_mensaje_noti(puntaje,r_norm, e_norm, p_norm, o_norm):

    message = ""

    if(puntaje <0.60):
        message = "No obtuviste ninguna insignia"
    elif(puntaje >= 0.60 and puntaje< 0.70):  #Voluntario persistente
        message = "Obtuviste la insignia de voluntario Persistente"

    elif(puntaje>= 0.70 and puntaje <0.80) : #Voluntario elite
        message = "Obtuviste la insignia de voluntario Elite"

    elif(puntaje>=0.80 and puntaje <0.90): #Voluntario experto
        message = "Obtuviste la insignia de voluntario Expero"

    elif(puntaje>= 0.90 and puntaje <=1):
        message = "Obtuviste la insignia de voluntario Heroe"

    alpha = 0.35
    beta = 0.20
    delta = 0.10

    dif_r = (alpha*1) - (alpha*r_norm)
    dif_e  = (alpha*1) - (alpha*e_norm)
    dif_p = (delta*1) - (delta*p_norm)
    dif_o = (beta*1) - (beta*o_norm)

       # Determinar el mensaje de retroalimentación basado en la mayor diferencia
    max_dif = max(dif_r, dif_e, dif_p, dif_o)

    if max_dif == dif_r:
        feedback = " Te recomendamos obtener una mejor posición en el ranking."
    elif max_dif == dif_e:
        feedback = " Te recomendamos asistir a una mayor cantidad de eventos."
    elif max_dif == dif_p:
        feedback = " Te recomendamos realizar más publicaciones."
    elif  max_dif == dif_o:
        feedback = " Te recomendamos apoyar una mayor cantidad de ODS."

    return message , feedback


def algoritmo_insignias():
    # Define la zona horaria de México
    tz = pytz.timezone('America/Mexico_City')

    # Obtener el timestamp actual en la zona horaria de México
    mexico_time = datetime.now(tz)
    mes_actual = mexico_time.month
    anio_actual = mexico_time.year

    
    #if mexico_time.day != 1:
    #    return ('Hoy no es el primer día del mes.', 200)

    mes_anterior = mexico_time - relativedelta(months=1)
    mes = mes_anterior.month
    anio = mes_anterior.year


    # Paso 1: Obtener todos los voluntarios y sus horas aportadas
    voluntarios = obtener_datos_voluntarios()
    ranking = obtener_ranking(anio_actual,mes_actual,tz)

    total_asistencias, eventos_asistidos = obtener_asistencias_y_eventos(anio,mes,tz,voluntarios)
    publicicaciones_realizadas = obtener_publicaciones_realizadas(anio,mes,tz,voluntarios)

    
    for uid in voluntarios.keys():
    
        r_norm =  obtener_posicion_ranking_norm(uid, ranking)   #es la posición normalizada obtenida en el ranking.
        e_norm =  obtener_eventos_asistidos_norm(uid, total_asistencias)    #número normalizado de eventos asistidos durante el mes. 
        p_norm =  obtener_publicaciones_realizadas_norm(uid,publicicaciones_realizadas) #numero normalizado de publicaciones realizadas durante el mes
        o = obtener_ods_apoyadas(uid, eventos_asistidos) #numero de ods que un voluntario apoyo a traves de eventos durante el mes.
        o_norm = obtener_ods_apoyadas_norm(o) #numero normalizado de ods apoyadas durante el mes


        print("-------------------------")
        
        print(f"Uid Voluntario {uid}")
        print(f"Variable posicion ranking normalizada r_norm {r_norm}")
        print(f"Variable numero eventos asistidos e_norm {e_norm}")
        print(f"Variable numero publicaciones realizadas e_norm {p_norm}")
        print(f"Variable numero ods apoyadas o_norm {o_norm}")

  
        puntaje = calcular_puntaje(r_norm, e_norm, p_norm,o_norm)

        print(f"Puntaje {puntaje}")

        procesar_puntaje(uid, puntaje)

        titulo, cuerpo = crear_mensaje_noti(puntaje, r_norm, e_norm, p_norm, o_norm)

        print(f"Cuerpo {cuerpo}")

        enviar_notificacion(uid,titulo, cuerpo)

        


        print("----------------")

        
        
    return ('ok', 200)
        


algoritmo_insignias()