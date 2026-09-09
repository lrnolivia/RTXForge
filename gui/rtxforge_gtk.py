#!/usr/bin/env python3
"""RTXForge's GNOME desktop. GTK widgets live only on the main thread."""
from pathlib import Path
import sys,threading,time,traceback,argparse
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import gi
gi.require_version('Gtk','4.0');gi.require_version('Adw','1')
from gi.repository import Gtk,Adw,GLib,Gio,Gdk,Graphene
import ui
from desktop_service import DesktopService

CSS=b'''
.hero { font-size: 30px; font-weight: 800; letter-spacing: -0.6px; }
.eyebrow { color: #76b900; font-weight: 800; font-size: 11px; letter-spacing: 1.6px; }
.forge-icon { color: #76b900; }
.forge-primary { background: #76b900; color: #172400; font-weight: 800; padding: 10px 24px; }
.status-strip { padding: 12px 18px; border-radius: 12px; background: alpha(@accent_bg_color,0.08); }
.page { padding: 22px; }
'''

def label(text,css=None):
    w=Gtk.Label(label=text,xalign=0,wrap=True)
    if css:w.add_css_class(css)
    return w

def button(text,fn,css=None):
    w=Gtk.Button(label=text);w.connect('clicked',fn)
    if css:w.add_css_class(css)
    return w

def group(title):return Adw.PreferencesGroup(title=title)
def clear(box):
    while box.get_first_child():box.remove(box.get_first_child())

