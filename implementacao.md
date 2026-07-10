# Plano de Implementação: Coleta e Análise de Dados do Instagram

## Objetivo

Transformar o script monolítico atual (`social_media/src/main.py`) em uma aplicação modular, testável e extensível que:

1. Extraia posts do Instagram via Apify de forma assíncrona.
2. Converta o JSON bruto em dataclasses de domínio tipadas.
3. Processe métricas e features por meio de um pipeline funcional de DataFrames.
4. Execute análise de sentimento em comentários com o modelo `nlptown/bert-base-multilingual-uncased-sentiment`.
5. Gere gráficos em PNG e exporte métricas estilizadas em XLSX.

O foco deste plano é o **MVP** definido em `planejamento.md`: métricas dos grupos 1, 4, 5 e 7 de `metrics.md`; gráficos dos grupos 1, 4 e 5 de `charts.md`; NLP de sentimento; e stubs de qualidade de dados.

## Requisitos

### Explícitos

- Extrair posts do Instagram a partir de URLs listadas em `links.txt` usando `apify-client`.
- Converter o JSON do Apify em dataclasses (`Author`, `Comment`, `Post`, `SentimentResult`).
- Calcular métricas de engajamento (grupo 1), features de legenda (grupo 4), features de comentários (grupo 5) e agregações de timing (grupo 7).
- Aplicar análise de sentimento nos comentários com `nlptown/bert-base-multilingual-uncased-sentiment`.
- Gerar gráficos PNG: timeline, ranking, posts por tipo, scatter de legenda vs. engajamento, heatmap e barras por dia da semana.
- Exportar resultados em XLSX com múltiplas abas e estilização básica.
- Usar programação funcional no pipeline de DataFrames e POO com injeção de dependências.
- Manter type hints em todas as assinaturas.
- Não usar `__init__.py` nos subpacotes.

### Implícitos

- O código deve tolerar dados ausentes ou malformados sem quebrar a execução.
- Logs devem ser estruturados (JSON) e conter `run_id`.
- O pipeline deve ser reexecutável e determinístico para a mesma entrada.
- O carregamento do modelo NLP deve ser lazy para não penalizar testes ou extração.
- As saídas devem ser organizadas por `run_id` em `output/{run_id}/`.

### Assunções

- O JSON do Apify segue a estrutura atualmente observada em `data/comments.json` (quando existente), com campos como `id`, `type`, `shortCode`, `caption`, `hashtags`, `mentions`, `url`, `commentsCount`, `likesCount`, `timestamp`, `owner`, `productType`, `videoViewCount`, `videoDuration`, `latestComments`, etc.
- `links.txt` contém uma URL por linha.
- A variável de ambiente `APIFY_API_KEY` está disponível no `.env`.
- O ambiente possui Python >= 3.14 e suporte a `async`/`await`.
- A instalação do `torch`+`transformers` é viável no ambiente de execução.

### Critérios de Sucesso

- `main.py` executa de ponta a ponta sem erros para a amostra real e para fixtures sintéticas.
- O parser produz `list[Post]` fiel ao JSON de entrada.
- Métricas dos grupos 1, 4, 5 e 7 estão presentes nos DataFrames de saída.
- A aba `Quality` do XLSX existe como stub e levanta `NotImplementedError` apenas se invocada explicitamente.
- Todos os gráficos do MVP são salvos como PNG.
- Testes unitários cobrem parser, métricas e pipeline.

## Visão Geral da Arquitetura

### Decisões Arquiteturais

