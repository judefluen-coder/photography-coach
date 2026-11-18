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
  addEventListener(event, fn) { const previous=this.events[event]; this.events[event]=previous ? (...args)=>{ previous(...args); fn(...args); } : fn; }
  contains(target) { return target === this || this.children.some(child => child.contains(target)); }
  getBoundingClientRect() {
    const rect = {...(this.rect || {left:120, top:120, width:44, height:44})};
    if (this.style.width?.endsWith('px')) rect.width = parseFloat(this.style.width);
    if (this.style.maxHeight?.endsWith('px')) rect.height = Math.min(rect.height, parseFloat(this.style.maxHeight));
    return {...rect,right:rect.left+rect.width,bottom:rect.top+rect.height};
  }
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
  el.hidden = /\shidden(?:\s|>)/.test(tag[0]);
  const mode = tag[0].match(/\bdata-mode="([^"]+)"/)?.[1];
  if (mode) el.dataset.mode = mode;
  el.value = tag[0].match(/\bvalue="([^"]+)"/)?.[1] || '';
  all.push(el);
}
byId.get('#reportData').textContent = embedded;
byId.get('#annotatedPhoto').rect = {left:0, top:0, width:640, height:480};
byId.get('#photoNote').rect = {left:0, top:0, width:290, height:160};
byId.get('#photoNote').append(...['#photoNoteTitle', '#photoNoteText', '#closePhotoNote', '#photoNoteLimits', '#photoNoteEdit'].map(id => byId.get(id)));
const buttons = all.filter(el => el.dataset.mode);
const document = {
  documentElement: {dataset: {}},
  events: {},
  addEventListener(event, fn) { this.events[event] = fn; },
  querySelector(selector) { assert.ok(byId.has(selector), `Missing ${selector}`); return byId.get(selector); },
  querySelectorAll(selector) {
    if (selector === '.tabs button') return buttons;
    if (selector === '.map-item button') return all.filter(el => el.className === 'observation-toggle');
    if (/^\.[\w-]+$/.test(selector)) return all.filter(el => el.className.split(/\s+/).includes(selector.slice(1)));
    return [];
  },
  createElement() { const el = new Element(); all.push(el); return el; },
  createElementNS(namespace, tag) { const el = new Element(); el.tag = tag; el.namespace = namespace; all.push(el); return el; }
};
let copied = '';
const navigator = {clipboard: {async writeText(value) { copied = value; }}};
const systemTheme = {matches: false, addEventListener(event, fn) { this.onChange = fn; }};
vm.runInNewContext(html.match(/<script>\s*([\s\S]*?)<\/script>/)[1], {
  document, navigator, matchMedia: query => query.includes('color-scheme') ? systemTheme : {matches: true}
});
const themeToggle = byId.get('#reportThemeToggle');
assert.equal(themeToggle.hidden, false);
assert.equal(themeToggle.attrs['aria-label'], '切换为浅色主题');
themeToggle.events.click();
assert.equal(document.documentElement.dataset.theme, 'light');
assert.equal(themeToggle.attrs['aria-label'], '切换为深色主题');
themeToggle.events.click();
assert.equal(document.documentElement.dataset.theme, 'dark');
delete document.documentElement.dataset.theme;
systemTheme.matches = true;
systemTheme.onChange();
assert.equal(themeToggle.attrs['aria-label'], '切换为浅色主题');
const expected = data.color_asset ? 'color' : data.treatment_asset ? 'treatment' : 'source';
const hasAdjustment = Boolean(data.color_asset || data.treatment_asset);
assert.equal(byId.get('#photoToolbar').hidden,!hasAdjustment,'No empty version toolbar when only the source exists');
assert.equal(byId.get('#editTitle').textContent, hasAdjustment ? '调整对照' : '后期建议');
assert.equal(byId.get('#editToneColor').textContent, data.edit.tone_color);
assert.equal(byId.get('#editCrop').textContent, data.edit.crop);
assert.ok(byId.get('#editStatus').textContent.includes(data.color_asset ? '已有仅调色' : data.treatment_asset ? '未单独提供仅调色' : '尚未生成调色'));
assert.equal(byId.get('#photoStage').dataset.mode, expected);
for (const kind of ['source', 'color', 'treatment']) {
  const suffix = kind[0].toUpperCase() + kind.slice(1);
  const loadedForDetail = Boolean(data.color_asset) && ['source','color'].includes(kind);
  assert.equal(byId.get(`#hero${suffix}`).src, kind === expected || loadedForDetail ? data[`${kind}_asset`] : undefined);
}
for (const button of buttons) {
  const mode = button.dataset.mode;
  const available = Boolean(data[`${mode}_asset`]);
  if (mode !== 'source') assert.equal(button.hidden, !available);
  const old = byId.get('#photoStage').dataset.mode;
  button.events.click();
  if (!available) { assert.equal(byId.get('#photoStage').dataset.mode, old); continue; }
  assert.equal(byId.get('#photoStage').dataset.mode, mode);
  const heroSuffix = mode[0].toUpperCase() + mode.slice(1);
  assert.equal(byId.get(`#hero${heroSuffix}`).src, data[`${mode}_asset`]);
  assert.ok(byId.get('#currentVersion').textContent);
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
  assert.equal(byId.get('#heroSource').src, data.source_asset);
  assert.equal(byId.get('#heroColor').src, data.color_asset);
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
const guides = data.visual_guides || [];
const note = byId.get('#photoNote');
assert.equal(note.hidden, true, 'Explanations start collapsed on the photograph');
assert.ok(!byId.has('#guideTakeaway'), 'Do not repeat guide explanations underneath the image');
const guideChoices = byId.get('#guideControls').children;
assert.equal(byId.get('#guideControls').hidden, !guides.length);
assert.equal(guideChoices.length, guides.length ? guides.length + 1 : 0);
for (const [index, guide] of guides.entries()) {
  const photoLabels = guide.labels.length ? guide.labels : [{text:'图解说明', explanation:guide.takeaway}];
  guideChoices[index].events.click();
  assert.equal(byId.get('#guidePanel').hidden, false);
  assert.equal(byId.get('#observationMap').hidden, true);
  assert.equal(layer.hidden, true);
  assert.equal(byId.get('#pinLayer').hidden, true);
  assert.equal(guideChoices.filter(button => button.attrs['aria-pressed'] === 'true').length, 1);
  assert.ok(byId.get('#guideSketch').attrs['aria-label'].includes(guide.takeaway));
  for (const id of ['#guideOverlay', '#guideSketch']) {
    const parts = byId.get(id).children;
    const paths = parts[0].children;
    assert.equal(parts[0].attrs.viewBox, '0 0 100 100');
    assert.equal(paths.filter(node => node.attrs.class === 'guide-shape guide-area').length, guide.areas.length);
    assert.equal(paths.filter(node => node.attrs.class === 'guide-shape guide-line').length, guide.lines.length);
    assert.equal(paths.filter(node => node.attrs.class === 'guide-shape guide-arrow').length, guide.lines.filter(line => line.arrow).length);
    assert.deepEqual(parts.slice(1).map(part => part.textContent), (id === '#guideOverlay' ? photoLabels : guide.labels).map(label => label.text));
    for (const path of paths) assert.ok(!/NaN|undefined|Infinity/.test(path.attrs.points));
  }
  const labels = byId.get('#guideOverlay').children.slice(1);
  for (const [labelIndex, marker] of labels.entries()) {
    marker.events.click();
    assert.equal(note.hidden, false);
    assert.equal(marker.attrs['aria-expanded'], 'true');
    assert.equal(marker.attrs['aria-controls'], 'photoNote');
    assert.equal(byId.get('#photoNoteTitle').textContent, photoLabels[labelIndex].text);
    assert.equal(byId.get('#photoNoteText').textContent, photoLabels[labelIndex].explanation || guide.takeaway);
    assert.equal(byId.get('#photoNoteBoundary').textContent, guide.boundary);
    assert.equal(byId.get('#photoNoteEdit').hidden, true, 'Do not guess an edit link from a guide label');
    assert.equal(labels.filter(label => label.attrs['aria-expanded'] === 'true').length, 1);
    document.events.click({target:byId.get('#photoNoteText')});
    assert.equal(note.hidden, false, 'Clicking inside does not dismiss the explanation');
    marker.events.click();
    assert.equal(note.hidden, true);
    assert.equal(marker.attrs['aria-expanded'], 'false');
  }
  if (labels.length) {
    labels[0].events.click();
    byId.get('#closePhotoNote').events.click();
    assert.equal(note.hidden, true);
    assert.equal(labels[0].focused, true);
    labels[0].events.click();
    let prevented = false;
    document.events.keydown({key:'Escape', preventDefault() { prevented = true; }});
    assert.equal(prevented, true);
    assert.equal(note.hidden, true);
    labels[0].events.click();
    document.events.click({target:byId.get('#inspectionSource')});
    assert.equal(note.hidden, true);
    labels[0].events.click();
    if (labels.length > 1) {
      labels[1].events.click();
      assert.equal(labels[0].attrs['aria-expanded'], 'false');
      assert.equal(labels[1].attrs['aria-expanded'], 'true');
    }
    // Keep the card inside the photo, including when a mark is on an edge.
    const frame = byId.get('#annotatedPhoto');
    const marker = labels[Math.min(1, labels.length - 1)];
    for (const [width,height] of [[640,480],[350,263]]) {
      frame.rect = {left:0,top:0,width,height};
      marker.rect = {left:width-44,top:height-44,width:44,height:44};
      byId.get('#inspectionSource').events.load();
      const box = note.getBoundingClientRect();
      assert.ok(parseFloat(note.style.left) >= 8 && parseFloat(note.style.left) + box.width <= width - 8);
      assert.ok(parseFloat(note.style.top) >= 8 && parseFloat(note.style.top) + box.height <= height - 8);
    }
    for (const [left,top] of [[60,72],[135,94],[75,170]]) {
      frame.rect = {left:0,top:0,width:350,height:263};
      marker.rect = {left,top,width:120,height:44};
      byId.get('#inspectionSource').events.load();
      const box = note.getBoundingClientRect(), x = parseFloat(note.style.left), y = parseFloat(note.style.top);
      assert.ok(x + box.width <= left || x >= left + 120 || y + box.height <= top || y >= top + 44, 'Expanded marker remains tappable');
      assert.equal(byId.get('#noteConnector').hidden, false);
    }
    frame.rect = {left:0,top:0,width:640,height:480};
  }
  byId.get('#toggleGuide').events.click();
  assert.equal(note.hidden, true, 'Hiding marks also dismisses their explanation');
  assert.equal(byId.get('#noteConnector').hidden, true);
  assert.equal(byId.get('#guideOverlay').hidden, true);
  assert.equal(byId.get('#toggleGuide').attrs['aria-pressed'], 'false');
  byId.get('#toggleGuide').events.click();
  assert.equal(byId.get('#guideOverlay').hidden, false);
}
if (guides.length) {
  const photo = byId.get('#inspectionSource');
  photo.naturalWidth = 960; photo.naturalHeight = 1280; photo.events.load();
  assert.equal(byId.get('#guideSketch').style.aspectRatio, '960 / 1280', 'Use source framing, including portrait photos');
  guideChoices[guides.length].events.click();
  assert.equal(byId.get('#guidePanel').hidden, true);
  assert.equal(byId.get('#observationMap').hidden, false);
  assert.equal(byId.get('#guideOverlay').hidden, true);
  assert.equal(layer.hidden, false);
  assert.equal(byId.get('#pinLayer').hidden, false);
}
assert.equal(byId.get('#observationWorkspace').className.includes('text-only'), byId.get('#inspection').hidden);
const locators = document.querySelectorAll('.map-item button');
for (const [index, locator] of locators.entries()) {
  locator.events.click();
  assert.equal(locator.attrs['aria-pressed'], 'true');
  assert.equal(layer.children.length, data.observations[index].regions?.length || 0);
  if (layer.children.length) assert.equal(byId.get('#inspection').scrolled, true);
  assert.equal(locators.filter(b => b.attrs['aria-pressed'] === 'true').length, 1);
  assert.equal(locator.attrs['aria-expanded'], 'true');
  if (data.observations[index].regions?.length) {
    assert.equal(note.hidden, false);
    assert.equal(byId.get('#photoNoteText').textContent, data.observations[index].text);
    assert.equal(byId.get('#photoNoteEdit').hidden, data.learning_check?.observation_index !== index);
    assert.equal(byId.get('#photoNoteLimits').hidden, true);
    assert.equal(byId.get('#observationMap').children[index].children[1].hidden, true);
    locator.events.click();
    assert.equal(note.hidden, true);
    assert.equal(locator.attrs['aria-expanded'], 'false');
  } else {
    assert.equal(note.hidden, true, 'Do not fabricate a point for an unlocalized observation');
  }
}
const pins = byId.get('#pinLayer').children;
assert.equal(pins.length, data.observations.filter(item => item.regions?.length).length);
for (const pin of pins) {
  pin.events.click();
  assert.equal(pin.attrs['aria-current'], 'true');
  assert.equal(pins.filter(item => item.attrs['aria-current'] === 'true').length, 1);
  assert.ok(layer.children.length > 0);
  assert.equal(note.hidden, false);
  pin.events.click();
  assert.equal(note.hidden, true);
  assert.equal(pin.attrs['aria-expanded'], 'false');
  assert.equal(layer.children.length, 0);
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
assert.equal(byId.get('#pinLayer').hidden, true);
byId.get('#clearRegions').events.click();
assert.equal(byId.get('#pinLayer').hidden, false);
const learning = data.learning_check;
const lesson = byId.get('#learningCheck');
assert.equal(lesson.hidden, !learning);
assert.equal(Boolean(lesson.open), false, 'The optional question never gates the critique');
assert.equal(byId.get('#learningAnswer').hidden, true);
assert.equal(byId.get('#learningSource').src, undefined, 'Do not load collapsed optional photos');
if (learning) {
  lesson.open = true; lesson.events.toggle();
  assert.equal(byId.get('#learningSource').src, data.source_asset);
  assert.equal(byId.get('#learningQuestion').textContent, learning.question);
  assert.equal(byId.get('#learningRegions').children.length, data.observations[learning.observation_index].regions?.length || 0);
  const choices = byId.get('#learningOptions').children;
  const feedback = byId.get('#learningFeedback').children;
  assert.equal(choices.length, 2);
  assert.equal(feedback.length, 2);
  byId.get('#skipLearning').events.click();
  assert.equal(byId.get('#learningAnswer').hidden, false, 'All reasoning is available without an answer');
  assert.equal(byId.get('#learningQuestion').focused, true);
  assert.equal(choices.filter(button => button.attrs['aria-pressed'] === 'true').length, 0, 'Skip never counts as an answer');
  for (const [index, choice] of choices.entries()) {
    choice.events.click();
    assert.equal(byId.get('#learningAnswer').hidden, false);
    assert.equal(choice.attrs['aria-pressed'], 'true');
    assert.equal(choices.filter(button => button.attrs['aria-pressed'] === 'true').length, 1);
    assert.equal(feedback[index].dataset.selected, 'true');
    assert.equal(feedback[index].children[1].children[1].textContent, learning.options[index].effect);
    assert.equal(feedback[index].children[2].children[1].textContent, learning.options[index].cost);
  }
  assert.equal(byId.get('#learningTakeaway').textContent, learning.takeaway);
  let stopped = false;
  byId.get('#learningBack').events.click({stopPropagation() { stopped = true; }});
  if (!stopped) document.events.click({target:byId.get('#learningBack')});
  assert.equal(stopped, true, 'Returning to a note must not immediately trigger outside-click dismissal');
  const related = locators[learning.observation_index];
  assert.equal(related.attrs['aria-pressed'], 'true');
  if (data.observations[learning.observation_index].regions?.length) {
    assert.equal(note.hidden, false);
    assert.equal(byId.get('#photoNoteEdit').hidden, false);
    byId.get('#photoNoteEdit').events.click();
    assert.equal(note.hidden, true);
    assert.equal(byId.get('#editTitle').scrolled, true);
    assert.equal(byId.get('#editTitle').focused, true);
  } else {
    assert.equal(note.hidden, true);
    assert.equal(related.focused, true);
  }
}
const compareFromEdit = byId.get('#openEditCompare');
assert.equal(compareFromEdit.hidden, !data.color_asset);
const oldMode = stage.dataset.mode;
compareFromEdit.events.click();
if (data.color_asset) {
  assert.equal(stage.dataset.mode, 'compare');
  assert.equal(stage.scrolled, true);
  assert.equal(range.focused, true);
  compareFromEdit.events.click();
  assert.equal(stage.dataset.mode, 'compare', 'The jump action is idempotent, not a toggle');
} else {
  assert.equal(stage.dataset.mode, oldMode, 'No color asset means no simulated comparison');
}
await byId.get('#copyPractice').events.click();
assert.equal(copied, byId.get('#practicePrompt').value);
assert.ok(copied.includes(data.exercise.instructions));
navigator.clipboard.writeText = async () => { throw new Error('Clipboard unavailable'); };
await byId.get('#copyPractice').events.click();
assert.equal(byId.get('#practicePrompt').hidden, false);
assert.equal(byId.get('#practicePrompt').selected, true);
assert.equal(byId.get('#scores').children.length, 8);
const radarChoices = byId.get('#radarChoices').children;
const radarNodes = byId.get('#scoreRadar').children;
const knownScores = data.scores.filter(score => score.interval !== 'N/A');
assert.equal(radarChoices.length, 8);
assert.equal(radarNodes.filter(node => node.attrs.class === 'radar-grid').length, 5);
assert.equal(radarNodes.filter(node => node.attrs.class === 'radar-axis').length, 8);
assert.equal(radarNodes.filter(node => node.attrs.class === 'radar-dot').length, knownScores.length);
const plottedDots = radarNodes.filter(node => node.attrs.class === 'radar-dot');
let plottedIndex = 0;
data.scores.forEach((score, index) => {
  if (score.interval === 'N/A') return;
  const high = Number(score.interval.match(/\d/g)[1]);
  const dot = plottedDots[plottedIndex++];
  assert.ok(Math.abs(Number(dot.attrs.cx) - (250 + Math.sin(index * Math.PI / 4) * 140 * high / 5)) < .001);
  assert.ok(Math.abs(Number(dot.attrs.cy) - (220 - Math.cos(index * Math.PI / 4) * 140 * high / 5)) < .001);
});
assert.equal(radarNodes.filter(node => node.attrs.class === 'radar-band').length, knownScores.length === 8 ? 1 : 0);
if (knownScores.length < 8) {
  assert.equal(byId.get('#radarCoverage').hidden, false);
  assert.equal(radarNodes.filter(node => node.tag === 'polygon' && /^radar-(upper|lower)$/.test(node.attrs.class)).length, 0, 'Do not connect missing scores into a filled polygon');
}
for (const [index, choice] of radarChoices.entries()) {
  choice.events.click();
  const score = data.scores[index];
  assert.equal(byId.get('#selectedDimension').textContent, score.dimension);
  assert.equal(byId.get('#selectedReason').textContent, score.reason);
  assert.equal(byId.get('#selectedInterval').textContent, score.interval === 'N/A' ? '未评分' : score.interval);
  assert.equal(byId.get('#selectedUncertainty').hidden, !score.uncertainty);
  assert.equal(byId.get('#selectedConfidence').hidden, !score.confidence);
  if (score.confidence) assert.ok(byId.get('#selectedConfidence').textContent.includes(score.confidence));
  assert.equal(choice.attrs['aria-pressed'], 'true');
  assert.equal(radarChoices.filter(button => button.attrs['aria-pressed'] === 'true').length, 1);
  assert.equal(radarNodes.filter(node => node.attrs.class === 'radar-axis' && node.attrs['data-selected'] === 'true').length, 1);
}
for (const node of radarNodes) {
  for (const key of ['x1','y1','x2','y2','cx','cy','r']) if (key in node.attrs) assert.ok(Number.isFinite(Number(node.attrs[key])), `Finite SVG ${key}`);
  for (const key of ['points','d']) if (key in node.attrs) assert.ok(!/NaN|undefined|Infinity/.test(node.attrs[key]));
}
for (const [index, score] of byId.get('#scores').children.entries()) {
  const interval = data.scores[index].interval;
  const track = score.children.find(item => item.className === 'score-track');
  if (interval === 'N/A') { assert.equal(track, undefined); continue; }
  const [low, high] = interval.match(/\d/g).map(Number);
  assert.equal(track.attrs.role, 'img');
  assert.ok(track.attrs['aria-label'].includes(interval));
  assert.equal(track.children[0].style['--low'], low === 5 ? 'calc(100% - 3px)' : `${low * 20}%`);
  assert.equal(track.children[0].style['--range'], `${(high - low) * 20}%`);
}
if (data.reference) {
  assert.equal(byId.get('#referenceLink').hidden, false);
  assert.equal(byId.get('#referenceLink').href, data.reference.url);
} else {
  assert.equal(byId.get('#referenceLink').hidden, true);
  assert.equal(byId.get('#referenceWork').textContent, '本次未提供参考作品');
  assert.equal(byId.get('#lookingTask').textContent, data.reference_status);
}
if (data.integrity) {
  assert.equal(byId.get('#integritySection').hidden, false);
  assert.equal(byId.get('#integrityChecks').children.length, 6);
  assert.equal(byId.get('#integritySummary').children.length, 6);
}
assert.equal(byId.get('#summary').textContent, data.summary);
assert.equal(byId.get('#summary').hidden, false);
assert.equal(byId.get('#priorityPreview').hidden, Boolean(data.coaching));
assert.equal(byId.get('#practiceConnection').hidden, !data.coaching);
assert.equal(byId.get('#practiceCriterion').hidden, !data.coaching);
if (data.coaching) {
  assert.equal(byId.get('#decisionLabel').textContent, data.coaching.action_type);
  assert.ok(byId.get('#practiceConnection').textContent.includes(data.coaching.exercise_connection));
  assert.ok(byId.get('#practiceCriterion').textContent.includes(data.coaching.success_criterion));
  assert.ok(copied.includes(data.coaching.success_criterion));
}
if (data.source_credit) {
  assert.equal(byId.get('#sourceCredit').hidden, false);
  assert.equal(byId.get('#creditAuthor').textContent, data.source_credit.author);
  assert.equal(byId.get('#creditSource').href, data.source_credit.url);
  assert.equal(byId.get('#creditLicense').href, data.source_credit.license_url);
}
assert.ok(html.includes('[hidden] { display: none !important; }'));
// Darkroom controls must reflect actual asset availability and preserve source geometry.
assert.equal(byId.get('#toneControls').hidden, !data.color_asset);
assert.equal(byId.get('#downloadMix').hidden, !data.color_asset);
assert.equal(byId.get('#mixHelp').hidden, !data.color_asset);
buttons.find(button=>button.dataset.mode==='source').events.click();
stage.rect={left:0,top:0,width:1000,height:400};
const sourceImage=byId.get('#heroSource'); sourceImage.naturalWidth=2000; sourceImage.naturalHeight=1000;
sourceImage.events.load();
assert.equal(parseFloat(byId.get('#photoCanvas').style.width),800);
assert.equal(parseFloat(byId.get('#photoCanvas').style.height),400);
const zoom=byId.get('#toggleZoom'); zoom.events.click();
assert.equal(stage.dataset.zoom,'detail');
assert.equal(parseFloat(byId.get('#photoCanvas').style.width),1250);
assert.equal(parseFloat(byId.get('#photoCanvas').style.height),625);
assert.equal(byId.get('#zoomState').textContent,'局部视图，未修改取景');
zoom.events.click();
assert.equal(stage.dataset.zoom,'fit');
assert.equal(parseFloat(byId.get('#photoCanvas').style.width)/parseFloat(byId.get('#photoCanvas').style.height),2);
const strength=byId.get('#toneMix'); strength.value='40'; strength.events.input();
if(data.color_asset) {
  assert.equal(stage.style['--tone-opacity'],'0.4');
  assert.equal(byId.get('#toneMixValue').textContent,'40%');
  assert.equal(stage.dataset.mode,'color');
} else assert.equal(stage.style['--tone-opacity'],undefined);
assert.equal(byId.get('#selectedScore').scrolled,undefined,'Inline score selection must not scroll the full-height embedded report away');
assert.ok(byId.get('#heroLayout').children.includes(byId.get('#darkroomDock')), 'Feedback rail shares the photo workspace');
assert.ok(byId.get('#dockScores').children.includes(byId.get('#selectedScore')), 'Score reason stays with its chart');
assert.ok(byId.get('#dockScores').children.includes(byId.get('#scoreDetails')), 'All eight reasons remain available');
assert.equal(byId.get('#scoreSection').hidden,true,'Moved scores must not leave an empty full-width section');
assert.equal(byId.get('#darkroomDock').dataset.state,data.color_asset?'color':data.treatment_asset?'combined':'advice');
if(!hasAdjustment) assert.equal(byId.get('#dockEditStatus').textContent,data.edit.tone_color,'Without an edit image, show useful advice rather than a blank column');
console.log('PASS: darkroom asset gating, fit/zoom geometry, tone strength, optional learning, photo-note toggles/bounds, guides, themes, versions, comparison, downloads, regions, clipboard and interval radar. DOM logic only; real export/layout checked in browser.');
