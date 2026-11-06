"""Bundle one official portable Node runtime for the isolated Orama helper."""
from pathlib import Path
import hashlib,json,os,subprocess,tarfile,tempfile,urllib.request
ROOT=Path(__file__).resolve().parents[1]
VERSION='v24.11.0'
ARCHIVE=f'node-{VERSION}-darwin-arm64.tar.gz'
BASE=f'https://nodejs.org/dist/{VERSION}/'
def main():
    checks=urllib.request.urlopen(BASE+'SHASUMS256.txt',timeout=60).read().decode()
    wanted=next(line.split()[0] for line in checks.splitlines() if line.split()[-1]==ARCHIVE)
    with tempfile.TemporaryDirectory(prefix='lab-node-') as temp:
        archive=Path(temp)/ARCHIVE
        with urllib.request.urlopen(BASE+ARCHIVE,timeout=60) as r,archive.open('wb') as f:
            while chunk:=r.read(1024*1024):f.write(chunk)
        found=hashlib.file_digest(archive.open('rb'),'sha256').hexdigest()
        if found!=wanted:raise RuntimeError('Official Node archive checksum mismatch')
        (ROOT/'bin').mkdir(exist_ok=True)
        with tarfile.open(archive,'r:gz') as tar:
            for member,target in [(f'node-{VERSION}-darwin-arm64/bin/node',ROOT/'bin/node'),(f'node-{VERSION}-darwin-arm64/LICENSE',ROOT/'search/NODE-LICENSE')]:
                file=tar.getmember(member)
                if not file.isfile():raise RuntimeError('Unexpected archive entry')
                data=tar.extractfile(file).read();partial=target.with_name(target.name+'.tmp');partial.write_bytes(data);partial.chmod(0o755 if target.name=='node' else 0o644);partial.replace(target)
    env={'PATH':str(ROOT/'bin')+':/usr/bin:/bin','HOME':os.environ['HOME']}
    actual=subprocess.check_output([str(ROOT/'bin/node'),'--version'],env=env,text=True).strip()
    if actual!=VERSION:raise RuntimeError('Node version mismatch')
    linkage=subprocess.check_output(['/usr/bin/otool','-L',str(ROOT/'bin/node')],text=True)
    if '/opt/homebrew/' in linkage or '/Users/' in linkage:raise RuntimeError('Portable Node has external runtime dependencies')
    result={'version':VERSION,'source':BASE+ARCHIVE,'archive_sha256':wanted,'binary_sha256':hashlib.file_digest((ROOT/'bin/node').open('rb'),'sha256').hexdigest(),'linkage':linkage,'restricted_path_run':True}
    (ROOT/'search/node-runtime.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
