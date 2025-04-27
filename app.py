import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# Configurações da página
st.set_page_config(page_title="Dashboard de Apostas", page_icon="🎯", layout="wide")

st.title('🎯 Dashboard de Apostas Esportivas')

# Nome do arquivo CSV
nome_arquivo = 'apostas_atualizadas.csv'

# Procura o arquivo no diretório atual
caminho_arquivo = None
for raiz, _, arquivos in os.walk(os.getcwd()):
    if nome_arquivo in arquivos:
        caminho_arquivo = os.path.join(raiz, nome_arquivo)
        break

if caminho_arquivo:
    # Carrega e limpa os dados
    df = pd.read_csv(caminho_arquivo, delimiter=';')
    df.columns = df.columns.str.strip()
    df = df.dropna(subset=["Data"])

    # Converte valores monetários para float
    for col in ['Valor Apostado (R$)', 'Retorno Previsto (R$)', 'Lucro/Prejuízo (R$)']:
        df[col] = (
            df[col].astype(str)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .str.strip()
            .astype(float)
        )

    df['Lucro/Prejuízo (R$)'] = df['Lucro/Prejuízo (R$)'].fillna(0)
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%Y')
    df.index = df.index + 1  # Índice começa em 1

    # Estatísticas
    total_apostado = df['Valor Apostado (R$)'].sum()
    total_retorno = df['Retorno Previsto (R$)'].sum()
    total_lucro = df['Lucro/Prejuízo (R$)'].sum()

    # Métricas (3 colunas)
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Apostado", f"R$ {total_apostado:,.2f}")
    col2.metric("🎯 Retorno Previsto", f"R$ {total_retorno:,.2f}")
    col3.metric("📈 Lucro/Prejuízo", f"R$ {total_lucro:,.2f}", delta=f"R$ {total_lucro:,.2f}")

    st.markdown("---")

    # Gráfico de Lucro por Data (Plotly)
    lucro_por_data = df.groupby('Data')['Lucro/Prejuízo (R$)'].sum().reset_index()
    lucro_por_data['Data'] = pd.to_datetime(lucro_por_data['Data'], format='%d/%m/%Y')
    lucro_por_data['Color'] = lucro_por_data['Lucro/Prejuízo (R$)'].apply(lambda x: 'green' if x > 0 else 'red')
    lucro_por_data['Label'] = lucro_por_data['Lucro/Prejuízo (R$)'].apply(lambda x: f"LUCRADO {x:.2f}" if x > 0 else f"PERDEU {x:.2f}")

    fig_lucro = go.Figure()
    fig_lucro.add_trace(go.Bar(
        x=lucro_por_data['Data'],
        y=lucro_por_data['Lucro/Prejuízo (R$)'],
        marker_color=lucro_por_data['Color'],
        text=lucro_por_data['Label'],
        width=0.1,
        textposition='inside'
    ))

    fig_lucro.update_layout(
        title="Lucro/Prejuízo por Data",
        xaxis_title='Data',
        yaxis_title='Lucro/Prejuízo (R$)',
        xaxis_tickformat='%d/%m/%Y',
        plot_bgcolor='rgb(30, 30, 30)',
        font=dict(color='white')
    )

    st.plotly_chart(fig_lucro, use_container_width=True)
    st.markdown("---")

    # Formatação condicional da tabela (Lucro: verde, Prejuízo: vermelho)
  def color_lucro(val):
    if isinstance(val, str) and val.startswith('R$ '):
        val = float(val.replace('R$ ', '').replace('.', '').replace(',', '.'))
    if isinstance(val, (int, float)):
        if val > 0:
            return 'color: green;'  # Apenas texto verde
        elif val < 0:
            return 'color: red;'    # Apenas texto vermelho
    return ''

# Aplicação (restante do código permanece igual):
styled_df = df_display.style.applymap(color_lucro, subset=['Lucro/Prejuízo (R$)'])
    # Formata os valores para exibição (R$)
    df_display = df.copy()
    for col in ['Valor Apostado (R$)', 'Retorno Previsto (R$)', 'Lucro/Prejuízo (R$)']:
        df_display[col] = df_display[col].apply(lambda x: f"R$ {x:,.2f}")

    # Aplica a formatação condicional
    styled_df = df_display.style.applymap(color_lucro, subset=['Lucro/Prejuízo (R$)'])

    st.subheader("📋 Dados Completos")
    st.dataframe(styled_df, use_container_width=True, height=500)

else:
    st.error(f"Arquivo '{nome_arquivo}' não encontrado.")