class Window(Adw.ApplicationWindow):
    def __init__(self,application,options):
        super().__init__(application=application,title='RTXForge',default_width=1000,default_height=820)
        self.options=options;self.service=DesktopService(options.provider);self.busy=False;self.writing=False
        self.games=[];self.checks=[];self.extra=[];self.libraries=[];self.review=None;self.records=[];self.log=[]
        self.connect('close-request',self.close_request)
        self.overlay=Adw.ToastOverlay();self.set_content(self.overlay)
        outer=Gtk.Box(orientation=Gtk.Orientation.VERTICAL);self.overlay.set_child(outer)
        header=Adw.HeaderBar();header.set_title_widget(Adw.WindowTitle(title='RTXForge',subtitle='GeForce tools · Built for Linux'))
        self.back=button('Back',self.go_back);header.pack_start(self.back);self.back.set_visible(False)
        self.recovery_button=button('Recovery',self.show_recovery);header.pack_end(self.recovery_button)
        self.cleanup_button=button('Cleanup',self.show_cleanup);header.pack_end(self.cleanup_button)
        outer.append(header)
        self.stack=Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE,vexpand=True);outer.append(self.stack)
        self.library_page=self.make_page('library');self.review_page=self.make_page('review');self.result_page=self.make_page('result');self.recovery_page=self.make_page('recovery')
        self.library_page.append(label('RTXFORGE / LIBRARY','eyebrow'))
        self.library_page.append(label('Your games, upgraded.','hero'))
        self.library_page.append(label('Choose your games and graphics stack. Review once, then apply.','dim-label'))
        tools=Gtk.Box(spacing=8);self.library_page.append(tools)
        self.library_select=Gtk.DropDown.new_from_strings(['Finding libraries…']);self.library_select.set_hexpand(True)
        self.library_select.connect('notify::selected',self.library_changed);tools.append(self.library_select)
        self.refresh=button('Refresh',lambda *_:self.scan());tools.append(self.refresh)
        self.add_folder=button('Add game folder',self.choose_folder);tools.append(self.add_folder)
        config=group('Graphics stack');self.library_page.append(config)
        self.mode=Adw.ComboRow(title='Profile',subtitle='MFG Only hides the NR panel. NR + MFG starts with NR enabled.')
        self.mode.set_model(Gtk.StringList.new(['MFG Only','NR + MFG']));config.add(self.mode)
        self.operation=Adw.ComboRow(title='Action');self.operation.set_model(Gtk.StringList.new(['Install / update','Repair / verify','Remove owned files']));config.add(self.operation)
        self.adopt=Adw.SwitchRow(title='Adopt an existing OptiScaler install',subtitle='Use only when its original ownership record is unavailable.');config.add(self.adopt)
        filters=Gtk.Box(spacing=8);self.library_page.append(filters)
        self.search=Gtk.SearchEntry(placeholder_text='Search games',hexpand=True);self.search.connect('search-changed',lambda *_:self.filter_games());filters.append(self.search)
        self.select_all=button('Select visible',lambda *_:self.select_visible(True));filters.append(self.select_all)
        self.select_none=button('Clear',lambda *_:self.select_visible(False));filters.append(self.select_none)
        self.game_group=group('Games');self.library_page.append(self.game_group)
        self.library_footer=Gtk.Box(spacing=12);self.library_footer.set_margin_start(22);self.library_footer.set_margin_end(22);self.library_footer.set_margin_top(10);self.library_footer.set_margin_bottom(10);outer.append(self.library_footer)
        self.selection_label=label('No games selected','dim-label');self.selection_label.set_hexpand(True);self.library_footer.append(self.selection_label)
        self.review_button=button('Review selected games',self.prepare,'forge-primary');self.review_button.set_halign(Gtk.Align.END);self.library_footer.append(self.review_button)
        self.review_footer=Gtk.Box(spacing=12,halign=Gtk.Align.END);self.review_footer.set_margin_end(22);self.review_footer.set_margin_bottom(10);outer.append(self.review_footer);self.review_footer.set_visible(False)
        self.status_box=Gtk.Box(spacing=10);self.status_box.add_css_class('status-strip')
        self.status_box.set_margin_start(18);self.status_box.set_margin_end(18);self.status_box.set_margin_bottom(12);outer.append(self.status_box)
        self.spinner=Gtk.Spinner();self.status_box.append(self.spinner)
        self.status=label('Ready');self.status.set_hexpand(True);self.status_box.append(self.status)
        self.elapsed=label('','dim-label');self.status_box.append(self.elapsed)
        self.progress=Gtk.ProgressBar();outer.append(self.progress)
        expander=Gtk.Expander(label='Activity details');expander.set_margin_start(18);expander.set_margin_end(18);expander.set_margin_bottom(12);outer.append(expander)
        scroll=Gtk.ScrolledWindow(min_content_height=90,max_content_height=140,propagate_natural_height=True)
        self.log_view=Gtk.TextView(editable=False,cursor_visible=False,monospace=True,wrap_mode=Gtk.WrapMode.WORD_CHAR);scroll.set_child(self.log_view);expander.set_child(scroll)
        self.stack.set_visible_child_name('library');self.update_selection()
        GLib.timeout_add(180,self.tick)
        if options.demo:self.load_demo()
        else:self.start('Finding game libraries',self.service.libraries,self.libraries_loaded)
        if options.smoke_test:GLib.timeout_add(700,self.smoke_library)

    def make_page(self,name):
        page=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=16);page.add_css_class('page')
        clamp=Adw.Clamp(maximum_size=1000,tightening_threshold=700);clamp.set_child(page)
        scroll=Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER);scroll.set_child(clamp);self.stack.add_named(scroll,name)
        return page

    def toast(self,text):self.overlay.add_toast(Adw.Toast.new(str(text)))
    def close_request(self,*_):
        if self.busy:self.toast('An operation is running. Please wait for it to finish.');return True
        return False
    def set_controls(self):
        for w in (self.library_select,self.refresh,self.add_folder,self.mode,self.operation,self.adopt,self.search,self.select_all,self.select_none,self.recovery_button,self.cleanup_button,self.back):w.set_sensitive(not self.busy)
        for _,check,row in self.checks:check.set_sensitive(not self.busy and not row['blocked'])
        self.review_button.set_sensitive(not self.busy and any(c.get_active() for _,c,_ in self.checks))
        if hasattr(self,'apply_button'):self.apply_button.set_sensitive(not self.busy and bool(self.review and self.review['rows']) and not self.options.demo)
    def tick(self):
        if self.busy:self.progress.pulse();self.elapsed.set_text(f'{int(time.monotonic()-self.started)}s')
        return True
    def event(self,event):
        if event['kind']=='progress':self.status.set_text(event['label'])
        else:
            self.log.append(event['text']);self.log=self.log[-400:];self.log_view.get_buffer().set_text('\n'.join(self.log))
        return False
    def start(self,title,action,done,writing=False):
        if self.busy:return
        self.busy=True;self.writing=writing;self.started=time.monotonic();self.spinner.start();self.status.set_text(title);self.progress.set_fraction(0);self.set_controls()
        def worker():
            try:
                with ui.report_to(lambda event:GLib.idle_add(self.event,event)):result=action()
            except Exception as ex:GLib.idle_add(self.finished,None,done,(str(ex),traceback.format_exc()))
            else:GLib.idle_add(self.finished,result,done,None)
        threading.Thread(target=worker,daemon=False).start()
    def finished(self,result,done,error):
        self.busy=False;self.writing=False;self.spinner.stop();self.progress.set_fraction(1 if not error else 0);self.set_controls()
        if error:
            self.status.set_text('Stopped — see details below');self.event({'kind':'log','text':error[1]})
            self.show_error(error[0])
        else:self.status.set_text('Ready');done(result)
        return False
    def show_error(self,message):
        dialog=Adw.MessageDialog(transient_for=self,heading='RTXForge stopped',body=str(message))
        dialog.add_response('close','Close');dialog.set_close_response('close');dialog.present()
    def libraries_loaded(self,paths):
        self.libraries=paths
        self.library_select.set_model(Gtk.StringList.new([str(p) for p in paths] or ['No Steam library found — add a game folder']))
        if not paths:self.status.set_text('Add a game folder to get started')
        elif not self.busy:self.scan()
    def library_changed(self,*_):
        if self.libraries and not self.busy and not self.options.demo:self.scan()
    def scan(self):
        if self.options.demo:return
        index=self.library_select.get_selected();library=self.libraries[index] if index<len(self.libraries) else None
        self.start('Scanning your games',lambda:self.service.scan(library,list(self.extra)),self.show_games)
    def choose_folder(self,*_):
        dialog=Gtk.FileChooserNative(title='Choose a game folder',transient_for=self,action=Gtk.FileChooserAction.SELECT_FOLDER,accept_label='Add game')
        def chosen(d,response):
            if response==Gtk.ResponseType.ACCEPT:
                path=d.get_file().get_path()
                if path and path not in self.extra:self.extra.append(path);self.scan()
            d.destroy()
        dialog.connect('response',chosen);dialog.show()
    def show_games(self,rows):
        for widget,_,_ in self.checks:self.game_group.remove(widget)
        self.games=rows;self.checks=[]
        for row in rows:
            action=Adw.ActionRow(title=row['name'],subtitle=row['blocked'] or row['source']+' · '+row['exe'])
            action.set_title_lines(1);action.set_subtitle_lines(1)
            check=Gtk.CheckButton(valign=Gtk.Align.CENTER);check.set_sensitive(not row['blocked']);action.add_prefix(check);action.set_activatable_widget(check)
            icon=Gtk.Image.new_from_icon_name('dialog-warning-symbolic' if row['blocked'] else 'applications-games-symbolic');action.add_suffix(icon)
            action.set_tooltip_text(row['game']);check.connect('toggled',lambda *_:self.update_selection())
            self.game_group.add(action);self.checks.append((action,check,row))
        self.game_group.set_title(f'Games · {len(rows)}');self.filter_games();self.status.set_text(f'{len(rows)} games found')
    def filter_games(self):
        query=self.search.get_text().casefold()
        for widget,_,row in self.checks:widget.set_visible(query in row['name'].casefold())
        self.update_selection()
    def select_visible(self,active):
        for widget,check,row in self.checks:
            if widget.get_visible() and not row['blocked']:check.set_active(active)
    def update_selection(self):
        count=sum(c.get_active() for _,c,_ in self.checks)
        self.selection_label.set_text(f'{count} selected · unavailable games stay protected')
        self.review_button.set_label(f'Review {count} games' if count else 'Select games to continue');self.set_controls()
    def prepare(self,*_):
        rows=[r for _,c,r in self.checks if c.get_active()];mode=['mfg-only','nr-mfg'][self.mode.get_selected()];operation=['install','repair','uninstall'][self.operation.get_selected()];adopt=self.adopt.get_active()
        if self.options.demo:self.show_review(self.demo_review());return
        self.start('Preparing your batch',lambda:self.service.prepare(rows,mode,operation,adopt),self.show_review)
    def go_back(self,*_):self.review=None;self.stack.set_visible_child_name('library');self.library_footer.set_visible(True);self.review_footer.set_visible(False);self.back.set_visible(False);self.update_selection()
    def show_review(self,review):
        self.review=review;clear(self.review_page);self.review_page.append(label('RTXFORGE / REVIEW','eyebrow'));self.review_page.append(label(review['title'],'hero'))
        text='Nothing changes until you click Apply. Backups and drift checks remain enabled.'
        if review['kind']=='batch':text+=' Keep existing launch options; merge any listed DLL override into WINEDLLOVERRIDES.'
        if review['kind']=='cleanup':text='Removes NR files and old DLSS5 backup folders across the Games mount. Every candidate is backed up first.'
        self.review_page.append(label(text,'dim-label'))
        ready=group(f"Ready · {len(review['rows'])}");self.review_page.append(ready)
        for r in review['rows']:ready.add(Adw.ActionRow(title=r['name'],subtitle=r['detail']))
        if review['blocked']:
            excluded=group(f"Excluded · {len(review['blocked'])}");self.review_page.append(excluded)
            for r in review['blocked']:excluded.add(Adw.ActionRow(title=r['name'],subtitle=r['reason']))
        if not review['rows']:self.review_page.append(label('No changes are ready to apply. Review the exclusions or go back.'))
        clear(self.review_footer);self.apply_button=button('Apply reviewed changes',self.apply,'forge-primary');self.review_footer.append(self.apply_button)
        self.library_footer.set_visible(False);self.review_footer.set_visible(True)
        if self.options.demo:self.review_page.append(label('Preview mode — installation is disabled.','dim-label'))
        self.stack.set_visible_child_name('review');self.back.set_visible(True);self.set_controls()
    def apply(self,*_):
        if self.options.demo or not self.review or not self.review['rows']:return
        review=self.review;self.start('Applying reviewed changes',lambda:self.service.execute(review),self.show_result,writing=True)
    def show_result(self,path):
        self.review=None;self.library_footer.set_visible(False);self.review_footer.set_visible(False);clear(self.result_page);self.result_page.append(label('RTXFORGE / COMPLETE','eyebrow'));self.result_page.append(label('Your changes are ready.','hero'))
        self.result_page.append(label('The file operation completed. Graphics behavior still needs to be checked in game.'))
        self.result_page.append(label('Recovery record','heading'));record=label(str(path));record.set_selectable(True);self.result_page.append(record)
        self.result_page.append(button('Back to games',self.go_back,'forge-primary'));self.stack.set_visible_child_name('result');self.back.set_visible(True)
        self.status.set_text('Completed · recovery record saved')
    def show_recovery(self,*_):self.start('Finding recovery records',self.service.recoveries,self.recoveries_loaded)
    def recoveries_loaded(self,records):
        self.library_footer.set_visible(False);self.review_footer.set_visible(False);clear(self.recovery_page);self.recovery_page.append(label('Recovery','hero'));self.recovery_page.append(label('Choose a recorded batch or cleanup to review its restoration.','dim-label'))
        g=group('Available records');self.recovery_page.append(g)
        for record in records:
            row=Adw.ActionRow(title=record['name'],subtitle=record['detail']);row.add_suffix(button('Review',lambda _,r=record:self.start('Checking recovery',lambda:self.service.review_recovery(r),self.show_review)));g.add(row)
        if not records:self.recovery_page.append(label('No recovery records are available.'))
        self.stack.set_visible_child_name('recovery');self.back.set_visible(True)
    def show_cleanup(self,*_):
        if self.options.demo:return
        self.start('Scanning global DLSS5 cleanup candidates',self.service.review_cleanup,self.show_review)
    def load_demo(self):
        self.library_select.set_model(Gtk.StringList.new(['Steam Library · Games drive']))
        names=['Avatar: Frontiers of Pandora','Cyberpunk 2077','Hogwarts Legacy','PRAGMATA','Star Wars Outlaws','Forza Horizon 6']
        self.show_games([{'name':n,'game':'/preview/'+n,'exe':'Game.exe','source':'Steam','blocked':''} for n in names])
        for _,c,_ in self.checks[:4]:c.set_active(True)
        self.status.set_text('Preview mode · no games accessed')
    def demo_review(self):return {'kind':'batch','title':'Repair / verify','plans':[],'rows':[{'name':r['name'],'detail':'2 file changes · MFG Only'} for _,c,r in self.checks if c.get_active()],'blocked':[{'name':'Forza Horizon 6','reason':'Separate winmm.dll loader — this game stays unchanged'}]}
    def capture(self,name):
        paint=Gtk.WidgetPaintable.new(self);snapshot=Gtk.Snapshot();paint.snapshot(snapshot,self.get_width(),self.get_height());node=snapshot.to_node()
        rect=Graphene.Rect();rect.init(0,0,self.get_width(),self.get_height())
        texture=self.get_renderer().render_texture(node,rect);out=ROOT/'dist';out.mkdir(exist_ok=True);texture.save_to_png(str(out/name))
    def smoke_library(self):
        try:
            self.capture('gnome-library.png')
            self.start('Checking preview',lambda:ui.work('Preparing preview',time.sleep,0.2),self.smoke_prepared)
        except Exception:traceback.print_exc();self.get_application().exit_code=1;self.get_application().quit()
        return False
    def smoke_prepared(self,_):
        self.show_review(self.demo_review());GLib.timeout_add(700,self.smoke_review)
    def smoke_review(self):
        try:
            self.capture('gnome-review.png');assert not self.apply_button.get_sensitive();self.go_back();assert self.stack.get_visible_child_name()=='library';print('GNOME smoke passed: library, selection, review, demo write protection, back navigation',flush=True)
        except Exception:traceback.print_exc();self.get_application().exit_code=1
        self.get_application().quit();return False

class Application(Adw.Application):
    def __init__(self,options):super().__init__(application_id='io.github.lrnolivia.RTXForge',flags=Gio.ApplicationFlags.NON_UNIQUE);self.options=options;self.exit_code=0
    def do_activate(self):
        Gtk.IconTheme.get_for_display(Gdk.Display.get_default()).add_search_path(str(ROOT/'gui/icons'))
        Gtk.Window.set_default_icon_name('io.github.lrnolivia.RTXForge')
        provider=Gtk.CssProvider();provider.load_from_data(CSS);Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(),provider,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.window=Window(self,self.options);self.window.present()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--provider',type=Path);parser.add_argument('--demo',action='store_true');parser.add_argument('--smoke-test',action='store_true');options=parser.parse_args()
    if options.smoke_test:options.demo=True
    app=Application(options);result=app.run([sys.argv[0]]);return app.exit_code or result
if __name__=='__main__':sys.exit(main())
