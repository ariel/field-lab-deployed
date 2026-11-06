// A small remark AST transform; Markdown parsing/rendering remains remark's job.
export function shotTargets(results=[]){
 const rows=results.flatMap(r=>[r,...(r.evidence||[])]),seen=new Set();
 return rows.filter(r=>{const key=`${r.id}:${r.assetId||r.asset_id}:${r.seconds}`;if(seen.has(key))return false;seen.add(key);return !!r.id&&Number.isFinite(r.seconds);});
}
export function timeTarget(label,results){
 const text=label.trim();let seconds,tolerance;
 if(/^\d+:\d{2}(?::\d{2})?$/.test(text)){seconds=text.split(':').reduce((n,p)=>n*60+Number(p),0);tolerance=1;}
 else if(/^\d+(?:\.\d+)?\s*s(?:ec(?:onds?)?)?$/i.test(text)){seconds=parseFloat(text);tolerance=text.includes('.')?.02:1;}
 else return null;
 const matches=shotTargets(results).filter(r=>Math.abs(r.seconds-seconds)<tolerance);
 if(!matches.length||new Set(matches.map(r=>r.assetId||r.asset_id)).size!==1)return null;
 return matches.sort((a,b)=>Math.abs(a.seconds-seconds)-Math.abs(b.seconds-seconds))[0];
}
export function shotHref(row){return '#shot='+encodeURIComponent(row.id)+'&t='+row.seconds;}
export function resolveShotHref(href,results){
 if(!href?.startsWith('#shot='))return null;
 const params=new URLSearchParams(href.slice(1)),matches=shotTargets(results).filter(r=>r.id===params.get('shot'));
 if(!matches.length)return null;
 const requested=params.has('t')?Number(params.get('t')):matches[0].seconds;
 return matches.find(r=>Number.isFinite(requested)&&Math.abs(r.seconds-requested)<.02)||null;
}
export function remarkShotLinks({results=[]}={}){
 return tree=>{
  function walk(node){
   if(!node.children||['link','linkReference','code','inlineCode'].includes(node.type))return;
   const children=[];
   for(const child of node.children){
    if(child.type!=='text'){walk(child);children.push(child);continue;}
    const pattern=/\b(?:\d+:\d{2}(?::\d{2})?|\d+(?:\.\d+)?\s*s(?:ec(?:onds?)?)?)\b/gi;let last=0;
    for(const match of child.value.matchAll(pattern)){
     const target=timeTarget(match[0],results);if(!target)continue;
     if(match.index>last)children.push({type:'text',value:child.value.slice(last,match.index)});
     children.push({type:'link',url:shotHref(target),children:[{type:'text',value:match[0]}]});last=match.index+match[0].length;
    }
    if(last<child.value.length)children.push({type:'text',value:child.value.slice(last)});
   }
   node.children=children;
  }walk(tree);
 };
}
