import streamlit as st
import pandas as pd

# Configurar página
st.set_page_config(page_title="Dashboard de Apostas", page_icon="📈", layout="wide")
st.title('📈 Dashboard de Apostas Esportivas do LC')

uploaded_file = st.file_uploader("Escolha um arquivo CSV", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, delimiter=',')
    df.columns = df.columns.str.strip()  # tira espaços nas bordas

    st.write("### ✅ Estas são as colunas que existem no seu arquivo:")
    st.write(list(df.columns))  # <<<< MOSTRAR COLUNAS AQUI
    
    # --- NÃO FAZ MAIS NADA POR ENQUANTO ---

else:
    st.info("Por favor, faça o upload de um arquivo CSV.")
