const cases = {
  station: {
    src: "../photography-benchmark/pilot-12/originals/p03-union-station-light.jpg",
    alt: "芝加哥联合车站候车厅，斜向光束落在巨大室内空间和小人物上",
    genre: "示范样本 · 建筑 / 人文",
    attribution: "Jack Delano，1943 · 公共领域 ↗",
    source: "https://commons.wikimedia.org/wiki/File:Chicago_Union_Station_1943_v2.jpg",
    confidence: "这次判断比较有把握",
    reading: "我第一眼会顺着左上方的光，一路看到地面亮处的两个人。人很小，但一点没丢；周围留出的大空间，反而让车站显得更有气势。",
    strengthTitle: "人不用拍得很大，也能稳稳接住整张照片",
    strength: "两个人刚好站在光落下来的位置，地面的线条也朝他们汇过去。右边还有一群等车的人，把车站的尺度托起来，却没有抢走视线。",
    decisionTag: "这张先别急着改",
    decisionName: "画面已经站住了",
    decisionTitle: "不用为了得到建议，硬从一张好照片里挑毛病",
    decision: "光把人带出来，人物又把空间托住，这个来回已经很完整。这里没有一处非改不可的错误，下面只能算一次小实验。",
    runnerLabel: "真要挑一处呢？",
    runner: "左下角的标牌会轻轻拉一下视线，但它没有打断光和人物的关系，留着也说得通。",
    actionKicker: "如果还想多拍一张",
    actionTitle: "机位别动，只等中间两个人稍微分开",
    availability: "要等机会",
    action: "构图和曝光都先不动，看看两个人之间会不会出现一条小缝，再按一张。",
    effect: "照片缩小时，两个人的轮廓会更容易辨认。",
    cost: "你也可能因此错过现在这组姿态，甚至错过这束光；新拍的未必比这一张好。",
    postCan: "可以试着从左边轻轻裁掉一点，再比较标牌是否安静下来。",
    postCannot: "别把上方暗处裁掉太多，那正是空间感的来源；已经白掉的细节，也不能保证靠后期找回来。",
    evidence: [
      ["先看左上到中间：", "几束斜光都落向地面亮处，眼睛很自然地跟过去。"],
      ["再看正中间：", "两个人正站在光和地面线条交会的地方，轮廓没有粘在一起。"],
      ["右边的人群：", "他们让空间显得更大，但明度和位置都没有盖过中间。"],
      ["所以我不建议大改：", "最重要的人、光和空间已经连成一条线，左下角那点干扰不足以拆散它。"],
    ],
    scores: [
      ["画面是否看得清", "3–4 / 5", "60%", "80%"],
      ["视线有没有落点", "4–5 / 5", "80%", "100%"],
      ["光和颜色是否帮忙", "4–5 / 5", "80%", "100%"],
      ["人物与空间的关系", "4–5 / 5", "80%", "100%"],
      ["有没有值得多看一眼", "4–5 / 5", "80%", "100%"],
      ["整张照片是否说到一起", "4–5 / 5", "80%", "100%"],
    ],
    boundaries: [
      ["我能看到：", "光往哪里落、人站在哪里，以及标牌和空间的明暗。"],
      ["我由此判断：", "多数人的视线可能会顺着斜光走到中间那两个人。"],
      ["单凭照片不知道：", "人物是谁、为什么拍、用了什么参数，也不知道底片高光里还剩多少细节。"],
    ],
    practiceTime: "找半小时，至少拍 20 张",
    practiceTitle: "别追着人跑，先守住一块好光",
    practice: "找一个有明显方向光的室内，把机位定住。只等人物走进光里、彼此分开的瞬间；这半小时里只改变按快门的时机。",
    passRule: "最后留 3 张。你应该能只看人物的位置，就说清楚为什么同一束光拍出了三种不同感觉。",
    reference: {
      src: "../photography-benchmark/ordinary-12-v0.2/images/N03-tokyo-white-collar.jpg",
      alt: "东京地下通道中的小人物站在暗空间的亮区里",
      label: "看一个相近的处理 · CC BY 2.0",
      title: "地点完全不同，但也是让一个小人物接住一大片空间",
      text: "先别管黑白风格，只看暗处、亮处和人站的位置。参考图不是标准答案，只是在示范同一种画面关系。",
      href: "https://commons.wikimedia.org/wiki/File:White_collar_-_Tokyo,_Japan_-_Black_and_white_street_photography_(39970316051).jpg",
      linkText: "Giuseppe Milo，2018 · CC BY 2.0 ↗",
    },
    direction: {
      title: "再去看看 Fan Ho 怎样等一个人走进光里",
      text: "重点看人物站在哪里，空间就怎样发生变化。先别急着模仿黑白、烟雾和复古城市的样子。",
      href: "https://fanho-forgetmenot.com/",
      linkText: "访问摄影师官方网站 ↗",
    },
  },
  dance: {
    src: "../photography-benchmark/pilot-12/originals/p06-jitterbugging-clarksdale.jpg",
    alt: "黑白舞厅照片，多名舞者在拥挤空间中举起手臂并相互连接",
    genre: "示范样本 · 纪实 / 群像",
    attribution: "Marion Post Wolcott，1939 · 公共领域 ↗",
    source: "https://commons.wikimedia.org/wiki/File:Jitterbugging_in_juke_joint,_Clarksdale,_Mississippi_Delta_8c11034v.jpg",
    confidence: "这次判断大体有把握",
    reading: "这张照片最先给我的不是某一个人的表情，而是一屋子人正在一起跳舞的热气。手臂、身体和目光挤在一起，乱，却不是散。",
    strengthTitle: "这些重叠没有毁掉画面，反而让舞池真的热起来了",
    strength: "左边的人往里靠，中间几只举起的手搭成一道弧线，右边握在一起的手又把视线兜回来。你拍到的是一群人的关系，不只是几张脸。",
    decisionTag: "这里没有唯一答案",
    decisionName: "先想清楚你更舍不得什么",
    decisionTitle: "要热闹，还是要一个清楚的主角？两种拍法都可以",
    decision: "如果你最舍不得现场的拥挤和热度，就让人物继续重叠；如果你真正想讲的是中间那位舞者，就多等半秒，让脸从手臂后面露出来。",
    runnerLabel: "为什么我不替你选？",
    runner: "把人分得更开，画面会清楚，却也可能一下变得没那么热闹。这里改变的不是好坏，而是照片在讲谁。",
    actionKicker: "下次先做一个小选择",
    actionTitle: "同一个位置拍两组：一组看人群，一组等一个人",
    availability: "遇到相似场景时",
    action: "第一组允许人物重叠，只等几只手能把大家连起来；第二组往旁边挪半步，等中间那张脸不再被手臂挡住。",
    effect: "第一组会更像集体狂欢，第二组会让一个舞者真正成为主角。",
    cost: "选热闹，就会少一点表情；选主角，就要放掉一部分拥挤和偶然。",
    postCan: "可以轻轻提亮中间的脸和手，再把后墙压暗一点，让关系更容易看见。",
    postCannot: "别用很重的锐化去追眼睛细节。原来没记录下来的东西不会回来，还容易把动作的柔边弄出一圈假轮廓。",
    evidence: [
      ["先看左边：", "几个人的身体和手臂都朝中间挤，力量是往里走的。"],
      ["再看中间：", "举起来的手搭出一道弧线，但戴帽子的脸也被这些动作切开了。"],
      ["右边为什么没散：", "那双握在一起的手，把已经走到边缘的视线又拉了回来。"],
      ["所以会有两种拍法：", "人群关系和中间那个人都值得留；把任何一边清理得太干净，都会损失另一边。"],
    ],
    scores: [
      ["画面是否看得清", "3–4 / 5", "60%", "80%"],
      ["视线有没有落点", "3–4 / 5", "60%", "80%"],
      ["光和颜色是否帮忙", "3–4 / 5", "60%", "80%"],
      ["人物彼此有没有关系", "4–5 / 5", "80%", "100%"],
      ["有没有值得多看一眼", "4–5 / 5", "80%", "100%"],
      ["整张照片是否说到一起", "4–5 / 5", "80%", "100%"],
    ],
    boundaries: [
      ["我能看到：", "身体往哪里动、手臂是什么形状、人物怎样重叠，以及黑白里的明暗。"],
      ["我由此判断：", "重叠让现场更热，也让单个人物更难被看清。"],
      ["单凭照片不知道：", "你最想突出谁、这些人是什么关系，也不能确定柔和边缘究竟来自运动、镜头还是扫描。"],
    ],
    practiceTime: "拍半小时，最后只选 2 张",
    practiceTitle: "把“看得最清楚”和“关系最有趣”分开选一次",
    practice: "去拍一次多人活动。按快门前只多看一眼脸和手有没有粘住；结束后，一张选最清楚的，一张选人物关系最有意思的。",
    passRule: "你要能各指出画面里的两个位置，解释它们为什么入选，而不只是说哪张“更有感觉”。",
    reference: {
      src: "../photography-benchmark/ordinary-12-v0.2/references/R06-jitterbug-crowd.jpg",
      alt: "1938 年舞池中的多组舞者和周围观众",
      label: "看一个相近的处理 · 公共领域",
      title: "人多的时候，不必让每张脸都露出来",
      text: "看看几组舞者的手臂、腿和旁边观众怎样被串在一起。重点不是把所有人排整齐，而是让重叠有理由。",
      href: "https://commons.wikimedia.org/wiki/File:Jitterbug_dancers_NYWTS.jpg",
      linkText: "Alan Fisher，1938 · 公共领域 ↗",
    },
    direction: {
      title: "再去看看 Garry Winogrand 怎样把边缘人物也留在故事里",
      text: "重点看拥挤街景里的人和手势怎样互相回应。先别模仿倾斜、粗颗粒和广角变形这些表面特征。",
      href: "https://www.moma.org/artists/6399",
      linkText: "访问 MoMA 摄影师页面 ↗",
    },
  },
  ferry: {
    src: "../photography-benchmark/pilot-12/originals/p12-amsterdam-ferry-2025.jpg",
    alt: "灰天的渡轮码头，人群从船上离开，前景有行人和固定设施",
    genre: "示范样本 · 街头 / 纪实",
    attribution: "Fons Heijnsbroek，2025 · CC0 1.0 ↗",
    source: "https://commons.wikimedia.org/wiki/File:2025_-_free_download_CC0_photo_Amsterdam_-_people_are_leaving_the_ferry_boat_near_IJ_river_on_a_grey_day_-_street_photography_in_free_image_by_Fons_Heijnsbroek,_Netherlands.tif",
    confidence: "这次判断比较有把握",
    reading: "我先看到渡轮和迎面下来的人，接着视线却被正中央的柱子和垃圾桶拦住了。你拍到了下船的忙乱感，只是这股人流还没在画面里连起来。",
    strengthTitle: "左边的人往外走，船上的人迎面涌来——现场是动的",
    strength: "这两股相反的人流很重要。它让人感觉到“船刚靠岸”，而不是只看到一艘停着的渡轮。这个瞬间你抓到了。",
    decisionTag: "先改这一处",
    decisionName: "让人流连起来",
    decisionTitle: "可惜正中间这根柱子，比人更抢眼",
    decision: "柱子把船口和左边行人从中间劈开，下面的垃圾桶又占了一块最显眼的位置。结果是人明明很多，第一眼却不知道该跟着谁走。",
    runnerLabel: "灰天不是最要紧的。",
    runner: "灰色反而符合通勤的日常感。先把人物关系理顺，比加颜色更有用。",
    actionKicker: "如果我在你旁边，我会这样提醒",
    actionTitle: "先别急着按，往右挪两三步",
    availability: "遇到相似场景时",
    action: "让柱子避开船口，再等一个近处的人走进左边空处时按下快门。",
    effect: "近处的人离开、远处的人涌来，两层动作能一口气读出来。",
    cost: "船身可能拍不全，码头设施也会少一些；但这张照片真正有意思的是人流，不是船的全貌。",
    postCan: "把柱子和垃圾桶稍微压暗一点，让它们别那么跳。",
    postCannot: "压暗只能减轻干扰，没法把被柱子隔开的两股人流重新接上。",
    evidence: [
      ["看正中间：", "柱子从上贯到底，刚好挡在船口人群前面。"],
      ["再看下面：", "垃圾桶又大又完整，比远处的人更容易先被看见。"],
      ["最后看左边：", "近处的人向左走，和船口迎面下来的人本来可以形成很好的一来一往。"],
      ["换句话说：", "问题不是画面里东西多，而是最显眼的东西没有帮你讲“人群下船”这件事。"],
    ],
    scores: [
      ["画面是否看得清", "3–4 / 5", "60%", "80%"],
      ["视线有没有落点", "2–3 / 5", "40%", "60%"],
      ["光和颜色是否帮忙", "3–4 / 5", "60%", "80%"],
      ["人物与物件的关系", "2–3 / 5", "40%", "60%"],
      ["有没有值得多看一眼", "3–4 / 5", "60%", "80%"],
      ["整张照片是否说到一起", "2–3 / 5", "40%", "60%"],
    ],
    boundaries: [
      ["我能看到：", "人物站在哪里、往哪儿走，以及谁挡住了谁。"],
      ["我由此判断：", "大多数人可能会先注意到柱子和垃圾桶，再去找人群。"],
      ["单凭照片不知道：", "你当时为什么拍、能不能换位置，也不知道你用了什么器材和参数。"],
    ],
    practiceTime: "找半小时，拍 20 张",
    practiceTitle: "去拍一次“一近一远”",
    practice: "找一个车站、路口或出入口，先站到柱子不会挡人的位置。每张都同时留一个近处的人和一组远处的人；机位别动，只等不同的时机。",
    passRule: "把照片缩小。如果你还能一眼看出近处和远处的人各自往哪里走，这张就留下。",
    reference: {
      src: "../photography-benchmark/ordinary-12-v0.2/references/R01-station-stairs.jpg",
      alt: "阿姆斯特丹中央车站楼梯，近景与远景行人沿不同方向移动",
      label: "看一个相近的处理 · CC0 1.0",
      title: "这里也有柱子，但人流没有被截断",
      text: "不用模仿地点和颜色，只看近处、远处的人怎么同时留在画面里。障碍物不必全清掉，关键是它有没有挡住最重要的动作。",
      href: "https://commons.wikimedia.org/wiki/File:Free_photo_of_people,_entering_and_leaving_Central_station_Amsterdam_on_the_outdoor_staircases_with_in_the_background_the_city_center_and_the_street_Prins_Hendrikkade;_-_street_photography_by_Fons_Heijnsbroek,_2026_-_free_image.tif",
      linkText: "Fons Heijnsbroek，2026 · CC0 1.0 ↗",
    },
    direction: {
      title: "可以去看 Joel Meyerowitz 怎么处理复杂街景",
      text: "看的时候先别学色调，只问一件事：画面里每一层为什么要留下？边缘的人又是怎么和中间发生关系的？",
      href: "https://www.joelmeyerowitz.com/street-photography",
      linkText: "访问摄影师官方页面 ↗",
    },
  },
};

