
from firebase_admin import firestore
from dateutil import parser

from flask import jsonify
from firebase_admin import firestore
from dateutil import parser
import firebase_admin
from firebase_admin import credentials
from math import exp, pi, sqrt
from collections import Counter
import calendar
import re


from unidecode import unidecode
import pytz
from datetime import datetime
from math import log

cred = credentials.Certificate('voluntred-9b82e-firebase-adminsdk-xe4ed-cddbd4b29e.json')
firebase_admin.initialize_app(cred)




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



def convertir_publicaciones_a_diccionarios(publicaciones_stream):
    publicaciones_lista = []
    for publicacion in publicaciones_stream:
        publicacion_dict = publicacion.to_dict()
        publicacion_info = {
            'date': publicacion_dict.get('date'),
            'textPlain': publicacion_dict.get('textPlain'),
            'ods': publicacion_dict.get('ods'),
            'meDivierte': publicacion_dict.get('meDivierte'),
            'meGusta': publicacion_dict.get('meGusta'),
            'meEncanta': publicacion_dict.get('meEncanta'),
            'meEntristece': publicacion_dict.get('meEntristece'),
            'meEnoja': publicacion_dict.get('meEnoja'),
            'uidAutor': publicacion_dict.get('uidAutor'),
            'uidPublicacion': publicacion_dict.get('uidPublicacion')
        }
        publicaciones_lista.append(publicacion_info)
    return publicaciones_lista


def filtrar_diccionario_por_ods_preferidas(diccionario_general, ods_preferidas):
    diccionario_filtrado = {}
    for ods in ods_preferidas: #(RQF 254)
        # Convertir cada ODS preferida a string y obtener las palabras clave correspondientes
        ods_str = str(ods)
        if ods_str in diccionario_general:
            diccionario_filtrado[ods_str] = diccionario_general[ods_str]
    return diccionario_filtrado # (RQF255)

def normalizar_texto(texto):
    # Convertir el texto a minúsculas
    texto = texto.lower()
    # Eliminar acentos
    texto = unidecode(texto)
    # Eliminar puntuación
    texto = re.sub(r'[^\w\s]', ' ', texto)
    return texto

def calcular_coincidencias_expresiones(publicacion, diccionario_filtrado):
    descripcion_publicacion = normalizar_texto(publicacion.get('textPlain', ''))
    coincidencias_expresiones = set()

    for _, palabras in diccionario_filtrado.items():
        for palabra in palabras:
            palabra_normalizada = normalizar_texto(palabra)
            # Verificar si la palabra o frase está en la descripción del evento
            if palabra_normalizada in descripcion_publicacion:
                coincidencias_expresiones.add(palabra)
    
    max_coincidencias_filtrado = sum(len(palabras) for _, palabras in diccionario_filtrado.items())
    coincidencia_expresiones_norm = len(coincidencias_expresiones) / (max_coincidencias_filtrado + 1) #(RQF256)


    return coincidencia_expresiones_norm



def coincidencia_ods(ods_preferidas, publicacion):
    # (RQNF113)Validar que el máximo número de coincidencias posibles sea 5
    max_coincidencias_posibles = 5
    
    # (RQF252)Contar cuántas ODS en el evento coinciden con las preferencias del voluntario
    coincidencias_ODS = sum(1 for ods in publicacion['ods'] if ods in ods_preferidas)
    
    # (RQF253)Normalizar la coincidencia entre 0 y 1
    coincidencia_ODS_norm = coincidencias_ODS / max_coincidencias_posibles

    return coincidencia_ODS_norm


