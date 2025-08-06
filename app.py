import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Configurações Iniciais da Página ---
st.set_page_config(
    page_title="Dashboard de Apostas Esportivas",
    page_icon="🎯",
    layout="wide"
)

# --- Título do Dashboard ---
st.title("🎯 Dashboard de Apostas Esportivas")

# --- Funções Auxiliares ---
def formatar_brl(valor):
    """Formata um valor numérico para o padrão BRL (R$)."""
    try:
        valor = float(valor)
        return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return "R$ 0,00"

@st.cache_data
def carregar_dados(url):
    """Carrega dados da URL da planilha com cache para performance."""
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        df = df.dropna(subset=['Data'])
        return df
    except Exception as e:
        st.error(f"Erro ao carregar os dados da planilha: {e}")
        return pd.DataFrame()

# --- Configurações da Planilha ---
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSQXIC1n_d8Wq5Ck0fsfyKfvTtEBvXtg2b-FMJzWclSHY3QtXkq2kuYMBSUiM3YAEsWp-fP7aK9C_4r/pub?output=csv"
BANCA_INICIAL = 2500

# --- Botão de Atualização de Dados ---
if st.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()

# --- Carregamento e Verificação dos Dados ---
df = carregar_dados(URL_PLANILHA)
if df.empty:
    st.warning("Não foi possível carregar os dados. Verifique a URL da planilha.")
    st.stop()

# --- Normalização de Nomes de Eventos ---
mapeamento_nomes = {
    'flamengo vs internacional': 'Flamengo x Internacional',
    'flamengo x internacional': 'Flamengo x Internacional',
    'bragantino vs botafogo': 'Bragantino x Botafogo',
    'bragantino x botafogo': 'Bragantino x Botafogo',
    'multipla - +2.5 gols na rodada do gdb': 'Múltipla',
    'crb chuta a gol': 'CRB Chuta a Gol'
}

def normalizar_evento(texto):
    if pd.isna(texto):
        return texto
    texto_limpo = str(texto).strip().lower()
    return mapeamento_nomes.get(texto_limpo, texto)

df['Jogador / Evento'] = df['Jogador / Evento'].apply(normalizar_evento)


# --- Processamento e Limpeza dos Dados ---
df = df.dropna(subset=["Status", "Valor apostado (R$)"])
df['Status'] = df['Status'].astype(str).str.strip().str.lower()
df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
df = df.dropna(subset=["Data"])

for col in ['Cotação', 'Valor apostado (R$)']:
    df[col] = pd.to_numeric(
        df[col].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip(),
        errors='coerce'
    )

# Cálculos de Ganho e Lucro/Prejuízo
df['Ganho (R$)'] = df.apply(lambda row:
    row['Valor apostado (R$)'] * row['Cotação'] if row['Status'] == 'green'
    else -row['Valor apostado (R$)'] if row['Status'] == 'red'
    else row['Valor apostado (R$)'] if row['Status'] == 'anulado'
    else 0, axis=1)

df['Lucro/Prejuízo (R$)'] = df.apply(lambda row:
    (row['Valor apostado (R$)'] * row['Cotação']) - row['Valor apostado (R$)'] if row['Status'] == 'green'
    else -row['Valor apostado (R$)'] if row['Status'] == 'red'
    else 0 if row['Status'] == 'anulado'
    else 0, axis=1)

# Filtrando apenas apostas com status válidos (CORREÇÃO)
status_validos = ['green', 'red', 'anulado']
df_finalizadas = df[df['Status'].isin(status_validos)].copy()

# --- Métricas Principais ---
total_apostas = len(df)
lucro_total = df_finalizadas['Lucro/Prejuízo (R$)'].sum()
banca_atual = BANCA_INICIAL + lucro_total
cotacao_media = df_finalizadas['Cotação'].mean()
variacao_banca = banca_atual - BANCA_INICIAL

# --- Layout de Métricas ---
col1, col2, col3, col4, col5 = st.columns(5)

