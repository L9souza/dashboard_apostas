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

def formatar_brl(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return "R$ 0,00"

@st.cache_data
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT_r9CxtMoWnWEkzzYwHAekTItzRrXjFvirDMNlokjlF82QzA8srPgDADnwRLef8WXh9XtFaIbwjRWE/pub?output=csv"
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return pd.DataFrame()

if st.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()

df = carregar_dados()
df = df.dropna(subset=["Status", "Valor apostado (R$)", "Data"])
df['Status'] = df['Status'].astype(str).str.strip().str.lower()

df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%y', errors='coerce')
df = df.dropna(subset=["Data"])
df['Data'] = df['Data'].dt.strftime('%d/%m/%Y')

for col in ['Cotação', 'Valor apostado (R$)']:
    df[col] = pd.to_numeric(df[col].astype(str)
                            .str.replace('R$', '').str.replace('−', '-')
                            .str.replace('.', '', regex=False)
                            .str.replace(',', '.', regex=False).str.strip(), errors='coerce')

# ✅ AQUI ESTÁ A LÓGICA FINAL
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
col2.metric("💰 Banca Inicial", formatar_brl(BANCA_INICIAL))
col3.metric("📊 Cotação Média", f"{df_finalizadas['Cotação'].mean():.1f}")
col4.metric("🏦 Banca Atual", formatar_brl(banca_atual),
             delta=formatar_brl(variacao_banca),
             delta_color="inverse" if variacao_banca < 0 else "normal")
col5.metric("📈 Lucro/Prejuízo Total", formatar_brl(lucro_total))

fig_lucro = go.Figure()
fig_lucro.add_trace(go.Bar(
    x=df_consolidado['Data'],
    y=df_consolidado['Lucro/Prejuízo (R$)'],
    marker_color=['green' if x > 0 else 'red' for x in df_consolidado['Lucro/Prejuízo (R$)']],
    text=[formatar_brl(x) for x in df_consolidado['Lucro/Prejuízo (R$)']],
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
    st.markdown(f"💸 **Total Apostado:** {formatar_brl(total_apostado)}")
    st.markdown(f"💰 **Total Recuperado:** {formatar_brl(total_ganho)}")
    st.markdown(f"📈 **Lucro Total:** {formatar_brl(lucro_total)}")
    st.markdown(f"💰 **Média por Aposta:** {formatar_brl(media_lucro)}")
    st.markdown(f"📈 **Maior Lucro:** {formatar_brl(maior_lucro)}")
    st.markdown(f"📉 **Maior Prejuízo:** {formatar_brl(maior_prejuizo)}")
    st.markdown(f"✅ **Greens:** {greens} ({green_pct:.1f}%)")
    st.markdown(f"❌ **Reds:** {reds} ({red_pct:.1f}%)")
    st.markdown(f"⚪ **Anuladas:** {anuladas} ({anulado_pct:.1f}%)")

df_display = df.copy().iloc[::-1].reset_index(drop=True)
df_display['Status'] = df_display['Status'].str.upper()

def estilo_linha(row):
    estilo = []
    for col in df_display.columns:
        if col == 'Status':
            status = row['Status']
            if status == "GREEN":
                estilo.append('color: #00AA00; font-weight: bold; text-transform: uppercase;')
            elif status == "RED":
                estilo.append('color: #FF0000; font-weight: bold; text-transform: uppercase;')
            elif status == "ANULADO":
                estilo.append('color: #999999; font-weight: bold; text-transform: uppercase;')
            else:
                estilo.append('')
        elif col == 'Lucro/Prejuízo (R$)' or col == 'Ganho (R$)':
            valor = row[col]
            if valor > 0:
                estilo.append('color: #00AA00; font-weight: bold;')
            elif valor < 0:
                estilo.append('color: #FF0000; font-weight: bold;')
            else:
                estilo.append('color: white;')
        else:
            estilo.append('')
    return estilo

styled_df = df_display.style.format({
    'Valor apostado (R$)': formatar_brl,
    'Ganho (R$)': formatar_brl,
    'Lucro/Prejuízo (R$)': formatar_brl,
    'Cotação': '{:.2f}'
}).apply(estilo_linha, axis=1)

st.dataframe(styled_df, use_container_width=True, hide_index=True, height=500)