const coachPrompt = `请使用 $photography-coach 分析我随本条消息附上的这一张照片。

要求：
1. 先盲读，不要求我提前解释为什么按下快门；
2. 像一位坐在我旁边看片的摄影老师那样说话：直接、具体、有判断，但不要报告腔和术语堆砌；
3. 先告诉我这张照片已经拍到的东西，再用画面里的具体位置指出最值得改的一件事；
4. 给一个我下次站在现场真能做到的动作，并说明这样会得到什么、又会失去什么；
5. 区分后期能做与不能做；
6. 给一个 20–40 分钟、拍完能自己选片的练习；
7. 如提供图例，只展示许可可核验的开放图片；名家作品否则只给官方链接；
8. 六维只给区间，不给综合总分；专业判断可以放在展开内容里，不要让分类标签打断第一屏的阅读。

先完成第一遍反馈，最后再问我是否愿意补充用途或拍摄意图。`;

const photoInput = document.querySelector("#photo-input");
const uploadButton = document.querySelector("#upload-button");
const photoPreview = document.querySelector("#photo-preview");
const photoCaption = document.querySelector("#photo-caption");
const resetButton = document.querySelector("#reset-button");
const caseButtons = [...document.querySelectorAll(".case-switcher button")];
const tabs = [...document.querySelectorAll(".tab")];
const tabPanels = [...document.querySelectorAll(".tab-panel")];
const feedbackTabs = document.querySelector("#feedback-tabs");
const analysisContent = document.querySelector("#analysis-content");
const customState = document.querySelector("#custom-state");
const copyButton = document.querySelector("#copy-prompt");
const copyStatus = document.querySelector("#copy-status");
const promptPreview = document.querySelector("#prompt-preview");
const contextButton = document.querySelector("#context-button");
const contextNote = document.querySelector("#context-note");
const zoomButton = document.querySelector("#zoom-button");
const imageDialog = document.querySelector("#image-dialog");
const dialogImage = document.querySelector("#dialog-image");
const dialogClose = document.querySelector("#dialog-close");
const feedbackHeading = document.querySelector("#feedback-heading");
const confidence = document.querySelector(".confidence");

