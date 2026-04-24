import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    FileText,
    Lightbulb,
    Mic,
    MicOff,
    Sparkles,
    ChevronDown,
    ChevronUp,
    ArrowRight,
    Loader2,
} from 'lucide-react';
import useSpeechRecognition from '../../hooks/useSpeechRecognition';
import './InputSection.css';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const DURATION_OPTIONS = [
    { value: 'short',  label: 'Short (~30s)',  description: 'Quick overview' },
    { value: 'medium', label: 'Medium (~60s)', description: 'Detailed explanation' },
];

const MIN_TEXT_CHARS  = 100;
const MAX_TEXT_CHARS  = 5000;
const MIN_TOPIC_CHARS = 5;

const EXAMPLE_TOPICS = [
    'Quantum Computing',
    'Machine Learning',
    'Blockchain Technology',
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/**
 * InputSection
 *
 * Tab 1 – "Paste Text": existing textarea with 100-char minimum.
 * Tab 2 – "Ask a Topic": single-line input; calls /api/explain/topic.
 *
 * onSubmit receives { mode: 'text'|'topic', text?, topic?, duration, instruction, avatarEnabled }
 */
function InputSection({ onSubmit, isLoading }) {
    // --- Tab state ---
    const [mode, setMode] = useState('text'); // 'text' | 'topic'

    // --- Text mode ---
    const [text, setText] = useState('');

    // --- Topic mode ---
    const [topic, setTopic] = useState('');

    // --- Shared settings ---
    const [duration,        setDuration]        = useState('medium');
    const [instruction,     setInstruction]     = useState('');
    const [showInstruction, setShowInstruction] = useState(false);
    const [avatarEnabled,   setAvatarEnabled]   = useState(true);

    // --- Voice input (text mode only) ---
    const {
        isListening,
        transcript,
        isSupported: voiceSupported,
        toggleListening,
        resetTranscript,
    } = useSpeechRecognition();

    // Append voice transcript to text
    useEffect(() => {
        if (transcript) {
            setText((prev) => {
                const sep = prev && !prev.endsWith(' ') ? ' ' : '';
                return prev + sep + transcript;
            });
            resetTranscript();
        }
    }, [transcript, resetTranscript]);

    // Reset inputs when switching modes
    const handleModeSwitch = (newMode) => {
        setMode(newMode);
    };

    // --- Validation ---
    const textValid  = text.length  >= MIN_TEXT_CHARS  && text.length  <= MAX_TEXT_CHARS;
    const topicValid = topic.trim().length >= MIN_TOPIC_CHARS;
    const canSubmit  = !isLoading && (mode === 'text' ? textValid : topicValid);

    const getCharColor = () => {
        if (text.length < MIN_TEXT_CHARS) return 'var(--color-text-muted)';
        if (text.length > MAX_TEXT_CHARS) return 'var(--color-accent-error)';
        return 'var(--color-accent-success)';
    };

    // --- Submit ---
    const handleSubmit = (e) => {
        e.preventDefault();
        if (!canSubmit) return;

        if (mode === 'topic') {
            onSubmit({
                mode: 'topic',
                topic: topic.trim(),
                duration,
                instruction: instruction.trim() || null,
                avatarEnabled,
            });
        } else {
            onSubmit({
                mode: 'text',
                text: text.trim(),
                duration,
                instruction: instruction.trim() || null,
                avatarEnabled,
            });
        }
    };

    // ---------------------------------------------------------------------------
    // Render
    // ---------------------------------------------------------------------------
    return (
        <motion.div
            className="input-section"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
        >
            {/* Header */}
            <div className="input-section__header">
                <motion.h1
                    className="input-section__title"
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                >
                    <span className="text-gradient">ConversAI</span>
                </motion.h1>
                <motion.p
                    className="input-section__subtitle"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.2 }}
                >
                    {mode === 'topic'
                        ? 'Type any topic and get an instant visual explanation'
                        : 'Transform any text into an engaging visual explanation'}
                </motion.p>
            </div>

            <motion.form
                className="input-section__form"
                onSubmit={handleSubmit}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
            >
                <div className="input-section__card">

                    {/* ── Mode Tab Toggle ─────────────────────────── */}
                    <div className="mode-tabs">
                        <button
                            type="button"
                            id="tab-text"
                            className={`mode-tab ${mode === 'text' ? 'mode-tab--active' : ''}`}
                            onClick={() => handleModeSwitch('text')}
                            disabled={isLoading}
                            aria-selected={mode === 'text'}
                            role="tab"
                        >
                            <FileText size={15} strokeWidth={2} />
                            Paste Text
                        </button>
                        <button
                            type="button"
                            id="tab-topic"
                            className={`mode-tab ${mode === 'topic' ? 'mode-tab--active' : ''}`}
                            onClick={() => handleModeSwitch('topic')}
                            disabled={isLoading}
                            aria-selected={mode === 'topic'}
                            role="tab"
                        >
                            <Lightbulb size={15} strokeWidth={2} />
                            Ask a Topic
                        </button>
                    </div>

                    {/* ── Input Panel (animated swap) ─────────────── */}
                    <AnimatePresence mode="wait">
                        {mode === 'text' ? (
                            <motion.div
                                key="text-panel"
                                className="input-group"
                                initial={{ opacity: 0, x: -12 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 12 }}
                                transition={{ duration: 0.2 }}
                            >
                                {/* Label + Voice button */}
                                <div className="input-label-row">
                                    <label htmlFor="content-input" className="input-label">
                                        Your Content
                                    </label>
                                    {voiceSupported && (
                                        <button
                                            type="button"
                                            className={`voice-btn ${isListening ? 'voice-btn--active' : ''}`}
                                            onClick={toggleListening}
                                            disabled={isLoading}
                                            title={isListening ? 'Stop listening' : 'Voice input'}
                                        >
                                            {isListening
                                                ? <MicOff size={13} strokeWidth={2} />
                                                : <Mic    size={13} strokeWidth={2} />
                                            }
                                            <span className="voice-btn__label">
                                                {isListening ? 'Listening…' : 'Voice Input'}
                                            </span>
                                        </button>
                                    )}
                                </div>

                                {/* Textarea */}
                                <div className="textarea-wrapper">
                                    <textarea
                                        id="content-input"
                                        className="textarea"
                                        placeholder="Paste your article, concept, or any text you want explained visually…"
                                        value={text}
                                        onChange={(e) => setText(e.target.value)}
                                        disabled={isLoading}
                                        rows={8}
                                    />
                                    <div
                                        className="char-count"
                                        style={{ color: getCharColor() }}
                                    >
                                        {text.length.toLocaleString()} / {MAX_TEXT_CHARS.toLocaleString()}
                                        {text.length < MIN_TEXT_CHARS && (
                                            <span className="char-count__hint">
                                                {' '}(min {MIN_TEXT_CHARS})
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </motion.div>
                        ) : (
                            <motion.div
                                key="topic-panel"
                                className="input-group"
                                initial={{ opacity: 0, x: 12 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -12 }}
                                transition={{ duration: 0.2 }}
                            >
                                <label htmlFor="topic-input" className="input-label">
                                    Your Topic or Question
                                </label>

                                <input
                                    id="topic-input"
                                    type="text"
                                    className="topic-input"
                                    placeholder="e.g., Explain quantum computing, How does machine learning work?, What is blockchain?"
                                    value={topic}
                                    onChange={(e) => setTopic(e.target.value)}
                                    disabled={isLoading}
                                    maxLength={2000}
                                    autoFocus
                                />

                                {/* Example topic chips */}
                                <div className="topic-chips">
                                    <span className="topic-chips__label">Try:</span>
                                    {EXAMPLE_TOPICS.map((t) => (
                                        <button
                                            key={t}
                                            type="button"
                                            className={`topic-chip ${topic === t ? 'topic-chip--active' : ''}`}
                                            onClick={() => setTopic(t)}
                                            disabled={isLoading}
                                        >
                                            {t}
                                        </button>
                                    ))}
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* ── Duration ────────────────────────────────── */}
                    <div className="input-group">
                        <label className="input-label">Duration</label>
                        <div className="duration-options">
                            {DURATION_OPTIONS.map((opt) => (
                                <button
                                    key={opt.value}
                                    type="button"
                                    className={`duration-option ${duration === opt.value ? 'duration-option--active' : ''}`}
                                    onClick={() => setDuration(opt.value)}
                                    disabled={isLoading}
                                >
                                    <span className="duration-option__label">{opt.label}</span>
                                    <span className="duration-option__description">{opt.description}</span>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* ── Avatar Toggle ───────────────────────────── */}
                    <div className="input-group">
                        <label className="input-label">Avatar</label>
                        <div className="toggle-container">
                            <button
                                type="button"
                                className={`toggle ${avatarEnabled ? 'toggle--active' : ''}`}
                                onClick={() => setAvatarEnabled(!avatarEnabled)}
                                disabled={isLoading}
                                aria-label={`Avatar ${avatarEnabled ? 'enabled' : 'disabled'}`}
                            >
                                <span className="toggle__switch" />
                            </button>
                            <span className="toggle__label">
                                {avatarEnabled ? 'Enabled' : 'Disabled'}
                            </span>
                        </div>
                    </div>

                    {/* ── Custom Instruction (collapsible) ────────── */}
                    <div className="input-group">
                        <button
                            type="button"
                            className="instruction-toggle"
                            onClick={() => setShowInstruction(!showInstruction)}
                            disabled={isLoading}
                        >
                            <span className="instruction-toggle__icon">
                                {showInstruction
                                    ? <ChevronUp  size={14} strokeWidth={2.5} />
                                    : <ChevronDown size={14} strokeWidth={2.5} />
                                }
                            </span>
                            Add custom instruction
                        </button>

                        <AnimatePresence>
                            {showInstruction && (
                                <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: 'auto' }}
                                    exit={{ opacity: 0, height: 0 }}
                                    transition={{ duration: 0.2 }}
                                >
                                    <input
                                        type="text"
                                        className="text-input"
                                        placeholder="e.g., Explain like I'm 5, Use technical terms, Focus on practical examples…"
                                        value={instruction}
                                        onChange={(e) => setInstruction(e.target.value)}
                                        disabled={isLoading}
                                        maxLength={2000}
                                    />
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>

                    {/* ── Submit Button ────────────────────────────── */}
                    <motion.button
                        type="submit"
                        className={`submit-button ${!canSubmit ? 'submit-button--disabled' : ''}`}
                        disabled={!canSubmit}
                        whileHover={canSubmit ? { scale: 1.02 } : {}}
                        whileTap={canSubmit  ? { scale: 0.98 } : {}}
                    >
                        {isLoading ? (
                            <span className="submit-button__loading">
                                <Loader2 size={18} strokeWidth={2} className="spinner-icon" />
                                Generating…
                            </span>
                        ) : mode === 'topic' ? (
                            <>
                                <Lightbulb size={18} strokeWidth={2} />
                                Explain This Topic
                                <ArrowRight size={16} strokeWidth={2.5} />
                            </>
                        ) : (
                            <>
                                <Sparkles size={18} strokeWidth={2} />
                                Explain
                            </>
                        )}
                    </motion.button>
                </div>
            </motion.form>

            {/* Footer hint */}
            <motion.p
                className="input-section__hint"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
            >
                Powered by AI • Takes about 30–60 seconds
            </motion.p>
        </motion.div>
    );
}

export default InputSection;
