"""Feature composition independent of the pinned, shared MFG provider."""
from pathlib import Path
import transactions as t
NR_NAMES={'nvngx_dlssnr.dll','nvngx.dll_dlssnr.dll','sl.dlss_nr.dll'}
PIPELINE='nvngx-headless-nr-separate-v1'

def compose(sources,mode,config):
    t.need(mode in {'mfg-only','nr-mfg'},'Unsupported graphics pipeline')
    result=dict(sources)
    if mode=='mfg-only':
        result={n:v for n,v in result.items() if Path(n).name.lower() not in NR_NAMES}
    else:
        for name in ('nvngx_dlssnr.dll','nvngx.dll_dlssnr.dll'):
            t.need(name in result,'NR component missing: '+name)
        expected=config['nr'].get('runtime_sha256')
        t.need(expected and result['nvngx_dlssnr.dll'][1]==expected,'NR model does not match the pinned patched runtime')
    t.need('OptiScaler/dlss-enabler-headless.dll' in result,'Headless MFG provider missing')
    return result

def describe(sources,mode,config):
    return {'pipeline':PIPELINE,'mode':mode,'core_provider':config['repo'],
            'core_commit':config['commit'],'mfg_input_default':'nvngxfg',
            'mfg_output_default':'dlssg','mfg_provider':'arturs-headless',
            'nr_provider':config['nr']['repo'] if mode=='nr-mfg' else None,
            'nr_enabled_at_install':mode=='nr-mfg',
            'private_streamline_present':any('/streamline/' in n for n in sources),
            'runtime_verified':False,
            'files':{n:{'sha256':h,'feature':'nr' if Path(n).name.lower() in NR_NAMES else 'shared-mfg'} for n,(_,h) in sorted(sources.items())}}
