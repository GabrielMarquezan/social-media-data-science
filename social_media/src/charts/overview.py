import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure


def plot_likes_comments_timeline(posts: pd.DataFrame) -> Figure:
    """Plota likes e comentários ao longo do tempo."""
    fig, ax = plt.subplots(figsize=(10, 6))

    df = posts[["timestamp", "num_likes", "num_comentarios"]].copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp")

    if df.empty:
        ax.text(0.5, 0.5, "Sem dados de timeline", ha="center", va="center")
        ax.set_title("Likes e Comentários ao Longo do Tempo")
        return fig

    ax.plot(df["timestamp"], df["num_likes"], marker="o", label="Likes", linewidth=2)
    ax.plot(
        df["timestamp"],
        df["num_comentarios"],
        marker="s",
        label="Comentários",
        linewidth=2,
    )

    ax.set_title("Likes e Comentários ao Longo do Tempo")
    ax.set_xlabel("Data")
    ax.set_ylabel("Quantidade")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.6)
    fig.autofmt_xdate()

    return fig


def plot_top_posts_engagement(posts: pd.DataFrame, top_n: int = 10) -> Figure:
    """Plota top N posts por engagement_rate (fallback para comments_per_like)."""
    fig, ax = plt.subplots(figsize=(10, 6))

    df = posts[["short_code", "engagement_rate", "comments_per_like"]].copy()
    df["ranking_metric"] = df["engagement_rate"].fillna(df["comments_per_like"])
    df = df.dropna(subset=["ranking_metric"]).sort_values("ranking_metric", ascending=False)

    if df.empty:
        ax.text(0.5, 0.5, "Sem dados de engajamento", ha="center", va="center")
        ax.set_title(f"Top {top_n} Posts por Engajamento")
        return fig

    top = df.head(top_n).sort_values("ranking_metric", ascending=True)
    labels = top["short_code"].fillna("sem_shortcode")
    colors = ["#2ca02c" if not pd.isna(er) else "#1f77b4" for er in top["engagement_rate"]]

    ax.barh(labels, top["ranking_metric"], color=colors)
    ax.set_title(f"Top {top_n} Posts por Engajamento")
    ax.set_xlabel("Engagement Rate (ou Comments per Like)")
    ax.grid(True, axis="x", linestyle="--", alpha=0.6)

    return fig


def plot_posts_by_type(posts: pd.DataFrame) -> Figure:
    """Plota volume de posts por tipo e média de comments_per_like."""
    fig, ax1 = plt.subplots(figsize=(8, 6))

    df = posts[["type", "comments_per_like"]].copy()
    df["type"] = df["type"].fillna("Desconhecido")

    grouped = (
        df.groupby("type")
        .agg(posts=("type", "size"), avg_comments_per_like=("comments_per_like", "mean"))
        .reset_index()
    )

    if grouped.empty:
        ax1.text(0.5, 0.5, "Sem dados por tipo", ha="center", va="center")
        ax1.set_title("Posts por Tipo")
        return fig

    x = range(len(grouped))
    ax1.bar(x, grouped["posts"], color="#1f77b4", label="Posts")
    ax1.set_xticks(x)
    ax1.set_xticklabels(grouped["type"])
    ax1.set_xlabel("Tipo de Post")
    ax1.set_ylabel("Quantidade de Posts", color="#1f77b4")
    ax1.tick_params(axis="y", labelcolor="#1f77b4")

    ax2 = ax1.twinx()
    ax2.plot(
        x,
        grouped["avg_comments_per_like"],
        color="#ff7f0e",
        marker="o",
        linewidth=2,
        label="Avg Comments/Like",
    )
    ax2.set_ylabel("Média de Comments per Like", color="#ff7f0e")
    ax2.tick_params(axis="y", labelcolor="#ff7f0e")

    ax1.set_title("Volume de Posts por Tipo vs. Média de Comments per Like")

    return fig
