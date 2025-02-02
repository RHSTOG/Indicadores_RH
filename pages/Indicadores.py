import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import plotly.express as px
import json
import requests

# Configuração inicial do aplicativo
st.set_page_config(
    page_title="Dashboard de Indicadores da STOG",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilização com CSS (para personalizar fontes e espaçamento)
st.markdown("""
    <style>
    .big-font {
        font-size:36px !important;
        font-weight: bold;
    }
    .sub-text {
        font-size:18px;
        color: #666;
    }
    .card {
        background: linear-gradient(135deg, #4CAF50, #2a9df4);
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        color: white;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        margin: 10px;
    }
    .card-icon {
        font-size: 40px;
        margin-bottom: 10px;
    }
    .card-value {
        font-size: 36px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .card-label {
        font-size: 18px;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

# Cabeçalho principal
st.markdown("<h1 class='big-font'>Painel de Gestão de Pessoal da STOG</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-text'>Aqui você encontra os principais indicadores sobre o fluxo de colaboradores, perfis demográficos e o índice de turnover. Use essas informações para tomar decisões estratégicas sobre planejamento de equipe e engajamento.</p>", unsafe_allow_html=True)

# Inicialização das métricas usando st.empty()
col1, col2, col3 = st.columns(3)

# Função para leitura da base de dados
def carregar_base_dados(uploaded_file):
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file, sheet_name='BD')
        return df
    return None

# Função para calcular as métricas principais
def calcular_metricas_principais(df):
    # Converter datas de contratação e desligamento
    df['Contratado'] = pd.to_datetime(df['Contratado'], errors='coerce')
    df['Desligado'] = pd.to_datetime(df['Desligado'], errors='coerce')

    hoje = pd.Timestamp.now()
    ano_atual = hoje.year

    # Calcular colaboradores ativos atualmente
    colaboradores_ativos = len(df[(df['Contratado'] <= hoje) & ((df['Desligado'].isna()) | (df['Desligado'] > hoje))])

    # Entradas e saídas no ano atual
    entradas_ano = len(df[df['Contratado'].dt.year == ano_atual])
    saidas_ano = len(df[df['Desligado'].dt.year == ano_atual])

    # Calcular colaboradores ativos no início e final do ano
    colaboradores_inicio_ano = len(df[(df['Contratado'] <= f'{ano_atual}-01-01') & 
                                      ((df['Desligado'].isna()) | (df['Desligado'] > f'{ano_atual}-01-01'))])
    
    colaboradores_fim_ano = len(df[(df['Contratado'] <= f'{ano_atual}-12-31') & 
                                   ((df['Desligado'].isna()) | (df['Desligado'] > f'{ano_atual}-12-31'))])

    # Média de colaboradores no período
    media_colaboradores = (colaboradores_inicio_ano + colaboradores_fim_ano) / 2

    # Cálculo do turnover e taxa de retenção
    turnover_anual = (saidas_ano / media_colaboradores * 100) if media_colaboradores > 0 else 0
    taxa_retencao = ((media_colaboradores - saidas_ano) / media_colaboradores * 100) if media_colaboradores > 0 else 100

    return colaboradores_ativos, turnover_anual, taxa_retencao


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

    # Filtro por ano
    anos_disponiveis = sorted(list(set(df_filtrado['Contratado'].dt.year.dropna().astype(int)) |
                                   set(df_filtrado['Desligado'].dt.year.dropna().astype(int))))
    ano_selecionado = st.selectbox("Selecione o ano para análise:", options=anos_disponiveis, index=len(anos_disponiveis) - 1)

    # Filtrar contratações e desligamentos no ano selecionado
    entradas_ano = df_filtrado[df_filtrado['Contratado'].dt.year == ano_selecionado]
    saidas_ano = df_filtrado[df_filtrado['Desligado'].dt.year == ano_selecionado]

    total_entradas = len(entradas_ano)
    total_saidas = len(saidas_ano)

    # Calcular colaboradores ativos no início e fim do ano selecionado
    colaboradores_ativos_inicio = df_filtrado[(df_filtrado['Contratado'] <= f'{ano_selecionado}-01-01') &
                                              ((df_filtrado['Desligado'].isna()) | (df_filtrado['Desligado'] >= f'{ano_selecionado}-01-01'))]
    colaboradores_ativos_fim = df_filtrado[(df_filtrado['Contratado'] <= f'{ano_selecionado}-12-31') &
                                           ((df_filtrado['Desligado'].isna()) | (df_filtrado['Desligado'] >= f'{ano_selecionado}-12-31'))]

    # Média de colaboradores no ano
    total_colaboradores_medio = (len(colaboradores_ativos_inicio) + len(colaboradores_ativos_fim)) / 2

    # Cálculo do turnover correto
    turnover_anual = ((total_entradas + total_saidas) / (2 * total_colaboradores_medio)) * 100 if total_colaboradores_medio > 0 else 0


    # Estatísticas gerais formatadas como cards
    st.divider()
    st.write("#### Estatísticas Gerais de Rotatividade")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Ano Selecionado", f"{ano_selecionado}")
    col2.metric("Entradas de Colaboradores", f"{total_entradas}")
    col3.metric("Saídas de Colaboradores", f"{total_saidas}")
    col4.metric("Média de Colaboradores", f"{total_colaboradores_medio:.2f}")
    col5.metric("Turnover Anual", f"{turnover_anual:.2f}%")
    st.divider()

    # Gráfico de barras: Entradas e saídas gerais
    df_entradas_saidas = pd.DataFrame({
        'Tipo': ['Entradas', 'Saídas'],
        'Quantidade': [total_entradas, total_saidas]
    })

    fig_entradas_saidas = px.bar(
        df_entradas_saidas,
        x='Tipo',
        y='Quantidade',
        text='Quantidade',
        labels={'Quantidade': 'Quantidade de Colaboradores', 'Tipo': 'Tipo'},
        title=f"Entradas e Saídas de Colaboradores ({ano_selecionado})",
        color='Tipo',
        color_discrete_map={'Entradas': '#2E8B57', 'Saídas': '#FF6347'}
    )
    fig_entradas_saidas.update_traces(texttemplate='%{text}', textposition='outside')
    fig_entradas_saidas.update_layout(showlegend=False)
    st.plotly_chart(fig_entradas_saidas, use_container_width=True)

    # Gráfico de linha para entradas e saídas mensais no ano selecionado
    entradas_mensais = entradas_ano.groupby(entradas_ano['Contratado'].dt.to_period('M')).size().reset_index(name='Contratações')
    saidas_mensais = saidas_ano.groupby(saidas_ano['Desligado'].dt.to_period('M')).size().reset_index(name='Desligamentos')

    # Convertendo os períodos para strings no formato MM/YY
    entradas_mensais['Mês'] = entradas_mensais['Contratado'].dt.strftime("%m/%y")
    saidas_mensais['Mês'] = saidas_mensais['Desligado'].dt.strftime("%m/%y")

    # Gerar um DataFrame com todos os meses do ano e preencher dados ausentes com 0
    meses_ano = pd.date_range(start=f'{ano_selecionado}-01-01', end=f'{ano_selecionado}-12-31', freq='M').strftime("%m/%y")
    timeline_df = pd.DataFrame({'Mês': meses_ano}).merge(
        entradas_mensais[['Mês', 'Contratações']], on='Mês', how='left'
    ).merge(
        saidas_mensais[['Mês', 'Desligamentos']], on='Mês', how='left'
    ).fillna(0)

    # Converter para int (evitar números decimais no gráfico)
    timeline_df['Contratações'] = timeline_df['Contratações'].astype(int)
    timeline_df['Desligamentos'] = timeline_df['Desligamentos'].astype(int)

    # Gráfico de linha para os meses do ano selecionado
    fig_timeline = px.line(
        timeline_df,
        x='Mês',
        y=['Contratações', 'Desligamentos'],
        labels={'value': 'Quantidade', 'Mês': 'Mês'},
        title="Entradas e Saídas de Colaboradores ao Longo do Ano",
        markers=True
    )
    fig_timeline.update_layout(
        yaxis_title='Quantidade',
        xaxis_title='Mês',
        legend_title_text='Indicador',
        hovermode='x unified'
    )
    st.plotly_chart(fig_timeline, use_container_width=True)

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
        df_grafico_genero = pd.DataFrame({
            "Gênero": ["Masculino", "Masculino", "Feminino", "Feminino"],
            "Tipo": ["Entradas", "Saídas", "Entradas", "Saídas"],
            "Quantidade": [
                turnover_quantidades["Masculino"]["Entradas"],
                turnover_quantidades["Masculino"]["Saídas"],
                turnover_quantidades["Feminino"]["Entradas"],
                turnover_quantidades["Feminino"]["Saídas"]
            ]
        })

        # Exibir o gráfico de comparação por gênero
        st.subheader("📊 Comparação de Entradas e Saídas por Gênero")
        fig_genero = px.bar(
            df_grafico_genero,
            x="Tipo",
            y="Quantidade",
            color="Gênero",
            barmode="group",
            title=f'Comparação de Entradas e Saídas de Colaboradores por Gênero ({ano_selecionado})',
            labels={"Quantidade": "Quantidade de Colaboradores", "Tipo": "Tipo"},
            color_discrete_map={"Masculino": "#1f77b4", "Feminino": "#FF69B4"}
        )
        fig_genero.update_traces(texttemplate='%{y}', textposition='outside')
        st.plotly_chart(fig_genero, use_container_width=True)






def indicadores_demograficos(df):
    if df is not None:
        # Calcular indicadores demográficos
        dist_genero = df['Sexo'].value_counts(normalize=True) * 100
        dist_estado_civil = df['Casado'].value_counts(normalize=True) * 100
        tem_filhos = df['Tem filhos'].value_counts(normalize=True) * 100

        # Gráfico 1: Distribuição de Gênero
        genero_data = {
            "Gênero": ['Masculino', 'Feminino'],
            "Percentual": [dist_genero.get('Masculino', 0), dist_genero.get('Feminino', 0)]
        }
        fig_genero = px.bar(
            genero_data, 
            x="Percentual", 
            y="Gênero", 
            orientation='h', 
            title="Distribuição de Gênero dos Colaboradores", 
            labels={"Percentual": "Percentual (%)", "Gênero": "Gênero"},
            color="Gênero",
            color_discrete_sequence=["skyblue", "pink"]
        )
        st.plotly_chart(fig_genero)

        # Gráfico 2: Estado Civil
        estado_civil_data = {
            "Estado Civil": ['Casado', 'Solteiro'],
            "Percentual": [dist_estado_civil.get('Sim', 0), dist_estado_civil.get('Não', 0)]
        }
        fig_estado_civil = px.bar(
            estado_civil_data, 
            x="Percentual", 
            y="Estado Civil", 
            orientation='h', 
            title="Distribuição por Estado Civil", 
            labels={"Percentual": "Percentual (%)", "Estado Civil": "Estado Civil"},
            color="Estado Civil",
            color_discrete_sequence=["lightcoral", "lightgreen"]
        )
        st.plotly_chart(fig_estado_civil)

        # Gráfico 3: Dependentes (Com ou Sem Filhos)
        filhos_data = {
            "Categoria": ['Com Filhos', 'Sem Filhos'],
            "Percentual": [tem_filhos.get('Sim', 0), tem_filhos.get('Não', 0)]
        }
        fig_filhos = px.bar(
            filhos_data, 
            x="Percentual", 
            y="Categoria", 
            orientation='h', 
            title="Distribuição de Dependentes (Com ou Sem Filhos)", 
            labels={"Percentual": "Percentual (%)", "Categoria": "Categoria"},
            color="Categoria",
            color_discrete_sequence=["orange", "lightblue"]
        )
        st.plotly_chart(fig_filhos)
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

        # Indicadores de idade e tempo de casa
        idade_media = df['Idade Atual'].mean()
        idade_max = df['Idade Atual'].max()
        idade_min = df['Idade Atual'].min()
        tempo_casa_medio = df['Tempo de Casa (anos)'].mean()

        # Exibindo indicadores de forma simplificada
        st.divider()
        st.write(""" ##### Indicadores Gerais de Idade e Tempo de Casa""")
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric("Idade Média", f"{idade_media:.2f} anos")
        col2.metric("Idade Máxima", f"{idade_max:.0f} anos")
        col3.metric("Idade Mínima", f"{idade_min:.0f} anos")
        col4.metric("Tempo Médio de Casa", f"{tempo_casa_medio:.2f} anos")
        st.divider()

        # Preparar distribuições
        faixas_etarias = pd.cut(df['Idade Atual'], bins=[0, 30, 40, 50, 100], labels=['Até 30', '31-40', '41-50', 'Acima de 50'])
        dist_faixas_etarias = faixas_etarias.value_counts(normalize=True).reset_index()
        dist_faixas_etarias.columns = ['Faixa Etária', 'Percentual']
        dist_faixas_etarias['Percentual'] *= 100  # Corrigir percentual

        faixas_tempo_casa = pd.cut(df['Tempo de Casa (anos)'], bins=[0, 1, 3, 5, 100], labels=['Até 1 ano', '1-3 anos', '3-5 anos', 'Acima de 5 anos'])
        dist_faixas_tempo_casa = faixas_tempo_casa.value_counts(normalize=True).reset_index()
        dist_faixas_tempo_casa.columns = ['Faixa de Tempo de Casa', 'Percentual']
        dist_faixas_tempo_casa['Percentual'] *= 100  # Corrigir percentual

        # Gráficos com plotly
        fig_faixas_etarias = px.bar(
            dist_faixas_etarias,
            x='Faixa Etária',
            y='Percentual',
            text='Percentual',
            labels={'Percentual': 'Percentual (%)'},
            title="Distribuição por Faixas Etárias",
        )
        fig_faixas_etarias.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig_faixas_etarias.update_layout(yaxis_title='Percentual (%)', showlegend=False)

        fig_faixas_tempo_casa = px.bar(
            dist_faixas_tempo_casa,
            x='Faixa de Tempo de Casa',
            y='Percentual',
            text='Percentual',
            labels={'Percentual': 'Percentual (%)'},
            title="Distribuição por Faixas de Tempo de Casa",
        )
        fig_faixas_tempo_casa.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig_faixas_tempo_casa.update_layout(yaxis_title='Percentual (%)', showlegend=False)

        st.plotly_chart(fig_faixas_etarias, use_container_width=True)
        st.plotly_chart(fig_faixas_tempo_casa, use_container_width=True)

    else:
        st.warning("Nenhuma base de dados carregada. Vá para a aba 'Base de Dados' e carregue um arquivo.")



# Menu de tabs
tabs = st.tabs(['Demografia', 'Idade/tempo de casa','Localização geográfica','Rotatividade',  'Base de Dados'])

# Inicialização do DataFrame
df = None

# Aba "Base de Dados"
with tabs[4]: 
    st.header("📁 Base de Dados")
    st.write("Acesse a base de dados completa para uma análise detalhada.")
    uploaded_file = st.file_uploader("Upload da base de dados", type=["xlsx"])
    
    if uploaded_file:
        df = carregar_base_dados(uploaded_file)
        st.write(df)
        # Calcular métricas principais
        colaboradores_ativos, turnover_anual, taxa_retencao = calcular_metricas_principais(df)

        # Atualizar as métricas no layout
        # Atualizar dinamicamente os valores dos cartões
        col1.markdown(f"""
            <div class="card">
            <div class="card-icon">👥</div>
            <div class="card-value">{colaboradores_ativos}</div>
            <div class="card-label">Colaboradores Ativos</div>
         </div>
        """, unsafe_allow_html=True)

        col2.markdown(f"""
        <div class="card">
            <div class="card-icon">📊</div>
            <div class="card-value">{turnover_anual:.2f}%</div>
            <div class="card-label">Volume de Negócios Anual</div>
        </div>
        """, unsafe_allow_html=True)

        col3.markdown(f"""
        <div class="card">
            <div class="card-icon">💼</div>
            <div class="card-value">{taxa_retencao:.2f}%</div>
            <div class="card-label">Taxa de Retenção</div>
        </div>
        """, unsafe_allow_html=True)

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

        # Top 5 cidades
        st.subheader("Principais Cidades com Colaboradores")
        top_cidades = dist_cidade.head(5)

        # Gráfico de barras com Plotly
        fig_cidades = px.bar(
            top_cidades,
            x='Quantidade',
            y='Cidade',
            text='Quantidade',
            orientation='h',
            labels={'Quantidade': 'Quantidade de Colaboradores', 'Cidade': 'Cidade'},
            title="Distribuição por Cidade - Top 5",
        )
        fig_cidades.update_traces(texttemplate='%{text}', textposition='outside')
        fig_cidades.update_layout(yaxis_title='Cidade', xaxis_title='Quantidade de Colaboradores', showlegend=False)
        
        st.plotly_chart(fig_cidades, use_container_width=True)

    else:
        st.warning("Por favor, carregue a base de dados para visualizar os indicadores geográficos.")

# Aba "Demografia"
with tabs[0]: 
    st.header("📊 Demografia")
    st.write("Visualize informações sobre a distribuição de gênero, idade e diversidade na empresa.")
    if df is not None:
        indicadores_demograficos(df)
    else:
        st.warning("Nenhuma base de dados carregada. Vá para a aba 'Base de Dados' e carregue um arquivo.")

# Aba "Idade/tempo de casa"
with tabs[1]: 
    st.header("⏳ Idade/Tempo de Casa")
    st.write("Veja como o tempo de empresa e a idade dos colaboradores afetam o perfil geral da equipe.")
    if df is not None:  
        indicadores_idade_tempo_casa(df)
    else:
        st.warning("Nenhuma base de dados carregada. Vá para a aba 'Base de Dados' e carregue um arquivo.")

# Aba "geografico"
with tabs[2]: 
    st.header("🌍 Localização Geográfica")
    st.write("Distribuição geográfica dos colaboradores por cidade ou estado.")
    if df is not None:
        indicadores_geograficos(df)
    else:
        st.warning("Nenhuma base de dados carregada. Vá para a aba 'Base de Dados' e carregue um arquivo.")

# Aba "Turnover"
with tabs[3]: 
    st.header("📉 Rotatividade")
    st.write("Análise das taxas de turnover, entradas e saídas de colaboradores.")
    if df is not None:
        calcular_indicadores_turnover(df)
    else:
        st.warning("Nenhuma base de dados carregada. Vá para a aba 'Base de Dados' e carregue um arquivo.")

# Rodapé opcional
st.markdown("---")
st.markdown("<p style='text-align:center;'>© 2025 STOG - Todos os direitos reservados.</p>", unsafe_allow_html=True)