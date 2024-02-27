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
        
        # Transformamos la columna "Orden" a string
        df['Orden'] = df['Orden'].astype(str)
        
        # Convertimos las columnas de fechas de formato Excel a formato de fecha
        for col in ['Fe.inic.extrema', 'Fecha entrada']:
            df[col] = pd.to_datetime(df[col], origin='1899-12-30', unit='D')
            
    except UnicodeDecodeError as e:
        st.error("Error de decodificación. Intente cambiar la codificación del archivo si el problema persiste.")
        raise e
    except Exception as e:
        st.error(f"Se ha producido un error al cargar el archivo: {e}")
        raise e
    else:
        # Mostramos un preview del DataFrame para confirmación del usuario
        st.write(df)

        # Notificación de carga completada
        st.success("Archivo cargado exitosamente!")
else:
    st.write("Por favor, cargue un archivo CSV para continuar.")
