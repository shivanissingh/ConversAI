/**
 * History Utility
 * Manages temporary history storage using localStorage with TTL and max entries.
 */

const STORAGE_KEY = 'conversai_history';
const TTL_MS = 60 * 60 * 1000; // 1 hour
const MAX_ENTRIES = 5;

/**
 * Generate a short title from text (first ~6 words)
 */
function generateTitle(text) {
    const words = text.trim().split(/\s+/).slice(0, 6);
    let title = words.join(' ');
    if (text.trim().split(/\s+/).length > 6) {
        title += '...';
    }
    return title;
}

/**
 * Clean expired entries from history
 */
function cleanExpiredEntries() {
    const history = getHistory();
    const now = Date.now();
    const validEntries = history.filter(entry => {
        return (now - entry.timestamp) < TTL_MS;
    });

    if (validEntries.length !== history.length) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(validEntries));
    }

    return validEntries;
}

/**
 * Get all valid history entries (not expired)
 */
export function getHistory() {
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (!stored) return [];

        const history = JSON.parse(stored);
        const now = Date.now();

        // Filter out expired entries
        return history.filter(entry => {
            return entry && entry.timestamp && (now - entry.timestamp) < TTL_MS;
        });
    } catch (error) {
        console.error('Error reading history:', error);
        return [];
    }
}

/**
 * Save a new entry to history
 */
export function saveToHistory(response, text) {
    try {
        const history = cleanExpiredEntries();

        const entry = {
            id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            timestamp: Date.now(),
            title: generateTitle(text),
            response,
        };

        // Add to beginning of array (newest first)
        history.unshift(entry);

        // Keep only MAX_ENTRIES
        const trimmed = history.slice(0, MAX_ENTRIES);

        localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));

        return entry.id;
    } catch (error) {
        console.error('Error saving to history:', error);
        return null;
    }
}

/**
 * Get a specific history entry by ID
 */
export function getHistoryEntry(id) {
    const history = getHistory();
    return history.find(entry => entry.id === id) || null;
}

/**
 * Delete a specific history entry
 */
export function deleteHistoryEntry(id) {
    try {
        const history = getHistory();
        const filtered = history.filter(entry => entry.id !== id);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
        return true;
    } catch (error) {
        console.error('Error deleting history entry:', error);
        return false;
    }
}

/**
 * Clear all history
 */
export function clearHistory() {
    try {
        localStorage.removeItem(STORAGE_KEY);
        return true;
    } catch (error) {
        console.error('Error clearing history:', error);
        return false;
    }
}

export default {
    getHistory,
    saveToHistory,
    getHistoryEntry,
    deleteHistoryEntry,
    clearHistory,
};
