'use strict';
// Local API only. No API keys, images or answers are stored in browser storage.
const $ = id => document.getElementById(id);
let token = '', config = {configured: false}, selected = null, demo = false, busy = null;
let acting = false, uploading = false, timer = null, historySignature = '', messageSignature = '';
let reportObserver = null;
const states = {uploaded:'待点评',running:'处理中',ready:'已保存',error:'处理失败',cancelled:'已停止等待',interrupted:'处理中断'};
const requestId = () => crypto.randomUUID().replaceAll('-', '');
const text = (id, value) => $(id).textContent = value || '';
function notice(message) { text('notice', message); $('notice').hidden = !message; }
async function api(path, options = {}) {
  const response = await fetch(path, {cache:'no-store', ...options, headers:{'X-Workbench-Token':token, ...options.headers}});
  const value = await response.json();
  if (!response.ok) throw new Error(value.error || '本机服务未能完成请求。');
  return value;
}
const post = (path, value) => api(path, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(value)});
function selectionUrl() {
  history.replaceState(null, '', demo ? '/?demo=1' : selected ? '/?photo=' + selected.id : '/');
}
function configureView() {
  text('connectModel', config.configured ? '模型已配置' : '连接模型');
  text('connectionState', config.configured ? config.model : '尚未连接模型');
  const destination = config.configured ? `${config.model}（${config.base_url}）` : '尚未配置的模型';
  text('consentText', `我确认将照片预览与补充文字发送至 ${destination}，并承担该服务的 API 费用。`);
  text('questionConsentText', `本次追问会向 ${destination} 再次发送预览、当前点评和近期对话，产生一次 API 调用费用。`);
  controls();
}
function controls() {
  $('startCritique').disabled = acting || uploading || !selected || !config.configured || !$('consent').checked || !!busy;
  $('askQuestion').disabled = acting || !selected || !config.configured || !$('questionConsent').checked || !!busy;
  $('makePreview').disabled = acting || !!busy;
  $('archivePhoto').disabled = acting || !!selected?.active;
  $('photoInput').disabled = uploading || !token;
  for (const id of ['jumpReference','jumpPractice']) $(id).disabled = !demo && !selected?.report_url;
}
function historyView(sessions) {
  const signature = JSON.stringify([sessions, selected?.id]);
  if (historySignature === signature) return;
  historySignature = signature;
  $('historyList').replaceChildren();
  text('sessionCount', String(sessions.length));
  $('emptyHistory').hidden = sessions.length > 0;
  for (const session of sessions) {
    const button = document.createElement('button');
    button.type = 'button'; button.className = 'history-item';
    button.setAttribute('aria-current', String(session.id === selected?.id));
    const image = document.createElement('img'); image.src = session.preview_url; image.alt = ''; image.loading = 'lazy';
    const label = document.createElement('span'), title = document.createElement('strong'), info = document.createElement('small');
    title.textContent = session.title;
    info.textContent = `${new Date(session.created * 1000).toLocaleDateString('zh-CN')} · ${states[session.state] || session.state}`;
    label.append(title, info); button.append(image, label);
    button.addEventListener('click', () => chooseSession(session.id));
    $('historyList').append(button);
  }
}
function applyFrameTheme() {
  document.documentElement.style.setProperty('--header-height', `${Math.ceil(document.querySelector('.topbar').getBoundingClientRect().height)}px`);
  const frame = $('reportFrame');
  if (frame.contentDocument?.documentElement) {
    frame.contentDocument.documentElement.dataset.theme = currentTheme();
    frame.contentDocument.documentElement.dataset.compact = String(window.innerHeight <= 800);
    frame.contentDocument.documentElement.style.setProperty('--workbench-stage-height',`${Math.max(360,Math.min(820,window.innerHeight-190))}px`);
  }
}
function fitReportFrame() {
  reportObserver?.disconnect();
  const frame = $('reportFrame'), body = frame.contentDocument?.body;
  if (!body) return;
  // Follow expanded observations/details without introducing a second scroll area.
  const fit = () => { frame.style.height = `${Math.ceil(body.getBoundingClientRect().height) + 2}px`; };
  reportObserver = new ResizeObserver(fit);
  reportObserver.observe(body);
  fit();
}
function showReport(url) {
  const embedded = url + '?embedded=1';
  if ($('reportFrame').getAttribute('src') !== embedded) $('reportFrame').src = embedded;
  $('reportFrame').hidden = false; $('openReport').href = url;
}
function resetFrame() { reportObserver?.disconnect(); $('reportFrame').removeAttribute('src'); $('reportFrame').hidden = true; }
function render() {
  document.body.dataset.demo = String(demo);
  const hasReport = !!selected?.report_url;
  document.body.dataset.view = demo || hasReport ? 'result' : 'upload';
  $('uploadView').hidden = demo || hasReport;
  $('resultView').hidden = !demo && !hasReport;
  $('taskPanel').hidden = !selected?.active || selected?.state !== 'running';
  if (!$('taskPanel').hidden) {
    text('taskTitle', {critique:'正在生成点评',question:'正在生成回复',preview:'正在本机生成试调版'}[selected.task] || '正在处理');
  }
  if (demo) {
    text('resultMode','公开案例'); text('resultTitle','迎面来的骑车人');
    text('resultBoundary','预先写好的示例点评 · 无需 API · 不产生费用');
    showReport('/demo-street/index.html');
  } else if (selected) {
    text('photoName',selected.name); text('photoSize',`${selected.width} × ${selected.height}`);
    $('emptyPhoto').hidden = true; $('photoPreview').hidden = false; $('photoPreview').src = selected.preview_url;
    text('chooseLabel','换一张照片 ↗');
    if (hasReport) {
      text('resultMode','点评记录 · 已保存在本机'); text('resultTitle',selected.name);
      text('resultBoundary','本次点评与 Skill 使用同一套摄影规则。工作台暂不提供实时参考作品检索。');
      showReport(selected.report_url);
      $('exportReport').href = `/export/${selected.id}.zip`;
      $('originalDownload').href = selected.original_url;
      const signature = JSON.stringify(selected.messages);
      if (signature !== messageSignature) {
        messageSignature = signature; $('messages').replaceChildren();
        for (const message of selected.messages) {
          const article=document.createElement('article'), question=document.createElement('h3'), answer=document.createElement('p'), boundary=document.createElement('small');
          question.textContent=message.question; answer.textContent=message.answer; boundary.textContent=message.boundary;
          article.append(question,answer,boundary); $('messages').append(article);
        }
      }
      const total = selected.usage.reduce((sum, item) => sum + (item.total_tokens || 0), 0);
      text('usage', total ? `服务已报告的累计用量：${total.toLocaleString()} tokens。不是费用报价；失败或中断的请求可能仍被计费。` : '实际费用以模型服务的账单为准。');
    } else resetFrame();
    if (selected.error) notice(selected.error);
  } else {
    $('emptyPhoto').hidden=false; $('photoPreview').hidden=true; $('photoPreview').removeAttribute('src');
    text('chooseLabel','选择照片 ↗'); text('photoName','JPG / PNG / WebP'); text('photoSize','小于 16 MB，最多 3000 万像素');
    resetFrame();
  }
  for (const id of ['exportReport','originalDownload','archivePhoto','conversation']) $(id).hidden = demo || !hasReport;
  $('trainDemo').hidden = true; // Legacy train case remains available by its documented URL, not in the main flow.
  $('makePreview').hidden = demo || !hasReport || !selected?.can_preview;
  $('previewBoundary').hidden = demo || !hasReport || !(selected.can_preview || selected.edited);
  controls();
}
async function refresh() {
  const state = await api('/api/state');
  if (config.revision !== state.config.revision) { $('consent').checked=false; $('questionConsent').checked=false; }
  token=state.token; config=state.config; busy=state.busy;
  if (selected) selected=await api('/api/sessions/'+selected.id);
  configureView(); historyView(state.sessions); render();
  clearTimeout(timer);
  if (busy) timer=setTimeout(() => refresh().catch(() => notice('本机连接中断。刷新后可恢复记录，不会自动重复调用模型。')),1500);
}
async function chooseSession(id) {
  if (acting || uploading) return;
  try {
    notice(''); selected=await api('/api/sessions/'+id); demo=false; $('context').value=selected.context || '';
    $('consent').checked=false; $('questionConsent').checked=false; $('question').value='';
    selectionUrl(); closeHistory(); await refresh();
  } catch(error) { notice(error.message); }
}
async function upload(file) {
  if (!file || uploading || acting || !token) return;
  if (file.size>16*1024*1024) return notice('照片需小于 16 MB；请先缩小或导出 JPG。');
  if (!['image/jpeg','image/png','image/webp'].includes(file.type)) return notice('暂时只接收 JPG、PNG 和 WebP，不支持 HEIC、RAW 或动画。');
  uploading=true; demo=false; selected=null; notice('正在保存到本机，尚未发送给模型。'); render();
  try {
    selected=await api('/api/photos',{method:'POST',headers:{'Content-Type':'application/octet-stream','X-Photo-Name':encodeURIComponent(file.name)},body:file});
    $('context').value=''; $('consent').checked=false; $('questionConsent').checked=false; $('question').value='';
    selectionUrl(); notice(''); await refresh();
  } catch(error) { notice(error.message); }
  finally { uploading=false; $('photoInput').value=''; controls(); }
}
async function runTask(task) {
  if (acting || !selected) return;
  acting=true; notice(''); controls();
  const payload={request_id:requestId(),config_revision:config.revision};
  if (task==='critique') Object.assign(payload,{context:$('context').value,consent:$('consent').checked});
  if (task==='question') Object.assign(payload,{question:$('question').value,consent:$('questionConsent').checked});
  try {
    selected=await post(`/api/sessions/${selected.id}/${task}`,payload);
    $('consent').checked=false; $('questionConsent').checked=false;
    await refresh();
  } catch(error) {
    notice(error.message);
    // Only re-read status after an uncertain POST. Never resubmit automatically.
    try { await refresh(); } catch { /* The error above remains visible. */ }
  } finally { acting=false; controls(); }
}
function openConfig() {
  $('baseUrl').value=config.base_url || 'https://api.openai.com/v1'; $('model').value=config.model || '';
  $('tokenLimit').value=config.max_output_tokens || 10000; $('apiKey').value=''; $('configError').hidden=true;
  $('configDialog').showModal();
}
$('photoInput').addEventListener('change',event=>upload(event.target.files[0]));
const drop=$('dropArea');
for(const event of ['dragenter','dragover']) drop.addEventListener(event,e=>{e.preventDefault(); drop.classList.add('dragging');});
for(const event of ['dragleave','drop']) drop.addEventListener(event,e=>{e.preventDefault(); drop.classList.remove('dragging');});
drop.addEventListener('drop',event=>upload(event.dataTransfer.files[0]));
$('critiqueForm').addEventListener('submit',event=>{event.preventDefault(); runTask('critique');});
$('questionForm').addEventListener('submit',event=>{event.preventDefault(); runTask('question');});
$('makePreview').addEventListener('click',()=>runTask('preview'));
for(const id of ['consent','questionConsent']) $(id).addEventListener('change',controls);
for(const id of ['connectModel','editConnection']) $(id).addEventListener('click',openConfig);
$('closeConfig').addEventListener('click',()=>$('configDialog').close());
$('configDialog').addEventListener('close',()=>$('apiKey').value='');
$('configForm').addEventListener('submit',async event=>{
  event.preventDefault(); $('saveConfig').disabled=true;
  try {
    config=await post('/api/config',{base_url:$('baseUrl').value,model:$('model').value,api_key:$('apiKey').value,max_output_tokens:Number($('tokenLimit').value)});
    $('apiKey').value=''; $('consent').checked=false; $('questionConsent').checked=false;
    $('configDialog').close(); notice('模型配置已保存到本次运行，还没有发起 API 调用。'); await refresh();
  } catch(error) { text('configError',error.message); $('configError').hidden=false; }
  finally { $('saveConfig').disabled=false; }
});
$('clearConfig').addEventListener('click',async()=>{
  try { await post('/api/config/clear',{}); $('apiKey').value=''; $('configDialog').close(); notice('已清除本次运行保存的密钥；已经发出的请求不受影响。'); await refresh(); }
  catch(error) { text('configError',error.message); $('configError').hidden=false; }
});
$('cancelTask').addEventListener('click',async()=>{
  if(!selected) return;
  try { selected=await post(`/api/sessions/${selected.id}/cancel`,{}); await refresh(); }
  catch(error) { notice(error.message); }
});
$('archivePhoto').addEventListener('click',async()=>{
  if(!selected || !confirm('把这条记录和照片移入本机回收区？它们可从数据目录的 trash 文件夹恢复，不会永久删除。')) return;
  try { const result=await post(`/api/sessions/${selected.id}/archive`,{}); selected=null; demo=false; selectionUrl(); notice(result.message); await refresh(); }
  catch(error) { notice(error.message); }
});
$('newPhoto').addEventListener('click',()=>{
  if(acting || uploading) return;
  demo=false; selected=null; $('context').value=''; $('consent').checked=false; selectionUrl(); notice(''); render(); refresh().catch(error=>notice(error.message));
});
for(const id of ['showDemo','tryDemo']) $(id).addEventListener('click',()=>{
  if(acting || uploading) return;
  selected=null; demo=true; selectionUrl(); notice(''); render(); refresh().catch(error=>notice(error.message));
});
const systemTheme=matchMedia('(prefers-color-scheme: dark)');
const currentTheme=()=>document.documentElement.dataset.theme || 'dark';
function refreshTheme() { const dark=currentTheme()==='dark'; text('themeToggle',dark?'浅色':'深色'); $('themeToggle').setAttribute('aria-label',dark?'切换为浅色主题':'切换为深色主题'); applyFrameTheme(); }
$('themeToggle').addEventListener('click',()=>{document.documentElement.dataset.theme=currentTheme()==='dark'?'light':'dark'; refreshTheme();});
systemTheme.addEventListener('change',refreshTheme);
window.addEventListener('resize',applyFrameTheme);
function closeHistory() { $('historySidebar').hidden=true; $('toggleHistory').setAttribute('aria-expanded','false'); }
$('toggleHistory').addEventListener('click',()=>{ const open=$('historySidebar').hidden; $('historySidebar').hidden=!open; $('toggleHistory').setAttribute('aria-expanded',String(open)); });
$('closeHistory').addEventListener('click',()=>{ closeHistory(); $('toggleHistory').focus(); });
document.addEventListener('keydown',event=>{ if(event.key==='Escape' && !$('historySidebar').hidden) { closeHistory(); $('toggleHistory').focus(); } });
function navigateReport(id) { const target=$('reportFrame').contentDocument?.getElementById(id); if(target) target.scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'}); }
$('workbenchHome').addEventListener('click',()=>window.scrollTo({top:0,behavior:'instant'}));
$('jumpReference').addEventListener('click',()=>navigateReport('referenceTitle'));
$('jumpPractice').addEventListener('click',()=>navigateReport('practiceTitle'));
$('reportFrame').addEventListener('load', () => { applyFrameTheme(); fitReportFrame(); });
refreshTheme();
(async()=>{
  try {
    const params=new URLSearchParams(location.search), photo=params.get('photo');
    if(photo && /^[a-f0-9]{32}$/.test(photo)) selected={id:photo};
    demo=params.get('demo')==='1' && !selected;
    await refresh();
    if(selected) $('context').value=selected.context || '';
  } catch(error) { selected=null; configureView(); render(); notice('无法载入本机工作台：'+error.message); }
})();
