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

# --- Função para carregar os dados ---
@st.cache_data
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT_r9CxtMoWnWEkzzYwHAekTItzRrXjFvirDMNlokjlF82QzA8srPgDADnwRLef8WXh9XtFaIbwjRWE/pub?output=csv"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    return df

# --- Atualizar dados ---
if st.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()
else:
    df = carregar_dados()

# --- Processamento de datas e conversões ---
df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%y', errors='coerce')
df = df.dropna(subset=["Data"])
df['Data'] = df['Data'].dt.strftime('%d/%m/%Y')  # <-- Só a data, sem horário

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

# --- Cálculo da banca consolidada ---
df_consolidado = df.groupby('Data').agg({
    'Valor apostado (R$)': 'sum',
    'Ganho (R$)': 'sum',
    'Lucro/Prejuízo (R$)': 'sum'
}).reset_index()

df_consolidado = df_consolidado.sort_values('Data')
df_consolidado['Lucro Acumulado'] = df_consolidado['Lucro/Prejuízo (R$)'].cumsum()

BANCA_INICIAL = 1250
ultimo_lucro = df_consolidado['Lucro Acumulado'].iloc[-1] if not df_consolidado.empty else 0
banca_atual = BANCA_INICIAL + ultimo_lucro
variacao_banca = banca_atual - BANCA_INICIAL

# --- Métricas principais ---
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("📅 Total de Apostas", f"{len(df)}")
col2.metric("💰 Banca Inicial", f"R$ {BANCA_INICIAL:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
col3.metric("📊 Cotação Média", f"{df['Cotação'].mean():.1f}")
col4.metric("🏦 Banca Atual", f"R$ {banca_atual:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), delta=f"R$ {variacao_banca:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), delta_color="inverse" if variacao_banca < 0 else "normal")
col5.metric("📈 Lucro/Prejuízo Total", f"R$ {df['Lucro/Prejuízo (R$)'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

st.markdown("---")

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

# --- Estatísticas detalhadas ---
st.markdown("---")
if st.button("📈 Ver Estatísticas Detalhadas"):
    status_col = df['Status'].fillna('').str.lower().str.strip()
    total = len(df)
    greens = (status_col == 'green').sum()
    reds = (status_col == 'red').sum()
    anuladas = status_col.str.contains('anul').sum()
    em_curso = status_col.str.contains('em curso').sum()

    taxa_sucesso = (greens / (greens + reds)) * 100 if (greens + reds) > 0 else 0
    valor_green = df.loc[status_col == 'green', 'Valor apostado (R$)'].sum()
    valor_red = df.loc[status_col == 'red', 'Valor apostado (R$)'].sum()
    taxa_valor = (valor_green / (valor_green + valor_red)) * 100 if (valor_green + valor_red) > 0 else 0

    maior_lucro = df['Lucro/Prejuízo (R$)'].max()
    maior_red = df['Lucro/Prejuízo (R$)'].min()
    maior_cotacao = df.loc[status_col == 'green', 'Cotação'].max()
    valor_medio = df['Valor apostado (R$)'].mean()

    vit = der = max_vit = max_der = 0
    for s in status_col:
        if s == 'green':
            vit += 1
            der = 0
        elif s == 'red':
            der += 1
            vit = 0
        else:
            vit = der = 0
        max_vit = max(max_vit, vit)
        max_der = max(max_der, der)

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"🔢 Total de Apostas: **{total}**")
        st.write(f"✅ Apostas Vencedoras: **{greens}**")
        st.write(f"❌ Apostas Perdedoras: **{reds}**")
        st.write(f"♻️ Apostas Reembolsadas: **{anuladas}**")
        st.write(f"⏳ Apostas em Curso: **{em_curso}**")
        st.write(f"📈 Taxa de Sucesso (Qtd): **{taxa_sucesso:.2f}%**")
        st.write(f"💸 Taxa de Sucesso (Valor): **{taxa_valor:.2f}%**")
    with col2:
        st.write(f"💵 Valor Médio Apostado: **R$ {valor_medio:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.write(f"🔥 Série Máxima de Vitórias: **{max_vit}**")
        st.write(f"💀 Série Máxima de Derrotas: **{max_der}**")
        st.write(f"🏆 Maior Lucro em Aposta: **R$ {maior_lucro:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.write(f"🩸 Maior Prejuízo em Aposta: **R$ {maior_red:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.write(f"📌 Maior Cotação Ganha: **{maior_cotacao:.2f}**")

# --- Estilização da tabela ---
def colorir_valor(val):
    if isinstance(val, str):
        val = val.replace('R$', '').replace('RS', '').strip().replace('.', '').replace(',', '.')
        try:
            val = float(val)
            if val > 0: return 'color: #00AA00; font-weight: bold;'
            if val < 0: return 'color: #FF0000; font-weight: bold;'
            return 'color: white;'
        except: return ''
    return ''

def colorir_status(val):
    if val == "Green": return 'color: #00AA00; font-weight: bold;'
    if val == "Red": return 'color: #FF0000; font-weight: bold;'
    return 'color: white;'

df_display = df.copy()
def formatar_moeda_condicional(valor, status):
    if pd.isna(status) or status.lower() not in ['green', 'red', 'anulado']:
        return '—'
    if pd.isna(valor):
        return '—'
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# Aplica formatação condicional
if 'Status' in df_display.columns:
    df_display['Lucro/Prejuízo (R$)'] = df.apply(lambda row: formatar_moeda_condicional(row['Lucro/Prejuízo (R$)'], row['Status']), axis=1)
    df_display['Ganho (R$)'] = df.apply(lambda row: formatar_moeda_condicional(row['Ganho (R$)'], row['Status']), axis=1)

# Valor apostado sempre aparece
if 'Valor apostado (R$)' in df_display.columns:
    df_display['Valor apostado (R$)'] = df_display['Valor apostado (R$)'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

if 'Cotação' in df_display.columns:
    df_display['Cotação'] = df_display['Cotação'].apply(lambda x: f"{x:.2f}")

styled_df = df_display.style
for col in ['Lucro/Prejuízo (R$)', 'Ganho (R$)']:
    styled_df = styled_df.applymap(colorir_valor, subset=[col])
if 'Status' in df_display.columns:
    styled_df = styled_df.applymap(colorir_status, subset=['Status'])

st.dataframe(styled_df, use_container_width=True, hide_index=True, height=450)
