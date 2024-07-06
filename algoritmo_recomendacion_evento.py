from flask import jsonify
from firebase_admin import firestore
from dateutil import parser
import firebase_admin
from firebase_admin import credentials
from math import exp, pi, sqrt
from collections import Counter
import calendar
import re

# Inicializar la aplicación de Firebase
cred = credentials.Certificate('voluntred-9b82e-firebase-adminsdk-xe4ed-cddbd4b29e.json')
firebase_admin.initialize_app(cred)



def obtener_eventos_futuros(eventos):
    # Filtra y mantiene solo los eventos con estado igual a 'Futuro'
    eventos_futuros = [evento for evento in eventos if evento.get('estado') == 'Futuro']

    # Lista para almacenar la información de los eventos futuros
    eventos_filtrados = []

    for evento in eventos_futuros:
        evento_info = {
            'date': evento.get('date'),
            'descriptionPlain': evento.get('descriptionPlain'),
            'odsTags': evento.get('odsTags'),
            'timeFin': evento.get('timeFin'),
            'timeInicio': evento.get('timeInicio'),
            'uidONG': evento.get('uidONG'),
            'uidEvento': evento.get('uidEvento'),
            'estado' : evento.get('estado')
        }
        eventos_filtrados.append(evento_info)

    return eventos_filtrados



def obtener_ods_preferidas(uid_voluntario):
 
    # Suponiendo que los voluntarios están almacenados en una colección llamada 'voluntarios'
    voluntario_ref = db.collection('voluntarios').document(uid_voluntario)
    voluntario_doc = voluntario_ref.get()

    if voluntario_doc.exists:
        ods_preferidas = voluntario_doc.to_dict().get('odsPreferidas', [])
        #print(f"ODS preferidas para el voluntario {uid_voluntario}: {ods_preferidas}")
        return ods_preferidas
    else:
        print(f"No se encontró el voluntario con UID {uid_voluntario}")
        return []




def convertir_eventos_a_diccionarios(eventos_stream):
    # Lista para almacenar la información de los eventos
    eventos_lista = []

    for evento in eventos_stream:
        evento_dict = evento.to_dict()  # Convierte el documento Firestore a un diccionario
        evento_info = {
            'date': evento_dict.get('date'),
            'descriptionPlain': evento_dict.get('descriptionPlain'),
            'odsTags': evento_dict.get('odsTags'),
            'timeFin': evento_dict.get('timeFin'),
            'timeInicio': evento_dict.get('timeInicio'),
            'uidONG': evento_dict.get('uidONG'),
            'uidEvento': evento_dict.get('uidEvento'),
            'estado' : evento_dict.get('estado')
        }
        eventos_lista.append(evento_info)

    return eventos_lista




def calcular_desviacion_horario_inicio_eventos(media):
    
    horarios_inicio_minutos_aux = [time_to_minutes(evento.get('timeInicio')) for evento in eventos]

    horarios_inicio_minutos = [abs(minuto - media) for minuto in horarios_inicio_minutos_aux]

    if not horarios_inicio_minutos:
        return 0, 0  # Si no hay horarios, retornamos 0 para ambos valores

    N = len(horarios_inicio_minutos)  # Número total de horarios
    mu = sum(horarios_inicio_minutos) / N  # Promedio de horarios de inicio
    sigma = (sum((x - mu) ** 2 for x in horarios_inicio_minutos) / N) ** 0.5  # Desviación estándar

    return  sigma # Retornamos ambos valores



