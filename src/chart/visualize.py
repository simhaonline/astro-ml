import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from typing import Literal

def generate_chart(dt: datetime, style: Literal["wheel", "north", "south"] = "wheel") -> bytes:
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(aspect="equal"))
    ax.axis("off")
    # dummy wheel for brevity – extend for north/south
    circle = plt.Circle((0, 0), 1, fill=False, edgecolor="black")
    ax.add_patch(circle)
    ax.text(0, 0, dt.strftime("%Y-%m-%d"), ha="center", va="center", fontsize=14)
    ax.set_xlim(-1.2, 1.2); ax.set_ylim(-1.2, 1.2)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()
