import { useMemo, useRef, useState, useEffect } from "react";
import "./styling/chatbox.css";
import ProcessingBlink from "../../components/Blink";

const makeMessageId = () =>
  typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : `msg-${Date.now()}-${Math.random().toString(16).slice(2)}`;

const ChatBox = ({
  case_id,
  showAlert,
  host,
  title = "Virtual Assistant",
  placeholder = "Ask about this outcome...",
}) => {
  const [inputValue, setInputValue] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoader] = useState(false);
  const messageListRef = useRef(null);
  const skipNextPersist = useRef(true);

  useEffect(() => {
    if (!case_id) {
      setMessages([]);
      return;
    }
    skipNextPersist.current = true;
    const storedMessages = localStorage.getItem(`chat_messages_${case_id}`);
    if (storedMessages) {
      setMessages(JSON.parse(storedMessages));
    } else {
      setMessages([]);
    }
  }, [case_id]);

  useEffect(() => {
    if (!case_id) return;
    if (skipNextPersist.current) {
      skipNextPersist.current = false;
      return;
    }
    localStorage.setItem(`chat_messages_${case_id}`, JSON.stringify(messages));
  }, [messages, case_id]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    const trimmed = inputValue.trim();
    if (!trimmed) return;

    const userMessage = {
      id: makeMessageId(),
      role: "user",
      content: trimmed,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setLoader(true);

    if (!case_id) {
      showAlert(
        "No case is selected yet. Please open a case before chatting.",
        "warning"
      );
      setLoader(false);
      return;
    }

    let assistantAnswer = "Unable to generate response.";

    try {
      const response = await fetch(`${host}/search/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          case_id: case_id,
          query: trimmed,
        }),
      });
      const payload = await response.json().catch(() => null);

      if (!response.ok || payload?.status !== 200) {
        const errorMessage =
          payload?.errors ||
          payload?.message ||
          "There was an error generating the response.";
        showAlert(
          "There was error generating response, see console logs for more details",
          "danger"
        );
        console.error(errorMessage);
      } else if (payload?.data?.response?.answer) {
        assistantAnswer = payload.data.response.answer;
      }
    } catch (error) {
      console.error("Chat query failed", error);
      showAlert("Unable to reach chat service", "danger");
    }
    const assistantMessage = {
      id: makeMessageId(),
      role: "assistant",
      content: assistantAnswer,
      animated: true,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, assistantMessage]);
    setLoader(false);
  };

  const emptyState = useMemo(
    () => ({
      headline: "How can I help?",
      body: "Use the chat to ask follow-up questions.",
    }),
    []
  );

  useEffect(() => {
    if (messageListRef.current) {
      messageListRef.current.scrollTop = messageListRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="chatbox-container">
      <div className="chatbox-window">
        <div className="chatbox-header">
          <div>
            <strong>{title}</strong>
            <div className="chatbox-header-subtitle">
              Ready to answer questions
            </div>
          </div>
        </div>

        <div className="chatbox-body" ref={messageListRef}>
          {messages.length === 0 ? (
            <div className="chatbox-empty-state">
              <h6 style={{ margin: 0, fontWeight: 600 }}>
                {emptyState.headline}
              </h6>
              <p style={{ margin: "0.4rem 0 0 0", fontSize: "0.9rem" }}>
                {emptyState.body}
              </p>
            </div>
          ) : (
            <div className="chatbox-messages">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`chatbox-message-row ${
                    message.role === "user"
                      ? "chatbox-message-user"
                      : "chatbox-message-assistant"
                  }`}
                >
                  <span
                    className={`chatbox-bubble ${
                      message.role === "user"
                        ? "chatbox-bubble-user"
                        : "chatbox-bubble-assistant text-secondary"
                    }`}
                  >
                    {message.content}
                  </span>
                </div>
              ))}
              {loading && (
                <div className="chatbox-message-row chatbox-message-assistant">
                  <ProcessingBlink tag="Thinking" text_color="secondary" />
                </div>
              )}
            </div>
          )}
        </div>

        <form className="chatbox-footer" onSubmit={handleSubmit}>
          <div className="input-group input-group-sm">
            <input
              type="text"
              className="form-control chatbox-input"
              placeholder={placeholder}
              value={inputValue}
              onChange={(event) => setInputValue(event.target.value)}
            />
            <button type="submit" className="btn btn-primary">
              Send
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChatBox;
