
const compareButton = document.querySelector(".compare-btn");

compareButton.addEventListener("click", async function () {
    const car1 = document.getElementById("trim1").value;
    const car2 = document.getElementById("trim2").value;
    const results = document.getElementById("comparison-results");

    if (!car1 || !car2) {
        alert("Please select both cars and configurations!");
        return;
    }

    compareButton.disabled = true;
    results.textContent = "Loading comparison...";

    try {
        const [response1, response2] = await Promise.all([
            fetch(`https://www.fueleconomy.gov/ws/rest/vehicle/${car1}`),
            fetch(`https://www.fueleconomy.gov/ws/rest/vehicle/${car2}`)
        ]);

        if (!response1.ok || !response2.ok) {
            throw new Error("Unable to retrieve vehicle specifications");
        }

        const [xml1, xml2] = await Promise.all([
            response1.text(),
            response2.text()
        ]);

        const parser = new DOMParser();

        const data1 = parser.parseFromString(xml1, "text/xml");
        const data2 = parser.parseFromString(xml2, "text/xml");

        if (
            data1.querySelector("parsererror") ||
            data2.querySelector("parsererror") ||
            !data1.querySelector("vehicle") ||
            !data2.querySelector("vehicle")
        ) {
            throw new Error("Invalid vehicle data");
        }

        const car1Data = getVehicleData(data1);
        const car2Data = getVehicleData(data2);

        results.innerHTML = `
            <h2>Vehicle Comparison</h2>
            <div class="comparison-grid">
                ${createCarCard(car1Data)}
                ${createCarCard(car2Data)}
            </div>
        `;

    } catch (error) {
        console.error("Comparison error:", error);
        results.textContent = "Unable to load vehicle specifications.";
    } finally {
        compareButton.disabled = false;
    }
});

function getVehicleData(xml) {
    const get = (tag) =>
        xml.querySelector(tag)?.textContent?.trim() || "N/A";

    const displacement = get("displ");
    const cylinders = get("cylinders");

    return {
        name: `${get("year")} ${get("make")} ${get("model")}`,
        engine: `${displacement}L ${cylinders} Cylinder`,
        drivetrain: get("drive"),
        transmission: get("trany"),
        fuel: get("fuelType1"),
        cityMPG: get("city08"),
        highwayMPG: get("highway08"),
        combinedMPG: get("comb08")
    };
}

function createCarCard(car) {
    return `
        <div class="result-card">
            <h3>${car.name}</h3>
            <div class="spec-row">
                <span>Engine</span>
                <strong>${car.engine}</strong>
            </div>
            <div class="spec-row">
                <span>Drivetrain</span>
                <strong>${car.drivetrain}</strong>
            </div>
            <div class="spec-row">
                <span>Transmission</span>
                <strong>${car.transmission}</strong>
            </div>
            <div class="spec-row">
                <span>Fuel Type</span>
                <strong>${car.fuel}</strong>
            </div>
            <div class="spec-row">
                <span>City MPG</span>
                <strong>${car.cityMPG}</strong>
            </div>
            <div class="spec-row">
                <span>Highway MPG</span>
                <strong>${car.highwayMPG}</strong>
            </div>
            <div class="spec-row">
                <span>Combined MPG</span>
                <strong>${car.combinedMPG}</strong>
            </div>
        </div>
    `;
}

function getCarId(make, model) {
    const normalized = model.trim().toLowerCase();

    return `${make}-${normalized.replace(/\s+/g, "-")}`;
}

