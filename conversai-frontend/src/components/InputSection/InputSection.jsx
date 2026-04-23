import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import useSpeechRecognition from '../../hooks/useSpeechRecognition';
import './InputSection.css';

const DURATION_OPTIONS = [
    { value: 'short', label: 'Short (~30s)', description: 'Quick overview' },
    { value: 'medium', label: 'Medium (~60s)', description: 'Detailed explanation' },
];

const MIN_CHARS = 100;
const MAX_CHARS = 5000;

/**
 * InputSection Component
 * Large text input with duration selection and optional instruction field.
 */
function InputSection({ onSubmit, isLoading }) {
    const [text, setText] = useState('');
    const [duration, setDuration] = useState('medium');
    const [instruction, setInstruction] = useState('');
    const [showInstruction, setShowInstruction] = useState(false);
    const [avatarEnabled, setAvatarEnabled] = useState(true);

    // Voice input
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
                const separator = prev && !prev.endsWith(' ') ? ' ' : '';
                return prev + separator + transcript;
            });
            resetTranscript();
        }
    }, [transcript, resetTranscript]);

    const charCount = text.length;
    const isValidLength = charCount >= MIN_CHARS && charCount <= MAX_CHARS;
    const canSubmit = isValidLength && !isLoading;

    const getCharCountColor = () => {
        if (charCount < MIN_CHARS) return 'var(--color-text-muted)';
        if (charCount > MAX_CHARS) return 'var(--color-accent-error)';
        return 'var(--color-accent-success)';
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!canSubmit) return;

        onSubmit({
            text: text.trim(),
            duration,
            instruction: instruction.trim() || null,
            avatarEnabled,
        });
    };

    return (
        <motion.div
            className="input-section"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
        >
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
                    Transform any text into an engaging visual explanation
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
                    {/* Main Text Input */}
                    <div className="input-group">
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
                                    <span className="voice-btn__icon">{isListening ? '🔴' : '🎙️'}</span>
                                    <span className="voice-btn__label">
                                        {isListening ? 'Listening...' : 'Voice Input'}
                                    </span>
                                </button>
                            )}
                        </div>
                        <div className="textarea-wrapper">
                            <textarea
                                id="content-input"
                                className="textarea"
                                placeholder="Paste your article, concept, or any text you want explained visually..."
                                value={text}
                                onChange={(e) => setText(e.target.value)}
                                disabled={isLoading}
                                rows={8}
                            />
                            <div
                                className="char-count"
                                style={{ color: getCharCountColor() }}
                            >
                                {charCount.toLocaleString()} / {MAX_CHARS.toLocaleString()}
                                {charCount < MIN_CHARS && (
                                    <span className="char-count__hint">
                                        {' '}(min {MIN_CHARS})
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Duration Selection */}
                    <div className="input-group">
                        <label className="input-label">Duration</label>
                        <div className="duration-options">
                            {DURATION_OPTIONS.map((option) => (
                                <button
                                    key={option.value}
                                    type="button"
                                    className={`duration-option ${duration === option.value ? 'duration-option--active' : ''}`}
                                    onClick={() => setDuration(option.value)}
                                    disabled={isLoading}
                                >
                                    <span className="duration-option__label">{option.label}</span>
                                    <span className="duration-option__description">{option.description}</span>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Avatar Toggle */}
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

                    {/* Optional Instruction Toggle */}
                    <div className="input-group">
                        <button
                            type="button"
                            className="instruction-toggle"
                            onClick={() => setShowInstruction(!showInstruction)}
                            disabled={isLoading}
                        >
                            <span className="instruction-toggle__icon">
                                {showInstruction ? '−' : '+'}
                            </span>
                            Add custom instruction
                        </button>

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
                                    placeholder="e.g., Explain like I'm 5, Use technical terms, Focus on practical examples..."
                                    value={instruction}
                                    onChange={(e) => setInstruction(e.target.value)}
                                    disabled={isLoading}
                                    maxLength={200}
                                />
                            </motion.div>
                        )}
                    </div>

                    {/* Submit Button */}
                    <motion.button
                        type="submit"
                        className={`submit-button ${!canSubmit ? 'submit-button--disabled' : ''}`}
                        disabled={!canSubmit}
                        whileHover={canSubmit ? { scale: 1.02 } : {}}
                        whileTap={canSubmit ? { scale: 0.98 } : {}}
                    >
                        {isLoading ? (
                            <span className="submit-button__loading">
                                <span className="spinner" />
                                Generating...
                            </span>
                        ) : (
                            <>
                                <span className="submit-button__icon">✨</span>
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
                Powered by AI • Takes about 30-60 seconds
            </motion.p>
        </motion.div>
    );
}

export default InputSection;
