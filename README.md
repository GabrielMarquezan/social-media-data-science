# coleta-de-dados

Pipeline de coleta e análise de dados do Instagram via Apify.

Este projeto lê links de posts/canais do Instagram, extrai dados públicos (posts, comentários, curtidas, etc.) usando o ator `apify/instagram-scraper`, e em seguida processa, enriquece e exporta métricas em planilhas Excel, arquivos CSV e gráficos PNG.

## Pré-requisitos

- **Python 3.14+** (ver `requires-python` em `pyproject.toml`).
- **uv** para gerenciamento de dependências: https://docs.astral.sh/uv/
- Uma conta no **Apify** com uma chave de API válida.
- (Recomendado) Git para clonar e versionar o repositório.

## Instalação

1. Clone o repositório e entre na pasta do projeto.

2. Instale as dependências Python:

   ```bash
   uv sync
   ```

3. Baixe o modelo spaCy padrão usado pelo pipeline:

   ```bash
   python -m spacy download pt_core_news_sm
   ```

   > O primeiro uso de modelos do `sentence-transformers`, `transformers` e `BERTopic` pode fazer download automático pela internet. Execuções subsequentes usam cache local.

4. Crie o arquivo de configuração local a partir do exemplo:

   ```bash
   cp .env.example .env
   ```

5. Edite `.env` e preencha pelo menos a variável `APIFY_API_KEY`.

## Configuração

O comportamento do pipeline é controlado por variáveis de ambiente. Veja a descrição completa abaixo.

### Variáveis obrigatórias

| Variável | Descrição |
|----------|-----------|
| `APIFY_API_KEY` | Chave de API do Apify. Obtenha em https://console.apify.com/account/integrations |

