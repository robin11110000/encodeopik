import React, { useState, useEffect } from "react";

function ProcessingBlink({ tag = "Processing", text_color = "info" }) {
  const [dots, setDots] = useState("");

  useEffect(() => {
    const interval = setInterval(() => {
      setDots((prev) => (prev.length < 6 ? prev + "." : ""));
    }, 500); // changes every 500ms

    return () => clearInterval(interval); // cleanup on unmount
  }, []);

  return (
    <p className={`text-${text_color} fw-semibold`}>
      {tag}
      {dots}
    </p>
  );
}

export default ProcessingBlink;
