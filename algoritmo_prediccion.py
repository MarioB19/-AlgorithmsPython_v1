from flask import jsonify

from firebase_admin import firestore
from dateutil import parser
import pandas as pd

from firebase_functions import options
from httplib2 import Credentials
import numpy as np
from sklearn.model_selection import train_test_split

import firebase_admin
from firebase_admin import credentials



cred = credentials.Certificate('voluntred-9b82e-firebase-adminsdk-xe4ed-cddbd4b29e.json')
firebase_admin.initialize_app(cred)


def extract_date_info(date_str):
    try:
        date = parser.parse(date_str)
        return date.strftime('%A'), date.strftime('%B')
    except ValueError as e:
        print(f"Error al analizar la fecha: {e}")
        return None, None
    

def one_hot_day(day):
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    return {day_name: 1 if day_name == day else 0 for day_name in days}


def one_hot_month(month):
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    return {month_name: 1 if month_name == month else 0 for month_name in months}


def one_hot_ods(ods_list):
    # Definir todos los posibles ODS como strings
    all_ods = ['1', '2', '3', '4', '5', '6', '7', '8', '10', '11','12', '13' '14', '15']
    # Crear el diccionario de One-Hot Encoding con valores iniciales en 0
    ods_encoding = {f"ODS{ods}": 0 for ods in all_ods}
    # Para cada ODS en la lista de ODS del evento, establecer su valor a 1
    for ods in ods_list:
        if ods in all_ods:  # Verifica que el ODS esté en la lista de todos los ODS posibles
            ods_encoding[f"ODS{ods}"] = 1  # Actualiza el valor a 1 si el ODS está presente
    return ods_encoding


def calcular_porcentaje_error(valores_reales, predicciones):
    mse = calcular_error(predicciones, valores_reales)
    promedio_valores_reales = np.mean(valores_reales)
    
    if promedio_valores_reales == 0:
        raise ValueError("El promedio de los valores reales es cero, el porcentaje de error no puede ser calculado.")
    
    porcentaje_error = (mse / promedio_valores_reales) * 100
    return porcentaje_error




def calcular_coeficientes(X, Y):

    # Asegurarse de que Y es un vector columna
    if Y.ndim == 1:
        Y = Y.reshape(-1, 1)

    # Calcular X transpuesta
    X_transpuesta = X.T

    # Calcular (X^T X)
    XtX = np.dot(X_transpuesta, X)

    XtX_inv = np.linalg.pinv(XtX)


    # Calcular (X^T Y)
    XtY = np.dot(X_transpuesta, Y)

    # Calcular los coeficientes beta = (X^T X)^-1 (X^T Y)
    beta = np.dot(XtX_inv, XtY)

    # Aplanar el array de coeficientes, si es necesario, para devolverlo como un vector simple
    return beta.flatten()





def predecir_valores(X_nuevos, beta):
    # Asegurarse de que beta es un vector columna
    if beta.ndim == 1:
        beta = beta.reshape(-1, 1)

    # Realizar la predicción
    predicciones = np.dot(X_nuevos, beta)

    # Aplanar el array de predicciones para devolverlo como un vector simple
    return predicciones.flatten()





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

def calculate_duration(start_time, end_time):
    try:
       
        duration = end_time - start_time
        return duration
    except ValueError as e:
        print(f"Error al calcular la duración: {e}")
        return None


def calcular_error(predicciones, valores_reales):

    if predicciones.shape != valores_reales.shape:
        raise ValueError("La longitud de predicciones y valores_reales debe ser la misma.")
    
    # Calcular el error cuadrático medio (MSE)
    mse = np.mean((predicciones - valores_reales) ** 2)
    return mse







def prediccion_asistentes_evento():




    fecha_evento_str = "27/04/2024"
    hora_inicio_str = "5:00 PM"
    hora_fin_str = "6:00 PM"
    ods = ["4", "6" , "3"]




    dayEvent, monthEvent = extract_date_info(fecha_evento_str)

    evento_predecir = {
        'timeInicio':  time_to_minutes(hora_inicio_str),
        'timeFin': time_to_minutes(hora_fin_str),
        'Duracion': calculate_duration(time_to_minutes(hora_inicio_str), time_to_minutes(hora_fin_str))
    }

    evento_predecir.update(one_hot_ods(ods))
        
    evento_predecir.update(one_hot_day(dayEvent))
    evento_predecir.update(one_hot_month(monthEvent))
       

    db = firestore.client()

    eventos_pasados = db.collection('eventos').where('estado', '==', 'Pasado').stream()

    historical_data = []
    personas_registradas = []
    for evento in eventos_pasados:
        datos_evento = evento.to_dict()
          # Obtener el día y el mes de la fecha
        day, month = extract_date_info(datos_evento.get('date'))

        ods_list = datos_evento.get('odsTags', [])  # Asegurar que es una lista
        
        # Crear un nuevo diccionario con solo los campos deseados
        evento_reducido = {
            'timeInicio':  time_to_minutes(datos_evento.get('timeInicio')),
            'timeFin': time_to_minutes(datos_evento.get('timeFin')),
            'Duracion': calculate_duration(time_to_minutes(datos_evento.get('timeInicio')), time_to_minutes(datos_evento.get('timeFin')))
        }

        evento_reducido.update(one_hot_ods(ods_list))
        
     
        evento_reducido.update(one_hot_day(day))
        evento_reducido.update(one_hot_month(month))
       
        
        historical_data.append(evento_reducido)
        personas_registradas.append(datos_evento.get('registeredPeopleCount'))


    dX = pd.DataFrame(historical_data)
    dY = pd.DataFrame(personas_registradas)

    matrizX = dX.values
    matrizY = dY.values.reshape(-1, 1)

    # Dividir los datos en conjuntos de entrenamiento y prueba
    X_train, X_test, y_train, y_test = train_test_split(matrizX, matrizY, test_size=0.30)

    # Calcular los coeficientes beta usando solo el conjunto de entrenamiento
    beta = calcular_coeficientes(X_train, y_train)

    predicciones_train = predecir_valores(X_train, beta)

    print("Predicciones")
    print(predicciones_train.flatten())
    print(y_train.flatten())
    print("___________________")
    



    # Hacer predicciones sobre el conjunto de prueba
    predicciones_test = predecir_valores(X_test, beta)
    
    # Comparar las predicciones con los valores reales del conjunto de prueba
    print(y_test)
    print(predicciones_test)
    porcentaje_error = calcular_porcentaje_error(y_test.flatten(), predicciones_test)
    print(f"Porcentaje de error en el conjunto de prueba: {porcentaje_error/34}")

    # Predecir el evento futuro
    dXnewDatos = pd.DataFrame([evento_predecir])
    prediccionNew = predecir_valores(dXnewDatos.values, beta)
    print(f"Prediccion asistentes para el nuevo evento: {prediccionNew}")

    if prediccionNew[0] <0:
        prediccionNew[0] = 0

    
    respuesta = {
        "prediccionNuevoEvento": prediccionNew[0],
        "margenError": porcentaje_error
    }


    
    return respuesta



prediccion_asistentes_evento()