| Decisão | Escolha | Justificativa |
|---|---|---|
| Paradigma | Híbrido: POO para domínio, funcional para pipeline de DataFrames | Separa modelagem conceitual da transformação tabular, facilitando testes e manutenção. |
| Pacotes | Por responsabilidade (`domain/`, `pipeline/`, `metrics/`, `charts/`, `exporters/`, `extract/`) | Clareza de dependências e evolução independente. |
| Domínio | Dataclasses imutáveis (`frozen=True`) | Garante integridade dos objetos de domínio. |
| Pipeline | `Dict[str, pd.DataFrame]` passado entre steps | Flexibilidade para adicionar novas tabelas sem alterar a assinatura dos steps. |
| Steps | Funções puras: `step(dfs: dict[str, pd.DataFrame], config: Config, deps: Dependencies) -> dict[str, pd.DataFrame]` | Previsibilidade, testabilidade e rastreabilidade. |
| Config | `Config` em `config.py`; segredos em `.env` | Centraliza constantes e evita exposição de credenciais. |
| Dependências | `Dependencies` em `dependencies.py` com lazy loading | Carrega o sentiment analyzer apenas quando necessário. |
| Logging | `logging.py` com formatter JSON e `run_id` global | Logs estruturados facilitam observabilidade. |
| Tolerância | Extração tolerante; ausências viram `None` | Robustez contra dados reais incompletos. |
| Async/sync | `extract/apify.py` async; `pipeline/` e `metrics/` sync; `main.py` async orquestradora | O Apify é I/O-bound; processamento de DataFrames é CPU-bound e sincronizado. |
| Type hints | Em todas as assinaturas; sem mypy no MVP | Documentação viva sem custo de tooling. |
| Subpacotes | Sem `__init__.py`; imports absolutos diretos | Conforme decisão de `planejamento.md`. |

### Estrutura de Dados-Chave

#### Domínio

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass(frozen=True)
class Author:
    id: str | None
    username: str | None
    full_name: str | None
    is_verified: bool | None
    profile_pic_url: str | None

@dataclass(frozen=True)
class Comment:
    id: str
    text: str
    owner: Author
    timestamp: datetime | None
    likes_count: int | None
    replies_count: int | None
    replies: list["Comment"] = field(default_factory=list)

@dataclass(frozen=True)
class SentimentResult:
    label: str  # "positivo", "neutro" ou "negativo"
    score: float  # valor mapeado para escala 0..1 ou -1..1
    raw_label: str  # rótulo original do modelo
    raw_score: float  # probabilidade bruta do modelo

@dataclass(frozen=True)
class Post:
    id: str
    type: str
    short_code: str
    caption: str | None
    hashtags: list[str]
    mentions: list[str]
    url: str
    comments_count: int | None
    first_comment: str | None
    latest_comments: list[Comment]
    likes_count: int | None
    timestamp: datetime | None
    owner: Author
    product_type: str | None
    views: int | None = None
    video_duration: float | None = None
```

#### Configuração

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Config:
    apify_token: str
    apify_actor: str
    results_limit: int
    qualified_comment_min_words: int
    sentiment_model: str
    output_dir: Path
    data_dir: Path
    log_level: str
    log_format: str
    top_posts_limit: int
    chart_dpi: int
    xlsx_engine: str
```

#### Dependências

```python
from dataclasses import dataclass
from typing import Callable

@dataclass
class Dependencies:
    sentiment_analyzer: Callable[[str], SentimentResult] | None = None

    def get_sentiment_analyzer(self) -> Callable[[str], SentimentResult]:
        if self.sentiment_analyzer is None:
            self.sentiment_analyzer = _build_transformers_sentiment_analyzer()
        return self.sentiment_analyzer
```

#### Pipeline

```python
from typing import Callable

Step = Callable[[dict[str, pd.DataFrame], Config, Dependencies], dict[str, pd.DataFrame]]
```

O dicionário `dfs` conterá, no mínimo:

- `"posts"`: DataFrame com uma linha por post e colunas de features.
- `"comments"`: DataFrame com uma linha por comentário (com `post_id` foreign key).
- `"timing_by_hour"`: agregação de posts por hora.
- `"timing_by_weekday"`: agregação de posts por dia da semana.

### Mapa de Componentes

