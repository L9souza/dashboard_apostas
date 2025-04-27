import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# Configurações iniciais da página
st.set_page_config(
    page_title="Dashboard de Apostas",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title('🎯 Dashboard de Apostas Esportivas')

# --- Função para localizar o arquivo de dados ---
def encontrar_arquivo(nome_arquivo):
    for raiz, _, arquivos in os.walk(os.getcwd()):
        if nome_arquivo in arquivos:
            return os.path.join(raiz, nome_arquivo)
    return None

# --- Carregar dados ---
nome_arquivo = 'apostas_atualizadas.csv'
caminho_arquivo = encontrar_arquivo(nome_arquivo)

if caminho_arquivo:
    df = pd.read_csv(caminho_arquivo, delimiter=';')
    df.columns = df.columns.str.strip()

    # Mostrar colunas encontradas na sidebar
    with st.sidebar:
        st.subheader("🔎 Colunas no arquivo:")
        st.write(df.columns.tolist())

    # --- Tratamento de dados ---
    df = df.dropna(subset=["Data"])

    # Definir as colunas que queremos converter
    colunas_para_converter = ['Valor Apostado (R$)', 'Retorno Previsto (R$)', 'Lucro/Prejuízo (R$)']
    colunas_existentes = [col for col in colunas_para_converter if col in df.columns]

    for col in colunas_existentes:
        df[col] = (
            df[col].astype(str)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .str.strip()
            .astype(float)
        )

    if 'Lucro/Prejuízo (R$)' in df.columns:
        df['Lucro/Prejuízo (R$)'] = df['Lucro/Prejuízo (R$)'].fillna(0)
    
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')

    # --- Consolidar dados por Data ---
    colunas_agrupar = {col: 'sum' for col in ['Valor Apostado (R$)', 'Retorno Previsto (R$)', 'Lucro/Prejuízo (R$)'] if col in df.columns}
    df_consolidado = df.groupby('Data').agg(colunas_agrupar).reset_index()

    df_consolidado['Data'] = df_consolidado['Data'].dt.strftime('%d/%m/%Y')

    # --- Métricas Principais ---
    total_apostado = df_consolidado.get('Valor Apostado (R$)', pd.Series(dtype=float)).sum()
    total_retorno = df_consolidado.get('Retorno Previsto (R$)', pd.Series(dtype=float)).sum()
    total_lucro = df_consolidado.get('Lucro/Prejuízo (R$)', pd.Series(dtype=float)).sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Apostado", f"R$ {total_apostado:,.2f}")
    col2.metric("🎯 Retorno Previsto", f"R$ {total_retorno:,.2f}")
    col3.metric("📈 Lucro/Prejuízo", f"R$ {total_lucro:,.2f}", delta=f"{total_lucro:,.2f}")

    st.markdown("---")

    # --- Gráfico de Lucro/Prejuízo por Data ---
    if 'Lucro/Prejuízo (R$)' in df_consolidado.columns:
        fig_lucro = go.Figure()
        fig_lucro.add_trace(go.Bar(
            x=df_consolidado['Data'],
            y=df_consolidado['Lucro/Prejuízo (R$)'],
            marker_color=['green' if x > 0 else 'red' for x in df_consolidado['Lucro/Prejuízo (R$)']],
            text=[f"R$ {x:,.2f}" for x in df_consolidado['Lucro/Prejuízo (R$)']],
            textposition='inside',
            width=0.6
        ))

        fig_lucro.update_layout(
            title="Lucro/Prejuízo Consolidado por Data",
            xaxis_title='Data',
            yaxis_title='Lucro/Prejuízo (R$)',
            height=600,
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_tickangle=-45,
            hovermode="x unified"
        )

        st.plotly_chart(fig_lucro, use_container_width=True)

        # --- Gráfico de Evolução Acumulada ---
        df_consolidado['Lucro Acumulado'] = df_consolidado['Lucro/Prejuízo (R$)'].cumsum()

        fig_acumulado = go.Figure()
        fig_acumulado.add_trace(go.Scatter(
            x=df_consolidado['Data'],
            y=df_consolidado['Lucro Acumulado'],
            mode='lines+markers',
            line=dict(color='gold', width=3),
            marker=dict(size=10)
        ))

        fig_acumulado.update_layout(
            title="Evolução do Lucro Acumulado",
            xaxis_title='Data',
            yaxis_title='Lucro Acumulado (R$)',
            height=500,
            showlegend=False
        )

        st.plotly_chart(fig_acumulado, use_container_width=True)

        st.markdown("---")

        # --- Tabela de Dados ---
        def colorir_lucro(val):
            if isinstance(val, str) and val.startswith('R$ '):
                val = float(val.replace('R$ ', '').replace(',', ''))
            if isinstance(val, (int, float)):
                if val > 0: return 'color: green; font-weight: bold;'
                elif val < 0: return 'color: red; font-weight: bold;'
            return ''

        df_display = df_consolidado.copy()
        for col in ['Valor Apostado (R$)', 'Retorno Previsto (R$)', 'Lucro/Prejuízo (R$)']:
            if col in df_display.columns:
                df_display[col] = df_display[col].apply(lambda x: f"R$ {x:,.2f}")

        styled_df = df_display.style.applymap(colorir_lucro, subset=['Lucro/Prejuízo (R$)'])
        st.subheader("📋 Dados Consolidados por Data")
        st.dataframe(styled_df, use_container_width=True, height=450)

else:
    st.error(f"Arquivo '{nome_arquivo}' não encontrado. Por favor, envie o arquivo correto.")
