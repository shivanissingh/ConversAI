import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BookOpen, PenLine, Image, Mic, Layers, Sparkles, CheckCircle2 } from 'lucide-react';
import './LoadingView.css';

// Pipeline steps that mirror the actual backend execution
const PIPELINE_STEPS = [
    { id: 'analyze', text: 'Analyzing your content', Icon: BookOpen, duration: 45000 },
    { id: 'explain', text: 'Crafting story-driven narration', Icon: PenLine, duration: 45000 },
    { id: 'visuals', text: 'Generating AI visuals', Icon: Image, duration: 45000 },
    { id: 'voice', text: 'Synthesizing natural voice', Icon: Mic, duration: 45000 },
    { id: 'sync', text: 'Synchronizing all components', Icon: Layers, duration: 45000 },
    { id: 'ready', text: 'Preparing your experience', Icon: Sparkles, duration: 45000 },
];

/**
 * LoadingView Component
 * Shows step-by-step pipeline progress with animated transitions.
 * Simulates the actual backend engine execution flow.
 */
function LoadingView() {
    const [currentStep, setCurrentStep] = useState(0);
    const [startTime] = useState(Date.now());
    const [elapsed, setElapsed] = useState(0);

    // Progress through steps based on estimated timings
    useEffect(() => {
        if (currentStep >= PIPELINE_STEPS.length - 1) return;

        const timer = setTimeout(() => {
            setCurrentStep((prev) => Math.min(prev + 1, PIPELINE_STEPS.length - 1));
        }, PIPELINE_STEPS[currentStep].duration);

        return () => clearTimeout(timer);
    }, [currentStep]);

    // Elapsed time counter
    useEffect(() => {
        const interval = setInterval(() => {
            setElapsed(Math.floor((Date.now() - startTime) / 1000));
        }, 1000);
        return () => clearInterval(interval);
    }, [startTime]);

    return (
        <div className="loading-view">
            {/* Background Gradient Animation */}
            <div className="loading-view__background" />

            {/* Floating Particles */}
            <div className="loading-view__particles">
                {[...Array(15)].map((_, i) => (
                    <motion.div
                        key={i}
                        className="particle"
                        initial={{
                            x: Math.random() * 100 - 50,
                            y: Math.random() * 100 - 50,
                            opacity: 0
                        }}
                        animate={{
                            x: Math.random() * 200 - 100,
                            y: -300 - Math.random() * 200,
                            opacity: [0, 0.5, 0],
                        }}
                        transition={{
                            duration: 4 + Math.random() * 3,
                            repeat: Infinity,
                            delay: Math.random() * 2,
                            ease: 'easeOut',
                        }}
                    />
                ))}
            </div>

            {/* Central Orb */}
            <motion.div
                className="loading-view__orb-container"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5 }}
            >
                <div className="loading-view__orb">
                    <motion.div
                        className="loading-view__orb-inner"
                        animate={{
                            scale: [1, 1.1, 1],
                            opacity: [0.8, 1, 0.8],
                        }}
                        transition={{
                            duration: 2,
                            repeat: Infinity,
                            ease: 'easeInOut',
                        }}
                    />
                    <motion.div
                        className="loading-view__orb-ring"
                        animate={{ rotate: 360 }}
                        transition={{
                            duration: 8,
                            repeat: Infinity,
                            ease: 'linear',
                        }}
                    />
                    <motion.div
                        className="loading-view__orb-ring loading-view__orb-ring--secondary"
                        animate={{ rotate: -360 }}
                        transition={{
                            duration: 12,
                            repeat: Infinity,
                            ease: 'linear',
                        }}
                    />
                </div>
            </motion.div>

            {/* Pipeline Steps */}
            <div className="loading-view__pipeline">
                {PIPELINE_STEPS.map((step, i) => {
                    const { Icon } = step;
                    const status = i < currentStep ? 'done' : i === currentStep ? 'active' : 'pending';
                    return (
                        <motion.div
                            key={step.id}
                            className={`loading-view__step loading-view__step--${status}`}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: i * 0.1 }}
                        >
                            <span className="loading-view__step-indicator">
                                {status === 'done' 
                                    ? <CheckCircle2 size={18} className="loading-view__step-done-icon" /> 
                                    : <Icon size={18} className="loading-view__step-icon-svg" />}
                            </span>
                            <span className="loading-view__step-text">{step.text}</span>
                            {status === 'active' && (
                                <motion.span
                                    className="loading-view__step-dots"
                                    animate={{ opacity: [0.3, 1, 0.3] }}
                                    transition={{ duration: 1.5, repeat: Infinity }}
                                >
                                    ...
                                </motion.span>
                            )}
                        </motion.div>
                    );
                })}
            </div>

            {/* Elapsed Timer */}
            <motion.p
                className="loading-view__hint"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1 }}
            >
                <span className="loading-view__timer">{elapsed}s</span> elapsed • Usually takes 240-300 seconds
            </motion.p>
        </div>
    );
}

export default LoadingView;
