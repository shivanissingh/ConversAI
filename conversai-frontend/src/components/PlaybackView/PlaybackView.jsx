import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { usePlayback } from '../../hooks/usePlayback';
import VisualDisplay from '../VisualDisplay/VisualDisplay.jsx';
import AvatarComponent from '../Avatar/AvatarComponent.jsx';
import Controls from '../Controls/Controls.jsx';
import { generateFollowUp } from '../../services/api';
import './PlaybackView.css';

/**
 * PlaybackView Component
 * Main playback experience with synchronized visuals, avatar, and controls.
 */
function PlaybackView({ response, onBack, onFollowUpResponse }) {
    const [followUpText, setFollowUpText] = useState('');
    const [isFollowUpLoading, setIsFollowUpLoading] = useState(false);
    const [followUpError, setFollowUpError] = useState(null);

    const {
        // Audio state
        isPlaying,
        isLoaded,
        currentTime,
        duration,
        progress,
        audioError,
        speed,

        // Audio controls
        toggle,
        seek,
        replay,
        setSpeed,

        // Segment state
        currentSegment,
        currentVisual,
        currentSegmentIndex,
        totalSegments,

        // Avatar state
        shouldAnimateAvatar,
        avatarAnimationSpeed,
        avatarScaleFactor,
        avatarIntensity,
        hasAvatar,

        // Metadata
        metadata,
    } = usePlayback(response);

    // Keyboard shortcuts for playback control
    useEffect(() => {
        const handleKeyDown = (event) => {
            // Ignore if user is typing in an input, textarea, or contentEditable element
            const activeElement = document.activeElement;
            const isTyping =
                activeElement.tagName === 'INPUT' ||
                activeElement.tagName === 'TEXTAREA' ||
                activeElement.isContentEditable;

            if (isTyping) return;

            switch (event.key) {
                case ' ': // Space - Toggle play/pause
                    event.preventDefault(); // Prevent page scroll
                    toggle();
                    break;

                case 'ArrowRight': // Seek forward 5 seconds
                    event.preventDefault();
                    if (duration) {
                        const newTime = Math.min(currentTime + 5, duration);
                        seek(newTime);
                    }
                    break;

                case 'ArrowLeft': // Seek backward 5 seconds
                    event.preventDefault();
                    if (duration) {
                        const newTime = Math.max(currentTime - 5, 0);
                        seek(newTime);
                    }
                    break;

                case 'Enter': // Restart playback
                    event.preventDefault();
                    replay();
                    break;

                default:
                    break;
            }
        };

        // Add event listener when component mounts
        window.addEventListener('keydown', handleKeyDown);

        // Clean up event listener when component unmounts
        return () => {
            window.removeEventListener('keydown', handleKeyDown);
        };
    }, [toggle, seek, replay, currentTime, duration]); // Dependencies for event handler

    return (
        <motion.div
            className="playback-view"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
        >
            {/* Segment Counter - Compact */}
            <motion.div
                className="playback-view__segment-counter"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
            >
                <span className="playback-view__segment-current">{currentSegmentIndex + 1}</span>
                <span className="playback-view__segment-separator">/</span>
                <span className="playback-view__segment-total">{totalSegments}</span>
            </motion.div>

            {/* Main Content */}
            <div className="playback-view__content">
                {/* Visual Display - Main Focus */}
                <motion.div
                    className="playback-view__visual-container"
                    initial={{ opacity: 0, scale: 0.98 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.2 }}
                >
                    <VisualDisplay
                        visual={currentVisual}
                        segmentText={currentSegment?.text}
                        segmentIndex={currentSegmentIndex}
                        allVisuals={response?.segments?.map(s => s.visual)}
                    />
                </motion.div>

                {/* Lottie Avatar — always visible, switches speaking/idle animation */}
                <motion.div
                    className="playback-view__avatar-container"
                    initial={{ opacity: 0, x: 50 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 }}
                >
                    <AvatarComponent
                        isSpeaking={isPlaying}
                        intensity={avatarIntensity || 'medium'}
                    />
                </motion.div>
            </div>

            {/* Controls */}
            <Controls
                isPlaying={isPlaying}
                currentTime={currentTime}
                duration={duration}
                progress={progress}
                speed={speed}
                onToggle={toggle}
                onReplay={replay}
                onSeek={seek}
                onSpeedChange={setSpeed}
            />

            {/* Audio Error Toast */}
            {audioError && (
                <motion.div
                    className="playback-view__error-toast"
                    initial={{ opacity: 0, y: 50 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <span>⚠️ {audioError}</span>
                </motion.div>
            )}

            {/* Follow-up Question Section */}
            <motion.div
                className="playback-view__followup"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
            >
                <div className="playback-view__followup-header">
                    <span className="playback-view__followup-icon">💬</span>
                    <span className="playback-view__followup-label">Ask a follow-up question</span>
                </div>
                <form
                    className="playback-view__followup-form"
                    onSubmit={async (e) => {
                        e.preventDefault();
                        if (!followUpText.trim() || isFollowUpLoading) return;
                        setIsFollowUpLoading(true);
                        setFollowUpError(null);
                        try {
                            const result = await generateFollowUp({
                                originalText: response?.narration || '',
                                followUpQuestion: followUpText.trim(),
                            });
                            // If parent provided callback, use it; otherwise stay on same view
                            if (onFollowUpResponse) {
                                onFollowUpResponse(result);
                            }
                            setFollowUpText('');
                        } catch (err) {
                            setFollowUpError(err.message);
                        } finally {
                            setIsFollowUpLoading(false);
                        }
                    }}
                >
                    <input
                        type="text"
                        className="playback-view__followup-input"
                        placeholder="e.g., Can you explain supervised learning in more detail?"
                        value={followUpText}
                        onChange={(e) => setFollowUpText(e.target.value)}
                        disabled={isFollowUpLoading}
                        maxLength={500}
                    />
                    <button
                        type="submit"
                        className="playback-view__followup-btn"
                        disabled={!followUpText.trim() || isFollowUpLoading}
                    >
                        {isFollowUpLoading ? (
                            <span className="spinner spinner--small" />
                        ) : (
                            '→'
                        )}
                    </button>
                </form>
                <AnimatePresence>
                    {followUpError && (
                        <motion.p
                            className="playback-view__followup-error"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                        >
                            {followUpError}
                        </motion.p>
                    )}
                </AnimatePresence>
            </motion.div>

            {/* Metadata Footer (optional - for debugging/info) */}
            {metadata && (
                <div className="playback-view__metadata">
                    {!metadata.visualSuccess && (
                        <span className="playback-view__metadata-item playback-view__metadata-item--warning">
                            ⚠️ Some visuals unavailable
                        </span>
                    )}
                </div>
            )}
        </motion.div>
    );
}

export default PlaybackView;
