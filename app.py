import streamlit as st
import pandas as pd

# Configurar a página
st.set_page_config(
    page_title="Dashboard de Apostas Esportivas do LC",
    page_icon="📈",
    layout="wide"
)

# Título
st.title('📈 Dashboard de Apostas Esportivas do LC')

# Texto
st.write('Bem-vindo ao seu sistema de apostas!')

# Criar os dados (em forma de tabela)
dados = {
    'Data': ['16/04', '16/04', '16/04'],
    'Casa de Apostas': ['Viva Sorte BET', 'Viva Sorte BET', 'BET365'],
    'Jogador/Evento': ['Pedro Raul', 'Raphinha', 'Mugini'],
    'Tipo de Aposta': ['Marcar Gol', 'Marcar Gol', 'Assistência'],
    'Valor Apostado (R$)': [5.00, 12.50, 5.00],  # Valores como números
    'Retorno Previsto (R$)': [17.55, 48.26, 55.00]  # Valores como números
}

# Transformar em DataFrame
df = pd.DataFrame(dados)

# Calcular lucro
df['Lucro (R$)'] = df['Retorno Previsto (R$)'] - df['Valor Apostado (R$)']

# Mostrar a tabela no dashboard
st.dataframe(df)
