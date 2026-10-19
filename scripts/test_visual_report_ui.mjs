// Run real inline report JS against a small DOM test double, not a browser/layout test.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import vm from 'node:vm';
const html = fs.readFileSync(process.argv[2], 'utf8');
const embedded = html.match(/<script id="reportData" type="application\/json">([\s\S]*?)<\/script>/)[1];
const data = JSON.parse(embedded);
const all = [];
class Element {
  constructor() {
    this.dataset = {}; this.attrs = {}; this.style = {setProperty(key, value) { this[key] = value; }}; this.children = [];
    this.events = {}; this.hidden = false; this.className = '';
    this.classList = {
      add: name => { this.className += ` ${name}`; },
      remove: name => { this.className = this.className.split(/\s+/).filter(x => x !== name).join(' '); }
    };
  }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
  setAttribute(key, value) { this.attrs[key] = value; }
  getAttribute(key) { return this.attrs[key]; }
  addEventListener(event, fn) { this.events[event] = fn; }
  scrollIntoView() { this.scrolled = true; }
  focus() { this.focused = true; }
  select() { this.selected = true; }
}
const byId = new Map();
for (const tag of html.matchAll(/<[a-z][^>]*>/g)) {
  const el = new Element();
  const id = tag[0].match(/\bid="([^"]+)"/)?.[1];
  if (id) { assert.ok(!byId.has(`#${id}`)); byId.set(`#${id}`, el); }
  el.className = tag[0].match(/\bclass="([^"]+)"/)?.[1] || '';
  const mode = tag[0].match(/\bdata-mode="([^"]+)"/)?.[1];
  if (mode) el.dataset.mode = mode;
  el.value = tag[0].match(/\bvalue="([^"]+)"/)?.[1] || '';
  all.push(el);
}
byId.get('#reportData').textContent = embedded;
const buttons = all.filter(el => el.dataset.mode);
const document = {
  querySelector(selector) { assert.ok(byId.has(selector), `Missing ${selector}`); return byId.get(selector); },
  querySelectorAll(selector) {
    if (selector === '.tabs button') return buttons;
    if (selector === '.map-item button') return all.filter(el => el.attrs['aria-controls'] === 'regionLayer');
    if (/^\.[\w-]+$/.test(selector)) return all.filter(el => el.className.split(/\s+/).includes(selector.slice(1)));
    return [];
  },
  createElement() { const el = new Element(); all.push(el); return el; }
};
let copied = '';
const navigator = {clipboard: {async writeText(value) { copied = value; }}};
vm.runInNewContext(html.match(/<script>\s*([\s\S]*?)<\/script>/)[1], {
  document, navigator, matchMedia: () => ({matches: true})
});
const expected = data.color_asset ? 'color' : data.treatment_asset ? 'treatment' : 'source';
assert.equal(byId.get('#photoStage').dataset.mode, expected);
for (const button of buttons) {
  const mode = button.dataset.mode;
  const available = Boolean(data[`${mode}_asset`]);
  if (mode !== 'source') assert.equal(button.hidden, !available);
  const old = byId.get('#photoStage').dataset.mode;
  button.events.click();
  if (!available) { assert.equal(byId.get('#photoStage').dataset.mode, old); continue; }
  assert.equal(byId.get('#photoStage').dataset.mode, mode);
  assert.equal(button.attrs['aria-pressed'], 'true');
  assert.equal(buttons.filter(b => b.attrs['aria-pressed'] === 'true').length, 1);
  assert.equal(byId.get('#heroDownload').href, data[`${mode}_download`]);
  assert.equal(byId.get('#heroDownload').download, `photography-coach-${mode}.${data[`${mode}_extension`]}`);
  for (const kind of ['source', 'color', 'treatment']) {
    const suffix = kind[0].toUpperCase() + kind.slice(1);
    assert.equal(byId.get(`#hero${suffix}`).attrs['aria-hidden'], String(kind !== mode));
  }
  assert.ok(html.includes(`.photo-stage[data-mode="${mode}"] .${mode} { opacity: 1; }`));
}
for (const kind of ['color', 'treatment']) {
  const suffix = kind[0].toUpperCase() + kind.slice(1);
  if (data[`${kind}_asset`]) {
    assert.equal(byId.get(`#compare${suffix}`).src, data[`${kind}_asset`]);
    assert.equal(byId.get(`#download${suffix}`).href, data[`${kind}_download`]);
  } else {
    assert.equal(byId.get(`#compare${suffix}`).src, undefined);
    assert.equal(byId.get(`#download${suffix}`).hidden, true);
  }
}
assert.equal(byId.get('#heroDownload').hidden, !data.color_asset && !data.treatment_asset);
const toggle = byId.get('#toggleCompare');
const stage = byId.get('#photoStage');
const range = byId.get('#comparisonRange');
assert.equal(toggle.hidden, !data.color_asset);
toggle.events.click();
if (data.color_asset) {
  assert.equal(stage.dataset.mode, 'compare');
  assert.equal(byId.get('#comparisonControl').hidden, false);
  assert.equal(byId.get('#heroDownload').hidden, true, 'Composite preview must not advertise a download');
  assert.equal(toggle.attrs['aria-pressed'], 'true');
  assert.equal(buttons.filter(b => b.attrs['aria-pressed'] === 'true').length, 0);
  for (const value of [0, 25, 100]) {
    range.value = String(value); range.events.input();
    assert.equal(stage.style['--split'], `${value}%`);
    assert.ok(range.attrs['aria-valuetext'].includes(`${value}%`));
  }
  toggle.events.click();
  assert.equal(stage.dataset.mode, 'color');
  assert.equal(byId.get('#comparisonControl').hidden, true);
  assert.equal(byId.get('#heroDownload').hidden, false);
  toggle.events.click();
  buttons.find(b => b.dataset.mode === 'source').events.click();
  assert.equal(stage.dataset.mode, 'source');
  assert.equal(toggle.attrs['aria-pressed'], 'false');
  assert.equal(byId.get('#heroDownload').href, data.source_download);
} else {
  assert.notEqual(stage.dataset.mode, 'compare');
  assert.equal(byId.get('#comparisonControl').hidden, true);
}
const layer = byId.get('#regionLayer');
const locators = document.querySelectorAll('.map-item button');
for (const locator of locators) {
  locator.events.click();
  assert.equal(locator.attrs['aria-pressed'], 'true');
  assert.ok(layer.children.length > 0);
  assert.equal(byId.get('#inspection').scrolled, true);
  assert.equal(locators.filter(b => b.attrs['aria-pressed'] === 'true').length, 1);
}
if (data.edit.crop_region) {
  byId.get('#showCrop').events.click();
  assert.equal(layer.children.length, 1);
  assert.equal(layer.children[0].className, 'region crop');
  assert.equal(locators.filter(b => b.attrs['aria-pressed'] === 'true').length, 0);
  byId.get('#showCrop').events.click();
  assert.equal(layer.children.length, 0);
}
byId.get('#clearRegions').events.click();
assert.equal(layer.children.length, 0);
await byId.get('#copyPractice').events.click();
assert.equal(copied, byId.get('#practicePrompt').value);
assert.ok(copied.includes(data.exercise.instructions));
navigator.clipboard.writeText = async () => { throw new Error('Clipboard unavailable'); };
await byId.get('#copyPractice').events.click();
assert.equal(byId.get('#practicePrompt').hidden, false);
assert.equal(byId.get('#practicePrompt').selected, true);
assert.equal(byId.get('#scores').children.length, 8);
if (data.reference) {
  assert.equal(byId.get('#referenceLink').hidden, false);
  assert.equal(byId.get('#referenceLink').href, data.reference.url);
} else {
  assert.equal(byId.get('#referenceLink').hidden, true);
  assert.equal(byId.get('#lookingTask').textContent, data.reference_status);
}
if (data.integrity) {
  assert.equal(byId.get('#integritySection').hidden, false);
  assert.equal(byId.get('#integrityChecks').children.length, 6);
}
if (data.source_credit) {
  assert.equal(byId.get('#sourceCredit').hidden, false);
  assert.equal(byId.get('#creditAuthor').textContent, data.source_credit.author);
  assert.equal(byId.get('#creditSource').href, data.source_credit.url);
  assert.equal(byId.get('#creditLicense').href, data.source_credit.license_url);
}
assert.ok(html.includes('[hidden] { display: none !important; }'));
console.log('PASS: versions, comparison slider, downloads, regions/crop, clipboard fallback, scores/reference. DOM logic only; layout not tested.');
