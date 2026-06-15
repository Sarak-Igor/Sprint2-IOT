import React from 'react';
import { getBezierPath, EdgeProps } from 'reactflow';

export const AnimatedEdge = ({
    id,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    style = {},
    markerEnd,
    data
}: EdgeProps) => {
    const [edgePath] = getBezierPath({
        sourceX,
        sourceY,
        sourcePosition,
        targetX,
        targetY,
        targetPosition,
    });

    return (
        <>
            <path
                id={id}
                style={{
                    ...style,
                    strokeWidth: 2,
                    stroke: data?.active ? '#ffffff' : '#334155',
                    transition: 'stroke 0.3s'
                }}
                className="react-flow__edge-path"
                d={edgePath}
                markerEnd={markerEnd}
            />
            {data?.active && (
                <circle r="4" fill={data?.color || '#3b82f6'}>
                    <animateMotion
                        dur="0.8s"
                        repeatCount="1"
                        path={edgePath}
                        begin="0s"
                    />
                    <filter id="glow">
                        <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
                        <feMerge>
                            <feMergeNode in="coloredBlur"/>
                            <feMergeNode in="SourceGraphic"/>
                        </feMerge>
                    </filter>
                </circle>
            )}
            
            {/* Pulsing effect on the path when active */}
            {data?.active && (
                <path
                    d={edgePath}
                    fill="none"
                    stroke={data?.color || '#3b82f6'}
                    strokeWidth="4"
                    strokeOpacity="0.3"
                    strokeLinecap="round"
                >
                    <animate
                        attributeName="stroke-dasharray"
                        from="0, 1000"
                        to="1000, 0"
                        dur="0.8s"
                        repeatCount="1"
                    />
                </path>
            )}
        </>
    );
};
