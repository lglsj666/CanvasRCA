import React from 'react';
import {Card,Rect} from './primitives.js';
import MetricLine from './MetricLine.js';
import TracePairedBars from './TracePairedBars.js';
import LogTimeline from './LogTimeline.js';
import EvidenceInventory from './EvidenceInventory.js';
import PairedObservations from './PairedObservations.js';
import ScopedDetails from './ScopedDetails.js';

// Explicit component grammar. Only field names are abbreviated; source values,
// units, strings, plot samples and their occurrence-specific bindings are intact.
// This fixed public glossary is also carried by the static reading instructions.
export const sourceLabelAliases:Record<string,string>={
 'sircl_met_z':'MET-Z','log_r':'LOG-R-meta','current_mean':'cur mean','current_std_dev':'cur SD',
 'regular_mean':'ref mean','regular_std_dev':'ref SD','deviation_sigma':'deviation σ',
 'fluctuating_3sigma':'fluctuating 3σ','legacy_display_rank':'legacy rank','signed_z':'signed z',
 'severity_z_display':'severity z','evidence_source_display':'source','onset_rel_min_display':'onset (min)',
 'current_interval_s':'cur interval (s)','reference_interval_s':'ref interval (s)',
 'current_median':'cur median','reference_median':'ref median','current_mad':'cur MAD','reference_mad':'ref MAD',
 'current_samples':'cur samples','reference_samples':'ref samples','relative_bin':'bin',
 'omitted_numeric_variables':'omitted numeric vars','numeric_preview':'numeric preview',
 'current':'cur','reference':'ref','parent':'P','child':'C','parent operation':'P op','child operation':'C op',
 'captured requests':'captured reqs','parent reference p95':'P ref p95','child reference p95':'C ref p95',
 'parent≤p95 child≤p95':'P≤p95 C≤p95','parent≤p95 child>p95':'P≤p95 C>p95',
 'parent>p95 child≤p95':'P>p95 C≤p95','parent>p95 child>p95':'P>p95 C>p95',
 'parent≤ref p95':'P≤ref p95','parent>ref p95':'P>ref p95','parent p50':'P p50','child p50':'C p50',
 'parent p95':'P p95','child p95':'C p95','parent_slow (0/1)':'P slow (0/1)',
 'reference span count':'ref spans','current span count':'cur spans',
 'reference exclusive p95':'ref exclusive p95','current exclusive p95':'cur exclusive p95',
 'current inclusive p95':'cur inclusive p95','exclusive latency change':'exclusive change',
 'span count change':'span count Δ','entry_index':'entry index','rank_score':'rank score',
};
export function captionName(name:string){return name.split(' · ').map(s=>sourceLabelAliases[s]??s).join(' · ');}
const native={metric:MetricLine,trace:TracePairedBars,log:LogTimeline,inventory:EvidenceInventory,comparison:PairedObservations};
export default function SourceCompact({card,rect}:{card:Card;rect:Rect}){
 const Component=native[card.kind as keyof typeof native];if(!Component)throw new Error('Unsupported compact kind');
 const captions={...card,data:{...card.data,details:card.data.details?.map(d=>({...d,name:captionName(d.name)}))}};
 const selector=`.panel[data-card="${card.id}"][data-component="${card.kind}.source_compact"]`;
 const css=`${selector} .scope-rows{display:flex;flex-wrap:wrap;gap:0 12px;align-items:flex-start}
 ${selector} .source-scope{flex:0 0 100%;padding-left:0;border-left:0}
 ${selector} .scope-prefix,${selector} .scoped-detail{line-height:32px;margin:0}
 ${selector} .scoped-detail{flex:0 1 auto;max-width:100%}
 ${selector} .scoped-detail .value{display:inline;white-space:normal}
 ${selector} .scope-prefix{font-weight:600}
 `;
 return <><style href={'source-compact-'+card.id} precedence="default">{css}</style>
  <Component card={card} rect={rect}/><ScopedDetails card={captions}/></>;
}

// Component-specific layout finalizer. Align its complete caption region to a
// merger row after the real font is loaded. It inserts only background spacing.
export function alignSourceCaptions(){
 for(const panel of document.querySelectorAll<HTMLElement>('[data-component$=".source_compact"]:not([data-component="graph.source_compact"])')){
  const cap=panel.querySelector<HTMLElement>(':scope > .scoped-details');if(!cap)throw new Error('No complete source captions');
  cap.style.paddingTop='0px';const y=cap.getBoundingClientRect().top-panel.getBoundingClientRect().top;
  cap.style.paddingTop=((32-y%32)%32)+'px';
 }
}