def calcular_cercania_temporal(publicaciones):
    tiempo_actual = datetime.now(pytz.utc)
    cercanias_temporales = []

    for publicacion in publicaciones:
        try:
            # Directamente usar el datetime si ya está en ese formato
            tiempo_publicacion = publicacion['date']

            if not isinstance(tiempo_publicacion, datetime):
                # Intenta analizar solo si no es un objeto datetime
                tiempo_publicacion = parser.parse(tiempo_publicacion)

            # Calcula la diferencia en segundos
            diferencia_segundos = (tiempo_actual - tiempo_publicacion).total_seconds()
            diferencia_estandarizada = log(diferencia_segundos + 1)
            cercania_temporal = 1 / (diferencia_estandarizada + 1)

            cercanias_temporales.append(cercania_temporal)
        except Exception as e:
            print(f"Error al procesar la fecha para la publicación {publicacion['uidPublicacion']}: {e}")
            cercanias_temporales.append(0)

    # Normalizar la cercanía temporal
    min_cercania = min(cercanias_temporales)
    max_cercania = max(cercanias_temporales)
    
    cercanias_temporales_norm = [(ct - min_cercania) / (max_cercania - min_cercania) if max_cercania != min_cercania else 0 for ct in cercanias_temporales]
    

    return cercanias_temporales_norm



def procesar_informacion_publicaciones_amitades(publicaciones_de_amigos, ods_preferidas, diccionario_filtrado, info_amigos):
    # Preparar datos
    antiguedad_normalizada = calcular_antiguedades_amistades_normalizadas(info_amigos)
    
    print("Antiguedades: ")

    print(antiguedad_normalizada)

    cercania_temporal_norm_list = calcular_cercania_temporal(publicaciones_de_amigos)
    cercania_temporal_norm = {pub['uidPublicacion']: valor for pub, valor in zip(publicaciones_de_amigos, cercania_temporal_norm_list)}


        
    resultados = []
    # Procesar y mostrar información para cada publicación
    for publicacion in publicaciones_de_amigos:
        uid_publicacion = publicacion['uidPublicacion']
        uid_autor = publicacion['uidAutor']
         # Obtener la antigüedad de la amistad para el autor de la publicación
        antiguedad_amistad = antiguedad_normalizada.get(uid_autor, 0)
    
        coincidencia_norm = coincidencia_ods(ods_preferidas, publicacion)
        coincidencia_expresiones_norm = calcular_coincidencias_expresiones(publicacion, diccionario_filtrado)

        cercania_temp = cercania_temporal_norm.get(uid_publicacion, 0)

        # Imprimir o almacenar la información de cada publicación
        
        print(f"UID Publicación: {uid_publicacion}, Coincidencia ODS Normalizada: {coincidencia_norm}")
        print(f"UID Publicación: {uid_publicacion}, Coincidencia de Expresiones Normalizada: {coincidencia_expresiones_norm}")
        print(f"UID Publicación: {uid_publicacion}, Antiguedad amistad : {antiguedad_amistad}")
        print(f"UID Publicación: {uid_publicacion}, Cercanía Temporal Normalizada: {cercania_temp}")
        
        puntaje_final = calcular_puntaje_final(antiguedad_amistad,coincidencia_norm,coincidencia_expresiones_norm, cercania_temp)

        resultados.append({
        'uidEvento': uid_publicacion,
        'puntaje_final': puntaje_final
        })


    resultados_ordenados = sorted(resultados, key=lambda x: x['puntaje_final'], reverse=True)

    return resultados_ordenados


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

def calcular_puntaje_final(antiguedad_normalizada,coincidencia_ODS_norm,coincidencia_expresiones_norm, cercania_temporal_norm):
    
  
    alpha = 0.3  # Peso para mayor impacto
    beta = 0.2  # Peso para impacto medio



    # Calcular el puntaje final
    puntaje = (alpha * cercania_temporal_norm) + \
              (beta * antiguedad_normalizada) + \
              (alpha * coincidencia_ODS_norm) + \
              (beta * coincidencia_expresiones_norm) 
              
    return puntaje



db = firestore.client()


