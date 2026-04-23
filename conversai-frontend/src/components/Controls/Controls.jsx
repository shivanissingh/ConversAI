import { motion } from 'framer-motion';
import './Controls.css';

/**
 * Controls Component
 * Playback controls with play/pause, replay, and progress bar.
 */
function Controls({
    isPlaying,
    currentTime,
    duration,
    progress,
    speed = 1,
    onToggle,
    onReplay,
    onSeek,
    onSpeedChange,
}) {
    const handleProgressClick = (e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        const clickPosition = (e.clientX - rect.left) / rect.width;
        const newTime = clickPosition * duration;
        onSeek(newTime);
    };

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    return (
        <motion.div
            className="controls"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
        >
            <div className="controls__container">
                {/* Progress Bar */}
                <div
                    className="controls__progress-container"
                    onClick={handleProgressClick}
                    role="slider"
                    aria-label="Seek"
                    aria-valuenow={currentTime}
                    aria-valuemin={0}
                    aria-valuemax={duration}
                    tabIndex={0}
                >
                    <div className="controls__progress-track">
                        <motion.div
                            className="controls__progress-fill"
                            style={{ width: `${progress}%` }}
                            layoutId="progress"
                        />
                        <motion.div
                            className="controls__progress-handle"
                            style={{ left: `${progress}%` }}
                            whileHover={{ scale: 1.3 }}
                            whileTap={{ scale: 1.1 }}
                        />
                    </div>
                </div>

                {/* Time Display */}
                <div className="controls__time">
                    <span className="controls__time-current">{formatTime(currentTime)}</span>
                    <span className="controls__time-separator">/</span>
                    <span className="controls__time-total">{formatTime(duration)}</span>
                </div>

                {/* Playback Speed */}
                {onSpeedChange && (
                    <div className="controls__speed">
                        <label className="controls__speed-label">Speed</label>
                        <div className="controls__speed-options">
                            {[0.75, 1, 1.25, 1.5].map((s) => (
                                <button
                                    key={s}
                                    className={`controls__speed-option ${speed === s ? 'controls__speed-option--active' : ''}`}
                                    onClick={() => onSpeedChange(s)}
                                >
                                    {s}x
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {/* Buttons */}
                <div className="controls__buttons">
                    {/* Replay Button */}
                    <motion.button
                        className="controls__button controls__button--secondary"
                        onClick={onReplay}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        aria-label="Replay"
                    >
                        <svg className="controls__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M3 12a9 9 0 1 1 9 9" />
                            <path d="M3 12V6" />
                            <path d="M3 12H9" />
                        </svg>
                    </motion.button>

                    {/* Play/Pause Button */}
                    <motion.button
                        className="controls__button controls__button--primary"
                        onClick={onToggle}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        aria-label={isPlaying ? 'Pause' : 'Play'}
                    >
                        {isPlaying ? (
                            <svg className="controls__icon" viewBox="0 0 24 24" fill="currentColor">
                                <rect x="6" y="4" width="4" height="16" rx="1" />
                                <rect x="14" y="4" width="4" height="16" rx="1" />
                            </svg>
                        ) : (
                            <svg className="controls__icon" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M8 5.14v14.72a1 1 0 0 0 1.5.86l11-7.36a1 1 0 0 0 0-1.72l-11-7.36A1 1 0 0 0 8 5.14z" />
                            </svg>
                        )}
                    </motion.button>
                </div>
            </div>
        </motion.div>
    );
}

export default Controls;
