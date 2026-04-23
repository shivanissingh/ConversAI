import { motion } from 'framer-motion';
import './Avatar.css';

/**
 * Avatar Component - V1 FINAL
 * Symbolic conversational orb with breathing and intensity-based animations.
 * Brand-driven (purple gradient), calm, premium, Notion-AI-like.
 * NO Lottie - Pure SVG + Framer Motion.
 */
function Avatar({
    shouldAnimate = false,
    animationSpeed = 1,
    scaleFactor = 1,
    intensity = 'medium',
    playbackSpeed = 1,
}) {
    // Intensity mapping for speaking states
    const intensityConfig = {
        low: {
            pulseScale: 1.05,
            glowOpacity: 0.4,
            duration: 2.5,
        },
        medium: {
            pulseScale: 1.08,
            glowOpacity: 0.6,
            duration: 1.8,
        },
        high: {
            pulseScale: 1.12,
            glowOpacity: 0.8,
            duration: 1.2,
        },
    };

    const config = intensityConfig[intensity] || intensityConfig.medium;

    // Adjust durations based on playback speed
    const pulseDuration = config.duration / playbackSpeed;
    const breathingDuration = 4 / playbackSpeed;

    return (
        <motion.div
            className="avatar"
            animate={{ scale: scaleFactor }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
        >
            <div className="avatar__orb-container">
                <svg
                    viewBox="0 0 200 200"
                    className="avatar__svg"
                    xmlns="http://www.w3.org/2000/svg"
                >
                    {/* Gradient Definitions */}
                    <defs>
                        {/* Primary Gradient - Purple Brand */}
                        <radialGradient id="orbGradient" cx="40%" cy="40%">
                            <stop offset="0%" stopColor="#a78bfa" />
                            <stop offset="50%" stopColor="#7c3aed" />
                            <stop offset="100%" stopColor="#5b21b6" />
                        </radialGradient>

                        {/* Glow Gradient */}
                        <radialGradient id="glowGradient" cx="50%" cy="50%">
                            <stop
                                offset="0%"
                                stopColor="#7c3aed"
                                stopOpacity={shouldAnimate ? config.glowOpacity : 0.2}
                            />
                            <stop
                                offset="60%"
                                stopColor="#a78bfa"
                                stopOpacity={shouldAnimate ? config.glowOpacity * 0.5 : 0.1}
                            />
                            <stop offset="100%" stopColor="transparent" stopOpacity="0" />
                        </radialGradient>

                        {/* Inner Highlight Gradient */}
                        <radialGradient id="highlightGradient" cx="30%" cy="30%">
                            <stop offset="0%" stopColor="rgba(255, 255, 255, 0.4)" />
                            <stop offset="100%" stopColor="rgba(255, 255, 255, 0)" />
                        </radialGradient>
                    </defs>

                    {/* Outer Glow Layer - Pulsing when speaking */}
                    <motion.circle
                        cx="100"
                        cy="100"
                        r="85"
                        fill="url(#glowGradient)"
                        animate={shouldAnimate ? {
                            scale: [1, 1.08, 1],
                            opacity: [0.6, 1, 0.6],
                        } : {
                            scale: [1, 1.02, 1],
                            opacity: [0.3, 0.4, 0.3],
                        }}
                        transition={{
                            duration: shouldAnimate ? pulseDuration : breathingDuration,
                            repeat: Infinity,
                            ease: 'easeInOut',
                        }}
                    />

                    {/* Main Orb - Core sphere */}
                    <motion.circle
                        cx="100"
                        cy="100"
                        r="50"
                        fill="url(#orbGradient)"
                        animate={shouldAnimate ? {
                            scale: [1, config.pulseScale, 1],
                        } : {
                            scale: [1, 1.03, 1],
                        }}
                        transition={{
                            duration: shouldAnimate ? pulseDuration : breathingDuration,
                            repeat: Infinity,
                            ease: 'easeInOut',
                        }}
                    />

                    {/* Inner Highlight - Depth effect */}
                    <motion.ellipse
                        cx="85"
                        cy="80"
                        rx="25"
                        ry="20"
                        fill="url(#highlightGradient)"
                        animate={{
                            opacity: [0.6, 0.8, 0.6],
                        }}
                        transition={{
                            duration: breathingDuration / 2,
                            repeat: Infinity,
                            ease: 'easeInOut',
                        }}
                    />

                    {/* Subtle Ring - Adds dimension */}
                    <motion.circle
                        cx="100"
                        cy="100"
                        r="50"
                        fill="none"
                        stroke="rgba(167, 139, 250, 0.3)"
                        strokeWidth="1"
                        animate={shouldAnimate ? {
                            scale: [1, 1.15, 1],
                            opacity: [0.3, 0.6, 0.3],
                        } : {
                            scale: [1, 1.05, 1],
                            opacity: [0.2, 0.3, 0.2],
                        }}
                        transition={{
                            duration: shouldAnimate ? pulseDuration * 1.2 : breathingDuration * 1.2,
                            repeat: Infinity,
                            ease: 'easeInOut',
                        }}
                    />

                    {/* Energy Particles - Speaking only */}
                    {shouldAnimate && (
                        <>
                            <motion.circle
                                cx="70"
                                cy="100"
                                r="3"
                                fill="#a78bfa"
                                animate={{
                                    x: [-10, 10, -10],
                                    y: [0, -5, 0],
                                    opacity: [0.4, 0.8, 0.4],
                                }}
                                transition={{
                                    duration: pulseDuration * 0.8,
                                    repeat: Infinity,
                                    ease: 'easeInOut',
                                }}
                            />
                            <motion.circle
                                cx="130"
                                cy="100"
                                r="3"
                                fill="#7c3aed"
                                animate={{
                                    x: [10, -10, 10],
                                    y: [0, 5, 0],
                                    opacity: [0.4, 0.8, 0.4],
                                }}
                                transition={{
                                    duration: pulseDuration * 0.8,
                                    repeat: Infinity,
                                    ease: 'easeInOut',
                                    delay: 0.2,
                                }}
                            />
                        </>
                    )}
                </svg>
            </div>
        </motion.div>
    );
}

export default Avatar;
