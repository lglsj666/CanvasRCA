"""Report-only figures from completed results; no inference or dashboard rendering.

Run with the project's tools Python. The JSON data snapshot lists source paths
and hashes; dashboard exemplars are byte-identical hard links to actual inputs.
"""
from pathlib import Path
import csv
import hashlib
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.ticker import PercentFormatter, FuncFormatter
from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = OUT / "references" if (OUT / "references").is_dir() else OUT.parent
BLUE, TEAL, PURPLE, ORANGE, GRAY = "#3569A4", "#16877F", "#8060A7", "#C66A32", "#667789"
DARK, LIGHT = "#203247", "#E9EFF4"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12,
                     "text.color": DARK, "axes.labelcolor": DARK,
                     "xtick.color": DARK, "ytick.color": DARK,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "svg.fonttype": "none", "savefig.facecolor": "white"})
provenance = {}

def source(path):
    p = ROOT / path
    provenance[path] = hashlib.sha256(p.read_bytes()).hexdigest()
    return p

def rows(path):
    with source(path).open() as f:
        return list(csv.DictReader(f))

def pick(data, **where):
    match = [r for r in data if all(r[k] == v for k, v in where.items())]
    assert len(match) == 1, where
    return match[0]

def save(fig, name):
    for ext in ("png", "svg"):
        fig.savefig(OUT / f"{name}.{ext}", dpi=170, bbox_inches="tight", pad_inches=0.18)
    plt.close(fig)

def clean(ax):
    ax.set_axisbelow(True)
    ax.grid(axis="x", color=LIGHT, linewidth=1)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(LIGHT)
    ax.tick_params(axis="y", length=0)

r316 = rows("RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/absolute_metrics.csv")
r43 = rows("docs/experiment_reports/RQ4_3_Qwen_Analysis_2026-10-12_assets/main_summary.csv")
r44 = rows("RQs/RQ4_4/results/source_views_v1/analysis/detailed_v1/main_summary.csv")
hybrid = pick(r316, dataset="all", arm="MARGINAL_FIVE")
headline = [{"label": "Full text + marginal plot\nRQ3.16 · MARGINAL_FIVE",
             "mrr": float(hybrid["mrr"]), "tokens": float(hybrid["mean_total_tokens"]), "color": PURPLE}]
for arm, label, color, table in [
    ("T_FULL", "Strong text reference\nRQ4.1 · T_FULL", BLUE, r44),
    ("U", "Uniform visual-token selection\nRQ4.1 · U", TEAL, r44),
    ("P_SOFT_IMAGE", "Soft image attention\nRQ4.3 · P_SOFT_IMAGE", GRAY, r43),
    ("SOURCE_ZOOM", "Overview + local high-resolution views\nRQ4.4 · SOURCE_ZOOM", ORANGE, r44),
]:
    r = pick(table, dataset="ALL", arm=arm)
    headline.append({"label": label, "mrr": float(r["mrr"]), "tokens": float(r["total"]), "color": color})

fig, axes = plt.subplots(1, 2, figsize=(14, 5.3), gridspec_kw={"width_ratios": [1, 1]})
fig.subplots_adjust(left=.32, right=.98, wspace=.13, top=.81, bottom=.19)
for ax, key, maximum in zip(axes, ["mrr", "tokens"], [.58, 27000]):
    values = [d[key] for d in headline]
    ax.barh(range(5), values, color=[d["color"] for d in headline], height=.61)
    ax.set_ylim(4.6, -.6)
    ax.set_xlim(0, maximum)
    ax.set_yticks(range(5), [d["label"] for d in headline] if key == "mrr" else [])
    for i, value in enumerate(values):
        ax.text(value + maximum * .018, i, f"{value:.4f}" if key == "mrr" else f"{value:,.0f}", va="center", fontsize=11, weight="bold")
    clean(ax)
    ax.set_xlabel("Mean reciprocal rank · higher is better" if key == "mrr" else "Mean input + output tokens · lower is better", fontsize=11)
    if key == "tokens":
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v/1000:g}k"))
fig.text(.025, .95, "Where the project stands: accuracy and token cost", fontsize=19, weight="bold")
fig.text(.025, .89, "Same 220 development cases; historical system comparisons, not one matched-backend trial.", fontsize=11)
fig.text(.025, .045, "The hybrid remains strongest. Uniform visual selection uses fewer tokens, but leaves a substantial ranking gap.\nToken counts do not measure visual-encoding cost or end-to-end latency.", fontsize=11)
save(fig, "fig_01_performance_cost")

