import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {remarkShotLinks,timeTarget,resolveShotHref} from '../src/shot-links.js';
const shots=[{id:'visual:bison',assetId:'trailer',seconds:14.014,evidence:[{id:'speech:line',asset_id:'trailer',seconds:14.48}]},{id:'face:ariel',assetId:'trailer',seconds:56.056}];
test('Markdown renders GFM and grounded time links without changing prose',()=>{
 const text='* **Bison Shot:** spoken at **14.48s**; visible at **14.01s**.\n* **Ariel:** **00:56**.\n\n| Shot | Found |\n|---|---|\n| Bison | Yes |\n\n~~No longer needed~~';
 const html=renderToStaticMarkup(React.createElement(Markdown,{remarkPlugins:[remarkGfm,[remarkShotLinks,{results:shots}]]},text));
 assert.match(html,/<ul>/);assert.match(html,/<strong>Bison Shot:<\/strong>/);assert.match(html,/<table>/);assert.match(html,/<del>/);assert.match(html,/#shot=speech%3Aline/);assert.match(html,/#shot=visual%3Abison/);assert.match(html,/#shot=face%3Aariel/);assert.doesNotMatch(html,/\*\*/);
});
test('unretrieved and ambiguous times never turn into invented clip links',()=>{
 assert.equal(timeTarget('99.00s',shots),null);assert.equal(resolveShotHref('#shot=made-up&t=14',shots),null);assert.equal(resolveShotHref('#shot=visual%3Abison&t=80',shots),null);
 assert.equal(timeTarget('00:14',[...shots,{id:'other',assetId:'another-clip',seconds:14.2}]),null);
 assert.equal(resolveShotHref('#shot=speech%3Aline&t=14.48',shots).seconds,14.48);
});
test('code spans and existing links are left to the Markdown renderer',()=>{
 const html=renderToStaticMarkup(React.createElement(Markdown,{remarkPlugins:[[remarkShotLinks,{results:shots}]]},'`14.48s` and [shot](#shot=visual%3Abison&t=14.014)'));
 assert.match(html,/<code>14.48s<\/code>/);assert.equal((html.match(/<a /g)||[]).length,1);
});
