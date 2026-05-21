# Relatorio Executivo de Analise de Posts

## 1. Estrutura de dados identificada antes da analise
- Total de shortcodes analisados: 27
- Pastas com post_*.xlsx: 27
- Pastas com comments_*.xlsx: 23
- Pastas sem comentarios: 4
- Estrutura validada: cada pasta pode conter post, comments e commentOwner conforme disponibilidade.

## 2. Resumo da base
- Posts processados: 27
- Comentarios observados (latestComments): 146
- Usuarios unicos comentando: 129
- Percentual de owners verificados: 2.21%

## 3. Metricas principais
- Engajamento principal usado: (likes + comentarios) / visualizacoes (quando visualizacoes > 0).
- Comentarios por visualizacao usado como proxy de profundidade.
- Metricas de comunidade: indice de discussao, indice de comunidade, comentarios qualificados e taxa de perguntas.

## 4. Respostas objetivas para decisao

### 4.1 Que tipo de conteudo devo postar mais?
- Maior media de comentarios: tipo Video com 234.77 comentarios/post.
- Melhor engagement rate medio (com views): tipo Video com 21.79.

### 4.2 Como aumentar comentarios (nao so likes)?
- Lift de comentarios com CTA: -8.65%.
- Lift de comentarios com coautoria: 3321.60%.
- Lift de comentarios com hashtags: -16.61%.
- Melhor hora para comentarios: 15h (media 467.00).
- Melhor dia para comentarios: terca (media 302.00).

### 4.3 Como atrair publico mais qualificado?
- Nesta base, qualidade foi medida por: comentarios qualificados (> X palavras), taxa de perguntas e indice de comunidade.
- Lift de indice de comunidade com coautoria: n/a%.
- Lift de comentarios qualificados com CTA: -21.58%.
- Lift de novos comentaristas com mencoes (proxy interno): 2.17%.

### 4.4 Vale a pena usar coautores?
- Impacto medio em visualizacoes: n/a%.
- Impacto medio em comentarios: 3321.60%.
- Coautoria deve ser usada quando o objetivo for alcance e conversa; validar consistencia com mais posts.

### 4.5 Qual o melhor horario?
- Melhor hora para comentarios: 15h.
- Melhor hora para visualizacoes: 20h.
- Melhor dia da semana: terca.

### 4.6 Hashtags ajudam ou atrapalham?
- Lift de engagement com hashtags: 29.75%.
- Lift de comentarios com hashtags: -16.61%.
- Analise por hashtag individual e coocorrencia disponivel nas tabelas exportadas.

## 5. NLP de legendas e comentarios (leve e rapido)
- Legendas: tamanho, emojis, CTA e temas principais calculados.
- Comentarios: sentimento (positivo/negativo/neutro), emocao (raiva/entusiasmo/duvida), perguntas e temas principais.

## 6. Metricas nao mensuraveis com os dados atuais
- Distribuicao de seguidores dos comentaristas: nao disponivel.
- Privado vs publico: nao disponivel.
- Relacao seguidor/seguindo: nao disponivel.
- Tamanho da audiencia dos coautores: nao disponivel.

## 7. Top hashtags (amostra)
- #ufsm: posts=16, avg_comments=150.44, avg_engagement=23.89
- #silveira: posts=5, avg_comments=467.40, avg_engagement=32.99
- #ufsmdaquiparaomundo: posts=4, avg_comments=507.50, avg_engagement=39.36
- #souufsm: posts=4, avg_comments=5.00, avg_engagement=1.16
- #extensãouniversitária: posts=3, avg_comments=2.67, avg_engagement=n/a
- #silveiraufsm: posts=2, avg_comments=599.50, avg_engagement=37.52
- #cinema: posts=1, avg_comments=1.00, avg_engagement=0.00
- #conexoesquetransformam: posts=1, avg_comments=8.00, avg_engagement=n/a
- #conscienciaafricana: posts=1, avg_comments=13.00, avg_engagement=18.79
- #abelhas: posts=1, avg_comments=9.00, avg_engagement=n/a

## 8. Usuarios recorrentes (amostra)
- dupladedoismartinmabel: comentarios=4, posts_distintos=1, taxa_perguntas=0.00
- ufsmpm: comentarios=4, posts_distintos=1, taxa_perguntas=0.00
- djarts_8: comentarios=3, posts_distintos=2, taxa_perguntas=0.00
- albummbel: comentarios=2, posts_distintos=2, taxa_perguntas=0.00
- ateliefogo: comentarios=2, posts_distintos=2, taxa_perguntas=0.00
- elisangelapessoa46: comentarios=2, posts_distintos=2, taxa_perguntas=0.00
- geanefedrigo: comentarios=2, posts_distintos=2, taxa_perguntas=0.00
- gislaine7166: comentarios=2, posts_distintos=2, taxa_perguntas=0.00
- radiosufsm: comentarios=2, posts_distintos=2, taxa_perguntas=0.00
- claudia_m_ferrari: comentarios=2, posts_distintos=1, taxa_perguntas=0.50