def calcular_antiguedades_amistades_normalizadas(info_amigos):
    # Inicialización de variables
    fecha_actual = datetime.now(pytz.utc)
    antiguedades = []

    # Convertir cada fecha de inicio de amistad a datetime y calcular las antigüedades
    for amigo in info_amigos:
        fecha_inicio_amistad_str = amigo['fechaAmistad']
        if isinstance(fecha_inicio_amistad_str, str):
            fecha_inicio_amistad = parser.parse(fecha_inicio_amistad_str)
        else:
            fecha_inicio_amistad = fecha_inicio_amistad_str

        # Calcular la diferencia en segundos y luego convertir a días para incluir fracciones de día
        diferencia_segundos = (fecha_actual - fecha_inicio_amistad).total_seconds()
        diferencia_dias = diferencia_segundos / (60 * 60 * 24)  # Convertir segundos a días

        # Aplicar el logaritmo neperiano a la diferencia de días y calcular la antigüedad
        diferencia_std = log(diferencia_dias + 1)
        antiguedad = (diferencia_std + 1)
        antiguedades.append(antiguedad)

    # Calcular los valores máximos y mínimos de antigüedad dentro del conjunto
    max_antiguedad = max(antiguedades)
    min_antiguedad = min(antiguedades)

    # Normalizar las antigüedades basándose en los valores máximos y mínimos encontrados
    antiguedades_normalizadas = [(a - min_antiguedad) / (max_antiguedad - min_antiguedad) if max_antiguedad != min_antiguedad else 1 for a in antiguedades]

    # Crear un diccionario para asociar cada UID de amigo con su antigüedad normalizada
    antiguedad_amigos_normalizada = {amigo['uidAmigo']: antiguedad for amigo, antiguedad in zip(info_amigos, antiguedades_normalizadas)}

    return antiguedad_amigos_normalizada


def obtener_amistades(uid_voluntario):
    # Consulta las amistades donde aparece el uidVoluntario.
    amistades_ref = db.collection('amistades')
    query = amistades_ref.where('uidParticipantes', 'array_contains', uid_voluntario)
    results = query.get()
    
    # Lista para guardar los UIDs de todos los amigos y las fechas de amistad.
    amigos_info = []

    # Itera sobre los resultados y obtén los uid y las fechas de las amistades.
    for amistad in results:
        amistad_data = amistad.to_dict()
        uid_participantes = amistad_data.get('uidParticipantes', [])
        fecha_amistad = amistad_data.get('fechaAmistad', None)

        # Encuentra y agrega los UIDs de los amigos y las fechas, excluyendo el UID del voluntario en cuestión.
        for uid in uid_participantes:
            if uid != uid_voluntario:
                amigo_info = {
                    'uidAmigo': uid,
                    'fechaAmistad': fecha_amistad
                }
                amigos_info.append(amigo_info)
                
    return amigos_info




def obtener_publicaciones_amigos(uid_amigos):

    # Lista para guardar las publicaciones de todos los amigos.
    todas_las_publicaciones = []

    # Itera sobre los UIDs de los amigos y obtén sus publicaciones.
    for uid_amigo in uid_amigos:
        publicaciones_ref = db.collection('publicacionesVoluntario')
        query_publicaciones = publicaciones_ref.where('uidAutor', '==', uid_amigo)
        resultados_publicaciones = query_publicaciones.get()
        
        # Añade los resultados a la lista de todas las publicaciones.
        todas_las_publicaciones.extend(resultados_publicaciones)
        
    # Convierte todas las publicaciones a una lista de diccionarios con el formato deseado.
    return convertir_publicaciones_a_diccionarios(todas_las_publicaciones)



def algoritmo_publicacion_amigos():

    uid_voluntario = "PgpqNGgGXEa7X4vnq9HPU90f5Jz2"

    info_amigos = obtener_amistades(uid_voluntario)

        # Extrae solo los UIDs de los amigos para pasarlos a la siguiente función.
    uid_amigos = [amigo['uidAmigo'] for amigo in info_amigos]

    publicaciones_de_amigos = obtener_publicaciones_amigos(uid_amigos)

    publicaciones_de_amigos = obtener_publicaciones_amigos(uid_amigos)



    ods_preferidas = obtener_ods_preferidas(uid_voluntario)

    print(ods_preferidas)

    diccionario_filtrado = filtrar_diccionario_por_ods_preferidas(diccionario_general, ods_preferidas)


    resultados_puntajes = procesar_informacion_publicaciones_amitades(publicaciones_de_amigos, ods_preferidas, diccionario_filtrado, info_amigos)
    

   

algoritmo_publicacion_amigos()