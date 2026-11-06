#!/usr/bin/env python3
"""OffShoot entry point: re-execute the bundled interpreter explicitly."""
import os,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
args=[str(root/'.venv/bin/python'),str(root/'ingest_service.py'),'start']
if 'start'=='event':
    if len(sys.argv)!=2:raise SystemExit('Expected OffShoot event JSON')
    args.append(sys.argv[1])
os.execv(args[0],args)
