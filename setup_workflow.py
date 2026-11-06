"""Repeat the documented OffShoot configuration using this drive's runtime."""
import argparse,json,os,platform,plistlib,re,shlex,shutil,subprocess,sys,tempfile,time
from pathlib import Path
from urllib.parse import quote
ROOT=Path(__file__).resolve().parent
from ingest_service import config,verify_volume,start
from ditnotes.atomic import atomic_json

def api(action,**values):
    log=Path.home()/'Library/Logs/Hedge/urlSchemeResponseLog.txt'
    before=log.stat().st_mtime_ns if log.exists() else None
    query='&'.join(quote(k,safe='')+'='+quote(json.dumps(v,separators=(',',':')) if not isinstance(v,str) else v,safe='') for k,v in values.items())
    subprocess.run(['/usr/bin/open','offshoot://'+action+('?' +query if query else '')],check=True)
    deadline=time.monotonic()+12
    while time.monotonic()<deadline:
        if log.exists() and log.stat().st_mtime_ns!=before:
            result=log.read_text().strip()
            if not result:
                time.sleep(.05);continue
            if result=='success':return
            if result=='mainview':raise RuntimeError('Select Disks in OffShoot, close Settings/dialogs, then run Setup again')
            raise RuntimeError('OffShoot rejected '+action+': '+result)
        time.sleep(.05)
    raise RuntimeError('OffShoot did not acknowledge '+action+'; close any open dialogs and run Setup again')

