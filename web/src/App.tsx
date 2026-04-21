import React from "react";
import { I18nProvider } from "./i18n";
import { useRouter } from "./router";
import { Navbar } from "./components/shell/Navbar";
import { Footer } from "./components/shell/Footer";
import { Starfield } from "./components/ui/Starfield";
import { Home } from "./components/pages/Home";
import { Lessons } from "./components/pages/Lessons";
import { Lab } from "./components/pages/Lab";
import { Glossary } from "./components/pages/Glossary";
import { About } from "./components/pages/About";

function Body() {
  const { route } = useRouter();
  switch (route.name) {
    case "home": return <Home />;
    case "lessons": return <Lessons chapterId={route.chapter} />;
    case "lab": return <Lab tool={route.tool} />;
    case "glossary": return <Glossary />;
    case "about": return <About />;
  }
}

export function App() {
  return (
    <I18nProvider>
      <Starfield density={1} intensity={1} />
      <div style={{ position: "relative", zIndex: 10, minHeight: "100vh", display: "flex", flexDirection: "column" }}>
        <Navbar />
        <main style={{ flex: 1 }}>
          <Body />
        </main>
        <Footer />
      </div>
    </I18nProvider>
  );
}
