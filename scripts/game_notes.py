"""User-recorded test results. Never deploys, launches, or modifies game files."""
from pathlib import Path
import hashlib,json,zipfile,datetime,stat
import transactions as t
import engine_bridge,library_media
from storage import storage
STATES=('Untested','Working','Problem','Bench')
def root(config):return storage(config)/'desktop/reports'
def path(config,game):return root(config)/'games'/(hashlib.sha256(str(game).encode()).hexdigest()[:24]+'.json')
def load(config,game):
    try:return json.loads(path(config,game).read_text())
    except (OSError,ValueError):return {'status':'Untested','notes':'','sessions':[]}
def save(config,game,record):
    t.need(record.get('status') in STATES,'Unknown test status')
    t.atomic_file(path(config,game),json.dumps(record,indent=2).encode(),0o600)
def start(config,game):
    record=load(config,game['game']);t.need(not record.get('active'),'Finish the current test first')
    record['active']={'started':t.now(),'selected_package':engine_bridge.providers()[library_media.load_settings(config).get('runtime_provider','y4my')],'profile':game.get('profile'),'name':game['name']}
    # Config pin is package provenance, NOT proof this DLL is installed.
    directory=Path(game['game'])/Path(game['exe']).parent
    record['active']['installed_proxies']={p.name:t.digest(p) for p in directory.iterdir() if p.name.lower() in {'dxgi.dll','winmm.dll','version.dll'} and p.is_file() and not p.is_symlink()}
    save(config,game['game'],record);return record

def finish(config,game):
    record=load(config,game['game']);session=record.get('active');t.need(session,'Start a test record first')
    session['finished']=t.now();session['logs']=[]
    destination=root(config)/'logs'/hashlib.sha256(game['game'].encode()).hexdigest()[:24]/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    directory=Path(game['game'])/Path(game['exe']).parent
    # Exact adjacent diagnostic names only; no recursive home/prefix/save collection.
    for name in ('OptiScaler.log','sl.log','sl.dlss_g.log','sl.interposer.log'):
        p=directory/name
        try:
            import os
            fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
            with os.fdopen(fd,'rb') as source:
                st=os.fstat(source.fileno())
                if not stat.S_ISREG(st.st_mode):continue
                source.seek(max(0,st.st_size-4*1024**2));data=source.read(4*1024**2)
            out=destination/name;t.atomic_file(out,data,0o600);session['logs'].append(str(out))
        except OSError:continue
    session['observation']='User test record; captured logs may include earlier runs. No automatic runtime success inference.'
    record.setdefault('sessions',[]).append(session);record.pop('active',None);save(config,game['game'],record);return record

def export(config,games):
    out=root(config)/('rtxForge-report-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.zip');out.parent.mkdir(parents=True,exist_ok=True)
    records=[]
    with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for game in games:
            record=load(config,game['game']);records.append({'name':game['name'],'game':game['game'],**record})
            for session in record.get('sessions',[]):
                for value in session.get('logs',[]):
                    p=Path(value)
                    if p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(root(config).resolve()/'logs'):
                        z.write(p,str(p.relative_to(root(config))))
        z.writestr('library.json',json.dumps(records,indent=2));z.writestr('package.json',json.dumps(config,indent=2))
    out.chmod(0o600);return out
