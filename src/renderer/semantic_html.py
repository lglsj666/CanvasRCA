"""Direct semantic HTML export of the unified renderer's public card packet.

A specifically registered text baseline, not a PNG dashboard or visual fallback.
Every public card field is preserved. CSS, pixels and token-support audit fields
are not incident evidence and are excluded; no private evaluator input is read.
"""
import html
import json
from html.parser import HTMLParser
from pathlib import Path
from .utils import validate_evidence


def export(evidence,path):
    validate_evidence(evidence)
    keys=sorted({key for card in evidence['cards'] for key in card})
    # One shared column definition; JSON inside cells preserves nested arrays,
    # exact strings, explicit nulls and type without verbose repeated HTML tags.
    head='<table><thead><tr>'+''.join('<th>'+html.escape(k)+'</th>' for k in keys)+'</tr></thead><tbody>'
    rows=[]
    for card in evidence['cards']:
        rows.append('<tr>'+''.join('<td>'+html.escape(json.dumps(columnar(card[k]),ensure_ascii=False,separators=(',',':'),allow_nan=False),quote=False)+'</td>' if k in card else '<td></td>' for k in keys)+'</tr>')
    text=head+''.join(rows)+'</tbody></table>'
    if decode(text)!=evidence['cards']:raise ValueError('Semantic HTML lost a public occurrence')
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    return text


def decode(text):
    class Reader(HTMLParser):
        def __init__(self):super().__init__(convert_charrefs=True);self.keys=[];self.rows=[];self.row=[];self.part=None;self.parts=[]
        def handle_starttag(self,tag,attrs):
            if tag in ('th','td'):self.part=tag;self.parts=[]
            elif tag=='tr':self.row=[]
        def handle_data(self,data):
            if self.part:self.parts.append(data)
        def handle_endtag(self,tag):
            if tag in ('td','th'):
                value=''.join(self.parts)
                if tag=='th':self.keys.append(value)
                else:self.row.append(value)
                self.part=None
            elif tag=='tr' and self.row:
                if len(self.row)!=len(self.keys):raise ValueError('HTML columns are not complete')
                self.rows.append({key:expand(json.loads(value)) for key,value in zip(self.keys,self.row) if value!=''})
    parser=Reader();parser.feed(text);parser.close();return parser.rows


def columnar(value):
    if isinstance(value,list):
        if value and all(isinstance(row,dict) for row in value):
            columns=list(dict.fromkeys(k for row in value for k in row))
            if all(set(row)==set(columns) for row in value):
                return {'columns':columns,'rows':[[columnar(row[k]) for k in columns] for row in value]}
        return [columnar(x) for x in value]
    if isinstance(value,dict):
        if set(value)=={'columns','rows'}:raise ValueError('Reserved table grammar collision')
        return {k:columnar(v) for k,v in value.items()}
    return value


def expand(value):
    if isinstance(value,list):return [expand(x) for x in value]
    if isinstance(value,dict):
        if set(value)=={'columns','rows'}:
            if len(set(value['columns']))!=len(value['columns']):raise ValueError('Duplicate columns')
            return [{k:expand(v) for k,v in zip(value['columns'],row,strict=True)} for row in value['rows']]
        return {k:expand(v) for k,v in value.items()}
    return value


PLOT_PSEUDOCODE = 'Drawing pseudocode for the other registered card kinds (not executable):\n- inventory: display every identities entry in original order.\n- graph: place all nodes; label each id and type; draw each edge from source to target with an arrow and its kind. Do not infer causality from edges.\n- comparison: for each comparisons row, draw paired reference/current bars with a shared axis within that row, retaining its name and unit.\n- trace_joint: for each parent_ms/child_ms axis, plot every real sample at log1p(ms), split rows by phase (reference/current); use the same scale for the two endpoints; label parent/child and operations and support counts. Samples are observations, not a temporal path.\nAll details, values, units and strings remain explicitly present in the HTML table.\n'


def plot_program():
    code=Path(__file__).with_name("semantic_plot.mjs").read_text()
    return '<script type="module">'+code+'\nwindow.__semantic_complete=true;</script><pre>'+html.escape(PLOT_PSEUDOCODE)+'</pre>'
