import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- Configurações Iniciais da Página ---
st.set_page_config(
    page_title="Dashboard de Apostas Esportivas",
    page_icon="🎯",
    layout="wide"
)

# --- Título do Dashboard ---
st.title("🎯 Dashboard de Apostas Esportivas")

# --- Configurações da Planilha ---
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1XLXwejqJ-L1J-yHKbDU4mhV6jYHbmt34_p13QWlGLSQ/export?format=csv"
BANCA_INICIAL = 3000

# --- Funções Auxiliares ---
def formatar_brl(valor):
    """Formata um valor numérico para o padrão BRL (R$)."""
    try:
        valor = float(valor)
        return (
            f"R$ {valor:,.2f}"
            .replace(',', 'X')
            .replace('.', ',')
            .replace('X', '.')
        )
    except (ValueError, TypeError):
        return "R$ 0,00"


# Mapeamento para normalizar nomes de eventos
mapeamento_nomes = {
    'flamengo vs internacional': 'Flamengo x Internacional',
    'flamengo x internacional': 'Flamengo x Internacional',
    'bragantino vs botafogo': 'Bragantino x Botafogo',
    'bragantino x botafogo': 'Bragantino x Botafogo',
    'multipla - +2.5 gols na rodada do gdb': 'Múltipla',
    'crb chuta a gol': 'CRB Chuta a Gol'
}

@st.cache_data
def carregar_dados(url):
    """Carrega dados da URL da planilha com cache para performance e trata anuladas sem cotação."""
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()

        # Status em minúsculas e sem espaços
        df['Status'] = df['Status'].astype(str).str.strip().str.lower()

        # Apostas anuladas sem cotação: definir como 1,00 (retorna apenas o valor apostado)
        df.loc[(df['Status'] == 'anulado') & (df['Cotação'].isna()), 'Cotação'] = '1,00'

        # Data
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')

        # Conversão de colunas numéricas
        cols_numericas = ['Cotação', 'Valor apostado (R$)']
        for col in cols_numericas:
            df[col] = pd.to_numeric(
                df[col].astype(str)
                      .str.replace('R$', '', regex=False)
                      .str.replace('.', '', regex=False)
                      .str.replace(',', '.', regex=False)
                      .str.strip(),
                errors='coerce'
            )

        # Normalização de texto
        df['Jogador / Evento'] = (
            df['Jogador / Evento']
            .astype(str)
            .str.strip()
            .str.lower()
            .map(lambda x: mapeamento_nomes.get(x, x))
        )
        df['Casa de Aposta'] = df['Casa de Aposta'].astype(str).str.strip()

        # Remove linhas sem Data ou sem valor apostado
        df = df.dropna(subset=['Data', "Valor apostado (R$)"])

        return df
    except Exception as e:
        st.error(f"Erro ao carregar os dados da planilha: {e}")
        return pd.DataFrame()

# --- Botão de Atualização de Dados ---
if st.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()

# --- Carregamento e Verificação dos Dados ---
df = carregar_dados(URL_PLANILHA)
if df.empty:
    st.warning("Não foi possível carregar os dados. Verifique a URL da planilha e a permissão de acesso.")
    st.stop()

# ----------------------------------------------------------------------
#                   CÁLCULOS CORRIGIDOS DE APOSTAS
# ----------------------------------------------------------------------

# Considera apenas apostas finalizadas
status_validos = ['green', 'red', 'anulado']
df_finalizadas = df[df['Status'].isin(status_validos)].copy()

# 1) Ganho (R$) = RESULTADO LÍQUIDO DA APOSTA
# GREEN  -> lucro positivo
# RED    -> valor apostado negativo
# ANULA  -> 0
df_finalizadas['Ganho (R$)'] = np.select(
    [
        df_finalizadas['Status'] == 'green',
        df_finalizadas['Status'] == 'red',
        df_finalizadas['Status'] == 'anulado'
    ],
    [
        df_finalizadas['Valor apostado (R$)'] * (df_finalizadas['Cotação'] - 1),  # green
        -df_finalizadas['Valor apostado (R$)'],                                   # red
        0                                                                         # anulado
    ],
    default=0
)

# Mantém Lucro/Prejuízo como mesmo valor (poderia até remover, mas deixei para usar em cálculos)
df_finalizadas['Lucro/Prejuízo (R$)'] = df_finalizadas['Ganho (R$)']

# ----------------------------------------------------------------------
#                              FILTROS
# ----------------------------------------------------------------------
df_filtrado = df_finalizadas.copy()

