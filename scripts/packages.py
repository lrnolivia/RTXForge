"""Pinned v3 runtime sourcing. Archives are never executed and payloads remain on Games."""
import pathlib,json,hashlib,urllib.request,urllib.parse,subprocess,shutil,zipfile,os
import transactions as t
import ui
import pipeline
from storage import storage
P=pathlib.Path
POLICY='RTXForge.NrPanel.v1'
def download(url,path,expected=None,blob=None,size=None):
    if path.exists():
        datahash=t.digest(path)
        if expected:t.need(datahash==expected,'Cached download drift: '+str(path))
        if blob:
            h=hashlib.sha1(b'blob '+str(path.stat().st_size).encode()+b'\0');h.update(path.read_bytes());t.need(h.hexdigest()==blob,'Cached Git blob mismatch')
        return path
    part=path.with_suffix(path.suffix+'.part');t.need(not part.exists(),'Incomplete download retained: '+str(part))
    path.parent.mkdir(parents=True,exist_ok=True)
    ui.line('Downloading',path.name)
    with urllib.request.urlopen(url,timeout=120) as src,part.open('xb') as out:shutil.copyfileobj(src,out)
    if expected:t.need(t.digest(part)==expected,'Downloaded SHA256 mismatch')
    if size:t.need(part.stat().st_size==size,'Downloaded size mismatch')
    if blob:
        h=hashlib.sha1(b'blob '+str(part.stat().st_size).encode()+b'\0');h.update(part.read_bytes());t.need(h.hexdigest()==blob,'Downloaded Git blob mismatch')
    part.rename(path);return path

def entries(archive):
    if archive.suffix.lower()=='.zip':
        with zipfile.ZipFile(archive) as z:raw=[(i.filename,i.file_size, i.is_dir(),i.external_attr>>16) for i in z.infolist()]
    else:
        seven=shutil.which('7zz') or shutil.which('7z');t.need(seven,'7z/7zz required; no system packages are installed automatically')
        listing=subprocess.check_output([seven,'l','-slt',str(archive)],text=True);raw=[]
        for block in listing.split('----------\n',1)[1].strip().split('\n\n'):
            row=dict(s.split(' = ',1) for s in block.splitlines() if ' = ' in s)
            t.need(not any('Link' in k for k in row),'Archive links refused')
            raw.append((row['Path'],int(row.get('Size','0')),row.get('Folder')=='+' or row.get('Attributes','').startswith('D'),0))
    import stat
    seen=set();result=[]
    for n,size,isdir,mode in raw:
        t.relative(n.rstrip('/'));t.need(n.casefold() not in seen and not stat.S_ISLNK(mode),'Unsafe archive entry');seen.add(n.casefold());t.need(size<1024**3,'Oversized archive member')
        if not isdir:result.append(n)
    return result

