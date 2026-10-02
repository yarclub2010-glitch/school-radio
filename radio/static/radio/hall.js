// Плеер актового зала: перемешивает одобренные треки и играет их только во время перемен.
const audio = document.getElementById('audio');
const $ = (id) => document.getElementById(id);
const csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;

let tracks = [];
let schedule = [];
let queue = [];
let current = null;
let clockOffset = 0;   // разница между часами сервера и этого компьютера, в секундах
let started = false;
let fading = false;

const toSecs = (hms) => { const [h, m, s] = hms.split(':').map(Number); return h * 3600 + m * 60 + (s || 0); };
const localSecs = () => { const d = new Date(); return d.getHours() * 3600 + d.getMinutes() * 60 + d.getSeconds(); };
const nowSecs = () => (localSecs() + clockOffset + 86400) % 86400;
const fmt = (secs) => {
  secs = Math.max(0, Math.round(secs));
  if (secs >= 3600) return `${Math.floor(secs / 3600)} ч ${Math.floor((secs % 3600) / 60)} мин`;
  return `${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, '0')}`;
};
const hhmm = (hms) => hms.slice(0, 5);

function post(url) {
  return fetch(url, { method: 'POST', headers: { 'X-CSRFToken': csrf } }).catch(() => {});
}

async function load() {
  const res = await fetch('/api/hall/');
  const data = await res.json();
  clockOffset = toSecs(data.server_time) - localSecs();
  const known = new Set(tracks.map((t) => t.id));
  const fresh = data.tracks.filter((t) => !known.has(t.id));
  const alive = new Set(data.tracks.map((t) => t.id));
  tracks = data.tracks;
  queue = queue.filter((t) => alive.has(t.id)).concat(shuffle(fresh)); // новые треки — в конец очереди
  schedule = data.schedule;
  renderSchedule();
}

function shuffle(list) {
  const a = [...list];
  for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; }
  return a;
}

function currentBreak() {
  if (!schedule.length) return { always: true };
  const now = nowSecs();
  return schedule.find((b) => toSecs(b.start) <= now && now < toSecs(b.end)) || null;
}

function nextBreak() {
  const now = nowSecs();
  return schedule.find((b) => toSecs(b.start) > now) || null;
}

function playNext() {
  if (!tracks.length) { setNowPlaying(null); return; }
  if (!queue.length) {
    queue = shuffle(tracks);
    if (current && queue.length > 1 && queue[0].id === current.id) queue.push(queue.shift()); // без повтора подряд
  }
  current = queue.shift();
  audio.src = current.url;
  audio.volume = Number($('vol').value);
  audio.play().catch(() => {});
  setNowPlaying(current);
  renderUpNext();
  post(`/api/hall/played/${current.id}/`);
}

function setNowPlaying(t) {
  $('np-title').textContent = t ? t.title : 'Нет одобренных треков';
  $('np-artist').textContent = t ? t.artist : 'Загрузите музыку и одобрите её в модерации';
  $('np-by').textContent = t ? `Прислал(а): ${t.by}` : '';
}

function renderUpNext() {
  $('up-next').textContent = queue.length ? `Далее: ${queue[0].artist} — ${queue[0].title}` : '';
}

function renderSchedule() {
  const now = nowSecs();
  $('schedule').innerHTML = schedule.map((b) => {
    const cls = toSecs(b.end) <= now ? 'past' : (toSecs(b.start) <= now ? 'active' : '');
    return `<li class="${cls}">${hhmm(b.start)}–${hhmm(b.end)} · ${b.name}</li>`;
  }).join('');
}

// Плавно убираем звук, когда перемена закончилась
function fadeOutAndPause() {
  if (fading) return;
  fading = true;
  const startVol = audio.volume;
  const step = setInterval(() => {
    audio.volume = Math.max(0, audio.volume - startVol / 20);
    if (audio.volume <= 0.001) {
      clearInterval(step);
      audio.pause();
      audio.volume = Number($('vol').value);
      fading = false;
      post('/api/hall/stopped/');
    }
  }, 150);
}

function tick() {
  if (!started) return;
  const brk = currentBreak();
  if (brk) {
    if (brk.always) $('status').textContent = 'Эфир идёт (расписание перемен не задано)';
    else $('status').textContent = `Перемена «${brk.name}» — до конца ${fmt(toSecs(brk.end) - nowSecs())}`;
    $('status').className = 'status live';
    if (audio.paused && !fading) {
      if (current && audio.currentTime > 0 && !audio.ended) audio.play().catch(() => {});
      else playNext();
    }
  } else {
    const nb = nextBreak();
    $('status').textContent = nb
      ? `Идёт урок. Следующая перемена в ${hhmm(nb.start)} (через ${fmt(toSecs(nb.start) - nowSecs())})`
      : 'Перемены на сегодня закончились';
    $('status').className = 'status';
    if (!audio.paused) fadeOutAndPause();
  }
  renderSchedule();
}

audio.addEventListener('ended', () => { if (currentBreak()) playNext(); });
audio.addEventListener('error', () => setTimeout(playNext, 1000)); // битый файл — пропускаем
audio.addEventListener('timeupdate', () => {
  $('bar').style.width = audio.duration ? `${(audio.currentTime / audio.duration) * 100}%` : '0';
});
$('vol').addEventListener('input', (e) => { if (!fading) audio.volume = Number(e.target.value); });
$('skip').addEventListener('click', playNext);

// Браузер не даёт включать звук без клика пользователя, поэтому эфир запускается кнопкой
$('start').addEventListener('click', async () => {
  started = true;
  $('start').hidden = true;
  $('skip').hidden = false;
  await load();
  tick();
});

load();
setInterval(tick, 1000);
setInterval(load, 60 * 1000);
