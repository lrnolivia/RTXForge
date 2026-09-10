"""Accept one explicitly downloaded, compiled Proton runtime artifact for packaging."""
from pathlib import Path
import argparse,hashlib,json,shutil
p=argparse.ArgumentParser();p.add_argument('artifact',type=Path);p.add_argument('--fork-commit',required=True);p.add_argument('--run-url',required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[1];meta=json.loads((a.artifact/'rtxforge-loader.json').read_text(encoding='utf-8-sig'));dll=a.artifact/'OptiScaler.dll';data=dll.read_bytes();c=json.loads((root/'provider.json').read_text())
assert data[:2]==b'MZ' and meta['sha256']==hashlib.sha256(data).hexdigest()
assert meta['upstream_commit']==c['commit'] and meta['fork_commit']==a.fork_commit
assert meta['policy']=='RTXForge.NrPanel.v1' and 'RTXForge.NativeMfgMenu.v3e' in meta['capabilities']
assert b'RTXForge.NativeMfgMenu.v3e' in data and b'RTXForge.NrPanel.v1' in data
out=root/'dist/panel-loader';out.mkdir(exist_ok=True)
shutil.copyfile(dll,out/'OptiScaler.dll');(out/'rtxforge-loader.json').write_text(json.dumps(meta,indent=2)+'\n')
c['bundled_loader_sha256']=meta['sha256'];c['runtime_fork']={'repo':'lrnolivia/RTXForge-MFG','commit':a.fork_commit,'build':a.run_url,'capabilities':meta['capabilities']}
(root/'provider.json').write_text(json.dumps(c,indent=2)+'\n')
(root/'docs/proton-runtime-build.json').write_text(json.dumps({**meta,'run':a.run_url,'runtime_verified':False},indent=2)+'\n')
print('Pinned compiled Proton runtime: '+meta['sha256'])