```
social_media/
├── src/
│   ├── main.py                      # Orquestradora async: extract → analyze → export
│   ├── config.py                    # Constantes e factory Config
│   ├── dependencies.py              # Lazy loading de dependências injetáveis
│   ├── logging.py                   # Configuração de logging
│   ├── domain/
│   │   ├── author.py                # dataclass Author
│   │   ├── comment.py               # dataclass Comment
│   │   ├── post.py                  # dataclass Post
│   │   └── sentiment.py             # dataclass SentimentResult
│   ├── parsers/
│   │   └── apify.py                 # JSON Apify → list[Post]
│   ├── pipeline/
│   │   ├── runner.py                # run_pipeline(dfs, steps, config, deps)
│   │   └── steps/
│   │       ├── parse.py             # JSON → DataFrames posts/comments
│   │       ├── post_features.py     # features de legenda + engajamento
│   │       ├── comment_features.py  # word_count, is_qualified, is_question, sentimento
│   │       └── timing.py            # agregações por hora/dia da semana
│   ├── metrics/
│   │   ├── engagement.py            # engagement_rate, comments_per_like, etc.
│   │   ├── caption.py               # caption_word_count, emoji_count, CTA flags, etc.
│   │   ├── comment.py               # word_count, is_qualified, is_question
│   │   └── timing.py                # post_hour, post_weekday, post_period
│   ├── nlp/
│   │   └── sentiment.py             # Funções puras de análise de sentimento
│   ├── charts/
│   │   ├── overview.py              # timeline, ranking, posts by type
│   │   ├── captions.py              # scatter caption vs engagement
│   │   └── timing.py                # heatmap + barras por dia da semana
│   ├── exporters/
│   │   ├── xlsx.py                  # Estilização e salvamento do XLSX
│   │   └── png.py                   # Salvamento dos gráficos
│   └── extract/
│       └── apify.py                 # Extração async do Apify
├── tests/
│   ├── fixtures/
│   │   ├── real_sample.json
│   │   └── synthetic_posts.json
│   ├── test_parser.py
│   ├── test_metrics.py
│   └── test_pipeline.py
├── links.txt
└── pyproject.toml
```

## Fases de Implementação

### Fase 1: Preparação do Ambiente e Configuração

#### Passo 1.1: Ajustar dependências do projeto

- **Arquivos**: `pyproject.toml`
- **Ação**: Remover dependências não usadas no MVP e garantir versões mínimas para as dependências mantidas.
- **Detalhes**: Remover `sentence-transformers`, `sentencepiece`, `tiktoken` e `protobuf`. Manter `apify-client>=3.0.2`, `matplotlib>=3.10.9`, `openpyxl>=3.1.5`, `pandas>=3.0.3`, `pytest>=9.0.3`, `python-dotenv>=1.2.2`, `scikit-learn>=1.6.0`, `torch>=2.12.0`, `transformers>=5.9.0`. Opcionalmente adicionar `emoji` para contagem de emojis, se desejado; caso contrário, usar regex simples.
- **Por quê**: Reduz tempo de instalação, tamanho de imagem e superfície de incompatibilidades.
- **Verificação**: `uv sync` ou `pip install -e .` conclui sem erros e `python -c "import pandas, openpyxl, matplotlib, transformers, torch"` funciona.

#### Passo 1.2: Criar módulo de configuração

- **Arquivos**: `social_media/src/config.py`
- **Ação**: Implementar a dataclass `Config` e uma factory `build_config() -> Config` que leia variáveis de ambiente via `dotenv`.
- **Detalhes**:
  - `apify_token`: obrigatório; lido de `APIFY_API_KEY`.
  - `apify_actor`: padrão `"apify/instagram-scraper"`.
  - `results_limit`: padrão `100`.
  - `qualified_comment_min_words`: padrão `5`.
  - `sentiment_model`: `"nlptown/bert-base-multilingual-uncased-sentiment"`.
  - `output_dir`: `Path("output")`.
  - `data_dir`: `Path("data")`.
  - `log_level`: `"DEBUG"`.
  - `log_format`: `"json"`.
  - `top_posts_limit`: padrão `10`.
  - `chart_dpi`: padrão `150`.
  - `xlsx_engine`: padrão `"openpyxl"`.
  - Campos `Path` devem ser convertidos para absolutos na factory.
- **Por quê**: Centraliza constantes e evita hardcoding espalhado.
- **Verificação**: `python -c "from social_media.src.config import build_config; print(build_config().sentiment_model)"` exibe o modelo correto.

#### Passo 1.3: Integrar logging com run_id

- **Arquivos**: `social_media/src/logging.py` (já existe), `social_media/src/main.py`
- **Ação**: Garantir que `configure_logging()` seja chamado no início de `main()` e que `set_run_id` seja invocado antes da extração.
- **Detalhes**: O logging existente já possui formatter JSON e suporte a `run_id`. Validar que `extra` campos são serializados corretamente e que o `run_id` é propagado.
- **Por quê**: Observabilidade desde o primeiro momento da execução.
- **Verificação**: Executar `configure_logging()` e emitir um log; verificar JSON com `run_id` e campos extras.

### Fase 2: Modelagem de Domínio e Parser