let objectUrl = null;
let currentCase = "ferry";

promptPreview.textContent = coachPrompt;

function updateCaption(data) {
  photoCaption.replaceChildren();
  const label = document.createElement("span");
  label.textContent = data.genre;
  const link = document.createElement("a");
  link.href = data.source;
  link.target = "_blank";
  link.rel = "noreferrer";
  link.textContent = data.attribution;
  photoCaption.append(label, link);
}

function renderEvidence(items) {
  const list = document.querySelector(".evidence-ledger ol");
  list.replaceChildren();
  items.forEach(([label, body]) => {
    const item = document.createElement("li");
    const strong = document.createElement("strong");
    strong.textContent = label;
    item.append(strong, document.createTextNode(body));
    list.append(item);
  });
}

function renderBoundaries(items) {
  const card = document.querySelector(".boundary-card");
  card.querySelectorAll(":scope > p").forEach((item) => item.remove());
  items.forEach(([label, body]) => {
    const paragraph = document.createElement("p");
    const strong = document.createElement("strong");
    strong.textContent = label;
    paragraph.append(strong, document.createTextNode(body));
    card.append(paragraph);
  });
}

function renderCase(caseId) {
  const data = cases[caseId];
  currentCase = caseId;
  photoPreview.src = data.src;
  photoPreview.alt = data.alt;
  updateCaption(data);

  caseButtons.forEach((button) => {
    const selected = button.dataset.case === caseId;
    button.classList.toggle("is-active", selected);
    button.setAttribute("aria-pressed", String(selected));
  });

  feedbackHeading.textContent = "这一次，只说最值得留意的一件事";
  confidence.textContent = data.confidence;
  document.querySelector(".reading-card p").textContent = data.reading;
  document.querySelector(".strength-card h3").textContent = data.strengthTitle;
  document.querySelector(".strength-card p").textContent = data.strength;

  const decisionLabels = document.querySelectorAll(".decision-label span");
  decisionLabels[0].textContent = data.decisionTag;
  decisionLabels[1].textContent = data.decisionName;
  document.querySelector(".decision-card h3").textContent = data.decisionTitle;
  document.querySelector(".decision-card > p:not(.runner-up)").textContent = data.decision;
  const runnerUp = document.querySelector(".runner-up");
  runnerUp.replaceChildren();
  const runnerLabel = document.createElement("strong");
  runnerLabel.textContent = data.runnerLabel;
  runnerUp.append(runnerLabel, document.createTextNode(` ${data.runner}`));

  document.querySelector(".action-card > .eyebrow").textContent = data.actionKicker;
  document.querySelector(".action-card h3").textContent = data.actionTitle;
  document.querySelector(".availability").textContent = data.availability;
  const actionDetails = document.querySelectorAll(".action-card dd");
  [data.action, data.effect, data.cost].forEach((value, index) => {
    actionDetails[index].textContent = value;
  });
  const postText = document.querySelectorAll(".post-card p");
  postText[0].textContent = data.postCan;
  postText[1].textContent = data.postCannot;

  renderEvidence(data.evidence);
  const scoreRows = document.querySelectorAll(".score-row");
  data.scores.forEach(([name, interval, from, to], index) => {
    const labels = scoreRows[index].querySelectorAll("span");
    labels[0].textContent = name;
    labels[1].textContent = interval;
    const bar = scoreRows[index].querySelector("i");
    bar.style.setProperty("--from", from);
    bar.style.setProperty("--to", to);
  });
  renderBoundaries(data.boundaries);

  document.querySelector(".practice-card > .eyebrow").textContent = data.practiceTime;
  document.querySelector(".practice-card > h3").textContent = data.practiceTitle;
  document.querySelector(".practice-card > p:not(.eyebrow)").textContent = data.practice;
  document.querySelector(".pass-rule p").textContent = data.passRule;

  const referenceImage = document.querySelector(".reference-card img");
  referenceImage.src = data.reference.src;
  referenceImage.alt = data.reference.alt;
  document.querySelector(".reference-card .eyebrow").textContent = data.reference.label;
  document.querySelector(".reference-card h3").textContent = data.reference.title;
  document.querySelector(".reference-card p:not(.eyebrow)").textContent = data.reference.text;
  const referenceLink = document.querySelector(".reference-card a");
  referenceLink.href = data.reference.href;
  referenceLink.textContent = data.reference.linkText;

  document.querySelector(".direction-card h3").textContent = data.direction.title;
  document.querySelector(".direction-card p:not(.eyebrow)").textContent = data.direction.text;
  const directionLink = document.querySelector(".direction-card a");
  directionLink.href = data.direction.href;
  directionLink.textContent = data.direction.linkText;
}