### Variáveis opcionais

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `APIFY_ACTOR` | `apify/instagram-scraper` | Ator do Apify usado na coleta. |
| `RESULTS_LIMIT` | `100` | Limite de resultados retornados pelo Apify por link. |
| `QUALIFIED_COMMENT_MIN_WORDS` | `5` | Mínimo de palavras para um comentário ser considerado "qualificado". |
| `SENTIMENT_MODEL` | `nlptown/bert-base-multilingual-uncased-sentiment` | Modelo do Transformers para análise de sentimento. |
| `LOG_LEVEL` | `DEBUG` | Nível de log (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `LOG_FORMAT` | `json` | Formato dos logs (`json` ou `text`). |
| `TOP_POSTS_LIMIT` | `10` | Quantidade de top posts destacados nos gráficos. |
| `CHART_DPI` | `150` | Resolução (DPI) dos gráficos PNG. |
| `XLSX_ENGINE` | `openpyxl` | Motor de escrita de arquivos Excel. |
| `SPACY_MODEL` | `pt_core_news_sm` | Modelo spaCy para tokenização e lematização. |
| `BERTOPIC_EMBEDDING_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | Modelo de embeddings usado pelo BERTopic. |
| `NLP_TOP_TERMS_LIMIT` | `20` | Quantidade de termos principais extraídos. |
| `NLP_TOPIC_COUNT` | `10` | Número de tópicos gerados pelo BERTopic. |
| `NLP_TOPIC_TERMS_LIMIT` | `10` | Quantidade de termos por tópico. |
| `NLP_SENTIMENT_TERMS_LIMIT` | `10` | Quantidade de termos por sentimento. |

## Execução

### Interface web (Streamlit)

A forma mais simples de usar o projeto é pela interface web:

```bash
streamlit run app.py
```

A interface abre em http://localhost:8501 e permite:

- Colar uma URL de post ou reel do Instagram por linha (com validação dos formatos `https://www.instagram.com/p/{shortcode}/` e `https://www.instagram.com/reel/{shortcode}/`).
- Iniciar a execução e acompanhar o progresso em tempo real (extração, etapas do pipeline, exportação).
- Visualizar e baixar os resultados: `metrics.xlsx` completo, tabelas individuais em XLSX e gráficos PNG, além de tabelas interativas.
- Navegar pelas execuções anteriores em `output/{run_id}/`, incluindo marcação de execuções incompletas.

### Linha de comando (CLI)

1. Crie ou atualize o arquivo `links.txt` na raiz do projeto, com uma URL do Instagram por linha (posts `/p/` e reels `/reel/` são aceitos). Exemplo:

   ```text
   https://www.instagram.com/p/ABC123/
   https://www.instagram.com/reel/DEF456/
   ```

2. Execute o pipeline:

   ```bash
   python -m social_media.src.main
   ```

3. Ao final, os resultados estarão em `output/{run_id}/`:

   - `metrics.xlsx` — métricas consolidadas, uma aba por tabela (posts, comentários, termos, tópicos, sentimentos, timing, qualidade).
   - `charts/*.png` — gráficos do MVP.

## Distribuição para Windows (executável standalone)

O projeto pode ser empacotado como um executavel Windows que abre a interface web com duplo clique.

### Para o usuario final

1. Baixe o arquivo `ColetaDeDados-windows.zip` da ultima release (ou receba a pasta `ColetaDeDados/`).
2. Descompacte em qualquer lugar do computador.
3. Abra a pasta `ColetaDeDados` e clique duas vezes em `ColetaDeDados.exe`.
4. O navegador padrao abrira automaticamente em http://localhost:8501.
5. Na primeira execucao, o programa baixa automaticamente os modelos de IA (spaCy ja vem incluso; Transformers e sentence-transformers sao baixados no primeiro uso). Isso pode levar alguns minutos, dependendo da conexao.

> A chave `APIFY_API_KEY` pode ser informada atraves de uma variavel de ambiente ou de um arquivo `.env` dentro da pasta do executavel.

### Como gerar o executavel (build no Windows)

Requisitos:

- Windows 10/11
- Python 3.14+
- Git (opcional, para clonar o repositorio)

Passos:

```powershell
# Clone ou copie o projeto para a maquina Windows
git clone <url-do-repositorio>
cd coleta_de_dados

# Crie e ative o ambiente virtual
python -m venv .venv
.venv\Scripts\Activate.ps1

# Instale as dependencias e o PyInstaller
pip install -e ".[dev]"
python -m spacy download pt_core_news_sm

# Gere o executavel (modo pasta --onedir)
python -m PyInstaller coleta-dados.spec --noconfirm --clean
```

O resultado ficara em `dist\ColetaDeDados\`. Compacte essa pasta e distribua.

### Build automatico com GitHub Actions

O repositorio inclui o workflow `.github/workflows/build-windows.yml`. A cada tag `v*`, uma release e gerada automaticamente com o arquivo `ColetaDeDados-windows.zip` anexado.

## Testes

Para rodar apenas os testes rápidos (exclui o teste que baixa e executa o modelo real de sentimento):

```bash
pytest social_media/tests -m "not slow"
```

Para rodar todos os testes, incluindo o lento:

```bash
pytest social_media/tests
```

> Aviso: o teste `test_real_data_pipeline_with_real_sentiment_analyzer` faz download do modelo de sentimento e pode demorar vários minutos na primeira execução.

## Estrutura do projeto

```text
.
├── .env.example              # Exemplo de variáveis de ambiente
├── AGENTS.md                 # Guia para agentes de codificação
├── app.py                    # Ponto de entrada da interface web (streamlit run app.py)
├── links.txt                 # Links do Instagram a serem processados
├── pyproject.toml            # Dependências e configurações do projeto
├── README.md                 # Este arquivo
├── data/                     # Dados brutos e fixtures
├── output/                   # Resultados gerados automaticamente
└── social_media/
    ├── src/
    │   ├── charts/           # Funções de plotagem com matplotlib
    │   ├── config.py         # Configurações e variáveis de ambiente
    │   ├── dependencies.py   # Fábrica lazy de modelos e clientes
    │   ├── domain/           # Modelos de dados (dataclasses)
    │   ├── exporters/        # Exportadores XLSX, CSV e PNG
    │   ├── extract/          # Extração de dados via Apify
    │   ├── log.py            # Configuração de logging
    │   ├── main.py           # Ponto de entrada do pipeline (CLI)
    │   ├── metrics/          # Cálculo de métricas
    │   ├── nlp/              # Funções de NLP (termos, tópicos, sentimento)
    │   ├── pipeline/         # Runner e steps de transformação
    │   ├── services/         # Serviços auxiliares
    │   └── ui/               # Interface web (app, orquestrador, validação, execuções)
    └── tests/                # Testes organizados por componente
```

## Convenções de código

- Use type hints em todas as assinaturas de funções e variáveis relevantes.
- Prefira imports absolutos: `social_media.src.*`.
- Os subpacotes de `social_media/src/` são pacotes de namespace e **não** possuem `__init__.py`.
- Funções de pipeline devem ser puras e tolerar dados ausentes ou malformados.
- Use `logging` com campos estruturados via `extra={...}`; evite `print`.
- Modelos de NLP devem ser carregados de forma lazy em `social_media/src/dependencies.py`.

## Troubleshooting

### `ValueError: APIFY_API_KEY não configurada no ambiente`

Você esqueceu de criar o `.env` ou de preencher `APIFY_API_KEY`. Execute:

```bash
cp .env.example .env
# edite .env e insira sua chave
```

### `OSError: Can't find model 'pt_core_news_sm'`

O modelo spaCy não está instalado. Execute:

```bash
python -m spacy download pt_core_news_sm
```

### Primeira execução muito lenta

Modelos de Transformers, sentence-transformers e BERTopic podem ser baixados automaticamente na primeira execução. Verifique sua conexão e aguarde. Execuções posteriores serão mais rápidas.

### `links.txt` não encontrado

O arquivo `links.txt` deve existir na raiz do projeto, com pelo menos uma URL do Instagram válida.

## Contribuição

- Adicione novas dependências em `pyproject.toml` e rode `uv lock`.
- Nunca comite arquivos `.env`, dados reais em `data/` nem conteúdo de `output/`.
- Mantenha `AGENTS.md` atualizado se alterar a arquitetura ou o setup do projeto.