#### Passo 2.1: Criar dataclasses de domínio

- **Arquivos**: `social_media/src/domain/author.py`, `social_media/src/domain/comment.py`, `social_media/src/domain/post.py`, `social_media/src/domain/sentiment.py`
- **Ação**: Implementar as dataclasses conforme especificação, com `frozen=True` e type hints.
- **Detalhes**:
  - `Author`: campos `id`, `username`, `full_name`, `is_verified`, `profile_pic_url`, todos nullable exceto quando indicado.
  - `Comment`: `id`, `text`, `owner: Author`, `timestamp: datetime | None`, `likes_count: int | None`, `replies_count: int | None`, `replies: list[Comment]`.
  - `SentimentResult`: `label: str`, `score: float`. Conforme `planejamento.md`, o MVP deve conter apenas esses dois campos. Campos extras como `raw_label` e `raw_score` são opcionais e, se mantidos, devem ser usados apenas para debug, sem fazer parte do contrato principal.
  - `Post`: campos conforme Estrutura de Dados-Chave; `views` e `video_duration` opcionais.
- **Por quê**: Garante modelagem de domínio explícita e imutável.
- **Verificação**: Instanciar cada dataclass com dados mínimos; verificar que `frozen=True` impede mutação.

#### Passo 2.2: Implementar parser do Apify

- **Arquivos**: `social_media/src/parsers/apify.py`
- **Ação**: Implementar `parse_apify_json(raw: list[dict]) -> list[Post]`.
- **Detalhes**:
  - Mapear campos do JSON do Apify para as dataclasses.
  - Tabela de mapeamento principal (ajustar conforme JSON real):
    | JSON Apify | Domínio |
    |---|---|
    | `id` | `Post.id` |
    | `type` | `Post.type` |
    | `shortCode` | `Post.short_code` |
    | `caption` | `Post.caption` |
    | `hashtags` | `Post.hashtags` |
    | `mentions` | `Post.mentions` |
    | `url` | `Post.url` |
    | `commentsCount` | `Post.comments_count` |
    | `likesCount` | `Post.likes_count` |
    | `timestamp` | `Post.timestamp` (ISO 8601 → `datetime`) |
    | `owner` | `Post.owner` (→ `Author`) |
    | `productType` | `Post.product_type` |
    | `videoViewCount` | `Post.views` |
    | `videoDuration` | `Post.video_duration` |
    | `latestComments` | `Post.latest_comments` (→ `list[Comment]`) |
  - `childPosts` devem ser ignorados.
  - Qualquer exceção durante a conversão de um item deve ser capturada, logada e o item ignorado (tolerância).
  - `first_comment`: primeiro item de `latestComments` quando disponível; caso contrário `None`.
- **Por quê**: Isola o conhecimento do formato do Apify em um único módulo.
- **Verificação**: Rodar parser com fixture real; comparar número de `Post` gerados com número de itens válidos.

### Fase 3: Pipeline Runner e Steps

#### Passo 3.1: Criar pipeline runner

- **Arquivos**: `social_media/src/pipeline/runner.py`
- **Ação**: Implementar `run_pipeline(steps: list[Step], dfs: dict[str, pd.DataFrame], config: Config, deps: Dependencies) -> dict[str, pd.DataFrame]`.
- **Detalhes**:
  - Itera sobre `steps` na ordem fornecida.
  - Aplica cada step a `dfs` e atualiza o dicionário.
  - Loga início e fim de cada step com `step_name` e shape dos DataFrames envolvidos.
  - Não tratar exceções dentro do runner para permitir falha rápida; logging de erro fica externo.
- **Por quê**: Orquestração simples e transparente das transformações.
- **Verificação**: Criar steps dummy que adicionam uma coluna; verificar que o DataFrame final possui as colunas esperadas.

#### Passo 3.2: Criar step de parse

- **Arquivos**: `social_media/src/pipeline/steps/parse.py`
- **Ação**: Implementar `parse_step(dfs, config, deps) -> dict` que lê `raw_json` e popula `posts` e `comments`.
- **Detalhes**:
  - Espera que `dfs["raw_json_path"]` exista (caminho do JSON) ou receba `raw_json` diretamente.
  - Lê o JSON, converte via `parse_apify_json`.
  - Cria DataFrame `posts` a partir de `list[Post]` usando `dataclasses.asdict` (com flattening de `owner` e excluindo `latest_comments`).
  - Cria DataFrame `comments` com uma linha por comentário, incluindo `post_id` e flattening de `owner`.
  - Adiciona ambos ao dicionário `dfs`.
