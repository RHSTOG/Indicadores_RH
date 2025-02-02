import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import plotly.express as px
import json
import requests

# Configuração inicial do aplicativo
st.set_page_config(
    page_title="Indicadores RH",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.header("👥 Painel de Gestão de Pessoal da STOG")
st.markdown("""
    Aqui você encontra os principais indicadores sobre o fluxo de colaboradores, perfis demográficos e o índice de turnover. Use essas informações para tomar decisões estratégicas sobre planejamento de equipe e engajamento.

""")

# Função para leitura da base de dados
def carregar_base_dados(uploaded_file):
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file, sheet_name='BD')
        return df
    return None

def calcular_indicadores_turnover(df):
    st.header("🔄 Indicadores de Rotatividade e Turnover")

    # Supondo que a base tenha colunas 'Contratado', 'Desligado', 'Sexo' e 'Função'
    df['Contratado'] = pd.to_datetime(df['Contratado'], errors='coerce')
    df['Desligado'] = pd.to_datetime(df['Desligado'], errors='coerce')

    # Filtro por gênero (incluir opção 'Todos')
    generos_disponiveis = ["Todos"] + df['Sexo'].unique().tolist()
    genero_selecionado = st.selectbox("Selecione o gênero:", options=generos_disponiveis)

    # Aplicar o filtro de gênero
    if genero_selecionado != "Todos":
        df_filtrado = df[df['Sexo'] == genero_selecionado]
    else:
        df_filtrado = df  # Se 'Todos' for selecionado, usa a base completa

    # Filtro por função (cargo)
    funcoes_disponiveis = ["Todos"] + df['Função'].unique().tolist()
    funcao_selecionada = st.selectbox("Selecione a função:", options=funcoes_disponiveis)

    # Aplicar o filtro de função
    if funcao_selecionada != "Todos":
        df_filtrado = df_filtrado[df_filtrado['Função'] == funcao_selecionada]

    # Opções de filtro por ano
    anos_disponiveis = sorted(list(set(df_filtrado['Contratado'].dt.year.dropna().astype(int)) | 
                                  set(df_filtrado['Desligado'].dt.year.dropna().astype(int))))
    ano_selecionado = st.selectbox("Selecione o ano para análise:", options=anos_disponiveis, index=len(anos_disponiveis) - 1)

    # Filtrar entradas e saídas no ano selecionado
    entradas_ano = df_filtrado[df_filtrado['Contratado'].dt.year == ano_selecionado]
    saidas_ano = df_filtrado[df_filtrado['Desligado'].dt.year == ano_selecionado]

    total_entradas = len(entradas_ano)
    total_saidas = len(saidas_ano)

    # Calcular colaboradores ativos no período
    colaboradores_ativos_inicio = df_filtrado[(df_filtrado['Contratado'] <= f'{ano_selecionado}-01-01') & 
                                              ((df_filtrado['Desligado'].isna()) | (df_filtrado['Desligado'] >= f'{ano_selecionado}-01-01'))]
    colaboradores_ativos_fim = df_filtrado[(df_filtrado['Contratado'] <= f'{ano_selecionado}-12-31') & 
                                           ((df_filtrado['Desligado'].isna()) | (df_filtrado['Desligado'] >= f'{ano_selecionado}-12-31'))]

    # Média de colaboradores no ano
    total_colaboradores_medio = (len(colaboradores_ativos_inicio) + len(colaboradores_ativos_fim)) / 2

    # Cálculo do turnover atual
    turnover_atual = ((total_entradas + total_saidas) / 2) / total_colaboradores_medio * 100

    # Mostrar o Card de Destaque com o índice de turnover atual
    st.metric(
        label=f"🔍 Índice de Turnover Atual ({genero_selecionado}, {funcao_selecionada})",
        value=f"{turnover_atual:.2f}%"
    )

    # Mostrar indicadores gerais
    st.subheader("📊 Estatísticas Gerais")
    st.write(f"**Ano Selecionado:** {ano_selecionado}")
    st.write(f"**Gênero Selecionado:** {genero_selecionado}")
    st.write(f"**Função Selecionada:** {funcao_selecionada}")
    st.write(f"**Entradas de colaboradores:** {total_entradas}")
    st.write(f"**Saídas de colaboradores:** {total_saidas}")
    st.write(f"**Total médio de colaboradores:** {total_colaboradores_medio:.2f}")

    # Gráficos de rotatividade
    st.subheader("📈 Gráficos de Rotatividade")
    def plot_bar_chart(labels, values, title, color):
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(labels, values, color=color)
        ax.set_ylabel('Quantidade')
        ax.set_title(title)
        st.pyplot(fig)

    # Gráfico 1: Entradas e saídas de colaboradores
    plot_bar_chart(
        labels=['Entradas', 'Saídas'],
        values=[total_entradas, total_saidas],
        title=f'Entradas e Saídas de Colaboradores ({ano_selecionado} - {genero_selecionado}, {funcao_selecionada})',
        color=['#2E8B57', '#FF6347']
    )

    # Se "Todos" for selecionado no filtro de gênero, mostrar comparação por gênero
    if genero_selecionado == "Todos":
        turnover_quantidades = {"Masculino": {"Entradas": 0, "Saídas": 0}, "Feminino": {"Entradas": 0, "Saídas": 0}}

        for genero in ["Masculino", "Feminino"]:
            df_genero = df[df['Sexo'] == genero]

            # Aplicar o filtro de função
            if funcao_selecionada != "Todos":
                df_genero = df_genero[df_genero['Função'] == funcao_selecionada]

            # Filtrar entradas e saídas no ano selecionado
            entradas_genero = len(df_genero[df_genero['Contratado'].dt.year == ano_selecionado])
            saidas_genero = len(df_genero[df_genero['Desligado'].dt.year == ano_selecionado])

            turnover_quantidades[genero]["Entradas"] = entradas_genero
            turnover_quantidades[genero]["Saídas"] = saidas_genero

        # Preparar os dados para o gráfico
        data = {
            "Gênero": ["Masculino", "Masculino", "Feminino", "Feminino"],
            "Tipo": ["Entradas", "Saídas", "Entradas", "Saídas"],
            "Quantidade": [
                turnover_quantidades["Masculino"]["Entradas"],
                turnover_quantidades["Masculino"]["Saídas"],
                turnover_quantidades["Feminino"]["Entradas"],
                turnover_quantidades["Feminino"]["Saídas"]
            ]
        }
        df_grafico = pd.DataFrame(data)

        # Exibir o gráfico de comparação por gênero
        st.subheader("📊 Comparação de Entradas e Saídas por Gênero")
        fig = px.bar(
            df_grafico,
            x="Tipo",
            y="Quantidade",
            color="Gênero",
            barmode="group",
            title=f'Comparação de Entradas e Saídas de Colaboradores por Gênero ({ano_selecionado}, {funcao_selecionada})',
            labels={"Quantidade": "Quantidade de Colaboradores", "Tipo": "Tipo"},
            color_discrete_map={"Masculino": "#1f77b4", "Feminino": "#FF69B4"}
        )
        st.plotly_chart(fig)


