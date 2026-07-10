# 📈 Métricas selecionadas (insights acionáveis)

> Lista enxuta de métricas que respondem a perguntas de negócio e permitem decisões práticas sobre conteúdo, audiência e engajamento em redes sociais.

---

## 1. Engajamento e alcance (por post)

- `engagement_rate` = (likes + comentários) / visualizações
- `comments_per_view` = comentários / visualizações
- `num_likes`
- `num_comentarios`
- `visualizacoes`

**O que responde:** Qual conteúdo gera mais interação proporcional? A conversa está crescendo em relação ao alcance?

---

## 2. Conversação e qualidade do diálogo (por post)

- `discussion_index` = respostas / comentários
- `avg_reply_depth`
- `max_reply_depth`
- `qualified_comment_rate` = % de comentários qualificados (> X palavras)
- `question_comment_rate` = % de comentários com perguntas
- `sent_positivo_share`, `sent_neutro_share`, `sent_negativo_share`

**O que responde:** O post gera debate profundo? Os comentários são relevantes? Qual a percepção do público?

---

## 3. Comunidade e recorrência (por post)

- `community_index` = comentadores recorrentes / comentadores únicos
- `recurring_comment_share` = % de comentários de usuários recorrentes
- `new_commenter_share` = % de comentários de usuários novos
- `verified_commenter_rate` = % de comentadores verificados

**O que responde:** A base de comentadores está ficando fiel? O conteúdo atrai novos usuários? Há presença de perfis relevantes?

---

## 4. Features de legenda (por post)

- `caption_word_count`, `caption_char_count`, `caption_emoji_count`, `caption_cta_count`
- Flags binárias: `has_hashtags`, `has_mentions`, `has_coauthors`, `has_location`, `has_cta`
- Contagens: `hashtag_count`, `mention_count`, `coauthor_count`
- Timestamp: `post_hour`, `post_weekday`, `post_period`

**O que responde:** Quais características da legenda e momento de publicação estão associados a melhor performance?

---

## 5. Features de comentários (por comentário)

- `word_count`, `is_qualified`, `is_question`
- `sentiment_label`, `sentiment_score`
- `emotion_label`
- `replies_total`, `reply_depth_max`
- `is_verified`

**O que responde:** Quais comentários merecem atenção imediata? Quais emoções e sentimentos o conteúdo desperta?

---

## 6. Agregações por tipo de conteúdo

- `posts`, `num_likes`, `num_comentarios`, `visualizacoes`
- `engagement_rate`, `comments_per_view`
- `qualified_comment_rate`, `discussion_index`, `community_index`, `new_commenter_share`

**O que responde:** Quais formatos, temas ou tipos de conteúdo merecem mais investimento?

---

## 7. Análise de timing

### Por hora

- `posts`, `avg_likes`, `avg_comments`, `avg_views`, `avg_engagement_rate`, `avg_qualified_comment_rate`

### Por dia da semana

- `posts`, `avg_likes`, `avg_comments`, `avg_views`, `avg_engagement_rate`, `avg_discussion_index`

**O que responde:** Quais são os melhores horários e dias para publicar?

---

## 8. Impacto de features binárias (`feature_impact_table.csv`)

Compara posts **COM** vs **SEM** cada feature, calculando `lift_pct` para:

- **Features:** `has_hashtags`, `has_mentions`, `has_coauthors`, `has_location`, `has_cta`
- **Métricas:** `num_likes`, `num_comentarios`, `visualizacoes`, `engagement_rate`, `discussion_index`, `qualified_comment_rate`, `community_index`, `new_commenter_share`

**O que responde:** Cada elemento realmente aumenta o engajamento? Qual o ganho percentual de usar CTA, hashtag, menção etc.?

---

## 9. Performance de hashtags

- `posts`, `avg_likes`, `avg_comments`, `avg_views`, `avg_engagement_rate`, `avg_comments_per_view`, `avg_qualified_comment_rate`
- `saturacao_interna` (nicho / média / alta)
- Co-ocorrência entre hashtags: `coocorrencias`, `posts`, `avg_comments`, `avg_engagement_rate`

**O que responde:** Quais hashtags performam melhor? Quais combinações de hashtags geram mais engajamento?

---

## 10. Performance de coautores

- `posts`, `avg_comments`, `avg_views`, `avg_engagement_rate`, `avg_discussion_index`, `avg_qualified_comment_rate`

**O que responde:** Quais parcerias e coautores realmente agregam resultado?

---

## 11. Audiência e comentaristas

- `total_owner_rows`, `owners_unicos`, `percent_verified`
- Top comentaristas: `comentarios`, `posts_distintos`, `comentarios_qualificados`, `taxa_perguntas`

**O que responde:** Quem são os principais interagentes? Quem são potenciais embaixadores, evangelistas ou críticos recorrentes?

---

## 12. Vídeo

- `video_posts`
- `corr_duracao_visualizacoes`, `corr_duracao_comments_per_view`
- `media_duracao`, `mediana_duracao`

**O que responde:** Qual a duração ideal de vídeo? Duração influencia visualizações e comentários?

---

## 13. NLP / Tópicos

- Top termos de legendas (`caption_top_terms.csv`)
- Top termos de comentários (`comment_top_terms.csv`)
- Tópicos via LDA para legendas (`caption_topics.csv`)
- Tópicos via LDA para comentários (`comment_topics.csv`)

**O que responde:** Quais palavras e temas ressoam mais com a audiência? O que as pessoas estão realmente comentando?

---

## 14. Qualidade de dados

- `comments_rows_loaded`, `comments_coverage_ratio`
- Avisos sobre discrepância entre comentários carregados e `num_comentarios`
- Avisos sobre posts sem visualizações válidas

**O que responde:** Os dados são confiáveis o suficiente para embasar decisões?
