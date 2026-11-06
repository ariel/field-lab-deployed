"""Read back OffShoot settings after supported API configuration; no app mutations."""
import json,plistlib,subprocess,sys
from pathlib import Path

def inspect(root):
    root=Path(root);receipt=json.loads((root/'runtime/setup-receipt.json').read_text())
    info=plistlib.loads(Path('/Applications/OffShoot.app/Contents/Info.plist').read_bytes())
    export=subprocess.run(['/usr/bin/defaults','export',info['CFBundleIdentifier'],'-'],capture_output=True,check=True)
    defaults=plistlib.loads(Path('/Applications/OffShoot.app/Contents/Resources/SFIDefaults.plist').read_bytes())
    overrides=plistlib.loads(export.stdout)
    if not isinstance(defaults,dict) or not isinstance(overrides,dict):raise ValueError('Preference export must be a mapping')
    actual={**defaults,**overrides};mismatches=[]
    for key,expected in receipt['hooks'].items():
        value=actual.get(key)
        if key=='SFIDefaultsDestinationDirectoryFormatIncrementer':
            # App may have advanced this counter after setup; it must never regress.
            try:ok=int(value)>=int(expected)
            except (TypeError,ValueError):ok=False
        else:ok=value==expected
        if not ok:mismatches.append({'key':key,'expected':expected,'actual':value})
    preset=Path.home()/'Library/Preferences/Hedge/Presets/Verified Ingest.hedge'
    presets=json.loads(preset.read_text())
    config=json.loads((root/'config.json').read_text())
    pattern=config['ingest_folder'].rstrip('/')+'/{YYYY}{MM}{DD}/{Source Name}-{Counter}'
    current_preset_ok=actual.get('SFIDefaultsCurrentOrganizePreset')=='Verified Ingest'
    item=presets[0] if isinstance(presets,list) and len(presets)==1 and isinstance(presets[0],dict) else {}
    try:counter_ok=int(item.get('counter'))>=int(receipt['counter'])
    except (ValueError,TypeError,KeyError):counter_ok=False
    preset_ok=bool(item.get('folderPattern')==pattern and item.get('flattenFolders') is False and not item.get('renamePattern') and item.get('ignoreEmptyFolders') is False and not item.get('doNotCopyFiles') and not item.get('copyOnlyFiles') and not any(item.get('ignoreBundles',[])) and counter_ok)
    hooks_ok=all(Path(receipt['hooks'][key]).is_file() for key in ['SFIDefaultsHedgeStartedScript','SFIDefaultsFileCopyCompletedScript'])
    return {'preferences_match':not mismatches,'mismatches':mismatches,'preset_matches':preset_ok,'hook_files_present':hooks_ok,'active_preset_matches':current_preset_ok,'settings_verified':not mismatches and preset_ok and hooks_ok and current_preset_ok,'destination_validation':'The URL API does not expose selected dropzones; confirm the actual destination preview and a disposable verified transfer','ccc_changed':False}
if __name__=='__main__':
    try:
        result=inspect(Path(__file__).resolve().parents[1]);print(json.dumps(result,indent=2));raise SystemExit(0 if result['settings_verified'] else 1)
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as error:
        print(json.dumps({'settings_verified':False,'changes_made':False,'error':str(error)}),file=sys.stderr);raise SystemExit(1)