with st.sidebar:
    st.header("🎛 Filtros")

    if not df_filtrado.empty:
        # Filtro de período
        min_data = df_filtrado['Data'].min().date()
        max_data = df_filtrado['Data'].max().date()

        periodo = st.date_input(
            "Período",
            value=(min_data, max_data),
            min_value=min_data,
            max_value=max_data
        )

        if isinstance(periodo, tuple) and len(periodo) == 2:
            data_ini, data_fim = periodo
            df_filtrado = df_filtrado[
                (df_filtrado['Data'] >= pd.to_datetime(data_ini)) &
                (df_filtrado['Data'] <= pd.to_datetime(data_fim))
            ]

        # Filtro por casa de aposta
        casas_unicas = sorted(df_finalizadas['Casa de Aposta'].unique())
        casas_sel = st.multiselect(
            "Casa de Aposta",
            options=casas_unicas,
            default=casas_unicas
        )
        df_filtrado = df_filtrado[df_filtrado['Casa de Aposta'].isin(casas_sel)]

        # Filtro por status
        status_unicos = ['green', 'red', 'anulado']
        status_sel = st.multiselect(
            "Status",
            options=status_unicos,
            default=status_unicos,
            format_func=lambda x: x.upper()
        )
        df_filtrado = df_filtrado[df_filtrado['Status'].isin(status_sel)]

# ----------------------------------------------------------------------
#                       MÉTRICAS PRINCIPAIS
# ----------------------------------------------------------------------
if df_filtrado.empty:
    total_apostas = 0
    lucro_total = 0
    banca_atual = BANCA_INICIAL
    cotacao_media = np.nan
    total_apostado = 0
    roi = 0
    winrate = 0
else:
    total_apostas = len(df_filtrado)
    lucro_total = df_filtrado['Lucro/Prejuízo (R$)'].sum()
    banca_atual = BANCA_INICIAL + lucro_total
    cotacao_media = df_filtrado['Cotação'].mean()
    total_apostado = df_filtrado['Valor apostado (R$)'].sum()

    greens = (df_filtrado['Status'] == 'green').sum()
    roi = (lucro_total / total_apostado * 100) if total_apostado > 0 else 0
    winrate = (greens / total_apostas * 100) if total_apostas > 0 else 0

variacao_banca = banca_atual - BANCA_INICIAL
delta_banca = round(variacao_banca, 2)  # deixa o delta "inteiro", sem aquele monte de casa decimal

st.markdown("---")
col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("📅 Total de Apostas", f"{total_apostas}")
col2.metric("💰 Banca Inicial", formatar_brl(BANCA_INICIAL))
col3.metric("📊 Cotação Média", f"{cotacao_media:.2f}" if not np.isnan(cotacao_media) else "-")
delta_text = f"🔻 R$ {variacao_banca:,.2f}" if variacao_banca < 0 else f"🔺 R$ {variacao_banca:,.2f}"

col4.metric(
    "🏦 Banca Atual",
    formatar_brl(banca_atual),
    delta_text,
    delta_color="inverse"
)

col5.metric("📈 Lucro/Prejuízo Total", formatar_brl(lucro_total))
col6.metric("🎯 ROI", f"{roi:.1f}%")
st.markdown("---")

# ----------------------------------------------------------------------
#              GRÁFICO DE LUCRO / PREJUÍZO POR DATA
# ----------------------------------------------------------------------
st.markdown("<h3>💰 Lucro/Prejuízo por Data</h3>", unsafe_allow_html=True)