- **Por quê**: Ponto de entrada do pipeline; separa leitura de processamento.
- **Verificação**: Contar linhas de `posts` e `comments` e comparar com fixture.

#### Passo 3.3: Criar step de features de post

- **Arquivos**: `social_media/src/pipeline/steps/post_features.py`, `social_media/src/metrics/engagement.py`, `social_media/src/metrics/caption.py`
- **Ação**: Calcular métricas de engajamento (grupo 1) e features de legenda (grupo 4) para cada post.
- **Detalhes**:
  - Módulo `metrics/engagement.py`:
    - `num_likes(df: pd.DataFrame) -> pd.Series`
    - `num_comentarios(df: pd.DataFrame) -> pd.Series`
    - `engagement_rate(likes: pd.Series, comments: pd.Series, views: pd.Series) -> pd.Series` — `np.where(views.notna() & (views > 0), (likes+comments)/views, np.nan)`.
    - `comments_per_view(comments: pd.Series, views: pd.Series) -> pd.Series` — similar ao anterior.
    - `comments_per_like(comments: pd.Series, likes: pd.Series) -> pd.Series` — `np.where(likes.notna() & (likes > 0), comments/likes, np.nan)`.
  - Módulo `metrics/caption.py`:
    - `caption_word_count(caption: pd.Series) -> pd.Series`
    - `caption_char_count(caption: pd.Series) -> pd.Series`
    - `caption_emoji_count(caption: pd.Series) -> pd.Series`
    - `has_hashtags(hashtags: pd.Series) -> pd.Series`
    - `has_mentions(mentions: pd.Series) -> pd.Series`
    - `has_cta(caption: pd.Series) -> pd.Series` — regex com `"link na bio"`, `"clique"`, `"swipe up"`, `"saiba mais"`, `"confira"`, etc.
    - `hashtag_count(hashtags: pd.Series) -> pd.Series`
    - `mention_count(mentions: pd.Series) -> pd.Series`
  - Step `post_features.py` invoca as funções e adiciona colunas ao DataFrame `posts`.
- **Por quê**: Métricas puras e testáveis isoladamente; step apenas as orquestra.
- **Verificação**: Testar funções individualmente com casos conhecidos; conferir colunas no DataFrame.

#### Passo 3.4: Criar step de features de comentário

- **Arquivos**: `social_media/src/pipeline/steps/comment_features.py`, `social_media/src/metrics/comment.py`, `social_media/src/nlp/sentiment.py`
- **Ação**: Calcular `word_count`, `is_qualified`, `is_question`, `sentiment_label` e `sentiment_score` para cada comentário.
- **Detalhes**:
  - Módulo `metrics/comment.py`:
    - `word_count(text: pd.Series) -> pd.Series` — `text.fillna("").str.split().str.len()`.
    - `is_qualified(word_count: pd.Series, min_words: int) -> pd.Series`.
    - `is_question(text: pd.Series) -> pd.Series` — `text.fillna("").str.contains(r"\?")`.
  - Módulo `nlp/sentiment.py`:
    - `analyze_sentiment(text: str, analyzer: Callable[[str], SentimentResult]) -> SentimentResult`
    - `map_label(raw_label: str) -> str` — mapeia rótulos do modelo (`1 star`..`5 stars`) para `"negativo"`, `"neutro"`, `"positivo"`.
      - 1-2 estrelas → `"negativo"`
      - 3 estrelas → `"neutro"`
      - 4-5 estrelas → `"positivo"`
    - `map_score(raw_score: float, raw_label: str) -> float` — normaliza para escala 0..1 ou -1..1.
  - Step `comment_features.py` aplica as métricas e o sentimento em batch/lista; fallback para neutro com score 0.5 caso o analisador falhe para um texto específico.
- **Por quê**: NLP isolado permite mock fácil nos testes.
- **Verificação**: Mockar analisador; verificar que labels e scores são atribuídos corretamente.

#### Passo 3.5: Criar step de timing