def indicadores_demograficos(df):
    if df is not None:
        # Calcular indicadores demográficos
        dist_genero = df['Sexo'].value_counts(normalize=True) * 100
        dist_estado_civil = df['Casado'].value_counts(normalize=True) * 100
        tem_filhos = df['Tem filhos'].value_counts(normalize=True) * 100

        # Função para criar gráfico de barras horizontais compactos
        def plot_bar_chart(labels, sizes, title, color):
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.barh(labels, sizes, color=color)
            ax.set_xlabel('Percentual (%)')
            ax.set_title(title, fontsize=10)
            ax.grid(axis='x', linestyle='--', alpha=0.5)
            ax.tick_params(axis='y', labelsize=8)
            st.pyplot(fig)

        # Gráfico 1: Gênero
        st.subheader("Distribuição de Gênero")
        plot_bar_chart(
            labels=['Masculino', 'Feminino'],
            sizes=[dist_genero.get('Masculino', 0), dist_genero.get('Feminino', 0)],
            title="Gênero dos Colaboradores",
            color='skyblue'
        )

        # Gráfico 2: Estado Civil
        st.subheader("Distribuição por Estado Civil")
        plot_bar_chart(
            labels=['Casado', 'Solteiro'],
            sizes=[dist_estado_civil.get('Sim', 0), dist_estado_civil.get('Não', 0)],
            title="Estado Civil dos Colaboradores",
            color='lightcoral'
        )

        # Gráfico 3: Dependentes (Com ou Sem Filhos)
        st.subheader("Distribuição de Dependentes")
        plot_bar_chart(
            labels=['Com Filhos', 'Sem Filhos'],
            sizes=[tem_filhos.get('Sim', 0), tem_filhos.get('Não', 0)],
            title="Colaboradores com e sem Filhos",
            color='lightsalmon'
        )
    else:
        st.error("Por favor, carregue a base de dados na aba 'Base de Dados' para visualizar os indicadores.")

