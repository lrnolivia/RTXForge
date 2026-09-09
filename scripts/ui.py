"""Small accessible ANSI interface; no network/UI dependencies."""
import os,sys,re
COLORS={'green':'38;2;118;185;0','cyan':'38;2;93;220;232','red':'38;2;255;111;105','dim':'2','bold':'1'}
def clean(value):return re.sub(r'[\x00-\x1f\x7f-\x9f]',' ',str(value))
def style(text,color='green'):
    text=clean(text)
    return '\033['+COLORS[color]+'m'+text+'\033[0m' if sys.stdout.isatty() and not os.environ.get('NO_COLOR') else text

def banner():
    print('\n'+style('  RTXForge','bold')+'  '+style('GEFORCE TOOLS · BUILT FOR LINUX','green'))
    print(style('  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━','green'))
    print('  Your library. Your settings. A reversible upgrade.\n')
def title(s):print('\n  '+style(s,'cyan'))
def line(label,value):print('  '+style(label.ljust(17),'dim')+clean(value))
def error(s):print('  '+style('STOP  '+str(s),'red'),file=sys.stderr)
def prompt(s):
    if not sys.stdin.isatty():raise RuntimeError('Interactive input needs a terminal; use --targets and --apply --confirm BATCH')
    return input('  '+s+' ').strip()
def table(rows):
    print('  '+style(f'{"CODE":<7}{"GAME":<43}PROFILE','dim'))
    for code,name,profile in rows:print('  '+style(str(code).ljust(7))+clean(name)[:41].ljust(43)+style(profile,'cyan'))
def selection(raw,codes):
    raw=raw.upper().strip()
    if raw=='ALL':return set(codes)
    chosen=set(re.split(r'[\s,;]+',raw))-{''}
    if not chosen.issubset(set(codes)):raise ValueError('Unknown game code(s): '+', '.join(chosen-set(codes)))
    return chosen
