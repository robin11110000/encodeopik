import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const Markdown = ({ content }) => {
  return <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>;
};

export default Markdown;