def box(ax, x, y, w, h, title, body, color=BLUE, fontsize=11):
    ax.add_patch(FancyBboxPatch((x,y), w,h, boxstyle="round,pad=0.012,rounding_size=0.015",
                               facecolor="#F5F8FB", edgecolor=color, linewidth=1.6))
    ax.text(x+.017, y+h-.038, title, fontsize=13, weight="bold", va="top", color=color)
    ax.text(x+.017, y+h-.105, body, fontsize=fontsize, va="top", linespacing=1.6)

def arrow(ax, start, end, color=GRAY, dashed=False):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=15,
                                 color=color, linewidth=1.6, linestyle="--" if dashed else "-"))

fig, ax = plt.subplots(figsize=(14, 5.2)); ax.set(xlim=(0,1), ylim=(0,1)); ax.axis("off")
ax.text(.01,.965,"The current route: one diagnostic call, all incident evidence in images", fontsize=18, weight="bold", va="top")
box(ax,.015,.40,.205,.37,"1  Compile evidence","Public metrics, traces,\nlogs and relations\n\nPreserve source identities",BLUE)
box(ax,.27,.40,.205,.37,"2  Render graphics","Registered graphics\nLabels, units, candidates\nand source-linked marks",TEAL)
box(ax,.525,.40,.205,.37,"3  Process images","Frozen visual encoder\nRegistered token policy\n(U: uniform selection)",PURPLE)
box(ax,.78,.40,.205,.37,"4  Diagnose once","Rank five candidates\nand explain the ranking\n\nNo upstream model call",ORANGE)
for x1,x2 in [(.22,.27),(.475,.525),(.73,.78)]: arrow(ax,(x1,.59),(x2,.59))
ax.text(.015,.26,"Audit path",weight="bold",fontsize=12,color=GRAY)
ax.text(.015,.19,"Source → graphic → image-token maps; exact inputs/outputs; scoring, cost and measured attention",fontsize=12)
arrow(ax,(.372,.40),(.372,.245),dashed=True)
ax.text(.53,.085,"General task / reading / output instructions",fontsize=12,color=BLUE)
arrow(ax,(.882,.12),(.882,.395),color=BLUE)
ax.text(.015,.015,"The audit map supports preprocessing and review; it is not an extra incident-specific text input.", fontsize=10.5)
save(fig,"fig_02_pipeline")

fig, ax = plt.subplots(figsize=(14,5.1));ax.set(xlim=(0,1),ylim=(0,1));ax.axis("off")
ax.text(.01,.96,"How the research question changed",fontsize=20,weight="bold",va="top")
stages = [
    ("RQ1 / RQ2", "Representation & selection", "Text, graphics, hybrid inputs;\nwhich evidence to retain", "Selective relation graphics\nhelped in some settings.", BLUE),
    ("RQ3.1–3.14", "Coverage & organization", "Evidence recovery, binding,\ncomparison and summaries", "More evidence or graphics\ndid not ensure gains.", PURPLE),
    ("RQ3.15–3.21", "Strong hybrid reference", "Parent–child duration facts,\nmarginals, output rules", "Full text + marginal graph\nreached about 0.50 MRR.", ORANGE),
    ("RQ4.1–4.4", "Pure-visual computation", "Token selection, grouping,\nprocessing and local detail", "Best pure visual: 0.3517.\nStrong text: 0.4846.", TEAL),
]
for i,(rq,title,body,lesson,color) in enumerate(stages):
    x=.01+i*.25
    box(ax,x,.19,.223,.60,rq,title+"\n\n"+body,color,fontsize=10.7)
    ax.text(x+.017,.355,lesson,fontsize=10.7,va="top",linespacing=1.5,weight="bold")
    if i<3:arrow(ax,(x+.226,.51),(x+.247,.51))
