const WELCOME_MESSAGE =
  "Hi! I am GlobalEdu Bridge, your personal scholarship assistant. " +
  "I will help you find scholarships you qualify for and guide you " +
  "through applying. Let us start — what country are you from?";

const CHIP_SETS = {
  country: ["Ghana", "Nigeria", "Kenya", "India", "South Africa", "Ethiopia"],
  level: [
    { label: "Secondary school", value: "1" },
    { label: "Undergraduate", value: "2" },
    { label: "Postgraduate", value: "3" },
    { label: "PhD", value: "4" },
  ],
  field: [
    "Medicine",
    "Engineering",
    "Computer Science",
    "Business",
    "Law",
    "Education",
  ],
  yesno: ["Yes", "No"],
  menu: ["1", "2", "3", "4"],
  grading: ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
};

let sessionId = null;
let sessionReady = false;
let messageCount = 0;
let currentChipSet = "country";

const chatArea = document.getElementById("chatArea");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const chipsContainer = document.getElementById("chips");

function stripMarkdown(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, "$1")
    .replace(/^#{1,6}\s*/gm, "")
    .replace(/^\s*[-*+]\s+/gm, "")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/^\s*>\s+/gm, "")
    .trim();
}

function scrollToBottom() {
  chatArea.scrollTop = chatArea.scrollHeight;
}

function botAvatar() {
  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.innerHTML =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
    '<path d="M12 2L2 7l10 5 10-5-10-5z"/>' +
    '<path d="M2 17l10 5 10-5"/>' +
    '<path d="M2 12l10 5 10-5"/>' +
    "</svg>";
  return avatar;
}

function addBotMessage(text) {
  const msg = document.createElement("div");
  msg.className = "msg bot";
  msg.appendChild(botAvatar());
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = stripMarkdown(text);
  msg.appendChild(bubble);
  chatArea.appendChild(msg);
  scrollToBottom();
}

function addUserMessage(text) {
  const msg = document.createElement("div");
  msg.className = "msg user";
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  msg.appendChild(bubble);
  chatArea.appendChild(msg);
  scrollToBottom();
}

function showTyping() {
  const existing = document.getElementById("typingIndicator");
  if (existing) return;

  const msg = document.createElement("div");
  msg.className = "msg bot typing";
  msg.id = "typingIndicator";
  msg.appendChild(botAvatar());
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
  msg.appendChild(bubble);
  chatArea.appendChild(msg);
  scrollToBottom();
}

function hideTyping() {
  const el = document.getElementById("typingIndicator");
  if (el) el.remove();
}

function updateChips() {
  chipsContainer.innerHTML = "";
  const chips = CHIP_SETS[currentChipSet] || CHIP_SETS.country;

  chips.forEach(function (item) {
    const label = typeof item === "object" ? item.label : item;
    const value = typeof item === "object" ? item.value : item;
    const chip = document.createElement("button");
    chip.className = "chip";
    chip.type = "button";
    chip.textContent = label;
    chip.addEventListener("click", function () {
      messageInput.value = value;
      sendMessage();
    });
    chipsContainer.appendChild(chip);
  });
}

function detectChipSet(botText, userText) {
  const lower = botText.toLowerCase();

  if (lower.includes("grading system")) {
    currentChipSet = "grading";
  } else if (lower.includes("financial need") || lower.includes("y/n")) {
    currentChipSet = "yesno";
  } else if (lower.includes("what would you like to do next")) {
    currentChipSet = "menu";
  } else if (lower.includes("level are you") || lower.includes("enter 1, 2, 3, or 4")) {
    currentChipSet = "level";
  } else if (lower.includes("field would you like")) {
    currentChipSet = "field";
  } else if (lower.includes("country are you from")) {
    currentChipSet = "country";
  } else if (userText && messageCount <= 1) {
    currentChipSet = "level";
  } else if (userText && messageCount === 2) {
    currentChipSet = "field";
  }

  updateChips();
}

function enableInput() {
  sessionReady = true;
  messageInput.disabled = false;
  sendBtn.disabled = false;
  messageInput.focus();
}

function disableInput() {
  sessionReady = false;
  messageInput.disabled = true;
  sendBtn.disabled = true;
}

async function startSession() {
  addBotMessage(WELCOME_MESSAGE);
  updateChips();

  try {
    const res = await fetch("/api/start", { method: "POST" });
    const data = await res.json();
    sessionId = data.session_id;
    enableInput();
  } catch (err) {
    addBotMessage("Could not connect to the assistant. Please refresh the page.");
  }
}

async function sendMessage() {
  const text = messageInput.value.trim();
  if (!text || !sessionReady || !sessionId) return;

  addUserMessage(text);
  messageInput.value = "";
  messageCount += 1;
  disableInput();
  showTyping();

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message: text }),
    });
    const data = await res.json();
    hideTyping();

    if (data.error) {
      addBotMessage(data.error);
    } else if (data.text) {
      addBotMessage(data.text);
      detectChipSet(data.text, text);
    }

    if (data.done) {
      messageInput.placeholder = "Session ended — refresh to start again";
    } else {
      enableInput();
    }
  } catch (err) {
    hideTyping();
    addBotMessage("Something went wrong. Please try again.");
    enableInput();
  }
}

sendBtn.addEventListener("click", sendMessage);

messageInput.addEventListener("keydown", function (e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

startSession();
