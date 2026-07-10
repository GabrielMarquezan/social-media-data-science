# Planejamento de implementação

## Visão geral

Transformar o script atual (`social_media/src/main.py`) em uma aplicação modular que:

1. Extrai posts do Instagram via Apify.
2. Converte o JSON em dataclasses de domínio.
3. Processa métricas e features via pipeline funcional de DataFrames.
4. Gera gráficos em PNG.
5. Exporta métricas em XLSX estilizado.

Atualmente, o código apenas extrai os dados do Instagram utilizando o Apify. Agora, devemos começar a implementar a análise de dados utilizando NLP.

## Escopo do MVP (enxuto)

- **Métricas:** grupos 1, 4, 5 e 7 de `metrics.md`.
- **Gráficos:** grupos 1, 4 e 5 de `charts.md`.
- **NLP:** sentiment analysis com `nlptown/bert-base-multilingual-uncased-sentiment`.
- **Qualidade de dados:** stubs com `raise NotImplementedError`, implementados posteriormente.

## Comportamento do código

- O código deve receber os dados extraídos do Instagram e processar as métricas definidas em `metrics.md`.
- As métricas devem ser salvas em uma tabela `.xlsx` estilizada para leitura humana.
- Os gráficos devem ser salvos em `.png`.

## Regras de implementação

- POO para modelagem de domínio, com classes `Post`, `Author`, `Comment`, `SentimentResult`, etc.
- Programação funcional para operações de processamento de dados.
- POO com injeção de dependências para configurações, fontes de dados e modelos de NLP.
- Padrão de Pipeline, onde cada etapa recebe um dicionário de DataFrames e devolve outro.

## Decisões arquiteturais

| Decisão | Escolha |
|---|---|
| Paradigma | Híbrido: POO para domínio, funcional para pipeline de DataFrames |
| Pacotes | Por responsabilidade (`domain/`, `pipeline/`, `charts/`, `exporters/`, etc.) |
| Domínio | Dataclasses (`Post`, `Author`, `Comment`) |
| Pipeline | Dict de DataFrames (`posts`, `comments`, agregações) passado por steps |
| Steps | Funções puras: `step(dfs: dict, config: Config, deps: Dependencies) -> dict` |
| Config | Constantes em `config.py`; dados sensíveis no `.env` |
| Dependências | `dependencies.py` com lazy loading do pipeline transformers |
| Logging | Módulo `logging` do Python; configuração ficará em `logging.py` |
| Tolerância | Extração tolerante; dados ausentes logam exceção e viram `None` |
| Async/sync | `extract.py` async, `analyze.py` sync, `main.py` async orquestradora |
| Type hints | Em todas as funções/classes, sem mypy no MVP |
| Subpacotes | Sem `__init__.py`; módulos serão importados diretamente |

## Estrutura de arquivos

```
social_media/
├── src/
│   ├── main.py                      # Orquestradora: extract → analyze → export
│   ├── config.py                    # Constantes de configuração
│   ├── dependencies.py              # Criação lazy de dependências injetáveis
│   ├── logging.py                   # Configuração de logging (a inserir)
│   │
│   ├── domain/
│   │   ├── author.py                # dataclass Author
│   │   ├── comment.py               # dataclass Comment
│   │   ├── post.py                  # dataclass Post (base + type)
│   │   └── sentiment.py             # dataclass SentimentResult
│   │
│   ├── parsers/
│   │   └── apify.py                 # JSON Apify → list[Post]
│   │
│   ├── pipeline/
│   │   ├── runner.py                # run_pipeline(dfs, steps, config, deps)
│   │   └── steps/
│   │       ├── parse.py             # JSON → DataFrames posts/comments
│   │       ├── post_features.py     # features de legenda + engajamento
│   │       ├── comment_features.py  # word_count, is_qualified, is_question, sentimento
│   │       └── timing.py            # agregações por hora/dia da semana
│   │
│   ├── metrics/
│   │   ├── engagement.py            # engagement_rate, comments_per_like, etc.
│   │   ├── caption.py               # caption_word_count, emoji_count, CTA flags, etc.
│   │   ├── comment.py               # word_count, is_qualified, is_question
│   │   └── timing.py                # post_hour, post_weekday, post_period
│   │
│   ├── nlp/
│   │   └── sentiment.py             # Funções puras de análise de sentimento
│   │
│   ├── charts/
│   │   ├── overview.py              # timeline, ranking, posts by type
│   │   ├── captions.py              # scatter caption vs engagement
│   │   └── timing.py                # heatmap + barras por dia da semana
│   │
│   ├── exporters/
│   │   ├── xlsx.py                  # Estilização e salvamento do XLSX
│   │   └── png.py                   # Salvamento dos gráficos
│   │
│   └── extract/
│       └── apify.py                 # Extração async do Apify
│
├── tests/
│   ├── fixtures/
│   │   ├── real_sample.json         # Subconjunto do JSON real
│   │   └── synthetic_posts.json     # Posts de múltiplos tipos
│   ├── test_parser.py
│   ├── test_metrics.py
│   └── test_pipeline.py
│
├── links.txt
└── ...
```

## Modelagem de domínio

