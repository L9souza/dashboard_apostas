import streamlit as st
import pandas as pd
import plotly.express as px

# Configurações da página
st.set_page_config(page_title="Dashboard de Apostas", page_icon="🎯", layout="wide")

st.title('🎯 Dashboard de Apostas Esportivas')

uploaded_file = st.file_uploader("Escolha um arquivo CSV", type="csv")

if uploaded_file is not None:
    # Carregar o arquivo
    df = pd.read_csv(uploaded_file, delimiter=';')
    df.columns = df.columns.str.strip()  # remove espaços extras nos nomes

    # Conversões de tipo (garantir que números sejam tratados como números)
    df['Valor Apostado (R$)'] = df['Valor Apostado (R$)'].str.replace(',', '.').astype(float)
    df['Retorno Previsto (R$)'] = df['Retorno Previsto (R$)'].str.replace(',', '.').astype(float)
    df['Lucro/Prejuízo (R$)'] = df['Lucro/Prejuízo (R$)'].str.replace(',', '.').astype(float)

    # Corrigir data
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df['Data'] = df['Data'].dt.strftime('%d/%m/%Y')  # Alterando a formatação da data

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

    # Gráfico 1: Lucro por Data (Estilo normal)
    lucro_por_data = df.groupby('Data')['Lucro/Prejuízo (R$)'].sum().reset_index()

    # Criando o gráfico com Plotly
    fig_lucro = px.line(lucro_por_data, x='Data', y='Lucro/Prejuízo (R$)', markers=True,
                        title="Lucro/Prejuízo por Data", line_shape='linear')

    # Estilo do gráfico
    fig_lucro.update_layout(
        xaxis_title='Data',
        yaxis_title='Lucro/Prejuízo (R$)',
        xaxis=dict(tickmode='array', tickangle=45),
        plot_bgcolor='rgb(30, 30, 30)',  # fundo do gráfico escuro
        paper_bgcolor='rgb(30, 30, 30)',  # fundo do gráfico geral
        font=dict(color='white')
    )

    # Exibindo o gráfico
    st.plotly_chart(fig_lucro, use_container_width=True)

    st.markdown("---")

    # Exibir a tabela final
    st.subheader("📋 Dados Completos")
    st.dataframe(df, use_container_width=True)
