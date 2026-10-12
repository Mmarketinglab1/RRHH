import io
import textwrap
from typing import Sequence
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


PRIMARY_TEAL = "#00857c"
DARK_DOT_COLOR = "#0f4c5c"
REFERENCE_GREEN = "#22c55e"
GRID_COLOR = "#e2e8f0"
BORDER_TEAL = "#00857c"
TEXT_DARK = "#1e293b"


def _setup_figure_style(ax, border_color=BORDER_TEAL):
    for spine in ax.spines.values():
        spine.set_color(border_color)
        spine.set_linewidth(1.0)
    ax.tick_params(colors=TEXT_DARK, labelsize=7)
    ax.grid(True, linestyle="--", linewidth=0.5, color=GRID_COLOR, alpha=0.8)
    ax.set_facecolor("white")


def generate_competency_items_chart(
    competencies_with_items: list[dict],
    width_inches: float = 8.5,
    height_inches: float = 5.2,
) -> bytes:
    """
    Página 8: Gráfica de 'Desarrollo de las competencias'
    Reactivos agrupados por competencia con barras horizontales y etiquetas.
    """
    fig, ax = plt.subplots(figsize=(width_inches, height_inches), dpi=200)
    _setup_figure_style(ax)

    # Preparar labels, valores y encabezados de grupos
    y_labels = []
    values = []
    y_positions = []
    group_headers = []

    current_y = 0

    # Invertir orden de competencias para que la primera quede arriba
    for comp in reversed(competencies_with_items):
        comp_name = comp["name"]
        items = comp.get("items", [])
        
        for item in reversed(items):
            wrapped_text = "\n".join(textwrap.wrap(item["text"], width=55))
            y_labels.append(wrapped_text)
            values.append(item["average"])
            y_positions.append(current_y)
            current_y += 1
            
        # Posición para el título de la competencia arriba del grupo
        group_headers.append((current_y, comp_name))
        current_y += 1

    # Dibujar barras
    bars = ax.barh(y_positions, values, height=0.55, color=PRIMARY_TEAL, zorder=3)

    # Etiquetas de valor numérico al extremo de cada barra
    for bar, val in zip(bars, values):
        ax.text(
            val + 0.04,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.2f}",
            va="center",
            ha="left",
            fontsize=6.5,
            color=TEXT_DARK,
            fontweight="normal",
        )

    # Escribir títulos de cada grupo de competencia
    for y_pos, header_text in group_headers:
        ax.text(
            7.00,
            y_pos - 0.2,
            header_text,
            va="center",
            ha="right",
            fontsize=7.5,
            color=TEXT_DARK,
            fontweight="bold",
        )

    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels, fontsize=6, color=TEXT_DARK)

    # Escala de 7.00 a 10.00 como en el PDF
    ax.set_xlim(7.00, 10.20)
    ax.set_xticks([7.00, 7.50, 8.00, 8.50, 9.00, 9.50, 10.00])
    ax.set_xticklabels(["7.00", "7.50", "8.00", "8.50", "9.00", "9.50", "10.00"], fontsize=7)

    ax.set_title("Desarrollo de las competencias", fontsize=9, color=BORDER_TEAL, pad=10, fontweight="bold")
    
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def generate_ranking_bars_chart(
    title: str,
    participants: list[tuple[str, float]],
    median_val: float,
    stddev_val: float,
    is_weighted: bool = False,
    width_inches: float = 7.5,
    height_inches: float = 8.5,
) -> bytes:
    """
    Páginas 11-15 y 20-24: Ranking Individual contra Mediana
    Barras horizontales ordenadas de mayor a menor con línea vertical de mediana.
    """
    fig, ax = plt.subplots(figsize=(width_inches, height_inches), dpi=200)
    _setup_figure_style(ax)

    # Ordenar participantes de mayor a menor y luego invertir para gráfico horizontal
    sorted_p = sorted(participants, key=lambda x: x[1], reverse=False)
    names = [p[0] for p in sorted_p]
    scores = [p[1] for p in sorted_p]
    y_pos = list(range(len(names)))

    bars = ax.barh(y_pos, scores, height=0.45, color=PRIMARY_TEAL, zorder=3)

    # Valores numéricos al final de la barra
    for bar, val in zip(bars, scores):
        ax.text(
            val + (0.04 if not is_weighted else 0.02),
            bar.get_y() + bar.get_height() / 2,
            f"{val:.2f}",
            va="center",
            ha="left",
            fontsize=6.5,
            color=TEXT_DARK,
        )

    # Línea vertical de la mediana
    ax.axvline(x=median_val, color=REFERENCE_GREEN, linestyle="-", linewidth=1.2, zorder=4)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=6.5, color=TEXT_DARK)

    # Configuración de límites del eje X
    if is_weighted:
        min_score = min(scores) if scores else 0.0
        max_score = max(scores) if scores else 10.0
        x_start = max(0.0, round(min_score - 0.5, 1))
        x_end = min(10.0, round(max_score + 0.5, 1))
        ax.set_xlim(x_start, x_end)
    else:
        min_score = min(scores) if scores else 7.0
        x_start = 7.50 if min_score >= 7.50 else 7.00
        ax.set_xlim(x_start, 10.20)

    if title:
        ax.set_title(title, fontsize=9, color=TEXT_DARK, pad=8, fontweight="bold")

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def generate_scatter_plot(
    title: str,
    points: list[tuple[int, float]],
    median_val: float,
    y_min: float = 6.50,
    y_max: float = 10.00,
    width_inches: float = 6.5,
    height_inches: float = 3.6,
) -> bytes:
    """
    Páginas 16 y 17: Gráficas de dispersión por Competencia (Puntaje Neto)
    """
    fig, ax = plt.subplots(figsize=(width_inches, height_inches), dpi=200)
    _setup_figure_style(ax)

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    # Puntos individuales
    ax.scatter(xs, ys, color=DARK_DOT_COLOR, s=18, zorder=3)

    # Línea horizontal de corte de la mediana
    ax.axhline(y=median_val, color=REFERENCE_GREEN, linestyle="-", linewidth=1.2, zorder=4)

    ax.set_xlim(0, max(xs) + 5 if xs else 50)
    ax.set_ylim(y_min, y_max)
    ax.set_title(title, fontsize=8, color=BORDER_TEAL, pad=6, fontweight="bold")

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def generate_segmented_scatter_plot(
    title: str,
    segments: list[dict],
    median_val: float,
    y_min: float = 6.50,
    y_max: float = 10.00,
    width_inches: float = 7.0,
    height_inches: float = 4.0,
) -> bytes:
    """
    Páginas 27, 28 y 29: Gráficas de dispersión segmentadas por Línea de Negocio
    (ej. Diabetes | Especialidades | Sotatercep)
    """
    fig, ax = plt.subplots(figsize=(width_inches, height_inches), dpi=200)
    _setup_figure_style(ax)

    current_x = 1
    boundary_x = []
    all_xs = []
    all_ys = []

    for seg in segments:
        seg_name = seg["name"]
        seg_points = seg.get("points", [])
        
        start_x = current_x
        for pt in seg_points:
            all_xs.append(current_x)
            all_ys.append(pt[1])
            current_x += 1
        end_x = current_x - 1

        # Etiqueta de la línea / unidad de negocio en caja
        mid_x = (start_x + end_x) / 2 if end_x >= start_x else start_x
        ax.text(
            mid_x,
            y_max - 0.25,
            f"  {seg_name}  ",
            ha="center",
            va="center",
            fontsize=7,
            color=BORDER_TEAL,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", edgecolor=BORDER_TEAL, facecolor="white", linewidth=0.8),
            zorder=5,
        )

        boundary_x.append(current_x)
        current_x += 2  # Separación entre segmentos

    # Graficar puntos
    ax.scatter(all_xs, all_ys, color=DARK_DOT_COLOR, s=18, zorder=3)

    # Línea horizontal de corte
    ax.axhline(y=median_val, color=REFERENCE_GREEN, linestyle="-", linewidth=1.2, zorder=4)

    # Líneas divisorias verticales entre líneas de negocio
    for bx in boundary_x[:-1]:
        ax.axvline(x=bx - 1, color="#38bdf8", linestyle="-", linewidth=1.0, zorder=2)

    ax.set_xlim(0, current_x + 2)
    ax.set_ylim(y_min, y_max)
    ax.set_title(title, fontsize=8, color=BORDER_TEAL, pad=8, fontweight="bold")

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()