## 9. Topicos de legenda
- topico_1: 2025, vagas, internacional, santa, maria, rural (lda_sklearn)
- topico_2: sobre, site, dia, link, bio, confira (lda_sklearn)
- topico_3: silveira, zeloufsm, silveirapodrao, campus, pro, caninos (lda_sklearn)
- topico_4: extensao, comunidade, cultura, campus, reitoria, 18h (lda_sklearn)

## 10. Topicos de comentarios
- topico_1: parabens, maria, santa, pena, sabe, resultado (lda_sklearn)
- topico_2: ufsm, gente, extensao, agenda, historia, deixa (lda_sklearn)
- topico_3: silveira, muito, desde, quando, hoje, bom (lda_sklearn)
- topico_4: projeto, todos, cara, animais, deus, amo (lda_sklearn)

## 11. Avisos de qualidade de dados
- Shortcode DJ1_MTEuA-i: sem visualizacoes validas para engagement por view.
- Shortcode DJ1oIOktsNX: sem visualizacoes validas para engagement por view.
- Shortcode DJ2nlbTpv68: comments carregados (6) bem abaixo de num_comentarios (830).
- Shortcode DJ48NUpJ544: sem visualizacoes validas para engagement por view.
- Shortcode DJ4ofY6Jf56: comments carregados (9) bem abaixo de num_comentarios (669).
- Shortcode DJ4ofY6Jf56: sem visualizacoes validas para engagement por view.
- Shortcode DJ4xlSdy-3m: comments carregados (8) bem abaixo de num_comentarios (62).
- Shortcode DJ4xlSdy-3m: sem visualizacoes validas para engagement por view.
- Shortcode DJ5AkVwJLXy: comments carregados (10) bem abaixo de num_comentarios (254).
- Shortcode DJ5J9TCJBVJ: comments carregados (8) bem abaixo de num_comentarios (767).
- Shortcode DJ630KnRcyp: sem visualizacoes validas para engagement por view.
- Shortcode DJ6unk6RCfx: sem visualizacoes validas para engagement por view.
- Shortcode DJ7XmcexhRk: sem visualizacoes validas para engagement por view.
- Shortcode DJ7jekBJKgG: comments carregados (6) bem abaixo de num_comentarios (432).
- Shortcode DJ90M-cvd_9: comments carregados (8) bem abaixo de num_comentarios (265).
- Shortcode DJ90M-cvd_9: sem visualizacoes validas para engagement por view.
- Shortcode DJ9NCJqOH35: comments carregados (9) bem abaixo de num_comentarios (163).
- Shortcode DJ9NCJqOH35: sem visualizacoes validas para engagement por view.
- Shortcode DJ9bfPfRMcs: comments carregados (6) bem abaixo de num_comentarios (35).
- Shortcode DKAHqt4x3uU: sem visualizacoes validas para engagement por view.
- Shortcode DKAkG0EpeK7: comments carregados (9) bem abaixo de num_comentarios (457).
- Shortcode DKHvDV_NcFc: sem visualizacoes validas para engagement por view.
- Shortcode DKK1ISuO5qS: comments carregados (5) bem abaixo de num_comentarios (51).
- Shortcode DKK1ISuO5qS: sem visualizacoes validas para engagement por view.
- Shortcode DKPaci-t7V9: sem visualizacoes validas para engagement por view.
- Shortcode DKPeLWNtI9U: comments carregados (10) bem abaixo de num_comentarios (246).

## 12. Pacote de graficos profissionais
- post_type_avg_comments: success (post_type_avg_comments.png) - ok
- timing_hour_avg_comments: success (timing_hour_avg_comments.png) - ok
- timing_weekday_avg_comments: success (timing_weekday_avg_comments.png) - ok
- top_hashtags_engagement: success (top_hashtags_engagement.png) - top_hashtags_engagement: removidos 69% de registros com NaN
- coauthor_impact_comments_views: success (coauthor_impact_comments_views.png) - ok
- quality_by_type: success (quality_by_type.png) - ok
- community_vs_quality: success (community_vs_quality.png) - ok

## 13. Arquivos gerados
- Tabelas CSV: analysis_output\tables
- Graficos PNG: analysis_output\charts