ax.text(.01,.06,"This is a map of research decisions, not a cumulative accuracy curve: cohorts, prompts and protocols changed.",fontsize=11)
save(fig,"fig_03_research_evolution")

qa = rows("RQs/RQ4_4/results/source_views_v1/analysis/detailed_v1/qa_summary.csv")
qa_match = rows("RQs/RQ4_4/results/source_views_v1/analysis/detailed_v1/qa_source_match_summary.csv")
qa_data=[pick(qa,condition=a,dataset="ALL") for a in ("SOURCE_ZOOM","ISOLATED_QA")]
fig, axes = plt.subplots(1,2,figsize=(13,4.9));fig.subplots_adjust(left=.06,right=.98,bottom=.30,top=.80,wspace=.25)
for ax,field,title in zip(axes,["tolerant","tolerant_numeric_pair"],["All answer fields · tolerant scoring", "Both requested numbers correct"]):
    values=[float(d[field]) for d in qa_data]
    ax.bar([0,1],values,color=[ORANGE,TEAL],width=.58)
    ax.set_xticks([0,1],["Full dashboard + local views\nSOURCE_ZOOM", "Only the target card\nISOLATED_QA"],fontsize=10.5)
    ax.set_ylim(0,1.16);ax.set_yticks([0,.25,.5,.75,1]);ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_title(title,loc="left",fontsize=12,pad=14)
    ax.grid(axis="y",color=LIGHT);ax.set_axisbelow(True)
    for i,v in enumerate(values):
        label=f"{v*100:.2f}%" if field=="tolerant" else f"{round(v*30)}/30"
        ax.text(i,v+.035,label,ha="center",weight="bold",fontsize=15)
fig.text(.03,.945,"Reading the wrong card is different from being unable to read",fontsize=19,weight="bold")
fig.text(.03,.88,"RQ4.4 · 30 fixed cases · independent question-answering probes, not RCA scores",fontsize=11)
fig.text(.03,.115,"23/30 full-dashboard numeric answers matched a different real card; 18/30 matched an added local-view card.",fontsize=11,weight="bold")
fig.text(.03,.045,"Isolation changes target visibility, competing cards, resolution and token retention together.\nOnly 2/30 SOURCE_ZOOM question targets were themselves enlarged; this is not a pure resolution comparison.",fontsize=10.5)
save(fig,"fig_04_qa_source_selection")

flip_data = [
    {"label":"RQ3.21 · reorder entity blocks\nCompact text", "changed":22,"repeat":1,"n":60,"source":"docs/experiment_reports/RQ3_21_Qwen_Analysis_2026-10-06.md"},
    {"label":"RQ3.21 · reorder entity blocks\nCompact text + marginal graph", "changed":20,"repeat":2,"n":60,"source":"docs/experiment_reports/RQ3_21_Qwen_Analysis_2026-10-06.md"},
    {"label":"RQ4.1 · move visual evidence\nComparison-aware token selection", "changed":47,"repeat":0,"n":90,"source":"docs/experiment_reports/RQ4_1_Qwen_Analysis_2026-10-09.md"},
    {"label":"RQ4.3 · perturb processing order\nLocal bidirectional processing", "changed":39,"repeat":5,"n":60,"source":"docs/experiment_reports/RQ4_3_Qwen_Analysis_2026-10-12.md"},
    {"label":"RQ4.4 · reorder local-view cards\nSOURCE_ZOOM", "changed":9,"repeat":3,"n":30,"source":"docs/experiment_reports/RQ4_4_Qwen_Analysis_2026-10-12.md"},
]
for d in flip_data: source(d["source"])
fig, ax=plt.subplots(figsize=(13,6));fig.subplots_adjust(left=.38,right=.98,bottom=.20,top=.77)
for key,offset,color,label in [("changed",-.17,ORANGE,"Fact-preserving presentation/order change"),("repeat",.17,BLUE,"New call with the original input")]:
    ys=[i+offset for i in range(5)];values=[d[key]/d["n"] for d in flip_data]
    ax.barh(ys,values,height=.29,color=color,label=label)
    for y,v,d in zip(ys,values,flip_data):ax.text(v+.012,y,f"{d[key]}/{d['n']}",va="center",fontsize=11)
