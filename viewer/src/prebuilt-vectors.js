// Accept only vectors from the active local MLX model revision and known document IDs.
export function selectPrebuilt(payload,readiness,documents,catalogRevision){
 const result={text:new Map(),image:new Map()};
 if(readiness.backend?.type!=='mlx'||!readiness.backend.ready)return result;
 if(catalogRevision!=null&&payload?.catalog_revision!=null&&String(catalogRevision)!==String(payload.catalog_revision))return result;
 const expected=readiness.backend.revision||{},actual=payload?.revision||{};
 const docs=new Map(documents.map(doc=>[doc.id,doc]));
 for(const row of payload?.vectors||[]){
  const kind=row.kind,doc=docs.get(row.document_id),model=kind==='text'?'text':kind==='image'?'clip':null;
  if(!model||!doc||!expected[model]||actual[model]!==expected[model])continue;
  if(kind==='text'&&!doc.embed||kind==='image'&&(doc.kind!=='visual'||!doc.image))continue;
  const vector=row.vector,width=kind==='text'?384:512;
  if(!Array.isArray(vector)||vector.length!==width||vector.some(value=>!Number.isFinite(value)))continue;
  const norm=Math.hypot(...vector);if(!norm)continue;
  result[kind].set(doc.id,Float32Array.from(vector,value=>value/norm));
 }
 return result;
}
