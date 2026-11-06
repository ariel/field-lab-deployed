import test from 'node:test';
import assert from 'node:assert/strict';
import {watchWorker,workerErrorMessage} from '../src/worker-lifecycle.js';
test('queued events from terminated worker cannot override its replacement or clear its reference',()=>{
 const old={terminate(){this.terminated=true}},fresh={terminate(){}},ref={current:old},events=[];
 const clean=watchWorker(old,ref,{message:e=>events.push(e),error:e=>events.push(e)}),queuedMessage=old.onmessage,queuedError=old.onerror;
 ref.current=fresh;watchWorker(fresh,ref,{message:e=>events.push(e),error:e=>events.push(e)});queuedMessage('stale ready');queuedError('stale error');assert.deepEqual(events,[]);clean();assert.equal(ref.current,fresh);assert.equal(old.onmessage,null);assert.equal(old.onerror,null);fresh.onmessage('fresh ready');assert.deepEqual(events,['fresh ready']);
});
test('generic worker error has a usable retry message instead of undefined',()=>{assert.doesNotMatch(workerErrorMessage({}),/undefined/);assert.match(workerErrorMessage({}),/retry search/);assert.equal(workerErrorMessage({message:'Module missing'}),'Module missing');});
