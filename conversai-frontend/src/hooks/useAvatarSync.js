import { useState, useEffect, useMemo } from 'react';

/**
 * Hook to synchronize avatar animation state with audio playback.
 * Maps currentTime to avatar states and derives animation parameters.
 * 
 * @param {Object} avatarData - Avatar data from API response
 * @param {number} currentTime - Current audio playback time in seconds
 * @param {boolean} isPlaying - Whether audio is currently playing
 * @returns {Object} Avatar animation state and parameters
 */
export function useAvatarSync(avatarData, currentTime, isPlaying) {
    const [currentState, setCurrentState] = useState({
        state: 'idle',
        intensity: 'low',
    });

    // Find current avatar state based on time
    useEffect(() => {
        if (!avatarData?.states || !isPlaying) {
            setCurrentState({ state: 'idle', intensity: 'low' });
            return;
        }

        const state = avatarData.states.find(
            (s) => currentTime >= s.startTime && currentTime < s.endTime
        );

        if (state) {
            setCurrentState({
                state: state.state,
                intensity: state.intensity,
            });
        } else {
            // Default to idle if no matching state
            setCurrentState({ state: 'idle', intensity: 'low' });
        }
    }, [avatarData, currentTime, isPlaying]);

    // Calculate animation speed based on intensity
    const animationSpeed = useMemo(() => {
        if (currentState.state !== 'speaking') return 0;

        switch (currentState.intensity) {
            case 'high':
                return 1.5;
            case 'medium':
                return 1.0;
            case 'low':
            default:
                return 0.7;
        }
    }, [currentState]);

    // Determine if avatar should be animating
    const shouldAnimate = useMemo(() => {
        return isPlaying && currentState.state === 'speaking';
    }, [isPlaying, currentState.state]);

    // Get scale factor based on intensity (for visual emphasis)
    const scaleFactor = useMemo(() => {
        if (!shouldAnimate) return 1;

        switch (currentState.intensity) {
            case 'high':
                return 1.05;
            case 'medium':
                return 1.02;
            case 'low':
            default:
                return 1;
        }
    }, [shouldAnimate, currentState.intensity]);

    // Check for cue at current time
    const currentCue = useMemo(() => {
        if (!avatarData?.cues) return null;

        // Find cue within 0.1s of current time
        return avatarData.cues.find(
            (cue) => Math.abs(cue.timestamp - currentTime) < 0.1
        ) || null;
    }, [avatarData, currentTime]);

    return {
        state: currentState.state,
        intensity: currentState.intensity,
        animationSpeed,
        shouldAnimate,
        scaleFactor,
        currentCue,
        hasAvatar: !!avatarData,
    };
}

export default useAvatarSync;
