"""Read back OffShoot settings after supported API configuration; no app mutations."""
import json,plistlib,subprocess
from pathlib import Path

def inspect(root):
    root=Path(root);receipt=json.loads((root/'runtime/setup-receipt.json').read_text())
    info=plistlib.loads(Path('/Applications/OffShoot.app/Contents/Info.plist').read_bytes())
    export=subprocess.run(['/usr/bin/defaults','export',info['CFBundleIdentifier'],'-'],capture_output=True,check=True)
    defaults=plistlib.loads(Path('/Applications/OffShoot.app/Contents/Resources/SFIDefaults.plist').read_bytes())
    actual={**defaults,**plistlib.loads(export.stdout)};mismatches=[]
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
    preset_ok=bool(presets and presets[0].get('folderPattern')==pattern and not presets[0].get('flattenFolders') and not presets[0].get('renamePattern'))
    hooks_ok=all(Path(receipt['hooks'][key]).is_file() for key in ['SFIDefaultsHedgeStartedScript','SFIDefaultsFileCopyCompletedScript'])
    return {'preferences_match':not mismatches,'mismatches':mismatches,'preset_matches':preset_ok,'hook_files_present':hooks_ok,'active_preset_matches':current_preset_ok,'settings_verified':not mismatches and preset_ok and hooks_ok and current_preset_ok,'destination_validation':'The URL API does not expose selected dropzones; confirm the actual destination preview and a disposable verified transfer','ccc_changed':False}
if __name__=='__main__':
    result=inspect(Path(__file__).resolve().parents[1]);print(json.dumps(result,indent=2));raise SystemExit(0 if result['settings_verified'] else 1)