async function loadModels(i) {
    const year = document.getElementById(`year${i}`).value;
    const makeSelect = document.getElementById(`make${i}`);
    const carSelect = document.getElementById(`car${i}`);
    const trimSelect = document.getElementById(`trim${i}`);

    carSelect.innerHTML = '<option value="">Select a model</option>';
    trimSelect.innerHTML = '<option value="">Select trim</option>';

    if (!year || !makeSelect.value) return;

    const make = makeSelect.selectedOptions[0].textContent.trim();

    carSelect.innerHTML = '<option value="">Loading models...</option>';

    try {
        const url = `https://www.fueleconomy.gov/ws/rest/vehicle/menu/model?year=${year}&make=${encodeURIComponent(make)}`;

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error("API request failed");
        }

        const data = await response.text();
        const xml = new DOMParser().parseFromString(data, "text/xml");

        if (xml.querySelector("parsererror")) {
            throw new Error("Invalid API response");
        }

        if (
            document.getElementById(`year${i}`).value !== year ||
            makeSelect.selectedOptions[0]?.textContent.trim() !== make
        ) {
            return;
        }

        carSelect.innerHTML = '<option value="">Select a model</option>';

        const models = xml.querySelectorAll("menuItem");

        models.forEach(function (model) {
            const modelName = model.querySelector("text")?.textContent;

            if (!modelName) return;

            const option = document.createElement("option");
            option.value = getCarId(makeSelect.value, modelName);
            option.textContent = modelName;

            carSelect.appendChild(option);
        });

        if (carSelect.options.length === 1) {
            carSelect.innerHTML =
                '<option value="">No models found</option>';
        }

    } catch (error) {
        console.error("Car API error:", error);
        carSelect.innerHTML =
            '<option value="">Unable to load models</option>';
    }
}

for (let i = 1; i <= 2; i++) {
    const yearSelect = document.getElementById(`year${i}`);
    const makeSelect = document.getElementById(`make${i}`);
    const carSelect = document.getElementById(`car${i}`);
    const trimSelect = document.getElementById(`trim${i}`);

    yearSelect.innerHTML = '<option value="">Select year</option>';

    for (let year = 2027; year >= 2000; year--) {
        const option = document.createElement("option");
        option.value = year;
        option.textContent = year;
        yearSelect.appendChild(option);
    }

   yearSelect.addEventListener("change", function () {
    makeSelect.value = "";
    carSelect.innerHTML = '<option value="">Select a model</option>';
    trimSelect.innerHTML = '<option value="">Select trim</option>';
});

    makeSelect.addEventListener("change", function () {
        loadModels(i);
    });

    carSelect.addEventListener("change", async function () {
        trimSelect.innerHTML =
            '<option value="">Select trim</option>';

        const year = yearSelect.value;
        const make = makeSelect.selectedOptions[0]?.textContent.trim();
        const model = carSelect.selectedOptions[0]?.textContent.trim();

        if (!year || !makeSelect.value || !carSelect.value) return;

        trimSelect.innerHTML =
            '<option value="">Loading trims...</option>';

        try {
            const url = `https://www.fueleconomy.gov/ws/rest/vehicle/menu/options?year=${year}&make=${encodeURIComponent(make)}&model=${encodeURIComponent(model)}`;

            const response = await fetch(url);

            if (!response.ok) {
                throw new Error("Failed to load trims");
            }

            const data = await response.text();
            const xml = new DOMParser().parseFromString(data, "text/xml");

            if (xml.querySelector("parsererror")) {
                throw new Error("Invalid trim response");
            }

            if (
                yearSelect.value !== year ||
                makeSelect.selectedOptions[0]?.textContent.trim() !== make ||
                carSelect.selectedOptions[0]?.textContent.trim() !== model
            ) {
                return;
            }

            const options = xml.querySelectorAll("menuItem");

            trimSelect.innerHTML =
                '<option value="">Select trim</option>';

            options.forEach(function (item) {
                const name = item.querySelector("text")?.textContent;
                const id = item.querySelector("value")?.textContent;

                if (!name || !id) return;

                const option = document.createElement("option");
                option.value = id;
                option.textContent = name;

                trimSelect.appendChild(option);
            });

            if (trimSelect.options.length === 1) {
                trimSelect.innerHTML =
                    '<option value="">No configurations found</option>';
            }

        } catch (error) {
            console.error("Trim API error:", error);
            trimSelect.innerHTML =
                '<option value="">Unable to load trims</option>';
        }
    });
}

const askAIButton = document.getElementById("ask-ai-btn");
const stopAIButton = document.getElementById("stop-ai-btn");
let stopGenerating = false;
let aiController = null;
stopAIButton.addEventListener("click", function () {
    stopGenerating = true;

    if (aiController) {
        aiController.abort();
        aiController = null;
    }

    askAIButton.disabled = false;
    stopAIButton.style.display = "none";
});
const chatMessages = document.getElementById("chat-messages");
const aiInput = document.getElementById("ai-question");

