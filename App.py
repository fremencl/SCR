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
    st.write("Esta App agregará Codigos NBI de manera automatica en tu archivo")

# Botón para iniciar el procesamiento (mapeo)
if st.button('Iniciar Procesamiento'):
    if 'df' in locals() or 'df' in globals():
        # Definimos la URL del primer archivo de referencia
        DATA1_URL = 'https://streamlitmaps.s3.amazonaws.com/Base_Equipos_NBI_Resumen.csv'

        # Función para cargar el primer archivo de referencia
        def load_data1():
            data1 = pd.read_csv(DATA1_URL, encoding='ISO-8859-1', sep=';')
            return data1
        
        data1 = load_data1()  # Cargamos el primer archivo de referencia
        
        # Verificamos que las columnas esperadas existen en data1
        expected_columns = ['CODIGO_OBRA', 'Equipo']
        if not all(column in data1.columns for column in expected_columns):
            st.error(f"El archivo de referencia no contiene las columnas esperadas: {expected_columns}")
        else:
            dict_mapeo = pd.Series(data1.CODIGO_OBRA.values, index=data1.Equipo).to_dict()
            df['CODIGO_OBRA'] = df['Equipo'].map(dict_mapeo)

            # Definimos la URL del segundo archivo de referencia (data_2.csv)
            DATA2_URL = 'https://streamlitmaps.s3.amazonaws.com/Base_UTEC_2024.csv'

            # Función para cargar el segundo archivo de referencia
            def load_data2():
                data2 = pd.read_csv(DATA2_URL, encoding='ISO-8859-1', sep=';')
                return data2
            
            data2 = load_data2()  # Cargamos el segundo archivo de referencia
            
            # Realizamos el segundo mapeo
            dict_mapeo2 = pd.Series(data2.CODIGO_OBRA.values, index=data2.UTEC).to_dict()
            # Aplicamos el segundo mapeo solo a las filas donde "CODIGO_OBRA" está vacío
            df.loc[df["CODIGO_OBRA"].isna(), "CODIGO_OBRA"] = df["Ubicac.técnica"].map(dict_mapeo2)

            st.success("Procesamiento completado exitosamente!")
            st.write(df)
        2
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
