#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import re
import urllib.request
from pathlib import Path


ZEN_FONT_URL = "https://fonts.gstatic.com/s/zenantique/v14/AYCPpXPnd91Ma_Zf-Ri2JXJq.ttf"


def b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def ensure_zen_font(cache_dir: Path) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    font_path = cache_dir / "ZenAntique400.ttf"
    if not font_path.exists():
        urllib.request.urlretrieve(ZEN_FONT_URL, font_path)
    return font_path


def build_font_css(src_fonts_dir: Path, zen_ttf: Path) -> str:
    arial_woff2 = b64(src_fonts_dir / "arial-rounded-mt/Arial-Rounded-MT.woff2")
    arial_woff = b64(src_fonts_dir / "arial-rounded-mt/Arial-Rounded-MT.woff")
    true_woff2 = b64(src_fonts_dir / "true-lcd-nge/true-lcd-nge.woff2")
    true_woff = b64(src_fonts_dir / "true-lcd-nge/true-lcd-nge.woff")
    seg_woff = b64(src_fonts_dir / "7segment/7segment.woff")
    zen_b64 = b64(zen_ttf)

    return f"""/* Embedded original fonts for EVA timer */
@font-face {{
    font-family: ArialRoundedMT;
    src:
        url("data:font/woff2;base64,{arial_woff2}") format("woff2"),
        url("data:font/woff;base64,{arial_woff}") format("woff");
    font-display: swap;
}}

@font-face {{
    font-family: TrueLCDNGE;
    src:
        url("data:font/woff2;base64,{true_woff2}") format("woff2"),
        url("data:font/woff;base64,{true_woff}") format("woff");
    font-display: swap;
}}

@font-face {{
    font-family: SevenSegment;
    src: url("data:font/woff;base64,{seg_woff}") format("woff");
    font-display: swap;
}}

@font-face {{
    font-family: "Zen Antique";
    src: url("data:font/ttf;base64,{zen_b64}") format("truetype");
    font-display: swap;
}}

@font-face {{
    font-family: ZenAntique-Regular;
    src: url("data:font/ttf;base64,{zen_b64}") format("truetype");
    font-display: swap;
}}
"""


