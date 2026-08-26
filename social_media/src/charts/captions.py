import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure


def plot_caption_word_count_vs_engagement(posts: pd.DataFrame) -> Figure:
    """Scatter plot de caption_word_count vs comments_per_like."""
    fig, ax = plt.subplots(figsize=(10, 6))

    df = posts[["caption_word_count", "comments_per_like"]].copy()
    df = df.dropna(subset=["comments_per_like"])

    if df.empty:
        ax.text(0.5, 0.5, "Sem dados suficientes", ha="center", va="center")
        ax.set_title("Palavras na Legenda vs. Comentários por Curtida")
        return fig

    ax.scatter(df["caption_word_count"], df["comments_per_like"], alpha=0.6, edgecolors="black")
    ax.set_title("Palavras na Legenda vs. Comentários por Curtida")
    ax.set_xlabel("Número de Palavras na Legenda")
    ax.set_ylabel("Comentários por Curtida")
    ax.grid(True, linestyle="--", alpha=0.6)

    return fig
