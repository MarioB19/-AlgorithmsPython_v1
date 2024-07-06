import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz
import math
import warnings

warnings.filterwarnings("ignore")
import requests


cred = credentials.Certificate('voluntred-9b82e-firebase-adminsdk-xe4ed-cddbd4b29e.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

def obtener_fecha_creacion(uid):
    # Inicializa el cliente de Firestore
    db = firestore.client()

    # Referencia al documento del voluntario basado en uid
    doc_ref = db.collection('voluntarios').document(uid)
    doc = doc_ref.get()

    # Retorna el campo fechaCreacion si el documento existe
    return doc.to_dict().get('fechaCreacion', 'La fecha de creación no está disponible')


def obtener_publicaciones_por_voluntario(uid_voluntario, anio, mes, tz):
    # Primer día del mes anterior
    inicio_mes = datetime(anio, mes, 1, tzinfo=tz)
    # Último día del mes anterior
    if mes == 12:
        fin_mes = datetime(anio + 1, 1, 1, tzinfo=tz)
    else:
        fin_mes = datetime(anio, mes + 1, 1, tzinfo=tz)

    # Contar las publicaciones por uidVoluntario del mes anterior
    query = db.collection('publicacionesVoluntario')\
        .where('uidAutor', "==", uid_voluntario)\
        .where('date', '>=', inicio_mes)\
        .where('date', '<', fin_mes)\
        .stream()

    # Contar el número de publicaciones
    numero_publicaciones = sum(1 for _ in query)

    return numero_publicaciones


def obtener_numero_asistencias_voluntario(uid_voluntario, anio, mes, tz):
  
    inicio_mes = datetime(anio, mes, 1, tzinfo=tz)
    if mes == 12:
        fin_mes = datetime(anio + 1, 1, 1, tzinfo=tz)
    else:
        fin_mes = datetime(anio, mes + 1, 1, tzinfo=tz)

    query = db.collection_group('voluntariosInscritos')\
        .where('Asistencia', '==', True)\
        .where('uidVoluntario', "==", uid_voluntario)\
        .where('date', '>=', inicio_mes)\
        .where('date', '<', fin_mes)\
        .stream()

    numero_asistencias = sum(1 for _ in query)

    return numero_asistencias

def obtener_horas_por_voluntario(uid_voluntario, anio, mes, tz):
   
    inicio_mes = datetime(anio, mes, 1, tzinfo=tz)
    if mes == 12:
        fin_mes = datetime(anio + 1, 1, 1, tzinfo=tz)
    else:
        fin_mes = datetime(anio, mes + 1, 1, tzinfo=tz)

    asistencias = db.collection_group('voluntariosInscritos')\
        .where('Asistencia', '==', True)\
        .where('uidVoluntario', '==', uid_voluntario)\
        .where('date', '>=', inicio_mes)\
        .where('date', '<', fin_mes)\
        .stream()

    total_horas = 0

    for asistencia in asistencias:
        doc = asistencia.to_dict()
        horas = doc.get('horasRealizadas', 0)  
        total_horas += horas

    return total_horas


def obtener_nuevas_amistades(uid_voluntario, anio, mes, tz):
    # Primer día del mes en la zona horaria especificada
    inicio_mes = datetime(anio, mes, 1, tzinfo=tz)
    # Último día del mes en la zona horaria especificada
    if mes == 12:
        fin_mes = datetime(anio + 1, 1, 1, tzinfo=tz)
    else:
        fin_mes = datetime(anio, mes + 1, 1, tzinfo=tz)

    amistades = db.collection('amistades')\
        .where('fechaAmistad', '>=', inicio_mes)\
        .where('fechaAmistad', '<', fin_mes)\
        .stream()

    nuevas_amistades = 0

    for amistad in amistades:
        doc = amistad.to_dict()
        if uid_voluntario in doc.get('uidParticipantes', []):
            nuevas_amistades += 1

    return nuevas_amistades

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


def obtener_posicion_ranking(uid,anio,mes,tz):

    doc_ref = get_document_for_current_month(anio,mes,tz, 'ranking')
    voluntarios_ranking = obtener_voluntarios_de_ranking(doc_ref)
    voluntarios_ranking = ordenar_ranking(voluntarios_ranking)

    return obtener_posicion(voluntarios_ranking,uid)




def ordenar_ranking(ranking):
    # Ordenar la lista de diccionarios por la clave 'posicion' en cada diccionario
    return sorted(ranking, key=lambda item: item['posicion'])


def obtener_posicion(ranking, uid):
    # Buscar la posición del UID dado dentro de la lista de diccionarios
    for voluntario in ranking:
        if voluntario['uid'] == uid:
            return 1/voluntario['posicion']
    return -1  # Retorna -1 si no se encuentra el UID



def obtener_suma_reacciones(uid_voluntario, anio, mes, tz):
    inicio_mes = datetime(anio, mes, 1, tzinfo=tz)
    if mes == 12:
        fin_mes = datetime(anio + 1, 1, 1, tzinfo=tz)
    else:
        fin_mes = datetime(anio, mes + 1, 1, tzinfo=tz)
    
    publicaciones = db.collection('publicacionesVoluntario')\
        .where('uidAutor', '==', uid_voluntario)\
        .where('date', '>=', inicio_mes)\
        .where('date', '<', fin_mes)\
        .stream()
    
    total_reacciones = 0
    
    for publicacion in publicaciones:
        doc = publicacion.to_dict()
        total_reacciones += doc.get('meDivierte', 0)
        total_reacciones += doc.get('meEnoja', 0)
        total_reacciones += doc.get('meEntristece', 0)
        total_reacciones += doc.get('meEncanta', 0)
        total_reacciones += doc.get('meGusta', 0)
    
    return total_reacciones



def contar_ejecuciones_algoritmo(fecha_creacion_local,anio_actual, mes_actual):
    ejecuciones = 0

    # Itera desde el mes siguiente de la fecha de creación hasta el mes actual

    anio, mes = fecha_creacion_local.year, fecha_creacion_local.month

    while anio < anio_actual or (anio == anio_actual and mes <= mes_actual):
        if mes == 12:
            anio += 1
            mes = 1
        else:
            mes += 1

        ejecuciones += 1
    # Ajusta la cuenta si la fecha de creación es después del primer día de su mes
    if fecha_creacion_local.day > 1:
        ejecuciones -= 1

    return ejecuciones


def obtener_metricas_comparativas(uid_voluntario, tz, obtener_metrica, mexico_time,ejecuciones):
    metricas = []
    mes_evaluado = mexico_time - relativedelta(months=1)
    valor_mes_anterior = obtener_metrica(uid_voluntario, mes_evaluado.year, mes_evaluado.month, tz)


    print(f"Valor del mes anterior: {valor_mes_anterior}")

       # Define los valores predeterminados para minMes y maxMes
    minMes = 2
    maxMes = 8

    # Ajusta minMes y maxMes según el número de ejecuciones
    if ejecuciones > 7:
        minMes = 2
        maxMes = 8

    if ejecuciones < 2:
        # Aquí puedes definir el comportamiento cuando las ejecuciones son menores a 2
        # Por ejemplo, puedes decidir no realizar ninguna iteración y retornar valores especiales
        print("No se realizan cálculos porque las ejecuciones son menores a 2")
        return valor_mes_anterior, []
    
    if ejecuciones >=2 and ejecuciones<=7:
        minMes = 2
        maxMes = ejecuciones+1
    

    for i in range(minMes, maxMes):  
        mes_evaluado = mexico_time - relativedelta(months=i)
        valor = obtener_metrica(uid_voluntario, mes_evaluado.year, mes_evaluado.month, tz)
        metricas.append(valor)
        print(f"Valor {i-1} meses atrás: {valor}")

    return valor_mes_anterior, metricas


def calcular_variacion_comparativa(valor_mes_anterior, metricas_anteriores):
    promedio_meses_anteriores = sum(metricas_anteriores) / len(metricas_anteriores) if metricas_anteriores else 0
    print(f"Promedio de los meses anteriores: {promedio_meses_anteriores}")
    
    if promedio_meses_anteriores == 0:
        variacion_porcentaje = valor_mes_anterior * 100
    else:
        variacion = (valor_mes_anterior - promedio_meses_anteriores) / promedio_meses_anteriores
        variacion_porcentaje = round(variacion * 100, 2)  
    return variacion_porcentaje


def obtener_reacciones_por_voluntario(uid_voluntario, anio, mes, tz):
    inicio_mes = datetime(anio, mes, 1, tzinfo=tz)
    fin_mes = inicio_mes + relativedelta(months=1)

    reacciones = db.collection_group('reacciones')\
        .where('uidAutor', '==', uid_voluntario)\
        .where('fechaReaccion', '>=', inicio_mes)\
        .where('fechaReaccion', '<', fin_mes)\
        .stream()

    # Inicializando contadores para cada tipo de reacción
    contador_reacciones = {
        'meGusta': 0,
        'meEncanta': 0,
        'meDivierte': 0,
        'meEnoja': 0,
        'meEntristece': 0
    }

    for reaccion in reacciones:
        doc = reaccion.to_dict()
        # Asumiendo que el campo de tipo de reacción se llama 'tipoReaccion'
        tipo = doc.get('reaccionHecha')
        if tipo in contador_reacciones:
            contador_reacciones[tipo] += 1

    return contador_reacciones

def calcular_porcentajes_reacciones(contador_reacciones):
    total_reacciones = sum(contador_reacciones.values())
    porcentajes = {}
    for tipo, cantidad in contador_reacciones.items():
        porcentajes[tipo] = (cantidad / total_reacciones * 100) if total_reacciones else 0
    return porcentajes



def analizar_correlacion(X, Y):

    if(len(X)-1 == 0 or len(Y)-1 == 0):
        return 0.0
    # Calcular el promedio de eventos asistidos y nuevos amigos
    promedio_X = sum(X) / len(X) if X else 0  # Evita la división por cero
    promedio_Y = sum(Y) / len(Y) if Y else 0  # Evita la división por cero

    print(f"Promedio x: {promedio_X}")
    print(f"Promedio y: {promedio_Y}")

    SX = math.sqrt(sum((x - promedio_X) ** 2 for x in X) / (len(X) - 1))
    SY = math.sqrt(sum((y - promedio_Y) ** 2 for y in Y) / (len(Y) - 1))

    if(SX == 0 or SY == 0):
        return 0.0
    print(f"Covarianza x: {SX}")
    print(f"Covarianza y: {SY}")
    suma_producto_desviaciones = sum((X[i] - promedio_X) * (Y[i] - promedio_Y) for i in range(len(X)))

    # Calcular coeficiente de correlación de Pearson y coeficiente de determinación
    r = suma_producto_desviaciones / ((len(X) - 1) * SX * SY)
    r_cuadrado = r ** 2

    print(f"Coeficiente de correlación de Pearson: {r}")


    return r_cuadrado*100


def procesar_informes_voluntarios(uid_voluntario,anio,mes,tz, anio_actual,mes_actual, mexico_time):
    fecha_creacion = obtener_fecha_creacion(uid_voluntario)

    fecha_creacion_local = fecha_creacion.astimezone(tz)

    ejecuciones = contar_ejecuciones_algoritmo(fecha_creacion_local,anio_actual, mes_actual)

    publicaciones = obtener_publicaciones_por_voluntario(uid_voluntario, anio, mes, tz)
    print(f"El voluntario {uid_voluntario} ha realizado un total de {publicaciones} publicaciones en {mes}/{anio}.")

    total_horas = obtener_horas_por_voluntario(uid_voluntario, anio, mes, tz)
    print(f"El voluntario {uid_voluntario} ha realizado un total de {total_horas} horas en {mes}/{anio}.")

    numero_asistencias = obtener_numero_asistencias_voluntario(uid_voluntario, anio, mes, tz)
    print(f"El voluntario {uid_voluntario} asistió a {numero_asistencias} eventos en {mes}/{anio}.")

    nuevas_amistades = obtener_nuevas_amistades(uid_voluntario, anio, mes, tz)
    print(f"El voluntario {uid_voluntario} hizo {nuevas_amistades} nuevas amistades en {mes}/{anio}.")


    posicion = obtener_posicion_ranking(uid_voluntario,anio,mes,tz)

    if posicion != -1:
        print(f"La posición del voluntario {uid_voluntario} en el ranking es: {posicion}")
    else:
        print(f"El voluntario {uid_voluntario} no se encuentra en el ranking.")

    total_reacciones = obtener_suma_reacciones(uid_voluntario, anio, mes, tz)
    print(f"El voluntario {uid_voluntario} obtuvo un total de {total_reacciones} reacciones en sus publicaciones durante {mes}/{anio}.")


    print("--------------")
    print("Nuevas amistades:")
    valor_mes_anterior_amistades, metricas_anteriores_amistades = obtener_metricas_comparativas(uid_voluntario, tz, obtener_nuevas_amistades, mexico_time,ejecuciones)
    if(metricas_anteriores_amistades == []):
        variacion_nuevas_amistades = []
    else:
        variacion_nuevas_amistades = calcular_variacion_comparativa(valor_mes_anterior_amistades, metricas_anteriores_amistades)
        print(f"Variación de nuevas amistades comparada con el mes anterior: {variacion_nuevas_amistades}%")
    print("--------------")


    print("--------------")
    print("Reacciones:")
    valor_mes_anterior_reacciones, metricas_anteriores_reacciones = obtener_metricas_comparativas(uid_voluntario, tz, obtener_suma_reacciones, mexico_time,ejecuciones)
    if(metricas_anteriores_reacciones == []):
        variacion_reacciones = []
    else:
        variacion_reacciones = calcular_variacion_comparativa(valor_mes_anterior_reacciones, metricas_anteriores_reacciones)
        print(f"Variación de reacciones comparada con el mes anterior: {variacion_reacciones}%")


    print("--------------")
    print("Publicaciones:")
    valor_mes_anterior_publicaciones, metricas_anteriores_publicaciones = obtener_metricas_comparativas(uid_voluntario, tz, obtener_publicaciones_por_voluntario, mexico_time,ejecuciones)
    if(metricas_anteriores_publicaciones == []):
        variacion_publicaciones = []
    else:
        variacion_publicaciones = calcular_variacion_comparativa(valor_mes_anterior_publicaciones, metricas_anteriores_publicaciones)
        print(f"Variación de publicaciones comparada con el mes anterior: {variacion_publicaciones}%")


    print("--------------")
    print("Horas voluntariado:")
    valor_mes_anterior_horas, metricas_anteriores_horas = obtener_metricas_comparativas(uid_voluntario, tz, obtener_horas_por_voluntario, mexico_time,ejecuciones)

    if(metricas_anteriores_horas == []):
        variacion_horas = []
    else:
        variacion_horas = calcular_variacion_comparativa(valor_mes_anterior_horas, metricas_anteriores_horas)
        print(f"Variación de horas de voluntariado comparada con el mes anterior: {variacion_horas}%")

    print("--------------")
    print("Eventos asistidos:")
    valor_mes_anterior_eventos, metricas_anteriores_eventos = obtener_metricas_comparativas(uid_voluntario, tz, obtener_numero_asistencias_voluntario, mexico_time,ejecuciones)
    if(metricas_anteriores_publicaciones == []):
        variacion_eventos = []
    else:
        variacion_eventos = calcular_variacion_comparativa(valor_mes_anterior_eventos, metricas_anteriores_eventos)
        print(f"Variación de eventos asistidos comparada con el mes anterior: {variacion_eventos}%")

    print(f'Eventos asistidos mes previo {valor_mes_anterior_eventos} , historial {metricas_anteriores_eventos}')

    print("--------------")
    print("Ranking:")

    valor_mes_anterior_ranking, metricas_anteriores_ranking = obtener_metricas_comparativas(uid_voluntario, tz, obtener_posicion_ranking, mexico_time,ejecuciones)\

    if(metricas_anteriores_ranking == []):
        variacion_ranking = []
    else:
        variacion_ranking = calcular_variacion_comparativa(valor_mes_anterior_ranking, metricas_anteriores_ranking)
        print(f"Variación de posicion ranking con el mes anterior: {variacion_ranking}%")

    print("--------------")
    print("Reacciones:")
    contador_reacciones = obtener_reacciones_por_voluntario(uid_voluntario, anio, mes, tz)
    porcentajes_reacciones = calcular_porcentajes_reacciones(contador_reacciones)

    print("Contador de reacciones:", contador_reacciones)
    print("Porcentajes de reacciones:", porcentajes_reacciones)

    # Realizar y mostrar el análisis de correlación para eventos asistidos y nuevas amistades
    print("Análisis de correlación para eventos asistidos y nuevas amistades:")
    #Variables
    Xi = metricas_anteriores_eventos.copy()
    Xi.insert(0,valor_mes_anterior_eventos)

    Yi = metricas_anteriores_amistades.copy()
    Yi.insert(0,valor_mes_anterior_amistades)

    coeficiente_determinacion_eventos_amigos = analizar_correlacion(Xi,Yi)
    print(f"coeficiente de determinacion: {coeficiente_determinacion_eventos_amigos}")
    print("--------------")

    Xi = metricas_anteriores_eventos.copy()
    Xi.insert(0,valor_mes_anterior_eventos)

    Yi = metricas_anteriores_publicaciones.copy()
    Yi.insert(0,valor_mes_anterior_publicaciones)

    print("Análisis de correlación para eventos asistidos y nuevas amistades:")
    coeficiente_determinacion_eventos_publicaciones = analizar_correlacion(Xi,Yi)
    print(f"Porcentaje del coeficiente de determinacion: {coeficiente_determinacion_eventos_publicaciones}")
    print("--------------")

    resultados = {
       "uidVoluntario" : uid_voluntario,
        "date" : firestore.SERVER_TIMESTAMP,
        "total_publicaciones": publicaciones,
        "total_horas": total_horas,
        "total_numero_asistencias": numero_asistencias,
        "total_nuevas_amistades": nuevas_amistades,
        "posicion_ranking": posicion,
        "total_reacciones": total_reacciones,

        "variacion_nuevas_amistades": float(variacion_nuevas_amistades) if not isinstance(variacion_nuevas_amistades, list) else variacion_nuevas_amistades,
        "variacion_reacciones": float(variacion_reacciones) if not isinstance(variacion_reacciones, list) else variacion_reacciones,
        "variacion_publicaciones": float(variacion_publicaciones) if not isinstance(variacion_publicaciones, list) else variacion_publicaciones,
        "variacion_horas": float(variacion_horas) if not isinstance(variacion_horas, list) else variacion_horas,
        "variacion_eventos": float(variacion_eventos) if not isinstance(variacion_eventos, list) else variacion_eventos,
        "variacion_ranking": float(variacion_ranking) if not isinstance(variacion_ranking, list) else variacion_ranking,
    
        "porcentajes_reacciones": porcentajes_reacciones,

        "coeficiente_determinacion_eventos_amigos": coeficiente_determinacion_eventos_amigos,
        "coeficiente_determinacion_eventos_publicaciones": coeficiente_determinacion_eventos_publicaciones,
    }


    return resultados



def enviar_correo(destinatario, mes):
    # Datos a enviar en el cuerpo de la solicitud
    datos_email = {
        "destinatario": destinatario,
        "asunto": "Informe mensual",
        "mensaje": f"Felicidades tu reporte del mes de {mes} ya esta disponible"
    }

    # Llamar a la primera API
    respuesta = requests.post(
        'https://us-central1-voluntred-9b82e.cloudfunctions.net/send_email',
        json=datos_email  # Usamos el argumento json para enviar los datos
    )

    if respuesta.status_code == 200:
        print("Correo enviado exitosamente.")
        print("Respuesta:", respuesta.text)
        return 200
    else:
        # Manejar errores o fallas en la respuesta
        print(f"Error al enviar el correo: {respuesta.status_code}")
        return None







def informes_voluntario(): 
    # Definir los nombres de los meses en español
    nombres_meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


    tz = pytz.timezone('America/Mexico_City')
    mexico_time = datetime.now(tz)

   # if mexico_time.day != 1:
    #    return ('Hoy no es el primer día del mes.', 0)

    mes_anterior = mexico_time - relativedelta(months=1)
    mes = mes_anterior.month
    anio = mes_anterior.year
    anio_actual = mexico_time.year
    mes_actual = mexico_time.month

    voluntarios = db.collection('voluntarios').stream()

    nombre_mes_actual = nombres_meses[mes_actual - 1]  # Los índices de la lista comienzan en 0

    for voluntario in voluntarios:
    # Obtiene el ID del documento
        
        uid_voluntario = voluntario.id

        if 'correoElectronico' in voluntario.to_dict():
            correo_electronico = voluntario.get('correoElectronico')
            enviar_correo(correo_electronico,nombre_mes_actual)

            print(f"Correo electrónico: {correo_electronico}")
        else:
            print("El voluntario no tiene un correo electrónico registrado.")
        

        print(f'Voluntario con UID {uid_voluntario} \n')
        resultados = procesar_informes_voluntarios(uid_voluntario,anio,mes,tz,anio_actual,mes_actual,mexico_time)
        doc_ref = db.collection('informesVoluntarios').document()  # Esto crea un nuevo documento con un ID único.
        doc_ref.set(resultados)

     
        print(" \n out...........")
        print(resultados)
        

    

 
informes_voluntario()