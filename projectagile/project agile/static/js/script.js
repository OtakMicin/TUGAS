document.addEventListener("DOMContentLoaded", function() {
    const toggleBtn = document.getElementById("darkModeToggle");
    const body = document.body;
    const navbar = document.getElementById("mainNavbar");

    if (localStorage.getItem("theme") === "dark") {
        enableDarkMode();
    }

    toggleBtn.addEventListener("click", () => {
        if (body.classList.contains("bg-dark")) {
            disableDarkMode();
        } else {
            enableDarkMode();
        }
    });

    function greetUser() {
    const bubble = document.getElementById('robotBubble');
    bubble.classList.add('show');
    
    // Hilang otomatis setelah 3 detik
    setTimeout(() => {
        bubble.classList.remove('show');
    }, 3000);
}

    function enableDarkMode() {
        body.classList.add("bg-dark", "text-light");
        navbar.classList.remove("bg-light", "navbar-light");
        navbar.classList.add("bg-dark", "navbar-dark");
        document.documentElement.setAttribute("data-bs-theme","dark")
        toggleBtn.innerHTML = "☀️ Light Mode";
        localStorage.setItem("theme", "dark");
    }

    function disableDarkMode() {
        body.classList.remove("bg-dark", "text-light");
        navbar.classList.remove("bg-dark", "navbar-dark");
        navbar.classList.add("bg-light", "navbar-light");
        document.documentElement.setAttribute("data-bs-theme","light")
        toggleBtn.innerHTML = "🌙 Dark Mode";
        localStorage.setItem("theme", "light");
    }
});

const sendBtn = document.getElementById('send-btn');
const userInput = document.getElementById('user-input');
const chatBox = document.getElementById('chat-box');

if (sendBtn && userInput && chatBox) {
    sendBtn.addEventListener('click', sendMessage);
    
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    async function sendMessage() {
        const message = userInput.value.trim();
        if (message === '') return;

        const userHtml = `
            <div class="mb-3 text-end">
                <div class="p-3 bg-primary text-white border rounded d-inline-block shadow-sm" style="max-width: 80%; border-bottom-right-radius: 0;">
                    ${message}
                </div>
            </div>
        `;
        chatBox.insertAdjacentHTML('beforeend', userHtml);
        userInput.value = '';
        scrollToBottom();

        const loadingId = "loading-" + Date.now();
        const loadingHtml = `
            <div class="mb-3" id="${loadingId}">
                <div class="p-3 bg-white border rounded d-inline-block shadow-sm" style="max-width: 80%; border-bottom-left-radius: 0;">
                    <strong>🤖 AI Dokter:</strong> <em>Sedang menganalisis...</em>
                </div>
            </div>
        `;
        chatBox.insertAdjacentHTML('beforeend', loadingHtml);
        scrollToBottom();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();
            const loader = document.getElementById(loadingId);
            if (loader) loader.remove();

            const aiHtml = `
                <div class="mb-3">
                    <div class="p-3 bg-white border rounded d-inline-block shadow-sm" style="max-width: 80%; border-bottom-left-radius: 0;">
                        <strong>🤖 AI Dokter:</strong> ${data.response}
                    </div>
                </div>
            `;
            chatBox.insertAdjacentHTML('beforeend', aiHtml);
            scrollToBottom();
        } catch (error) {
            const loader = document.getElementById(loadingId);
            if (loader) { 
                loader.innerHTML = `
                    <div class="p-3 bg-danger text-white border rounded d-inline-block shadow-sm">
                        Gagal terhubung ke server.
                    </div>
                `;
            }
        }
    }

    function scrollToBottom() {
        chatBox.scrollTop = chatBox.scrollHeight;
    }
}

document.addEventListener("DOMContentLoaded", function() {
    const langSwitcher = document.querySelector("select");

    // ambil bahasa dari localStorage
    let lang = localStorage.getItem("lang") || "id";

    // set dropdown sesuai bahasa
    langSwitcher.value = lang;

    // langsung apply bahasa saat load
    applyLanguage(lang);

    // event change
    langSwitcher.addEventListener("change", (e) => {
        const selectedLang = e.target.value;
        localStorage.setItem("lang", selectedLang);
        applyLanguage(selectedLang);
    });

    function applyLanguage(lang) {
        const elements = document.querySelectorAll("[data-en]");
        elements.forEach(el => {
            el.innerHTML = lang === "en"
                ? el.getAttribute("data-en")
                : el.getAttribute("data-id");
        });
    }

});


document.addEventListener("DOMContentLoaded", function() {
    const faders = document.querySelectorAll('.fade-in-up');
    
    const appearOptions = {
        threshold: 0.15,
        rootMargin: "0px 0px -50px 0px"
    };

    const appearOnScroll = new IntersectionObserver(function(entries, appearOnScroll) {
        entries.forEach(entry => {
            if (!entry.isIntersecting) {
                return;
            } else {
                entry.target.classList.add('muncul');
                appearOnScroll.unobserve(entry.target);
            }
        });
    }, appearOptions);

    faders.forEach(fader => {
        appearOnScroll.observe(fader);
    });
});