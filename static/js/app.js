const messages = document.querySelector("#messages");
const form = document.querySelector("#chatForm");
const input = document.querySelector("#messageInput");
const micButton = document.querySelector("#micButton");
const speakToggle = document.querySelector("#speakToggle");

let speakReplies = true;
let recognition = null;

function addMessage(text, sender, meta = "") {
  const bubble = document.createElement("div");
  bubble.className = `bubble ${sender}`;
  bubble.textContent = text;

  if (meta) {
    const small = document.createElement("span");
    small.className = "meta";
    small.textContent = meta;
    bubble.appendChild(small);
  }

  messages.appendChild(bubble);
  messages.scrollTop = messages.scrollHeight;
}

function speak(text) {
  if (!speakReplies || !("speechSynthesis" in window)) return;

  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.95;
  utterance.pitch = 1;

  window.speechSynthesis.speak(utterance);
}

async function sendMessage(message) {
  addMessage(message, "user");

  input.value = "";
  input.disabled = true;

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ message }),
    });

    const data = await response.json();

    addMessage(
      data.reply,
      "bot",
      `${data.source} · ${data.tag}`
    );

    speak(data.reply);

  } catch (error) {

    const reply =
      "The chat service is not reachable. Please make sure the Flask server is running.";

    addMessage(reply, "bot", "error");
    speak(reply);

  } finally {
    input.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();

  const message = input.value.trim();

  if (message) {
    sendMessage(message);
  }
});

speakToggle.addEventListener("click", () => {
  speakReplies = !speakReplies;

  speakToggle.textContent =
    speakReplies ? "🔊" : "🔇";
});

function setupSpeechRecognition() {

  const SpeechRecognition =
    window.SpeechRecognition ||
    window.webkitSpeechRecognition;

  if (!SpeechRecognition) {

    micButton.disabled = true;

    micButton.title =
      "Speech recognition is not supported in this browser";

    return;
  }

  recognition = new SpeechRecognition();

  recognition.lang = "en-US";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.addEventListener("start", () => {
    micButton.classList.add("listening");
  });

  recognition.addEventListener("end", () => {
    micButton.classList.remove("listening");
  });

  recognition.addEventListener("result", (event) => {

    const transcript =
      event.results[0][0].transcript;

    input.value = transcript;

    sendMessage(transcript);
  });
}

micButton.addEventListener("click", () => {

  if (recognition) {
    recognition.start();
  }

});


// Start speech recognition
setupSpeechRecognition();


// Initial chatbot message
addMessage(
  "Hello! I can explain the project overview, objectives, architecture, tech stack, timeline, and voice module.",
  "bot",
  "intent · greeting"
);


// Clear Chat
function clearChat() {

  messages.innerHTML = "";

  addMessage(
    "Chat cleared. How can I help you?",
    "bot",
    "system"
  );

}
function setupSpeechRecognition() {
  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    micButton.disabled = true;
    micButton.title = "Speech recognition is not supported";
    return;
  }

  recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.addEventListener("start", () => {
    micButton.classList.add("listening");
    micButton.textContent = "🎙️";
    input.placeholder = "Listening...";
    input.disabled = true;
  });

  recognition.addEventListener("end", () => {
    micButton.classList.remove("listening");
    micButton.textContent = "🎤";
    input.placeholder = "Type your message...";
    input.disabled = false;
    input.focus();
  });

  recognition.addEventListener("result", (event) => {
    const transcript = event.results[0][0].transcript.trim();

    if (transcript) {
      input.value = transcript;
      sendMessage(transcript);
    }
  });

  recognition.addEventListener("error", (event) => {
    console.error("Speech recognition error:", event.error);

    if (event.error === "not-allowed") {
      addMessage(
        "Microphone permission was denied. Please allow microphone access.",
        "bot",
        "voice error"
      );
    } else if (event.error === "no-speech") {
      addMessage(
        "I could not hear anything. Please try speaking again.",
        "bot",
        "voice error"
      );
    }
  });
}

micButton.addEventListener("click", () => {
  if (!recognition) return;

  try {
    recognition.start();
  } catch (error) {
    console.log("Recognition already running.");
  }
});

setupSpeechRecognition();

