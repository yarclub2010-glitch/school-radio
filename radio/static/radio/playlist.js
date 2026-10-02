// Прослушивание плейлиста на своём устройстве: один общий плеер внизу страницы.
const items = [...document.querySelectorAll('.track')];
const audio = document.getElementById('audio');
const player = document.getElementById('player');
const toggle = document.getElementById('toggle');
let index = -1;

function play(i) {
  if (i < 0 || i >= items.length) return;
  items.forEach((el) => el.classList.remove('playing'));
  index = i;
  const el = items[i];
  el.classList.add('playing');
  audio.src = el.dataset.src;
  audio.play();
  document.getElementById('p-title').textContent = el.dataset.title;
  document.getElementById('p-artist').textContent = el.dataset.artist;
  player.hidden = false;
}

items.forEach((el, i) => el.querySelector('.play').addEventListener('click', () => {
  if (i === index) { audio.paused ? audio.play() : audio.pause(); } else play(i);
}));

audio.addEventListener('ended', () => play(index + 1));
audio.addEventListener('play', () => { toggle.textContent = '⏸'; items[index]?.querySelector('.play').replaceChildren('⏸'); });
audio.addEventListener('pause', () => { toggle.textContent = '▶'; items[index]?.querySelector('.play').replaceChildren('▶'); });
audio.addEventListener('emptied', () => items.forEach((el) => el.querySelector('.play').replaceChildren('▶')));
toggle.addEventListener('click', () => (audio.paused ? audio.play() : audio.pause()));
document.getElementById('prev').addEventListener('click', () => play(Math.max(0, index - 1)));
document.getElementById('next').addEventListener('click', () => play(index + 1));
