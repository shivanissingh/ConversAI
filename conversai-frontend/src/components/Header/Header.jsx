import { motion } from 'framer-motion';
import ThemeToggle from '../ThemeToggle/ThemeToggle.jsx';
import './Header.css';

/**
 * Header Component
 * App-wide header with navigation and theme toggle.
 */
function Header({ onNewExplanation, onHistory, showNavigation = false }) {
    return (
        <motion.header
            className="header"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
        >
            <div className="header__container">
                {/* Logo/Title */}
                <div className="header__logo">
                    <span className="text-gradient">ConversAI</span>
                </div>

                {/* Navigation (conditional) */}
                {showNavigation && (
                    <nav className="header__nav">
                        <button
                            className="header__nav-button"
                            onClick={onNewExplanation}
                        >
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M12 5v14M5 12h14" />
                            </svg>
                            <span>New</span>
                        </button>
                        <button
                            className="header__nav-button"
                            onClick={onHistory}
                        >
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                                <path d="M3 3v5h5" />
                                <path d="M12 7v5l4 2" />
                            </svg>
                            <span>History</span>
                        </button>
                    </nav>
                )}

                {/* Theme Toggle */}
                <div className="header__actions">
                    <ThemeToggle />
                </div>
            </div>
        </motion.header>
    );
}

export default Header;
