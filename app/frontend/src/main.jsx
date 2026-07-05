import React from "react";
import ReactDOM from "react-dom/client";
import { createHashRouter, RouterProvider } from "react-router-dom";
// bundle Monaco locally (no CDN) so the app runs fully offline
import * as monaco from "monaco-editor";
import { loader } from "@monaco-editor/react";
import editorWorker from "monaco-editor/esm/vs/editor/editor.worker?worker";

self.MonacoEnvironment = { getWorker: () => new editorWorker() };
loader.config({ monaco });
import ProblemList from "./ProblemList.jsx";
import Problem from "./Problem.jsx";
import "./index.css";

const router = createHashRouter([
  { path: "/", element: <ProblemList /> },
  { path: "/problem/:id", element: <Problem /> },
]);

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>
);
