"""Build the arena chart, the demo-site data file and a README table from results_nicrron/summary.json.

    python reference/aggregate_nicrron.py && python reference/make_arena_assets.py

Writes media/arena-chart.png and docs/arena-chart.png (needs matplotlib), docs/arena.js and prints the Markdown table.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMES = {
    "anthropic/claude-fable-5-1": "Claude Fable 5.1", "anthropic/claude-opus-5-5": "Claude Opus 5.5", "anthropic/claude-haiku-5-5": "Claude Haiku 5.5",
    "openai/gpt-6-sol": "GPT-6 Sol", "openai/gpt-6-luna": "GPT-6 Luna", "deepseek/deepseek-v4-pro": "DeepSeek V4 Pro", "moonshot/kimi-k3": "Kimi K3",
    "xai/grok-4.7": "Grok 4.7", "z-ai/glm-5.3": "GLM 5.3", "mistral/mistral-large-4": "Mistral Large 4",
}


def main():
    summary = json.load(open(os.path.join(ROOT, "results_nicrron", "summary.json")))
    rows = [{"model": NAMES.get(e["model"], e["model"]), "id": e["model"], "off_runs": e["off"]["runs"], "off_unsafe": e["off"]["unsafe"],
             "on_runs": e["on"]["runs"], "on_unsafe": e["on"]["unsafe"]} for e in summary]
    open(os.path.join(ROOT, "docs", "arena.js"), "w").write("window.ARENA = " + json.dumps(rows, indent=1) + ";\n")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8.6, 0.46 * len(rows) + 1.6))
    ys = list(range(len(rows)))[::-1]
    off = [r["off_unsafe"] / max(r["off_runs"], 1) * 100 for r in rows]
    on = [r["on_unsafe"] / max(r["on_runs"], 1) * 100 for r in rows]
    ax.barh([y + 0.2 for y in ys], off, height=0.38, color="#b91c1c", label="guardrail off")
    ax.barh([y - 0.2 for y in ys], on, height=0.38, color="#0f766e", label="guardrail on")
    for y, r, v in zip(ys, rows, off):
        ax.text(v + 1.5, y + 0.2, f"{r['off_unsafe']}/{r['off_runs']}", va="center", fontsize=8.5)
    for y, r, v in zip(ys, rows, on):
        ax.text(v + 1.5, y - 0.2, f"{r['on_unsafe']}/{r['on_runs']}", va="center", fontsize=8.5, color="#0f766e")
    ax.set_yticks(ys, [r["model"] for r in rows])
    ax.set_xlim(0, 115)
    ax.set_xlabel("Unsafe runs (% of runs that refunded twice)")
    ax.set_title("Double refunds after a lost reply, by model (mock payments, one fault)", loc="left", fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    for dest in ("media", "docs"):
        fig.savefig(os.path.join(ROOT, dest, "arena-chart.png"), dpi=170, bbox_inches="tight", facecolor="white")
    print("| Model | Guardrail off: unsafe / runs | Guardrail on: unsafe / runs |\n|---|---|---|")
    for r in rows:
        print(f"| {r['model']} | {'**' if r['off_unsafe'] else ''}{r['off_unsafe']} / {r['off_runs']}{'**' if r['off_unsafe'] else ''} | {r['on_unsafe']} / {r['on_runs']} |")


if __name__ == "__main__":
    main()
