# 📊 Gráficos selecionados (dashboards acionáveis)

> Visualizações diretamente ligadas às métricas úteis definidas em `metrics.md`. O foco é permitir decisões rápidas sobre conteúdo, timing, audiência e qualidade do engajamento.

---

## 1. Visão geral de performance

- **Linha temporal:** `engagement_rate`, `comments_per_view`, `num_likes`, `num_comentarios`, `visualizacoes` ao longo do tempo.
- **Ranking de posts:** top 10 posts por `engagement_rate`, `comments_per_view` e `qualified_comment_rate`.
- **Distribuição de posts:** volume de posts por tipo de conteúdo com média de `engagement_rate`.

---

## 2. Conversação e qualidade do diálogo

- **Barras:** `discussion_index`, `qualified_comment_rate`, `question_comment_rate` por post ou por tipo de conteúdo.
- **Treemap / sunburst:** profundidade de respostas (`avg_reply_depth`, `max_reply_depth`).
- **Pizza / stacked bar:** shares de sentimento (`sent_positivo_share`, `sent_neutro_share`, `sent_negativo_share`).

---

## 3. Comunidade e recorrência

- **Linha temporal:** evolução de `community_index`, `recurring_comment_share` e `new_commenter_share`.
- **Barras empilhadas:** proporção de comentários de recorrentes vs. novos por post.
- **Tabela:** comentadores verificados mais ativos (`verified_commenter_rate` + top perfis).

---

## 4. Otimização de legendas

- **Barras:** `lift_pct` de cada feature binária (`has_hashtags`, `has_mentions`, `has_coauthors`, `has_location`, `has_cta`) sobre `engagement_rate` e `comments_per_view`.
- **Scatter plot:** `caption_word_count` / `caption_char_count` / `caption_emoji_count` vs. `engagement_rate`.
- **Heatmap:** performance média por `post_hour` × `post_weekday`.

---

## 5. Análise de timing

- **Heatmap:** `avg_engagement_rate` por hora do dia e dia da semana.
- **Linhas:** `avg_likes`, `avg_comments`, `avg_views`, `avg_qualified_comment_rate` por `post_hour`.
- **Barras:** `avg_engagement_rate` e `avg_discussion_index` por dia da semana.

---

## 6. Performance de hashtags

- **Ranking:** top hashtags por `avg_engagement_rate` e `avg_comments_per_view`.
- **Scatter plot:** `saturacao_interna` vs. `avg_engagement_rate`.
- **Grafo / matriz de calor:** co-ocorrência entre hashtags com média de engajamento.

---

## 7. Performance de coautores

- **Ranking:** coautores por `avg_engagement_rate`, `avg_comments`, `avg_views`.
- **Barras comparativas:** posts com coautor vs. sem coautor (`feature_impact_table.csv`).

---

## 8. Audiência e comentaristas estratégicos

- **Tabela:** top comentaristas com `comentarios`, `posts_distintos`, `comentarios_qualificados`, `taxa_perguntas`.
- **Indicadores:** `owners_unicos`, `percent_verified`.
- **Tag cloud ou ranking:** perfis verificados que mais interagem.

---

## 9. Vídeo

- **Scatter plot:** duração do vídeo vs. `visualizacoes` e vs. `comments_per_view`.
- **Indicadores:** `media_duracao`, `mediana_duracao`, `corr_duracao_visualizacoes`, `corr_duracao_comments_per_view`.
- **Histograma:** distribuição de duração dos vídeos de maior performance.

---

## 10. NLP / Tópicos

- **Word cloud:** principais termos de legendas (`caption_top_terms.csv`).
- **Word cloud:** principais termos de comentários (`comment_top_terms.csv`).
- **Barras:** tópicos LDA com peso e termos principais para legendas e comentários.
- **Comparativo:** termos mais frequentes em comentários positivos vs. negativos.

---

## 11. Qualidade e confiabilidade dos dados

- **Indicadores:** `comments_coverage_ratio`.
- **Alertas / tabela:** posts com discrepância entre comentários carregados e `num_comentarios`.
- **Alertas / tabela:** posts sem visualizações válidas.