def calcular_desviacion_duracion_eventos():
    
    duraciones_en_horas = []  # Cambiamos el nombre de la lista para reflejar que ahora contiene horas
    for evento in eventos:
        time_inicio = time_to_minutes(evento.get('timeInicio'))
        time_fin = time_to_minutes(evento.get('timeFin'))

        if time_inicio is not None and time_fin is not None:
            duracion_en_minutos = time_fin - time_inicio
            duracion_en_horas = duracion_en_minutos / 60  # Convertir minutos a horas
            duraciones_en_horas.append(duracion_en_horas)

    print(f"duraciones_en_horas {duraciones_en_horas}")

    if not duraciones_en_horas:
        return 0  # Si no hay duraciones, la desviación estándar es 0

    N = len(duraciones_en_horas)  # Número total de duraciones
    media = sum(duraciones_en_horas) / N  # Promedio de duraciones en horas

    # Calcular la suma de los cuadrados de las diferencias entre cada duración y la media
    suma_cuadrados_diferencias = sum((duracion - media) ** 2 for duracion in duraciones_en_horas)
    
    # Calcular la desviación estándar en horas
    desviacion_estandar = (suma_cuadrados_diferencias / N) ** 0.5

    return desviacion_estandar  # Retornamos la desviación estándar en horas



def obtener_eventos_pasados_con_asistencia(uid_voluntario):

    # Realizar la consulta para obtener los eventos pasados del voluntario
    eventos_query = db.collection_group('voluntariosInscritos') \
                     .where('uidVoluntario', '==', uid_voluntario) \
                     .where('Asistencia', '==', True) \
                     .select(['date','uidONG', 'timeFin', 'timeInicio', 'descriptionPlain']) \
                     .get()

    # Lista para almacenar los resultados
    eventos = []

    # Iterar sobre los resultados de la consulta
    for evento_ref in eventos_query:
        evento_snapshot = evento_ref.reference.parent.parent.get()
        if evento_snapshot.exists:
            evento_dict = evento_snapshot.to_dict()
            # Verificar si el evento está en estado "Pasado"
            if evento_dict['estado'] == 'Pasado':
                evento = {
                    'date': evento_dict.get('date'),
                    'uidONG': evento_dict.get('uidONG'),
                    'timeFin': evento_dict.get('timeFin'),
                    'timeInicio': evento_dict.get('timeInicio'),
                    'descriptionPlain': evento_dict.get('descriptionPlain'),
                    
                }
                eventos.append(evento)
             

    return eventos


def funcion_gaussiana(diferencia_minutos, sigma):
    exponente = -0.5 * (diferencia_minutos / sigma) ** 2
    valor = 1- exp(exponente)
    return valor





def calcular_coincidencia_horaria( evento_prueba, eventos_pasados):

 
    N = len(eventos_pasados)
    if N == 0:
        return 0  # No hay eventos pasados

    # Calcular los horarios de inicio en minutos de los eventos pasados
    horarios_inicio_minutos = [time_to_minutes(evento['timeInicio']) for evento in eventos_pasados]


    media = sum(horarios_inicio_minutos) / N  # Promedio de horarios


    # Calcular la diferencia en minutos entre el evento de prueba y la media de los horarios de inicio
    hora_inicio_prueba_minutos = time_to_minutes(evento_prueba['timeInicio'])

    diferencia_minutos = abs(hora_inicio_prueba_minutos - media)

    sigma = calcular_desviacion_horario_inicio_eventos(media)


    if diferencia_minutos == 0:
        coincidencia_horaria_norm = 1  # Coincidencia perfecta
    else:
        
        diferencia_std = funcion_gaussiana(diferencia_minutos,  sigma)
        coincidencia_horaria = 1-diferencia_std
        coincidencia_horaria_norm = (coincidencia_horaria-0)
    return coincidencia_horaria_norm

def time_to_minutes(time_str):
    try:
        # Asegúrate de que time_str es una cadena
        if not isinstance(time_str, str):
            # Si time_str no es una cadena, intenta convertirlo a cadena
            time_str = str(time_str)
        time = parser.parse(time_str)
        return time.hour * 60 + time.minute
    except Exception as e:  # Captura cualquier excepción para depuración
        print(f"Error al convertir la hora a minutos con '{time_str}': {e}")
        return None
    






