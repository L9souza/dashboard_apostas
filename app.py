import streamlit as st
import pandas as pd

# Configurar página
st.set_page_config(page_title="Dashboard de Apostas", page_icon="📈", layout="wide")

# Título
st.title('📈 Dashboard de Apostas Esportivas do LC')

# Carregar o arquivo CSV
uploaded_file = st.file_uploader("Escolha um arquivo CSV", type="csv")

if uploaded_file is not None:
    # Carregar o CSV
    df = pd.read_csv(uploaded_file, delimiter=',')
    
    # Exibir as colunas para verificar se estão corretas
    st.write("Colunas do arquivo CSV:", df.columns)
    
    # Remover espaços extras dos nomes das colunas
    df.columns = df.columns.str.strip()
    
    # Cálculo do lucro/prejuízo (subtraindo o valor apostado do retorno previsto)
    try:
        df['Lucro/Prejuízo (R$)'] = df['Retorno Previsto (R$)'] - df['Valor Apostado (R$)']
    except KeyError as e:
        st.write(f"Erro: A coluna {e} não foi encontrada. Verifique os nomes das colunas.")
    
    # Exibir os dados
    st.write("**Tabela de Apostas:**")
    st.write(df)
    
    # Função para colorir as células baseado no lucro/prejuízo
    def colorize(val):
        color = 'green' if val > 0 else 'red'
        return f'color: {color}'
    
    # Aplicando a cor no dataframe
    styled_df = df.style.applymap(colorize, subset=['Lucro/Prejuízo (R$)'])
    
    # Exibir a tabela estilizada com lucros e prejuízos coloridos
    st.write("**Tabela com Lucro/Prejuízo colorido:**")
    st.write(styled_df)

else:
    st.write("Por favor, faça o upload de um arquivo CSV.")

