import { createContext, useContext, useState, useEffect, useCallback } from 'react';

const STORAGE_KEY = 'conversai-theme';
const THEMES = {
    LIGHT: 'light',
    DARK: 'dark',
};

/**
 * Get initial theme based on:
 * 1. localStorage (user preference)
 * 2. System preference (prefers-color-scheme)
 * 3. Default to dark
 */
function getInitialTheme() {
    // Check localStorage first (user override)
    if (typeof window !== 'undefined') {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored === THEMES.LIGHT || stored === THEMES.DARK) {
            return stored;
        }

        // Check system preference
        if (window.matchMedia?.('(prefers-color-scheme: light)').matches) {
            return THEMES.LIGHT;
        }
    }

    // Default to dark
    return THEMES.DARK;
}

const ThemeContext = createContext({
    theme: THEMES.DARK,
    toggleTheme: () => { },
    setTheme: () => { },
    isDark: true,
});

/**
 * ThemeProvider Component
 * Manages theme state, persistence, and applies theme to document.
 */
export function ThemeProvider({ children }) {
    const [theme, setThemeState] = useState(THEMES.DARK);
    const [isInitialized, setIsInitialized] = useState(false);

    // Initialize theme on mount
    useEffect(() => {
        const initialTheme = getInitialTheme();
        setThemeState(initialTheme);
        setIsInitialized(true);
    }, []);

    // Apply theme to document when it changes
    useEffect(() => {
        if (!isInitialized) return;

        // Apply data-theme attribute to html element
        document.documentElement.setAttribute('data-theme', theme);

        // Also update color-scheme for native elements
        document.documentElement.style.colorScheme = theme;

        // Persist to localStorage
        localStorage.setItem(STORAGE_KEY, theme);
    }, [theme, isInitialized]);

    // Toggle between light and dark
    const toggleTheme = useCallback(() => {
        setThemeState((prev) => prev === THEMES.DARK ? THEMES.LIGHT : THEMES.DARK);
    }, []);

    // Set specific theme
    const setTheme = useCallback((newTheme) => {
        if (newTheme === THEMES.LIGHT || newTheme === THEMES.DARK) {
            setThemeState(newTheme);
        }
    }, []);

    const value = {
        theme,
        toggleTheme,
        setTheme,
        isDark: theme === THEMES.DARK,
        isLight: theme === THEMES.LIGHT,
    };

    return (
        <ThemeContext.Provider value={value}>
            {children}
        </ThemeContext.Provider>
    );
}

/**
 * Hook to access theme context.
 */
export function useTheme() {
    const context = useContext(ThemeContext);
    if (!context) {
        throw new Error('useTheme must be used within a ThemeProvider');
    }
    return context;
}

export { THEMES };
export default ThemeContext;