def build_js(assets_json: str) -> str:
    js = r"""
const ASSETS = __ASSETS__;

const MODE_COUNT_DOWN = 0;
const MODE_COUNT_UP = 1;
const MODE_SYSTEM_TIME = 2;

const STATUS = {
  STANDBY: 'STANDBY',
  RACING: 'RACING',
  EMERGENCY: 'EMERGENCY',
  ENDED: 'ENDED',
  SYSTEMTIME: 'SYSTEMTIME'
};

const SEL = {
  BACKGROUND: "#pan-background",
  PANEL_TIMER: "#pan-clock",
  PANEL_POWER: "#pan-power",
  ALL_TEXT: "text",
  ALL_BORDERS: "path[id*=border], rect[id*=border]",
  ALL_DOT_GREEN: "#dot-green line",
  ALL_DOT_BLACK: "#dot-black line",
  ALL_DOT_AMBER: "#dot-amber line",
  ALL_DOT_POWER: "#pan-power [id^=dot]",
  ALL_RECTS: "rect",
  ALL_LINES: "line",
  ALL_PATHS: "path",
  ALL_CLICKABLES: "[id^=clickable-]",
  ALL_HELP_TEXTS: "[id^=help-]",
  BORDER_STOP: "#border-stop",
  BORDER_SLOW: "#border-slow",
  BORDER_NORMAL: "#border-normal",
  BORDER_RACING: "#border-racing",
  BORDER_EMERGENCY: "#border-emergency",
  BUTTON_POWER_INTERNAL: "#pan-internal",
  BUTTON_POWER_EXTERNAL: "#pan-external",
  BUTTON_STOP: "#pan-stop",
  BUTTON_SLOW: "#pan-slow",
  BUTTON_NORMAL: "#pan-normal",
  BUTTON_RACING: "#pan-racing",
  BUTTON_EMERGENCY: "#pan-emergency",
  FILL_STOP: "#bkg-stop",
  FILL_SLOW: "#bkg-slow",
  FILL_NORMAL: "#bkg-normal",
  FILL_RACING: "#bkg-racing",
  FILL_EMERGENCY: "#bkg-emergency",
  DOT_EMERGENCY: "#dot-emergency1, #dot-emergency2",
  BAR_STOP: "#bar-stop",
  BAR_SLOW: "#bar-slow",
  BAR_NORMAL: "#bar-normal",
  BAR_RACING: "#bar-racing",
  TEXT_STOP: "#text-stop",
  TEXT_SLOW: "#text-slow",
  TEXT_NORMAL: "#text-normal",
  TEXT_RACING: "#text-racing",
  TEXTGROUP_ACTIVE_TIME: "#textgroup-active-time",
  STRIP_INTERNAL: "#strip-internal",
  STRIP_EXTERNAL: "#strip-external",
  CLICKABLE_TOP: "#clickable-top",
  CLICKABLE_LEFT: "#clickable-left",
  CLICKABLE_BOTTOM: "#clickable-bottom",
  TEXTGROUP_TIMER: "#textgroup-clock",
  TEXTGROUP_SYSTEM_TIMER: "#textgroup-clock-sys",
  TEXT_SYSTEM_TIMER_MIN_SEC: "#text-min-sec-sys",
  TEXT_SYSTEM_TIMER_CENTISEC: "#text-millis-sys",
  TEXT_MIN_SEC: "#text-min-sec",
  TEXT_CENTISEC: "#text-millis",
  TEXT_TIMER: "#text-min-sec, #text-millis, #text-min-sec-sys, #text-millis-sys"
};

const STY = {
  BLINK: 'blink',
  BREATH: 'breath',
  BLINK_FAST: 'blink-fast',
  VIEW_FLATTENED: 'view-flattened',
  VIEW_TILTED: 'view-tilted'
};

const params = new URLSearchParams(location.search);
const config = {
  mode: Number(params.get('mode') ?? 0),
  autoplay: Boolean(Number(params.get('autoplay') ?? 0)),
  tilted: Boolean(Number(params.get('tilted') ?? 1)),
  fullscreen: Boolean(Number(params.get('fullscreen') ?? 0)),
  theme: params.get('theme') || 'default',
  duration: Number(params.get('duration') ?? 300),
  emergency_duration: Number(params.get('emergency_duration') ?? 60),
};

const parent = document.getElementById('parent');
const timerHost = document.getElementById('timer');
const settingsHost = document.getElementById('settings');

function updateTiltScale() {
  const baseW = 2133;
  const baseH = 1106;
  const rect = timerHost.getBoundingClientRect();
  const width = rect.width || window.innerWidth;
  const height = rect.height || window.innerHeight;
  const scale = Math.min(width / baseW, height / baseH);
  document.documentElement.style.setProperty('--eva-tilt-scale', String(Math.max(scale, 0.2)));
}

timerHost.innerHTML = ASSETS.svg;
settingsHost.innerHTML = `
  <div id="popup-bg" class="popup-background">
    <div class="popup-foreground" onclick="event.stopPropagation()" style="width: 80%; height: 80%;">
      <div id="popup-fg">${ASSETS.settings}</div>
    </div>
  </div>
`;

const popupBg = settingsHost.querySelector('#popup-bg');
popupBg.addEventListener('click', () => hideSettings());
updateTiltScale();
window.addEventListener('resize', updateTiltScale);
if (window.ResizeObserver) {
  const tiltObserver = new ResizeObserver(() => updateTiltScale());
  tiltObserver.observe(parent);
  tiltObserver.observe(timerHost);
}

function q(root, selectors) {
  if (Array.isArray(selectors)) return Array.from(root.querySelectorAll(selectors.join(',')));
  return Array.from(root.querySelectorAll(selectors));
}
function addClass(selectors, cls) { q(timerHost, selectors).forEach(e => e.classList.add(cls)); }
function removeClass(selectors, cls) { q(timerHost, selectors).forEach(e => e.classList.remove(cls)); }
function toggleClass(selectors, cls) { q(timerHost, selectors).forEach(e => e.classList.toggle(cls)); }
function show(selectors) { q(timerHost, selectors).forEach(e => { e.style.visibility='visible'; e.style.opacity='1'; }); }
function hide(selectors) { q(timerHost, selectors).forEach(e => { e.style.visibility='hidden'; e.style.opacity='0'; }); }
function allColor(selectors, c) { q(timerHost, selectors).forEach(e => { e.style.fill = c; e.style.stroke = c; }); }
function fillColor(selectors, c) { q(timerHost, selectors).forEach(e => { e.style.fill = c; }); }
function strokeColor(selectors, c) { q(timerHost, selectors).forEach(e => { e.style.stroke = c; }); }
function resetStyle(selectors) { q(timerHost, selectors).forEach(e => e.removeAttribute('style')); }
function textContent(selectors, txt) { q(timerHost, selectors).forEach(e => e.textContent = txt); }
function fontFamily(selectors, ff) { q(timerHost, selectors).forEach(e => e.style.fontFamily = ff); }
function fontSize(selectors, fs) { q(timerHost, selectors).forEach(e => e.style.fontSize = fs); }
function opacity(selectors, op) { q(timerHost, selectors).forEach(e => e.style.opacity = op); }

function blinkShowHide(shows, hides) {
  q(timerHost, shows).forEach(e => e.classList.add('blink-show'));
  q(timerHost, hides).forEach(e => e.classList.add('blink-hide'));
  setTimeout(() => {
    q(timerHost, shows).forEach(e => { e.classList.remove('blink-show'); e.style.visibility='visible'; e.style.opacity='1'; });
    q(timerHost, hides).forEach(e => { e.classList.remove('blink-hide'); e.style.visibility='hidden'; e.style.opacity='0'; });
  }, 500);
}

function showSettings(){ popupBg.style.visibility='visible'; popupBg.style.opacity='1'; }
function hideSettings(){ popupBg.style.visibility='hidden'; popupBg.style.opacity='0'; }
function toggleSettings(){ (popupBg.style.visibility === 'visible') ? hideSettings() : showSettings(); }

class Timer {
  constructor(interval, duration, emergencyDuration, mode, statusCb, renderCb, configCb) {
    this.STOPWATCH_INTERVAL = interval;
    this.SYSTEM_TIME_INTERVAL = 0.5;
    this.interval = interval;
    this.duration = duration;
    this.emergency_duration = Math.min(emergencyDuration, duration);
    this.mode = mode;
    this.status_callback = statusCb;
    this.render_callback = renderCb;
    this.config_callback = configCb;
    this.remaining_time = duration;
    this.running = false;
    this.elapsed_time = 0;
    this.previous_status = null;
    this.previous_running = null;
    this._raf = null;
    this._last = null;
  }
  update() {
    let newStatus;
    if (this.mode === MODE_SYSTEM_TIME) {
      newStatus = STATUS.SYSTEMTIME;
      this.render_callback(null);
    } else {
      this.remaining_time = this.duration - this.elapsed_time;
      if (this.remaining_time <= 0) {
        newStatus = STATUS.ENDED;
        this.remaining_time = 0;
        this.previous_running = this.running;
        this.running = false;
      } else if (this.remaining_time <= this.emergency_duration) {
        newStatus = STATUS.EMERGENCY;
      } else if (this.remaining_time === this.duration) {
        newStatus = STATUS.STANDBY;
      } else {
        newStatus = STATUS.RACING;
      }
      const displayTime = this.mode === MODE_COUNT_UP ? this.elapsed_time : this.remaining_time;
      this.render_callback(displayTime);
    }
    if (this.previous_status !== newStatus || this.previous_running !== this.running) {
      this.status_callback(this.previous_status, newStatus, this.previous_running, this.running);
    }
    this.previous_status = newStatus;
    this.previous_running = this.running;
  }
  _loop = (ts) => {
    if (!this.running) return;
    if (this._last == null) this._last = ts;
    const dt = (ts - this._last) / 1000;
    this._last = ts;
    this.elapsed_time += dt;
    this.update();
    this._raf = requestAnimationFrame(this._loop);
  }
  play() {
    if (this.running) return;
    this.previous_running = this.running;
    this.running = true;
    this._last = null;
    this._raf = requestAnimationFrame(this._loop);
  }
  pause() {
    this.previous_running = this.running;
    this.running = false;
    if (this._raf) cancelAnimationFrame(this._raf);
    this.update();
  }
  time_is_up(){ return this.remaining_time <= 0; }
  toggle_play_pause(){ this.running ? this.pause() : this.play(); }
  reset(){
    this.previous_running = this.running;
    this.running = false;
    if (this._raf) cancelAnimationFrame(this._raf);
    const nothing_to_reset = this.elapsed_time <= 0 || this.mode === MODE_SYSTEM_TIME;
    this.elapsed_time = 0;
    this.update();
    return !nothing_to_reset;
  }
  toggle_mode(){ this.set_mode(this.mode + 1); }
  toggle_mode_count_updown(){ this.mode !== MODE_COUNT_DOWN ? this.set_mode(MODE_COUNT_DOWN) : this.set_mode(MODE_COUNT_UP); }
  set_mode(mode){
    this.mode = ((mode % 3) + 3) % 3;
    if (this.mode === MODE_SYSTEM_TIME) this.play();
    else this.pause();
    this.update();
    this.config_callback?.();
  }
  adjust_elapsed_time(seconds){ this.elapsed_time += seconds; this.update(); }
  parse_mmss(text){
    try {
      const [m, s] = text.split(':').map(x => Number(x));
      const mm = Math.max(0, Math.min(59, m));
      const ss = Math.max(0, Math.min(59, s));
      return mm * 60 + ss;
    } catch { return null; }
  }
  format_mmss(seconds){
    const ss = Math.floor(seconds % 60);
    const mm = Math.floor((seconds - ss) / 60);
    return `${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}`;
  }
  parse_duration(text){ const i = this.parse_mmss(text); if (i != null) { this.duration = i; this.update(); this.config_callback?.(); }}
  parse_emergency_duration(text){ const i = this.parse_mmss(text); if (i != null) { this.emergency_duration = Math.min(this.duration, i); this.update(); this.config_callback?.(); }}
  format_duration(){ return this.format_mmss(this.duration); }
  format_emergency_duration(){ return this.format_mmss(this.emergency_duration); }
}

let theme = 'default';
let default_color_gradient = null;
let timer = null;

function render_callback(time) {
  let minutes, seconds, centiseconds;
  if (time == null) {
    const now = new Date();
    minutes = now.getHours();
    seconds = now.getMinutes();
    centiseconds = now.getSeconds();
  } else {
    minutes = Math.floor((time % 3600) / 60);
    seconds = Math.floor(time % 60);
    centiseconds = Math.floor((time % 1) * 100);
  }
  if (minutes < 10) {
    show(SEL.TEXTGROUP_TIMER); hide(SEL.TEXTGROUP_SYSTEM_TIMER);
    textContent(SEL.TEXT_MIN_SEC, `${minutes}:${String(seconds).padStart(2,'0')}`);
    textContent(SEL.TEXT_CENTISEC, `:${String(centiseconds).padStart(2,'0')}`);
  } else {
    hide(SEL.TEXTGROUP_TIMER); show(SEL.TEXTGROUP_SYSTEM_TIMER);
    textContent(SEL.TEXT_SYSTEM_TIMER_MIN_SEC, `${String(minutes).padStart(2,'0')}:${String(seconds).padStart(2,'0')}`);
    textContent(SEL.TEXT_SYSTEM_TIMER_CENTISEC, `:${String(centiseconds).padStart(2,'0')}`);
  }
}

function status_callback(_f, to_status, _fr, to_running) {
  switch (to_status) {
    case STATUS.STANDBY: show_standby(); break;
    case STATUS.RACING: show_racing(); break;
    case STATUS.EMERGENCY: show_emergency(); break;
    case STATUS.ENDED: show_ended(); break;
    case STATUS.SYSTEMTIME: show_system_time(); break;
  }
  if (!to_running && to_status !== STATUS.ENDED) {
    addClass(SEL.BAR_STOP, STY.BREATH); show(SEL.BAR_STOP); addClass(SEL.TEXTGROUP_TIMER, STY.BREATH);
  } else {
    removeClass(SEL.BAR_STOP, STY.BREATH); hide(SEL.BAR_STOP); removeClass(SEL.TEXTGROUP_TIMER, STY.BREATH);
  }
}

function config_callback() {
  const s = settingsHost;
  s.querySelector('#countdown').checked = timer.mode === MODE_COUNT_DOWN;
  s.querySelector('#countup').checked = timer.mode === MODE_COUNT_UP;
  s.querySelector('#systemtime').checked = timer.mode === MODE_SYSTEM_TIME;
  s.querySelector('#autoplay').checked = config.autoplay === 1 || config.autoplay === true;
  s.querySelector('#tiltedview').checked = !timerHost.classList.contains(STY.VIEW_FLATTENED);
  s.querySelector('#fullscreen').checked = !!document.fullscreenElement;
  s.querySelector('#wireframe').checked = false;
  s.querySelector('#greyscale').checked = false;
  s.querySelector('#rebuild').checked = (theme === 'rebuild');
  s.querySelector('#duration').value = timer.format_duration();
  s.querySelector('#emergency_duration').value = timer.format_emergency_duration();
}

function show_standby() {
  addClass(SEL.TEXTGROUP_TIMER, STY.BREATH);
  resetStyle([SEL.ALL_TEXT, SEL.ALL_DOT_GREEN, SEL.DOT_EMERGENCY, SEL.ALL_BORDERS]);
  removeClass([SEL.STRIP_INTERNAL, SEL.BAR_RACING], STY.BLINK_FAST);
  removeClass([SEL.BUTTON_EMERGENCY, SEL.TEXTGROUP_ACTIVE_TIME], STY.BLINK);
  show([SEL.BUTTON_EMERGENCY, SEL.BUTTON_POWER_EXTERNAL, SEL.BUTTON_POWER_INTERNAL, SEL.BAR_STOP, SEL.BAR_SLOW, SEL.BAR_NORMAL, SEL.BAR_RACING, SEL.TEXT_STOP, SEL.TEXT_SLOW, SEL.TEXT_NORMAL, SEL.TEXT_RACING, SEL.BORDER_STOP, SEL.BORDER_SLOW, SEL.BORDER_NORMAL, SEL.BORDER_RACING, SEL.BUTTON_EMERGENCY, SEL.STRIP_EXTERNAL, SEL.STRIP_INTERNAL]);
  if (theme === 'rebuild') apply_rebuild_theme(); else remove_rebuild_theme();
}
function show_racing() {
  hide([SEL.BAR_STOP, SEL.BAR_SLOW, SEL.BAR_NORMAL, SEL.BUTTON_EMERGENCY, SEL.BUTTON_POWER_EXTERNAL]);
  blinkShowHide([SEL.BUTTON_POWER_INTERNAL, SEL.STRIP_INTERNAL, SEL.BAR_RACING], [SEL.BUTTON_POWER_EXTERNAL, SEL.STRIP_EXTERNAL, SEL.BAR_NORMAL, SEL.BUTTON_EMERGENCY]);
}
function show_emergency() {
  allColor([SEL.ALL_TEXT, SEL.ALL_DOT_GREEN, SEL.DOT_EMERGENCY], 'red');
  strokeColor(SEL.ALL_BORDERS, 'red');
  show(SEL.BUTTON_EMERGENCY);
  hide([SEL.BUTTON_POWER_EXTERNAL, SEL.BAR_STOP, SEL.BAR_SLOW, SEL.BAR_NORMAL, SEL.BAR_RACING]);
  blinkShowHide([SEL.BUTTON_EMERGENCY], [SEL.BAR_RACING]);
}
function show_ended() {
  toggleClass([SEL.STRIP_INTERNAL, SEL.BAR_RACING], STY.BLINK_FAST);
  toggleClass([SEL.BUTTON_EMERGENCY, SEL.TEXTGROUP_ACTIVE_TIME], STY.BLINK);
  show(SEL.BAR_RACING);
  hide([SEL.BUTTON_POWER_EXTERNAL, SEL.BAR_STOP, SEL.BAR_SLOW, SEL.BAR_NORMAL, SEL.TEXT_SLOW, SEL.TEXT_NORMAL, SEL.TEXT_RACING, SEL.BORDER_SLOW, SEL.BORDER_NORMAL, SEL.BORDER_RACING]);
}
function show_system_time() {
  removeClass(SEL.TEXTGROUP_TIMER, STY.BREATH);
  blinkShowHide([SEL.BUTTON_POWER_EXTERNAL, SEL.STRIP_EXTERNAL, SEL.BAR_NORMAL, SEL.BUTTON_EMERGENCY], [SEL.BUTTON_POWER_INTERNAL, SEL.STRIP_INTERNAL, SEL.BAR_RACING, SEL.BAR_STOP, SEL.BAR_SLOW]);
}
function toggle_wireframe() {
  toggleClass([SEL.ALL_LINES, SEL.ALL_RECTS, SEL.ALL_PATHS], 'wireframe');
  toggleClass(SEL.ALL_CLICKABLES, 'wireframe');
  toggleClass(SEL.ALL_TEXT, 'opacity70');
  toggleClass(SEL.ALL_TEXT, 'wireframe');
  toggleClass(SEL.TEXT_TIMER, 'wireframe-bold');
  hide(SEL.ALL_HELP_TEXTS);
}
function toggle_greyscale(){ toggle_wireframe(); toggleClass(SEL.TEXT_TIMER, 'greyscale'); toggleClass(SEL.TEXT_TIMER, 'wireframe-bold'); }
function toggle_rebuild_theme(){ if (theme === 'rebuild') { theme = 'default'; remove_rebuild_theme(); } else { theme = 'rebuild'; apply_rebuild_theme(); }}
function remove_rebuild_theme() {
  if (default_color_gradient != null) q(timerHost, '#linear-gradient').forEach(e => e.innerHTML = default_color_gradient);
  resetStyle([SEL.TEXT_TIMER, SEL.ALL_TEXT, SEL.ALL_DOT_GREEN, SEL.ALL_DOT_BLACK, SEL.ALL_DOT_AMBER, SEL.ALL_DOT_POWER, SEL.FILL_STOP, SEL.FILL_SLOW, SEL.FILL_NORMAL, SEL.FILL_RACING, SEL.FILL_EMERGENCY, SEL.BORDER_STOP, SEL.BORDER_SLOW, SEL.BORDER_NORMAL, SEL.BORDER_RACING, SEL.BORDER_EMERGENCY, SEL.ALL_BORDERS, '#border-external', '#border-internal', '#border-system']);
}
function apply_rebuild_theme() {
  const MODE_BUTTON_COLOR = 'rgb(52,71,103)';
  const POWER_BUTTON_COLOR = 'rgb(78,108,178)';
  const TEXT_COLOR = 'rgb(220,231,242)';
  const REBUILD_RED = 'Crimson';
  const cg = q(timerHost, '#linear-gradient')[0];
  if (cg) {
    if (default_color_gradient == null) default_color_gradient = cg.innerHTML;
    cg.innerHTML = '<stop offset="0" stop-color="Tomato"></stop><stop offset=".5" stop-color="Orchid"></stop><stop offset=".85" stop-color="rgb(51,50,200)"></stop><stop offset="1" stop-color="Blue"></stop>';
  }
  allColor('#bar-purple', POWER_BUTTON_COLOR);
  allColor(SEL.ALL_TEXT, TEXT_COLOR);
  allColor(SEL.ALL_DOT_AMBER, 'MediumSlateBlue');
  allColor(SEL.ALL_DOT_POWER, 'Orchid');
  allColor([SEL.ALL_DOT_GREEN, SEL.ALL_DOT_BLACK], 'MintCream'); opacity([SEL.ALL_DOT_GREEN, SEL.ALL_DOT_BLACK], 0.6);
  allColor([SEL.FILL_STOP, SEL.FILL_SLOW, SEL.FILL_NORMAL, SEL.FILL_RACING], MODE_BUTTON_COLOR); opacity([SEL.FILL_STOP, SEL.FILL_SLOW, SEL.FILL_NORMAL, SEL.FILL_RACING], 0.45);
  fillColor(SEL.FILL_EMERGENCY, MODE_BUTTON_COLOR);
  strokeColor([SEL.BORDER_STOP, SEL.BORDER_SLOW, SEL.BORDER_NORMAL, SEL.BORDER_RACING, SEL.BORDER_EMERGENCY], 'MidNightBlue'); opacity([SEL.BORDER_STOP, SEL.BORDER_SLOW, SEL.BORDER_NORMAL, SEL.BORDER_RACING, SEL.BORDER_EMERGENCY], 0.45);
  hide(SEL.ALL_BORDERS);
  show(['#border-external', '#border-internal', '#border-system']);
  allColor(['#border-external', '#border-internal', '#border-system'], POWER_BUTTON_COLOR);
  fontFamily(SEL.TEXT_TIMER, 'SevenSegment'); allColor(SEL.TEXT_TIMER, REBUILD_RED);
  fontSize(SEL.TEXT_MIN_SEC, '3700%'); fontSize(SEL.TEXT_CENTISEC, '2600%'); fontSize(SEL.TEXT_SYSTEM_TIMER_MIN_SEC, '3550%'); fontSize(SEL.TEXT_SYSTEM_TIMER_CENTISEC, '2200%');
}

function toggleFullscreen(){ if (!document.fullscreenElement) parent.requestFullscreen?.(); else document.exitFullscreen?.(); }

q(timerHost, SEL.PANEL_TIMER).forEach(e => e.addEventListener('click', () => (timer.time_is_up() ? timer.reset() : timer.toggle_play_pause())));
q(timerHost, SEL.PANEL_POWER).forEach(e => e.addEventListener('click', toggleSettings));
q(timerHost, SEL.CLICKABLE_TOP).forEach(e => e.addEventListener('click', () => timerHost.classList.toggle(STY.VIEW_FLATTENED)));
q(timerHost, SEL.CLICKABLE_LEFT).forEach(e => e.addEventListener('click', toggleFullscreen));
q(timerHost, SEL.BUTTON_NORMAL).forEach(e => e.addEventListener('click', () => { timer.reset(); timer.set_mode(MODE_SYSTEM_TIME); }));
q(timerHost, SEL.BUTTON_RACING).forEach(e => e.addEventListener('click', () => { timer.reset(); timer.toggle_mode_count_updown(); }));
q(timerHost, SEL.BUTTON_STOP).forEach(e => e.addEventListener('click', () => timer.reset()));
q(timerHost, SEL.BUTTON_SLOW).forEach(e => e.addEventListener('click', () => timer.toggle_play_pause()));
q(timerHost, SEL.CLICKABLE_BOTTOM).forEach(e => e.addEventListener('click', () => toggle_rebuild_theme()));

settingsHost.querySelector('#countdown').addEventListener('click', () => timer.set_mode(0));
settingsHost.querySelector('#countup').addEventListener('click', () => timer.set_mode(1));
settingsHost.querySelector('#systemtime').addEventListener('click', () => timer.set_mode(2));
settingsHost.querySelector('#tiltedview').addEventListener('click', () => timerHost.classList.toggle(STY.VIEW_FLATTENED));
settingsHost.querySelector('#fullscreen').addEventListener('click', toggleFullscreen);
settingsHost.querySelector('#wireframe').addEventListener('click', toggle_wireframe);
settingsHost.querySelector('#greyscale').addEventListener('click', toggle_greyscale);
settingsHost.querySelector('#rebuild').addEventListener('click', toggle_rebuild_theme);
settingsHost.querySelector('#ok').addEventListener('click', hideSettings);
settingsHost.querySelector('#duration').addEventListener('input', (e) => timer.parse_duration(e.target.value));
settingsHost.querySelector('#duration').addEventListener('focusout', () => settingsHost.querySelector('#duration').value = timer.format_duration());
settingsHost.querySelector('#emergency_duration').addEventListener('input', (e) => timer.parse_emergency_duration(e.target.value));
settingsHost.querySelector('#emergency_duration').addEventListener('focusout', () => settingsHost.querySelector('#emergency_duration').value = timer.format_emergency_duration());

document.addEventListener('keydown', (event) => {
  switch (event.code) {
    case 'Space': event.preventDefault(); timer.toggle_play_pause(); break;
    case 'KeyR': timer.reset() || timer.toggle_mode(); break;
    case 'KeyP': timerHost.classList.toggle(STY.VIEW_FLATTENED); break;
    case 'KeyF': toggleFullscreen(); break;
    case 'KeyS': toggleSettings(); break;
    case 'KeyW': toggle_wireframe(); break;
    case 'KeyG': toggle_greyscale(); break;
    case 'KeyT': toggle_rebuild_theme(); break;
    case 'ArrowUp': event.preventDefault(); timer.adjust_elapsed_time(-1); break;
    case 'ArrowDown': event.preventDefault(); timer.adjust_elapsed_time(+1); break;
    case 'Escape': hideSettings(); if (document.fullscreenElement) document.exitFullscreen?.(); break;
  }
});

timer = new Timer(35/1000, config.duration, config.emergency_duration, config.mode, status_callback, render_callback, config_callback);
timer.reset();
config_callback();
timerHost.classList.add(STY.VIEW_TILTED);
if (config.autoplay) timer.play();
if (!config.tilted) timerHost.classList.toggle(STY.VIEW_FLATTENED);
if (config.fullscreen) setTimeout(() => parent.requestFullscreen?.(), 120);
if (config.theme === 'wireframe') toggle_wireframe();
else if (config.theme === 'greyscale') toggle_greyscale();
else if (config.theme === 'rebuild') toggle_rebuild_theme();
"""
    return js.replace("__ASSETS__", assets_json)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build offline single-file EVA timer HTML")
    default_repo = Path(__file__).resolve().parent
    default_out = default_repo / "dist" / "eva-timer.html"
    parser.add_argument("--repo", default=str(default_repo), help="Path to eva-timer repo")
    parser.add_argument("--out", default=str(default_out), help="Output HTML path")
    args = parser.parse_args()

    repo = Path(args.repo)
    src = repo / "src"
    src_fonts = src / "fonts"
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    zen_font = ensure_zen_font(repo / ".build-cache")
    font_css = build_font_css(src_fonts, zen_font)
    svgui_css = (src / "svgui.css").read_text(encoding="utf-8")
    eva_css = (src / "eva-timer.css").read_text(encoding="utf-8")
    settings_html = (src / "settings.html").read_text(encoding="utf-8")
    svg = (src / "images/eva-timer.svg").read_text(encoding="utf-8")

    assets_json = json.dumps({"svg": svg, "settings": settings_html}, ensure_ascii=False)
    js = build_js(assets_json)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>活動限界まであと (Offline Single HTML)</title>
  <style>{font_css}</style>
  <style>{svgui_css}</style>
  <style>{eva_css}</style>
  <style>
