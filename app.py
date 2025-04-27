import streamlit as st
import pandas as pd

# Configurar página
st.set_page_config(page_title="Dashboard de Apostas", page_icon="📈", layout="wide")

# Título
st.title('📈 Dashboard de Apostas Esportivas do LC')

# Adiciona a opção para o usuário fazer upload do arquivo CSV
uploaded_file = st.file_uploader("Escolha um arquivo CSV", type="csv")

if uploaded_file is not None:
    # Carrega o CSV
    df = pd.read_csv(uploaded_file, delimiter=',')
    
    # Mostra os nomes das colunas para checar se estão corretas
    st.write("Nomes das colunas:", df.columns)
    
    # Remove espaços extras nos nomes das colunas
    df.columns = df.columns.str.strip()
    
    # Cálculo do lucro/prejuízo (subtrai o valor apostado do retorno previsto)
    df['Lucro/Prejuízo (R$)'] = df['Retorno Previsto (R$)'] - df['Valor Apostado (R$)']
    
    # Exibe os dados
    st.write("**Tabela de Apostas:**")
    st.write(df)
    
    # Função para colorir as células baseado no lucro/prejuízo
    def colorize(val):
        color = 'green' if val > 0 else 'red'
        return f'color: {color}'
    
    # Aplica a cor no dataframe
    styled_df = df.style.applymap(colorize, subset=['Lucro/Prejuízo (R$)'])
    
    # Exibe a tabela estilizada com os lucros e prejuízos coloridos
    st.write("**Tabela com Lucro/Prejuízo colorido:**")
    st.write(styled_df)
    
else:
    st.write("Por favor, faça o upload de um arquivo CSV.")
