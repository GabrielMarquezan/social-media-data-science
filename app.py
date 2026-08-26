"""Ponto de entrada da interface web Streamlit.

Execute a partir da raiz do projeto com:

    streamlit run app.py

A interface fica disponível em http://localhost:8501.
"""

import os

# Garante backend não-interativo do matplotlib antes de qualquer import de
# charts/pyplot (os gráficos são gerados em uma thread de fundo).
os.environ.setdefault("MPLBACKEND", "Agg")

from social_media.src.ui.app import main

main()
