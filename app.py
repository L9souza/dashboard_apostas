import streamlit as st
import pandas as pd
import plotly.express as px

# Configurações da página
st.set_page_config(page_title="Dashboard de Apostas", page_icon="🎯", layout="wide")

st.title('🎯 Dashboard de Apostas Esportivas')

# Upload de arquivo
uploaded_file = st.file_uploader("📂 Faça upload do seu arquivo CSV", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, delimiter=';')
    df.columns = df.columns.str.strip()

    # Limpeza dos dados
    df = df.dropna(subset=["Data"])  # remove linhas vazias
    df['Valor Apostado (R$)'] = df['Valor Apostado (R$)'].astype(float)
    df['Retorno Previsto (R$)'] = df['Retorno Previsto (R$)'].astype(float)
    df['Lucro/Prejuízo (R$)'] = df['Lucro/Prejuízo (R$)'].astype(float)
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')

    # Estatísticas
    total_apostado = df['Valor Apostado (R$)'].sum()
    total_retorno = df['Retorno Previsto (R$)'].sum()
    total_lucro = df['Lucro/Prejuízo (R$)'].sum()

    # Layout com 3 colunas
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Apostado", f"R$ {total_apostado:,.2f}")
    col2.metric("🎯 Retorno Previsto", f"R$ {total_retorno:,.2f}")
    col3.metric("📈 Lucro/Prejuízo", f"R$ {total_lucro:,.2f}", delta=f"R$ {total_lucro:,.2f}")

    st.markdown("---")

    # Gráfico 1: Lucro por Data
    lucro_por_data = df.groupby('Data')['Lucro/Prejuízo (R$)'].sum().reset_index()
    fig_lucro = px.line(lucro_por_data, x='Data', y='Lucro/Prejuízo (R$)', markers=True,
                        title="Lucro/Prejuízo por Data")
    st.plotly_chart(fig_lucro, use_container_width=True)

    # Gráfico 2: Distribuição por Casa de Apostas
    casa_apostas = df['Casa de Apostas'].value_counts().reset_index()
    casa_apostas.columns = ['Casa de Apostas', 'Quantidade']

    fig_casa = px.pie(casa_apostas, names='Casa de Apostas', values='Quantidade',
                      title="Distribuição por Casa de Apostas")
    st.plotly_chart(fig_casa, use_container_width=True)

    st.markdown("---")

    # Exibir a tabela final
    st.subheader("📋 Dados Completos")
    st.dataframe(df, use_container_width=True)

else:
    st.info("⏳ Aguardando o upload de um arquivo CSV.")
