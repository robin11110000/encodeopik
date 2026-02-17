import React from "react";
import Main from "./components/Main";
import Task from "./components/Task";
import Footer from "./components/Footer";

const Home = (props) => {
  const { showAlert, showToast } = props.prop;
  return (
    <>
      <Main prop={{ showAlert }} />
      <Task prop={{ showAlert, showToast }} />
      <Footer />
    </>
  );
};

export default Home;
