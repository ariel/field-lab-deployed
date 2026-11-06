import React from 'react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {remarkShotLinks,resolveShotHref} from './shot-links.js';
import {safeLocalUrl} from './data.js';

export function ChatMarkdown({text,results=[],onSelect}){
 return <div className="chat-answer"><Markdown remarkPlugins={[remarkGfm,[remarkShotLinks,{results}]]} components={{
  a:({href,children})=>{const shot=resolveShotHref(href,results);if(href?.startsWith('#shot='))return shot?<a href={href} onClick={e=>{e.preventDefault();onSelect({...shot,assetId:shot.assetId||shot.asset_id});}}>{children}</a>:<span>{children}</span>;return <a href={href} target="_blank" rel="noreferrer">{children}</a>;},
  img:({src,alt})=>safeLocalUrl(src)?<img src={src} alt={alt||''}/>:null
 }}>{text}</Markdown></div>;
}
