"""Install this AppImage under the user's persistent XDG data directory."""
from pathlib import Path
import os,shutil,subprocess,tempfile

def install():
    source=Path(os.environ['APPIMAGE']).resolve(strict=True)
    data=Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))
    if not data.is_absolute():raise ValueError('XDG_DATA_HOME must be absolute')
    root=data/'rtxforge/application';root.mkdir(parents=True,exist_ok=True)
    target=root/'RTXForge.AppImage'
    if source!=target:
        fd,name=tempfile.mkstemp(prefix='.update-',dir=root);os.close(fd);stage=Path(name)
        try:
            shutil.copyfile(source,stage);stage.chmod(0o755)
            with stage.open('rb') as f:os.fsync(f.fileno())
            if target.exists():shutil.copyfile(target,root/'RTXForge.previous.AppImage');(root/'RTXForge.previous.AppImage').chmod(0o755)
            os.replace(stage,target)
        finally:stage.unlink(missing_ok=True)
    icon=data/'icons/hicolor/scalable/apps/io.github.lrnolivia.RTXForge.svg';icon.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(Path(__file__).resolve().parents[1]/'gui/icons/hicolor/scalable/apps/io.github.lrnolivia.RTXForge.svg',icon)
    apps=data/'applications';apps.mkdir(parents=True,exist_ok=True)
    # Desktop Exec quoting is distinct from shell quoting; percent signs are field codes.
    quoted=str(target).replace('\\','\\\\').replace('"','\\"').replace('`','\\`').replace('$','\\$').replace('%','%%')
    desktop=apps/'io.github.lrnolivia.RTXForge.desktop'
    desktop.write_text('[Desktop Entry]\nType=Application\nName=RTXForge\nComment=GeForce tools for Linux\nExec="'+quoted+'"\nIcon=io.github.lrnolivia.RTXForge\nTerminal=false\nCategories=Game;Utility;\nStartupWMClass=io.github.lrnolivia.RTXForge\n')
    if shutil.which('update-desktop-database'):subprocess.run(['update-desktop-database',str(apps)],check=False,capture_output=True)
    return str(target)

if __name__=='__main__':print(install())