if not df_filtrado.empty:
    df_consolidado = df_filtrado.groupby(df_filtrado['Data'].dt.date).agg({
        'Lucro/Prejuízo (R$)': 'sum'
    }).reset_index()

    df_consolidado['Data'] = pd.to_datetime(df_consolidado['Data']).dt.strftime('%d/%m/%Y')

    fig_lucro = go.Figure()
    fig_lucro.add_trace(go.Bar(
        x=df_consolidado['Data'],
        y=df_consolidado['Lucro/Prejuízo (R$)'],
        marker_color=['#00AA00' if x > 0 else '#FF0000' for x in df_consolidado['Lucro/Prejuízo (R$)']],
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
else:
    st.info("Ainda não há apostas (com filtros atuais) para montar o gráfico de lucro por data.")

# ----------------------------------------------------------------------
#                    ESTATÍSTICAS DETALHADAS
# ----------------------------------------------------------------------
with st.expander("📊 Estatísticas Detalhadas"):
    total_apostas_finalizadas = len(df_filtrado)
    total_apostado_f = df_filtrado['Valor apostado (R$)'].sum()
    total_ganho_f = df_filtrado['Ganho (R$)'].sum()

    greens_f = (df_filtrado['Status'] == 'green').sum()
    reds_f = (df_filtrado['Status'] == 'red').sum()
    anuladas_f = (df_filtrado['Status'] == 'anulado').sum()

    green_pct_f = greens_f / total_apostas_finalizadas * 100 if total_apostas_finalizadas > 0 else 0
    red_pct_f = reds_f / total_apostas_finalizadas * 100 if total_apostas_finalizadas > 0 else 0
    anulado_pct_f = anuladas_f / total_apostas_finalizadas * 100 if total_apostas_finalizadas > 0 else 0

    maior_lucro_f = df_filtrado['Lucro/Prejuízo (R$)'].max() if not df_filtrado.empty else 0
    maior_prejuizo_f = df_filtrado['Lucro/Prejuízo (R$)'].min() if not df_filtrado.empty else 0
    media_lucro_f = df_filtrado['Lucro/Prejuízo (R$)'].mean() if not df_filtrado.empty else 0

    st.markdown(f"**🎯 Total de Apostas (filtradas):** **{total_apostas_finalizadas}**")
    st.markdown(f"💸 **Total Apostado:** {formatar_brl(total_apostado_f)}")
    st.markdown(f"💰 **Resultado Total (Ganho Líquido):** {formatar_brl(total_ganho_f)}")
    st.markdown(f"📈 **Lucro Total:** {formatar_brl(lucro_total)}")
    st.markdown(f"💰 **Média de Lucro/Prejuízo por Aposta:** {formatar_brl(media_lucro_f)}")
    st.markdown(f"📈 **Maior Lucro Individual:** {formatar_brl(maior_lucro_f)}")
    st.markdown(f"📉 **Maior Prejuízo Individual:** {formatar_brl(maior_prejuizo_f)}")
    st.markdown(f"🎯 **ROI Total:** {roi:.1f}%")
    st.markdown(f"🎯 **Taxa de Acerto (Winrate):** {winrate:.1f}%")
    st.markdown(f"✅ **Greens:** **{greens_f}** ({green_pct_f:.1f}%)")
    st.markdown(f"❌ **Reds:** **{reds_f}** ({red_pct_f:.1f}%)")
    st.markdown(f"⚪ **Anuladas:** **{anuladas_f}** ({anulado_pct_f:.1f}%)")

    st.markdown("---")
    st.subheader("Análise por Casa de Aposta (filtradas)")

    if not df_filtrado.empty:
        df_casa_analise = df_filtrado.groupby('Casa de Aposta').agg(
            lucro_total=('Lucro/Prejuízo (R$)', 'sum'),
            total_apostas=('Status', 'count')
        ).sort_values(by='lucro_total', ascending=False)

        casa_mais_lucrativa = df_casa_analise['lucro_total'].idxmax()
        lucro_casa_mais_lucrativa = df_casa_analise['lucro_total'].max()
        st.markdown(f"🏆 **Casa mais lucrativa:** **{casa_mais_lucrativa}** com lucro de **{formatar_brl(lucro_casa_mais_lucrativa)}**")

        lucro_casa_menos_lucrativa = df_casa_analise['lucro_total'].min()
        if lucro_casa_menos_lucrativa < 0:
            casa_menos_lucrativa = df_casa_analise['lucro_total'].idxmin()
            st.markdown(f"💔 **Casa com maior prejuízo:** **{casa_menos_lucrativa}** com prejuízo de **{formatar_brl(lucro_casa_menos_lucrativa)}**")

        casa_mais_apostas = df_casa_analise['total_apostas'].idxmax()
        total_apostas_casa = df_casa_analise['total_apostas'].max()
        st.markdown(f"🎰 **Casa com mais apostas:** **{casa_mais_apostas}** com **{total_apostas_casa}** apostas")
    else:
        st.info("Adicione apostas ou ajuste os filtros para ver a análise por casa de aposta.")

# ----------------------------------------------------------------------
#                    TABELA DETALHADA DAS APOSTAS
# ----------------------------------------------------------------------
st.markdown("<h3>📋 Detalhes das Apostas</h3>", unsafe_allow_html=True)

colunas_tabela = [
    'Ordem', 'Data', 'Jogador / Evento', 'Casa de Aposta', 'Mercado',
    'Cotação', 'Valor apostado (R$)', 'Ganho (R$)', 'Status'
]

df_tabela = df_filtrado.copy()

if not df_tabela.empty:
    # Ordenação e coluna Ordem
    df_tabela = df_tabela.sort_values(by='Data', ascending=False)
    df_tabela['Ordem'] = range(len(df_tabela), 0, -1)
    df_tabela['Ordem'] = df_tabela['Ordem'].astype(str) + '°'

    # Seleciona colunas
    df_tabela = df_tabela[colunas_tabela]

    # Formata Data e Status
    df_tabela['Data'] = df_tabela['Data'].dt.strftime('%d/%m/%Y')
    df_tabela['Status'] = df_tabela['Status'].str.upper()

    # --- Estilização ---
    def destacar_status(val):
        if val == 'GREEN':
            return 'color: #00AA00; font-weight: bold;'
        elif val == 'RED':
            return 'color: #FF0000; font-weight: bold;'
        elif val == 'ANULADO':
            return 'color: #999999; font-weight: bold;'
        else:
            return None

    def destacar_valor(val):
        if isinstance(val, (int, float)):
            if val > 0:
                color = '#00AA00'
            elif val < 0:
                color = '#FF0000'
            else:
                color = 'white'
            return f'color: {color}; font-weight: bold;'
        return None

    styled_df = df_tabela.style.set_properties(**{'text-align': 'center'})
    styled_df = styled_df.map(destacar_status, subset=['Status'])
    styled_df = styled_df.map(destacar_valor, subset=['Ganho (R$)'])

    styled_df = styled_df.format({
        'Valor apostado (R$)': formatar_brl,
        'Ganho (R$)': formatar_brl,
        'Cotação': '{:.2f}'
    })

    st.dataframe(styled_df, use_container_width=True, hide_index=True)
else:
    st.info("Ainda não há apostas (com os filtros atuais) para exibir na tabela.")
