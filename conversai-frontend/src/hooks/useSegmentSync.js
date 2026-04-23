import { useState, useEffect, useMemo } from 'react';

/**
 * Hook to synchronize current segment and visual with audio currentTime.
 * 
 * @param {Array} segments - Array of segment objects with startTime, endTime, visual
 * @param {number} currentTime - Current audio playback time in seconds
 * @returns {Object} Current segment and visual information
 */
export function useSegmentSync(segments, currentTime) {
    const [currentIndex, setCurrentIndex] = useState(0);

    // Find current segment based on time
    useEffect(() => {
        if (!segments || segments.length === 0) return;

        const index = segments.findIndex(
            (seg) => currentTime >= seg.startTime && currentTime < seg.endTime
        );

        // If we're past the last segment, stay on the last one
        if (index === -1 && currentTime >= segments[segments.length - 1]?.endTime) {
            setCurrentIndex(segments.length - 1);
        } else if (index !== -1 && index !== currentIndex) {
            setCurrentIndex(index);
        }
    }, [segments, currentTime, currentIndex]);

    // Memoize current segment and visual
    const currentSegment = useMemo(() => {
        if (!segments || segments.length === 0) return null;
        return segments[currentIndex] || segments[0];
    }, [segments, currentIndex]);

    const currentVisual = useMemo(() => {
        return currentSegment?.visual || null;
    }, [currentSegment]);

    // Calculate segment progress (0-100)
    const segmentProgress = useMemo(() => {
        if (!currentSegment) return 0;
        const { startTime, endTime } = currentSegment;
        const segmentDuration = endTime - startTime;
        if (segmentDuration <= 0) return 0;

        const elapsed = currentTime - startTime;
        return Math.min(100, Math.max(0, (elapsed / segmentDuration) * 100));
    }, [currentSegment, currentTime]);

    return {
        currentSegment,
        currentVisual,
        currentIndex,
        segmentProgress,
        totalSegments: segments?.length || 0,
    };
}

export default useSegmentSync;
