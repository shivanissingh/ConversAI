import { motion } from 'framer-motion';
import {
    Sparkles, Mic, LayoutGrid, ChevronRight,
    Brain, Image, Activity, Zap, RefreshCw,
    MonitorPlay, Smartphone, Clock, CheckCircle2,
    ArrowRight
} from 'lucide-react';
import ThemeToggle from '../ThemeToggle/ThemeToggle.jsx';
import './LandingPage.css';

/**
 * LandingPage Component
 * Premium landing page — first thing examiners see.
 */
function LandingPage({ onGetStarted }) {
    return (
        <div className="landing">
            {/* Theme toggle — top-right, above all content */}
            <div className="landing__theme-toggle">
                <ThemeToggle />
            </div>

            {/* Hero */}
            <section className="landing__hero">
                <motion.div
                    className="landing__hero-content"
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
                >
                    <motion.div
                        className="landing__badge"
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.2 }}
                    >
                        <span className="landing__badge-dot" />
                        AI-Powered Multimodal Explanations
                    </motion.div>

                    <h1 className="landing__title">
                        <span className="landing__title-line">Transform Text Into</span>
                        <span className="landing__title-gradient">Interactive Experiences</span>
                    </h1>

                    <motion.p
                        className="landing__subtitle"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.3 }}
                    >
                        ConversAI converts complex text into story-driven explanations
                        with synchronized AI-generated visuals, natural voice narration,
                        and an interactive digital avatar — making learning as engaging
                        as watching a YouTube video.
                    </motion.p>

                    <motion.div
                        className="landing__cta-group"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.5 }}
                    >
                        <button className="landing__cta-primary" onClick={onGetStarted}>
                            <Sparkles size={18} />
                            Try It Now
                        </button>
                        <a href="#how-it-works" className="landing__cta-secondary">
                            See How It Works
                            <ChevronRight size={16} />
                        </a>
                    </motion.div>
                </motion.div>

                {/* Floating feature cards */}
                <div className="landing__hero-visuals">
                    <motion.div
                        className="landing__float-card landing__float-card--1"
                        animate={{ y: [-5, 5, -5] }}
                        transition={{ duration: 4, repeat: Infinity }}
                    >
                        <Brain size={18} className="landing__float-icon" />
                        <span>AI Analysis</span>
                    </motion.div>
                    <motion.div
                        className="landing__float-card landing__float-card--2"
                        animate={{ y: [5, -5, 5] }}
                        transition={{ duration: 5, repeat: Infinity }}
                    >
                        <Mic size={18} className="landing__float-icon" />
                        <span>Voice Narration</span>
                    </motion.div>
                    <motion.div
                        className="landing__float-card landing__float-card--3"
                        animate={{ y: [-3, 7, -3] }}
                        transition={{ duration: 4.5, repeat: Infinity }}
                    >
                        <Image size={18} className="landing__float-icon" />
                        <span>Smart Visuals</span>
                    </motion.div>
                </div>
            </section>

            {/* Problem Section */}
            <section className="landing__problem">
                <motion.div
                    className="landing__section-content"
                    initial={{ opacity: 0, y: 40 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                >
                    <h2 className="landing__section-title">The Problem We Solve</h2>
                    <div className="landing__stats-grid">
                        {[
                            { num: '79%', label: 'of users skim content instead of reading it fully' },
                            { num: '65%', label: 'are visual learners who struggle with text-only content' },
                            { num: '10x', label: 'faster comprehension with multimodal vs plain text' },
                        ].map((stat, i) => (
                            <motion.div
                                key={i}
                                className="landing__stat-card"
                                whileHover={{ y: -4 }}
                            >
                                <span className="landing__stat-number">{stat.num}</span>
                                <span className="landing__stat-label">{stat.label}</span>
                            </motion.div>
                        ))}
                    </div>
                    <p className="landing__problem-text">
                        AI systems generate massive walls of text. Users are expected to interpret
                        complex explanations without visuals, voice, or guidance.{' '}
                        <strong>ConversAI changes that.</strong>
                    </p>
                </motion.div>
            </section>

            {/* How It Works */}
            <section className="landing__how" id="how-it-works">
                <motion.div
                    className="landing__section-content"
                    initial={{ opacity: 0, y: 40 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                >
                    <h2 className="landing__section-title">How ConversAI Works</h2>
                    <p className="landing__section-subtitle">
                        A 4-engine AI pipeline that transforms any text into a multimedia experience
                    </p>

                    <div className="landing__pipeline">
                        {[
                            { icon: Brain, title: 'Explanation Engine', desc: 'Gemini LLM analyzes your text and creates a story-driven narration broken into segments', color: '#6C63FF' },
                            { icon: Image, title: 'Visual Engine', desc: 'Generates cinematic AI images via Pollinations.ai — one unique visual per narration segment', color: '#00C9A7' },
                            { icon: Mic, title: 'Voice Engine', desc: 'Microsoft Neural TTS converts narration to natural speech with human-like intonation', color: '#FF6B6B' },
                            { icon: Activity, title: 'Aggregation Engine', desc: 'Orchestrates all engines, synchronizes timing, and composes the final multimodal response', color: '#FFD93D' },
                        ].map((step, i) => {
                            const Icon = step.icon;
                            return (
                                <motion.div
                                    key={i}
                                    className="landing__pipeline-step"
                                    initial={{ opacity: 0, x: -20 }}
                                    whileInView={{ opacity: 1, x: 0 }}
                                    viewport={{ once: true }}
                                    transition={{ delay: i * 0.15 }}
                                >
                                    <div className="landing__step-number" style={{ background: step.color }}>
                                        {i + 1}
                                    </div>
                                    <div className="landing__step-icon-wrap" style={{ color: step.color }}>
                                        <Icon size={24} />
                                    </div>
                                    <div className="landing__step-content">
                                        <h3 className="landing__step-title">{step.title}</h3>
                                        <p className="landing__step-desc">{step.desc}</p>
                                    </div>
                                </motion.div>
                            );
                        })}
                    </div>
                </motion.div>
            </section>

            {/* Features */}
            <section className="landing__features">
                <motion.div
                    className="landing__section-content"
                    initial={{ opacity: 0, y: 40 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                >
                    <h2 className="landing__section-title">Key Features</h2>
                    <div className="landing__features-grid">
                        {[
                            { icon: Brain, title: 'Story-Driven Narration', desc: 'Setup → Insight → Takeaway structure that makes any topic click' },
                            { icon: Image, title: 'AI-Generated Visuals', desc: 'Real cinematic images generated by AI, synced to each segment of narration' },
                            { icon: Mic, title: 'Natural Voice', desc: 'Microsoft Neural TTS with human-like intonation, rhythm and emphasis' },
                            { icon: RefreshCw, title: 'Synchronized Playback', desc: 'Visuals, voice, and subtitles perfectly synced — just like a YouTube video' },
                            { icon: Smartphone, title: 'Responsive Design', desc: 'Works beautifully on desktop, tablet, and mobile with adaptive layouts' },
                            { icon: Zap, title: 'Fast Generation', desc: 'Optimized pipeline delivers a complete multimodal explanation in under 60 seconds' },
                        ].map((feature, i) => {
                            const Icon = feature.icon;
                            return (
                                <motion.div
                                    key={i}
                                    className="landing__feature-card"
                                    initial={{ opacity: 0, y: 20 }}
                                    whileInView={{ opacity: 1, y: 0 }}
                                    viewport={{ once: true }}
                                    transition={{ delay: i * 0.1 }}
                                    whileHover={{ y: -4 }}
                                >
                                    <div className="landing__feature-icon-wrap">
                                        <Icon size={22} strokeWidth={1.5} />
                                    </div>
                                    <h3 className="landing__feature-title">{feature.title}</h3>
                                    <p className="landing__feature-desc">{feature.desc}</p>
                                </motion.div>
                            );
                        })}
                    </div>
                </motion.div>
            </section>

            {/* Tech Stack */}
            <section className="landing__tech">
                <motion.div
                    className="landing__section-content"
                    initial={{ opacity: 0, y: 40 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                >
                    <h2 className="landing__section-title">Built With</h2>
                    <div className="landing__tech-grid">
                        {[
                            'React + Vite', 'Python FastAPI', 'Google Gemini',
                            'Microsoft Neural TTS', 'Pollinations.ai', 'Framer Motion',
                            'TalkingHead.js', 'WebSpeech API', 'SQLite'
                        ].map((tech, i) => (
                            <motion.span
                                key={i}
                                className="landing__tech-badge"
                                initial={{ opacity: 0, scale: 0.9 }}
                                whileInView={{ opacity: 1, scale: 1 }}
                                viewport={{ once: true }}
                                transition={{ delay: i * 0.05 }}
                            >
                                {tech}
                            </motion.span>
                        ))}
                    </div>
                </motion.div>
            </section>

            {/* Final CTA */}
            <section className="landing__final-cta">
                <motion.div
                    className="landing__section-content"
                    initial={{ opacity: 0, y: 40 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                >
                    <h2 className="landing__cta-title">Ready to Transform Your Content?</h2>
                    <p className="landing__cta-subtitle">
                        Paste any text and watch it come alive as an interactive explanation.
                    </p>
                    <button className="landing__cta-primary landing__cta-primary--large" onClick={onGetStarted}>
                        <Sparkles size={20} />
                        Get Started — It's Free
                    </button>
                </motion.div>
            </section>

            {/* Footer */}
            <footer className="landing__footer">
                <div className="landing__footer-content">
                    <span className="landing__footer-brand">ConversAI</span>
                    <span className="landing__footer-meta">
                        BE Major Project — Atharva College of Engineering, Mumbai
                    </span>
                    <span className="landing__footer-year">© 2026</span>
                </div>
            </footer>
        </div>
    );
}

export default LandingPage;