# Métricas com emojis
col1.metric("📅 Total de Apostas", f"{total_apostas}")
col2.metric("💰 Banca Inicial", formatar_brl(BANCA_INICIAL))
col3.metric("📊 Cotação Média", f"{cotacao_media:.2f}")
col4.metric("🏦 Banca Atual", formatar_brl(banca_atual), delta=formatar_brl(variacao_banca))
col5.metric("📈 Lucro/Prejuízo Total", formatar_brl(lucro_total))

# --- Gráfico de Barras de Lucro por Data ---
st.markdown("<h3>💰 Lucro/Prejuízo por Data</h3>", unsafe_allow_html=True)
df_consolidado = df_finalizadas.groupby(df_finalizadas['Data'].dt.date).agg({
    'Lucro/Prejuízo (R$)': 'sum'
}).reset_index()

df_consolidado['Data'] = pd.to_datetime(df_consolidado['Data']).dt.strftime('%d/%m/%Y')

fig_lucro = go.Figure()
fig_lucro.add_trace(go.Bar(
    x=df_consolidado['Data'],
    y=df_consolidado['Lucro/Prejuízo (R$)'],
    marker_color=['green' if x > 0 else 'red' for x in df_consolidado['Lucro/Prejuízo (R$)']],
    text=[formatar_brl(x) for x in df_consolidado['Lucro/Prejuízo (R$)']],
    textposition='auto',
    name='Lucro/Prejuízo',
    width=0.6
))

fig_lucro.update_layout(
    xaxis_title='Data',
    yaxis_title='Valor (R$)',
    height=400,
    plot_bgcolor='#0e1117',
    paper_bgcolor='#0e1117',
    font_color='#f0f0f0',
    xaxis=dict(showgrid=False, type='category'),
    yaxis=dict(showgrid=True, gridcolor='#333333'),
    title=None,
    margin=dict(l=0, r=0, t=0, b=0)
)
st.plotly_chart(fig_lucro, use_container_width=True)

# Expander com estatísticas detalhadas
with st.expander("📊 Estatísticas Detalhadas"):
    total_apostas_finalizadas = len(df_finalizadas)
    total_apostado = df_finalizadas['Valor apostado (R$)'].sum()
    total_ganho = df_finalizadas['Ganho (R$)'].sum()
    greens = (df_finalizadas['Status'] == 'green').sum()
    reds = (df_finalizadas['Status'] == 'red').sum()
    anuladas = (df_finalizadas['Status'] == 'anulado').sum()
    green_pct = greens / total_apostas_finalizadas * 100 if total_apostas_finalizadas > 0 else 0
    red_pct = reds / total_apostas_finalizadas * 100 if total_apostas_finalizadas > 0 else 0
    anulado_pct = anuladas / total_apostas_finalizadas * 100 if total_apostas_finalizadas > 0 else 0
    maior_lucro = df_finalizadas['Lucro/Prejuízo (R$)'].max()
    maior_prejuizo = df_finalizadas['Lucro/Prejuízo (R$)'].min()
    media_lucro = df_finalizadas['Lucro/Prejuízo (R$)'].mean()
    
    st.markdown(f"**🎯 Total de Apostas Finalizadas:** {total_apostas_finalizadas}")
    st.markdown(f"💸 **Total Apostado:** {formatar_brl(total_apostado)}")
    st.markdown(f"💰 **Total Recuperado:** {formatar_brl(total_ganho)}")
    st.markdown(f"📈 **Lucro Total:** {formatar_brl(lucro_total)}")
    st.markdown(f"💰 **Média por Aposta:** {formatar_brl(media_lucro)}")
    st.markdown(f"📈 **Maior Lucro:** {formatar_brl(maior_lucro)}")
    st.markdown(f"📉 **Maior Prejuízo:** {formatar_brl(maior_prejuizo)}")
    st.markdown(f"✅ **Greens:** {greens} ({green_pct:.1f}%)")
    st.markdown(f"❌ **Reds:** {reds} ({red_pct:.1f}%)")
    st.markdown(f"⚪ **Anuladas:** {anuladas} ({anulado_pct:.1f}%)")

    st.markdown("---")
    st.subheader("Análise por Casa de Aposta")
    
    if not df_finalizadas.empty:
        df_casa_analise = df_finalizadas.groupby('Casa de Aposta').agg(
            lucro_total=('Lucro/Prejuízo (R$)', 'sum'),
            total_apostas=('Status', 'count')
        ).sort_values(by='lucro_total', ascending=False)

        casa_mais_lucrativa = df_casa_analise['lucro_total'].idxmax()
        lucro_casa_mais_lucrativa = df_casa_analise['lucro_total'].max()
        st.markdown(f"🏆 **Casa mais lucrativa:** {casa_mais_lucrativa} com lucro de {formatar_brl(lucro_casa_mais_lucrativa)}")
        
        lucro_casa_menos_lucrativa = df_casa_analise['lucro_total'].min()
        if lucro_casa_menos_lucrativa < 0:
            casa_menos_lucrativa = df_casa_analise['lucro_total'].idxmin()
            st.markdown(f"💔 **Casa com maior prejuízo:** {casa_menos_lucrativa} com prejuízo de {formatar_brl(lucro_casa_menos_lucrativa)}")
        
        casa_mais_apostas = df_casa_analise['total_apostas'].idxmax()
        total_apostas_casa = df_casa_analise['total_apostas'].max()
        st.markdown(f"🎰 **Casa com mais apostas:** {casa_mais_apostas} com {total_apostas_casa} apostas")
    else:
        st.info("Adicione apostas para ver a análise por casa de aposta.")