def extract(archive,member,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as out:
        if archive.suffix.lower()=='.zip':
            with zipfile.ZipFile(archive) as z,z.open(member) as src:shutil.copyfileobj(src,out)
        else:subprocess.run([shutil.which('7zz') or shutil.which('7z'),'x','-so','-mmt=1',str(archive),member],stdout=out,check=True)

def verify(folder,record):
    t.need(set(t.files(folder))=={n.casefold() for n in record['files']},'Payload listing drift')
    for n,h in record['files'].items():t.need(t.digest(folder/n)==h,'Payload hash drift: '+n)

def prepare(c,mode,readonly=False):
    root=storage(c,3*1024**3);cache=root/'packages'/c['sha256'];pkg=cache/'payload';record=cache/'files.json'
    if readonly:
        required=[record,*[root/'headless'/P(r['destination']).name for r in c['headless']]]
        if mode=='nr-mfg':required += [root/'nr/runtime.json',root/'nr/nvngx_dlssnr.dll']
        t.need(all(p.is_file() for p in required),'Payload not prepared; run Prepare first. Dry-run never downloads or writes cache.')
    if record.exists():manifest=t.read_json(record);verify(pkg,manifest)
    else:
        cache.mkdir(parents=True,exist_ok=True)
        archive=download(c['url'],cache/c['asset'],expected=c['sha256'])
        t.need(not pkg.exists(),'Partial extraction retained; inspect '+str(pkg));pkg.mkdir()
        for n in entries(archive):
            if n in ('OptiScaler.dll','OptiScaler.ini','nvngx.dll_dlssnr.dll') or n.startswith(('OptiScaler/','Licenses/')):extract(archive,n,pkg/n)
        t.need((pkg/'OptiScaler.dll').exists() and (pkg/'OptiScaler/streamline/sl.interposer.dll').exists(),'Unexpected v3 payload layout')
        manifest={'archive_sha256':c['sha256'],'files':{n:t.digest(pkg/n) for n in t.files(pkg).values()}};t.save_new(record,manifest)
    sources={n:(pkg/n,h) for n,h in manifest['files'].items()}
    for row in c['headless']:
        dest=root/'headless'/P(row['destination']).name
        url='https://raw.githubusercontent.com/ShyVortex/dlss-unlocked/v0.3.0/'+urllib.parse.quote(row['path'])
        download(url,dest,blob=row['git_blob'],size=row['size']);sources[row['destination']]=(dest,t.digest(dest))
    if mode=='nr-mfg':
        n=c['nr'];folder=root/'nr';nr=folder/'nvngx_dlssnr.dll';proof=folder/'runtime.json'
        if proof.exists():t.need(t.digest(nr)==t.read_json(proof)['sha256'],'NR runtime drift')
        else:
            url='https://github.com/'+n['repo']+'/releases/download/'+n['tag']+'/'+n['asset'];a=download(url,folder/n['asset'],expected=n['sha256']);members=[m for m in entries(a) if P(m).name.lower()=='nvngx_dlssnr.dll'];t.need('nvngx_dlssnr.dll' in members,'Expected root NR runtime absent');extract(a,'nvngx_dlssnr.dll',nr)
            t.need(100000000<nr.stat().st_size<250000000,'Unexpected NR runtime size');t.save_new(proof,{'sha256':t.digest(nr),'source_archive':n['sha256']})
        sources['nvngx_dlssnr.dll']=(nr,t.digest(nr))
    else:
        sources.pop('nvngx.dll_dlssnr.dll',None)
    custom=root/'loader/rtxforge-loader.json'
    bundled=P(__file__).resolve().parents[1]/'bundled-loader/rtxforge-loader.json'
    if not custom.exists() and bundled.exists():
        custom=bundled
        t.need(t.read_json(custom)['sha256']==c.get('bundled_loader_sha256'),'Bundled loader is not the pinned RTXForge build')
    if custom.exists():
        meta=t.read_json(custom);dll=custom.parent/'OptiScaler.dll';t.need(meta['policy']==POLICY and meta['upstream_commit']==c['commit'] and t.digest(dll)==meta['sha256'],'Custom loader identity mismatch');sources['OptiScaler.dll']=(dll,meta['sha256'])
    # Imported builds enforce NrPanel; stock builds keep the inactive panel.
    return pipeline.compose(sources,mode,c)

def import_loader(c,folder):
    root=storage(c,100*1024**2);meta=t.read_json(folder/'rtxforge-loader.json');dll=t.safe(folder/'OptiScaler.dll')
    t.need(meta['policy']==POLICY and meta['upstream_commit']==c['commit'],'Incompatible loader build metadata')
    t.need(t.digest(dll)==meta['sha256'] and POLICY.encode() in dll.read_bytes(),'Loader hash/policy marker mismatch')
    out=root/'loader';t.need(not out.exists(),'Loader already imported; retain it and select a new versioned state root for a new build')
    out.mkdir(parents=True);shutil.copyfile(dll,out/'OptiScaler.dll');t.save_new(out/'rtxforge-loader.json',meta);return out
