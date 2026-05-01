import json

with open("scratch/aicredits_models.txt", "r", encoding="utf-8-sig") as f:
    data = json.load(f)

models = data.get("data", [])

# Group by provider
from collections import defaultdict
by_provider = defaultdict(list)
for m in models:
    provider = m.get("provider", "unknown")
    by_provider[provider].append(m)

lines = []
lines.append("# AICredits Model Catalogue\n")
lines.append(f"**Total models:** {len(models)}  ")
lines.append(f"**Total providers:** {len(by_provider)}  ")
lines.append(f"**Exchange rate (USD→INR):** ~93.18\n")
lines.append("---\n")

for provider in sorted(by_provider.keys()):
    provider_models = sorted(by_provider[provider], key=lambda x: x.get("id",""))
    lines.append(f"## {provider.upper()}\n")
    lines.append("| Model ID | Name | Input $/1k tokens | Output $/1k tokens | Input ₹/1k tokens | Output ₹/1k tokens | Context | Active |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for m in provider_models:
        mid = m.get("id", "")
        name = m.get("name", "")
        inp_usd = m.get("input_cost_per_token", 0)
        out_usd = m.get("output_cost_per_token", 0)
        inp_inr = m.get("input_cost_per_token_inr", 0)
        out_inr = m.get("output_cost_per_token_inr", 0)
        ctx = m.get("context_length", 0)
        active = "✅" if m.get("is_active") else "❌"
        # Per 1k tokens
        inp_usd_1k = f"${inp_usd * 1000:.4f}"
        out_usd_1k = f"${out_usd * 1000:.4f}"
        inp_inr_1k = f"₹{inp_inr * 1000:.4f}"
        out_inr_1k = f"₹{out_inr * 1000:.4f}"
        ctx_str = f"{ctx:,}" if ctx else "—"
        lines.append(f"| `{mid}` | {name} | {inp_usd_1k} | {out_usd_1k} | {inp_inr_1k} | {out_inr_1k} | {ctx_str} | {active} |")
    lines.append("")

output = "\n".join(lines)
with open("scratch/aicredits_catalogue.md", "w", encoding="utf-8") as f:
    f.write(output)

print(f"Done. {len(models)} models across {len(by_provider)} providers written to scratch/aicredits_catalogue.md")