:root {{
    --eva-tilt-scale: 1;
}}

.view-tilted {{
    -webkit-transform:
        perspective(calc(1237px * var(--eva-tilt-scale)))
        translate(calc(-341px * var(--eva-tilt-scale)), calc(171px * var(--eva-tilt-scale)))
        rotateX(-6deg) rotateZ(-18deg) rotateY(-36deg);
    transform:
        perspective(calc(1237px * var(--eva-tilt-scale)))
        translate(calc(-341px * var(--eva-tilt-scale)), calc(171px * var(--eva-tilt-scale)))
        rotateX(-6deg) rotateZ(-18deg) rotateY(-36deg);
}}

.view-flattened {{
    -webkit-transform: none !important;
    transform: none !important;
}}

html, body, #parent {{
  width: 100%;
  height: 100%;
  margin: 0;
  background-color: black;
  overflow: hidden;
}}
#timer {{
  width: 100%;
  height: 100%;
  transform-origin: 50% 50%;
  transition: transform 0.5s ease;
  will-change: transform;
}}
#timer > svg {{
  width: 100%;
  height: 100%;
  display: block;
}}
  </style>
</head>
<body>
  <div id="parent">
    <div id="timer"></div>
    <div id="settings"></div>
  </div>
  <script>{js}</script>
</body>
</html>
"""

    out.write_text(html, encoding="utf-8")
    print(f"Generated: {out}")
    print(f"Size: {out.stat().st_size} bytes")


if __name__ == "__main__":
    main()
