const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const elements = new Map();
function element() { return { addEventListener(){}, append(){}, replaceChildren(){}, style:{}, setAttribute(){}, files:[], value:'' }; }
const sandbox = { document:{ getElementById(id){ if(!elements.has(id))elements.set(id,element());return elements.get(id); }, createElement:element }, GameAPI:{request:()=>Promise.resolve({redes:[]})}, setTimeout, URL, Blob, FormData };
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync('frontend/js/app.js','utf8'),sandbox);
test('CSV formulas neutralized, quoted values preserved',()=>{
  for(const value of ['=1+1','+cmd','-1+2','@SUM(A1)','  =1','\tformula']) assert.match(sandbox.csvCell(value),/^"'/);
  assert.equal(sandbox.csvCell('hola "juego"'),'"hola ""juego"""');
  assert.equal(sandbox.csvCell('normal'),'"normal"');
});
test('user content is assigned as plain text',()=>{
  const node=sandbox.el('p','<img src=x onerror=alert(1)>');
  assert.equal(node.textContent,'<img src=x onerror=alert(1)>');
  assert.equal(node.innerHTML,undefined);
});
