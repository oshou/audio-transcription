import { useEffect, useState } from "react";
import "./App.css";
import styles from "./App.module.css";
import MessageList from "./MessageList";

function App() {
  const wsTextOutputURL = process.env.REACT_APP_WS_TEXT_OUTPUT_URL ?? "";
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);

  useEffect(() => {
    const wsConnection = new WebSocket(wsTextOutputURL);
    setWsConnection(wsConnection);

    return () => {
      wsConnection.close();
    };
  }, []);

  return (
    <div className="App">
      <h1 className={styles.title}>Audio transcription</h1>
      <MessageList wsConnection={wsConnection} />
    </div>
  );
}

export default App;
