import { defineConfig } from 'vite';
export default defineConfig({worker:{format:'es'},build:{target:'es2022',sourcemap:true},server:{proxy:{'/api':'http://127.0.0.1:8765','/media':'http://127.0.0.1:8765','/notes':'http://127.0.0.1:8765','/models':'http://127.0.0.1:8765','/runtime':'http://127.0.0.1:8765'}}});
