#!/usr/bin/env python3
"""Native GNOME poster library. All engine work is serialized off the GTK thread."""
from pathlib import Path
import sys,threading,time,traceback,argparse,datetime
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import gi
gi.require_version('Gtk','4.0');gi.require_version('Adw','1')
from gi.repository import Gtk,Adw,GLib,Gio,Gdk,Graphene,Pango,GdkPixbuf
import ui,library_media
from desktop_service import DesktopService

CSS=b'''
.hero-title { font-size: 29px; font-weight: 800; letter-spacing: -0.8px; }
.eyebrow { color: #bdd897; font-weight: 800; font-size: 10px; letter-spacing: 2px; }
.hero { background: alpha(@window_fg_color,0.045); border: 1px solid alpha(@window_fg_color,0.06); border-radius: 18px; padding: 20px 24px; }
.forge-primary { background: #bdd897; color: #1c2316; font-weight: 800; padding: 10px 18px; }
.forge-primary:hover { background: #dcefc1; }
.bulk-remove { color: #ff928c; padding: 10px 16px; }
.pill { border-radius: 99px; padding: 5px 10px; background: alpha(@window_fg_color,0.07); font-size: 11px; }
.game-card { border-radius: 14px; background: @card_bg_color; border: 2px solid alpha(@window_fg_color,0.06); }
.game-card.selected { border-color: #bdd897; box-shadow: 0 2px 12px alpha(#76b900,0.22); }
.poster-button { padding: 0; border: 0; border-radius: 11px 11px 0 0; }
.poster { border-radius: 11px 11px 0 0; background: #242426; }
.poster-fallback { color: #a5a5a8; padding: 22px; font-weight: 800; font-size: 19px; }
.card-info { padding: 10px 12px 12px; }
.card-title { font-weight: 800; font-size: 13px; }
.card-meta { font-size: 10px; opacity: 0.7; }
.cover-badge { background: alpha(#111a10,0.90); color: #dcefc1; padding: 5px 8px; border-radius: 8px; font-size: 10px; font-weight: 700; }
.cover-badge.unavailable { color: #ffb3ad; }
.selection-bar { padding: 12px 20px; background: alpha(@window_fg_color,0.04); }
.status-strip { padding: 8px 20px; font-size: 12px; }
.panel-body { padding: 18px 24px; }
.profile-toggle:checked { background: alpha(@window_fg_color,0.13); color: @window_fg_color; }
.progress-orb { border-radius: 999px; background: alpha(@window_fg_color,0.06); padding: 18px; }
.progress-title { font-size: 22px; font-weight: 800; }
'''

def label(text,css=None):
    w=Gtk.Label(label=str(text),xalign=0,wrap=True)
    if css:w.add_css_class(css)
    return w
def button(text,fn,css=None):
    w=Gtk.Button(label=text);w.connect('clicked',fn)
    if css:w.add_css_class(css)
    return w
def margins(w,n=16):
    for edge in ('start','end','top','bottom'):getattr(w,'set_margin_'+edge)(n)
def clear(box):
    while box.get_first_child():box.remove(box.get_first_child())
def row(title,subtitle=''):
    w=Adw.ActionRow(title=str(title),subtitle=str(subtitle));w.set_use_markup(False);return w

def demo_games():
    titles=[('Cyberpunk 2077','1091500'),('Hogwarts Legacy','990080'),('PRAGMATA','3357650'),('Star Wars Outlaws','2842040'),('Avatar: Frontiers of Pandora','2840770'),('Forza Horizon 6','')]
    return [{'name':n,'appid':a,'game':'/preview/'+n,'exe':'Game.exe','source':'Steam' if a else 'Non-Steam','library':'Games drive','blocked':'','installed':i<3,'profile':'MFG Only' if i<3 else 'Not installed'} for i,(n,a) in enumerate(titles)]