def calcular_coincidencia_duracion_normalizada(evento_actual, eventos_pasados):

    # Calcular el promedio de duración de los eventos pasados en minutos y luego convertir a horas
    duraciones_en_minutos = []
    for evento in eventos_pasados:
        time_inicio = time_to_minutes(evento.get('timeInicio'))
        time_fin = time_to_minutes(evento.get('timeFin'))

        if time_inicio is not None and time_fin is not None:
            duracion = time_fin - time_inicio
            duraciones_en_minutos.append(duracion)
    if not duraciones_en_minutos:
        promedio_duracion_horas = 0
    else:
        promedio_duracion_horas = sum(duraciones_en_minutos) / len(duraciones_en_minutos) / 60

    # Calcular la diferencia en duración entre evento actual y el promedio
    time_inicio_actual = time_to_minutes(evento_actual.get('timeInicio'))
    time_fin_actual = time_to_minutes(evento_actual.get('timeFin'))

    sigma = calcular_desviacion_duracion_eventos()



 
    duracion_actual_horas = (time_fin_actual - time_inicio_actual) / 60
    diferencia_horas = abs(duracion_actual_horas - promedio_duracion_horas)



    diferencia_std = funcion_gaussiana(diferencia_horas, sigma)


    coincidencia_duracion = 1-diferencia_std

    coincidencia_duracion_norm = (coincidencia_duracion -0) / (1-0) 

    return coincidencia_duracion_norm



def contar_participacion_semanal(eventos):
    dias_semana = []
    for evento in eventos:
        try:
            fecha_evento = parser.parse(evento['date'])
            dia_semana = calendar.day_name[fecha_evento.weekday()]
            dias_semana.append(dia_semana)
        except ValueError as e:
            print(f"No se pudo analizar la fecha: {evento['date']}. Error: {e}")
    frecuencia_dias = Counter(dias_semana)
    return frecuencia_dias

def ordenar_dias_semana(frecuencia_dias):
    dias_ordenados = frecuencia_dias.most_common()
    return dias_ordenados



def asignar_valores_a_dias(dias_ordenados):
   
      valores_dias = {}
      total_dias = 7  # Total de rangos posibles
      ranking_actual = total_dias
      frecuencia_anterior = None

      for dia, frecuencia in dias_ordenados:
            if frecuencia != frecuencia_anterior:
                ranking_actual = ranking_actual - sum(f == frecuencia for _, f in valores_dias.items())
            valores_dias[dia] = ranking_actual / total_dias
            frecuencia_anterior = frecuencia

        # Asegurar que todos los días estén presentes en el diccionario
      for dia in calendar.day_name:
            if dia not in valores_dias:
                valores_dias[dia] = 1 / total_dias  # El valor mínimo si el día no tiene eventos

      return valores_dias





def coincidencia_dia_variable(evento_prueba, valores_dias):
    try:
        fecha_evento = parser.parse(evento_prueba['date'])
        dia_semana = calendar.day_name[fecha_evento.weekday()]
        coincidencia_dia_valor = valores_dias.get(dia_semana, 0)  # Obtener el valor para el día de la semana
       
        return coincidencia_dia_valor
    except ValueError as e:
        print(f"No se pudo analizar la fecha: {evento_prueba['date']}. Error: {e}")
        return 0
    
    


def coincidencia_ods(ods_preferidas, evento):
    # Validar que el máximo número de coincidencias posibles sea 5
    max_coincidencias_posibles = 5
    
    # Contar cuántas ODS en el evento coinciden con las preferencias del voluntario
    coincidencias_ODS = sum(1 for ods in evento['odsTags'] if ods in ods_preferidas)
    
    # Normalizar la coincidencia entre 0 y 1
    coincidencia_ODS_norm = coincidencias_ODS / max_coincidencias_posibles

    return coincidencia_ODS_norm





def filtrar_diccionario_por_ods_preferidas(diccionario_general, ods_preferidas):
    diccionario_filtrado = {}
    for ods in ods_preferidas:
        # Convertir cada ODS preferida a string y obtener las palabras clave correspondientes
        ods_str = str(ods)
        if ods_str in diccionario_general:
            diccionario_filtrado[ods_str] = diccionario_general[ods_str]
    return diccionario_filtrado

