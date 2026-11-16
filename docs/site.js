// The project home is a static showcase. It does not upload photos or call AI.
const versions = {
  workbench: {src: 'images/workbench-browser.jpg', label: '工作台', note: '左侧看完整照片，右侧看建议和评分理由。公开案例无需密钥即可查看。', alt: '暗房工作台实际截图：左侧为完整骑行街拍，右侧为建议、八维评分和具体理由'},
  annotation: {src: 'images/report-annotation-browser.jpg', label: '图上点评', note: '在照片上点击标记，展开对应位置的具体分析；再次点击或按 Escape 收起。', alt: '真实报告截图：照片上的标记展开点评说明，并用连线指向讨论位置'},
  scores: {src: 'images/report-scores-browser.jpg', label: '八维评分', note: '点击雷达图维度查看理由。区间反映判断的不确定性，面积不代表总分。', alt: '真实报告截图：八维区间雷达图和当前维度的评分依据'}
};
document.querySelector('#sampleControls').hidden = false;
document.querySelectorAll('[data-version]').forEach(button => button.addEventListener('click', () => {
  const version = button.dataset.version;
  const selected = versions[version];
  if (!selected) return;
  document.querySelector('#sampleImage').src = selected.src;
  document.querySelector('#sampleImage').alt = selected.alt;
  document.querySelector('#sampleVersion').textContent = selected.label;
  document.querySelector('#sampleNote').textContent = selected.note;
  document.querySelectorAll('[data-version]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
}));
document.querySelectorAll('[data-copy]').forEach(button => {
  button.hidden = false;
  button.addEventListener('click', async () => {
    const value = document.getElementById(button.dataset.copy).textContent;
    const fallback = document.querySelector('#copyFallback');
    const status = document.querySelector('#copyStatus');
    fallback.hidden = true;
    try {
      await navigator.clipboard.writeText(value);
      status.textContent = '已复制。可以粘贴到终端或 Codex。';
    } catch {
      fallback.value = value;
      fallback.hidden = false;
      fallback.focus();
      fallback.select();
      status.textContent = '自动复制不可用，请手动复制下面选中的文字。';
    }
  });
});
const themeButton = document.querySelector('#themeToggle');
themeButton.hidden = false;
const preferredTheme = () => 'dark';
const refreshThemeLabel = () => {
  const isDark = (document.documentElement.dataset.theme || preferredTheme()) === 'dark';
  themeButton.textContent = isDark ? '浅色' : '深色';
  themeButton.setAttribute('aria-label', isDark ? '切换为浅色主题' : '切换为深色主题');
};
themeButton.addEventListener('click', () => {
  document.documentElement.dataset.theme = (document.documentElement.dataset.theme || preferredTheme()) === 'dark' ? 'light' : 'dark';
  refreshThemeLabel();
});
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', refreshThemeLabel);
refreshThemeLabel();
