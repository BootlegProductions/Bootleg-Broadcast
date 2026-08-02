let schedule = null;
let currentChannel = 0;
let currentIndex = 0;

let channelMemory = {};
let retryState = {};
let advertPools = {};
let advertsPerBreak = 5;
let advertHistory = {};

const player = document.getElementById("player");
const channelName = document.getElementById("channelName");
const powerBtn = document.getElementById("power");
/* -------------------- Channel No. Overlay -------------------- */

const channelNumber = document.getElementById("channelNumber");
const channelNameOverlay = document.getElementById("channelNameOverlay");
const staticScreen = document.getElementById("static");
const channelOverlay = document.getElementById("channelOverlay");

const tvOnSound = new Audio("assets/tv on sfx/tv on sfx.mp3");
const tvOffSound = new Audio("assets/tv off sfx/tv off sfx.mp3");
const channelSwitchSound = new Audio("assets/static sfx/channel switch static.mp3");
const remoteButtonSound = new Audio("assets/remote button sfx/remote button sfx.mp3");

[tvOnSound, tvOffSound, channelSwitchSound, remoteButtonSound].forEach(sound => {
  sound.preload = "auto";
});

let started = false;

function playSound(sound, options = {}) {
  if (!sound) return;

  const volume = options.volume ?? 1;
  const duration = options.duration ?? null;

  sound.pause();
  sound.currentTime = 0;
  sound.volume = volume;

  sound.play().catch(() => {});

  if (duration) {
    setTimeout(() => {
      sound.pause();
      sound.currentTime = 0;
    }, duration);
  }
}
/* -------------------- Channel Logo Overlay -------------------- */

const channelBug = document.getElementById("channelBug");

function updateChannelBug(channelName) {
  if (!channelBug || !channelName) return;

  const logoMap = {
    "90s Toons": "assets/channel logos/90s Cartoons Logo.png",
    "Cartoons Cartoons": "assets/channel logos/Cartoons Cartoons Logo.png",
    "AAA": "assets/channel logos/AAA Logo.png",
    "Off-Licence TV": "assets/channel logos/Off Licence TV Logo.png",
    "Japanime": "assets/channel logos/Japanime Logo.png",
    "Star Spangled TV": "assets/channel logos/Star Spangled TV Logo.png",
    "What": "assets/channel logos/What Logo.png",
    "Dizzy": "assets/channel logos/Dizzy Logo.png",
    "Dickleodeon": "assets/channel logos/Dickleodeon Logo.png",
    "GirlyPop": "assets/channel logos/Girly Pop Logo.png"
  };

  const logo = logoMap[channelName];

  if (!logo) {
    channelBug.style.display = "none";
    return;
  }

  channelBug.src = logo;
  channelBug.style.display = "block";
}


/* -------------------- POWER BUTTON -------------------- */

powerBtn.addEventListener("click", () => {
  started = true;
  player.muted = false;

  playSound(tvOnSound);
  showChannelOverlay();

  if (player.src) {
    player.play().catch(() => {});
  }

  powerBtn.style.display = "none";
});


/* -------------------- LOAD SCHEDULE -------------------- */

const currentMonth = new Date()
  .toLocaleString("en-GB", { month: "long" })
  .toLowerCase();

function fetchJson(path) {
  return fetch(path, { cache: "no-store" }).then(res => {
    if (!res.ok) throw new Error(`Could not load ${path}`);
    return res.json();
  });
}

Promise.all([
  fetchJson(`schedules/${currentMonth}.json`).catch(err => {
    console.error("Monthly schedule failed to load:", err);
    return fetchJson("schedule.json").then(data => ({
      weeks: [{ week_number: 1, week: data.week }]
    }));
  }),
  fetchJson("adverts.json").catch(err => {
    console.error("Advert library failed to load:", err);
    return { channels: {}, adverts_per_break: 5 };
  })
]).then(([scheduleData, advertData]) => {
  schedule = scheduleData;
  advertPools = advertData.channels || {};
  advertsPerBreak = advertData.adverts_per_break || 5;

  expandTodayAdBreaks();
  console.log("Loaded month:", currentMonth);
  loadChannel();
}).catch(err => {
  console.error("Bootleg Broadcast failed to initialise:", err);
});


/* -------------------- HELPERS -------------------- */

