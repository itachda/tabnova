let tg = window.Telegram.WebApp;
tg.expand();

let user = tg.initDataUnsafe.user;

function switchTab(tab) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.getElementById(`section-${tab}`).classList.add('active');
  if (tab === "profile") showProfile();
  if (tab === "top") showLeaderboard();
  if (tab === "ref") loadReferrals();
  if (tab === "tasks") loadTasks();
}

// تسجيل المستخدم تلقائيًا
fetch("/register", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    id: user.id,
    first_name: user.first_name,
    ref: new URLSearchParams(window.location.search).get("ref"),
    is_premium: user.is_premium
  })
});

function startClick() {
  fetch("/start_click", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: user.id })
  })
  .then(res => res.json())
  .then(data => {
    if (data.status === "ok") {
      startTimer(data.end);
    } else {
      alert("⛔ يرجى الانتظار حتى تنتهي المدة الحالية.");
    }
  });
}

function startTimer(endTime) {
  document.getElementById("click-area").style.display = "block";
  let timerInterval = setInterval(() => {
    const now = new Date();
    const diff = new Date(endTime) - now;
    if (diff <= 0) {
      clearInterval(timerInterval);
      document.getElementById("timer").innerText = "انتهى!";
      document.getElementById("click-area").style.display = "none";
    } else {
      const min = Math.floor(diff / 60000);
      const sec = Math.floor((diff % 60000) / 1000);
      document.getElementById("timer").innerText = `${min}:${sec.toString().padStart(2, "0")}`;
    }
  }, 1000);
}

function doClick() {
  fetch("/click", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: user.id })
  }).then(res => res.json())
    .then(data => {
      if (data.status === "clicked") {
        showSuccess("🎯 نقرة ناجحة", "+1 nova");
      }
    });
}

function dailyLogin() {
  fetch("/daily_login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: user.id })
  }).then(res => res.json())
    .then(data => {
      if (data.status === "rewarded") {
        showSuccess("🎁 مكافأة يومية", `+${data.reward} nova`);
        document.getElementById("daily-status").innerText = `🌟 سلسلة ${data.streak} يوم`;
      } else {
        document.getElementById("daily-status").innerText = `✅ تم تسجيل اليوم`;
      }
    });
}

function loadTasks() {
  const tasks = [
    { label: "متابعة قناة تيليجرام", code: "tg", link: "https://t.me/tapnovaa" },
    { label: "متابعة تويتر", code: "x", link: "https://x.com/Tapnovas" },
    { label: "متابعة إنستغرام", code: "ig", link: "https://www.instagram.com/tapnovas?igsh=MTFweDV6d3N3OGI0NA==" },
    { label: "متابعة يوتيوب", code: "yt", link: "https://youtube.com/@tapnovas?si=hWtabBDw0RzFcHmj" },
    { label: "متابعة فيسبوك", code: "fb", link: "https://www.facebook.com/profile.php?id=61576925872593" },
    { label: "قناة تعاون 1", code: "c1", link: "https://t.me/venomtrad" },
    { label: "قناة تعاون 2", code: "c2", link: "https://t.me/+ua3dKMOKgrQxM2Y0" },
    { label: "قناة تعاون 3", code: "c3", link: "https://t.me/+R8Cb1I3GwWZmYjA8" }
  ];

  const container = document.getElementById("follow-tasks");
  container.innerHTML = "";
  tasks.forEach(task => {
    const div = document.createElement("div");
    div.innerHTML = `
      <p>${task.label} <a href="${task.link}" target="_blank">🔗 فتح</a>
      <button onclick="verifyTask('${task.code}')">تحقق</button></p>`;
    container.appendChild(div);
  });
}

function verifyTask(code) {
  fetch("/verify_task", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: user.id, task: code })
  }).then(res => res.json())
    .then(data => {
      if (data.status === "rewarded") {
        showSuccess("🎉 تم التحقق", "+1000 nova");
      } else {
        alert("تم تنفيذ المهمة من قبل ✅");
      }
    });
}

function showProfile() {
  fetch("/my_profile", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: user.id })
  }).then(res => res.json())
    .then(data => {
      const mask = name => name.length <= 2 ? "**" : name[0] + "*".repeat(name.length - 2) + name.at(-1);
      document.getElementById("profile-name").innerText = "🙋 الاسم: " + mask(data.name);
      document.getElementById("profile-nova").innerText = "🪙 رصيدك: " + data.nova + " nova";
      document.getElementById("profile-rank").innerText = "🏆 ترتيبك: #" + data.rank;
      document.getElementById("profile-streak").innerText = "📅 أيام متتالية: " + data.streak;
      document.getElementById("profile-click").innerText = "🕹️ حالة النقر: " + data.click_status;
    });
}

function loadReferrals() {
  const refLink = `https://t.me/TAPNOVASbot?start=ref${user.id}`;
  document.getElementById("ref-link").innerText = refLink;

  fetch("/referrals", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(user)
  }).then(res => res.json())
    .then(data => {
      document.getElementById("ref-count").innerText = "👥 عدد الأشخاص الذين قمت بدعوتهم: " + data.count;
      const list = document.getElementById("ref-list");
      list.innerHTML = "";
      data.names.forEach(name => {
        const li = document.createElement("li");
        li.innerText = name;
        list.appendChild(li);
      });
    });
}

function showLeaderboard() {
  fetch("/leaderboard")
    .then(res => res.json())
    .then(data => {
      const topThree = data.slice(0, 3);
      const others = data.slice(3);
      const topBox = document.getElementById("top-three");
      const list = document.getElementById("top-list");

      topBox.innerHTML = `
        <div style="display:flex;justify-content:center;gap:15px">
          ${topThree.map((u, i) => `
            <div style="text-align:center;">
              <img src="${u.photo}" onerror="this.src='/static/default.jpg'" width="64" height="64" style="border-radius:50%;border:2px solid gold">
              <p>${i === 1 ? "🥇" : i === 0 ? "🥈" : "🥉"}<br>${u.name}<br>${u.nova}</p>
            </div>
          `).join("")}
        </div>
      `;

      list.innerHTML = "";
      others.forEach((u, i) => {
        const li = document.createElement("li");
        li.innerText = `#${i + 4} ${u.name} - ${u.nova} nova`;
        list.appendChild(li);
      });
    });
}

function showSuccess(title, text) {
  document.getElementById("popup-title").innerText = title;
  document.getElementById("popup-text").innerText = text;
  document.getElementById("popup-success").style.display = "flex";
}

function closeSuccess() {
  document.getElementById("popup-success").style.display = "none";
}
