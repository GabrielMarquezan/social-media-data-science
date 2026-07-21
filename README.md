# coleta-de-dados

Pipeline de coleta e análise de dados do Instagram via Apify.

## Execução

```bash
python -m social_media.src.main
```

## Testes

```bash
pytest social_media/tests -m "not slow"
```

## Estrutura

- `social_media/src/` — código fonte
- `social_media/tests/` — testes
- `data/` — dados brutos e fixtures
- `output/` — resultados de execuções
