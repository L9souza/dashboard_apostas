import streamlit as st
import pandas as pd
import plotly.express as px
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
else:
    st.error(f"Arquivo '{nome_arquivo}' não encontrado a partir de {diretorio_base}.")
    df = None

# Se o DataFrame foi carregado com sucesso
if df is not None:
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

    # Alterar para barras verticais em vez de pontos
    fig_lucro = px.bar(lucro_por_data, x='Data', y='Lucro/Prejuízo (R$)', 
                       title="Lucro/Prejuízo por Data", color='Lucro/Prejuízo (R$)', 
                       color_continuous_scale=['red', 'green'],  # Colorir barras de vermelho (prejuízo) a verde (lucro)
                       labels={'Lucro/Prejuízo (R$)': 'Lucro/Prejuízo (R$)', 'Data': 'Data'})

    # Ajustando o layout e aparência
    fig_lucro.update_layout(
        xaxis_title='Data',
        yaxis_title='Lucro/Prejuízo (R$)',
        xaxis_tickformat='%d/%m/%Y',  # Formatar o eixo X para o formato DD/MM/YYYY
        xaxis_tickangle=-45,  # Gira os ticks das datas para uma melhor visualização
        plot_bgcolor='rgb(30, 30, 30)',  # Fundo escuro
        paper_bgcolor='rgb(30, 30, 30)',  # Fundo escuro
        font=dict(color='white'),  # Texto em branco
        barmode='group',  # Adicionando um espaço entre as barras para evitar sobreposição
        bargap=0.2  # Definindo o espaço entre as barras
    )

    st.plotly_chart(fig_lucro, use_container_width=True)

    st.markdown("---")

    # Formatar a coluna Lucro/Prejuízo (R$) com cor condicional
    def color_lucro(val):
        if val > 0:
            return 'color: green;'  # Lucro em verde
        elif val < 0:
            return 'color: red;'  # Prejuízo em vermelho
        return ''  # Quando o valor for 0, não exibir cor

    # Aplicando formatação condicional
    df_style = df.style.applymap(color_lucro, subset=['Lucro/Prejuízo (R$)'])

    # Exibir a tabela final com formatação
    st.subheader("📋 Dados Completos")
    st.dataframe(df_style.format({
        'Valor Apostado (R$)': '{:,.2f}',
        'Retorno Previsto (R$)': '{:,.2f}',
        'Lucro/Prejuízo (R$)': '{:,.2f}',  # Formatar para não exibir muitos zeros à direita
    }), use_container_width=True)