def compile_hooks(home):
    output=home/'shared/runtime/offshoot-hooks';output.mkdir(parents=True,exist_ok=True)
    hooks={}
    for title,command in [('OffShoot Started','start'),('File Copy Completed','recover')]:
        shell=shlex.join([str(home/'run'),command])
        # JSON and AppleScript use the same quoted-string escaping here.
        script=output/f'{title}.applescript'
        with tempfile.TemporaryDirectory(dir=output) as tmp:
            staged=Path(tmp)/script.name
            staged.write_text('-- Managed callback resolves the active release at invocation.\nreturn do shell script '+json.dumps(shell,ensure_ascii=False)+'\n')
            compiled=staged.with_suffix('.scpt')
            subprocess.run(['/usr/bin/osacompile','-o',str(compiled),str(staged)],check=True)
            os.replace(compiled,script.with_suffix('.scpt'));os.replace(staged,script)
        hooks[title]=str(script.with_suffix('.scpt'))
    return hooks


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--home',type=Path,required=True);parser.add_argument('--offshoot-idle',action='store_true');args=parser.parse_args()
    if not args.offshoot_idle:raise RuntimeError('Confirm OffShoot has no active or queued transfers before configuration')
    home=args.home.expanduser().absolute()
    if (home/'current').resolve()!=ROOT:raise RuntimeError('Configure only the active managed release')
    if platform.machine()!='arm64':raise RuntimeError('This bundle requires an Apple Silicon Mac')
    mac_major=int(subprocess.check_output(['/usr/bin/sw_vers','-productVersion'],text=True).split('.')[0])
    if mac_major<27:raise RuntimeError('This bundled FFmpeg/native build currently requires macOS27 or newer')
    c=config();verify_volume(c)
    app=Path('/Applications/OffShoot.app')
    if not app.exists():raise RuntimeError('Install and activate OffShoot Pro first, then run Setup again')
    info=plistlib.loads((app/'Contents/Info.plist').read_bytes())
    version=tuple(int(x) for x in info['CFBundleShortVersionString'].split('.')[:2])
    if version<(26,3):raise RuntimeError('This workflow was validated with OffShoot26.3; update OffShoot Pro before setup')
    check=subprocess.run([sys.executable,str(ROOT/'dit_notes.py'),'prepare-offline','--check'],capture_output=True,text=True)
    readiness=json.loads(check.stdout)
    if check.returncode or not readiness['ready']:raise RuntimeError('Offline assets are incomplete; run prepare-offline before field use')
    project=Path(c['ingest_root']);project.mkdir(parents=True,exist_ok=True)
    counters=[int(m.group(1)) for p in project.glob('*/*') if p.is_dir() and (m:=re.search(r'-(\d+)$',p.name))]
    # Retain counters even when media has moved or earlier rolls live elsewhere.
    domain=info['CFBundleIdentifier']
    exported=subprocess.run(['/usr/bin/defaults','export',domain,'-'],capture_output=True,check=False)
    if exported.returncode!=0:raise RuntimeError('Cannot back up OffShoot preferences. Open OffShoot and retry; no settings have been changed')
    existing=plistlib.loads(exported.stdout)
    target=Path.home()/'Library/Preferences/Hedge/Presets/Verified Ingest.hedge'
    prior=json.loads(target.read_text()) if target.is_file() else []
    saved=[int(str(x)) for x in [existing.get('SFIDefaultsDestinationDirectoryFormatIncrementer','0'),*[v.get('counter','0') for v in prior]] if str(x).isdigit()]
    counter=f'{max([max(counters,default=0)+1,*saved]):03d}'
    backup=ROOT/'runtime/setup-backups'/str(time.time_ns());backup.mkdir(parents=True,exist_ok=True)
    if exported.returncode==0:(backup/'offshoot-preferences.plist').write_bytes(exported.stdout)
    atomic_json(backup/'plan.json',{'volume_uuid':c['volume_uuid'],'ingest_root':c['ingest_root'],'counter':counter,'previous_preferences_exported':exported.returncode==0,'ccc_configured':False})
    old_hooks=home/'shared/runtime/offshoot-hooks'
    if old_hooks.is_dir():shutil.copytree(old_hooks,backup/'offshoot-hooks')
    hooks=compile_hooks(home)
    preset=json.loads((ROOT/'offshoot/Verified Ingest.hedge').read_text());preset[0]['counter']=counter; preset[0]['folderPattern']=c['ingest_folder'].rstrip('/')+'/{YYYY}{MM}{DD}/{Source Name}-{Counter}'
    target=Path.home()/'Library/Preferences/Hedge/Presets/Verified Ingest.hedge'
    if target.exists():
        shutil.copy2(target,backup/target.name)
    atomic_json(target,preset)
    # The vendor supports applying preferences through this API while the app is running.
    prefs={'SFIDefaultsAutoDestinations':False,'SFIDefaultsAutoSources':False,'SFIDefaultsAutoSourcesWildcard':False,'SFIDefaultsHedgeStartedScript':hooks['OffShoot Started'],'SFIDefaultsFileCopyCompletedScript':hooks['File Copy Completed'],'SFIDefaultsUserAcceptsResponsibilityForScripts':True,'TransfersSettingsVerifyKey':'SourceAndDestination','SFIDefaultsAutoVerificationModeSelection':'SourceAndDestination','SFIDefaultsAutoVerificationModeWildcard':False,'SFIDefaultsTransferShouldMoveEnabled':False,'SFIDefaultsAutoEjectDisks':False,'SFIDefaultsTransferSettingsLogging':True,'SFIDefaultsIsrganizePresetActive':True,'SFIDefaultsDestinationDirectoryFormatIncrementer':counter,'SFIDefaultsConnectNotifications':False,'SFIDefaultsExtraLogLocation':''}
    try:
        api('setPreferences',preferences=prefs)
        api('reloadPresets')
        api('setPreferences',preferences={'SFIDefaultsCurrentOrganizePreset':'Verified Ingest'})
        api('reset',type='destinations')
        api('setDestination',path=c['volume_mount'])
    except Exception as error:
        atomic_json(backup/'failure.json',{'error':str(error),'partial_configuration_possible':True})
        raise RuntimeError('OffShoot configuration did not finish; settings may be partially applied. Preserve cards. Backup: '+str(backup)+'. '+str(error)) from error
    # Service start is explicit after the operator reviews settings.
    status={'status':'not_started'}
    atomic_json(ROOT/'runtime/setup-receipt.json',{'configured_at':time.time(),'offshoot_version':info['CFBundleShortVersionString'],'runtime_python':platform.python_version(),'volume_uuid':c['volume_uuid'],'ingest_root':c['ingest_root'],'counter':counter,'hooks':prefs,'ccc_configured':False})
    print('OffShoot ingest and local AI are configured. Run the managed start command to begin reconciliation.\nBrowser: http://127.0.0.1:'+str(c['port'])+'/\nCCC is not configured; keep camera cards until there is a second verified copy.')
if __name__=='__main__':main()