function showDemo() {
  if (objectUrl) {
    URL.revokeObjectURL(objectUrl);
    objectUrl = null;
  }
  photoInput.value = "";
  resetButton.hidden = true;
  feedbackTabs.hidden = false;
  customState.hidden = true;
  analysisContent.hidden = false;
  renderCase(currentCase);
}

caseButtons.forEach((button) => {
  button.addEventListener("click", () => {
    currentCase = button.dataset.case;
    showDemo();
  });
});

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    const target = tab.dataset.tab;
    tabs.forEach((item) => {
      const selected = item === tab;
      item.classList.toggle("is-active", selected);
      item.setAttribute("aria-selected", String(selected));
      item.tabIndex = selected ? 0 : -1;
    });
    tabPanels.forEach((panel) => {
      panel.hidden = panel.dataset.panel !== target;
    });
  });
});

feedbackTabs.addEventListener("keydown", (event) => {
  if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
  event.preventDefault();
  const current = tabs.indexOf(document.activeElement);
  let next = current;
  if (event.key === "ArrowLeft") next = (current - 1 + tabs.length) % tabs.length;
  if (event.key === "ArrowRight") next = (current + 1) % tabs.length;
  if (event.key === "Home") next = 0;
  if (event.key === "End") next = tabs.length - 1;
  tabs[next].focus();
  tabs[next].click();
});

