import { useState, useEffect } from 'react';
import { AnimatePresence } from 'framer-motion';
import { ThemeProvider } from './context/ThemeContext.jsx';
import Navbar from './components/Navbar/Navbar.jsx';
import LandingPage from './components/LandingPage/LandingPage.jsx';
import InputSection from './components/InputSection/InputSection.jsx';
import LoadingView from './components/LoadingView/LoadingView.jsx';
import PlaybackView from './components/PlaybackView/PlaybackView.jsx';
import ErrorView from './components/ErrorView/ErrorView.jsx';
import HistoryView from './components/HistoryView/HistoryView.jsx';
import { generateExplanation, generateTopicExplanation } from './services/api';
import { saveToHistory } from './utils/history';
import './App.css';

// Application states
const STATES = {
  LANDING: 'landing',
  INPUT: 'input',
  LOADING: 'loading',
  PLAYBACK: 'playback',
  ERROR: 'error',
  HISTORY: 'history',
};

function App() {
  const [appState, setAppState] = useState(STATES.LANDING);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [lastRequest, setLastRequest] = useState(null);

  // Restore state from sessionStorage on mount
  useEffect(() => {
    const saved = sessionStorage.getItem('conversai_state');
    if (saved) {
      try {
        const { appState: savedState, response: savedResponse, lastRequest: savedReq } = JSON.parse(saved);
        if (savedResponse && savedState === STATES.PLAYBACK) {
          setResponse(savedResponse);
          setLastRequest(savedReq);
          setAppState(STATES.PLAYBACK);
        }
      } catch (e) {
        console.error('Failed to restore state:', e);
      }
    }
  }, []);

  // Save state to sessionStorage on change
  useEffect(() => {
    if (appState === STATES.PLAYBACK && response) {
      sessionStorage.setItem('conversai_state', JSON.stringify({
        appState,
        response,
        lastRequest
      }));
    } else if (appState === STATES.INPUT || appState === STATES.LANDING) {
      sessionStorage.removeItem('conversai_state');
    }
  }, [appState, response, lastRequest]);

  const handleGetStarted = () => {
    setAppState(STATES.INPUT);
  };

  const handleGoHome = () => {
    setAppState(STATES.LANDING);
    setResponse(null);
    setError(null);
  };

  const handleSubmit = async (data) => {
    setLastRequest(data);
    setAppState(STATES.LOADING);
    setError(null);

    try {
      // Route to topic endpoint or text endpoint based on mode
      const result = data.mode === 'topic'
        ? await generateTopicExplanation(data)
        : await generateExplanation(data);

      setResponse(result);
      setAppState(STATES.PLAYBACK);

      // Save to history — use topic or text as the label
      const historyLabel = data.mode === 'topic' ? data.topic : data.text;
      saveToHistory(result, historyLabel);
    } catch (err) {
      console.error('Generation failed:', err);
      setError(err);
      setAppState(STATES.ERROR);
    }
  };

  const handleRetry = () => {
    if (lastRequest) {
      handleSubmit(lastRequest);
    } else {
      handleBack();
    }
  };

  const handleBack = () => {
    setAppState(STATES.INPUT);
    setResponse(null);
    setError(null);
  };

  const handleNewExplanation = () => {
    setAppState(STATES.INPUT);
    setResponse(null);
    setError(null);
  };

  const handleShowHistory = () => {
    setAppState(STATES.HISTORY);
  };

  const handleRestoreFromHistory = (historyResponse) => {
    setResponse(historyResponse);
    setAppState(STATES.PLAYBACK);
  };

  // Show Navbar on all views except Landing and Loading
  const showNavbar = appState !== STATES.LANDING && appState !== STATES.LOADING;
  // Show "New Explanation" button only on Playback and History pages
  const showNewExplanation = appState === STATES.PLAYBACK || appState === STATES.HISTORY;

  return (
    <ThemeProvider>
      <div className="app">
        {/* Shared Navbar - visible on all views except Landing & Loading */}
        {showNavbar && (
          <Navbar
            onNewExplanation={handleNewExplanation}
            onHistory={handleShowHistory}
            onGoHome={handleGoHome}
            showNewExplanation={showNewExplanation}
          />
        )}

        <AnimatePresence mode="wait">
          {appState === STATES.LANDING && (
            <LandingPage
              key="landing"
              onGetStarted={handleGetStarted}
            />
          )}

          {appState === STATES.INPUT && (
            <InputSection
              key="input"
              onSubmit={handleSubmit}
              isLoading={false}
            />
          )}

          {appState === STATES.LOADING && (
            <LoadingView key="loading" />
          )}

          {appState === STATES.PLAYBACK && response && (
            <PlaybackView
              key="playback"
              response={response}
              onBack={handleBack}
              onFollowUpResponse={(newResponse) => {
                setResponse(newResponse);
                // Save follow-up to history too
                saveToHistory(newResponse, 'Follow-up question');
              }}
            />
          )}

          {appState === STATES.ERROR && (
            <ErrorView
              key="error"
              error={error}
              onRetry={handleRetry}
              onBack={handleBack}
            />
          )}

          {appState === STATES.HISTORY && (
            <HistoryView
              key="history"
              onRestore={handleRestoreFromHistory}
              onBack={handleBack}
            />
          )}
        </AnimatePresence>
      </div>
    </ThemeProvider>
  );
}

export default App;
