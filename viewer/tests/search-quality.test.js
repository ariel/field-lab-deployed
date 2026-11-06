import test from 'node:test';
import assert from 'node:assert/strict';
import {gateReranked,gateImages} from '../src/search-quality.js';
import {createIndexes,searchText} from '../src/search-index.js';
test('text gate uses raw cross-encoder logits, excludes unreranked tails and ignores relative retrieval score',()=>{
 const rows=[{id:'bad',score:1,rerankScore:-8},{id:'good',score:0.05,rerankScore:3},{id:'tail',score:1},{id:'invalid',rerankScore:NaN},{id:'boundary',rerankScore:0}];
 assert.deepEqual(gateReranked(rows,0).map(r=>r.id),['good','boundary']);
 assert.deepEqual(gateReranked([{score:1,rerankScore:-8}],0),[]);
});
test('image gate independently uses cosine with no normalization to the best result',()=>{
 assert.deepEqual(gateImages([{id:'weak',score:.19},{id:'strong',score:.32},{id:'bad',score:NaN}],.25).map(r=>r.id),['strong']);
 assert.deepEqual(gateImages([{id:'best-but-unrelated',score:.19}],.25),[]);
});
test('keyword fallback requires exact tokens and all terms',async()=>{
 const index=createIndexes([{id:'a',kind:'visual',assetKind:'video',assetId:'a',path:'a.mp4',title:'',text:'Sunlit forest with fallen tree and rocks'}]);
 assert.deepEqual(await searchText(index.text,'chocolate',{}),[]);
 assert.deepEqual(await searchText(index.text,'forest chocolate',{}),[]);
 assert.equal((await searchText(index.text,'forest',{}))[0].id,'a');
 assert.deepEqual(await searchText(index.text,'fores',{}),[]);
});

test('measured trailer controls fail conservative gates while grounded matches remain',()=>{
 assert.deepEqual(gateReranked([{id:'chocolate',rerankScore:-11},{id:'vehicle-wrong',rerankScore:-10.244}],-6),[]);
 assert.deepEqual(gateReranked([{id:'vehicle',rerankScore:-.475},{id:'animals',rerankScore:-4.95}],-6).map(r=>r.id),['vehicle','animals']);
 for(const score of [.210,.235,.232,.233,.231])assert.deepEqual(gateImages([{score}],.25),[]);
 assert.deepEqual(gateImages([{id:'bison',score:.281},{id:'tail',score:.255}],.25).map(r=>r.id),['bison']);
 assert.equal(gateImages([{score:.251}],.25).length,1);
});
