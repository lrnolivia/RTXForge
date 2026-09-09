import json,pathlib,sys,re,shutil,subprocess
import transactions as e
P=pathlib.Path
def storage(c, required=0):
    s = c['storage']
    mount = e.safe(s['mount'])
    root = e.safe(s['root'])
    e.need(root.is_relative_to(mount / 'Ada-Lab') and root != mount / 'Ada-Lab', 'State must be below verified Games/Ada-Lab')
    e.need(sys.platform == 'linux', 'Windows: preview/configuration reuse supported; Bazzite storage adapter required for mutation')
    r = json.loads(subprocess.check_output(['findmnt', '--json', '--target', str(mount), '--output', 'TARGET,FSTYPE,UUID'], text=True))['filesystems']
    r = [row for row in r if row['fstype'] != 'autofs']
    e.need(len(r) == 1 and r[0]['target'] == str(mount) and (r[0]['fstype'] == 'btrfs') and (r[0]['uuid'] == s['uuid']), 'Games mount/UUID mismatch; no storage fallback')
    for line in P('/proc/self/mountinfo').read_text().splitlines():
        raw = line.split()[4]
        mp = P(re.sub('\\\\([0-7]{3})', lambda m: chr(int(m[1], 8)), raw))
        e.need(not mp.is_relative_to(mount / 'Ada-Lab'), 'Nested mount under Ada-Lab refused')
    parent = root
    while not parent.exists():
        parent = parent.parent
    e.need(parent.stat().st_dev == mount.stat().st_dev, 'Wrong state device')
    e.need(shutil.disk_usage(mount).free >= s['reserve_bytes'] + required, 'Insufficient Games space; reserve preserved')
    return root
