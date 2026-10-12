import React from 'react';
import {Card,Rect} from './primitives.js';
import MetricLine from './MetricLine.js';
import TracePairedBars from './TracePairedBars.js';
import LogTimeline from './LogTimeline.js';
import EvidenceInventory from './EvidenceInventory.js';
import PairedObservations from './PairedObservations.js';
import PackedDetails from './PackedDetails.js';

// Explicit component grammar. Only field names are abbreviated; source values,
// units, strings, plot samples and their occurrence-specific bindings are intact.
// This fixed public glossary is also carried by the static reading instructions.
export const packedLabelAliases:Record<string,string>={
 "baseline": "base",
 "legacy_display_rank": "old ID",
 "signed_z": "z",
 "sircl_met_z": "MET-Z",
 "log_r": "LOG-R-meta",
 "current_mean": "C μ",
 "current_std_dev": "C σ",
 "regular_mean": "R μ",
 "regular_std_dev": "R σ",
 "deviation_sigma": "dev σ",
 "fluctuating_3sigma": "3σ flag",
 "evidence_source_display": "source",
 "severity_z_display": "severity z",
 "onset_rel_min_display": "onset min",
 "current_interval_s": "C interval s",
 "reference_interval_s": "R interval s",
 "current_median": "C median",
 "reference_median": "R median",
 "current_mad": "C MAD",
 "reference_mad": "R MAD",
 "current_samples": "C samples",
 "reference_samples": "R samples",
 "relative_bin": "bin",
 "omitted_numeric_variables": "omitted vars",
 "numeric_preview": "numeric preview",
 "current": "cur",
 "reference": "ref",
 "parent": "P",
 "child": "C",
 "parent operation": "P op",
 "child operation": "c op",
 "captured requests": "N requests",
 "parent reference p95": "P R95",
 "child reference p95": "c R95",
 "parent≤p95 child≤p95": "P≤95 c≤95",
 "parent≤p95 child>p95": "P≤95 c>95",
 "parent>p95 child≤p95": "P>95 c≤95",
 "parent>p95 child>p95": "P>95 c>95",
 "parent≤ref p95": "P≤R95",
 "parent>ref p95": "P>R95",
 "parent p50": "P50",
 "child p50": "c50",
 "parent p95": "P95",
 "child p95": "c95",
 "parent_slow (0/1)": "P slow 0/1",
 "reference span count": "R spans",
 "current span count": "C spans",
 "reference exclusive p95": "R excl95",
 "current exclusive p95": "C excl95",
 "current inclusive p95": "C incl95",
 "exclusive latency change": "excl Δ",
 "span count change": "spans Δ",
 "entry_index": "entry index",
 "rank_score": "rank score",
 "duration_rel_s": "duration s",
 "source_metric_rows": "metric rows",
 "omitted_services": "omitted services",
 "service_count": "services count",
 "binary_output": "binary output",
 "schema_version": "schema version",
 "semantic_round_trip": "round trip",
 "template_count": "template count",
 "event_count": "event count",
 "values": "v",
 "count": "cnt",
 "summary": "window",
 "rank": "r",
 "entity": "ent",
 "entity_id": "ent ID",
 "entities": "ents",
 "level": "lvl",
 "components": "parts",
 "error count": "errors",
 "error rate": "err rate",
 "log rate": "logs rate",
 "requests": "reqs",
 "ref_threshold_ms": "R threshold ms",
 "child_slow (0/1)": "c slow 0/1"
};
export function captionName(name:string){return name.split(' · ').map(s=>packedLabelAliases[s]??s).join(' · ');}
const native={metric:MetricLine,trace:TracePairedBars,log:LogTimeline,inventory:EvidenceInventory,comparison:PairedObservations};
export default function PackedSource({card,rect}:{card:Card;rect:Rect}){
 const Component=native[card.kind as keyof typeof native];if(!Component)throw new Error('Unsupported compact kind');
 const captions={...card,data:{...card.data,details:card.data.details?.map(d=>({...d,name:captionName(d.name)}))}};
 const selector=`.panel[data-card="${card.id}"][data-component="${card.kind}_packed.source_compact"]`;
 const css=`${selector} .scope-rows{display:flex;flex-wrap:wrap;gap:0 12px;align-items:flex-start}
 ${selector} .source-scope{flex:0 0 100%;padding-left:0;border-left:0;display:flex;flex-wrap:wrap;gap:0 8px;align-items:baseline}
 ${selector} .source-scope>.scope-rows{display:contents}
 ${selector} .scope-prefix,${selector} .scoped-detail{line-height:24px;margin:0}
 ${selector} .scoped-detail{flex:0 1 auto;max-width:100%}
 ${selector} .scoped-detail .value{display:inline;white-space:normal}
 ${selector} .scope-prefix{font-weight:600}
 `;
 return <><style href={'source-compact-'+card.id} precedence="default">{css}</style>
  <Component card={card} rect={rect}/><PackedDetails card={captions}/></>;
}

