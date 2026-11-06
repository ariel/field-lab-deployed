#!/usr/bin/env python3
"""Read-only CCC discovery. Task creation/configuration remains in CCC's supported UI.

No start/stop/enable/disable, preferences writes, task imports or snapshot commands
are exposed here. Task names and histories are operator-private local output.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import plistlib
import subprocess
import sys

DEFAULT_APP=Path('/Applications/Carbon Copy Cloner.app')
READ_ONLY={'version':['--version'],'tasks':['--uuids'],'status':['--status'],'idle':['--no-running-tasks']}

def inspect(app=DEFAULT_APP,runner=subprocess.run):
    app=Path(app).expanduser().absolute()
    info_path=app/'Contents/Info.plist';cli=app/'Contents/MacOS/ccc'
    if not info_path.is_file() or not cli.is_file():raise ValueError('CCC application/CLI not found at '+str(app))
    with info_path.open('rb') as stream:info=plistlib.load(stream)
    if info.get('CFBundleIdentifier')!='com.bombich.ccc':raise ValueError('Unexpected application bundle identifier')
    result={'app':str(app),'app_version':info.get('CFBundleShortVersionString'),'app_build':info.get('CFBundleVersion'),'changes_made':False,'task_configuration':'Use CCC UI; no supported creation CLI is assumed','checks':{}}
    for key,args in READ_ONLY.items():
        try:
            check=runner([str(cli),*args],capture_output=True,text=True,timeout=15,check=False)
            result['checks'][key]={'exit_code':check.returncode,'stdout':check.stdout.strip(),'stderr':check.stderr.strip()}
        except (OSError,subprocess.TimeoutExpired) as exc:
            result['checks'][key]={'exit_code':None,'error':str(exc)}
    # Non-zero can mean running tasks or an error. Do not turn it into a clean idle state.
    result['idle_confirmed']=result['checks']['idle'].get('exit_code')==0
    result['inventory_complete']=all(result['checks'][key].get('exit_code')==0 for key in ('version','tasks','status'))
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--app',type=Path,default=DEFAULT_APP);args=parser.parse_args()
    try:
        result=inspect(args.app);print(json.dumps(result,indent=2));return 0 if result['inventory_complete'] else 1
    except (OSError,ValueError,plistlib.InvalidFileException) as exc:
        print(json.dumps({'error':str(exc),'changes_made':False}),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