def indicadores_idade_tempo_casa(df):
    if df is not None:
        # Convertendo datas
        df['Data de Nascimento'] = pd.to_datetime(df['Data de Nascimento'], errors='coerce')
        df['Contratado'] = pd.to_datetime(df['Contratado'], errors='coerce')

        # Calculando a idade atual e o tempo de casa
        hoje = dt.datetime.now()
        df['Idade Atual'] = df['Data de Nascimento'].apply(lambda x: hoje.year - x.year if pd.notnull(x) else None)
        df['Tempo de Casa (anos)'] = df['Contratado'].apply(lambda x: (hoje - x).days / 365 if pd.notnull(x) else None)

        # Indicadores de idade
        idade_media = df['Idade Atual'].mean()
        idade_max = df['Idade Atual'].max()
        idade_min = df['Idade Atual'].min()

        # Faixas etárias
        faixas_etarias = pd.cut(df['Idade Atual'], bins=[0, 30, 40, 50, 100], labels=['Até 30', '31-40', '41-50', 'Acima de 50'])
        dist_faixas_etarias = faixas_etarias.value_counts(normalize=True) * 100

        # Indicadores de tempo de casa
        tempo_casa_medio = df['Tempo de Casa (anos)'].mean()

        # Faixas de tempo de casa
        faixas_tempo_casa = pd.cut(df['Tempo de Casa (anos)'], bins=[0, 1, 3, 5, 100], labels=['Até 1 ano', '1-3 anos', '3-5 anos', 'Acima de 5 anos'])
        dist_faixas_tempo_casa = faixas_tempo_casa.value_counts(normalize=True) * 100

        # Mostrar indicadores
        st.subheader("Indicadores Gerais de Idade e Tempo de Casa")
        st.write(f"**Idade Média:** {idade_media:.2f} anos")
        st.write(f"**Idade Máxima:** {idade_max:.0f} anos")
        st.write(f"**Idade Mínima:** {idade_min:.0f} anos")
        st.write(f"**Tempo Médio de Casa:** {tempo_casa_medio:.2f} anos")

        # Função para gráfico de barras
        def plot_bar_chart(labels, sizes, title, color):
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.barh(labels, sizes, color=color)
            ax.set_xlabel('Percentual (%)')
            ax.set_title(title, fontsize=10)
            ax.grid(axis='x', linestyle='--', alpha=0.5)
            st.pyplot(fig)

        # Gráfico 1: Faixas Etárias
        st.subheader("Distribuição por Faixas Etárias")
        plot_bar_chart(
            labels=dist_faixas_etarias.index.astype(str),
            sizes=dist_faixas_etarias.values,
            title="Distribuição de Idade dos Colaboradores",
            color='skyblue'
        )

        # Gráfico 2: Faixas de Tempo de Casa
        st.subheader("Distribuição por Faixas de Tempo de Casa")
        plot_bar_chart(
            labels=dist_faixas_tempo_casa.index.astype(str),
            sizes=dist_faixas_tempo_casa.values,
            title="Distribuição de Tempo de Casa",
            color='lightgreen'
        )
    else:
        st.warning("Nenhuma base de dados carregada. Vá para a aba 'Base de Dados' e carregue um arquivo.")

# Menu de tabs
tabs = st.tabs(['Demografia', 'Idade/tempo de casa','Localização geográfica','Rotatividade',  'Base de Dados'])

# Inicialização do DataFrame
df = None

# Aba "Base de Dados"
with tabs[4]: 
    st.subheader("Upload e Visualização da Base de Dados")
    uploaded_file = st.file_uploader("Upload da base de dados", type=["xlsx"])
    
    if uploaded_file:
        df = carregar_base_dados(uploaded_file)
        st.write(df)
    else:
        st.info("Por favor, faça o upload da base de dados para visualização.")

