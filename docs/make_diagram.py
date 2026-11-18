import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
fig, ax = plt.subplots(figsize=(12, 6), dpi=130); ax.axis("off"); ax.set_xlim(0, 12); ax.set_ylim(0, 6)
def box(x, y, w, h, t, c):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05", fc=c, ec="#333")); ax.text(x+w/2, y+h/2, t, ha="center", va="center", fontsize=9)
def arr(a, b, t=""):
    ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="->", lw=1.3)); 
    if t: ax.text((a[0]+b[0])/2, (a[1]+b[1])/2+.12, t, fontsize=7, ha="center")
box(.2, 2.4, 1.8, 1.2, "User\n(Streamlit UI /\nCLI)\napp.py · cli.py", "#e8f1fb")
box(2.9, 2.4, 2.4, 1.2, "Agent (agent.py)\nClaude tool-use loop\n+ offline router fallback", "#fff2cc")
box(6.2, 4.3, 2.4, 1.0, "Tool layer (tools.py)\nJSON schemas + dispatcher", "#e2f0d9")
box(6.2, 2.4, 2.4, 1.2, "Analytics (analytics.py)\nlatest · history · YoY/QoQ\ncorrelation · trends", "#e2f0d9")
box(6.2, .4, 2.4, 1.2, "Charts (charts.py)\nmatplotlib → outputs/*.png", "#e2f0d9")
box(9.5, 2.4, 2.2, 1.2, "Data (fred.py)\nCSV fetch + disk cache\ndata/*.csv", "#fce4d6")
box(2.9, 4.5, 2.4, 1.0, "Anthropic API\nClaude model", "#ead1f5")
box(9.5, .4, 2.2, 1.2, "FRED\nGDP · CPILFESL", "#fce4d6")
arr((2, 3), (2.9, 3), "question"); arr((2.9, 2.7), (2, 2.7), "answer + chart")
arr((5.3, 3.4), (6.2, 4.6), "tool calls"); 
arr((4.1, 3.6), (4.1, 4.5), "messages"); 
arr((7.4, 4.3), (7.4, 3.6)); arr((7.4, 2.4), (7.4, 1.6)); arr((8.6, 3), (9.5, 3)); arr((10.6, 2.4), (10.6, 1.6), "HTTPS CSV")
ax.set_title("System architecture: conversational FRED GDP & Core CPI assistant", fontsize=11, fontweight="bold", loc="left")
fig.savefig("docs/architecture.png", bbox_inches="tight")
