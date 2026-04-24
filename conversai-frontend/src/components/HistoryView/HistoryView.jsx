import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { getHistory, deleteHistoryEntry, clearHistory } from '../../utils/history';
import './HistoryView.css';

/**
 * HistoryView Component
 * Displays temporary history of generated explanations with restore capability.
 */
function HistoryView({ onRestore, onBack }) {
    const [history, setHistory] = useState([]);

    useEffect(() => {
        // Load history and clean expired entries
        const entries = getHistory();
        setHistory(entries);
    }, []);

    const handleRestore = (entry) => {
        onRestore(entry.response);
    };

    const handleDelete = (id) => {
        deleteHistoryEntry(id);
        setHistory(history.filter(entry => entry.id !== id));
    };

    const handleClearAll = () => {
        if (window.confirm('Clear all history? This cannot be undone.')) {
            clearHistory();
            setHistory([]);
        }
    };

    const formatTimestamp = (timestamp) => {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;

        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours}h ago`;

        return date.toLocaleDateString();
    };

    return (
        <motion.div
            className="history-view"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
        >
            {/* Content */}
            <div className="history-view__content">
                {/* Title and Clear Button */}
                <div className="history-view__header-inline">
                    <h1 className="history-view__title">History</h1>
                    {history.length > 0 && (
                        <button className="history-view__clear" onClick={handleClearAll}>
                            Clear All
                        </button>
                    )}
                </div>
                {history.length === 0 ? (
                    <motion.div
                        className="history-view__empty"
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                    >
                        <div className="history-view__empty-icon">📚</div>
                        <h2 className="history-view__empty-title">No History Yet</h2>
                        <p className="history-view__empty-text">
                            Your recent explanations will appear here.
                            <br />
                            History is stored for 2 days.
                        </p>
                    </motion.div>
                ) : (
                    <motion.div
                        className="history-view__list"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                    >
                        <AnimatePresence>
                            {history.map((entry, index) => (
                                <motion.div
                                    key={entry.id}
                                    className="history-entry"
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: 20 }}
                                    transition={{ delay: index * 0.05 }}
                                >
                                    <button
                                        className="history-entry__content"
                                        onClick={() => handleRestore(entry)}
                                    >
                                        <div className="history-entry__header">
                                            <h3 className="history-entry__title">{entry.title}</h3>
                                            <span className="history-entry__time">
                                                {formatTimestamp(entry.timestamp)}
                                            </span>
                                        </div>
                                        <div className="history-entry__meta">
                                            <span className="history-entry__segments">
                                                {entry.response?.segments?.length || 0} segments
                                            </span>
                                            {entry.response?.metadata?.visualSuccess && (
                                                <span className="history-entry__badge">
                                                    ✓ Visuals
                                                </span>
                                            )}
                                            {entry.response?.avatar && (
                                                <span className="history-entry__badge">
                                                    ✓ Avatar
                                                </span>
                                            )}
                                        </div>
                                    </button>

                                    <button
                                        className="history-entry__delete"
                                        onClick={() => handleDelete(entry.id)}
                                        aria-label="Delete entry"
                                    >
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M18 6L6 18M6 6l12 12" />
                                        </svg>
                                    </button>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    </motion.div>
                )}
            </div>
        </motion.div>
    );
}

export default HistoryView;