function chooseAdverts(channelName, requestedCount) {
  const pool = advertPools[channelName] || [];
  if (!pool.length) return [];

  const count = Math.min(requestedCount || advertsPerBreak, pool.length);
  const history = advertHistory[channelName] || [];
  const recent = new Set(history.slice(-Math.min(25, pool.length)));

  let candidates = pool.filter(item => !recent.has(item.url));
  if (candidates.length < count) candidates = [...pool];

  // Fisher-Yates shuffle so each page load gets varied commercial breaks.
  for (let i = candidates.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [candidates[i], candidates[j]] = [candidates[j], candidates[i]];
  }

  const selected = candidates.slice(0, count).map(item => ({ ...item }));
  advertHistory[channelName] = [
    ...history,
    ...selected.map(item => item.url)
  ].slice(-50);

  return selected;
}

function expandTodayAdBreaks() {
  const today = getTodaySchedule();
  if (!today?.channels) return;

  today.channels.forEach(channel => {
    if (channel._advertBreaksExpanded) return;

    const expanded = [];
    (channel.playlist || []).forEach(item => {
      if (item.type === "AdBreak") {
        expanded.push(...chooseAdverts(channel.name, item.count || advertsPerBreak));
      } else {
        expanded.push(item);
      }
    });

    channel.playlist = expanded;
    channel._advertBreaksExpanded = true;
  });
}



function getTodaySchedule() {
  const todayDate = new Date().getDate();

  if (schedule?.weeks) {
    let count = 0;
    for (const weekBlock of schedule.weeks) {
      const weekDays = weekBlock.week || [];
      if (todayDate <= count + weekDays.length) {
        return weekDays[todayDate - count - 1] || null;
      }
      count += weekDays.length;
    }
  }

  if (schedule?.week) {
    const dayIndex = new Date().getDay();
    return schedule.week[dayIndex] || null;
  }

  return null;
}

function getCurrentChannelData() {
  const today = getTodaySchedule();
  if (!today || !today.channels || !today.channels.length) return null;

  const channel = today.channels[currentChannel];
  if (!channel || !channel.playlist || !channel.playlist.length) return null;

  return channel;
}

function getCurrentItem() {
  const channel = getCurrentChannelData();
  if (!channel) return null;
  return channel.playlist[currentIndex] || null;
}

function makeItemKey(item) {
  return item?.url || item?.title || `${currentChannel}:${currentIndex}`;
}

function setMemoryForCurrentItem(timeOverride) {
  const item = getCurrentItem();

  channelMemory[currentChannel] = {
    episodeIndex: currentIndex,
    time: typeof timeOverride === "number" ? timeOverride : (player.currentTime || 0),
    url: item?.url || "",
    title: item?.title || ""
  };
}

function saveChannelState() {
  setMemoryForCurrentItem();
}

function restoreChannelState() {
  if (channelMemory[currentChannel]) {
    currentIndex = channelMemory[currentChannel].episodeIndex || 0;
  } else {
    currentIndex = 0;
  }
}

function resetPlayer() {
  player.pause();
  player.removeAttribute("src");
  player.load();
}

/* -------------------- Channel Fade -------------------- */

function showChannelOverlay() {
  if (!channelOverlay) return;

  channelOverlay.style.opacity = 1;

  setTimeout(() => {
    channelOverlay.style.opacity = 0;
  }, 2000);
}

/* -------------------- CHANNEL LOADING -------------------- */

function loadChannel() {
  restoreChannelState();
  playCurrent();
}

function playCurrent() {
  const channel = getCurrentChannelData();
  if (!channel) return;

  if (currentIndex < 0 || currentIndex >= channel.playlist.length) {
    currentIndex = 0;
  }

  const item = channel.playlist[currentIndex];
  if (!item || !item.url) return;

  if (channelName) {
    channelName.textContent = channel.name;
  }

  if (channelNumber) {
    channelNumber.textContent = "CH " + String(currentChannel + 1).padStart(2, "0");
  }

  if (channelNameOverlay) {
    channelNameOverlay.textContent = channel.name;
  }
  
  updateChannelBug(channel.name);

  const itemKey = makeItemKey(item);

  player.onloadedmetadata = null;
  player.src = item.url;
  player.load();

  if (document.getElementById("scheduleOverlay")?.classList.contains("active")) {
    renderScheduleOverlay();
  }

  player.onloadedmetadata = () => {
    const memory = channelMemory[currentChannel];

    if (
      item.type !== "Ident" &&
      memory &&
      memory.episodeIndex === currentIndex &&
      memory.url === item.url
    ) {
      player.currentTime = memory.time || 0;
    } else {
      player.currentTime = 0;
    }

    retryState[itemKey] = 0;

    if (started) {
      player.play().catch(() => {});
    }
  };
}


