// src/components/ChatBox.js
import React, { useState } from "react";
import axios from "axios";

const ChatBox = () => {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);

  const sendMessage = async (e) => {
    e.preventDefault();

    setMessages((prev) => [...prev, `🧑 You: ${input}`]);

    try {
      const res = await axios.post("http://localhost:8000/chat", {
        user_input: input,
      });
      setMessages((prev) => [...prev, `🤖 Bot: ${res.data.response}`]);
    } catch (err) {
      setMessages((prev) => [...prev, "⚠️ Error contacting bot."]);
    }

    setInput("");
  };

  return (
    <div style={{ padding: "2rem", maxWidth: "600px", margin: "auto" }}>
      <h2>♻️ EcoChat Assistant</h2>
      <div style={{ marginBottom: "1rem" }}>
        {messages.map((msg, i) => (
          <div key={i}>{msg}</div>
        ))}
      </div>
      <form onSubmit={sendMessage}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          style={{ width: "80%", padding: "0.5rem" }}
          placeholder="Ask something like 'List available electronics'"
        />
        <button type="submit" style={{ padding: "0.5rem" }}>
          Send
        </button>
      </form>
    </div>
  );
};

export default ChatBox;