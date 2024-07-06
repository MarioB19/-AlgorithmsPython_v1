import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz
import math
import warnings
from dateutil import parser
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
from scipy import stats

warnings.filterwarnings("ignore")


cred = credentials.Certificate('voluntred-9b82e-firebase-adminsdk-xe4ed-cddbd4b29e.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

def obtener_fecha_creacion(uid):
    # Inicializa el cliente de Firestore
    db = firestore.client()

    # Referencia al documento del voluntario basado en uid
    doc_ref = db.collection('asociacion').document(uid)
    doc = doc_ref.get()

    # Retorna el campo fechaCreacion si el documento existe
    return doc.to_dict().get('fechaAceptado', 'La fecha de creación no está disponible')


def obtener_publicaciones_por_ong(uid_ong, anio, mes, tz):
    # Primer día del mes anterior
    inicio_mes = datetime(anio, mes, 1, tzinfo=tz)
    # Último día del mes anterior
    if mes == 12:
        fin_mes = datetime(anio + 1, 1, 1, tzinfo=tz)
    else:
        fin_mes = datetime(anio, mes + 1, 1, tzinfo=tz)

    # Contar las publicaciones por uidOng del mes anterior
    query = db.collection('publicacionesAsociaciones')\
        .where('uidAutor', "==", uid_ong)\
        .where('date', '>=', inicio_mes)\
        .where('date', '<', fin_mes)\
        .stream()

    # Contar el número de publicaciones
    numero_publicaciones = sum(1 for _ in query)

    return numero_publicaciones

def obtener_eventos_por_ong(uid_ong, anio, mes, tz):
    # Primer día del mes especificado
    inicio_mes = datetime(anio, mes, 1, tzinfo=tz)
    # Último día del mes especificado
    if mes == 12:
        fin_mes = datetime(anio + 1, 1, 1, tzinfo=tz)
    else:
        fin_mes = datetime(anio, mes + 1, 1, tzinfo=tz)

    # Contar los eventos por uidOng en el mes especificado
    query = db.collection('eventos')\
        .where('uidONG', "==", uid_ong)\
        .where('fechaCreacion', '>=', inicio_mes)\
        .where('fechaCreacion', '<', fin_mes)\
        .stream()

    # Contar el número de eventos
    numero_eventos = sum(1 for _ in query)

    return numero_eventos



def suma_horas_eventos_ong(uid_ong, anio, mes, tz):
    inicio_mes = datetime(anio, mes, 1, tzinfo=tz)
    if mes == 12:
        fin_mes = datetime(anio + 1, 1, 1, tzinfo=tz)
    else:
        fin_mes = datetime(anio, mes + 1, 1, tzinfo=tz)

    query = db.collection('eventos')\
        .where('uidONG', "==", uid_ong)\
        .where("estado", "==", "Pasado")\
        .where('fechaCreacion', '>=', inicio_mes)\
        .where('fechaCreacion', '<', fin_mes)\
        .stream()

    suma_horas = 0
    for evento_snapshot in query:
        evento = evento_snapshot.to_dict()  # Convierte el DocumentSnapshot a un diccionario
        if 'timeInicio' in evento and 'timeFin' in evento:
            formato_tiempo = '%I:%M %p'
            # Convertir timeInicio y timeFin a objetos datetime
            inicio = parser.parse(evento['timeInicio'], ignoretz=True)
            fin = parser.parse(evento['timeFin'], ignoretz=True)
            # Calcular la duración y convertirla a horas
            duracion = (fin - inicio).seconds / 3600
            suma_horas += max(0, duracion)  # Sumar solo si la duración es positiva

    return suma_horas

def obtener_nuevos_seguidores_ong(uid_ong, anio, mes, tz):
    # Primer día del mes especificado
    inicio_mes = datetime(anio, mes, 1, tzinfo=tz)
    # Último día del mes especificado
    if mes == 12:
        fin_mes = datetime(anio + 1, 1, 1, tzinfo=tz)
    else:
        fin_mes = datetime(anio, mes + 1, 1, tzinfo=tz)

    # Contar los nuevos seguidores por uidOng en el mes especificado
    query = db.collection('seguimientosONG')\
        .where('uidOng', "==", uid_ong)\
        .where('fechaSeguimientoONG', '>=', inicio_mes)\
        .where('fechaSeguimientoONG', '<', fin_mes)\
        .stream()

    # Contar el número de nuevos seguidores
    numero_seguidores = sum(1 for _ in query)

    return numero_seguidores

def obtener_inscritos_eventos_ong(uid_ong, anio, mes, tz):
    # Primer día del mes especificado
    inicio_mes = datetime(anio, mes, 1, tzinfo=tz)
    # Último día del mes especificado
    if mes == 12:
        fin_mes = datetime(anio + 1, 1, 1, tzinfo=tz)
    else:
        fin_mes = datetime(anio, mes + 1, 1, tzinfo=tz)

    # Obtener los eventos por uidONG en el mes especificado
    eventos_query = db.collection_group('voluntariosInscritos')\
        .where('uidONG', "==", uid_ong)\
        .where('fechaInscripcion', '>=', inicio_mes)\
        .where('fechaInscripcion', '<', fin_mes)\
        .stream()

    # Sumar el número de voluntarios inscritos en cada evento
    total_inscritos = 0
    for evento in eventos_query:
       total_inscritos +=1

    return total_inscritos


def calcular_edad_promedio_voluntarios(uid_ong, anio, mes, tz):
    inicio_mes = datetime(anio, mes, 1, tzinfo=tz)
    if mes == 12:
        fin_mes = datetime(anio + 1, 1, 1, tzinfo=tz)
    else:
        fin_mes = datetime(anio, mes + 1, 1, tzinfo=tz)

    eventos_query = db.collection_group('voluntariosInscritos')\
        .where('uidONG', "==", uid_ong)\
        .where('fechaInscripcion', '>=', inicio_mes)\
        .where('fechaInscripcion', '<', fin_mes)\
        .stream()


    uid_voluntarios_unicos = set()
    edades = []

    for evento in eventos_query:
        uid_voluntario = evento.get('uidVoluntario')

        if uid_voluntario not in uid_voluntarios_unicos:
            uid_voluntarios_unicos.add(uid_voluntario)
            voluntario_data = db.collection('voluntarios').document(uid_voluntario).get()

            if voluntario_data.exists:
                fecha_nacimiento_str = voluntario_data.get('fechaNacimiento')
                fecha_nacimiento = parser.parse(fecha_nacimiento_str, dayfirst=True).date()
                edad = relativedelta(datetime.now().date(), fecha_nacimiento).years
                edades.append(edad)

    if len(edades) > 0:
        edad_promedio = sum(edades) / len(edades)
    else:
        edad_promedio = 0

    return edad_promedio



def obtener_promedio_calificaciones_eventos(uid_ong, anio, mes, tz):
    inicio_mes = datetime(anio, mes, 1, tzinfo=tz)
    if mes == 12:
        fin_mes = datetime(anio + 1, 1, 1, tzinfo=tz)
    else:
        fin_mes = datetime(anio, mes + 1, 1, tzinfo=tz)

    eventos_query = db.collection('eventos')\
        .where('uidONG', "==", uid_ong)\
        .where("estado", "==", "Pasado")\
        .where('fechaCreacion', '>=', inicio_mes)\
        .where('fechaCreacion', '<', fin_mes)\
        .stream()

    total_calificaciones = 0
    numero_calificaciones = 0

    for evento in eventos_query:
        promedio_calificaciones = evento.get('promedioCalificaciones')
        if promedio_calificaciones:
            promedio_evento = sum(promedio_calificaciones.values()) / len(promedio_calificaciones)
            total_calificaciones += promedio_evento
            numero_calificaciones += 1

    # Calcular el promedio general de las calificaciones de todos los eventos
    if numero_calificaciones > 0:
        promedio_general = total_calificaciones / numero_calificaciones
    else:
        promedio_general = 0

    return promedio_general




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

       # Define los valores predeterminados para minMes y maxMes
    minMes = 2
    maxMes = 8

    # Ajusta minMes y maxMes según el número de ejecuciones
    if ejecuciones > 7:
        minMes = 2
        maxMes = 8

    if ejecuciones < 2:
        return valor_mes_anterior, []
    
    if ejecuciones >=2 and ejecuciones<=7:
        minMes = 2
        maxMes = ejecuciones+1
    

    for i in range(minMes, maxMes):  
        mes_evaluado = mexico_time - relativedelta(months=i)
        valor = obtener_metrica(uid_voluntario, mes_evaluado.year, mes_evaluado.month, tz)
        metricas.append(valor)


    return valor_mes_anterior, metricas


def calcular_variacion_comparativa(valor_mes_anterior, metricas_anteriores):
    promedio_meses_anteriores = sum(metricas_anteriores) / len(metricas_anteriores) if metricas_anteriores else 0
    
    if promedio_meses_anteriores == 0:
        variacion_porcentaje = valor_mes_anterior * 100
    else:
        variacion = (valor_mes_anterior - promedio_meses_anteriores) / promedio_meses_anteriores
        variacion_porcentaje = round(variacion * 100, 2)  
    return variacion_porcentaje



def obtener_total_reacciones_por_ong(uid_ong, anio, mes, tz):
    inicio_mes = datetime(anio, mes, 1, tzinfo=tz)
    fin_mes = inicio_mes + relativedelta(months=1)

    reacciones = db.collection_group('reacciones')\
        .where('uidAutor', '==', uid_ong)\
        .where('fechaReaccion', '>=', inicio_mes)\
        .where('fechaReaccion', '<', fin_mes)\
        .stream()

    total_reacciones = 0

    for reaccion in reacciones:
        doc = reaccion.to_dict()
        # Cada vez que se encuentra una reacción, independientemente de su tipo, incrementa el total
        if doc.get('reaccionHecha') in ['meGusta', 'meEncanta', 'meDivierte', 'meEnoja', 'meEntristece']:
            total_reacciones += 1

    return total_reacciones


def obtener_reacciones_por_ong(uid_ong, anio, mes, tz):
    inicio_mes = datetime(anio, mes, 1, tzinfo=tz)
    fin_mes = inicio_mes + relativedelta(months=1)

    reacciones = db.collection_group('reacciones')\
        .where('uidAutor', '==', uid_ong)\
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

def analizar_correlacion_publicaciones_seguidores(uid_ong, anio, mes, tz):
    def obtener_datos_diarios():
        inicio_mes = datetime(anio, mes, 1, tzinfo=tz)
        fin_mes = inicio_mes + relativedelta(months=1)

        publicaciones_diarias = [0] * (fin_mes - inicio_mes).days
        seguidores_diarios = [0] * (fin_mes - inicio_mes).days

        publicaciones = db.collection('publicacionesAsociaciones')\
                          .where('uidAutor', '==', uid_ong)\
                          .where('date', '>=', inicio_mes)\
                          .where('date', '<', fin_mes)\
                          .stream()

        for publicacion in publicaciones:
            dia = publicacion.to_dict().get('date').day
            publicaciones_diarias[dia - 1] += 1

        seguidores = db.collection('seguimientosONG')\
                        .where('uidOng', '==', uid_ong)\
                        .where('fechaSeguimientoONG', '>=', inicio_mes)\
                        .where('fechaSeguimientoONG', '<', fin_mes)\
                        .stream()

        for seguidor in seguidores:
            dia = seguidor.to_dict().get('fechaSeguimientoONG').day
            seguidores_diarios[dia - 1] += 1

        return publicaciones_diarias, seguidores_diarios

    def calcular_promedio(datos):
        if(len(datos) == 0):
            return 0
        return sum(datos) / len(datos)

    def calcular_desviaciones(datos, promedio):
        return [dato - promedio for dato in datos]

    publicaciones_diarias, seguidores_diarios = obtener_datos_diarios()

    promedio_publicaciones = calcular_promedio(publicaciones_diarias)
    promedio_seguidores = calcular_promedio(seguidores_diarios)

    desviaciones_publicaciones = calcular_desviaciones(publicaciones_diarias, promedio_publicaciones)
    desviaciones_seguidores = calcular_desviaciones(seguidores_diarios, promedio_seguidores)

    sum_desv = sum(d_pub * d_seg for d_pub, d_seg in zip(desviaciones_publicaciones, desviaciones_seguidores))

    varianza_pub = sum((x - promedio_publicaciones) ** 2 for x in publicaciones_diarias) / len(publicaciones_diarias)
    varianza_seg = sum((x - promedio_seguidores) ** 2 for x in seguidores_diarios) / len(seguidores_diarios)

    varianza_pub = abs(varianza_pub)
    varianza_seg = abs(varianza_seg)

    sigma_pub = np.sqrt(varianza_pub)
    sigma_seg = np.sqrt(varianza_seg)

    if( (sigma_pub * sigma_seg * len(publicaciones_diarias)) ==0):
        return 0.0

    coeficiente_correlacion = sum_desv / (sigma_pub * sigma_seg * len(publicaciones_diarias))
    coeficiente_determinacion = coeficiente_correlacion ** 2


    return coeficiente_determinacion *100

def analizar_correlacion_eventos_publicaciones(uid_ong, tz, mexico_time):
    # Obtener el número de ejecuciones/meses disponibles para el análisis
    fecha_creacion = obtener_fecha_creacion(uid_ong)
    fecha_creacion_local = fecha_creacion.astimezone(tz)
    ejecuciones = contar_ejecuciones_algoritmo(fecha_creacion_local, mexico_time.year, mexico_time.month)

    minMes = 1
    maxMes = 8

    # Ajusta minMes y maxMes según el número de ejecuciones
    if ejecuciones > 7:
        minMes = 1
        maxMes = 8

    if ejecuciones < 2:

        return 0.0

    if 2 <= ejecuciones <= 7:
        minMes = 1
        maxMes = ejecuciones + 1

    # Inicializar las listas para almacenar los datos de voluntarios inscritos y publicaciones
    X = []  # Número de publicaciones hechas
    Y = []  # Número de inscritos

    # Iterar sobre los meses disponibles
    
    for i in range(minMes, maxMes):
        mes_evaluado = mexico_time - relativedelta(months=i)
        publicaciones = obtener_publicaciones_por_ong(uid_ong, mes_evaluado.year, mes_evaluado.month, tz)
        inscritos = obtener_inscritos_eventos_ong(uid_ong, mes_evaluado.year, mes_evaluado.month, tz)

        X.append(publicaciones)
        Y.append(inscritos)

    if(len(X)-1 == 0 or len(Y)-1 == 0):
        return 0.0
    
    # Calcular el promedio de eventos asistidos y nuevos amigos
    promedio_X = sum(X) / len(X) if X else 0  # división por cero
    promedio_Y = sum(Y) / len(Y) if Y else 0  # división por cero

    
    SX = math.sqrt(sum((x - promedio_X) ** 2 for x in X) / (len(X) - 1))
    SY = math.sqrt(sum((y - promedio_Y) ** 2 for y in Y) / (len(Y) - 1))
    
    suma_producto_desviaciones = sum((X[i] - promedio_X) * (Y[i] - promedio_Y) for i in range(len(X)))

    # Calcular coeficiente de correlación de Pearson y coeficiente de determinación

    if(((len(X) - 1) * SX * SY ) == 0):
        return 0
    
    r = suma_producto_desviaciones / ((len(X) - 1) * SX * SY)
    r_cuadrado = r ** 2


    
    return r_cuadrado*100

# Esta función obtiene las edades de los voluntarios, contribuyendo al RQF458 y RQF460
def obtener_edades_voluntarios(uid_ong, anio, mes, tz):
    # Establece el rango de fechas para el mes en cuestión
    inicio_mes = datetime(anio, mes, 1, tzinfo=tz)
    fin_mes = datetime(anio + 1, 1, 1, tzinfo=tz) if mes == 12 else datetime(anio, mes + 1, 1, tzinfo=tz)

    # Consulta los eventos pasados para el ONG y el mes especificado
    eventos_query = db.collection_group('voluntariosInscritos')\
        .where('uidONG', "==", uid_ong)\
        .where('fechaInscripcion', '>=', inicio_mes)\
        .where('fechaInscripcion', '<', fin_mes)\
        .stream()


    # Inicializa un conjunto para mantener únicos los ID de los voluntarios
    uid_voluntarios_unicos = set()
    edades = []

    # Itera sobre cada evento
    for evento in eventos_query:
        uid_voluntario = evento.get('uidVoluntario')
        if uid_voluntario not in uid_voluntarios_unicos:
            uid_voluntarios_unicos.add(uid_voluntario)
            voluntario_data = db.collection('voluntarios').document(uid_voluntario).get()
            if voluntario_data.exists:
                fecha_nacimiento_str = voluntario_data.get('fechaNacimiento')
                fecha_nacimiento = parser.parse(fecha_nacimiento_str, dayfirst=True).date()
                edad = relativedelta(datetime.now().date(), fecha_nacimiento).years
                edades.append(edad)  # Agrega la edad calculada a la lista
    
    return edades

# Esta función aplica el algoritmo de tendencia, relacionándose con RQF458 a RQF469
def algoritmo_tendencia(uid_ong, anio, mes, tz):
    edades = obtener_edades_voluntarios(uid_ong, anio, mes, tz)
    N = len(edades)  # RQF458: Total de voluntarios

    if(len(edades) == 0):
        return 0,0,0
    
    # RQF459: Define los rangos de edad
    rangos = [(18, 25), (26, 35), (36, 45), (46, 55), (56, 65), (66, 75), (76, 100)]
    F = [0] * len(rangos)  # RQF461: Inicializa el vector de frecuencias


    # RQF460: Cuenta los voluntarios en cada rango de edad
    for edad in edades:
        for i, (inicio, fin) in enumerate(rangos):
            if inicio <= edad <= fin:
                F[i] += 1
                break

    # RQF462: Calcula la proporción de voluntarios en cada rango de edad
    P = [f / N for f in F]

    # RQF464: Calcula los puntos medios de cada rango de edad
    puntos_medios = [np.mean(rango) for rango in rangos]

 

    puntos_medios_array = np.array(puntos_medios)
    proporcion_array = np.array(P)
    # RQF467 a RQF469: Realiza una regresión lineal para encontrar la tendencia
    # Cálculo de los coeficientes de la regresión lineal
    coeficientes = np.polyfit(puntos_medios_array, proporcion_array, 1)


    pendiente = coeficientes[0]
    intercepto = coeficientes[1]

    # Imprime la ecuación de la línea de tendencia

    # Devuelve los resultados, que podrían ser utilizados para graficar o análisis adicional
    return intercepto, pendiente, P



def procesar_informes_ong(uid_ong,anio,mes,anio_actual,mes_actual, tz, mexico_time):

    fecha_creacion = obtener_fecha_creacion(uid_ong)

    fecha_creacion_local = fecha_creacion.astimezone(tz)
    ejecuciones = contar_ejecuciones_algoritmo(fecha_creacion_local,anio_actual, mes_actual)

    #--------------------------Comienza Algoritmo----------------------------------------

    seguidores = obtener_nuevos_seguidores_ong(uid_ong, anio, mes, tz)
  

    eventos = obtener_eventos_por_ong(uid_ong, anio, mes, tz)


    publicaciones = obtener_publicaciones_por_ong(uid_ong, anio, mes, tz)


    horas_eventos = suma_horas_eventos_ong(uid_ong,anio, mes, tz)
  

    inscritos= obtener_inscritos_eventos_ong(uid_ong,anio, mes, tz)

    edad_promedio=calcular_edad_promedio_voluntarios(uid_ong, anio, mes, tz)
  
    promedio_calificaciones =obtener_promedio_calificaciones_eventos(uid_ong, anio, mes, tz)

    total_reacciones = obtener_total_reacciones_por_ong(uid_ong, anio, mes, tz)

    valor_mes_anterior_reacciones, metricas_anteriores_reacciones = obtener_metricas_comparativas(uid_ong, tz, obtener_total_reacciones_por_ong, mexico_time,ejecuciones)
    if(metricas_anteriores_reacciones == []):
        variacion_reacciones = []
    else:
        variacion_reacciones = calcular_variacion_comparativa(valor_mes_anterior_reacciones, metricas_anteriores_reacciones)
      
    valor_mes_anterior_calificaciones, metricas_anteriores_calificaciones = obtener_metricas_comparativas(uid_ong, tz, obtener_promedio_calificaciones_eventos, mexico_time,ejecuciones)
    if(metricas_anteriores_calificaciones == []):
        variacion_calificaciones = []
    else:
        variacion_calificaciones = calcular_variacion_comparativa(valor_mes_anterior_calificaciones, metricas_anteriores_calificaciones)
    
    valor_mes_anterior_edades, metricas_anteriores_edades = obtener_metricas_comparativas(uid_ong, tz, calcular_edad_promedio_voluntarios, mexico_time,ejecuciones)
    if(metricas_anteriores_edades == []):
        variacion_edades = []
    else:
        variacion_edades = calcular_variacion_comparativa(valor_mes_anterior_edades, metricas_anteriores_edades)
      
    valor_mes_anterior_inscritos, metricas_anteriores_inscritos = obtener_metricas_comparativas(uid_ong, tz, obtener_inscritos_eventos_ong, mexico_time,ejecuciones)
    if(metricas_anteriores_inscritos== []):
        variacion_inscritos = []
    else:
        variacion_inscritos = calcular_variacion_comparativa(valor_mes_anterior_inscritos, metricas_anteriores_inscritos)

    valor_mes_anterior_horas_realizadas, metricas_anteriores_horas_realizadas = obtener_metricas_comparativas(uid_ong, tz, suma_horas_eventos_ong, mexico_time,ejecuciones)
    if(metricas_anteriores_horas_realizadas == []):
        variacion_horas_realizadas = []
    else:
        variacion_horas_realizadas = calcular_variacion_comparativa(valor_mes_anterior_horas_realizadas, metricas_anteriores_horas_realizadas)

     
    valor_mes_anterior_publicaciones, metricas_anteriores_publicaciones= obtener_metricas_comparativas(uid_ong, tz, obtener_publicaciones_por_ong, mexico_time,ejecuciones)
    if(metricas_anteriores_publicaciones== []):
        variacion_publicaciones = []
    else:
        variacion_publicaciones = calcular_variacion_comparativa(valor_mes_anterior_publicaciones, metricas_anteriores_publicaciones)
   
    valor_mes_anterior_eventos, metricas_anteriores_eventos = obtener_metricas_comparativas(uid_ong, tz, obtener_eventos_por_ong, mexico_time,ejecuciones)
    if(metricas_anteriores_eventos == []):
        variacion_eventos = []
    else:
        variacion_eventos = calcular_variacion_comparativa(valor_mes_anterior_eventos, metricas_anteriores_eventos)
   
    valor_mes_anterior_seguidores, metricas_anteriores_seguidores = obtener_metricas_comparativas(uid_ong, tz, obtener_nuevos_seguidores_ong, mexico_time,ejecuciones)
    if(metricas_anteriores_seguidores == []):
        variacion_seguidores = []
    else:
        variacion_seguidores = calcular_variacion_comparativa(valor_mes_anterior_seguidores, metricas_anteriores_seguidores)
   
    

    contador_reacciones = obtener_reacciones_por_ong(uid_ong, anio, mes, tz)
    porcentajes_reacciones = calcular_porcentajes_reacciones(contador_reacciones)


    coeficiente_determinacion_publicaciones_seguidores = analizar_correlacion_publicaciones_seguidores(uid_ong, anio, mes, tz)
  
   
    coeficiente_determinacion_eventos_publicaciones = analizar_correlacion_eventos_publicaciones(uid_ong, tz, mexico_time)



    intercepto,pendiente, proporciones = algoritmo_tendencia(uid_ong, anio, mes, tz)

    resultados = {
        "uidONG" : uid_ong,
        "date" : firestore.SERVER_TIMESTAMP,
        "total_seguidores":seguidores,
        "total_eventos": eventos,
        "total_publicaciones": publicaciones,
        "total_horas_eventos": horas_eventos,
        "total_inscritos": inscritos,
        "total_edad_promedio": edad_promedio,
        "total_promedio_calificaciones": promedio_calificaciones,
        "total_reacciones": total_reacciones,

        "variacion_seguidores": float(variacion_seguidores) if not isinstance(variacion_seguidores, list) else variacion_seguidores,
        "variacion_eventos": float(variacion_eventos) if not isinstance(variacion_eventos, list) else variacion_eventos,
        "variacion_publicaciones": float(variacion_publicaciones) if not isinstance(variacion_publicaciones, list) else variacion_publicaciones,
        "variacion_horas_eventos": float(variacion_horas_realizadas) if not isinstance(variacion_horas_realizadas, list) else variacion_horas_realizadas,
        "variacion_inscritos": float(variacion_inscritos) if not isinstance(variacion_inscritos, list) else variacion_inscritos,
        "variacion_edad_promedio": float(variacion_edades) if not isinstance(variacion_edades, list) else variacion_edades,
        "variacion_promedio_calificaciones": float(variacion_calificaciones) if not isinstance(variacion_calificaciones, list) else variacion_calificaciones,
        "variacion_reacciones": float(variacion_reacciones) if not isinstance(variacion_reacciones, list) else variacion_reacciones,

        



        "porcentajes_reacciones": porcentajes_reacciones,
        "coeficiente_determinacion_publicaciones_seguidores": coeficiente_determinacion_publicaciones_seguidores,
        "coeficiente_determinacion_eventos_publicaciones": coeficiente_determinacion_eventos_publicaciones,
       
        "tendencia": {
            "intercepto": float(intercepto),
            "pendiente": float( pendiente),
            "proporciones":   float(proporciones) if not isinstance(proporciones, list) else proporciones
          
        }
        
    }

    return resultados



def informes_ong():
    tz = pytz.timezone('America/Mexico_City')
    mexico_time = datetime.now(tz)
    anio_actual = mexico_time.year
    mes_actual = mexico_time.month

   # if mexico_time.day != 1:
    #    return ('Hoy no es el primer día del mes.', 0)

    mes_anterior = mexico_time - relativedelta(months=1)
    mes = mes_anterior.month
    anio = mes_anterior.year

    asociaciones = db.collection('asociacion').stream()

    for asociacion in asociaciones:
    # Obtiene el ID del documento
        
        uid_ong = asociacion.id

      
        resultados = procesar_informes_ong(uid_ong,anio,mes,anio_actual,mes_actual, tz, mexico_time)
        doc_ref = db.collection('informesAsociaciones').document()  # Esto crea un nuevo documento con un ID único.
        doc_ref.set(resultados)
     
 
        

    
  



informes_ong()