import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Configurações iniciais
st.set_page_config(
    page_title="Dashboard de Apostas", 
    page_icon="🎯", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Estilos CSS customizados
st.markdown("""
    <style>
    thead tr th:first-child {display:none}
    tbody th {display:none}
    .stDataFrame {font-size: 14px;}
    .metric {text-align: center;}
    .stMetricValue {font-size: 18px !important;}
    .stMetricLabel {font-size: 14px !important;}
    .negative-value {color: #FF0000 !important; font-weight: bold;}
    .positive-value {color: #00AA00 !important; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

st.title('🎯 Dashboard de Apostas Esportivas')

# Constantes
BANCA_INICIAL = 1250
STATUS_VALIDOS = ['green', 'red', 'anulado']

# Funções auxiliares
def formatar_brl(valor):
    """Formata valores monetários em BRL"""
    try:
        valor = float(valor)
        return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return "R$ 0,00"

def limpar_valor_monetario(valor):
    """Limpa e converte strings monetárias para float"""
    if pd.isna(valor):
        return 0.0
    try:
        return float(str(valor).replace('R$', '').replace('−', '-')
                     .replace('.', '').replace(',', '.').strip())
    except:
        return 0.0

@st.cache_data(ttl=300)  # Cache por 5 minutos
def carregar_dados():
    """Carrega os dados da planilha Google Sheets"""
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT_r9CxtMoWnWEkzzYwHAekTItzRrXjFvirDMNlokjlF82QzA8srPgDADnwRLef8WXh9XtFaIbwjRWE/pub?output=csv"
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        
        # Limpeza e conversão de dados
        df = df.dropna(subset=["Status", "Valor apostado (R$)", "Data"], how='any')
        df['Status'] = df['Status'].astype(str).str.strip().str.lower()
        
        # Conversão de datas
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%y', errors='coerce')
        df = df.dropna(subset=["Data"])
        df['Data'] = df['Data'].dt.strftime('%d/%m/%Y')
        
        # Limpeza de valores monetários
        for col in ['Cotação', 'Valor apostado (R$)']:
            df[col] = df[col].apply(limpar_valor_monetario)
        
        # Cálculo de ganhos e lucro - CORREÇÃO APLICADA AQUI
        df['Ganho (R$)'] = df.apply(
            lambda row: row['Valor apostado (R$)'] * row['Cotação'] if row['Status'] == 'green'
            else row['Valor apostado (R$)'] if row['Status'] == 'anulado'
            else 0,  # RED tem ganho zero
            axis=1
        )
        
        df['Lucro/Prejuízo (R$)'] = df['Ganho (R$)'] - df['Valor apostado (R$)']
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return pd.DataFrame()

# Interface
if st.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()

# Carregar e processar dados
df = carregar_dados()
if df.empty:
    st.warning("Nenhum dado disponível para exibição.")
    st.stop()

df_finalizadas = df[df['Status'].isin(STATUS_VALIDOS)].copy()

# Cálculos consolidados
df_consolidado = df_finalizadas.groupby('Data').agg({
    'Valor apostado (R$)': 'sum',
    'Ganho (R$)': 'sum',
    'Lucro/Prejuízo (R$)': 'sum'
}).reset_index().sort_values('Data')

df_consolidado['Lucro Acumulado'] = df_consolidado['Lucro/Prejuízo (R$)'].cumsum()

# Métricas principais
lucro_total = df_finalizadas['Lucro/Prejuízo (R$)'].sum()
banca_atual = BANCA_INICIAL + lucro_total
variacao_banca = banca_atual - BANCA_INICIAL

# Layout de métricas
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("📅 Total de Apostas", f"{len(df)}")
col2.metric("💰 Banca Inicial", formatar_brl(BANCA_INICIAL))
col3.metric("📊 Cotação Média", f"{df_finalizadas['Cotação'].mean():.1f}")
col4.metric("🏦 Banca Atual", formatar_brl(banca_atual),
           delta=formatar_brl(variacao_banca),
           delta_color="inverse" if variacao_banca < 0 else "normal")
col5.metric("📈 Lucro/Prejuízo Total", formatar_brl(lucro_total))

# Gráfico de lucro por data
fig_lucro = go.Figure()
fig_lucro.add_trace(go.Bar(
    x=df_consolidado['Data'],
    y=df_consolidado['Lucro/Prejuízo (R$)'],
    marker_color=['green' if x > 0 else 'red' for x in df_consolidado['Lucro/Prejuízo (R$)']],
    text=[formatar_brl(x) for x in df_consolidado['Lucro/Prejuízo (R$)']],
    textposition='inside',
    width=0.6,
    name="Lucro/Prejuízo"
))

fig_lucro.add_trace(go.Scatter(
    x=df_consolidado['Data'],
    y=df_consolidado['Lucro Acumulado'],
    mode='lines+markers',
    name='Lucro Acumulado',
    line=dict(color='gold', width=2),
    yaxis='y2'
))

fig_lucro.update_layout(
    title="Lucro/Prejuízo por Data e Lucro Acumulado",
    xaxis_title='Data',
    yaxis_title='Valor (R$)',
    yaxis2=dict(
        title='Lucro Acumulado (R$)',
        overlaying='y',
        side='right'
    ),
    height=500,
    plot_bgcolor='rgba(0,0,0,0)',
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig_lucro, use_container_width=True)

# Estatísticas detalhadas
with st.expander("📊 Estatísticas Detalhadas", expanded=False):
    total_apostas = len(df_finalizadas)
    total_apostado = df_finalizadas['Valor apostado (R$)'].sum()
    total_ganho = df_finalizadas['Ganho (R$)'].sum()
    
    greens = (df_finalizadas['Status'] == 'green').sum()
    reds = (df_finalizadas['Status'] == 'red').sum()
    anuladas = (df_finalizadas['Status'] == 'anulado').sum()
    
    green_pct = greens / total_apostas * 100 if total_apostas > 0 else 0
    red_pct = reds / total_apostas * 100 if total_apostas > 0 else 0
    anulado_pct = anuladas / total_apostas * 100 if total_apostas > 0 else 0
    
    maior_lucro = df_finalizadas['Lucro/Prejuízo (R$)'].max()
    maior_prejuizo = df_finalizadas['Lucro/Prejuízo (R$)'].min()
    media_lucro = df_finalizadas['Lucro/Prejuízo (R$)'].mean()
    
    cols = st.columns(3)
    with cols[0]:
        st.metric("🎯 Total de Apostas Finalizadas", total_apostas)
        st.metric("💸 Total Apostado", formatar_brl(total_apostado))
        st.metric("💰 Total Recuperado", formatar_brl(total_ganho))
    
    with cols[1]:
        st.metric("📈 Lucro Total", formatar_brl(lucro_total))
        st.metric("📊 Média por Aposta", formatar_brl(media_lucro))
        st.metric("📉 ROI (%)", f"{(lucro_total / total_apostado * 100):.1f}%" if total_apostado > 0 else "0%")
    
    with cols[2]:
        st.metric("✅ Greens", f"{greens} ({green_pct:.1f}%)")
        st.metric("❌ Reds", f"{reds} ({red_pct:.1f}%)")
        st.metric("⚪ Anuladas", f"{anuladas} ({anulado_pct:.1f}%)")

# Tabela de apostas - CORREÇÃO APLICADA AQUI
colunas_ordenadas = ['Data', 'Valor apostado (R$)', 'Cotação', 'Status', 'Ganho (R$)', 'Lucro/Prejuízo (R$)']
df_display = df[colunas_ordenadas].copy().iloc[::-1].reset_index(drop=True)

def colorir_status(val):
    """Aplica estilo condicional ao status"""
    val = str(val).strip().lower()
    if val == "green":
        return 'background-color: #e6f7e6; color: #006400; font-weight: bold;'
    elif val == "red":
        return 'background-color: #ffebeb; color: #8B0000; font-weight: bold;'
    elif val == "anulado":
        return 'background-color: #f0f0f0; color: #666666;'
    return ''

# Aplicar estilos à tabela
styled_df = df_display.style.format({
    'Valor apostado (R$)': formatar_brl,
    'Ganho (R$)': formatar_brl,
    'Lucro/Prejuízo (R$)': formatar_brl,
    'Cotação': "{:.2f}"
}).applymap(lambda x: 'color: #00AA00; font-weight: bold;' if isinstance(x, (int, float)) and x > 0 else '', 
            subset=['Lucro/Prejuízo (R$)']).applymap(lambda x: 'color: #FF0000; font-weight: bold;' if isinstance(x, (int, float)) and x < 0 else '', 
            subset=['Lucro/Prejuízo (R$)']).applymap(colorir_status, subset=['Status'])

# Exibir tabela
st.dataframe(
    styled_df,
    use_container_width=True,
    hide_index=True,
    height=600,
    column_config={
        "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
        "Cotação": st.column_config.NumberColumn("Cotação", format="%.2f")
    }
)

# Rodapé
st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")