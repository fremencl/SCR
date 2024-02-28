# Importacion de librerias
import streamlit as st
import pandas as pd

# Título de la aplicación
st.title('Portal Procesamiento datos SCR')

# Carga del archivo - solo CSV
archivo_usuario = st.file_uploader("Por favor, cargue su archivo de datos en formato CSV aquí", type=['csv'])

# Verificación y carga del DataFrame
if archivo_usuario is not None:
    try:
        # Especificamos la codificación ISO-8859-1 y el separador ";"
        df = pd.read_csv(archivo_usuario, encoding='ISO-8859-1', sep=';')
        
        # Transformamos la columna "Orden" a string y ajustamos fechas
        df['Orden'] = df['Orden'].astype(str)
        for col in ['Fe.inic.extrema', 'Fecha entrada']:
            df[col] = pd.to_datetime(df[col], origin='1899-12-30', unit='D').dt.date
        
        # Agregamos las nuevas columnas y eliminamos filas no deseadas
        df["CODIGO_OBRA"] = pd.NA
        df["RECINTO"] = pd.NA
        df["LOCALIDAD"] = pd.NA
        df["TIPO_OBRA"] = pd.NA
        df = df[df["Status usuario"] != "NOEJ"]
        
        # Mostramos un preview del DataFrame para confirmación del usuario
        st.write(df)

    except Exception as e:
        st.error(f"Se ha producido un error al cargar el archivo: {e}")
else:
    st.write("Por favor, cargue un archivo CSV para continuar.")

# Botón para iniciar el procesamiento (mapeo)
if st.button('Iniciar Procesamiento'):
    if 'df' in locals() or 'df' in globals():
        # Definimos la URL del archivo de referencia (asegúrate de que la URL es correcta)
        DATA1_URL = 'https://streamlitmaps.s3.amazonaws.com/data1.csv'

        # Función para cargar el archivo de referencia
        def load_data1():
            data1 = pd.read_csv(DATA1_URL)
            return data1

        # Cargamos el archivo de referencia y realizamos el mapeo
        data1 = load_data1()  # Aseguramos cargar los datos de referencia
        dict_mapeo = pd.Series(data1.CODIGO_OBRA.values, index=data1.ID_EQUIPO).to_dict()
        df['CODIGO_OBRA'] = df['Equipos'].map(dict_mapeo)
        
        st.success("Procesamiento completado exitosamente!")
        st.write(df)  # Mostramos el DataFrame después del mapeo

        # Preparar el DataFrame para la descarga
        csv = df.to_csv(index=False, encoding='ISO-8859-1', sep=';').encode('ISO-8859-1')
        
        # Widget de descarga
        st.download_button(
            label="Descargar datos como CSV",
            data=csv,
            file_name='datos_procesados.csv',
            mime='text/csv',
        )
    else:
        st.error("No hay datos cargados para procesar.")
