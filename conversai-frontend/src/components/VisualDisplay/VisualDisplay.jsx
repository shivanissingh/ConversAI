import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Image, AlertCircle } from 'lucide-react';
import './VisualDisplay.css';

/**
 * VisualDisplay Component
 * Renders AI-generated images (delivered as base64 data URIs from the backend).
 *
 * Because images arrive as embedded base64 strings, they load immediately
 * without any network round-trip to Pollinations — no retry logic needed.
 */
function VisualDisplay({ visual, segmentText, segmentIndex, allVisuals }) {
    return (
        <div className="visual-display">
            <div className="visual-display__image-wrapper">
                <AnimatePresence mode="wait">
                    {visual?.url ? (
                        <ImagePanel
                            key={`img-${segmentIndex}`}
                            visual={visual}
                            segmentIndex={segmentIndex}
                        />
                    ) : (
                        <motion.div
                            key="placeholder"
                            className="visual-display__placeholder"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.3 }}
                        >
                            <Image className="visual-display__placeholder-icon" size={48} strokeWidth={1} />
                            <p className="visual-display__placeholder-text">
                                Visuals will appear here
                            </p>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            {/* Segment narration text below the image */}
            <AnimatePresence mode="wait">
                {segmentText && (
                    <motion.div
                        key={`text-${segmentIndex}`}
                        className="visual-display__text-panel"
                        initial={{ opacity: 0, y: 15 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.4, ease: 'easeOut' }}
                    >
                        <p className="visual-display__segment-text">{segmentText}</p>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

/**
 * ImagePanel — renders a single base64-embedded image.
 * No retry logic is needed because the image data is already fully embedded
 * by the backend before the response is returned to the frontend.
 */
function ImagePanel({ visual, segmentIndex }) {
    const [loaded, setLoaded] = useState(false);
    const [error, setError] = useState(false);
    const imgRef = useRef(null);

    // Reset state when visual changes (new segment)
    // For base64 data URIs, the browser may decode the image synchronously
    // before React attaches onLoad — so we also check img.complete after mount.
    useEffect(() => {
        setLoaded(false);
        setError(false);

        const raf = requestAnimationFrame(() => {
            if (imgRef.current?.complete && imgRef.current?.naturalWidth > 0) {
                setLoaded(true);
            }
        });
        return () => cancelAnimationFrame(raf);
    }, [visual.url]);

    return (
        <motion.div
            className="visual-display__image-container"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 1.02 }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
        >
            {/* Error state */}
            {error && (
                <div className="visual-display__error-state">
                    <div className="visual-display__error-fallback"
                         style={{ background: `linear-gradient(135deg, #1a1040 0%, #2d1b69 50%, #1a1040 100%)` }}>
                        <AlertCircle size={28} strokeWidth={1.5} className="visual-display__error-icon" />
                        {visual.headline && (
                            <p className="visual-display__error-headline">{visual.headline}</p>
                        )}
                        {visual.imagePrompt && (
                            <p className="visual-display__error-prompt">
                                {visual.imagePrompt.substring(0, 120)}...
                            </p>
                        )}
                    </div>
                </div>
            )}

            {/* Actual image — always rendered (hidden until loaded) */}
            {!error && (
                <img
                    ref={imgRef}
                    src={visual.url}
                    alt={visual.headline || 'Visual explanation'}
                    className={`visual-display__image ${loaded ? 'visual-display__image--loaded' : ''}`}
                    onLoad={() => setLoaded(true)}
                    onError={() => setError(true)}
                    loading="eager"
                />
            )}

            {/* Headline overlay — appears after image loads */}
            {loaded && visual.headline && (
                <motion.div
                    className="visual-display__headline-overlay"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                >
                    {visual.headline}
                </motion.div>
            )}

            {/* Segment counter badge */}
            <div className="visual-display__segment-badge">
                {segmentIndex + 1}
            </div>
        </motion.div>
    );
}

export default VisualDisplay;
