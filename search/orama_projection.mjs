// Orama is injected from the existing pinned package; this is schema/projection glue.
// No second retrieval engine, vector database, or ranking implementation is added.
const fields={title:'string',path:'string',text:'string',assetKind:'enum',assetId:'enum',folders:'enum[]',personIds:'enum[]',personNames:'string[]',speakerIds:'enum[]',faceIds:'enum[]',faceNames:'string[]',source:'enum',recordKind:'enum',contentId:'enum'};
export function folderPrefixes(path){const p=path.split('/');p.pop();return p.map((_,i)=>p.slice(0,i+1).join('/'));}
function record(d,vector){return {id:d.id,title:d.kind==='file'?d.title:'',path:d.kind==='file'?d.path:'',text:d.text,assetKind:d.assetKind,assetId:d.assetId,folders:folderPrefixes(d.path),speakerIds:d.speakerIds||[],faceIds:d.faceIds||[],faceNames:d.faceNames||[],personIds:d.personIds||[],personNames:d.personNames||[],source:d.source||'ai',recordKind:d.kind,contentId:d.contentId,...(vector?{embedding:Array.from(vector)}:{})};}
export function createProjectIndexes(orama,projection){const text=orama.create({schema:{...fields,embedding:'vector[384]'}}),images=orama.create({schema:{...fields,embedding:'vector[512]'}});for(const d of projection.documents)orama.insert(text,record(d));return{text,images};}
export function addTextVector(orama,db,doc,vector){if(vector.length!==384)throw Error('Text vector width must be384');orama.update(db,doc.id,record(doc,vector));}
export function addImageVector(orama,db,doc,vector){if(vector.length!==512)throw Error('Image vector width must be512');orama.insert(db,record(doc,vector));}
export function where(filters={}){return{...(filters.faceId?{faceIds:{containsAll:[filters.faceId]}}:{}),...(filters.speakerId?{speakerIds:{containsAll:[filters.speakerId]}}:{}),...(filters.personId?{personIds:{containsAll:[filters.personId]}}:{}),...(filters.assetId?{assetId:{eq:filters.assetId}}:{}),...(filters.source?{source:{eq:filters.source}}:{})};}
export function searchText(orama,db,term,filters={},vector){return orama.search(db,{mode:vector?'hybrid':'fulltext',term,properties:['title','path','text','personNames','faceNames'],where:where(filters),tolerance:vector?1:0,threshold:0,limit:40,...(vector?{vector:{property:'embedding',value:Array.from(vector)},similarity:.12}:{})});}
export function searchImages(orama,db,vector,filters={}){if(vector.length!==512)throw Error('Image vector width must be512');return orama.search(db,{mode:'vector',vector:{property:'embedding',value:Array.from(vector)},where:{...where(filters),recordKind:{eq:'visual'}},similarity:.25,limit:40});}

export function addClipSummary(orama,indexes,contentId,packet){
 if(!Array.isArray(packet.vector)||packet.vector.length!==512||packet.vector.some(v=>!Number.isFinite(v))||Math.hypot(...packet.vector)<=1e-12)throw Error('CLIP summary must be512 finite values');
 const d={id:`content:${contentId}:clip_summary`,kind:'clip_summary',contentId,assetId:`content:${contentId}`,title:'',path:'',text:'',assetKind:'video',personIds:[],personNames:[],source:'clip_summary'};
 if(orama.getByID(indexes.images,d.id))orama.remove(indexes.images,d.id);
 orama.insert(indexes.images,record(d,packet.vector));return d.id;
}
export async function clipCandidates(orama,indexes,newContentId,fingerprints,eligibleIds,{limit=3,threshold=.9}={}){
 if(!Number.isInteger(limit)||limit<1||limit>16||threshold< -1||threshold>1)throw Error('Invalid candidate policy');
 const query=fingerprints[newContentId];if(!query||!Array.isArray(query.vector)||query.vector.length!==512||query.vector.some(v=>!Number.isFinite(v))||Math.hypot(...query.vector)<=1e-12)throw Error('Missing comparable CLIP summary');
 if(!query.model_revision)throw Error('Missing CLIP model/aggregation revision');
 for(const id of indexes.clipSummaryIds||[])if(orama.getByID(indexes.images,id))orama.remove(indexes.images,id);
 indexes.clipSummaryIds=[];const packets=new Map();
 for(const contentId of new Set(eligibleIds)){
  if(contentId===newContentId)continue;const packet=fingerprints[contentId];if(!packet||packet.model_revision!==query.model_revision)continue;
  const id=addClipSummary(orama,indexes,contentId,packet);indexes.clipSummaryIds.push(id);packets.set(id,{content_id:contentId,...packet});
 }
 const r=await orama.search(indexes.images,{mode:'vector',vector:{property:'embedding',value:query.vector},where:{recordKind:{eq:'clip_summary'}},similarity:threshold,limit});
 return r.hits.map(h=>({...packets.get(h.id),cosine:h.score}));
}
