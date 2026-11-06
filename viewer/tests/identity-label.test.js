import test from 'node:test';
import assert from 'node:assert/strict';
import {identityLabel} from '../src/identity-label.js';
test('identity display uses stable short modality labels and keeps assigned names',()=>{
 const voice={id:'person_3ec45d1234567890'},face={id:'face_6a71651234567890'};
 assert.equal(identityLabel(voice),'Voice 3ec45d');assert.equal(identityLabel(face),'Face 6a7165');assert.equal(identityLabel({...voice,name:'Ariel'}),'Ariel');assert.equal(voice.id,'person_3ec45d1234567890');
});
test('colliding short prefixes expand consistently within the modality',()=>{
 const a={id:'face_abcdef001234'},b={id:'face_abcdef101234'};assert.equal(identityLabel(a,[a,b]),'Face abcdef0');assert.equal(identityLabel(b,[a,b]),'Face abcdef1');assert.equal(identityLabel(a,[{id:'person_abcdef001234'}]),'Face abcdef');
});