/* -------------------- AUTO NEXT EPISODE -------------------- */

player.addEventListener("ended", () => {
  const channel = getCurrentChannelData();
  if (!channel) return;

  currentIndex++;

  if (currentIndex >= channel.playlist.length) {
    currentIndex = 0;
  }

  setMemoryForCurrentItem(0);
  playCurrent();
});

player.addEventListener("error", () => {
  const channel = getCurrentChannelData();
  if (!channel) return;

  const item = channel.playlist[currentIndex];
  if (!item) return;

  const itemKey = makeItemKey(item);
  const attempts = retryState[itemKey] || 0;

  console.error("Video failed to load:", item.title, item.url, "attempt", attempts + 1);

  if (attempts < 1) {
    retryState[itemKey] = attempts + 1;

    setTimeout(() => {
      player.load();
      if (started) {
        player.play().catch(() => {});
      }
    }, 900);

    return;
  }

  retryState[itemKey] = 0;

  currentIndex++;

  if (currentIndex >= channel.playlist.length) {
    currentIndex = 0;
  }

  setMemoryForCurrentItem(0);

  setTimeout(() => {
    playCurrent();
  }, 250);
});

/* -------------------- SHOW TV STATIC -------------------- */

function showStatic() {
  if (!staticScreen) return;

  staticScreen.style.opacity = 1;

  setTimeout(() => {
    staticScreen.style.opacity = 0;
  }, 350);
}

/* -------------------- CHANNEL SWITCHING -------------------- */

function nextChannel() {
  const today = getTodaySchedule();
  if (!today || !today.channels || !today.channels.length) return;

  saveChannelState();

  playSound(channelSwitchSound, {
  volume: 0.08,
  duration: 220
});
  showStatic();
  showChannelOverlay();

  currentChannel++;
  if (currentChannel >= today.channels.length) {
    currentChannel = 0;
  }

  resetPlayer();
  loadChannel();
}

function prevChannel() {
  const today = getTodaySchedule();
  if (!today || !today.channels || !today.channels.length) return;

  saveChannelState();

  playSound(channelSwitchSound, {
  volume: 0.08,
  duration: 220
});
  showStatic();
  showChannelOverlay();

  currentChannel--;
  if (currentChannel < 0) {
    currentChannel = today.channels.length - 1;
  }

  resetPlayer();
  loadChannel();
}

/* -------------------- Mute & Fullscreen -------------------- */

document.addEventListener("keydown", (e) => {
  const key = e.key.toLowerCase();

  const tag = document.activeElement?.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA") return;

  // B = big picture mode / fullscreen whole webpage
if (key === "b") {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen?.().catch(() => {});
  } else {
    document.exitFullscreen?.().catch(() => {});
  }
}

  // S = Schedule
if (key === "s") {
  e.preventDefault();
  toggleScheduleOverlay();
}

  // F = fullscreen VIDEO only
  if (key === "f") {
    if (!document.fullscreenElement) {
      player.requestFullscreen?.().catch(() => {});
    } else {
      document.exitFullscreen?.().catch(() => {});
    }
  }

  // M = mute
  if (key === "m") {
    player.muted = !player.muted;
  }

  // → RIGHT arrow = next channel
  if (e.key === "ArrowRight") {
    e.preventDefault();
    nextChannel();
  }

  // ← LEFT arrow = previous channel
  if (e.key === "ArrowLeft") {
    e.preventDefault();
    prevChannel();
  }
});

/* -------------------- Schedule Display -------------------- */

function renderScheduleOverlay() {
  const overlay = document.getElementById("scheduleOverlay");
  const channel = getCurrentChannelData();

  if (!overlay || !channel) return;

  const items = channel.playlist || [];

  const visibleItems = items
    .slice(currentIndex)
    .filter(item =>
      !["Advert", "AdBreak", "Ident"].includes(item.type)
    )
    .slice(0, 10);

  overlay.innerHTML = `
    <h3>${channel.name} - Today's Schedule</h3>

    ${visibleItems.map((item, index) => `
      <div class="schedule-item ${index === 0 ? "now-playing" : ""}">
        <span class="schedule-marker">
          ${index === 0 ? "▶ NOW" : "NEXT"}
        </span>

        <span class="schedule-title">
          ${item.type || "Episode"} - ${item.title || "Untitled"}
        </span>
      </div>
    `).join("")}
  `;
}

