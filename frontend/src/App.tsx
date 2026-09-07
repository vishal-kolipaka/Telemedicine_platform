import { useState } from 'react';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { DashboardPage } from './pages/DashboardPage';
import { AnalyzePage } from './pages/AnalyzePage';
import { AboutPage } from './pages/AboutPage';
import { ContactPage } from './pages/ContactPage';

type Tab = 'dashboard' | 'analyze' | 'about' | 'contact';

export function App() {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 selection:bg-sky-500 selection:text-white">
      
      {/* Navigation Bar */}
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content Area */}
      <main className="flex-1 max-w-[1550px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'dashboard' && (
          <DashboardPage onStartAnalysis={() => setActiveTab('analyze')} />
        )}

        {activeTab === 'analyze' && <AnalyzePage />}

        {activeTab === 'about' && <AboutPage />}

        {activeTab === 'contact' && <ContactPage />}
      </main>

      {/* Footer */}
      <Footer setActiveTab={setActiveTab} />

    </div>
  );
}

export default App;