```python
@dataclass
class Author:
    id: str | None
    username: str | None
    full_name: str | None
    is_verified: bool | None
    profile_pic_url: str | None

@dataclass
class Comment:
    id: str
    text: str
    owner: Author
    timestamp: datetime | None
    likes_count: int | None
    replies_count: int | None
    replies: list[Comment] = field(default_factory=list)

@dataclass
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
    # Campos específicos por tipo (None quando não aplicável)
    views: int | None = None
    video_duration: float | None = None
```

**Notas:**
- `childPosts` são ignorados no domínio.
- `views` e `video_duration` são opcionais por tipo de post.
- Posts sem `views` (imagens e carrosséis) usam `comments_per_like` como métrica de conversão.

## Métricas do MVP

### 1. Engajamento (por post)

| Métrica | Fórmula |
|---|---|
| `num_likes` | `likes_count` |
| `num_comentarios` | `comments_count` |
| `engagement_rate` | `(likes + comments) / views` — apenas quando `views` existe |
| `comments_per_view` | `comments / views` — apenas quando `views` existe |
| `comments_per_like` | `comments / likes` — quando não há `views` |

### 2. Features de legenda (por post)

| Métrica | Descrição |
|---|---|
| `caption_word_count` | Número de palavras na legenda |
| `caption_char_count` | Número de caracteres na legenda |
| `caption_emoji_count` | Número de emojis na legenda |
| `has_hashtags` | `True` se `hashtags` não vazio |
| `has_mentions` | `True` se `mentions` não vazio |
| `has_cta` | `True` se legenda contiver CTA (regra inicial: "link na bio", "clique", etc.) |
| `hashtag_count` | `len(hashtags)` |
| `mention_count` | `len(mentions)` |
| `post_hour` | Hora do timestamp |
| `post_weekday` | Dia da semana do timestamp |
| `post_period` | Madrugada (0–5), Manhã (6–11), Tarde (12–17), Noite (18–23) |

### 3. Features de comentários (por comentário)

| Métrica | Descrição |
|---|---|
| `word_count` | Número de palavras |
| `is_qualified` | `True` se `word_count >= QUALIFIED_COMMENT_MIN_WORDS` (padrão: 5) |
| `is_question` | `True` se texto contiver `?` |
| `sentiment_label` | `positivo`, `neutro` ou `negativo` |
| `sentiment_score` | Score mapeado do modelo |

### 4. Agregações de timing

- `timing_by_hour`: `posts`, `avg_likes`, `avg_comments`, `avg_comments_per_like`
- `timing_by_weekday`: `posts`, `avg_likes`, `avg_comments`, `avg_comments_per_like`

## Gráficos do MVP

1. `likes_comments_timeline.png` — likes + comments ao longo do tempo.
2. `top_posts_engagement.png` — top 10 posts por `engagement_rate` (ou `comments_per_like`).
3. `posts_by_type.png` — volume de posts por tipo com média de `comments_per_like`.
4. `caption_word_count_vs_engagement.png` — scatter `caption_word_count` vs `comments_per_like`.
5. `engagement_heatmap_hour_weekday.png` — heatmap `avg_comments_per_like` por hora × dia.
6. `avg_likes_comments_by_weekday.png` — barras de `avg_likes` e `avg_comments` por dia.

## Outputs

### XLSX

Abas por grupo:

- `Posts`
- `Comments`
- `Timing_Hour`
- `Timing_Weekday`
- `Quality` (stub: `NotImplementedError`)

Estilização: cabeçalhos em negrito, autofit de colunas, filtros e freeze panes.

### PNGs

Salvos em `output/{run_id}/charts/`.

## Fluxo de execução

```python
# main.py
async def main():
    links = read_links("links.txt")
    raw_json_path = await extract(links, output_dir=Path("data"))

    config = Config()  # constantes de config.py
    deps = build_dependencies(config)  # lazy loading do sentiment analyzer

    dfs = run_pipeline(raw_json_path, config, deps)

    export_xlsx(dfs, output_dir=Path("output") / run_id)
    export_charts(dfs, output_dir=Path("output") / run_id / "charts")
```

## Testes

- `test_parser.py`: JSON real e sintético → dataclasses.
- `test_metrics.py`: funções individuais de métricas.
- `test_pipeline.py`: runner e steps.
- Mock do sentiment analyzer para testes rápidos sem carregar transformers.

## Dependências

**Manter:**

- `pandas`, `openpyxl`, `matplotlib`
- `transformers`, `torch`
- `scikit-learn`, `apify-client`, `python-dotenv`, `pytest`

**Remover do MVP:**

- `sentence-transformers`
- `sentencepiece`
- `tiktoken`
- `protobuf`

## Ordem de implementação

1. **Domínio + Parser**: dataclasses e conversão do JSON.
2. **Config + Dependências**: `config.py`, `dependencies.py`, lazy loading.
3. **Pipeline runner**: `run_pipeline` e estrutura de steps.
4. **Métricas**: steps de post, comentário e timing.
5. **NLP**: funções puras de sentimento.
6. **Exportadores**: XLSX e PNG.
7. **Extração**: mover Apify para `extract/apify.py`.
8. **Orquestração**: reescrever `main.py`.
9. **Testes**: fixtures e testes unitários.
