"""One sequential desktop review/apply/recovery check on disposable Games fixtures."""
import pathlib,sys,uuid,struct,json
from unittest.mock import patch
P=pathlib.Path
sys.path.insert(0,str(P(__file__).resolve().parents[1]/'scripts'))
from desktop_service import DesktopService
from storage import storage
import packages,transactions as t,ui
service=DesktopService();root=storage(service.config)/'verification'/uuid.uuid4().hex;root.mkdir(parents=True)
service.config['storage']['root']=str(root/'state');source=root/'payload';source.mkdir();sources={}
for n,data in {'OptiScaler.dll':b'OptiScaler synthetic','OptiScaler.ini':b'[DlssNr]\nEnabled=false\n','OptiScaler/dlss-enabler-headless.dll':b'synthetic'}.items():
 p=source/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);sources[n]=(p,t.digest(p))
rows=[]
for name in ('Ready','Blocked'):
 game=root/name;game.mkdir();pe=bytearray(70);pe[:2]=b'MZ';struct.pack_into('<I',pe,60,64);pe[64:]=b'PE\0\0\x64\x86';(game/'Game.exe').write_bytes(pe);(game/'nvngx_dlssg.dll').write_bytes(b'native');(game/'save.dat').write_bytes(b'preserve')
 rows.append({'name':name,'game':str(game),'exe':'Game.exe','source':'fixture','blocked':''})
(P(rows[1]['game'])/'winmm.dll').write_bytes(b'unknown loader')
events=[]
with ui.report_to(events.append),patch.object(packages,'prepare',return_value=sources):
 review=service.prepare(rows,'mfg-only','repair')
 assert len(review['plans'])==1 and review['blocked'][0]['name']=='Blocked'
 assert not (P(rows[0]['game'])/'dxgi.dll').exists() # review never deploys
 record=service.execute(review)
 assert (P(rows[0]['game'])/'dxgi.dll').exists() and not (P(rows[1]['game'])/'dxgi.dll').exists()
 recovery=service.review_recovery({'kind':'rollback','path':record});service.execute(recovery)
 assert not (P(rows[0]['game'])/'dxgi.dll').exists()
assert all((P(r['game'])/'save.dat').read_bytes()==b'preserve' for r in rows)
assert any(e['kind']=='progress' for e in events)
(root/'desktop-result.json').write_text(json.dumps({'success':True,'observed_utc':t.now(),'real_game_writes':False,'checks':['read-only review','blocked exclusion','explicit apply','recovery','progress events','save controls preserved']},indent=2))
print('PASS: desktop review/apply/recovery and progress; synthetic fixtures only')
print(root/'desktop-result.json')
