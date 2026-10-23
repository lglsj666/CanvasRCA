"""Explicit sampled-pair budget component; historical 32-sample DTO unchanged."""
from decimal import Decimal,InvalidOperation


def validate(card):
    from .utils import keys,text,entity,number
    d=card['data'];keys(d,{'parent','child','parent_operation','child_operation','samples','support','complete','sampling_budget'})
    if card['unit']!='ms':raise ValueError('Budget pair duration unit')
    for key in ('parent','child'):entity(d[key])
    if d['parent']==d['child']:raise ValueError('Pair endpoints must differ')
    for key in ('parent_operation','child_operation'):text(d[key])
    if len(d['support'])!=2 or any(type(n)is not int or n<20 for n in d['support']):raise ValueError('Population support')
    budget=d['sampling_budget'];keys(budget,{'schema','limit','available','indices','source_sha256'})
    if budget['schema']!='ObservedRankSubsetV1' or budget['limit']!=8:raise ValueError('Unknown sampling budget')
    if not isinstance(budget['source_sha256'],str) or len(budget['source_sha256'])!=64:raise ValueError('Missing original pair source identity')
    if len(budget['available'])!=2 or len(budget['indices'])!=2:raise ValueError('Missing phase sample provenance')
    phases=('reference','current');spec=d['complete'];keys(spec,{'schema','thresholds','phases','values','sample_ids'})
    if spec['schema']!='CompleteMarginalsV1' or len(spec['phases'])!=2 or len(spec['thresholds'])!=2:raise ValueError('Population statistic schema')
    def numeric(v,integer=False):
        text(v)
        try:x=Decimal(v)
        except InvalidOperation as exc:raise ValueError('Invalid exact observed value') from exc
        if not x.is_finite() or x<0 or (integer and x!=x.to_integral_value()):raise ValueError('Nonnegative original number required')
        return x
    for v in spec['thresholds']:numeric(v)
    count=sum(min(8,n) for n in d['support'])
    if len(d['samples'])!=count or len(spec['values'])!=count or len(spec['sample_ids'])!=count:raise ValueError('Selected sample count')
    if len(set(spec['sample_ids']))!=count:raise ValueError('Duplicate selected observation')
    offset=0
    for i,p in enumerate(spec['phases']):
        keys(p,{'phase','n','sampled','binary','quantiles','conditional_child'})
        available=min(32,d['support'][i]);indices=[round(j*(available-1)/7) for j in range(8)]
        if budget['available'][i]!=available or budget['indices'][i]!=indices:raise ValueError('Unregistered observed-rank selection')
        if p['phase']!=phases[i] or numeric(p['n'],True)!=d['support'][i] or numeric(p['sampled'],True)!=8:raise ValueError('Phase/population/shown count mismatch')
        if len(p['binary'])!=4 or sum(numeric(v,True) for v in p['binary'])!=d['support'][i]:raise ValueError('Binary population count')
        if len(p['quantiles'])!=2 or any(len(q)!=2 or numeric(q[0])>numeric(q[1]) for q in p['quantiles']):raise ValueError('Population quantiles')
        for row in p['conditional_child']:
            if len(row)!=4 or row[0] not in {'0','1'}:raise ValueError('Conditional group')
            numeric(row[1],True)
            for v in row[2:]:
                if v is not None:numeric(v)
            if all(v is not None for v in row[2:]) and Decimal(row[2])>Decimal(row[3]):raise ValueError('Conditional quantile order')
        for j,index in enumerate(indices):
            sample=d['samples'][offset+j];keys(sample,{'phase','parent_ms','child_ms'})
            if sample['phase']!=phases[i] or spec['sample_ids'][offset+j]!=(('R' if i==0 else 'C')+str(index+1).zfill(2)):
                raise ValueError('Selected source sample identity')
            original=spec['values'][offset+j]
            if len(original)!=2:raise ValueError('Missing sample endpoint')
            for v,key in zip(original,('parent_ms','child_ms'),strict=True):
                number(sample[key])
                if float(numeric(v))!=sample[key]:raise ValueError('Exact value and observed glyph differ')
        offset+=8