uploadButton.addEventListener("click", () => photoInput.click());

photoInput.addEventListener("change", () => {
  const [file] = photoInput.files;
  if (!file) return;

  if (objectUrl) URL.revokeObjectURL(objectUrl);
  objectUrl = URL.createObjectURL(file);
  photoPreview.src = objectUrl;
  photoPreview.alt = `用户选择的照片：${file.name}`;
  photoCaption.replaceChildren();

  const label = document.createElement("span");
  label.textContent = `本地预览 · ${file.name}`;
  const notice = document.createElement("span");
  notice.textContent = "尚未分析";
  photoCaption.append(label, notice);

  caseButtons.forEach((button) => {
    button.classList.remove("is-active");
    button.setAttribute("aria-pressed", "false");
  });
  resetButton.hidden = false;
  feedbackTabs.hidden = true;
  analysisContent.hidden = true;
  customState.hidden = false;
  feedbackHeading.textContent = "把照片发给摄影教练";
  confidence.textContent = "还没有看片";
  copyStatus.textContent = "";
});

resetButton.addEventListener("click", showDemo);

async function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.append(textarea);
  textarea.select();
  const copied = document.execCommand("copy");
  textarea.remove();
  if (!copied) throw new Error("copy failed");
}

copyButton.addEventListener("click", async () => {
  try {
    await copyText(coachPrompt);
    copyStatus.textContent = "复制好了。把照片发到 Codex，再粘贴这段话就行。";
    copyButton.textContent = "已复制";
    window.setTimeout(() => {
      copyButton.textContent = "复制看片请求";
    }, 1800);
  } catch {
    copyStatus.textContent = "浏览器没能自动复制。请展开下面的文字，手动复制一下。";
  }
});

contextButton.addEventListener("click", () => {
  contextNote.hidden = !contextNote.hidden;
  contextButton.textContent = contextNote.hidden ? "我想说说当时为什么拍" : "先收起来";
});

zoomButton.addEventListener("click", () => {
  dialogImage.src = photoPreview.src;
  dialogImage.alt = photoPreview.alt;
  imageDialog.showModal();
});

dialogClose.addEventListener("click", () => imageDialog.close());

imageDialog.addEventListener("click", (event) => {
  if (event.target === imageDialog) imageDialog.close();
});

renderCase(currentCase);
