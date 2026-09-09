"""Two routes only. NR+MFG is enabled before the process starts."""
import transactions as t
MODES={'nr-mfg':'NR + MFG','mfg-only':'MFG Only'}
ROUTE='arturs-headless-proton-stable-v3'
def render(template,existing,mode):
    t.need(mode in MODES,'Only NR + MFG and MFG Only are supported')
    text=template;old=t.ini(existing) if existing else None
    if old:
        for section in old.sections():
            if section.lower()=='mfgunlock':continue
            for k,v in old[section].items():text=t.setvalue(text,section,k,v)
    def put(section,values):
        nonlocal text
        for k,v in values.items():text=t.setvalue(text,section,k,str(v))
    # Migrate the v3 route once, then keep user choices (even when switching NR mode).
    sentinel=old.get('BazziteInstaller','MfgRoute',fallback='') if old else ''
    if sentinel!=ROUTE:
        put('FrameGen',{'Enabled':'true','FGInput':'nvngxfg','FGOutput':'dlssg','FGNvngxReplacement':'arturs'})
        put('DLSSG',{'AdaMfgUnlock':'true','AdaBlackwellKernels':'true','UseGamesReflexMarkers':'auto','InterpolationCount':'auto','OverrideInterpolationCount':'auto','OverrideForceDMFG':'false','ForceDMFG':'false'})
        put('NvApi',{'DisableFlipMetering':'true','DisableReflexSync':'true'})
        put('BazziteInstaller',{'MfgRoute':ROUTE})
    nr=mode=='nr-mfg'
    profile=old.get('RTXForge','NrProfile',fallback='') if old else ''
    if nr and profile!='nr70-startup-v1':
        put('Upscalers',{'Dx12Upscaler':'dlss'})
        put('DlssNr',{'DualFeature':'true','PreUpscale':'false','DualEnlarger':'dlss','Passes':'1'})
        put('Sharpness',{'Shader':'rcas','OverrideSharpness':'true','Sharpness':'0.30'})
        put('CAS',{'Enabled':'true'})
        put('RTXForge',{'NrProfile':'nr70-startup-v1'})
    # Selection is an explicit request to install this effect already on/off, never hot-enable it.
    put('DlssNr',{'Enabled':str(nr).lower()})
    if nr:put('DlssNr',{'WorkingScale':'0.70'})
    put('RTXForge',{'Pipeline':'nvngx-headless-nr-separate-v1','Mode':mode,'NrPanel':'1' if nr else '0'})
    if not old:
        put('Menu',{'OverlayMenu':'true'});put('Log',{'LogToFile':'true','LogLevel':'2'})
    t.ini(text)
    return text