def normalizar_texto(texto):
    # Convertir el texto a minúsculas y eliminar puntuación
    return re.sub(r'[^\w\s]', ' ', texto.lower())

def calcular_coincidencias_expresiones(evento, diccionario_filtrado):
    descripcion_evento = normalizar_texto(evento.get('descriptionPlain', ''))
    coincidencias_expresiones = set()

    for _, palabras in diccionario_filtrado.items():
        for palabra in palabras:
            palabra_normalizada = normalizar_texto(palabra)
            # Verificar si la palabra o frase está en la descripción del evento
            if palabra_normalizada in descripcion_evento:
                coincidencias_expresiones.add(palabra)
    
    max_coincidencias_filtrado = sum(len(palabras) for _, palabras in diccionario_filtrado.items())
    coincidencia_expresiones_norm = len(coincidencias_expresiones) / (max_coincidencias_filtrado + 1)


    return coincidencia_expresiones_norm




def verificar_seguimiento_ong(uid_voluntario, evento_prueba):

    uid_ong = evento_prueba.get('uidONG', '')  
    seguimientos_query = db.collection('seguimientosONG').where('uidVoluntario', '==', uid_voluntario).where('uidOng', '==', uid_ong).get()

    for documento in seguimientos_query:
        if documento.exists:  # Cambiado aquí, se quitan los paréntesis
            return 1  # El voluntario sigue a la ONG
    return 0




def calcular_puntaje_final(organizaciones_seguidas, coincidencia_horaria_norm, coincidencia_dia, coincidencia_duracion_norm, coincidencia_ODS_norm, coincidencia_expresiones_norm):
    
    alpha = 0.25  # Peso para mayor impacto
    beta = 0.15   # Peso para impacto medio
    gamma = 0.05  # Peso para bajo impacto

    print(f"organizaciones seguidas: {organizaciones_seguidas}" )
    print(f"coincidencia_horario_norm  : {coincidencia_horaria_norm}" )
    print(f"coincidencia_dia  : {coincidencia_dia}" )
    print(f"coincidencia_duracion_norm  : {coincidencia_duracion_norm}" )
    print(f"coincidencia_ODS_norm  : {coincidencia_ODS_norm}" )
    print(f"coincidencia_expresiones_norm  : {coincidencia_expresiones_norm}" )
    

    # Calcular el puntaje final
    puntaje = (alpha * organizaciones_seguidas) + \
              (beta * coincidencia_horaria_norm) + \
              (beta * coincidencia_dia) + \
              (gamma * coincidencia_duracion_norm) + \
              (alpha * coincidencia_ODS_norm) + \
              (beta * coincidencia_expresiones_norm)
    
    
    return puntaje



