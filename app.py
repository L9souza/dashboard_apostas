import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Configuração da página ---
st.set_page_config(
    page_title="Dashboard de Apostas",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS para esconder índice da tabela ---
st.markdown("""
    <style>
    thead tr th:first-child {display:none}
    tbody th {display:none}
    </style>
""", unsafe_allow_html=True)

st.title('🎯 Dashboard de Apostas Esportivas')

@st.cache_data
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT_r9CxtMoWnWEkzzYwHAekTItzRrXjFvirDMNlokjlF82QzA8srPgDADnwRLef8WXh9XtFaIbwjRWE/pub?output=csv"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    return df

if st.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()

df = carregar_dados()

# --- Tratamento de colunas e datas ---
df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%y', errors='coerce')
df = df.dropna(subset=["Data"])
df['Data'] = df['Data'].dt.strftime('%d/%m/%Y')

# --- Conversão robusta de valores ---
colunas_para_converter = ['Cotação', 'Valor apostado (R$)', 'Lucro/Prejuízo (R$)', 'Ganho (R$)']
def limpar_valor_monetario(valor):
    if isinstance(valor, str):
        valor = valor.replace('R$', '').replace('−', '-').replace('–', '-').replace('‐', '-')
        valor = valor.replace('- ', '-').replace(' ', '').replace('.', '').replace(',', '.').strip()
    return pd.to_numeric(valor, errors='coerce')
for col in colunas_para_converter:
    df[col] = df[col].apply(limpar_valor_monetario)

# --- Status normalizado ---
df['Status'] = df['Status'].astype(str).str.strip().str.lower()
status_validos = ['green', 'red', 'anulado']
df_finalizadas = df[df['Status'].isin(status_validos)].copy()

# --- Cálculo por data ---
df_consolidado = df_finalizadas.groupby('Data').agg({
    'Valor apostado (R$)': 'sum',
    'Ganho (R$)': 'sum',
    'Lucro/Prejuízo (R$)': 'sum'
}).reset_index()
df_consolidado = df_consolidado.sort_values('Data')
df_consolidado['Lucro Acumulado'] = df_consolidado['Lucro/Prejuízo (R$)'].cumsum()

# --- Cálculos principais ---
BANCA_INICIAL = 1250
lucro_total = df_finalizadas['Lucro/Prejuízo (R$)'].sum()
ultimo_lucro = df_consolidado['Lucro Acumulado'].iloc[-1] if not df_consolidado.empty else 0
banca_atual = BANCA_INICIAL + ultimo_lucro
variacao_banca = banca_atual - BANCA_INICIAL

# --- Métricas principais ---
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("📅 Total de Apostas", f"{len(df)}")
col2.metric("💰 Banca Inicial", f"R$ {BANCA_INICIAL:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
col3.metric("📊 Cotação Média", f"{df_finalizadas['Cotação'].mean():.1f}")
col4.metric("🏦 Banca Atual", f"R$ {banca_atual:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), delta=f"R$ {variacao_banca:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), delta_color="inverse" if variacao_banca < 0 else "normal")
col5.metric("📈 Lucro/Prejuízo Total", f"R$ {lucro_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

# --- Estatísticas detalhadas ---
with st.expander("📊 Estatísticas Detalhadas"):
    total_apostas = len(df_finalizadas)
    greens = (df_finalizadas['Status'] == 'green').sum()
    reds = (df_finalizadas['Status'] == 'red').sum()
    anuladas = (df_finalizadas['Status'] == 'anulado').sum()
    green_pct = greens / total_apostas * 100 if total_apostas > 0 else 0
    red_pct = reds / total_apostas * 100 if total_apostas > 0 else 0
    anulado_pct = anuladas / total_apostas * 100 if total_apostas > 0 else 0
    maior_lucro = df_finalizadas['Lucro/Prejuízo (R$)'].max()
    maior_prejuizo = df_finalizadas['Lucro/Prejuízo (R$)'].min()
    media_lucro = df_finalizadas['Lucro/Prejuízo (R$)'].mean()

    st.markdown(f"**🎯 Total de Apostas Finalizadas:** {total_apostas}")
    st.markdown(f"✅ **Greens:** {greens} ({green_pct:.1f}%)")
    st.markdown(f"❌ **Reds:** {reds} ({red_pct:.1f}%)")
    st.markdown(f"⚪ **Anuladas:** {anuladas} ({anulado_pct:.1f}%)")
    st.markdown(f"📈 **Lucro Total:** R$ {lucro_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    st.markdown(f"💰 **Média por Aposta:** R$ {media_lucro:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    st.markdown(f"📈 **Maior Lucro:** R$ {maior_lucro:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    st.markdown(f"📉 **Maior Prejuízo:** R$ {maior_prejuizo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

# --- Gráfico de lucro por data ---
fig_lucro = go.Figure()
fig_lucro.add_trace(go.Bar(
    x=df_consolidado['Data'],
    y=df_consolidado['Lucro/Prejuízo (R$)'],
    marker_color=['green' if x > 0 else 'red' for x in df_consolidado['Lucro/Prejuízo (R$)']],
    text=[f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') for x in df_consolidado['Lucro/Prejuízo (R$)']],
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

# --- Tabela com estilização condicional ---
def formatar_moeda_condicional(valor, status):
    if pd.isna(status) or status not in ['green', 'red', 'anulado']:
        return '—'
    if pd.isna(valor):
        return '—'
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def colorir_valor(val):
    if isinstance(val, str):
        try:
            val = float(val.replace('R$', '').replace('.', '').replace(',', '.'))
            if val > 0: return 'color: #00AA00; font-weight: bold;'
            if val < 0: return 'color: #FF0000; font-weight: bold;'
        except: return ''
    return ''

def colorir_status(val):
    if val == "green": return 'color: #00AA00; font-weight: bold;'
    if val == "red": return 'color: #FF0000; font-weight: bold;'
    return 'color: white;'

df_display = df.copy()
df_display['Lucro/Prejuízo (R$)'] = df.apply(lambda row: formatar_moeda_condicional(row['Lucro/Prejuízo (R$)'], row['Status']), axis=1)
df_display['Ganho (R$)'] = df.apply(lambda row: formatar_moeda_condicional(row['Ganho (R$)'], row['Status']), axis=1)
df_display['Valor apostado (R$)'] = df_display['Valor apostado (R$)'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
df_display['Cotação'] = df_display['Cotação'].apply(lambda x: f"{x:.2f}")

styled_df = df_display.style
styled_df = styled_df.applymap(colorir_valor, subset=['Lucro/Prejuízo (R$)', 'Ganho (R$)'])
styled_df = styled_df.applymap(colorir_status, subset=['Status'])

st.dataframe(styled_df, use_container_width=True, hide_index=True, height=450)
