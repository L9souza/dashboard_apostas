import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Configurações da página
st.set_page_config(page_title="Dashboard de Apostas", page_icon="🎯", layout="wide")

st.title('🎯 Dashboard de Apostas Esportivas')

# Nome do arquivo que queremos encontrar
nome_arquivo = 'apostas_atualizadas.csv'

# Começamos procurando a partir do diretório onde o script está sendo executado
diretorio_base = os.getcwd()

# Variável para armazenar o caminho do arquivo encontrado
caminho_arquivo = None

# Procura o arquivo no diretório atual e em todas as subpastas
for raiz, diretorios, arquivos in os.walk(diretorio_base):
    if nome_arquivo in arquivos:
        caminho_arquivo = os.path.join(raiz, nome_arquivo)
        break

# Se o arquivo for encontrado, carregamos o CSV
if caminho_arquivo:
    df = pd.read_csv(caminho_arquivo, delimiter=';')  # Use o caminho encontrado aqui
    df.columns = df.columns.str.strip()

    # Limpeza dos dados
    df = df.dropna(subset=["Data"])  # remove linhas vazias

    # Correção da conversão de valores monetários
    for col in ['Valor Apostado (R$)', 'Retorno Previsto (R$)', 'Lucro/Prejuízo (R$)']:
        df[col] = (
            df[col].astype(str)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .str.strip()
            .astype(float)
        )

    # Substituir valores NaN ou None na coluna "Lucro/Prejuízo (R$)" com 0
    df['Lucro/Prejuízo (R$)'] = df['Lucro/Prejuízo (R$)'].fillna(0)

    # Ajustando a data para o formato brasileiro (sem hora)
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%Y')

    # Adicionando 1 ao índice para que comece a partir de 1
    df.index = df.index + 1

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

    # Gráfico 1: Lucro por Data (ajustes feitos)
    lucro_por_data = df.groupby('Data')['Lucro/Prejuízo (R$)'].sum().reset_index()
    lucro_por_data['Data'] = pd.to_datetime(lucro_por_data['Data'], format='%d/%m/%Y')

    # Definindo as cores e textos para lucro (verde) e prejuízo (vermelho)
    lucro
