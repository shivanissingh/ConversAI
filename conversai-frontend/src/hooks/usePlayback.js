import useAudio from './useAudio';
import useSegmentSync from './useSegmentSync';
import useAvatarSync from './useAvatarSync';

/**
 * Combined playback hook that orchestrates audio, segments, and avatar.
 * This is the main hook for the PlaybackView component.
 * 
 * @param {Object} response - API response containing audio, segments, avatar
 * @returns {Object} Complete playback state and controls
 */
export function usePlayback(response) {
    // Audio playback
    const audio = useAudio(response?.audio, true);

    // Segment synchronization
    const segment = useSegmentSync(response?.segments, audio.currentTime);

    // Avatar synchronization
    const avatar = useAvatarSync(response?.avatar, audio.currentTime, audio.isPlaying);

    return {
        // Audio state
        isPlaying: audio.isPlaying,
        isLoaded: audio.isLoaded,
        currentTime: audio.currentTime,
        duration: audio.duration,
        progress: audio.progress,
        audioError: audio.error,
        speed: audio.speed,

        // Audio controls
        toggle: audio.toggle,
        play: audio.play,
        pause: audio.pause,
        seek: audio.seek,
        replay: audio.replay,
        setSpeed: audio.setSpeed,

        // Segment state
        currentSegment: segment.currentSegment,
        currentVisual: segment.currentVisual,
        currentSegmentIndex: segment.currentIndex,
        segmentProgress: segment.segmentProgress,
        totalSegments: segment.totalSegments,

        // Avatar state
        avatarState: avatar.state,
        avatarIntensity: avatar.intensity,
        avatarAnimationSpeed: avatar.animationSpeed,
        shouldAnimateAvatar: avatar.shouldAnimate,
        avatarScaleFactor: avatar.scaleFactor,
        hasAvatar: avatar.hasAvatar,

        // Raw API response data
        narration: response?.narration,
        metadata: response?.metadata,
    };
}

export { useAudio, useSegmentSync, useAvatarSync };
export default usePlayback;
