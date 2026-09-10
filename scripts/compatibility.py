"""Small, auditable per-game MFG route policy.

Native Streamline DLSS-G is the default. Rules here exist only for titles with
reproduced route-specific failures; they never change game-native DLSS/SL DLLs.
"""
import re

DEFAULT_ROUTE = 'native-streamline'

ROUTES = {
    'native-streamline': {
        'id': 'native-streamline-dlssg-ada-v5',
        'label': 'Native Streamline DLSS-G',
        'fg_input': 'dlssg',
        'fg_output': 'dlssg',
        'nvngx_replacement': 'none',
        'provider': 'y4my-native-dlssg',
    },

}

# Only reproduced exceptions belong here. Keep matching conservative.
_RULES = [
    {
        'route': 'native-streamline',
        'patterns': (r'\bcyberpunk 2077\b', r'\bcyberpunk2077\b'),
        'reason': 'Native Streamline DLSS-G reproduced with normal performance; Enabler MFG reproduced severe performance loss.',
    },
]


def route_for(target):
    """Return route metadata for a target without mutating it."""
    text = ' '.join(str(target.get(k, '')) for k in ('name', 'game', 'exe')).casefold()
    compact = re.sub(r'[^a-z0-9]+', '', text)
    searchable = text + ' ' + compact
    for rule in _RULES:
        if any(re.search(pattern, searchable, re.I) for pattern in rule['patterns']):
            return {**ROUTES[rule['route']], 'key': rule['route'], 'reason': rule['reason'], 'profiled': True}
    route = ROUTES[DEFAULT_ROUTE]
    return {**route, 'key': DEFAULT_ROUTE, 'reason': 'Default RTXForge MFG route.', 'profiled': False}