- **Arquivos**: `social_media/src/pipeline/steps/timing.py`, `social_media/src/metrics/timing.py`
- **Ação**: Calcular `post_hour`, `post_weekday`, `post_period` e gerar agregações por hora e por dia da semana.
- **Detalhes**:
  - Módulo `metrics/timing.py`:
    - `post_hour(ts: pd.Series) -> pd.Series`
    - `post_weekday(ts: pd.Series) -> pd.Series` — 0=segunda, 6=domingo.
    - `post_period(ts: pd.Series) -> pd.Series` — categorias "Madrugada", "Manhã", "Tarde", "Noite".
    - `aggregate_by_hour(posts: pd.DataFrame) -> pd.DataFrame` — colunas `posts`, `avg_likes`, `avg_comments`, `avg_comments_per_like`.
    - `aggregate_by_weekday(posts: pd.DataFrame) -> pd.DataFrame` — mesmas colunas.
  - Step `timing.py` adiciona colunas a `posts` e cria `timing_by_hour` e `timing_by_weekday` no dicionário.
- **Por quê**: Satisfaz grupo 7 de métricas e fornece dados para gráficos de timing.
- **Verificação**: Conferir número de linhas nas agregações e valores médios em fixture conhecida.

### Fase 4: Exportadores

#### Passo 4.1: Criar exportador XLSX

- **Arquivos**: `social_media/src/exporters/xlsx.py`
- **Ação**: Implementar `export_xlsx(dfs: dict[str, pd.DataFrame], output_dir: Path) -> Path`.
- **Detalhes**:
  - Abas obrigatórias: `Posts`, `Comments`, `Timing_Hour`, `Timing_Weekday`.
  - Aba `Quality` como stub: chama `build_quality_report(dfs) -> pd.DataFrame` que levanta `NotImplementedError`.
  - Estilização com `openpyxl`:
    - Cabeçalhos em negrito.
    - Autoajuste de largura de colunas.
    - Filtros e freeze panes na primeira linha.
  - Salva em `output_dir / "metrics.xlsx"`.
- **Por quê**: Entregável principal do MVP em formato legível.
- **Verificação**: Abrir arquivo gerado e verificar abas, estilos e filtros.

#### Passo 4.2: Criar exportador PNG

- **Arquivos**: `social_media/src/exporters/png.py`, `social_media/src/charts/overview.py`, `social_media/src/charts/captions.py`, `social_media/src/charts/timing.py`
- **Ação**: Implementar `export_charts(dfs: dict[str, pd.DataFrame], output_dir: Path) -> list[Path]`.
- **Detalhes**:
  - Módulo `charts/overview.py`:
    - `plot_likes_comments_timeline(posts: pd.DataFrame) -> Figure`
    - `plot_top_posts_engagement(posts: pd.DataFrame, top_n: int = 10) -> Figure` — usa `engagement_rate` quando disponível; fallback para `comments_per_like`.
    - `plot_posts_by_type(posts: pd.DataFrame) -> Figure`
  - Módulo `charts/captions.py`:
    - `plot_caption_word_count_vs_engagement(posts: pd.DataFrame) -> Figure` — scatter `caption_word_count` vs `comments_per_like`.
  - Módulo `charts/timing.py`:
    - `plot_engagement_heatmap_hour_weekday(posts: pd.DataFrame) -> Figure`
    - `plot_avg_likes_comments_by_weekday(timing_by_weekday: pd.DataFrame) -> Figure`
  - `png.py` salva cada figura em `output_dir / f"{chart_name}.png"` com `bbox_inches="tight"` e `dpi=config.chart_dpi`.
  - Nomes exatos dos 6 arquivos PNG do MVP:
    - `likes_comments_timeline.png`
    - `top_posts_engagement.png`
    - `posts_by_type.png`
    - `caption_word_count_vs_engagement.png`
    - `engagement_heatmap_hour_weekday.png`
    - `avg_likes_comments_by_weekday.png`
- **Por quê**: Visualizações diretamente ligadas às métricas do MVP.
- **Verificação**: Verificar que todos os arquivos PNG listados acima existem após execução.

### Fase 5: Extração e Orquestração

#### Passo 5.1: Mover extração do Apify para módulo dedicado

