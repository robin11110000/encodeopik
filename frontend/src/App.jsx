import { useState } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import UserState from "./context/UserState";
import Navbar from "./components/Navbar";
import Alert from "./components/Alert";
import Toast from "./components/Toast";
import Scrolltotop from "./components/Scrolltotop";
import Home from "./pages/home/Home";
import Outcomes from "./pages/Outcomes";
import Wrong from "./pages/Wrong";

function App() {
  const host = "http://127.0.0.1:8000/api";
  const [alert, setAlert] = useState(null);
  const [toast, setToast] = useState(null);

  const showAlert = (message, type) => {
    setAlert({
      msg: message,
      type: type,
    });
    setTimeout(() => {
      setAlert(null);
    }, 3500);
  };

  const showToast = (content, copy = false, msg = "", variant = "primary") => {
    console.log(content, copy, msg);
    setToast({
      content,
      copy,
      msg,
      variant,
    });
  };

  const handleToastClose = () => {
    setToast(null);
  };

  return (
    <>
      <UserState prop={{ showAlert, showToast, host }}>
        <Router>
          <Navbar />
          <Scrolltotop />
          <Alert alert={alert} />
          {toast && (
            <Toast
              content={toast.content}
              copy={toast.copy}
              msg={toast.msg}
              variant={toast.variant}
              onClose={handleToastClose}
            />
          )}
          <Routes>
            <Route
              exact
              path="/"
              element={<Home prop={{ showAlert, showToast }} />}
            ></Route>
            <Route
              exact
              path="/:wrong"
              element={<Wrong prop={{ showAlert, showToast }} />}
            ></Route>
<Route
              exact
              path="/outcomes/:caseid"
              element={<Outcomes prop={{ showAlert, showToast, host }} />}
            ></Route>
          </Routes>
        </Router>
      </UserState>
    </>
  );
}

export default App;
