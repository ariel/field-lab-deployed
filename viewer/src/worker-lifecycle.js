// Queued events from a superseded worker must not overwrite the current search.
export function watchWorker(worker,current,handlers){
 worker.onmessage=event=>{if(current.current===worker)handlers.message(event);};
 worker.onerror=event=>{if(current.current===worker)handlers.error(event);};
 return ()=>{worker.onmessage=null;worker.onerror=null;worker.terminate();if(current.current===worker)current.current=null;};
}
export function workerErrorMessage(event){return event?.message||'The search worker stopped. You can retry search and keep browsing.';}