- **Arquivos**: `social_media/src/extract/apify.py`
- **Ação**: Implementar `async def extract(links: list[str], config: Config, run_id: str) -> Path`.
- **Detalhes**:
  - Recebe lista de URLs, `Config` e `run_id`.
  - Cria `ApifyClientAsync(config.apify_token)`.
  - Monta `run_input` com `directUrls`, `resultsType="posts"`, `resultsLimit`, etc.
  - Chama o ator e aguarda `call()`.
  - Lista itens do dataset e salva em `config.data_dir / f"raw_{run_id}.json"`.
  - Retorna `Path` do JSON salvo.
  - Tolerância: se `call()` retornar `None`, logar erro e levantar `RuntimeError`.
- **Por quê**: Isola a dependência externa e permite testes com mock.
- **Verificação**: Mockar `ApifyClientAsync` e verificar que o JSON é salvo corretamente.

#### Passo 5.2: Reescrever orquestradora principal

- **Arquivos**: `social_media/src/main.py`
- **Ação**: Reescrever `main()` para executar o fluxo completo: extract → pipeline → export.
- **Detalhes**:
  ```python
  async def main() -> None:
      run_id = str(uuid4())
      set_run_id(run_id)
      configure_logging()

      config = build_config()
      deps = build_dependencies(config)

      links = read_links(Path("links.txt"))
      raw_json_path = await extract(links, config, run_id)

      initial_dfs = {"raw_json_path": raw_json_path}
      steps = [
          parse_step,
          post_features_step,
          comment_features_step,
          timing_step,
      ]
      dfs = run_pipeline(steps, initial_dfs, config, deps)

      output_root = config.output_dir / run_id
      export_xlsx(dfs, output_root)
      export_charts(dfs, output_root / "charts")
  ```
  - `read_links(path: Path) -> list[str]` lê o arquivo indicado, remove linhas vazias e faz strip. No MVP o caminho é hardcoded como `Path("links.txt")` no diretório raiz do projeto, não precisando estar em `Config`.
- **Por quê**: Ponto único de execução, orquestração clara e observável.
- **Verificação**: Executar `python -m social_media.src.main` e verificar que arquivos XLSX e PNGs são criados.

### Fase 6: Testes

#### Passo 6.1: Criar fixtures

- **Arquivos**: `social_media/tests/fixtures/real_sample.json`, `social_media/tests/fixtures/synthetic_posts.json`
- **Ação**: Gerar fixtures representativas.
- **Detalhes**:
  - `real_sample.json`: subconjunto do JSON real (mínimo 2 posts com comentários).
  - `synthetic_posts.json`: posts de múltiplos tipos (`Image`, `Video`, `Carousel`), com e sem views, com e sem comentários, com e sem caption.
- **Por quê**: Base para testes determinísticos.
- **Verificação**: Parser consegue ler ambas as fixtures sem exceções.

#### Passo 6.2: Criar testes unitários

- **Arquivos**: `social_media/tests/test_parser.py`, `social_media/tests/test_metrics.py`, `social_media/tests/test_pipeline.py`
- **Ação**: Implementar testes unitários com pytest.
- **Detalhes**:
  - `test_parser.py`: validar mapeamento de campos, parsing de `latestComments`, ignoring de `childPosts`, tolerância a itens malformados.
  - `test_metrics.py`: testar funções de `engagement.py`, `caption.py`, `comment.py`, `timing.py` com valores conhecidos.
  - `test_pipeline.py`: testar `run_pipeline` com steps dummy; testar cada step real com fixtures; garantir que DataFrames resultantes possuem colunas esperadas.
- **Por quê**: Garantir comportamento correto em refatorações futuras.
- **Verificação**: `pytest social_media/tests/` passa.

#### Passo 6.3: Criar testes de integração

- **Arquivos**: `social_media/tests/test_integration.py`
- **Ação**: Executar pipeline completo com fixtures e mock de sentiment analyzer.
- **Detalhes**:
  - Carregar fixture sintética.
  - Rodar `run_pipeline` com steps reais.
  - Verificar existência de todas as abas do XLSX e todos os PNGs ao chamar `export_xlsx` e `export_charts`.
  - Mockar `Dependencies.get_sentiment_analyzer` para retornar label fixo.
- **Por quê**: Valida que todos os módulos se integram corretamente.
- **Verificação**: Teste passa e arquivos temporários são gerados.

#### Passo 6.4: Realizar testes manuais