ax.set_yticks(range(5),[d["label"] for d in flip_data],fontsize=11)
ax.set_ylim(4.6,-.65);ax.set_xlim(0,.76);ax.xaxis.set_major_formatter(PercentFormatter(1));clean(ax)
ax.set_xlabel("Cases whose first-ranked candidate changed")
fig.text(.025,.95,"Presentation changes often exceed independent-repeat variability",fontsize=18,weight="bold")
handles,labels=ax.get_legend_handles_labels();fig.legend(handles,labels,loc="upper left",bbox_to_anchor=(.022,.895),ncol=2,frameon=False,fontsize=10.5)
fig.text(.025,.055,"Each row has its own cases and intervention. Counts are not pooled; no common effect size is implied.\nA changed first choice can improve or worsen RCA. The small RQ4.4 comparison is exploratory.",fontsize=11)
save(fig,"fig_05_order_sensitivity")

# Hybrid input contracts: a schematic, deliberately not a reconstructed input.
fig, ax=plt.subplots(figsize=(14,6));ax.set(xlim=(0,1),ylim=(0,1));ax.axis("off")
ax.text(.01,.965,"Two different hybrid designs: replace a text block or repeat its facts",fontsize=18,weight="bold",va="top")
ax.text(.01,.88,"Schematic of input composition; not an original dashboard or a paired cross-experiment trial.",fontsize=11)
box(ax,.015,.36,.445,.44,"TPV · replace topology text",
    "TEXT: metrics + traces + logs\nIMAGE: topology relations\n\nThe topology text block is omitted.",TEAL,fontsize=13)
box(ax,.54,.36,.445,.44,"MARGINAL_FIVE · repeat selected facts",
    "TEXT: complete facts, including duration pairs\nIMAGE: selected duration pairs as marginal plots\n\nThe plotted facts remain in the text.",PURPLE,fontsize=12)
ax.text(.035,.265,"Question: does changing the carrier help?",fontsize=12,weight="bold",color=TEAL)
ax.text(.56,.265,"Question: does an extra depiction help?",fontsize=12,weight="bold",color=PURPLE)
ax.text(.015,.13,"Other methods mix these choices: RQ3.7 replaces topology text but redraws retained numeric facts.\nRQ3.17 repeats topology too; it is therefore not the same input design as TPV.",fontsize=12,linespacing=1.5)
save(fig,"fig_11_hybrid_contracts")