function toggleScheduleOverlay() {
  const overlay = document.getElementById("scheduleOverlay");
  const channel = getCurrentChannelData();

  if (!overlay || !channel) return;

  if (overlay.classList.contains("active")) {
    overlay.classList.remove("active");
    overlay.innerHTML = "";
    return;
  }

  renderScheduleOverlay();
  overlay.classList.add("active");
}

/* -------------------- Remote Functions -------------------- */

function toggleMute() {
  player.muted = !player.muted;
}

function volumeUp() {
  player.volume = Math.min(1, player.volume + 0.1);
}

function volumeDown() {
  player.volume = Math.max(0, player.volume - 0.1);
}

function toggleVideoFullscreen() {
  if (!document.fullscreenElement) {
    player.requestFullscreen?.().catch(() => {});
  } else {
    document.exitFullscreen?.().catch(() => {});
  }
}

function toggleBigPicture() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen?.().catch(() => {});
  } else {
    document.exitFullscreen?.().catch(() => {});
  }
}

function togglePower() {
  if (!started) {
    powerBtn.click();
    return;
  }

  if (player.paused) {
    playSound(tvOnSound);
    player.play().catch(() => {});
  } else {
    playSound(tvOffSound);
    player.pause();
  }
}

const remoteControl = document.getElementById("remote-control");

document.addEventListener("keydown", (e) => {
  const tag = document.activeElement?.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA") return;

  if (e.key.toLowerCase() === "r" && remoteControl) {
    e.preventDefault();
    remoteControl.classList.toggle("active");
  }
});

function flashRemoteIR() {
  const ir = document.getElementById("remote-ir");
  if (!ir) return;

  ir.classList.remove("flash");
  void ir.offsetWidth;
  ir.classList.add("flash");

  setTimeout(() => {
    ir.classList.remove("flash");
  }, 120);
}

const remote = document.getElementById("remote-control");

if (remote) {
  remote.addEventListener("click", (e) => {
    if (e.target.closest(".remote-btn")) {
      playSound(remoteButtonSound);
      flashRemoteIR();
    }
  });
}



/* -------------------- Mobile Device Functions -------------------- */

function enterVideoFullscreen() {
  if (player.requestFullscreen) {
    player.requestFullscreen().catch(() => {});
    return;
  }

  if (player.webkitEnterFullscreen) {
    player.webkitEnterFullscreen();
    return;
  }

  if (player.webkitRequestFullscreen) {
    player.webkitRequestFullscreen();
  }
}

if ("ontouchstart" in window) {
  const mobileScreen = document.getElementById("screen");

  let touchStartX = 0;
  let touchStartY = 0;
  let touchStartTime = 0;
  let lastScreenTap = 0;

  mobileScreen?.addEventListener("touchstart", (event) => {
    const touch = event.changedTouches[0];
    touchStartX = touch.clientX;
    touchStartY = touch.clientY;
    touchStartTime = Date.now();
  }, { passive: true });

  mobileScreen?.addEventListener("touchend", (event) => {
    const touch = event.changedTouches[0];
    const deltaX = touch.clientX - touchStartX;
    const deltaY = touch.clientY - touchStartY;
    const elapsed = Date.now() - touchStartTime;

    const horizontalSwipe =
      Math.abs(deltaX) > 55 &&
      Math.abs(deltaX) > Math.abs(deltaY) * 1.25;

    if (horizontalSwipe) {
      if (deltaX < 0) nextChannel();
      else prevChannel();
      lastScreenTap = 0;
      return;
    }

    const movedTooFar = Math.abs(deltaX) > 16 || Math.abs(deltaY) > 16;
    if (movedTooFar || elapsed > 450) {
      lastScreenTap = 0;
      return;
    }

    const now = Date.now();
    if (lastScreenTap && now - lastScreenTap < 350) {
      event.preventDefault();
      enterVideoFullscreen();
      lastScreenTap = 0;
      return;
    }

    lastScreenTap = now;
  }, { passive: false });
}
