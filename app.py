import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Configuração da página (remover barra lateral)
st.set_page_config(
    page_title="Dashboard de Apostas",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS para esconder o índice e melhorar a tabela
hide_table_row_index = """
    <style>
    thead tr th:first-child {display:none}
    tbody th {display:none}
    </style>
"""
st.markdown(hide_table_row_index, unsafe_allow_html=True)

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
df['Data_formatada'] = df['Data'].dt.strftime('%d/%m/%Y')  # só para exibição

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

df_consolidado = df_consolidado.sort_values('Data')
df_consolidado['Lucro Acumulado'] = df_consolidado['Lucro/Prejuízo (R$)'].cumsum()
df_consolidado['Data_formatada'] = df_consolidado['Data'].dt.strftime('%d/%m/%Y')

BANCA_INICIAL = 1250
if not df_consolidado.empty:
    ultimo_lucro = df_consolidado['Lucro Acumulado'].iloc[-1]
else:
    ultimo_lucro = 0

banca_atual = BANCA_INICIAL + ultimo_lucro
variacao_banca = banca_atual - BANCA_INICIAL

# --- Métricas principais ---
qtd_apostas = len(df)
media_cotacao = df['Cotação'].mean() if 'Cotação' in df.columns else 0
lucro_total = df['Lucro/Prejuízo (R$)'].sum()

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("📅 Total de Apostas", f"{qtd_apostas}")
col2.metric("💰 Banca Inicial", f"R$ {BANCA_INICIAL:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
col3.metric("📊 Cotação Média", f"{media_cotacao:.1f}")
col4.metric(
    "🏦 Banca Atual",
    f"R$ {banca_atual:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
    delta=f"R$ {variacao_banca:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
    delta_color="normal"
)
col5.metric(
    "📈 Lucro/Prejuízo Total",
    f"R$ {lucro_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
    delta=None,
    delta_color="off"
)

st.markdown("---")

# --- Gráfico de Lucro/Prejuízo por Data ---
fig_lucro = go.Figure()
fig_lucro.add_trace(go.Bar(
    x=df_consolidado['Data_formatada'],
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

# --- PAINEL DE ESTATÍSTICAS ---
st.markdown("---")
with st.container():
    if st.button("📈 Ver Estatísticas Detalhadas"):
        total_apostas = len(df)
        vencedoras = len(df[df['Status'] == 'Green'])
        perdedoras = len(df[df['Status'] == 'Red'])
        reembolsadas = len(df[df['Status'].str.lower().str.contains('anul', na=False)])
        em_curso = len(df[df['Status'].str.lower().str.contains('em curso', na=False)])
        valor_medio = df['Valor apostado (R$)'].mean()
        maior_lucro = df['Lucro/Prejuízo (R$)'].max()
        maior_red = df['Lucro/Prejuízo (R$)'].min()
        maior_cotacao = df[df['Status'] == 'Green']['Cotação'].max()
        taxa_sucesso = (vencedoras / (vencedoras + perdedoras)) * 100 if (vencedoras + perdedoras) > 0 else 0

        # Série máxima de vitórias/derrotas
        max_vit = max_der = vit = der = 0
        for s in df['Status']:
            if s == 'Green':
                vit += 1
                der = 0
            elif s == 'Red':
                der += 1
                vit = 0
            else:
                vit = der = 0
            max_vit = max(max_vit, vit)
            max_der = max(max_der, der)

        st.markdown("### 📊 Estatísticas de Apostas")
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"🔢 Total de Apostas: **{total_apostas}**")
            st.write(f"✅ Apostas Vencedoras: **{vencedoras}**")
            st.write(f"❌ Apostas Perdedoras: **{perdedoras}**")
            st.write(f"♻️ Apostas Reembolsadas: **{reembolsadas}**")
            st.write(f"⏳ Apostas em Curso: **{em_curso}**")
            st.write(f"📈 Taxa de Sucesso: **{taxa_sucesso:.2f}%**")

        with col2:
            st.write(f"💵 Valor Médio Apostado: **R$ {valor_medio:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
            st.write(f"🔥 Série Máxima de Vitórias: **{max_vit}**")
            st.write(f"💀 Série Máxima de Derrotas: **{max_der}**")
            st.write(f"🏆 Maior Lucro em Aposta: **R$ {maior_lucro:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
            st.write(f"🩸 Maior Prejuízo em Aposta: **R$ {maior_red:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
            st.write(f"📌 Maior Cotação Ganha: **{maior_cotacao:.2f}**")

# --- Funções de estilização ---
def colorir_valor(val):
    if isinstance(val, str):
        num_str = val.replace('R$', '').replace('RS', '').strip()
        num_str = num_str.replace('.', '').replace(',', '.')
        try:
            valor = float(num_str)
            if valor > 0:
                return 'color: #00AA00; font-weight: bold;'
            elif valor < 0:
                return 'color: #FF0000; font-weight: bold;'
            return 'color: white; font-weight: normal;'
        except:
            return ''
    return ''

def colorir_status(val):
    if val == "Green":
        return 'color: #00AA00; font-weight: bold;'
    elif val == "Red":
        return 'color: #FF0000; font-weight: bold;'
    return 'color: white; font-weight: normal;'

# --- Preparar DataFrame para exibição ---
df_display = df.copy()
for col in ['Valor apostado (R$)', 'Ganho (R$)', 'Lucro/Prejuízo (R$)']:
    if col in df_display.columns:
        df_display[col] = df_display[col].apply(
            lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        )
if 'Cotação' in df_display.columns:
    df_display['Cotação'] = df_display['Cotação'].apply(lambda x: f"{x:.1f}")

colunas_existentes = df_display.columns.tolist()
styled_df = df_display.style
for col in ['Lucro/Prejuízo (R$)', 'Ganho (R$)']:
    if col in colunas_existentes:
        styled_df = styled_df.applymap(colorir_valor, subset=[col])
if 'Status' in colunas_existentes:
    styled_df = styled_df.applymap(colorir_status, subset=['Status'])

st.dataframe(
    styled_df,
    use_container_width=True,
    height=450,        
    hide_index=True
)
