import { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { DashboardPage } from './pages/DashboardPage';
import { AnalyzePage } from './pages/AnalyzePage';
import { AboutPage } from './pages/AboutPage';
import { ContactPage } from './pages/ContactPage';
import { GuidedDemoPage } from './pages/GuidedDemoPage';

type Tab = 'dashboard' | 'analyze' | 'about' | 'contact' | 'guided-demo';

export function App() {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');
  const [guidedDemoActive, setGuidedDemoActive] = useState(false);
  const [guidedDemoStep, setGuidedDemoStep] = useState(0);

  // Always reset scroll to the top whenever tab or guided demo step changes
  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
  }, [activeTab, guidedDemoStep]);

  const handleStartGuidedDemo = () => {
    setGuidedDemoActive(true);
    setGuidedDemoStep(0);
    setActiveTab('guided-demo');
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
  };

  const handleExitGuidedDemo = () => {
    setGuidedDemoActive(false);
    setGuidedDemoStep(0);
    setActiveTab('dashboard');
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
  };

  const handleContinueToAnalyze = () => {
    setGuidedDemoActive(true);
    setGuidedDemoStep(2);
    setActiveTab('analyze');
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
  };

  const handleTabChange = (tab: Tab) => {
    // If the user navigates using normal navigation, clear guided demo state
    if (tab !== 'guided-demo') {
      setGuidedDemoActive(false);
      setGuidedDemoStep(0);
    }
    setActiveTab(tab);
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 selection:bg-sky-500 selection:text-white">
      
      {/* Navigation Bar */}
      <Navbar activeTab={activeTab} setActiveTab={handleTabChange} />

      {/* Main Content Area */}
      <main className="flex-1 max-w-[1550px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'dashboard' && (
          <DashboardPage
            onStartAnalysis={() => {
              setGuidedDemoActive(false);
              setActiveTab('analyze');
            }}
            onStartGuidedDemo={handleStartGuidedDemo}
          />
        )}

        {activeTab === 'analyze' && (
          <AnalyzePage
            isGuidedDemo={guidedDemoActive && guidedDemoStep >= 2}
            guidedDemoStep={guidedDemoStep}
            onExitGuidedDemo={handleExitGuidedDemo}
            onGuidedDemoAdvance={() => setGuidedDemoStep(3)}
          />
        )}

        {activeTab === 'about' && <AboutPage />}

        {activeTab === 'contact' && <ContactPage />}

        {activeTab === 'guided-demo' && (
          <GuidedDemoPage
            step={guidedDemoStep}
            setStep={setGuidedDemoStep}
            onExit={handleExitGuidedDemo}
            onContinueToAnalyze={handleContinueToAnalyze}
          />
        )}
      </main>

      {/* Footer */}
      <Footer setActiveTab={handleTabChange} />

    </div>
  );
}

export default App;
