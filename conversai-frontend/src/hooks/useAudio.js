import { useState, useRef, useEffect, useCallback } from 'react';

/**
 * Custom hook for managing HTML Audio playback.
 * Handles play/pause, seeking, and time updates.
 * 
 * @param {string} audioSrc - Base64 encoded audio source or URL
 * @param {boolean} autoPlay - Whether to autoplay when loaded
 * @returns {Object} Audio state and control functions
 */
export function useAudio(audioSrc, autoPlay = true) {
    const audioRef = useRef(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [isLoaded, setIsLoaded] = useState(false);
    const [error, setError] = useState(null);
    const [speed, setSpeed] = useState(1);

    // Initialize audio element
    useEffect(() => {
        if (!audioSrc) return;

        const audio = new Audio();
        audioRef.current = audio;

        const handleLoadedMetadata = () => {
            setDuration(audio.duration);
            setIsLoaded(true);
            setError(null);

            if (autoPlay) {
                audio.play()
                    .then(() => setIsPlaying(true))
                    .catch((e) => {
                        console.warn('Autoplay prevented:', e);
                        setIsPlaying(false);
                    });
            }
        };

        const handleTimeUpdate = () => {
            setCurrentTime(audio.currentTime);
        };

        const handleEnded = () => {
            setIsPlaying(false);
            setCurrentTime(audio.duration);
        };

        const handleError = (e) => {
            console.error('Audio error:', e);
            setError('Failed to load audio');
            setIsLoaded(false);
        };

        const handlePlay = () => setIsPlaying(true);
        const handlePause = () => setIsPlaying(false);

        audio.addEventListener('loadedmetadata', handleLoadedMetadata);
        audio.addEventListener('timeupdate', handleTimeUpdate);
        audio.addEventListener('ended', handleEnded);
        audio.addEventListener('error', handleError);
        audio.addEventListener('play', handlePlay);
        audio.addEventListener('pause', handlePause);

        // Set source and load
        audio.src = audioSrc;
        audio.load();

        return () => {
            audio.pause();
            audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
            audio.removeEventListener('timeupdate', handleTimeUpdate);
            audio.removeEventListener('ended', handleEnded);
            audio.removeEventListener('error', handleError);
            audio.removeEventListener('play', handlePlay);
            audio.removeEventListener('pause', handlePause);
            audioRef.current = null;
        };
    }, [audioSrc, autoPlay]);

    // Update playback speed
    useEffect(() => {
        const audio = audioRef.current;
        if (audio) {
            audio.playbackRate = speed;
        }
    }, [speed]);

    // Toggle play/pause
    const toggle = useCallback(() => {
        const audio = audioRef.current;
        if (!audio) return;

        if (isPlaying) {
            audio.pause();
        } else {
            audio.play().catch(console.error);
        }
    }, [isPlaying]);

    // Play
    const play = useCallback(() => {
        const audio = audioRef.current;
        if (audio && !isPlaying) {
            audio.play().catch(console.error);
        }
    }, [isPlaying]);

    // Pause
    const pause = useCallback(() => {
        const audio = audioRef.current;
        if (audio && isPlaying) {
            audio.pause();
        }
    }, [isPlaying]);

    // Seek to specific time
    const seek = useCallback((time) => {
        const audio = audioRef.current;
        if (!audio) return;

        const clampedTime = Math.max(0, Math.min(time, duration));
        audio.currentTime = clampedTime;
        setCurrentTime(clampedTime);
    }, [duration]);

    // Replay from beginning
    const replay = useCallback(() => {
        const audio = audioRef.current;
        if (!audio) return;

        audio.currentTime = 0;
        setCurrentTime(0);
        audio.play()
            .then(() => setIsPlaying(true))
            .catch(console.error);
    }, []);

    // Get progress as percentage (0-100)
    const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

    return {
        audioRef,
        isPlaying,
        isLoaded,
        currentTime,
        duration,
        progress,
        error,
        speed,
        setSpeed,
        toggle,
        play,
        pause,
        seek,
        replay,
    };
}

export default useAudio;
