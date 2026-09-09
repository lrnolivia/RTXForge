"""Toolkit-free desktop operations. A UI owns selection and review; writes stay explicit."""
from pathlib import Path
import rtxforge as app
import discovery,planning,packages,profiles,cleanup,transactions as t
import re,datetime,hardware
from storage import storage

class DesktopService:
    def __init__(self,provider=None):
        self.config=app.load_provider(provider)

    def hardware(self):return hardware.detect()

    def libraries(self):
        return sorted(discovery.candidate_libraries(),key=discovery.count_manifests,reverse=True)

    def scan(self,library,extra=()):
        found=discovery.discover_games(Path(library),discovery.discover_nonsteam_roots(Path(library),[]),include_unavailable=True) if library else []
        for path in extra:
            p=Path(path).resolve()
            g=discovery.inspect_game(discovery.Game('',p.name,str(p),'Folder'))
            if g.exe:found.append(g)
        rows=[];seen=set()
        for g in found:
            root=Path(g.root).resolve()
            if str(root) in seen:continue
            seen.add(str(root))
            native=any(Path(p).name.lower() in ('nvngx_dlssg.dll','sl.dlss_g.dll') and 'optiscaler' not in [q.lower() for q in Path(p).relative_to(g.root).parts] for p in g.upscalers)
            reason='No Windows executable found' if not g.exe else 'Anti-cheat detected' if g.anti_cheat else 'No native DLSS-G detected' if not native else ''
            exe=Path(g.exe).relative_to(g.root).as_posix() if g.exe else ''
            config=Path(g.exe).parent/'OptiScaler.ini' if g.exe else root/'OptiScaler.ini'
            ini=discovery.get_ini_values_all(config)
            installed=config.is_file()
            row={'name':g.name,'game':str(root),'exe':exe,'source':g.type,'blocked':reason,'appid':g.appid,
                 'library':str(library or root.parent),'installed':installed,
                 'profile':('NR + MFG' if ini.get('DlssNr',{}).get('Enabled','false').lower()=='true' else 'MFG Only') if installed else 'Not installed'}
            if g.manifest:
                try:
                    text=Path(g.manifest).read_text()
                    for key,out in [('SizeOnDisk','size_bytes'),('LastUpdated','updated')]:
                        match=re.search(r'"'+key+r'"\s+"(\d+)"',text)
                        if match:row[out]=int(match[1])
                except OSError:pass
            rows.append(row)
        return sorted(rows,key=lambda r:r['name'].casefold())

    def scan_all(self,extra=()):
        import ui
        rows=[];seen=set();libraries=self.libraries()
        for index,library in enumerate(libraries):
            for row in ui.work(f'Scanning library {index+1}/{len(libraries)}',self.scan,library):
                if row['game'] not in seen:rows.append(row);seen.add(row['game'])
        for row in self.scan(None,extra):
            if row['game'] not in seen:rows.append(row);seen.add(row['game'])
        return sorted(rows,key=lambda r:r['name'].casefold())

    def prepare(self,rows,mode,operation,adopt=False):
        import ui
        if operation!='uninstall':
            host=self.hardware()
            if not host['ready']:return {'kind':'batch','operation':operation,'title':operation.title(),'plans':[],'rows':[],'blocked':[{'name':'Hardware check','reason':host['reason']}]}
        blocked=[{'name':r['name'],'reason':r.get('blocked') or 'No executable found'} for r in rows if not r.get('exe') or (operation!='uninstall' and r.get('blocked'))]
        eligible=[r for r in rows if r.get('exe') and (operation=='uninstall' or not r.get('blocked'))]
        if not eligible:return {'kind':'batch','operation':operation,'title':operation.title(),'plans':[],'blocked':blocked,'rows':[]}
        targets=app.normalize_targets([{**r,'mode':mode} for r in eligible]);state=storage(self.config)
        sources={} if operation=='uninstall' else ui.work('Preparing and verifying '+profiles.MODES[mode],packages.prepare,self.config,mode)
        ready=[]
        for index,row in enumerate(targets,1):
            try:
                label=f'Checking {index}/{len(targets)} · '+row.get('name',Path(row['game']).name)
                plan=ui.work(label,planning.remove,row,state) if operation=='uninstall' else ui.work(label,planning.make,row,state,sources,operation,adopt)
                if plan['conflicts']:blocked.append({'name':row['name'],'reason':friendly('\n'.join(plan['conflicts']))})
                elif plan['changes']:ready.append(plan)
                else:blocked.append({'name':row['name'],'reason':'Already up to date — no changes needed'})
            except (t.Refusal,OSError,ValueError) as ex:blocked.append({'name':row['name'],'reason':friendly(str(ex))})
        return {'kind':'batch','title':{'install':'Install / update','repair':'Repair','uninstall':'Uninstall OptiScaler'}[operation],
                'operation':operation,'plans':ready,'blocked':blocked,'rows':[{'name':Path(p['game']).name,'detail':f"{len(p['changes'])} file changes · {profiles.MODES[p['mode']]}"+(f" · Proton override: {Path(p['proxy']).stem}=n,b" if p.get('proxy') else '')} for p in ready]}

    def recoveries(self):
        root=storage(self.config);rows=[]
        for path in sorted((root/'batches').glob('*/batch.json'),reverse=True):
            doc=t.read_json(path)
            if doc['status']!='rolled-back':rows.append({'kind':'rollback','path':str(path),'name':'Batch '+path.parent.name,'detail':doc['status']})
        for path in sorted((root/'cleanup').glob('*/cleanup.json'),reverse=True):
            doc=t.read_json(path)
            if doc['status'] in ('complete','removing','interrupted'):rows.append({'kind':'restore-cleanup','path':str(path),'name':'Cleanup '+path.parent.name,'detail':doc['status']})
        return rows

    def review_recovery(self,row):
        root=storage(self.config);path=t.safe(row['path']);details=[]
        if row['kind']=='rollback':
            t.need(path.is_relative_to(root/'batches'),'Invalid batch record')
            doc=t.read_json(path);t.need(doc['status']!='rolled-back','Already restored')
            for value in reversed(doc['transactions']):
                state=t.safe(value);t.need(state.is_relative_to(root/'transactions'),'Invalid transaction path')
                if not (state/'transaction.json').exists():continue
                if t.read_json(state/'transaction.json')['status'] in ('preparing','rolled-back'):continue
                view=t.rollback_transaction(state);details.append({'name':Path(view['game']).name,'detail':str(len(view['files']))+' files to restore'})
        else:details=[{'name':'Cleanup recovery','detail':str(cleanup.restore(self.config,path))+' files to restore'}]
        return {'kind':row['kind'],'path':str(path),'title':'Restore recorded changes','rows':details,'blocked':[]}

    def review_cleanup(self):
        items=cleanup.discover([Path(self.config['storage']['mount'])],self.config)
        return {'kind':'cleanup','title':'Global DLSS5 cleanup','items':items,'blocked':[],
                'rows':[{'name':Path(r['path']).name,'detail':r['path']} for r in items]}

    def execute(self,review):
        # The desktop must pass the exact in-memory review shown to the user.
        kind=review['kind']
        if kind=='batch':return str(app.apply_batch(self.config,review['plans']))
        if kind=='cleanup':return str(cleanup.apply(self.config,review['items']))
        if kind=='restore-cleanup':cleanup.restore(self.config,Path(review['path']),True);return review['path']
        t.need(kind=='rollback','Unknown action')
        args=app.parser().parse_args(['rollback','--batch',review['path'],'--apply','--confirm','ROLLBACK'])
        app.rollback(args,self.config);return review['path']


def friendly(message):
    return (message.replace('No ownership record; no broad cleanup is performed','No install record found. RTXForge cannot safely identify which files to remove.')
            .replace('Competing/unowned graphics file:','Another graphics tool uses:')
            .replace('Unowned replacement:','An existing file needs identification:')
            .replace('Owned binary drift:','An installed file changed:')
            .replace('Changed owned file:','An installed file changed:')
            .replace('provide manifest or explicitly adopt recognized files','enable “Recognize previous installs” in Settings if this is OptiScaler'))
