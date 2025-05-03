import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Apostas",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title('🎯 Dashboard de Apostas Esportivas')

# --- Função para carregar os dados ---
@st.cache_data
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT_r9CxtMoWnWEkzzYwHAekTItzRrXjFvirDMNlokjlF82QzA8srPgDADnwRLef8WXh9XtFaIbwjRWE/pub?output=csv"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    return df

# --- Botão para atualizar dados ---
atualizar = st.button("🔄 Atualizar Dados")
if atualizar:
    st.cache_data.clear()
    st.rerun()
else:
    df = carregar_dados()

# --- Tratamento dos dados ---
df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%y', errors='coerce')
df = df.dropna(subset=["Data"])
df['Data'] = df['Data'].dt.strftime('%d/%m/%Y')

# --- Conversão de colunas numéricas ---
colunas_para_converter = ['Cotação', 'Valor apostado (R$)', 'Lucro/Prejuízo (R$)', 'Ganho (R$)']
for col in colunas_para_converter:
    if col in df.columns:
        df[col] = (
            df[col].astype(str)
            .str.replace('R\$', '', regex=True)
            .str.replace(r'[−–‐]', '-', regex=True)
            .str.replace('- ', '-', regex=False)
            .str.replace(' ', '', regex=False)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .str.strip()
        )
        df[col] = pd.to_numeric(df[col], errors='coerce')

df = df.dropna(subset=colunas_para_converter, how='all')

# --- Cálculos da banca ---
df_consolidado = df.groupby('Data').agg({
    'Valor apostado (R$)': 'sum',
    'Ganho (R$)': 'sum',
    'Lucro/Prejuízo (R$)': 'sum'
}).reset_index()

df_consolidado['Lucro Acumulado'] = df_consolidado['Lucro/Prejuízo (R$)'].cumsum()
BANCA_INICIAL = 1250  # Altere aqui conforme necessário
banca_atual = BANCA_INICIAL + df_consolidado['Lucro Acumulado'].iloc[-1]
variacao_banca = banca_atual - BANCA_INICIAL

# --- Métricas principais ---
qtd_apostas = len(df)
media_cotacao = df['Cotação'].mean() if 'Cotação' in df.columns else 0
total_lucro = df['Lucro/Prejuízo (R$)'].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("📅 Total de Apostas", f"{qtd_apostas}")
col2.metric("📊 Cotação Média", f"{media_cotacao:.2f}")
col3.metric("💰 Banca Inicial", f"R$ {BANCA_INICIAL:,.2f}")
col4.metric("🏦 Banca Atual", f"R$ {banca_atual:,.2f}", delta=f"R$ {variacao_banca:,.2f}")

st.markdown("---")

# --- Gráfico de Lucro/Prejuízo por Data ---
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
    title="Lucro/Prejuízo por Data",
    xaxis_title='Data',
    yaxis_title='Valor (R$)',
    height=500,
    plot_bgcolor='rgba(0,0,0,0)',
    hovermode="x unified"
)
st.plotly_chart(fig_lucro, use_container_width=True)

st.markdown("---")

# --- Função para colorir os valores (Green e Red) ---
def colorir_lucro(val):
    if isinstance(val, str) and val.startswith('R$ '):
        val = float(val.replace('R$ ', '').replace(',', ''))
    if isinstance(val, (int, float)):
        if val > 0:
            return 'color: green; font-weight: bold;'  # Green
        elif val < 0:
            return 'color: red; font-weight: bold;'  # Red
        else:
            return 'color: white;'  # Para valores zero
    return ''

# --- Função para colorir a coluna 'Ganho (R$)' --- 
def colorir_ganho(row):
    if row['Status'] == "Green":
        return 'color: green; font-weight: bold;'  # Green
    elif row['Status'] == "Red":
        return 'color: red; font-weight: bold;'  # Red
    return 'color: white;'  # Para 'Anulada'

# Formatando o dataframe
df_display = df.copy()
df_display['Ganho (R$)'] = df_display['Ganho (R$)'].apply(lambda x: f"R$ {x:,.2f}")
df_display['Lucro/Prejuízo (R$)'] = df_display['Lucro/Prejuízo (R$)'].apply(lambda x: f"R$ {x:,.2f}")

# Aplicando as cores
styled_df = df_display.style.applymap(colorir_lucro, subset=['Lucro/Prejuízo (R$)']) \
                            .apply(colorir_ganho, axis=1, subset=['Ganho (R$)'])

st.dataframe(styled_df, use_container_width=True, height=450)
