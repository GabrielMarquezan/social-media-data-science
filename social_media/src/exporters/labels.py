"""Rótulos em português (pt-BR) para os artefatos visíveis ao usuário final.

Aplicados apenas na camada de exportação: o pipeline interno mantém os nomes
técnicos das colunas, e a tradução acontece na geração do XLSX (que alimenta
as tabelas e os downloads da interface web).
"""

import pandas as pd

# Nome lógico do DataFrame -> nome da aba no metrics.xlsx (máx. 31 caracteres)
SHEET_NAMES: dict[str, str] = {
    "posts": "Posts",
    "comments": "Comentários",
    "timing_by_hour": "Por_Hora",
    "timing_by_weekday": "Por_Dia_da_Semana",
    "content_by_type": "Por_Tipo",
    "quality": "Qualidade",
    "caption_top_terms": "Termos_da_Legenda",
    "comment_top_terms": "Termos_dos_Comentários",
    "comment_topics": "Tópicos_dos_Comentários",
    "sentiment_term_comparison": "Termos_por_Sentimento",
}

# Nome técnico da coluna -> rótulo em pt-BR (colunas não mapeadas são mantidas)
COLUMN_LABELS: dict[str, str] = {
    # Identificação e conteúdo do post
    "id": "id",
    "type": "tipo",
    "short_code": "código_curto",
    "caption": "legenda",
    "hashtags": "hashtags",
    "mentions": "menções",
    "url": "url",
    "first_comment": "primeiro_comentário",
    "timestamp": "data_publicação",
    "product_type": "tipo_de_produto",
    "video_duration": "duração_do_vídeo_s",
    # Métricas do post
    "likes_count": "curtidas",
    "num_likes": "num_curtidas",
    "comments_count": "comentários_totais",
    "num_comentarios": "num_comentários",
    "views": "visualizações",
    "visualizacoes": "visualizações",
    "engagement_rate": "taxa_de_engajamento",
    "comments_per_view": "comentários_por_visualização",
    "comments_per_like": "comentários_por_curtida",
    "caption_word_count": "palavras_na_legenda",
    "caption_char_count": "caracteres_na_legenda",
    "caption_emoji_count": "emojis_na_legenda",
    "has_hashtags": "tem_hashtags",
    "has_mentions": "tem_menções",
    "has_cta": "tem_chamada_para_ação",
    "hashtag_count": "num_hashtags",
    "mention_count": "num_menções",
    # Autor (posts e comentários)
    "owner_id": "autor_id",
    "owner_username": "autor_usuário",
    "owner_full_name": "autor_nome",
    "owner_is_verified": "autor_verificado",
    "owner_profile_pic_url": "autor_foto_url",
    # Conversação
    "discussion_index": "índice_de_discussão",
    "avg_reply_depth": "profundidade_média_das_respostas",
    "max_reply_depth": "profundidade_máxima_das_respostas",
    "qualified_comment_rate": "taxa_de_comentários_qualificados",
    "question_comment_rate": "taxa_de_comentários_com_pergunta",
    "sent_positivo_share": "percentual_positivo",
    "sent_neutro_share": "percentual_neutro",
    "sent_negativo_share": "percentual_negativo",
    # Timing
    "post_hour": "hora_da_publicação",
    "post_weekday": "dia_da_semana_da_publicação",
    "post_period": "período_da_publicação",
    # Comentários
    "text": "texto",
    "replies_count": "num_respostas",
    "post_id": "post_id",
    "parent_id": "comentário_pai_id",
    "depth": "profundidade",
    "word_count": "num_palavras",
    "is_qualified": "qualificado",
    "is_question": "é_pergunta",
    "sentiment_label": "sentimento",
    "sentiment_score": "confiança_do_sentimento",
    # Agregações
    "posts": "posts",
    "avg_likes": "média_de_curtidas",
    "avg_comments": "média_de_comentários",
    "avg_views": "média_de_visualizações",
    "avg_engagement_rate": "média_da_taxa_de_engajamento",
    "avg_comments_per_view": "média_de_comentários_por_visualização",
    "avg_comments_per_like": "média_de_comentários_por_curtida",
    "avg_qualified_comment_rate": "média_da_taxa_de_comentários_qualificados",
    "avg_discussion_index": "média_do_índice_de_discussão",
    "community_index": "índice_de_comunidade",
    "new_commenter_share": "percentual_de_novos_comentaristas",
    # Qualidade
    "check": "verificação",
    "value": "valor",
    "status": "status",
    # NLP
    "term": "termo",
    "relevancia": "relevância",
    "count": "ocorrências",
    "topic_id": "tópico_id",
    "topic_label": "tópico",
    "keyword": "palavra_chave",
    "sentiment": "sentimento",
}

# Valores da coluna "verificação" da aba de qualidade
QUALITY_CHECK_LABELS: dict[str, str] = {
    "total_posts": "Total de posts",
    "posts_without_valid_views": "Posts sem visualizações válidas",
    "posts_without_timestamp": "Posts sem data de publicação",
    "total_comments": "Total de comentários",
    "comments_without_text": "Comentários sem texto",
    "posts_with_comment_count_discrepancy": "Posts com divergência no nº de comentários",
    "comments_coverage_ratio": "Cobertura de comentários",
}

# Valores da coluna "status" da aba de qualidade
STATUS_LABELS: dict[str, str] = {
    "ok": "ok",
    "warning": "atenção",
}


def translate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Renomeia colunas e traduz valores descritivos para pt-BR."""
    df = df.rename(columns={c: COLUMN_LABELS.get(c, c) for c in df.columns})
    if "verificação" in df.columns:
        df["verificação"] = df["verificação"].map(
            lambda v: QUALITY_CHECK_LABELS.get(v, v)
        )
    if "status" in df.columns:
        df["status"] = df["status"].map(lambda v: STATUS_LABELS.get(v, v))
    return df
