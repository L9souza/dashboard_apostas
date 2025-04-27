import streamlit as st
import pandas as pd

# Configurar a página
st.set_page_config(page_title="Dashboard de Apostas", page_icon="📈", layout="wide")

# Título
st.title('📈 Dashboard de Apostas Esportivas do LC')

# Dados de apostas
dados = {
    'Data': ['16/04', '16/04', '16/04'],
    'Casa de Apostas': ['Viva Sorte BET', 'Viva Sorte BET', 'BET365'],
    'Jogador/Evento': ['Pedro Raul', 'Raphinha', 'Mugini'],
    'Tipo de Aposta': ['Marcar Gol', 'Marcar Gol', 'Assistência'],
    'Valor Apostado (R$)': [5.00, 12.50, 5.00],
    'Retorno Previsto (R$)': [17.55, 48.26, 55.00]
}
df = pd.DataFrame(dados)

# Calcular lucro
df['Lucro (R$)'] = df['Retorno Previsto (R$)'] - df['Valor Apostado (R$)']

# Calcular Resumos
total_apostado = df['Valor Apostado (R$)'].sum()
lucro_total = df['Lucro (R$)'].sum()
roi = (lucro_total / total_apostado) * 100

# Mostrar Cards Resumo
col1, col2, col3 = st.columns(3)

col1.metric("Valor Apostado", f"R${total_apostado:.2f}")
col2.metric("Lucro Total", f"R${lucro_total:.2f}")
col3.metric("ROI (%)", f"{roi:.2f}%")

# Mostrar Tabela de Apostas
st.subheader('📋 Histórico de Apostas')
st.dataframe(df)

# Calcular o saldo acumulado
df['Saldo Acumulado (R$)'] = df['Lucro (R$)'].cumsum()

# Mostrar Gráfico de Saldo
st.subheader('📈 Evolução do Saldo')
st.line_chart(df[['Saldo Acumulado (R$)']])
