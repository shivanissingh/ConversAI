import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Image, Loader2, AlertCircle } from 'lucide-react';
import './VisualDisplay.css';

/**
 * VisualDisplay Component
 * Renders Pollinations.ai AI-generated images with headline overlay.
 *
 * Key behavior:
 *  - Shows shimmer while Pollinations generates the image (can take 5-30s on first load)
 *  - Retries up to 3 times if image fails (network hiccup, generation timeout)
 *  - Shows headline overlay once image is loaded
 *  - Pre-loads the next segment's image in background
 */
function VisualDisplay({ visual, segmentText, segmentIndex, allVisuals }) {
    // Pre-load next segment's image in background for smooth transitions
    useEffect(() => {
        if (!allVisuals) return;
        const nextVisual = allVisuals[segmentIndex + 1];
        if (nextVisual?.url) {
            const img = new window.Image();
            img.src = nextVisual.url;
        }
    }, [segmentIndex, allVisuals]);

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
 * ImagePanel — renders a single AI-generated image with retry logic.
 * Pollinations.ai can take 5-30s on first generation, so we show
 * an animated shimmer and retry on failure.
 */
function ImagePanel({ visual, segmentIndex }) {
    const [loaded, setLoaded] = useState(false);
    const [error, setError] = useState(false);
    const [retryCount, setRetryCount] = useState(0);
    const [imgSrc, setImgSrc] = useState(visual.url);
    const MAX_RETRIES = 3;
    const retryTimerRef = useRef(null);

    // Reset state when visual changes (new segment)
    useEffect(() => {
        setLoaded(false);
        setError(false);
        setRetryCount(0);
        setImgSrc(visual.url);
    }, [visual.url]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (retryTimerRef.current) clearTimeout(retryTimerRef.current);
        };
    }, []);

    const handleError = () => {
        if (retryCount < MAX_RETRIES) {
            // Retry with cache-busting after a delay
            const delay = (retryCount + 1) * 3000; // 3s, 6s, 9s
            retryTimerRef.current = setTimeout(() => {
                const cacheBust = `&_retry=${retryCount + 1}&_t=${Date.now()}`;
                setImgSrc(visual.url + cacheBust);
                setRetryCount(prev => prev + 1);
            }, delay);
        } else {
            setError(true);
        }
    };

    return (
        <motion.div
            className="visual-display__image-container"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 1.02 }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
        >
            {/* Loading shimmer — visible while image is generating */}
            {!loaded && !error && (
                <div className="visual-display__loading-shimmer">
                    <Loader2
                        className="visual-display__loading-icon"
                        size={32}
                        strokeWidth={1.5}
                    />
                    <span className="visual-display__loading-text">
                        {retryCount > 0
                            ? `Generating visual... (attempt ${retryCount + 1}/${MAX_RETRIES + 1})`
                            : 'Generating visual...'}
                    </span>
                    <span className="visual-display__loading-subtext">
                        AI images take 5–30 seconds on first generation
                    </span>
                </div>
            )}

            {/* Error state — shown after all retries exhausted */}
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
                    src={imgSrc}
                    alt={visual.headline || 'Visual explanation'}
                    className={`visual-display__image ${loaded ? 'visual-display__image--loaded' : ''}`}
                    onLoad={() => setLoaded(true)}
                    onError={handleError}
                    crossOrigin="anonymous"
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
