"""Opt-in complete request-pair component contract; old joint DTOs unchanged."""
from decimal import Decimal, InvalidOperation


def validate(data):
    from .utils import keys, text
    spec=data['complete']
    keys(spec,{'schema','thresholds','phases','values','sample_ids'})
    if spec['schema']!='CompleteMarginalsV1':raise ValueError('Unknown complete marginal schema')
    def numeric(value,integer=False):
        text(value)
        try:decimal=Decimal(value)
        except InvalidOperation as exc:raise ValueError('Invalid exact marginal number') from exc
        if not decimal.is_finite() or decimal<0 or (integer and decimal!=decimal.to_integral_value()):
            raise ValueError('Nonnegative original number required')
        return decimal
    if len(spec['thresholds'])!=2 or len(spec['phases'])!=2:raise ValueError('Threshold/phase capacity')
    for v in spec['thresholds']:numeric(v)
    if len(spec['values'])!=len(data['samples']) or len(spec['sample_ids'])!=len(data['samples']):raise ValueError('Paired lexical values missing')
    if len(set(spec['sample_ids']))!=len(spec['sample_ids']):raise ValueError('Duplicate sample reference')
    for name in spec['sample_ids']:text(name)
    for original,sample in zip(spec['values'],data['samples'],strict=True):
        if len(original)!=2:raise ValueError('Two sample endpoints required')
        for value,key in zip(original,('parent_ms','child_ms'),strict=True):
            if float(numeric(value))!=sample[key]:raise ValueError('Exact glyph label disagrees with position')
    for i,phase in enumerate(spec['phases']):
        keys(phase,{'phase','n','sampled','binary','quantiles','conditional_child'})
        if phase['phase']!=('reference','current')[i]:raise ValueError('Phase order')
        n=numeric(phase['n'],True);sampled=numeric(phase['sampled'],True)
        if n!=data['support'][i] or sampled!=min(n,32):raise ValueError('Population/sample counts')
        if len(phase['binary'])!=4 or sum(numeric(v,True) for v in phase['binary'])!=n:raise ValueError('Joint count total')
        if len(phase['quantiles'])!=2 or any(len(r)!=2 for r in phase['quantiles']):raise ValueError('Quantile shape')
        for q in phase['quantiles']:
            if numeric(q[0])>numeric(q[1]):raise ValueError('Quantile order')
        for row in phase['conditional_child']:
            if len(row)!=4 or row[0] not in {'0','1'}:raise ValueError('Conditional group shape')
            numeric(row[1],True)
            for v in row[2:]:
                if v is not None:numeric(v)
            if all(v is not None for v in row[2:]) and Decimal(row[2])>Decimal(row[3]):raise ValueError('Conditional quantile order')


def bindings(card):
    d=card['data']['complete'];cid=card['id'];out=[]
    out.extend(f'{cid}.threshold.{i}' for i in range(2))
    for p in d['phases']:
        prefix=cid+'.'+p['phase']
        out.extend(prefix+'.'+key for key in ('n','sampled'))
        out.extend(prefix+'.binary.'+str(j) for j in range(4))
        out.extend(prefix+f'.quantile.{i}.{j}' for i in range(2) for j in range(2))
        for i,row in enumerate(p['conditional_child']):
            out.extend(prefix+f'.conditional.{i}.{j}' for j,v in enumerate(row) if v is not None)
    return out
