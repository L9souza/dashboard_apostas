import streamlit as st
import pandas as pd

# Configurar a página
st.set_page_config(page_title="Dashboard de Apostas", page_icon="📈", layout="wide")
st.title('📈 Dashboard de Apostas Esportivas do LC')

uploaded_file = st.file_uploader("Escolha um arquivo CSV", type="csv")

if uploaded_file is not None:
    # Carregar o arquivo
    df = pd.read_csv(uploaded_file, delimiter=';')
    df.columns = df.columns.str.strip()  # remove espaços extras nos nomes

    # Mostrar as colunas para confirmação
    st.write("### ✅ Colunas encontradas:")
    st.write(list(df.columns))

    # Conversões de tipo (garantir que números sejam tratados como números)
    df['Valor Apostado (R$)'] = df['Valor Apostado (R$)'].str.replace(',', '.').astype(float)
    df['Retorno Previsto (R$)'] = df['Retorno Previsto (R$)'].str.replace(',', '.').astype(float)
    df['Lucro/Prejuízo (R$)'] = df['Lucro/Prejuízo (R$)'].str.replace(',', '.').astype(float)

    # Mostrar o DataFrame
    st.write("### 📄 Visualização dos Dados:")
    st.dataframe(df)

    # Mostrar estatísticas
    st.write("### 📊 Estatísticas:")
    total_apostado = df['Valor Apostado (R$)'].sum()
    total_retorno = df['Retorno Previsto (R$)'].sum()
    total_lucro = df['Lucro/Prejuízo (R$)'].sum()

    st.metric("Total Apostado (R$)", f"R$ {total_apostado:.2f}")
    st.metric("Total Retorno Previsto (R$)", f"R$ {total_retorno:.2f}")
    st.metric("Total Lucro/Prejuízo (R$)", f"R$ {total_lucro:.2f}")

else:
    st.info("Por favor, faça o upload de um arquivo CSV.")