askAIButton.addEventListener("click", async function () {
    const question = aiInput.value.trim();
    stopGenerating = false;

    if (!question) return;

    const userMessage = document.createElement("div");
    userMessage.className = "user-message";
    userMessage.textContent = question;
    chatMessages.appendChild(userMessage);

    aiInput.value = "";

    const aiMessage = document.createElement("div");
    aiMessage.className = "ai-message";
    aiMessage.textContent = "Thinking...";
    chatMessages.appendChild(aiMessage);

    chatMessages.scrollTop = chatMessages.scrollHeight;
    askAIButton.disabled = true;
    stopAIButton.style.display = "inline-block";

    try {
        const controller = new AbortController();
        aiController = controller;
        const response = await fetch("http://127.0.0.1:5001/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message: question }),
            signal: controller.signal
        });

        if (!response.ok) {
            throw new Error("AI request failed");
        }

        const data = await response.json();
        const reply = data.reply || data.error || "No response.";

const words = reply.split(/(\s+)/);
let currentText = "";
aiMessage.textContent = "";

for (const word of words) {

    if (stopGenerating) break;
    currentText += word;

    if (typeof marked !== "undefined" && typeof DOMPurify !== "undefined") {
        aiMessage.innerHTML = DOMPurify.sanitize(marked.parse(currentText));
    } else {
        aiMessage.textContent = currentText;
    }

    chatMessages.scrollTop = chatMessages.scrollHeight;
    await new Promise(resolve => setTimeout(resolve, 35));
}

   } catch (error) {
    if (error.name === "AbortError") {
        aiMessage.textContent = "Generation stopped.";
    } else {
        aiMessage.textContent = "Unable to connect to AI.";
        console.error(error);
    }
} finally {
    askAIButton.disabled = false;
    stopAIButton.style.display = "none";
    chatMessages.scrollTop = chatMessages.scrollHeight;
}
});

aiInput.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !askAIButton.disabled) {
        askAIButton.click();
    }
});

const newChatButton = document.getElementById("new-chat-btn");

newChatButton.addEventListener("click", async function () {
    try {
        const response = await fetch("http://127.0.0.1:5001/new-chat", {
            method: "POST"
        });

        if (!response.ok) {
            throw new Error("Failed to reset conversation");
        }

        chatMessages.innerHTML = `
            <div class="ai-message">
                Hi! I'm your AI Car Assistant. Ask me anything about cars.
            </div>
        `;

        aiInput.value = "";

    } catch (error) {
        console.error("New Chat error:", error);
        alert("Unable to start a new chat.");
    }
});

const heroSection = document.querySelector(".hero");
const heroOverlay = document.createElement("style");
document.head.appendChild(heroOverlay);

window.addEventListener("scroll", function () {
    const scrollAmount = window.scrollY;
    const darkness = Math.min(scrollAmount / 500, 1);
    const heroContent = heroSection.querySelectorAll("h1, p, .hero-buttons");

heroContent.forEach(function (element) {
    element.style.opacity = 1 - darkness;
});
    const overlayDarkness = 0.35 + darkness * 0.45;
    const zoom = 100 + darkness * 8;

heroSection.style.backgroundSize = `${zoom}% auto`;

heroOverlay.textContent = `
    .hero::before {
        background: rgba(0, 0, 0, ${overlayDarkness});
    }
`;
    const shade = Math.round(245 - darkness * 185);

    heroSection.style.backgroundColor = `rgb(${shade}, ${shade}, ${shade})`;
    const heroTitle = heroSection.querySelector("h1");
const heroText = heroSection.querySelector("p");

const textShade = Math.round(17 + darkness * 238);
const paragraphShade = Math.round(107 + darkness * 148);

heroTitle.style.color = `rgb(${textShade}, ${textShade}, ${textShade})`;
heroText.style.color = `rgb(${paragraphShade}, ${paragraphShade}, ${paragraphShade})`;
});