# --- Tabela Detalhada das Apostas ---
st.markdown("<h3>📋 Detalhes das Apostas</h3>", unsafe_allow_html=True)

# Define a ordem das colunas, com a nova coluna 'Ordem' no início
colunas_tabela = ['Ordem', 'Data', 'Jogador / Evento', 'Casa de Aposta', 'Mercado', 'Cotação', 'Valor apostado (R$)', 'Lucro/Prejuízo (R$)', 'Ganho (R$)', 'Status']
df_tabela = df_finalizadas.copy()

# Ordena por data, com a mais recente no topo
df_tabela = df_tabela.sort_values(by='Data', ascending=False)

# Adiciona a coluna de ordem numérica depois da ordenação
df_tabela['Ordem'] = range(len(df_tabela), 0, -1)
df_tabela['Ordem'] = df_tabela['Ordem'].astype(str) + '°'

# Pega as colunas na ordem desejada
df_tabela = df_tabela[colunas_tabela]

# Formata as datas e o status
df_tabela['Data'] = df_tabela['Data'].dt.strftime('%d/%m/%Y')
df_tabela['Status'] = df_tabela['Status'].str.upper()

# Vamos criar o objeto Styler do pandas e aplicar os estilos em cadeia.
styled_df = df_tabela.style

# 1. Aplicar a centralização a todas as células.
styled_df = styled_df.set_properties(**{'text-align': 'center'})

# 2. Aplicar cor e negrito para a coluna 'Status'.
def destacar_status(val):
    if val == 'GREEN':
        return 'color: #00AA00; font-weight: bold;'
    elif val == 'RED':
        return 'color: #FF0000; font-weight: bold;'
    elif val == 'ANULADO':
        return 'color: #999999; font-weight: bold;'
    else:
        return ''

styled_df = styled_df.applymap(destacar_status, subset=['Status'])

# 3. Aplicar cor e negrito para as colunas numéricas (Lucro/Prejuízo e Ganho).
def destacar_valor(val):
    if isinstance(val, (int, float)):
        color = '#00AA00' if val > 0 else '#FF0000' if val < 0 else 'white'
        return f'color: {color}; font-weight: bold;'
    return None

styled_df = styled_df.applymap(destacar_valor, subset=['Lucro/Prejuízo (R$)', 'Ganho (R$)'])

# 4. Finalmente, aplicar a formatação BRL e de números.
styled_df = styled_df.format({
    'Valor apostado (R$)': formatar_brl,
    'Ganho (R$)': formatar_brl,
    'Lucro/Prejuízo (R$)': formatar_brl,
    'Cotação': '{:.2f}'
})

st.dataframe(styled_df, use_container_width=True, hide_index=True)