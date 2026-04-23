import { motion } from 'framer-motion';
import ThemeToggle from '../ThemeToggle/ThemeToggle.jsx';
import './Navbar.css';

/**
 * Navbar Component
 * Shared sticky navigation bar for all views (Home, Playback, History).
 * Features: Clickable logo (→ landing), navigation buttons, theme toggle.
 */
function Navbar({ onNewExplanation, onHistory, onGoHome, showNewExplanation = false }) {
    return (
        <motion.nav
            className="navbar"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
        >
            <div className="navbar__container">
                {/* Logo — click to go back to landing page */}
                <button
                    className="navbar__logo navbar__logo--btn"
                    onClick={onGoHome}
                    aria-label="Go to home"
                    title="Back to home"
                >
                    <span className="text-gradient">ConversAI</span>
                </button>

                {/* Navigation Actions */}
                <div className="navbar__actions">
                    {/* New Explanation - Only on Playback and History */}
                    {showNewExplanation && (
                        <button
                            className="navbar__button"
                            onClick={onNewExplanation}
                            aria-label="New Explanation"
                        >
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M12 5v14M5 12h14" />
                            </svg>
                            <span>New Explanation</span>
                        </button>
                    )}

                    {/* History - Always visible */}
                    <button
                        className="navbar__button"
                        onClick={onHistory}
                        aria-label="History"
                    >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                            <path d="M3 3v5h5" />
                            <path d="M12 7v5l4 2" />
                        </svg>
                        <span>History</span>
                    </button>
                </div>

                {/* Theme Toggle — always visible on the right */}
                <div className="navbar__theme">
                    <ThemeToggle />
                </div>
            </div>
        </motion.nav>
    );
}

export default Navbar;
