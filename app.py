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

    # --- Tratamento de dados ---
    df = df.dropna(subset=["Data"])

    # Converter colunas necessárias apenas se existirem
    colunas_para_converter = ['Cotação', 'Valor Apostado (R$)', 'Lucro/Prejuízo (R$)', 'Ganho (R$)']
    for col in colunas_para_converter:
        if col in df.columns:
            df[col] = (
                df[col].astype(str)
                .str.replace('.', '', regex=False)
                .str.replace(',', '.', regex=False)
                .str.strip()
                .astype(float)
            )

    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df['Data'] = df['Data'].dt.strftime('%d/%m/%Y')

    # --- Calcular Lucro/Prejuízo se não existir ---
    if 'Lucro/Prejuízo (R$)' not in df.columns and 'Ganho (R$)' in df.columns and 'Valor Apostado (R$)' in df.columns:
        df['Lucro/Prejuízo (R$)'] = df['Ganho (R$)'] - df['Valor Apostado (R$)']

    # --- Consolida dados ---
    df_consolidado = df.groupby('Data').agg({
        'Valor Apostado (R$)': 'sum',
        'Ganho (R$)': 'sum',
        'Lucro/Prejuízo (R$)': 'sum'
    }).reset_index()

    # --- Métricas Principais ---
    qtd_apostas = len(df)
    media_cotacao = df['Cotação'].mean() if 'Cotação' in df.columns else 0
    total_lucro = df['Lucro/Prejuízo (R$)'].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("📅 Quantidade de Apostas", f"{qtd_apostas}")
    col2.metric("🔢 Média das Cotações", f"{media_cotacao:.2f}")
    col3.metric("📈 Lucro/Prejuízo", f"R$ {total_lucro:,.2f}", delta=f"{total_lucro:,.2f}")

    st.markdown("---")

    # --- Gráfico de Lucro/Prejuízo Consolidado ---
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
        xaxis_tickangle=0,
        hovermode="x unified"
    )

    st.plotly_chart(fig_lucro, use_container_width=True)

    st.markdown("---")

    # --- Tabela de Dados ---
    def colorir_lucro(val):
        if isinstance(val, str) and val.startswith('R$ '):
            val = float(val.replace('R$ ', '').replace(',', ''))
        if isinstance(val, (int, float)):
            if val > 0: return 'color: green; font-weight: bold;'
            elif val < 0: return 'color: red; font-weight: bold;'
        return ''

    df_display = df.reset_index(drop=True).copy()
    for col in ['Valor Apostado (R$)', 'Ganho (R$)', 'Lucro/Prejuízo (R$)']:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(lambda x: f"R$ {x:,.2f}")

    styled_df = df_display.style.applymap(colorir_lucro, subset=['Lucro/Prejuízo (R$)'])
    st.subheader("📋 Todas as Apostas")
    st.dataframe(styled_df, use_container_width=True, height=450, hide_index=True)

else:
    st.error(f"Arquivo '{nome_arquivo}' não encontrado. Por favor, envie o arquivo correto.")
