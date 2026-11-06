// Display only: canonical UUIDs stay unchanged in APIs, forms and audit records.
export function identityLabel(value,peers=[]){
 const identity=typeof value==='string'?{id:value}:value||{};
 if(identity.name)return identity.name;
 const id=String(identity.id||''),kind=id.startsWith('face_')?'Face':'Voice';
 const token=id.replace(/^(?:face|person)_/,'');let length=Math.min(6,token.length);
 const others=peers.map(p=>typeof p==='string'?p:p.id).filter(other=>other&&other!==id&&other.startsWith(kind==='Face'?'face_':'person_')).map(other=>other.replace(/^(?:face|person)_/,''));
 while(length<token.length&&others.some(other=>other.slice(0,length)===token.slice(0,length)))length++;
 return `${kind} ${token.slice(0,length)}`;
}