class Window(Adw.ApplicationWindow):
    def __init__(self,application,options):
        super().__init__(application=application,title='RTXForge',default_width=1160,default_height=820)
        self.options=options;self.service=DesktopService(options.provider)
        self.settings=dict(library_media.DEFAULTS) if options.demo else library_media.load_settings(self.service.config)
        self.settings.setdefault('dark',True);self.hardware_info={'ready':True,'gpu':'Preview GPU','reason':'Preview mode'} if options.demo else None;self.games=[];self.cards={};self.mode='mfg-only';self.filter='all'
        self.busy=False;self.task_kind='';self.pending=None;self.cancel_art=threading.Event();self.log=[];self.dialog=None;self.review=None;self.action_buttons=[]
        self.connect('close-request',self.close_request)
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.PREFER_DARK if self.settings['dark'] else Adw.ColorScheme.DEFAULT)
        self.overlay=Adw.ToastOverlay();self.set_content(self.overlay);outer=Gtk.Box(orientation=Gtk.Orientation.VERTICAL);self.overlay.set_child(outer)
        header=Adw.HeaderBar();header.set_title_widget(Adw.WindowTitle(title='RTXForge',subtitle='Your whole library. One place.'))
        self.refresh=button('Refresh',lambda *_:self.scan());header.pack_start(self.refresh)
        self.add=button('Add game',self.choose_folder);header.pack_start(self.add)
        header.pack_end(button('Settings',self.show_settings));header.pack_end(button('Activity',self.show_activity));outer.append(header)
        top=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=14);margins(top,18);outer.append(top)
        hero=Gtk.Box(spacing=20);hero.add_css_class('hero');top.append(hero)
        title=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=7,hexpand=True);hero.append(title)
        title.append(label('GEFORCE / BUILT FOR LINUX','eyebrow'));title.append(label('Forge your entire library.','hero-title'))
        self.stats=label('Finding your games…','dim-label');title.append(self.stats)
        self.hardware_label=label('Preview mode · no game writes' if options.demo else 'Checking system hardware…','card-meta');title.append(self.hardware_label)
        bulk=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8,valign=Gtk.Align.CENTER);hero.append(bulk)
        self.install_all=button('Install entire library',lambda *_:self.launch_action('install',True),'forge-primary');bulk.append(self.install_all)
        self.uninstall_all=button('Uninstall entire library',lambda *_:self.launch_action('uninstall',True),'bulk-remove');bulk.append(self.uninstall_all)
        self.install_all.set_tooltip_text('One click: prepare, back up and install wherever possible across every library. Incompatible games are skipped.')
        self.uninstall_all.set_tooltip_text('One click: remove recorded OptiScaler installs across every library, with backups. Your games remain installed.')
        controls=Gtk.Box(spacing=10);top.append(controls);controls.append(label('Install profile','dim-label'))
        linked=Gtk.Box();linked.add_css_class('linked');controls.append(linked)
        self.mfg=Gtk.ToggleButton(label='MFG Only');self.nr=Gtk.ToggleButton(label='NR + MFG');self.nr.set_group(self.mfg)
        for toggle,mode in ((self.mfg,'mfg-only'),(self.nr,'nr-mfg')):
            toggle.add_css_class('profile-toggle');toggle.connect('toggled',self.profile_changed,mode);linked.append(toggle)
        (self.nr if self.settings.get('default_profile')=='nr-mfg' else self.mfg).set_active(True);self.profile_note=label('Headless MFG · no NR panel','dim-label');controls.append(self.profile_note)
        filters=Gtk.Box(spacing=8);top.append(filters)
        self.search=Gtk.SearchEntry(placeholder_text='Search your entire library',hexpand=True);self.search.connect('search-changed',lambda *_:self.filter_games());filters.append(self.search)
        filterbox=Gtk.Box();filterbox.add_css_class('linked');filters.append(filterbox);previous=None
        for name,key in [('All','all'),('Installed','installed'),('Available','available')]:
            b=Gtk.ToggleButton(label=name)
            if previous:b.set_group(previous)
            else:previous=b;b.set_active(True)
            b.connect('toggled',self.filter_changed,key);filterbox.append(b)
        filters.append(button('Select all',lambda *_:self.select_all(True)));filters.append(button('Clear',lambda *_:self.select_all(False)))
        scroll=Gtk.ScrolledWindow(vexpand=True,hscrollbar_policy=Gtk.PolicyType.NEVER);outer.append(scroll)
        self.flow=Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE,column_spacing=14,row_spacing=16,min_children_per_line=1,max_children_per_line=8,homogeneous=True,valign=Gtk.Align.START);margins(self.flow,18);scroll.set_child(self.flow)
        footer=Gtk.Box(spacing=8);footer.add_css_class('selection-bar');outer.append(footer)
        self.selected_label=label('0 selected',css='heading');self.selected_label.set_hexpand(True);footer.append(self.selected_label)
        for name,op,css in [('Install selected','install','forge-primary'),('Repair','repair',None),('Uninstall selected','uninstall','bulk-remove')]:
            b=button(name,lambda _,action=op:self.launch_action(action),css);footer.append(b);self.action_buttons.append(b)
        statusbox=Gtk.Box(spacing=10);statusbox.add_css_class('status-strip');outer.append(statusbox)
        self.spinner=Gtk.Spinner();statusbox.append(self.spinner);self.status=label('Ready');self.status.set_hexpand(True);statusbox.append(self.status)
        self.elapsed=label('','dim-label');statusbox.append(self.elapsed);self.progress=Gtk.ProgressBar();outer.append(self.progress)
        GLib.timeout_add(180,self.tick)
        if options.demo:
            games=demo_games()
            for game in games:
                path=ROOT/'dist/demo-media'/((game['appid'] or 'forza')+'.json')
                if path.exists():game.update(__import__('json').loads(path.read_text()))
            self.show_games(games,False)
            for key in list(self.cards)[:3]:self.cards[key]['check'].set_active(True)
        else:self.scan()
        if options.smoke_test:GLib.timeout_add(800,self.smoke_library)

    def toast(self,text):self.overlay.add_toast(Adw.Toast.new(str(text)))
    def profile_changed(self,toggle,mode):
        if toggle.get_active():
            self.mode=mode
            if hasattr(self,'profile_note'):self.profile_note.set_text('NR starts enabled · NR panel visible' if mode=='nr-mfg' else 'Headless MFG · no NR panel')
    def filter_changed(self,toggle,key):
        if toggle.get_active():self.filter=key;self.filter_games()
    def close_request(self,*_):
        if self.busy and self.task_kind!='art':self.toast('Please wait for the current file operation to finish.');return True
        if self.busy:self.cancel_art.set()
        return False
    def tick(self):
        if self.busy:self.progress.pulse();self.elapsed.set_text(f'{int(time.monotonic()-self.started)}s')
        return True
    def controls(self):
        enabled=not self.busy or self.task_kind=='art'
        compatible=bool(self.hardware_info and self.hardware_info['ready'])
        self.install_all.set_sensitive(enabled and bool(self.games) and compatible);self.uninstall_all.set_sensitive(enabled and bool(self.games))
        for i,b in enumerate(self.action_buttons):b.set_sensitive(enabled and (compatible or i==2) and any(v['check'].get_active() for v in self.cards.values()))
        for b in (self.refresh,self.add,self.mfg,self.nr):b.set_sensitive(enabled)
    def event(self,event):
        if event['kind']=='progress':self.status.set_text(event['label'])
        elif event['kind']=='art':
            card=self.cards.get(event['game'])
            if card:card['data'].update(event['data']);self.paint_card(card)
        else:self.log.append(event['text']);self.log=self.log[-400:]
        if self.dialog and hasattr(self,'job_label') and self.job_label:self.job_label.set_text(self.status.get_text())
        return False
    def start(self,title,action,done,kind='work'):
        if self.busy:
            if self.task_kind=='art':self.pending=(title,action,done,kind);self.cancel_art.set();self.status.set_text('Finishing current artwork request…')
            return
        self.busy=True;self.task_kind=kind;self.started=time.monotonic();self.spinner.start();self.status.set_text(title);self.progress.set_fraction(0);self.controls()
        def worker():
            try:
                with ui.report_to(lambda e:GLib.idle_add(self.event,e)):result=action()
            except Exception as ex:GLib.idle_add(self.finished,None,done,(str(ex),traceback.format_exc()))
            else:GLib.idle_add(self.finished,result,done,None)
        threading.Thread(target=worker,daemon=False).start()
    def finished(self,result,done,error):
        self.busy=False;self.task_kind='';self.spinner.stop();self.progress.set_fraction(0 if error else 1);self.controls()
        if error:
            self.log.append(error[1]);self.status.set_text('Stopped · details available in Activity');self.error(error[0])
        else:self.status.set_text('Ready');done(result)
        if self.pending:
            task=self.pending;self.pending=None;self.start(*task)
        return False
    def open_panel(self,title,width=730,height=620):
        if self.dialog:self.dialog.force_close()
        dialog=Adw.Dialog(title=title,content_width=width,content_height=height);self.dialog=dialog;self.job_label=None
        box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL);dialog.set_child(box)
        header=Adw.HeaderBar();header.set_title_widget(Adw.WindowTitle(title=title));box.append(header)
        scroll=Gtk.ScrolledWindow(vexpand=True,hscrollbar_policy=Gtk.PolicyType.NEVER);box.append(scroll)
        body=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=16);body.add_css_class('panel-body');scroll.set_child(body)
        foot=Gtk.Box(spacing=10,halign=Gtk.Align.END);margins(foot,16);box.append(foot)
        dialog.present(self);return dialog,body,foot
    def error(self,message):
        d,b,f=self.open_panel('Could not finish',height=390);b.append(label(str(message)));f.append(button('Close',lambda *_:d.close()))
    def scan(self):
        if self.options.demo:return
        extra=list(self.settings['extra_folders']);self.start('Checking hardware and scanning libraries',lambda:{'hardware':self.service.hardware(),'games':self.service.scan_all(extra)},self.scanned)
    def scanned(self,result):
        self.hardware_info=result['hardware'];self.hardware_label.set_text(self.hardware_info['gpu']+' · '+('Hardware check passed' if self.hardware_info['ready'] else 'Install unavailable — see Settings'));self.show_games(result['games'])
    def choose_folder(self,*_):
        d=Gtk.FileChooserNative(title='Add a game folder',transient_for=self,action=Gtk.FileChooserAction.SELECT_FOLDER,accept_label='Add game')
        def selected(dialog,response):
            if response==Gtk.ResponseType.ACCEPT:
                path=dialog.get_file().get_path()
                if path and path not in self.settings['extra_folders']:
                    self.settings['extra_folders'].append(path)
                    self.start('Saving game folder',lambda:library_media.save_settings(self.service.config,self.settings),lambda _:self.scan())
            dialog.destroy()
        d.connect('response',selected);d.show()
    def show_games(self,games,art=True):
        selected={k for k,v in self.cards.items() if v['check'].get_active()}
        clear(self.flow);self.games=games;self.cards={}
        view=self.settings.get('library_view','posters');self.flow.set_max_children_per_line(1 if view=='list' else 8);self.flow.set_homogeneous(view!='list')
        for game in games:
            self.make_card(game)
            if game['game'] in selected:self.cards[game['game']]['check'].set_active(True)
        count=sum(g.get('installed',False) for g in games);libs=len(set(g.get('library','') for g in games))
        self.stats.set_text(f'{len(games)} games · {libs} locations · {count} OptiScaler installs detected')
        self.filter_games();self.status.set_text('Your entire library is ready')
        if art and self.settings['online_art'] and games:self.fetch_media()
    def make_card(self,game):
        view=self.settings.get('library_view','posters');scale=self.settings.get('art_scale',100)/100
        width,height=(int(158*scale),int(237*scale)) if view=='posters' else (int(290*scale),int(136*scale)) if view=='capsules' else (54,81)
        card=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL if view=='list' else Gtk.Orientation.VERTICAL);card.add_css_class('game-card');card.set_size_request(width+4,-1)
        overlay=Gtk.Overlay();card.append(overlay)
        pic=Gtk.Picture(content_fit=Gtk.ContentFit.COVER,can_shrink=True);pic.set_size_request(width,height);pic.add_css_class('poster')
        click=Gtk.Button(child=pic);click.add_css_class('poster-button');click.connect('clicked',lambda *_:self.details(game));overlay.set_child(click)
        fallback=label(game['name'],'poster-fallback');fallback.set_halign(Gtk.Align.CENTER);fallback.set_valign(Gtk.Align.CENTER);fallback.set_max_width_chars(13);overlay.add_overlay(fallback)
        check=Gtk.CheckButton(halign=Gtk.Align.END,valign=Gtk.Align.START);margins(check,10);check.set_tooltip_text('Select '+game['name']);check.connect('toggled',lambda *_:self.selection_changed())
        if view=='list':card.prepend(check);fallback.set_visible(False)
        else:overlay.add_overlay(check)
        badge=label('Unavailable' if game.get('blocked') else game.get('profile','Ready') if game.get('installed') else 'Ready','cover-badge');badge.set_halign(Gtk.Align.START);badge.set_valign(Gtk.Align.END);margins(badge,8)
        if game.get('blocked'):badge.add_css_class('unavailable')
        if view!='list':overlay.add_overlay(badge)
        text=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=5,hexpand=view=='list',valign=Gtk.Align.CENTER);text.add_css_class('card-info');card.append(text)
        title=label(game['name'],'card-title');title.set_lines(2);title.set_ellipsize(Pango.EllipsizeMode.END);title.set_max_width_chars(70 if view=='list' else 24 if view=='capsules' else 18);text.append(title)
        meta=label(game.get('source',''),'card-meta');meta.set_lines(1);meta.set_ellipsize(Pango.EllipsizeMode.END);meta.set_max_width_chars(80 if view=='list' else 28 if view=='capsules' else 22);text.append(meta)
        self.flow.insert(card,-1);wrapper=card.get_parent()
        entry={'widget':card,'wrapper':wrapper,'check':check,'picture':pic,'fallback':fallback,'meta':meta,'data':game,'size':(width,height)};self.cards[game['game']]=entry;self.paint_card(entry)
    def paint_card(self,entry):
        game=entry['data'];path=(game.get('capsule') or game.get('poster')) if self.settings.get('library_view')=='capsules' else game.get('poster')
        if path:
            try:entry['picture'].set_paintable(Gdk.Texture.new_for_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_scale(path,*entry['size'],True)));entry['fallback'].set_visible(False)
            except Exception:entry['fallback'].set_visible(True)
        entry['meta'].set_text(game.get('genres') or game.get('source',''))
        entry['widget'].set_tooltip_text(game['name']+'\n'+(game.get('art_credit') or 'Artwork pending'))
    def filter_games(self):
        if not hasattr(self,'search'):return
        text=self.search.get_text().casefold()
        for e in self.cards.values():
            g=e['data'];visible=text in g['name'].casefold() and (self.filter=='all' or self.filter=='installed' and g.get('installed') or self.filter=='available' and not g.get('blocked'))
            e['wrapper'].set_visible(bool(visible))
        self.selection_changed()
    def select_all(self,active):
        # Select ALL always means the unified library, even when search/filter is active.
        for e in self.cards.values():e['check'].set_active(active)
    def selection_changed(self):
        count=0
        for e in self.cards.values():
            if e['check'].get_active():count+=1;e['widget'].add_css_class('selected')
            else:e['widget'].remove_css_class('selected')
        if hasattr(self,'selected_label'):self.selected_label.set_text(f'{count} selected'+(' · across the whole library' if count else ''))
        if hasattr(self,'install_all'):self.controls()
    def fetch_media(self,refresh=False):
        self.cancel_art.clear();games=list(self.games);settings=dict(self.settings)
        def load():
            media=library_media.LibraryMedia(self.service.config,settings)
            for index,game in enumerate(games):
                if self.cancel_art.is_set():break
                try:data=ui.work(f'Artwork {index+1}/{len(games)} · '+game['name'],media.enrich,game,refresh)
                except Exception:continue
                GLib.idle_add(self.event,{'kind':'art','game':game['game'],'data':data})
        self.start('Loading SteamGridDB posters and metadata',load,lambda _:None,'art')
    def details(self,game):
        d,b,f=self.open_panel(game['name'])
        b.append(label(game.get('description') or 'Game details from your library.'))
        group=Adw.PreferencesGroup(title='Game information');b.append(group)
        values=[('Installed profile',game.get('profile','Not installed')),('Compatibility',game.get('blocked') or 'Native DLSS-G detected; install checks still apply'),('Developer',game.get('developers')),('Genre',game.get('genres')),('Released',game.get('release')),('Library',game.get('library')),('Folder',game['game'])]
        if game.get('size_bytes'):values.append(('Installed size',f"{game['size_bytes']/1024**3:.1f} GiB"))
        if game.get('updated'):values.append(('Updated',datetime.datetime.fromtimestamp(game['updated'],datetime.timezone.utc).strftime('%Y-%m-%d')))
        for name,value in values:
            if value:group.add(row(name,value))
        if game.get('art_credit'):b.append(label(game['art_credit'],'dim-label'))
        if game.get('art_link'):b.append(Gtk.LinkButton(uri=game['art_link'],label='View artwork source'))
        if game.get('media_note'):b.append(label(game['media_note'],'dim-label'))
        f.append(button('Close',lambda *_:d.close()))
    def launch_action(self,operation,entire=False):
        if self.busy and self.task_kind!='art':return
        rows=list(self.games) if entire else [e['data'] for e in self.cards.values() if e['check'].get_active()]
        if not rows:self.toast('Select games first.');return
        title={'install':'Install','repair':'Repair','uninstall':'Uninstall'}[operation]+(' entire library' if entire else ' selected games')
        d,b,f=self.open_panel(title);d.set_can_close(False)
        orb=Gtk.Box(halign=Gtk.Align.CENTER);orb.add_css_class('progress-orb');orb.append(Gtk.Image.new_from_icon_name('applications-games-symbolic'));b.append(orb)
        self.job_label=label(f'Preparing {len(rows)} games','progress-title');b.append(self.job_label)
        b.append(label('Your games and saves stay installed. Only identified OptiScaler components are removed.' if operation=='uninstall' else f"Profile: {'NR + MFG' if self.mode=='nr-mfg' else 'MFG Only'}. Backups are created before file changes."))
        spin=Gtk.Spinner(spinning=True,halign=Gtk.Align.CENTER,width_request=34,height_request=34);b.append(spin)
        pulse=Gtk.ProgressBar();b.append(pulse)
        def animate():
            if self.dialog!=d or not self.busy:return False
            pulse.pulse();return True
        GLib.timeout_add(160,animate)
        if entire:b.append(label('One-click action · installs where possible; unavailable games are reported and skipped.' if operation!='uninstall' else 'One-click action · removes OptiScaler where an install record is available.','dim-label'))
        if self.options.demo:
            preview={'kind':'batch','operation':operation,'title':title,'plans':[],'rows':[{'name':r['name'],'detail':'2 file changes'} for r in rows[:4]],'blocked':[{'name':'Example protected game','reason':'Another graphics tool is installed.'}]}
            self.action_ready(preview,d,b,f,False);return
        mode=self.mode;adopt=self.settings['recognize_previous']
        self.start('Preparing '+title.lower(),lambda:self.service.prepare(rows,mode,operation,adopt),lambda review:self.action_ready(review,d,b,f,entire))
    def action_ready(self,review,d,b,f,automatic=False):
        self.review=review;clear(b);clear(f);self.job_label=None;d.set_can_close(True)
        g=Adw.PreferencesGroup(title=f"Ready · {len(review['rows'])}");b.append(g)
        for item in review['rows']:g.add(row(item['name'],item['detail']))
        if review['blocked']:
            skipped=Adw.PreferencesGroup(title=f"Skipped · {len(review['blocked'])}");b.append(skipped)
            for item in review['blocked']:skipped.add(row(item['name'],item['reason']))
        if not review['rows']:b.append(label('No file changes can be applied.'));f.append(button('Close',lambda *_:d.close()));return
        apply=button('Uninstall OptiScaler' if review.get('operation')=='uninstall' else 'Apply to ready games',lambda *_:self.execute(review,d,b,f),'forge-primary');apply.set_sensitive(not self.options.demo);f.append(apply)
        if self.options.demo:b.append(label('Preview mode · all file changes are disabled.','dim-label'))
        elif automatic:self.execute(review,d,b,f)
    def execute(self,review,d,b,f):
        if self.options.demo:return
        clear(f);d.set_can_close(False);self.job_label=label('Applying changes…','progress-title');b.prepend(self.job_label)
        indicator=Gtk.Spinner(spinning=True,width_request=32,height_request=32,halign=Gtk.Align.CENTER);b.prepend(indicator)
        self.start('Applying changes',lambda:self.service.execute(review),lambda path:self.completed(path,d,b,f))
    def completed(self,path,d,b,f):
        self.job_label=None;d.set_can_close(True);clear(b);clear(f)
        b.append(label('Done.','hero-title'));b.append(label('Your changes are complete. Backups are available under Undo previous changes in Settings.'))
        record=label(str(path),'dim-label');record.set_selectable(True);b.append(record)
        f.append(button('Back to library',lambda *_:(d.close(),self.scan()),'forge-primary'))
    def show_activity(self,*_):
        d,b,f=self.open_panel('Activity');text=Gtk.TextView(editable=False,monospace=True,wrap_mode=Gtk.WrapMode.WORD_CHAR);text.get_buffer().set_text('\n'.join(self.log) or 'No activity yet.');b.append(text);f.append(button('Close',lambda *_:d.close()))
    def show_settings(self,*_):
        d,b,f=self.open_panel('Settings')
        appearance=Adw.PreferencesGroup(title='Library appearance');b.append(appearance)
        view_group=Gtk.Box(spacing=0);view_group.add_css_class('linked');view_choice={'value':self.settings.get('library_view','posters')};first=None
        for title,key in [('Posters','posters'),('Wide capsules','capsules'),('List','list')]:
            toggle=Gtk.ToggleButton(label=title)
            if first:toggle.set_group(first)
            else:first=toggle
            toggle.set_active(view_choice['value']==key)
            toggle.connect('toggled',lambda widget,value=key:view_choice.update(value=value) if widget.get_active() else None);view_group.append(toggle)
        appearance.add(row('Library layout','Posters show more games at once.'))
        b.append(view_group)
        scale=Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL,70,150,10);scale.set_value(self.settings.get('art_scale',100));scale.set_digits(0);scale.set_draw_value(True)
        b.append(label('Artwork size (%)','heading'));b.append(scale)
        defaults=Adw.PreferencesGroup(title='Default install profile');b.append(defaults)
        default_nr=Adw.SwitchRow(title='Start with NR + MFG',subtitle='Off uses MFG Only. You can change it in the library.',active=self.settings.get('default_profile')=='nr-mfg');defaults.add(default_nr)
        dark=Adw.SwitchRow(title='Prefer dark appearance',active=self.settings['dark']);appearance.add(dark)
        art=Adw.SwitchRow(title='SteamGridDB posters',subtitle='Automatic, keyless artwork with Steam fallback and offline caching.',active=self.settings['online_art']);appearance.add(art)
        metadata=Adw.SwitchRow(title='Game metadata',subtitle='Fetch descriptions, developers, genres and release dates from Steam.',active=self.settings['steam_metadata']);appearance.add(metadata)
        install=Adw.PreferencesGroup(title='Installation');b.append(install)
        adopt=Adw.SwitchRow(title='Recognize previous installs',subtitle='Allow updating an identifiable OptiScaler install from another installer.',active=self.settings['recognize_previous']);install.add(adopt)
        network=Adw.ExpanderRow(title='Advanced artwork settings',subtitle='Cache lifetime and network timeout')
        cache=Gtk.SpinButton.new_with_range(1,30,1);cache.set_value(self.settings.get('cache_days',7));cache.set_valign(Gtk.Align.CENTER)
        cache_row=row('Refresh cached metadata after (days)');cache_row.add_suffix(cache);network.add_row(cache_row)
        timeout=Gtk.SpinButton.new_with_range(5,30,1);timeout.set_value(self.settings.get('network_timeout',10));timeout.set_valign(Gtk.Align.CENTER)
        timeout_row=row('Request timeout (seconds)');timeout_row.add_suffix(timeout);network.add_row(timeout_row)
        advanced=Adw.PreferencesGroup(title='Advanced');advanced.add(network);b.append(advanced)
        host=self.hardware_info or {'reason':'Hardware check not finished'}
        system=Adw.PreferencesGroup(title='System compatibility');b.append(system)
        for title,key in [('Graphics card','gpu'),('Driver','driver'),('Video memory','vram'),('Processor','cpu'),('System','architecture')]:
            if host.get(key):system.add(row(title,host[key]))
        system.add(row('Hardware check',host.get('reason','Not checked')))
        future=Adw.PreferencesGroup(title='OptiScaler source · coming later',description='UI preview only. RTXForge currently uses its verified bundled source.');b.append(future)
        future.add(row('Current source',self.service.config['repo']))
        repo=Adw.EntryRow(title='Custom OptiScaler repository');repo.set_text('https://github.com/owner/repository');repo.set_sensitive(False);future.add(repo)
        detect=button('Understand repository · coming later',lambda *_:None);detect.set_sensitive(False);b.append(detect)
        maintenance=Adw.PreferencesGroup(title='Undo and removal tools');b.append(maintenance)
        undo=row('Undo previous changes','Restore a recorded install, uninstall or cleanup.');undo.add_suffix(button('Browse',lambda *_:self.show_undo()));maintenance.add(undo)
        old=row('Remove old NR files','Global DLSS5 cleanup with recovery copies.');old.add_suffix(button('Review',lambda *_:self.show_cleanup()));maintenance.add(old)
        def save(*_):
            self.settings.update({'library_view':view_choice['value'],'art_scale':int(scale.get_value()),'cache_days':cache.get_value_as_int(),'network_timeout':timeout.get_value_as_int(),'default_profile':'nr-mfg' if default_nr.get_active() else 'mfg-only','dark':dark.get_active(),'online_art':art.get_active(),'steam_metadata':metadata.get_active(),'recognize_previous':adopt.get_active()})
            Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.PREFER_DARK if self.settings['dark'] else Adw.ColorScheme.DEFAULT)
            if self.options.demo:d.close();self.show_games(self.games,False);return
            self.start('Saving settings',lambda:library_media.save_settings(self.service.config,self.settings),lambda _:(d.close(),self.show_games(self.games,False),self.fetch_media(True) if self.settings['online_art'] else None))
        f.append(button('Save settings',save,'forge-primary'))
    def show_undo(self):
        if self.options.demo:
            d,b,f=self.open_panel('Undo previous changes');b.append(label('Your install and uninstall backups will appear here.'));return
        self.start('Finding previous changes',self.service.recoveries,self.undo_loaded)
    def undo_loaded(self,records):
        d,b,f=self.open_panel('Undo previous changes');g=Adw.PreferencesGroup(title='Recorded changes');b.append(g)
        for record in records:
            item=row(record['name'],record['detail']);item.add_suffix(button('Review',lambda _,r=record:self.start('Checking restore',lambda:self.service.review_recovery(r),lambda review:self.action_ready(review,d,b,f))));g.add(item)
        if not records:b.append(label('No recorded changes yet.'))
    def show_cleanup(self):
        if self.options.demo:return
        d,b,f=self.open_panel('Remove old NR files');b.append(label('Checking global cleanup candidates…'))
        self.start('Scanning old NR files',self.service.review_cleanup,lambda review:self.action_ready(review,d,b,f))
    def capture(self,name):
        paint=Gtk.WidgetPaintable.new(self);snapshot=Gtk.Snapshot();paint.snapshot(snapshot,self.get_width(),self.get_height());node=snapshot.to_node();rect=Graphene.Rect();rect.init(0,0,self.get_width(),self.get_height());texture=self.get_renderer().render_texture(node,rect);texture.save_to_png(str(ROOT/'dist'/name))
    def smoke_library(self):
        try:
            self.capture('gnome-library.png');self.search.set_text('Cyberpunk');self.select_all(True);assert all(e['check'].get_active() for e in self.cards.values())
            self.nr.set_active(True);assert self.mode=='nr-mfg';self.launch_action('uninstall',True);GLib.timeout_add(700,self.smoke_action)
        except Exception:traceback.print_exc();self.get_application().exit_code=1;self.get_application().quit()
        return False
    def smoke_action(self):
        try:self.capture('gnome-review.png');self.show_settings();GLib.timeout_add(700,self.smoke_settings)
        except Exception:traceback.print_exc();self.get_application().exit_code=1;self.get_application().quit()
        return False
    def smoke_settings(self):
        try:self.capture('gnome-settings.png');print('PASS: unified cards, Select all across search, profile toggles, floating uninstall and settings; demo writes disabled',flush=True)
        except Exception:traceback.print_exc();self.get_application().exit_code=1
        self.get_application().quit();return False

class Application(Adw.Application):
    def __init__(self,options):super().__init__(application_id='io.github.lrnolivia.RTXForge',flags=Gio.ApplicationFlags.NON_UNIQUE);self.options=options;self.exit_code=0
    def do_activate(self):
        Gtk.IconTheme.get_for_display(Gdk.Display.get_default()).add_search_path(str(ROOT/'gui/icons'));Gtk.Window.set_default_icon_name('io.github.lrnolivia.RTXForge')
        provider=Gtk.CssProvider();provider.load_from_data(CSS);Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(),provider,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.window=Window(self,self.options);self.window.present()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--provider',type=Path);parser.add_argument('--demo',action='store_true');parser.add_argument('--smoke-test',action='store_true');options=parser.parse_args()
    if options.smoke_test:options.demo=True
    app=Application(options);result=app.run([sys.argv[0]]);return app.exit_code or result
if __name__=='__main__':sys.exit(main())
