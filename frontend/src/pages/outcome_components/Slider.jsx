import React, { useId } from "react";

const Slider = ({ images }) => {
  const carouselId = useId();

  if (!images || images.length === 0) {
    return <p>No images to display.</p>;
  }

  return (
    <div
      id={carouselId}
      className="carousel slide"
      data-bs-ride="carousel"
      style={{
        margin: "0 auto",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      {/* Indicators */}
      <div className="carousel-indicators">
        {images.map((_, idx) => (
          <button
            key={idx}
            type="button"
            data-bs-target={`#${carouselId}`}
            data-bs-slide-to={idx}
            className={idx === 0 ? "active" : ""}
            aria-current={idx === 0 ? "true" : undefined}
            aria-label={`Slide ${idx + 1}`}
            style={{
              backgroundColor: "black",
            }}
          ></button>
        ))}
      </div>

      {/* Slides */}
      <div className="carousel-inner">
        {images.map((img, idx) => (
          <div
            key={idx}
            className={`carousel-item ${idx === 0 ? "active" : ""}`}
          >
            <img
              src={
                img.startsWith("data:image")
                  ? img
                  : `data:image/jpeg;base64,${img}`
              }
              className="d-block animate__animated animate__zoomIn"
              alt={`Slide ${idx + 1}`}
              style={{
                maxWidth: "100%",
                height: "710px",
                margin: "0 auto",
                borderRadius: "8px",
              }}
            />
          </div>
        ))}
      </div>

      {/* Controls */}
      <button
        className="carousel-control-prev"
        type="button"
        data-bs-target={`#${carouselId}`}
        data-bs-slide="prev"
        style={{ filter: "invert(100%)" }} // makes arrow icon black
      >
        <span
          className="carousel-control-prev-icon"
          aria-hidden="true"
          style={{
            filter: "invert(100%)", // ensure icon turns black
          }}
        ></span>
        <span className="visually-hidden">Previous</span>
      </button>

      <button
        className="carousel-control-next"
        type="button"
        data-bs-target={`#${carouselId}`}
        data-bs-slide="next"
        style={{ filter: "invert(100%)" }} // makes arrow icon black
      >
        <span
          className="carousel-control-next-icon"
          aria-hidden="true"
          style={{
            filter: "invert(100%)", // ensure icon turns black
          }}
        ></span>
        <span className="visually-hidden">Next</span>
      </button>
    </div>
  );
};

export default Slider;
