import { useState, useEffect, useMemo } from "react";
import "../Styling/intro.css";

const TypingEffect = ({ className, text, textSegments, speed = 40 }) => {
  const segments = useMemo(() => {
    if (Array.isArray(textSegments) && textSegments.length > 0) {
      return textSegments;
    }
    if (typeof text === "string") {
      return [{ text }];
    }
    return [];
  }, [textSegments, text]);

  const characters = useMemo(() => {
    const chars = [];
    segments.forEach(({ text: segmentText = "", className: segmentClass }) => {
      segmentText.split("").forEach((char) => {
        chars.push({ char, className: segmentClass });
      });
    });
    return chars;
  }, [segments]);

  const [displayCount, setDisplayCount] = useState(0);

  useEffect(() => {
    setDisplayCount(0);
  }, [characters]);

  useEffect(() => {
    if (displayCount < characters.length) {
      const timeout = setTimeout(() => {
        setDisplayCount((prev) => prev + 1);
      }, speed);
      return () => clearTimeout(timeout);
    }
  }, [displayCount, characters.length, speed]);

  const displayedSegments = useMemo(() => {
    const typed = characters.slice(0, displayCount);
    return typed.reduce((groups, currentChar) => {
      const lastGroup = groups[groups.length - 1];
      if (lastGroup && lastGroup.className === currentChar.className) {
        lastGroup.text += currentChar.char;
      } else {
        groups.push({
          className: currentChar.className,
          text: currentChar.char,
        });
      }
      return groups;
    }, []);
  }, [characters, displayCount]);

  return (
    <div id="typing">
      <h4 className={className}>
        {displayedSegments.map((segment, index) =>
          segment.className ? (
            <span key={index} className={segment.className}>
              {segment.text}
            </span>
          ) : (
            segment.text
          )
        )}
      </h4>
    </div>
  );
};

export default TypingEffect;
