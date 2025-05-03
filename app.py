
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Dashboard de Apostas", page_icon="🎯", layout="wide", initial_sidebar_state="collapsed")

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
df = df.dropna(subset=["Status", "Valor apostado (R$)", "Data"], how='any')
df['Status'] = df['Status'].astype(str).str.strip().str.lower()

df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%y', errors='coerce')
df = df.dropna(subset=["Data"])
df['Data'] = df['Data'].dt.strftime('%d/%m/%Y')

for col in ['Cotação', 'Valor apostado (R$)']:
    df[col] = pd.to_numeric(df[col].astype(str)
                            .str.replace('R$', '').str.replace('−', '-')
                            .str.replace('.', '', regex=False)
                            .str.replace(',', '.', regex=False).str.strip(), errors='coerce')

df['Ganho (R$)'] = df.apply(lambda row:
    row['Valor apostado (R$)'] * row['Cotação'] if row['Status'] == 'green'
    else row['Valor apostado (R$)'] if row['Status'] == 'anulado'
    else 0, axis=1)
df['Lucro/Prejuízo (R$)'] = df['Ganho (R$)'] - df['Valor apostado (R$)']

status_validos = ['green', 'red', 'anulado']
df_finalizadas = df[df['Status'].isin(status_validos)].copy()

df_consolidado = df_finalizadas.groupby('Data').agg({
    'Valor apostado (R$)': 'sum',
    'Ganho (R$)': 'sum',
    'Lucro/Prejuízo (R$)': 'sum'
}).reset_index().sort_values('Data')
df_consolidado['Lucro Acumulado'] = df_consolidado['Lucro/Prejuízo (R$)'].cumsum()

BANCA_INICIAL = 1250
lucro_total = df_finalizadas['Lucro/Prejuízo (R$)'].sum()
banca_atual = BANCA_INICIAL + lucro_total
variacao_banca = banca_atual - BANCA_INICIAL

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("📅 Total de Apostas", f"{len(df)}")
col2.metric("💰 Banca Inicial", f"R$ {BANCA_INICIAL:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
col3.metric("📊 Cotação Média", f"{df_finalizadas['Cotação'].mean():.1f}")
col4.metric("🏦 Banca Atual", f"R$ {banca_atual:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
             delta=f"R$ {variacao_banca:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
             delta_color="inverse" if variacao_banca < 0 else "normal")
col5.metric("📈 Lucro/Prejuízo Total", f"R$ {lucro_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

fig_lucro = go.Figure()
fig_lucro.add_trace(go.Bar(
    x=df_consolidado['Data'],
    y=df_consolidado['Lucro/Prejuízo (R$)'],
    marker_color=['green' if x > 0 else 'red' for x in df_consolidado['Lucro/Prejuízo (R$)']],
    text=[f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') for x in df_consolidado['Lucro/Prejuízo (R$)']],
    textposition='inside',
    width=0.6
))
fig_lucro.update_layout(title="Lucro/Prejuízo por Data", xaxis_title='Data', yaxis_title='Valor (R$)',
                        height=500, plot_bgcolor='rgba(0,0,0,0)', hovermode="x unified")
st.plotly_chart(fig_lucro, use_container_width=True)

with st.expander("📊 Estatísticas Detalhadas"):
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
    st.markdown(f"**🎯 Total de Apostas Finalizadas:** {total_apostas}")
    st.markdown(f"💸 **Total Apostado:** R$ {total_apostado:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    st.markdown(f"💰 **Total Recuperado:** R$ {total_ganho:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    st.markdown(f"📈 **Lucro Total:** R$ {lucro_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    st.markdown(f"💰 **Média por Aposta:** R$ {media_lucro:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    st.markdown(f"📈 **Maior Lucro:** R$ {maior_lucro:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    st.markdown(f"📉 **Maior Prejuízo:** R$ {maior_prejuizo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    st.markdown(f"✅ **Greens:** {greens} ({green_pct:.1f}%)")
    st.markdown(f"❌ **Reds:** {reds} ({red_pct:.1f}%)")
    st.markdown(f"⚪ **Anuladas:** {anuladas} ({anulado_pct:.1f}%)")

df_display = df.copy()
df_display = df_display.iloc[::-1].reset_index(drop=True)

for col in ['Valor apostado (R$)', 'Ganho (R$)', 'Lucro/Prejuízo (R$)']:
    df_display[col + '_orig'] = df_display[col]
    df_display[col] = df_display[col].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

if 'Cotação' in df_display.columns:
    df_display['Cotação'] = df_display['Cotação'].apply(lambda x: f"{x:.2f}")

def colorir_numerico(val):
    if val > 0:
        return 'color: #00AA00; font-weight: bold;'
    elif val < 0:
        return 'color: #FF0000; font-weight: bold;'
    return 'color: white; font-weight: normal;'

def colorir_status(val):
    if val == "green":
        return 'color: #00AA00; font-weight: bold;'
    elif val == "red":
        return 'color: #FF0000; font-weight: bold;'
    return 'color: white; font-weight: normal;'

styled_df = df_display.style
styled_df = styled_df.applymap(colorir_numerico, subset=['Lucro/Prejuízo (R$)_orig', 'Ganho (R$)_orig'])
styled_df = styled_df.applymap(colorir_status, subset=['Status'])

colunas_visuais = [col for col in df_display.columns if not col.endswith('_orig')]
st.dataframe(styled_df[colunas_visuais], use_container_width=True, hide_index=True, height=450)
