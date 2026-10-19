// Static homepage behavior and local links. Browser layout is checked separately.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';

const root = fileURLToPath(new URL('../docs/', import.meta.url));
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const byId = new Map();
const versionButtons = [];
const copyButtons = [];
class Element {
  constructor() { this.dataset = {}; this.attrs = {}; this.events = {}; this.hidden = true; }
  setAttribute(key, value) { this.attrs[key] = value; }
  addEventListener(event, fn) { this.events[event] = fn; }
  focus() { this.focused = true; }
  select() { this.selected = true; }
}
for (const tag of html.matchAll(/<[a-z][^>]*>/g)) {
  const element = new Element();
  const id = tag[0].match(/\bid="([^"]+)"/)?.[1];
  if (id) { assert.ok(!byId.has(id), `Duplicate ID: ${id}`); byId.set(id, element); }
  for (const [field, collection] of [['version', versionButtons], ['copy', copyButtons]]) {
    const value = tag[0].match(new RegExp(`data-${field}="([^"]+)"`))?.[1];
    if (value) { element.dataset[field] = value; collection.push(element); }
  }
}
for (const id of ['installCommand', 'starterPrompt']) {
  byId.get(id).textContent = html.match(new RegExp(`id="${id}">([^<]+)<`))[1];
}
let clipboardValue = '';
const navigator = {clipboard: {async writeText(value) { clipboardValue = value; }}};
const document = {
  documentElement: {dataset: {}},
  querySelector(selector) { assert.ok(byId.has(selector.slice(1)), selector); return byId.get(selector.slice(1)); },
  querySelectorAll(selector) { return selector === '[data-version]' ? versionButtons : selector === '[data-copy]' ? copyButtons : []; },
  getElementById(id) { return byId.get(id); }
};
let systemDark = false;
let onThemeChange;
vm.runInNewContext(fs.readFileSync(path.join(root, 'site.js'), 'utf8'), {
  document, navigator, matchMedia: () => ({matches: systemDark, addEventListener(event, fn) { onThemeChange = fn; }})
});
assert.equal(byId.get('sampleControls').hidden, false);
assert.equal(versionButtons.length, 3);
for (const button of versionButtons) {
  button.events.click();
  assert.equal(byId.get('sampleImage').src, `demo/assets/${button.dataset.version}-preview.jpg`);
  assert.ok(fs.existsSync(path.join(root, byId.get('sampleImage').src)));
  assert.equal(versionButtons.filter(b => b.attrs['aria-pressed'] === 'true').length, 1);
  assert.ok(byId.get('sampleImage').alt);
  assert.ok(byId.get('sampleNote').textContent);
}
for (const button of copyButtons) {
  assert.equal(button.hidden, false);
  await button.events.click();
  assert.equal(clipboardValue, byId.get(button.dataset.copy).textContent);
  assert.equal(byId.get('copyFallback').hidden, true);
}
navigator.clipboard.writeText = async () => { throw new Error('Denied'); };
await copyButtons[0].events.click();
assert.equal(byId.get('copyFallback').hidden, false);
assert.equal(byId.get('copyFallback').selected, true);
assert.equal(byId.get('copyFallback').value, byId.get('installCommand').textContent);
const theme = byId.get('themeToggle');
assert.equal(theme.hidden, false);
theme.events.click();
assert.equal(document.documentElement.dataset.theme, 'dark');
assert.equal(theme.attrs['aria-label'], '切换为浅色主题');
theme.events.click();
assert.equal(document.documentElement.dataset.theme, 'light');
delete document.documentElement.dataset.theme;
systemDark = true; onThemeChange();
assert.equal(theme.attrs['aria-label'], '切换为浅色主题');
for (const [, value] of html.matchAll(/(?:href|src)="([^"]+)"/g)) {
  if (/^(https?:|data:)/.test(value)) continue;
  assert.ok(!value.split('#')[0].endsWith('/'), `Use an explicit file for local-file navigation: ${value}`);
  const [file, fragment] = value.split('#');
  let target = file ? path.resolve(root, file) : path.join(root, 'index.html');
  assert.ok(fs.existsSync(target), `Missing ${value}`);
  if (fs.statSync(target).isDirectory()) target = path.join(target, 'index.html');
  assert.ok(fs.existsSync(target), `Missing ${value}`);
  if (fragment) assert.ok(fs.readFileSync(target, 'utf8').includes(`id="${fragment}"`), `Missing anchor ${value}`);
}
assert.ok(!html.includes('http-equiv="refresh"'), 'Home should not auto-redirect');
assert.ok(!html.includes('type="file"'), 'Static sample must not pretend to upload for critique');
console.log('PASS: home versions, copy/fallback, themes, local links and assets. Layout not tested.');