def indicadores_geograficos(df):
    if df is not None:
        # Distribuição por Estado
        dist_estado = df['Estado'].value_counts().reset_index()
        dist_estado.columns = ['Estado', 'Quantidade']

        # Distribuição por Cidade
        dist_cidade = df['Cidade'].value_counts().reset_index()
        dist_cidade.columns = ['Cidade', 'Quantidade']

        # Mapeamento para siglas do IBGE (ajustar conforme necessário)
        siglas_estados = {
            'Acre': 'AC', 'Alagoas': 'AL', 'Amapá': 'AP', 'Amazonas': 'AM', 'Bahia': 'BA',
            'Ceará': 'CE', 'Distrito Federal': 'DF', 'Espírito Santo': 'ES', 'Goiás': 'GO',
            'Maranhão': 'MA', 'Mato Grosso': 'MT', 'Mato Grosso do Sul': 'MS', 'Minas Gerais': 'MG',
            'Pará': 'PA', 'Paraíba': 'PB', 'Paraná': 'PR', 'Pernambuco': 'PE', 'Piauí': 'PI',
            'Rio de Janeiro': 'RJ', 'Rio Grande do Norte': 'RN', 'Rio Grande do Sul': 'RS',
            'Rondônia': 'RO', 'Roraima': 'RR', 'Santa Catarina': 'SC', 'São Paulo': 'SP',
            'Sergipe': 'SE', 'Tocantins': 'TO'
        }

        # Adicionar a sigla correspondente ao dataframe
        dist_estado['Sigla'] = dist_estado['Estado'].map(siglas_estados)

        # Carregar o GeoJSON dos estados brasileiros
        geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
        geojson_data = requests.get(geojson_url).json()

        # Mapa interativo com Plotly
        st.subheader("Distribuição de Colaboradores por Estado (Mapa)")
        fig = px.choropleth(
            dist_estado,
            geojson=geojson_data,
            locations="Sigla",
            featureidkey="properties.sigla",  # Mapeia com as siglas no GeoJSON
            color="Quantidade",
            hover_name="Estado",
            color_continuous_scale="Blues",
            title="Distribuição de Colaboradores por Estado"
        )

        fig.update_geos(fitbounds="locations", visible=False)  # Ajustar o mapa

        st.plotly_chart(fig)

        # Função para gráfico de barras horizontais
        def plot_bar_chart(labels, sizes, title, color):
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.barh(labels, sizes, color=color)
            ax.set_xlabel('Quantidade')
            ax.set_title(title, fontsize=10)
            ax.grid(axis='x', linestyle='--', alpha=0.5)
            st.pyplot(fig)

        # Gráfico 2: Top 5 Cidades
        st.subheader("Distribuição por Cidade - Top 5")
        top_cidades = dist_cidade.head(5)
        plot_bar_chart(
            labels=top_cidades['Cidade'],
            sizes=top_cidades['Quantidade'],
            title="Principais Cidades com Colaboradores",
            color='lightcoral'
        )

    else:
        st.warning("Por favor, carregue a base de dados para visualizar os indicadores geográficos.")

# Aba "Demografia"
with tabs[0]: 
    if df is not None:
        indicadores_demograficos(df)
    else:
        st.warning("Nenhuma base de dados carregada. Vá para a aba 'Base de Dados' e carregue um arquivo.")

# Aba "Idade/tempo de casa"
with tabs[1]: 
    if df is not None:  
        indicadores_idade_tempo_casa(df)
    else:
        st.warning("Nenhuma base de dados carregada. Vá para a aba 'Base de Dados' e carregue um arquivo.")

# Aba "geografico"
with tabs[2]: 
    if df is not None:
        indicadores_geograficos(df)
    else:
        st.warning("Nenhuma base de dados carregada. Vá para a aba 'Base de Dados' e carregue um arquivo.")

# Aba "Turnover"
with tabs[3]: 
    if df is not None:
        calcular_indicadores_turnover(df)
    else:
        st.warning("Nenhuma base de dados carregada. Vá para a aba 'Base de Dados' e carregue um arquivo.")