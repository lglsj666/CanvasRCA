"""Explicit compact source captions; unchanged text, values and default styles."""


def apply(design, profile='source_cards_v1'):
    if profile not in {'source_cards_v1', 'source_scopes_v2', 'source_reflow_v3', 'source_scopes_pack_v4'}:
        raise ValueError('Unregistered readable-card profile')
    design['readable_cards'] = profile
