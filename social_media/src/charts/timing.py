import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure

_WEEKDAY_LABELS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]


def plot_engagement_heatmap_hour_weekday(posts: pd.DataFrame) -> Figure:
    """Heatmap de avg_comments_per_like por hora do dia e dia da semana."""
    fig, ax = plt.subplots(figsize=(12, 8))

    df = posts[["post_hour", "post_weekday", "comments_per_like"]].copy()
    df = df.dropna(subset=["post_hour", "post_weekday", "comments_per_like"])

    if df.empty:
        ax.text(0.5, 0.5, "Sem dados de timing", ha="center", va="center")
        ax.set_title("Heatmap de Engajamento (Hora × Dia da Semana)")
        return fig

    pivot = df.pivot_table(
        values="comments_per_like",
        index="post_hour",
        columns="post_weekday",
        aggfunc="mean",
    )

    # Garante índices completos de 0-23 e colunas 0-6
    pivot = pivot.reindex(index=range(24), columns=range(7))

    im = ax.imshow(pivot.values, aspect="auto", cmap="YlOrRd")
    ax.set_xticks(np.arange(7))
    ax.set_xticklabels(_WEEKDAY_LABELS)
    ax.set_yticks(np.arange(24))
    ax.set_yticklabels([str(h) for h in range(24)])
    ax.set_xlabel("Dia da Semana")
    ax.set_ylabel("Hora do Dia")
    ax.set_title("Heatmap de Comentários por Curtida (Hora × Dia da Semana)")
    fig.colorbar(im, ax=ax, label="Média de Comentários por Curtida")

    # Anota valores apenas quando a matriz é pequena o suficiente para ser legível
    non_null_count = pivot.notna().sum().sum()
    if non_null_count <= 30:
        for i in range(24):
            for j in range(7):
                value = pivot.iloc[i, j]
                if not pd.isna(value):
                    ax.text(
                        j,
                        i,
                        f"{value:.3f}",
                        ha="center",
                        va="center",
                        color="black",
                        fontsize=6,
                    )

    return fig


def plot_avg_likes_comments_by_weekday(timing_by_weekday: pd.DataFrame) -> Figure:
    """Barras de avg_likes e avg_comments por dia da semana."""
    fig, ax = plt.subplots(figsize=(10, 6))

    df = timing_by_weekday.copy()
    df = df.dropna(subset=["post_weekday"])

    if df.empty:
        ax.text(0.5, 0.5, "Sem dados por dia da semana", ha="center", va="center")
        ax.set_title("Média de Curtidas e Comentários por Dia da Semana")
        return fig

    # Garante que todos os dias da semana apareçam no eixo x
    full_week = pd.DataFrame({"post_weekday": range(7)})
    df["post_weekday"] = df["post_weekday"].astype(int)
    df = full_week.merge(df, on="post_weekday", how="left")
    df["avg_likes"] = df["avg_likes"].fillna(0)
    df["avg_comments"] = df["avg_comments"].fillna(0)

    df["weekday_label"] = df["post_weekday"].map(lambda d: _WEEKDAY_LABELS[d])
    x = np.arange(len(df))
    width = 0.35

    ax.bar(x - width / 2, df["avg_likes"], width, label="Média de Curtidas", color="#1f77b4")
    ax.bar(x + width / 2, df["avg_comments"], width, label="Média de Comentários", color="#ff7f0e")

    ax.set_xlabel("Dia da Semana")
    ax.set_ylabel("Média")
    ax.set_title("Média de Curtidas e Comentários por Dia da Semana")
    ax.set_xticks(x)
    ax.set_xticklabels(df["weekday_label"])
    ax.legend()
    ax.grid(True, axis="y", linestyle="--", alpha=0.6)

    return fig
