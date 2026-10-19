// The project home is a static showcase. It does not upload photos or call AI.
const versions = {
  source: {label: '原图', note: '弯道、大小和远近的关系已经清楚。先保留它，不用一上来就重新构图。', alt: '原图：从近处车头向远处弯曲延伸的列车'},
  color: {label: '仅调色', note: '先让车头多露一点细节，再收一点旁边的亮绿。完整保留原图取景和内容。', alt: '仅调色版：弯道上的列车，车头暗部略微提亮，外围绿叶颜色收敛'},
  treatment: {label: '裁切＋调色', note: '沿用同一调色，只另外去掉顶部和右侧少量环境。裁切的收益与损失要单独判断。', alt: '裁切加调色版：同一列车照片，顶部和右侧少量环境被裁去'}
};
document.querySelector('#sampleControls').hidden = false;
document.querySelectorAll('[data-version]').forEach(button => button.addEventListener('click', () => {
  const version = button.dataset.version;
  const selected = versions[version];
  if (!selected) return;
  document.querySelector('#sampleImage').src = `demo/assets/${version}-preview.jpg`;
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
const preferredTheme = () => matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
const refreshThemeLabel = () => {
  const isDark = (document.documentElement.dataset.theme || preferredTheme()) === 'dark';
  themeButton.textContent = isDark ? '☀' : '☾';
  themeButton.setAttribute('aria-label', isDark ? '切换为浅色主题' : '切换为深色主题');
};
themeButton.addEventListener('click', () => {
  document.documentElement.dataset.theme = (document.documentElement.dataset.theme || preferredTheme()) === 'dark' ? 'light' : 'dark';
  refreshThemeLabel();
});
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', refreshThemeLabel);
refreshThemeLabel();
