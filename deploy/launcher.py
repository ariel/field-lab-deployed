"""Stable OffShoot callback dispatcher; serialize against release switches."""
import argparse,fcntl,os,subprocess
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--home',type=Path,required=True);p.add_argument('command',choices=['start','stop','recover','reconcile']);a=p.parse_args()
    home=a.home.expanduser().absolute()
    with (home/'deploy.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_SH)
        root=(home/'current').resolve(strict=True)
        if root.parent!=home/'releases':raise ValueError('Invalid managed release')
        subprocess.run([str(root/'.venv/bin/python'),str(root/'ingest_service.py'),a.command],check=True,cwd=root)
if __name__=='__main__':main()