diccionario_general = {
    '1': set(["pobreza", "hambre", "desigualdad", "necesidades básicas", "alimentación", "educación", "vivienda", "empleo", "ingresos", "salario", "carencia", "marginación", "desamparo", "exclusión", "precariedad", "subsistencia", "capacitación", "oportunidades", "desarrollo", "bienestar", "estabilidad", "equidad", "asistencia social", "vulnerabilidad", "privaciones", "salubridad", "analfabetismo", "capacidades", "movilidad social", "dignidad"]),  
    '2': set(["hambre", "desnutrición", "agricultura", "alimentos", "producción", "distribución", "acceso", "consumo", "malnutrición", "seguridad alimentaria", "desarrollo rural", "granjas", "cultivos", "fertilizantes", "irrigación", "procesamiento", "mercados", "pesca", "ganadería", "nutrientes", "conservación", "desperdicio de alimentos", "pequeños productores", "dietas sustentables", "consumo responsable", "educación alimentaria"]),  
    '3': set(["salud", "bienestar", "enfermedades", "virus", "vacunas", "mortalidad", "esperanza de vida", "cobertura médica", "seguro", "hospitales", "atención primaria", "prevención", "diagnóstico", "tratamiento", "medicamentos", "sistemas de salud", "personal médico", "financiamiento", "nutrición", "higiene", "salud mental", "salud sexual", "planificación familiar", "enfermedades no transmisibles", "tabaquismo", "ejercicio físico"]),  
    '4': set(["educación", "aprendizaje", "escuela", "universidad", "alfabetización", "habilidades", "capacitación", "conocimiento", "tecnología", "docentes", "currículum", "evaluación", "inclusión", "equidad", "formación técnica", "educación para adultos", "educación para el desarrollo sostenible", "pensamiento crítico", "solución de problemas", "toma de decisiones", "infraestructura escolar", "Tics en educación", "becas", "financiamiento", "educación de niñas"]),  
    '5': set(["género", "mujeres", "niñas", "derechos", "igualdad", "empoderamiento", "liderazgo", "inclusión", "diversidad", "identidad", "discriminación", "violencia", "acceso a la educación", "participación política", "toma de decisiones", "división sexual del trabajo", "estereotipos de género", "hombres", "trabajadoras remuneradas", "cuidado del hogar", "planificación familiar", "niños"]),  
    '6': set(["agua", "saneamiento", "acceso", "higiene", "contaminación", "tratamiento", "escasez", "servicios", "recursos hídricos", "cuencas", "ríos", "lagos", "aguas subterráneas", "aguas residuales", "infraestructura", "distribución", "alcantarillado", "gestión integrada del recurso hídrico", "recursos hídricos transfronterizos", "reúso", "desalinización", "captación de agua", "tecnologías apropiadas"]),  
    '7': set(["energía", "recursos", "renovables", "panel solar", "eólica", "eficiencia", "emisiones", "contaminación", "gas", "petróleo", "carbón", "electricidad", "energía limpia", "hidroeléctrica", "biomasa", "hidrógeno", "redes eléctricas", "energías alternativas", "combustibles fósiles", "investigación e innovación", "financiamiento", "energía para cocinar", "pobreza energética", "acción climática", "transporte limpio"]),  
    '8': set(["empleo", "trabajo", "crecimiento económico", "producción", "innovación", "infraestructura", "industria", "empresa", "desarrollo", "productividad laboral", "condiciones de trabajo", "salario mínimo", "protección social", "derechos laborales", "trabajo infantil", "desempleo juvenil", "igualdad de género", "espíritu empresarial", "diversificación económica", "investigación y desarrollo", "acceso a mercados"]),  
    '10': set(["desigualdad", "equidad", "inclusión", "discriminación", "derechos", "minorías", "grupos vulnerables", "diversidad", "justicia social", "igualdad de resultados", "igualdad de oportunidades", "movilidad social", "cohesión social", "brecha de ingresos", "concentración de riqueza", "políticas fiscales y sociales", "representación política", "cuotas de género", "cuotas raciales", "accesibilidad"]),  
    '11': set(["ciudad", "comunidad", "vivienda", "espacios públicos", "transporte", "planificación urbana", "sostenibilidad ambiental", "resiliencia", "infraestructura", "zonificación", "densidad poblacional", "áreas verdes", "edificios ecológicos", "transporte público", "peatonalización", "ciclovías", "vivienda asequible", "tugurios", "riesgos", "mitigación de desastres", "contaminación del aire"]),  
    '12': set(["producción", "consumo", "desechos", "reciclaje", "recursos", "huella ambiental", "compras sostenibles", "economía circular", "ecodiseño", "ciclo de vida del producto", "cadenas de suministro", "materiales no tóxicos", "empresas sostenibles", "empaquetado", "desperdicio alimentario", "productos orgánicos", "moda ética y sostenible", "obsolescencia programada", "reparabilidad"]),  
    '13': set(["cambio climático", "calentamiento global", "emisiones CO2", "eventos extremos", "mitigación", "adaptación", "huella de carbono", "gases de efecto invernadero", "transición energética", "sumideros de carbono", "resiliencia climática", "compromisos de reducción", "efectos adversos", "desastres climáticos", "retroceso de glaciares", "aumento del nivel del mar", "acidificación de océanos", "financiamiento climático"]),  
    '14': set(["océanos", "mares", "especies marinas", "pesca sostenible", "arrecifes de coral", "contaminación marina", "acidificación", "protección", "zonas protegidas", "biodiversidad", "desoxigenación", "basura plástica", "sobrepesca", "recursos costeros", "manglares", "pastos marinos", "recursos genéticos marinos", "gobernanza", "observación de océanos"]),  
    '15': set(["bosques", "selvas", "desiertos", "especies en peligro de extinción", "degradación ambiental", "deforestación", "reforestación", "manglares", "humedales", "montañas", "estepas", "praderas", "conservación", "restauración ecológica", "corredores biológicos", "agrodiversidad", "bancos de semillas", "conocimiento tradicional", "bioprospección"])
}


