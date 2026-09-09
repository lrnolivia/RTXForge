"""Focused reversible-cleanup check on disposable Games-drive fixtures only."""
import pathlib,sys,uuid,json
P=pathlib.Path
sys.path.insert(0,str(P(__file__).resolve().parents[1]/'scripts'))
import rtxforge as app,cleanup,transactions as t
from storage import storage
c=app.load_provider();root=storage(c)/'verification'/uuid.uuid4().hex;root.mkdir(parents=True)
c['storage']['root']=str(root/'state')
game=root/'fixture';game.mkdir();model=game/'nvngx_dlssnr.dll';model.write_bytes(b'NR fixture')
backup=game/'_DLSS5_Backup';(backup/'empty').mkdir(parents=True);(backup/'original.dll').write_bytes(b'original fixture')
control=game/'unrelated.dll';control.write_bytes(b'keep')
items=[{'path':str(p),**cleanup.snapshot(p)} for p in (model,backup)]
assert cleanup.discover([root],c)==[] # real scanner excludes the whole lab/recovery area
record=cleanup.apply(c,items)
assert not model.exists() and not backup.exists() and control.read_bytes()==b'keep'
model.write_bytes(b'external change')
try:cleanup.restore(c,record);raise AssertionError('drift accepted')
except t.Refusal:pass
model.unlink();assert cleanup.restore(c,record)==2
cleanup.restore(c,record,True)
assert [{'path':str(p),**cleanup.snapshot(p)} for p in (model,backup)]==items
assert control.read_bytes()==b'keep'
report={'observed_utc':t.now(),'success':True,'checks':['all backups verified before cleanup','recovery restores files and empty directories','external drift refused','unrelated files retained','lab/recovery excluded from scan'],'real_games_modified':False,'runtime_verified':False}
(root/'result.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));print(root/'result.json')
