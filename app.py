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
    
    # Cálculo do lucro/prejuízo
    try:
        df['Lucro/Prejuízo (R$)'] = df['Retorno Previsto (R$)'] - df['Valor Apostado (R$)']
    except KeyError as e:
        st.error(f"Erro: A coluna {e} não foi encontrada. Verifique os nomes das colunas.")
    
    # Exibir os dados
    st.write("**Tabela de Apostas:**")
    st.dataframe(df, use_container_width=True)
    
    # Função para colorir as células baseado no lucro/prejuízo
    def colorize(val):
        color = 'green' if val > 0 else 'red'
        return f'color: {color}'
    
    # Só aplicar a estilização se a coluna existir
    if 'Lucro/Prejuízo (R$)' in df.columns:
        styled_df = df.style.applymap(colorize, subset=['Lucro/Prejuízo (R$)'])
        
        # Exibir a tabela estilizada corretamente
        st.write("**Tabela com Lucro/Prejuízo colorido:**")
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.warning("A coluna 'Lucro/Prejuízo (R$)' não foi criada. Tabela estilizada não será exibida.")
else:
    st.info("Por favor, faça o upload de um arquivo CSV.")
