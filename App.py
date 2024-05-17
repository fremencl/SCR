# Importacion de librerias
import streamlit as st
import pandas as pd
import numpy as np

# Título de la aplicación
st.title('Portal Procesamiento datos SCR - AUX_44')

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
        df["TIPO_ACTIVIDAD_MANTENCION"] = pd.NA
        df["CODIGO_CARGO_SISS"] = pd.NA
        
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
            DATA3_URL = 'https://streamlitscr.s3.amazonaws.com/Codigo_Actividad.csv'
        
            # Función para cargar el tercer archivo de referencia
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

            # Definimos la URL archivo de referencia Tipo Actividad mantencion
            DATA4_URL = 'https://streamlitscr.s3.amazonaws.com/Tipo_act_mant.csv'

            # Función para cargar el tercer archivo de referencia
            def load_data4():
                data4 = pd.read_csv(DATA4_URL, encoding='ISO-8859-1', sep=';')
                return data4

            data4 = load_data4()  # Cargamos el cuarto archivo de referencia

            # Crear la columna temporal "Familia" extrayendo los primeros 4 caracteres de "Equipo"
            df['Familia'] = df['Equipo'].str[:4]
            
            # Crear la columna temporal "CONCA_2" concatenando "Familia" y "Clase de orden"
            df['CONCA_2'] = df['Familia'] + df['Clase de orden']

            # Preparar el diccionario para el mapeo desde el cuarto archivo de referencia
            dict_mapeo4 = pd.Series(data4.Tipo_act_mant.values, index=data4.CONCA_2).to_dict()

            # Realizar el mapeo para obtener "TIPO_ACTIVIDAD_MANTENCION" basado en "CONCA_2"
            df['TIPO_ACTIVIDAD_MANTENCION'] = df['CONCA_2'].map(dict_mapeo4)

            # Eliminar las columnas temporales "Familia" y "CONCA_2" después del mapeo
            df.drop(columns=['Familia', 'CONCA_2'], inplace=True)

            # Asignación inicial de codigos basada en 'Grupo planif.'
            condiciones = [
                df['Grupo planif.'].isin(['OPR', 'ORE', 'ORM']),
                df['Grupo planif.'] == 'ORA',
                df['Grupo planif.'].isin(['RGO', 'SGM']),
                df['Grupo planif.'].isin(['DED', 'DEP', 'DEE', 'DEI', 'DEL', 'DEM', 'ON1', 'ON2', 'ON3', 'OS1', 'OS2', 'OS3']),
                df['Grupo planif.'].isin(['LOO', 'P01', 'P02', 'P03', 'P04', 'P05', 'P06', 'P07', 'P08', 'P09', 'P10', 'P11', 'P12', 'P13', 'P14', 'P15', 'P16', 'P17', 'P18', 'P19', 'P20', 'P21', 'TG1', 'TG2', 'TG3', 'TG4', 'TP1', 'TP2', 'TR1', 'TR2', 'TR3', 'TR4', 'TR5', 'TR6']),
                df['Grupo planif.'] == 'JET'
            ]

            codigos = [
                40304,  # Código para 'OPR', 'ORE', 'ORM'
                40305,  # Código para 'ORA'
                40306,  # Código para 'RGO', 'SGM'
                40305,  # Código para primer grupo que requiere duplicación
                40305,  # Código para segundo grupo que requiere duplicación
                40305   # Código para 'JET' que también requiere duplicación
            ]

            df['CODIGO_CARGO_SISS'] = np.select(condiciones, codigos, default=np.nan)

            # Duplicar filas según condiciones específicas y asignar diferentes códigos
            grupos_duplicar = {
                'DED': (40305, 40306),
                'DEP': (40305, 40306),
                'DEE': (40305, 40306),
                'DEI': (40305, 40306),
                'DEL': (40305, 40306),
                'DEM': (40305, 40306),
                'ON1': (40305, 40306),
                'ON2': (40305, 40306),
                'ON3': (40305, 40306),
                'OS1': (40305, 40306),
                'OS2': (40305, 40306),
                'OS3': (40305, 40306),
                'LOO': (40305, 40114),
                'P01': (40305, 40114),
                'P02': (40305, 40114),
                'P03': (40305, 40114),
                'P04': (40305, 40114),
                'P05': (40305, 40114),
                'P06': (40305, 40114),
                'P07': (40305, 40114),
                'P08': (40305, 40114),
                'P09': (40305, 40114),
                'P10': (40305, 40114),
                'P11': (40305, 40114),
                'P12': (40305, 40114),
                'P13': (40305, 40114),
                'P14': (40305, 40114),
                'P15': (40305, 40114),
                'P16': (40305, 40114),
                'P17': (40305, 40114),
                'P18': (40305, 40114),
                'P19': (40305, 40114),
                'P20': (40305, 40114),
                'P21': (40305, 40114),
                'TG1': (40305, 40114),
                'TG2': (40305, 40114),
                'TG3': (40305, 40114),
                'TG4': (40305, 40114),
                'TP1': (40305, 40114),
                'TP2': (40305, 40114),
                'TR1': (40305, 40114),
                'TR2': (40305, 40114),
                'TR3': (40305, 40114),
                'TR4': (40305, 40114),
                'TR5': (40305, 40114),
                'TR6': (40305, 40114),
                'JET': (40305, 40303)
            }

            # Procesar duplicación y asignación de códigos
            for grupo, (codigo_original, codigo_duplicado) in grupos_duplicar.items():
                filtro = df['Grupo planif.'] == grupo
                filas_a_duplicar = df[filtro].copy()
                filas_a_duplicar['CODIGO_CARGO_SISS'] = codigo_duplicado
                df = pd.concat([df, filas_a_duplicar])

            # Resetear el índice después de la duplicación
            df.reset_index(drop=True, inplace=True)

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
