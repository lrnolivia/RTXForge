"""Apply RTXForge's startup-only NR panel policy to the exact audited upstream source."""
import hashlib,pathlib,sys
p=pathlib.Path(sys.argv[1])/'OptiScaler/menu/menu_common.cpp'
s=p.read_text(encoding='utf-8-sig')
old='        DlssNr::RenderMenu(ctx.config, ctx.menuResScale);'
assert s.count(old)==1,'Upstream menu changed: review before applying'
new='''        // RTXForge route policy is fixed at startup, independent of the NR effect toggle.
        static const bool rtxforgeNrPanel = [&]() {
            const auto ini = std::filesystem::path(ctx.config->MainDllPath.value()) / L"OptiScaler.ini";
            const bool enabled = GetPrivateProfileIntW(L"RTXForge", L"NrPanel", 1, ini.c_str()) != 0;
            LOG_INFO("RTXForge.NrPanel.v1: {}", enabled);
            return enabled;
        }();
        if (rtxforgeNrPanel)
            DlssNr::RenderMenu(ctx.config, ctx.menuResScale);'''
p.write_text(s.replace(old,new),encoding='utf-8')
print('Applied startup-only [RTXForge] NrPanel policy; stock configurations default visible.')
