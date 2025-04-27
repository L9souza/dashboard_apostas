import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# Configurações da página (gráficos maiores)
st.set_page_config(
    page_title="Dashboard de Apostas", 
    page_icon="🎯", 
    layout="wide",
    initial_sidebar_state="expanded"  # Mais espaço para gráficos
)

st.title('🎯 Dashboard de Apostas Esportivas')

# --- Carregamento e tratamento dos dados ---
nome_arquivo = 'apostas_atualizadas.csv'
caminho_arquivo = None

for raiz, _, arquivos in os.walk(os.getcwd()):
    if nome_arquivo in arquivos:
        caminho_arquivo = os.path.join(raiz, nome_arquivo)
        break

if caminho_arquivo:
    df = pd.read_csv(caminho_arquivo, delimiter=';')
    df.columns = df.columns.str.strip()
    df = df.dropna(subset=["Data"])

    # Conversão de valores
    for col in ['Valor Apostado (R$)', 'Retorno Previsto (R$)', 'Lucro/Prejuízo (R$)']:
        df[col] = (
            df[col].astype(str)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .str.strip()
            .astype(float)
        )

    df['Lucro/Prejuízo (R$)'] = df['Lucro/Prejuízo (R$)'].fillna(0)
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')

    # --- Consolida dados por data (soma múltiplas apostas no mesmo dia) ---
    df_consolidado = df.groupby('Data').agg({
        'Valor Apostado (R$)': 'sum',
        'Retorno Previsto (R$)': 'sum',
        'Lucro/Prejuízo (R$)': 'sum'
    }).reset_index()
    df_consolidado['Data'] = df_consolidado['Data'].dt.strftime('%d/%m/%Y')

    # --- Métricas ---
    total_apostado = df_consolidado['Valor Apostado (R$)'].sum()
    total_retorno = df_consolidado['Retorno Previsto (R$)'].sum()
    total_lucro = df_consolidado['Lucro/Prejuízo (R$)'].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Apostado", f"R$ {total_apostado:,.2f}")
    col2.metric("🎯 Retorno Previsto", f"R$ {total_retorno:,.2f}")
    col3.metric("📈 Lucro/Prejuízo", f"R$ {total_lucro:,.2f}", delta=f"{total_lucro:,.2f}")

    st.markdown("---")

    # --- Gráfico 1: Lucro por Data (MAIOR e consolidado) ---
    fig_lucro = go.Figure()
    
    fig_lucro.add_trace(go.Bar(
        x=df_consolidado['Data'],
        y=df_consolidado['Lucro/Prejuízo (R$)'],
        marker_color=['green' if x > 0 else 'red' for x in df_consolidado['Lucro/Prejuízo (R$)']],
        text=[f"R$ {x:,.2f}" for x in df_consolidado['Lucro/Prejuízo (R$)']],
        textposition='inside',
        width=0.5  # Barras mais largas
    ))

    fig_lucro.update_layout(
        title="Lucro/Prejuízo Consolidado por Data",
        xaxis_title='Data',
        yaxis_title='Lucro/Prejuízo (R$)',
        height=600,  # Altura aumentada
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_tickangle=-45,
        hovermode="x unified"
    )

    st.plotly_chart(fig_lucro, use_container_width=True)

    # --- Gráfico 2: Evolução Acumulada (novo) ---
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

    # --- Tabela de Dados (com formatação condicional) ---
    def color_lucro(val):
        if isinstance(val, str) and val.startswith('R$ '):
            val = float(val.replace('R$ ', '').replace(',', ''))
        if isinstance(val, (int, float)):
            if val > 0: return 'color: green; font-weight: bold;'
            elif val < 0: return 'color: red; font-weight: bold;'
        return ''

    df_display = df_consolidado.copy()
    for col in ['Valor Apostado (R$)', 'Retorno Previsto (R$)', 'Lucro/Prejuízo (R$)']:
        df_display[col] = df_display[col].apply(lambda x: f"R$ {x:,.2f}")

    styled_df = df_display.style.applymap(color_lucro, subset=['Lucro/Prejuízo (R$)'])
    st.subheader("📋 Dados Consolidados por Data")
    st.dataframe(styled_df, use_container_width=True, height=400)

else:
    st.error(f"Arquivo '{nome_arquivo}' não encontrado.")