rq11_path="docs/experiment_reports/RQ1_1_RQ2_1_findings/assets/rq11_performance_cost_runtime_all_arms_datasets.csv"
rq11=rows(rq11_path)
tpv_rows=[r for r in rq11 if r["arm"] in {"T","TPV","H","V"}]
rq11_primary=[pick(rq11,arm=a,dataset="headline") for a in ("T","TPV","H","V")]
labels=["All diagnostic facts in text\nT", "Topology replaces its text block\nTPV", "Full text + redundant dashboard\nH", "All diagnostic facts in graphics\nV"]
colors=[BLUE,TEAL,PURPLE,GRAY]
fig,axes=plt.subplots(1,2,figsize=(14,4.9));fig.subplots_adjust(left=.30,right=.98,top=.79,bottom=.24,wspace=.14)
for ax,key,maximum in zip(axes,["mrr","total"],[.46,18500]):
    values=[float(r[key]) for r in rq11_primary]
    ax.barh(range(4),values,color=colors,height=.62)
    ax.set_yticks(range(4),labels if key=="mrr" else []);ax.set_ylim(3.6,-.6);ax.set_xlim(0,maximum);clean(ax)
    for i,v in enumerate(values):ax.text(v+maximum*.018,i,f"{v:.4f}" if key=="mrr" else f"{v:,.0f}",va="center",weight="bold",fontsize=11)
    ax.set_xlabel("Mean reciprocal rank · higher is better" if key=="mrr" else "Mean input + output tokens",fontsize=11)
    if key=="total":ax.xaxis.set_major_formatter(FuncFormatter(lambda v,p:f"{v/1000:g}k"))
fig.text(.02,.95,"TPV is a positive result for selective replacement, not full duplication",fontsize=18,weight="bold")
fig.text(.02,.88,"RQ1.1 · Qwen · 300 primary cases (100 per dataset) · same-round representation comparison",fontsize=11)
fig.text(.02,.085,"TPV − T: ΔMRR +0.0727; registered five-comparison Holm p ≈ 0.0276.\nTotal tokens increased by about 12.5%: replacing text with a picture did not automatically save cost.",fontsize=11)
save(fig,"fig_12_tpv_performance_cost")

# One unaltered input image per representative arm, all from the same incident.
examples = [
    ("MARGINAL_FIVE", "dashboard_01_marginal_five.png", "RQs/RQ3_16/preparation/marginal_coverage_v1/renders/INC-7FCA48559A2E/MARGINAL_FIVE/dashboard.png", "Hybrid: accompanying complete text is not shown."),
    ("A_UNIFORM_E50", "dashboard_02_uniform.png", "RQs/RQ4_1/results/comparison_coding_v1/cpu_admission_v4/typed_source_render/INC-7FCA48559A2E/render/dashboard.png", "Source image; feature-token selection is not a pixel mask."),
    ("SEM", "dashboard_03_sem.png", "RQs/RQ4_2/results/partition_v4/formal_v1/materialized/ba46067b50a1432ebce9c3e389f348c3/INC-7FCA48559A2E_SEM/render/dashboard.png", "SEM changes encoder grouping, which is not visible in this shared image."),
    ("X_SRP", "dashboard_04_xsrp.png", "RQs/RQ4_3/results/xsrp_v8/population02/inputs/INC-7FCA48559A2E/packed/render_repair1/dashboard.png", "Combined selection/rendering/processing method; actual formal request checked."),
    ("SOURCE_ZOOM", "dashboard_05_source_zoom.png", "RQs/RQ4_4/results/source_views_v1/inputs/INC-7FCA48559A2E/SOURCE_ZOOM/dashboard.png", "Local atlas only; the request also contains the unchanged U overview."),
]
dashboard_index=[]
for arm,name,path,note in examples:
    original=source(path);target=OUT/name
    if not target.exists():os.link(original,target)
    assert hashlib.sha256(target.read_bytes()).hexdigest()==provenance[path]
    with Image.open(target) as im: dimensions=list(im.size)
    dashboard_index.append({"arm":arm,"case":"INC-7FCA48559A2E","dataset":"aegislab", "file":name,
                            "original":path,"sha256":provenance[path],"pixels":dimensions,"note":note})
(OUT/"figure_data.json").write_text(json.dumps({"headline":headline,"tpv_rq11":tpv_rows,"qa":qa_data,"qa_source_matches":qa_match,
    "order_sensitivity":flip_data,"dashboards":dashboard_index,"source_sha256":provenance},indent=2)+"\n")
print(json.dumps({"analysis_figures":7,"dashboard_examples":len(dashboard_index),"directory":str(OUT)}))
