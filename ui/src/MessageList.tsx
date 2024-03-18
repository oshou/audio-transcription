import React, { useEffect, useState } from "react";
import styles from "./MessageList.module.css";

interface Message {
  id: number;
  text: string;
}

interface MessageInputProps {
  wsConnection: WebSocket | null;
}

const MessageList: React.FC<MessageInputProps> = ({ wsConnection }) => {
  const [messages, setMessages] = useState<Message[]>([]);

  useEffect(() => {
    if (wsConnection) {
      wsConnection.onmessage = (event) => {
        setMessages((prevMessages) => [
          { id: prevMessages.length, text: event.data },
          ...prevMessages,
        ]);
      };
    }
  }, [wsConnection]);

  return (
    <ul className={styles.messageList}>
      {messages.map((message) => (
        <li key={message.id} className={styles.messageItem}>
          {message.text}
        </li>
      ))}
    </ul>
  );
};

export default MessageList;
