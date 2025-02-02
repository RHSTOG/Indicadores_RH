import streamlit as st
import pandas as pd
from PIL import Image

# Configuração inicial da página
st.set_page_config(page_title="Bem-vindo ao Dashboard STOG", layout="wide")

# Estilo customizado usando HTML e CSS embutidos
st.markdown("""
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
        }
        .metric-box {
            background: linear-gradient(135deg, #43cea2, #185a9d);
            color: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            transition: 0.3s ease;
            box-shadow: 0px 4px 8px rgba(0,0,0,0.1);
        }
        .metric-box:hover {
            transform: scale(1.05);
        }
        .navigation-button {
            background-color: #1e88e5;
            padding: 15px 30px;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 18px;
            transition: 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }
        .navigation-button:hover {
            background-color: #1565c0;
            transform: scale(1.05);
        }
    </style>
""", unsafe_allow_html=True)

# Exibir o logo com tamanho ajustado (altere o valor de width conforme necessário)
logo = Image.open("STOG.png")  # Substituir pelo caminho correto da imagem do logo
st.image(logo, width=300)  # Ajuste a largura aqui

# Texto de boas-vindas
st.markdown("""
    <h1 style='text-align: center; font-size: 40px; font-weight: bold;'>Bem-vindo ao Dashboard de Indicadores da STOG</h1>
    <p style='text-align: center; font-size: 18px; color: #555;'>
        Este painel foi projetado para fornecer informações estratégicas sobre nossos colaboradores, 
        como perfis demográficos, índice de turnover e fluxo de pessoal. Com essas informações, 
        você pode tomar decisões baseadas em dados e melhorar o planejamento da equipe.
    </p>
""", unsafe_allow_html=True)

# Rodapé
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #777;'>© 2025 STOG - Todos os direitos reservados.</p>", unsafe_allow_html=True)
