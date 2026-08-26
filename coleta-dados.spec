# -*- mode: python ; coding: utf-8 -*-
"""Spec do PyInstaller para gerar o executavel Windows do Coleta de Dados.

Build (no Windows, com o ambiente virtual ativo):

    python -m PyInstaller coleta-dados.spec --noconfirm --clean

Resultado: pasta dist/ColetaDeDados/ contendo ColetaDeDados.exe.
"""

from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT


a = Analysis(
    ["launcher.py"],
    pathex=["."],
    binaries=[],
    datas=[
        ("app.py", "."),
        ("social_media", "social_media"),
    ],
    hiddenimports=[
        "social_media.src.ui.app",
        "social_media.src.main",
        "social_media.src.dependencies",
        "social_media.src.config",
        "social_media.src.log",
        "social_media.src.extract.apify",
        "social_media.src.pipeline.runner",
        "social_media.src.pipeline.steps.parse",
        "social_media.src.pipeline.steps.post_features",
        "social_media.src.pipeline.steps.comment_features",
        "social_media.src.pipeline.steps.post_conversation",
        "social_media.src.pipeline.steps.content_type",
        "social_media.src.pipeline.steps.timing",
        "social_media.src.pipeline.steps.nlp_terms",
        "social_media.src.pipeline.steps.nlp_topics",
        "social_media.src.pipeline.steps.nlp_sentiment_terms",
        "social_media.src.exporters.xlsx",
        "social_media.src.exporters.png",
        "social_media.src.charts.overview",
        "social_media.src.charts.captions",
        "social_media.src.charts.timing",
        "bertopic",
        "sklearn",
        "sklearn.utils._typedefs",
        "sklearn.utils._cython_blas",
        "spacy",
        "torch",
        "torchvision",
        "transformers",
        "sentence_transformers",
        "keybert",
        "pandas",
        "openpyxl",
        "matplotlib",
        "matplotlib.backends.backend_agg",
        "numpy",
        "apify_client",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ColetaDeDados",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon="icon.ico",  # descomente apos colocar um arquivo de icone na raiz
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ColetaDeDados",
)