db = firestore.client()

eventosFirebase = db.collection('eventos').stream()


eventos = convertir_eventos_a_diccionarios(eventosFirebase)




def calcular_puntaje_para_eventos():
        # Llamada a la función
    uid_voluntario = "PgpqNGgGXEa7X4vnq9HPU90f5Jz2"

    eventos_futuros = obtener_eventos_futuros(eventos)

    # Llamada a la función
    ods_preferidas = obtener_ods_preferidas(uid_voluntario)
    eventos_pasados = obtener_eventos_pasados_con_asistencia(uid_voluntario)

    frecuencia_dias = contar_participacion_semanal(eventos_pasados)

    #Ordenar los días de la semana por frecuencia de participación
    dias_ordenados = ordenar_dias_semana(frecuencia_dias)
    valores_dias = asignar_valores_a_dias(dias_ordenados)

    resultados = []

    for evento in eventos_futuros:
        # Simulación de la obtención de coincidencia horaria y de día, ya que las funciones reales requieren interacción con otros datos
        coincidencia_horaria_norm = calcular_coincidencia_horaria(evento, eventos_pasados)

          # Necesitas ajustar esta función para que funcione con los datos del evento
        coincidencia_dia = coincidencia_dia_variable(evento, valores_dias)  # Asegúrate de que esta función funcione con los datos del evento
    

        # Asumir que la duración del evento se calcula y se normaliza en otro lugar, por ahora se simula con un valor estático
        coincidencia_duracion_norm = calcular_coincidencia_duracion_normalizada(evento, eventos_pasados)
   

        # Calcular coincidencia ODS
        coincidencia_ODS_norm = coincidencia_ods(ods_preferidas, evento)
   
        # Calcular coincidencia de expresiones
        diccionario_filtrado = filtrar_diccionario_por_ods_preferidas(diccionario_general, ods_preferidas)
        coincidencia_expresiones_norm = calcular_coincidencias_expresiones(evento, diccionario_filtrado)
     
        # Verificar seguimiento ONG
        organizaciones_seguidas = verificar_seguimiento_ong(uid_voluntario, evento)

        print("Evento " + evento['uidEvento'])
      
        # Calcular el puntaje final
        puntaje_final = calcular_puntaje_final(organizaciones_seguidas, coincidencia_horaria_norm, coincidencia_dia, coincidencia_duracion_norm, coincidencia_ODS_norm, coincidencia_expresiones_norm)

        print("---------------------------------------")

        resultados.append({
            'uidEvento': evento['uidEvento'],
            'puntaje_final': puntaje_final
        })

    resultados_ordenados = sorted(resultados, key=lambda x: x['puntaje_final'], reverse=True)

    return resultados_ordenados

resultados_puntajes = calcular_puntaje_para_eventos()

# Mostrar los resultados
for resultado in resultados_puntajes:
    print(f"Evento {resultado['uidEvento']} tiene un puntaje de {resultado['puntaje_final']}")



    