- **Arquivos**: `social_media/src/main.py`
- **Ação**: Executar a orquestradora com `links.txt` real e inspecionar saídas.
- **Detalhes**:
  - Verificar logs estruturados.
  - Validar XLSX (abas, colunas, estilos).
  - Validar PNGs (legibilidade, títulos, eixos).
  - Verificar que posts sem views usam `comments_per_like` corretamente.
- **Por quê**: Captura problemas de dados reais não cobertos por fixtures.
- **Verificação**: Execução completa sem exceções e outputs conforme esperado.

## Casos de Borda e Tratamento de Erros

| Caso de borda | Comportamento esperado |
|---|---|
| Dados ausentes em campos opcionais (`caption`, `likes_count`, etc.) | Campo vira `None` ou lista vazia; métricas dependentes retornam `np.nan` ou `False`. |
| Divisão por zero (`engagement_rate` com `views == 0`) | Resultado `np.nan`. |
| Comentários sem texto (`text` vazio ou `None`) | `word_count = 0`, `is_qualified = False`, `is_question = False`, sentimento = `neutro` com score padrão. |
| Posts sem views (imagens/carrosséis) | Usar `comments_per_like` como métrica de conversão nos gráficos/rankings. |
| Posts sem comentários | DataFrame `comments` vazio; agregações de timing ainda funcionam; gráficos de comentários devem ser omitidos ou mostrar mensagem. |
| Falha no modelo NLP para um comentário | Logar exceção; atribuir `sentiment_label="neutro"` e `sentiment_score=0.5` para aquele comentário. |
| JSON malformado ou campo inesperado | Parser loga e ignora o item; execução continua com itens válidos. |
| Timestamps inválidos | `timestamp` vira `None`; features de timing retornam `NaT`/`-1`/`"unknown"`. |
| `links.txt` vazio | `extract` recebe lista vazia; Apify retorna dataset vazio; pipeline gera DataFrames vazios e exporta XLSX/PNGs vazios com mensagem apropriada. |
| Falha na chamada ao Apify (`call()` retorna `None`) | Levantar `RuntimeError` com mensagem clara no log. |
| Dependência `transformers` não instalada | `build_dependencies` loga erro e levanta `ImportError` somente quando `get_sentiment_analyzer` for chamado. |

## Estratégia de Testes

### Testes Unitários

- **Parser**: mapeamento completo de campos, parsing recursivo de respostas, tolerância a itens malformados.
- **Métricas**: valores esperados para engajamento, legenda, comentários e timing.
- **Pipeline runner**: ordem de execução, passagem de `config` e `deps`, imutabilidade opcional.
- **NLP**: mapeamento de labels e scores do modelo.

### Testes de Integração

- Pipeline completo com fixture sintética e mock de sentiment analyzer.
- Exportadores XLSX e PNG com dados reais de fixture.
- Extração Apify mockada.

### Testes Manuais

- Execução de ponta a ponta com `links.txt` real.
- Inspeção visual dos gráficos.
- Inspeção do XLSX (formatação, filtros, abas).
- Revisão dos logs estruturados.

### Critérios de Cobertura Mínimos

- 100% das funções de métricas testadas com pelo menos 2 casos cada.
- Todas as branches de fallback (dados ausentes, divisão por zero) cobertas.
- Pelo menos 1 teste de integração do fluxo completo.

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Dependências pesadas do `transformers`/`torch` dificultam instalação | Média | Alto | Lazy loading; mock de sentiment analyzer para testes; documentar requisitos de hardware. |
| Instabilidade ou indisponibilidade do Apify | Média | Alto | Cache do JSON extraído; testes com fixtures; retry com backoff na chamada async. |
| Dados malformados ou mudança no schema do Apify | Média | Médio | Parser tolerante; logs detalhados; atualização periódica das fixtures. |
| Performance ruim com grandes volumes de posts/comentários | Média | Médio | Processamento vetorizado com pandas; batch no sentiment analysis; possibilidade de amostragem futura. |
| Divisão por zero ou NaNs inesperados em gráficos | Baixa | Médio | Tratamento de bordas nas funções de métricas; validação de dados antes de plotar. |
| Qualidade de dados não implementada no MVP | Baixa | Baixo | Stub explícito com `NotImplementedError`; backlog documentado. |

---

**Arquivo criado em:** `/home/gabriel/pessoal/projetos/coleta_de_dados/implementacao.md`

**Número aproximado de linhas:** 600
