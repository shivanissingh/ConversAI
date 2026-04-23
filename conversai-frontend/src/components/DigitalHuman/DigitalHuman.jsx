import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { User2, Loader2, AlertCircle } from 'lucide-react';
import './DigitalHuman.css';

/**
 * DigitalHuman Component — TalkingHead.js 3D Avatar with Real-Time Lip-Sync
 *
 * Uses TalkingHead.js (met4citizen/TalkingHead) which renders a WebGL scene with:
 *  - A Ready Player Me GLB avatar
 *  - Real-time lip-sync from audio data
 *  - Idle animations: blinking, breathing, micro-expressions
 *
 * The module is served from /public/talkinghead/ to avoid Vite module bundling issues.
 * Audio is the base64 MP3 from the backend — decoded and fed to TalkingHead's speakAudio().
 *
 * Props:
 *   audioBase64  - Base64 MP3 string from backend API
 *   isPlaying    - Whether playback is active
 */
function DigitalHuman({ audioBase64, isPlaying }) {
    const containerRef = useRef(null);
    const headRef = useRef(null);
    const [status, setStatus] = useState('idle'); // idle | loading | ready | error
    const [loadProgress, setLoadProgress] = useState(0);
    const lastAudioRef = useRef(null);
    const speakingRef = useRef(false);

    // Initialize TalkingHead on mount — import from /public/ to bypass Vite bundling
    useEffect(() => {
        let cancelled = false;
        let head = null;

        async function initAvatar() {
            if (!containerRef.current) return;
            setStatus('loading');
            setLoadProgress(0);

            try {
                // Import TalkingHead via @talkinghead alias (defined in vite.config.js)
                // pointing to src/vendor/talkinghead/. Vite resolves the alias but
                // doesn't pre-bundle it (excluded in optimizeDeps) so its internal
                // dynamic imports of lipsync-en.mjs, dynamicbones.mjs work at runtime.
                const { TalkingHead } = await import(
                    /* @vite-ignore */
                    '@talkinghead/talkinghead.mjs'
                );

                if (cancelled) return;
                setLoadProgress(20);

                head = new TalkingHead(containerRef.current, {
                    ttsEndpoint: null,          // No built-in TTS — we provide audio
                    lipsyncModules: ['en'],     // English lip-sync
                    cameraView: 'upper',        // Head + shoulders view
                    cameraDistance: 1.3,
                    cameraX: 0.05,
                    cameraY: 0.1,
                    lightAmbientColor: 0xffffff,
                    lightAmbientIntensity: 3,
                    lightDirectionalColor: 0xffffff,
                    lightDirectionalIntensity: 5,
                });

                headRef.current = head;
                setLoadProgress(40);

                // Use TalkingHead's built-in example avatar (always accessible)
                // This is a Google sample avatar hosted on their CDN
                const AVATAR_URL = 'https://models.readyplayer.me/64bfa15f0e72c63d7c3934a6.glb'
                    + '?morphTargets=ARKit,Oculus+Visemes&textureAtlas=1024';

                await head.showAvatar(
                    {
                        url: AVATAR_URL,
                        body: 'F',
                        avatarMood: 'neutral',
                        ttsLang: 'en-US',
                        ttsVoice: 'en-US-AriaNeural',
                        lipsyncLang: 'en',
                    },
                    (progress) => {
                        if (!cancelled) {
                            setLoadProgress(40 + Math.round(progress * 55));
                        }
                    }
                );

                if (cancelled) return;
                setLoadProgress(100);
                setStatus('ready');

            } catch (err) {
                console.error('[DigitalHuman] Init failed:', err);
                if (!cancelled) setStatus('error');
            }
        }

        initAvatar();

        return () => {
            cancelled = true;
            if (head) {
                try { head.stopSpeaking?.(); } catch (_) {}
                try { head.dispose?.(); } catch (_) {}
            }
            headRef.current = null;
            speakingRef.current = false;
        };
    }, []);

    // Drive lip-sync when audio/playing state changes
    useEffect(() => {
        const head = headRef.current;
        if (!head || status !== 'ready') return;

        // Stop if not playing or no audio
        if (!isPlaying || !audioBase64) {
            if (speakingRef.current) {
                try { head.stopSpeaking?.(); } catch (_) {}
                speakingRef.current = false;
            }
            return;
        }

        // Don't re-trigger if same audio and already speaking
        if (lastAudioRef.current === audioBase64 && speakingRef.current) return;
        lastAudioRef.current = audioBase64;

        async function driveAudio() {
            try {
                // Decode base64 MP3 → ArrayBuffer
                const binaryStr = atob(audioBase64);
                const bytes = new Uint8Array(binaryStr.length);
                for (let i = 0; i < binaryStr.length; i++) {
                    bytes[i] = binaryStr.charCodeAt(i);
                }

                speakingRef.current = true;
                await head.speakAudio(
                    bytes.buffer,
                    { avatarMood: 'neutral' },
                    () => { speakingRef.current = false; }
                );
            } catch (err) {
                console.error('[DigitalHuman] speakAudio failed:', err);
                speakingRef.current = false;
            }
        }

        driveAudio();
    }, [audioBase64, isPlaying, status]);

    return (
        <div className="digital-human">
            {/* Three.js WebGL canvas — rendered by TalkingHead */}
            <div
                ref={containerRef}
                className={`digital-human__canvas ${status === 'ready' ? 'digital-human__canvas--visible' : ''}`}
            />

            {/* Loading overlay */}
            <AnimatePresence>
                {status === 'loading' && (
                    <motion.div
                        className="digital-human__overlay"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.3 }}
                    >
                        <div className="digital-human__avatar-placeholder">
                            <User2 size={40} strokeWidth={1} className="digital-human__placeholder-icon" />
                        </div>
                        <div className="digital-human__loading-info">
                            <Loader2 size={14} className="digital-human__spinner" />
                            <span>Loading avatar {loadProgress}%</span>
                        </div>
                        <div className="digital-human__progress-bar">
                            <motion.div
                                className="digital-human__progress-fill"
                                animate={{ width: `${loadProgress}%` }}
                                transition={{ duration: 0.4 }}
                            />
                        </div>
                    </motion.div>
                )}

                {status === 'error' && (
                    <motion.div
                        className="digital-human__overlay digital-human__overlay--error"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                    >
                        <AlertCircle size={28} strokeWidth={1.5} className="digital-human__error-icon" />
                        <p className="digital-human__error-text">Avatar unavailable</p>
                        <p className="digital-human__error-hint">Check browser console for details</p>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

export default DigitalHuman;
