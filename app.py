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
BANCA_INICIAL = 1250
banca_atual = BANCA_INICIAL + df_consolidado['Lucro Acumulado'].iloc[-1]
variacao_banca = banca_atual - BANCA_INICIAL

# --- Métricas principais ---
qtd_apostas = len(df)
media_cotacao = df['Cotação'].mean() if 'Cotação' in df.columns else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("📅 Total de Apostas", f"{qtd_apostas}")
col2.metric("💰 Banca Inicial", f"R$ {BANCA_INICIAL:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
col3.metric("📊 Cotação Média", f"{media_cotacao:.1f}")
col4.metric(
    "🏦 Banca Atual",
    f"R$ {banca_atual:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
    delta=f"R$ {variacao_banca:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
)

st.markdown("---")

# --- Gráfico de Lucro/Prejuízo por Data ---
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

st.markdown("---")

# --- Funções de estilização ---
def colorir_valor(val):
    if isinstance(val, str):
        # Remove formatação monetária para análise
        num_str = val.replace('R$', '').replace('RS', '').strip()
        num_str = num_str.replace('.', '').replace(',', '.')
        try:
            valor = float(num_str)
            if valor > 0:
                return 'color: #00AA00; font-weight: bold;'  # Verde
            elif valor < 0:
                return 'color: #FF0000; font-weight: bold;'  # Vermelho
            return 'color: white; font-weight: normal;'      # Zero
        except:
            return ''
    return ''

def colorir_status(val):
    if val == "Green":
        return 'color: #00AA00; font-weight: bold;'  # Verde
    elif val == "Red":
        return 'color: #FF0000; font-weight: bold;'  # Vermelho
    return 'color: white; font-weight: normal;'      # Outros = branco

# --- Preparar DataFrame para exibição ---
df_display = df.copy()

# Formatar colunas monetárias (com separador brasileiro)
for col in ['Valor apostado (R$)', 'Ganho (R$)', 'Lucro/Prejuízo (R$)']:
    if col in df_display.columns:
        df_display[col] = df_display[col].apply(
            lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        )

# Formatar cotação com 1 casa decimal
if 'Cotação' in df_display.columns:
    df_display['Cotação'] = df_display['Cotação'].apply(lambda x: f"{x:.1f}")

# --- Aplicar estilização ---
colunas_existentes = df_display.columns.tolist()
styled_df = df_display.style

# Estilizar colunas monetárias
for col in ['Lucro/Prejuízo (R$)', 'Ganho (R$)']:
    if col in colunas_existentes:
        styled_df = styled_df.applymap(colorir_valor, subset=[col])

# Estilizar coluna de Status
if 'Status' in colunas_existentes:
    styled_df = styled_df.applymap(colorir_status, subset=['Status'])

# --- Exibição final ---
st.dataframe(
    styled_df,
    use_container_width=True,
    height=450,
    hide_index=True
)
