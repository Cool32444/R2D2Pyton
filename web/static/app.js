async function sendMessage() {

    const input = document.getElementById("messageInput");

    const message = input.value.trim();

    if (!message) {
        return;
    }

    addMessage("You", message);

    input.value = "";

    addMessage("R2D2", "Thinking...");

    try {

        const response = await fetch("/api/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: message
            })

        });

        const data = await response.json();

        removeThinking();

        addMessage("R2D2", data.response);

    }

    catch (error) {

        removeThinking();

        addMessage(
            "R2D2",
            "Sorry, something went wrong."
        );

        console.error(error);

    }
}


function addMessage(sender, text) {

    const messages =
        document.getElementById("messages");

    const message =
        document.createElement("div");

    message.className =
        sender === "You"
        ? "message user"
        : "message r2";

    message.textContent =
        sender + ": " + text;

    messages.appendChild(message);

    messages.scrollTop =
        messages.scrollHeight;
}


function removeThinking() {

    const messages =
        document.getElementById("messages");

    const last =
        messages.lastElementChild;

    if (
        last &&
        last.textContent === "R2D2: Thinking..."
    ) {
        last.remove();
    }
}


function handleKey(event) {

    if (event.key === "Enter") {
        sendMessage();
    }
}


function newChat() {

    document.getElementById("messages").innerHTML = "";

    addMessage(
        "R2D2",
        "New conversation started."
    );
}

function logout() {
    window.location.href = "/logout";
}