import { motion } from 'framer-motion';
import { useTheme } from '../../context/ThemeContext.jsx';
import './ThemeToggle.css';

/**
 * ThemeToggle Component
 * Elegant sun/moon toggle for switching between light and dark themes.
 */
function ThemeToggle() {
    const { isDark, toggleTheme } = useTheme();

    return (
        <motion.button
            className="theme-toggle"
            onClick={toggleTheme}
            aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
        >
            <div className="theme-toggle__icons">
                {/* Sun Icon */}
                <motion.svg
                    className="theme-toggle__icon theme-toggle__icon--sun"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    animate={{
                        scale: isDark ? 0 : 1,
                        opacity: isDark ? 0 : 1,
                        rotate: isDark ? -90 : 0,
                    }}
                    transition={{ duration: 0.3, ease: 'easeOut' }}
                >
                    <circle cx="12" cy="12" r="5" />
                    <line x1="12" y1="1" x2="12" y2="3" />
                    <line x1="12" y1="21" x2="12" y2="23" />
                    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                    <line x1="1" y1="12" x2="3" y2="12" />
                    <line x1="21" y1="12" x2="23" y2="12" />
                    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                </motion.svg>

                {/* Moon Icon */}
                <motion.svg
                    className="theme-toggle__icon theme-toggle__icon--moon"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    animate={{
                        scale: isDark ? 1 : 0,
                        opacity: isDark ? 1 : 0,
                        rotate: isDark ? 0 : 90,
                    }}
                    transition={{ duration: 0.3, ease: 'easeOut' }}
                >
                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                </motion.svg>
            </div>
        </motion.button>
    );
}

export default ThemeToggle;
