import React from "react";
import "../styling/intro.css";

const Footer = () => {
  return (
    <footer className="footer-bar text-white py-4">
      <div className="container d-flex flex-column flex-md-row align-items-center justify-content-between gap-3">
        <div>
          <h6 className="mb-1 text-uppercase">0xnavi AI</h6>
          <small className="text-white-50">
            Your quickest path to loan approval.
          </small>
        </div>
        <div className="text-white-50 small">
          © {new Date().getFullYear()} 0xnavi AI. Crafted for smarter lending.
        </div>
      </div>
    </footer>
  );
};

export default Footer;
