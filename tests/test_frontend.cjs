const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const elements = new Map();
function element() {
  return {
    children: [],
    addEventListener(){},
    append(...children){ this.children.push(...children); },
    replaceChildren(){ this.children = []; },
    style:{}, setAttribute(){}, files:[], value:''
  };
}
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

test('YouTube bars show all three sentiments and count unclassified comments separately', () => {
  sandbox.renderYouTube({
    resultados: [
      { texto: 'Gran video', sentimiento_modelo: 'POSITIVO', probabilidades: { POSITIVO: 0.9 }, confianza: 0.9, motivos_revision: [] },
      { texto: 'Another language', sentimiento_modelo: 'PENDIENTE_IDIOMA', probabilidades: {}, motivos_revision: ['Traducir'] }
    ],
    resumen: { POSITIVO: 1, PENDIENTE_IDIOMA: 1 }
  });
  const [positive, positiveBar, neutral, neutralBar, negative, negativeBar] = elements.get('youtube-chart').children;
  assert.deepEqual([positive.textContent, neutral.textContent, negative.textContent], ['Positivo · 1', 'Neutral · 0', 'Negativo · 0']);
  assert.deepEqual([positiveBar.value, neutralBar.value, negativeBar.value], [1, 0, 0]);
  assert.equal(positiveBar.max, 2);
  assert.equal(elements.get('youtube-totals').textContent, '2 obtenidos · 1 clasificados · 1 sin clasificar');
});
