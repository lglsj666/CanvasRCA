"""Trace baseline/current comparisons with explicitly labeled latency axes."""
import math

from . import human_dashboard as hd


def source_trace_exposure(view, window):
    """Public source span range; no identity/label/file or injection-time access."""
    import numpy as np
    import pandas as pd
    from .panels import resolve_time_seconds
    if view.traces_df.empty:return {'status':'no_source_trace_range'}
    clock=pd.to_numeric(view.metrics_df['timestamp'],errors='coerce').to_numpy(dtype=float)
    clock=clock[np.isfinite(clock)]
    if not len(clock) or window is None:return {'status':'no_source_trace_range'}
    ts=resolve_time_seconds(view.traces_df,(float(clock.min()),float(clock.max())))
    ts=np.asarray(ts,dtype=float);ts=ts[np.isfinite(ts)]
    if len(ts)<2:return {'status':'no_source_trace_range'}
    if any(isinstance(v,bool) or not math.isfinite(float(v)) for v in window) or len(window)!=2:
        raise ValueError('invalid public trace analysis interval')
    start,end=map(float,window)
    if end<=start:raise ValueError('invalid public trace interval order')
    lower,upper=float(ts.min()),float(ts.max())
    current=max(0.,min(upper,end)-max(lower,start));baseline=upper-lower-current
    if current<=0 or baseline<=0:return {'status':'no_source_trace_range'}
    return {'status':'finite_source_trace_range','baseline_s':baseline,'current_s':current,
            'source_range_s':upper-lower,'source_finite_rows':len(ts)}


def rate_lines(payload):
    rate=payload['observed_span_rate'];d0,d1=(rate[k] for k in ('baseline_minutes','current_minutes'))
    b,c=(rate[k] for k in ('baseline_per_minute','current_per_minute'))
    if any(isinstance(v,bool) or not math.isfinite(float(v)) for v in (d0,d1,b,c)) or min(d0,d1)<=0 or min(b,c)<0:
        raise ValueError('invalid displayed span rate')
    if not math.isclose(b,payload['count_base']/d0) or not math.isclose(c,payload['count_fault']/d1):
        raise ValueError('span rate is not bound to count/exposure')
    expected=c/b if b else None
    if (expected is None)!=(rate['ratio'] is None) or (expected is not None and not math.isclose(rate['ratio'],expected)):
        raise ValueError('span rate ratio mismatch')
    ratio=f"{hd._fmt(expected)}×" if expected is not None else 'no baseline events'
    return f"Observed spans/min {hd._fmt(b)} → {hd._fmt(c)}    ratio {ratio}"


def paint_trace_axis(draw,box,facts,encoding,colors,rate=False):
    x0,y0,x1,y1=box
    rows=sorted([f for f in facts if f['field']=='trace_summary_entry'],key=lambda f:f['payload']['entry_index'])
    if any(f not in rows for f in facts):
        raise ValueError('labeled trace axis does not implement additional trace context fields')
    width=x1-x0-32
    header='GREEN = baseline    RED = current'
    if rows and rate:
        durations=[(f['payload']['observed_span_rate']['baseline_minutes'],f['payload']['observed_span_rate']['current_minutes']) for f in rows]
        if any(d!=durations[0] for d in durations):raise ValueError('inconsistent public trace exposure')
        d0,d1=durations[0];header=f'GREEN = baseline ({hd._fmt(d0)} min)    RED = current ({hd._fmt(d1)} min)'
    if any(('observed_span_rate' in f['payload'])!=rate for f in rows):raise ValueError('trace rate evidence/encoding mismatch')
    header_font=hd._single_line_font(draw,header,width,start=13,floor=11) if rate else hd._font(13,True)
    draw.text((x0+16,y0+40),header,font=header_font,fill=colors['text'])
    draw.text((x0+16,y0+64),'Horizontal position = exclusive p95 latency (ms), NOT time',font=hd._single_line_font(draw,'Horizontal position = exclusive p95 latency (ms), NOT time',width,start=13,floor=11),fill=colors['muted'])
    top=y0+96;row_h=(y1-top-12)/max(1,len(rows))
    font=hd._font(14);line_h=font.getbbox('Ag')[3]-font.getbbox('Ag')[1]+8
    values=[float(f['payload'][k]) for f in rows for k in ('exl_p95_base_ms','exl_p95_fault_ms')]
    if any(not math.isfinite(v) or v<0 for v in values):
        raise ValueError('labeled trace axis needs finite nonnegative latencies')
    upper=max(1.,*values)*1.05
    ticks=[0.]+[10.**p for p in range(-3,8) if 10.**p<=upper]
    # Limit labels by measured separation, without changing the data scale.
    result={}
    for i,fact in enumerate(rows):
        p=fact['payload'];y=top+i*row_h
        title=f"{p['service']} · {p['operation']}"
        lines=hd._wrap(draw,title,hd._font(15,True),width)
        for line in lines:
            draw.text((x0+16,y),line,font=hd._font(15,True),fill=colors['text']);y+=line_h
        count=f"Count {p['count_base']} → {p['count_fault']}    Δlog2 {hd._fmt(p['count_lfc'])}"
        latency=f"Exclusive p95 ms {hd._fmt(p['exl_p95_base_ms'])} → {hd._fmt(p['exl_p95_fault_ms'])}    Δlog2 {hd._fmt(p['latency_lfc'])}"
        texts=(count,rate_lines(p),latency) if rate else (count,latency)
        for text in texts:
            for line in hd._wrap(draw,text,font,width):
                draw.text((x0+16,y),line,font=font,fill=colors['text']);y+=line_h
        if y+54>top+(i+1)*row_h:raise ValueError('insufficient trace row height for complete axis')
        left,right=x0+34,x1-45
        pos=lambda v:left+math.log1p(v)/math.log1p(upper)*(right-left)
        axis=y+18
        draw.line((left,axis,right,axis),fill=colors['grid'],width=2)
        previous_right=-math.inf
        for tick in ticks:
            x=pos(tick);text=hd._fmt(tick);tf=hd._font(11)
            tw=draw.textlength(text,font=tf)
            if x-tw/2<previous_right+14:continue
            draw.line((x,axis-4,x,axis+4),fill=colors['border'],width=1)
            draw.text((x-tw/2,axis+9),text,font=tf,fill=colors['muted']);previous_right=x+tw/2
        xb,xc=pos(float(p['exl_p95_base_ms'])),pos(float(p['exl_p95_fault_ms']))
        if encoding=='trace_baseline_fault_bars':
            draw.line((left,axis-10,xb,axis-10),fill=colors['base'],width=5)
            draw.line((left,axis-2,xc,axis-2),fill=colors['current'],width=5)
        else:
            draw.line((xb,axis-8,xc,axis-8),fill=colors['border'],width=2)
            for x,color in ((xb,colors['base']),(xc,colors['current'])):
                draw.ellipse((x-5,axis-13,x+5,axis-3),fill=color)
        bottom=top+(i+1)*row_h
        draw.line((x0+12,bottom-5,x1-12,bottom-5),fill=colors['grid'],width=1)
        result[fact['fact_id']]=[{'kind':'labeled_trace_latency_axis','bbox':[x0+12,top+i*row_h,x1-12,bottom-5],
                               'axis_unit':'ms','axis_scale':'log1p','baseline':{'point':[xb,axis-8]},
                               'current':{'point':[xc,axis-8]},'axis_max':upper}]
        if rate:result[fact['fact_id']][0]['observed_span_rate']=dict(p['observed_span_rate'])
    return result
