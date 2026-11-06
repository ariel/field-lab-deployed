import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizeCatalog,buildDocuments,stamp,safeLocalUrl} from '../src/data.js';
import {contentKey,imageKey} from '../src/cache.js';
import {createIndexes,addTextVector,addImageVector,searchText,searchImages} from '../src/search-index.js';
test('normalizes timed words and visual cues without losing stream identity',()=>{
 const catalog=normalizeCatalog({project:{id:'p',name:'Prairies'},assets:[{id:'a',content_id:'same-content',name:'Interview.MP4',relative_path:'Day 1/Interview.MP4',duration:60,highlights:[{seconds:20,note:'Person at microscope',image_url:'/notes/frame.jpg'}],transcript:{sentences:[{start:4,end:8,text:'A meadow full of insects.',stream:2}]}}]});
 assert.equal(catalog.assets[0].transcript[0].stream,2);const docs=buildDocuments(catalog);assert.equal(docs.length,3);assert.equal(docs.find(d=>d.kind==='speech').seconds,4);assert.equal(docs.find(d=>d.kind==='visual').text,'Person at microscope');assert.equal(docs.find(d=>d.kind==='file').embed,false);
});
test('long transcript sentences create bounded searchable passages with their original timing',()=>{
 const text=Array.from({length:190},(_,i)=>`word${i}`).join(' '),docs=buildDocuments(normalizeCatalog({assets:[{id:'a',name:'a.wav',transcript:[{start:23,end:70,text}]}]})).filter(d=>d.kind==='speech');assert.equal(docs.length,3);assert.ok(docs.every(d=>d.seconds===23&&d.end===70));assert.equal(docs.map(d=>d.text).join(' '),text);
});
test('Orama native hybrid and CLIP indexes return semantic and visual candidates with native folder filters',async()=>{
 const docs=[{id:'1',assetId:'one',assetKind:'video',path:'Day 1/a.mp4',title:'a',text:'A scientist at a microscope'},{id:'2',assetId:'two',assetKind:'video',path:'Day 2/b.mp4',title:'b',text:'Person in yellow gear'}],db=createIndexes(docs);
 const v=Array(384).fill(0);v[0]=1;addTextVector(db.text,docs[0],v);
 const results=await searchText(db.text,'science',{},v);assert.equal(results[0].id,'1');assert.equal((await searchText(db.text,'science',{folder:'Day 2'},v)).length,0);
 const image=Array(512).fill(0);image[1]=1;addImageVector(db.images,docs[1],image);const images=await searchImages(db.images,image,{});assert.equal(images[0].id,'2');assert.equal(images[0].kind,'image');assert.equal((await searchImages(db.images,image,{folder:'Day 1'})).length,0);
});
test('vector cache survives reorganization and invalidates changed text/model revision',async()=>{
 const doc={contentId:'content',kind:'speech',text:'A prairie story',path:'a/original.mp4'},a=await contentKey('project',doc,'revision-a'),b=await contentKey('project',{...doc,path:'b/moved.mp4'},'revision-a');assert.equal(a,b);assert.notEqual(a,await contentKey('project',{...doc,text:'New'},'revision-a'));assert.notEqual(a,await contentKey('project',doc,'revision-b'));assert.notEqual(a,await contentKey('another-project',doc,'revision-a'));
 const frame={...doc,image:'/notes/.objects/content/frame.jpg',seconds:8};assert.notEqual(await imageKey('p',frame,'a'),await imageKey('p',frame,'b'));
});
test('local media URLs reject external origins and protocol-relative paths',()=>{assert.equal(safeLocalUrl('https://example.com/a.mp4'),'');assert.equal(safeLocalUrl('//example.com/a.mp4'),'');assert.equal(safeLocalUrl('/media/Day%201/a.mp4'),'/media/Day%201/a.mp4');assert.equal(safeLocalUrl('file:///private/a.mp4'),'');});
test('clip relative timestamp formatting',()=>{assert.equal(stamp(3661.4),'01:01:01');assert.equal(stamp(-1),'00:00');});
