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
        df["CODIGO_EMPRESA"] = pd.NA
        df["PERIODO_INFORMACION"] = pd.NA
        df["ANO_INFORMADO"] = pd.NA
        df["CODIGO_SECTOR_TARIFARIO"] = pd.NA
        df["FECHA_EVENTO"] = pd.NA
        df["CODIGO_ACTIVIDAD"] = pd.NA
        df = df[df["Status usuario"] != "NOEJ"]
        
        # ETAPA 2 COMPLETAR CAMPOS CODIGO_EMPRESA
        equivalencias = {1000: '033', 2000: '034', 2100: '034', 3100: '035'}
        df['CODIGO_EMPRESA'] = df['Sociedad'].map(equivalencias).fillna(df['CODIGO_EMPRESA']).astype(str)

        df["ANO_INFORMADO"] = '2024'
        df["CODIGO_SECTOR_TARIFARIO"] = '01'

        def procesar_fechas(row):
            if row['Clase de orden'] in ['PM01', 'PM02']:
                row['PERIODO_INFORMACION'] = str(row['Fecha entrada'].year)
                row['FECHA_EVENTO'] = row['Fecha entrada']
            elif row['Clase de orden'] == 'PM03':
                row['PERIODO_INFORMACION'] = str(row['Fe.inic.extrema'].year)
                row['FECHA_EVENTO'] = row['Fe.inic.extrema']
            return row

        # Aplicar la función a cada fila
        df = df.apply(procesar_fechas, axis=1)

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

            # Filtrar df para trabajar solo con filas donde CODIGO_OBRA no está vacío
            # df_filtrado = df.dropna(subset=['CODIGO_OBRA'])

            # Crear mapeos para RECINTO, LOCALIDAD y TIPO_OBRA
            mapeo_recinto = pd.Series(data1.RECINTO.values, index=data1.CODIGO_OBRA).to_dict()
            mapeo_localidad = pd.Series(data1.LOCALIDAD.values, index=data1.CODIGO_OBRA).to_dict()
            mapeo_tipobra = pd.Series(data1.TIPO_OBRA.values, index=data1.CODIGO_OBRA).to_dict()
            
            # Aplicar los mapeos directamente en el df original sin eliminar filas
            df['RECINTO'] = df['CODIGO_OBRA'].map(mapeo_recinto).fillna(df['RECINTO'])
            df['LOCALIDAD'] = df['CODIGO_OBRA'].map(mapeo_localidad).fillna(df['LOCALIDAD'])
            df['TIPO_OBRA'] = df['CODIGO_OBRA'].map(mapeo_tipobra).fillna(df['TIPO_OBRA'])

            # Definimos la URL del segundo archivo de referencia data_3.csv
            DATA3_URL = 'https://streamlitmaps.s3.amazonaws.com/Codigo_Actividad.csv'
        
            # Función para cargar el primer archivo de referencia
            def load_data3():
                data3 = pd.read_csv(DATA3_URL, encoding='ISO-8859-1', sep=';')
                return data3
        
            data3 = load_data3()  # Cargamos el tercer archivo de referencia

            # Crear la columna temporal "CONCA_1" concatenando "Clase de orden" y "TIPO_OBRA"
            df['CONCA_1'] = df['Clase de orden'] + df['TIPO_OBRA']

            # Preparar el diccionario para el mapeo desde el tercer archivo de referencia
            dict_mapeo3 = pd.Series(data3.CODIGO_ACTIVIDAD.values, index=data3.CONCA_1).to_dict()

            # Realizar el mapeo para obtener "CODIGO_ACTIVIDAD" basado en "CONCA_1"
            df['CODIGO_ACTIVIDAD'] = df['CONCA_1'].map(dict_mapeo3)

            # Eliminar la columna temporal "CONCA_1" después del mapeo
            df.drop(columns='CONCA_1', inplace=True)

            st.success("Espera un momento mientras procesamos tu archivo NBI!")
            st.write(df)
        
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
