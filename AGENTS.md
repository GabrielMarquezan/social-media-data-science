# Guia para Agentes — coleta-de-dados

Este documento contém instruções para agentes de codificação que forem trabalhar neste projeto.

## Visão geral

Pipeline de coleta e análise de dados do Instagram usando o Apify. O fluxo principal:

1. Lê links do Instagram de `links.txt` (posts `/p/` e reels `/reel/`).
2. Extrai posts e comentários via Apify (ator `apify/instagram-scraper`).
3. Processa os dados em etapas (`social_media/src/pipeline/steps/`): parse, features de posts/comentários, análise de conteúdo, timing, NLP (termos, tópicos, sentimento).
4. Exporta resultados em `.xlsx`, `.csv` e `.png` dentro de `output/{run_id}/`.

## Setup

Dependências gerenciadas com `uv`:

```bash
uv sync
```

Baixe o modelo spaCy padrão:

```bash
python -m spacy download pt_core_news_sm
```

Crie o `.env` a partir do exemplo:

```bash
cp .env.example .env
```

Edite o `.env` e preencha pelo menos `APIFY_API_KEY`.

## Execução

### Interface web (Streamlit)

```bash
streamlit run app.py
```

Abre em http://localhost:8501. O `app.py` da raiz é um ponto de entrada fino que
chama `social_media.src.ui.app.main()`. A UI executa o pipeline em uma thread de
fundo (`social_media/src/ui/runner.py::start_run_in_thread`) e consome eventos de
progresso por uma fila (`social_media/src/ui/progress.py`), sem bloquear o Streamlit.

### CLI

```bash
python -m social_media.src.main
```

A execução requer:
- `APIFY_API_KEY` válida.
- Arquivo `links.txt` na raiz com uma URL do Instagram por linha.

## Testes

Rode os testes não lentos:

```bash
pytest social_media/tests -m "not slow"
```

O teste marcado como `slow` (`test_real_data_pipeline_with_real_sentiment_analyzer`) baixa e executa o modelo real de sentimento do Transformers, por isso é excluído do ciclo rápido.

## Convenções de código

- **Python 3.14+**.
- Type hints obrigatórios em assinaturas de funções e variáveis relevantes.
- Import absoluto preferencial: `social_media.src.*`.
- Os subpacotes de `social_media/src/` são **pacotes de namespace** e **não devem** conter `__init__.py`.
- Funções de pipeline devem ser puras e tolerar dados ausentes/malformados.
- Use `logging` com campos estruturados via `extra={...}`; não use `print`.
- Modelos de NLP (spaCy, Transformers, sentence-transformers, BERTopic) devem ser carregados de forma lazy em `social_media/src/dependencies.py`.

## Arquitetura

- `app.py` (raiz) — ponto de entrada da interface web Streamlit.
- `social_media/src/config.py` — centraliza variáveis de ambiente e defaults.
- `social_media/src/dependencies.py` — fábrica de dependências pesadas (modelos, clientes).
- `social_media/src/pipeline/runner.py` — executa as etapas em sequência (aceita `progress_callback` opcional).
- `social_media/src/pipeline/steps/` — transformações de dados.
- `social_media/src/charts/` — funções de plotagem matplotlib.
- `social_media/src/exporters/` — exportadores XLSX, CSV e PNG.
- `social_media/src/extract/` — extração de dados (Apify).
- `social_media/src/ui/` — interface web: `app.py` (visões Streamlit), `runner.py` (orquestração em thread), `progress.py` (eventos), `validation.py` (URLs), `runs.py` (execuções anteriores).
- `social_media/tests/` — testes organizados por componente.

## Cuidados

- Nunca comite arquivos `.env` ou dados reais. O `.gitignore` já os protege.
- A pasta `output/` e os arquivos `data/raw_*.json` são gerados automaticamente e devem permanecer ignorados.
- O primeiro uso de modelos Transformers/sentence-transformers pode fazer download automático; execuções subsequentes usam cache local.
- Se adicionar uma nova dependência, inclua no `pyproject.toml` e rode `uv lock`.

## Dependências principais

- `apify-client`
- `bertopic`, `keybert`, `sentence-transformers`, `spacy`, `transformers`, `torch`
- `pandas`, `openpyxl`, `matplotlib`
- `pytest`, `python-dotenv`, `scikit-learn`
- `streamlit` (interface web)

## Saídas esperadas

Após uma execução bem-sucedida, `output/{run_id}/` conterá:

- `metrics.xlsx` — métricas consolidadas por aba (posts, comentários, termos, tópicos, sentimentos, timing, qualidade).
- `charts/*.png` — gráficos do MVP.

Execuções antigas podem conter arquivos `.csv` (formato de exportação anterior); a interface os exibe em uma seção "formato antigo".
