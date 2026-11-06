export const stamp = (value = 0) => {
  const s = Math.max(0, Number(value) || 0), h = Math.floor(s / 3600);
  return `${h ? String(h).padStart(2, '0') + ':' : ''}${String(Math.floor(s % 3600 / 60)).padStart(2, '0')}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
};
export function normalizeCatalog(raw = {}) {
  const project = typeof raw.project === 'string' ? {name:raw.project} : (raw.project || {});
  return {search_projection:raw.search_projection,updated_at:raw.updated_at,catalog_revision:raw.catalog_revision,project:{name:'Footage library', ...project},assets:(raw.assets || []).map((a,i) => {
    let transcript = a.transcript || a.sentences || [];
    if (!Array.isArray(transcript)) transcript = transcript.sentences || [];
    if (!transcript.length && Array.isArray(a.transcripts)) transcript = a.transcripts.flatMap(t => (t.sentences || t.segments || []).map(s => ({...s,stream:t.stream ?? t.index})));
    return {...a,id:String(a.id ?? a.content_id ?? i),name:a.name || a.filename || a.relative_path?.split('/').at(-1) || `Clip ${i+1}`,relative_path:a.relative_path || a.name || '',media_url:a.media_url || a.source_url || '',kind:a.kind || (/\.(wav|mp3|m4a|flac|aiff|aif|ogg)$/i.test(a.name || a.relative_path || '')?'audio':'video'),duration:Number(a.duration) || 0,highlights:(a.highlights || []).map((h,j)=>({...h,id:j,seconds:Number(h.seconds ?? h.start ?? h.time) || 0,note:h.note || h.text || '',image_url:h.image_url || h.image || ''})).sort((a,b)=>a.seconds-b.seconds),transcript:transcript.map((s,j)=>({...s,id:j,start:Number(s.start ?? s.seconds) || 0,end:Number(s.end ?? s.start ?? s.seconds) || 0,text:s.text || ''})).filter(s=>s.text.trim()).sort((a,b)=>a.start-b.start)};
  })};
}
function splitWords(text, size = 85) {
  const words = text.trim().split(/\s+/), chunks=[];
  for(let i=0;i<words.length;i+=size) chunks.push(words.slice(i,i+size).join(' '));
  return chunks;
}
export function buildDocuments(catalog) {
  if(Array.isArray(catalog.search_projection?.documents))return catalog.search_projection.documents;
  const docs=[];
  for(const a of catalog.assets){
    const base={assetId:a.id,contentId:a.content_id || a.id,title:a.name,path:a.relative_path,assetKind:a.kind};
    docs.push({...base,id:`${a.id}:file`,kind:'file',text:[a.name,a.relative_path].join(' '),seconds:0,image:a.poster_url || a.highlights[0]?.image_url || '',embed:false});
    a.highlights.forEach((h,i)=>{if(h.note.trim())docs.push({...base,id:`${a.id}:visual:${i}`,kind:'visual',text:h.note,seconds:h.seconds,image:h.image_url,embed:true});});
    a.transcript.forEach((s,i)=>splitWords(s.text).forEach((text,j)=>docs.push({...base,id:`${a.id}:speech:${i}:${j}`,kind:'speech',text,seconds:s.start,end:s.end,stream:s.stream,image:a.poster_url || a.highlights[0]?.image_url || '',embed:true})));
  }
  return docs;
}
export function folderOf(path){const i=path.lastIndexOf('/');return i<0?'':path.slice(0,i);}
export function safeLocalUrl(url){return typeof url==='string' && url.startsWith('/') && !url.startsWith('//') ? url : '';}
