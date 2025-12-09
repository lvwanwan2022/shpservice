
import { Coordinate, RouteNode, RouteSegment } from '../types';

/**
 * Basic vector operations
 */
const sub = (v1: Coordinate, v2: Coordinate): Coordinate => ({ x: v1.x - v2.x, y: v1.y - v2.y });
const add = (v1: Coordinate, v2: Coordinate): Coordinate => ({ x: v1.x + v2.x, y: v1.y + v2.y });
const mul = (v: Coordinate, s: number): Coordinate => ({ x: v.x * s, y: v.y * s });
const len = (v: Coordinate): number => Math.sqrt(v.x * v.x + v.y * v.y);
const norm = (v: Coordinate): Coordinate => {
  const l = len(v);
  return l === 0 ? { x: 0, y: 0 } : { x: v.x / l, y: v.y / l };
};

export interface CornerData {
  t1: Coordinate;
  t2: Coordinate;
  center: Coordinate;
  actualRadius: number;
  startAngle: number;
  endAngle: number;
}

/**
 * Calculates the geometry for a filleted corner at pCurr.
 */
export const getCornerData = (pPrev: Coordinate, pCurr: RouteNode, pNext: Coordinate): CornerData | null => {
  const v1 = sub(pPrev, pCurr);
  const v2 = sub(pNext, pCurr);
  const l1 = len(v1);
  const l2 = len(v2);

  if (l1 < 0.001 || l2 < 0.001) return null;

  const n1 = norm(v1);
  const n2 = norm(v2);

  const dot = n1.x * n2.x + n1.y * n2.y;
  const clampedDot = Math.max(-1, Math.min(1, dot));
  const angle = Math.acos(clampedDot);

  // If angle is effectively 180 degrees (straight line), no curve
  if (Math.abs(angle - Math.PI) < 0.01) return null;

  const halfAngle = angle / 2;
  // Radius comes from the node itself
  const radius = pCurr.radius || 0;
  
  if (radius <= 0) return null;

  const tangentDist = radius / Math.tan(halfAngle);

  // Constrain tangent distance to half the length of adjacent segments
  const maxDist = Math.min(l1, l2) / 2;
  const actualTangentDist = Math.min(tangentDist, maxDist);
  const actualRadius = actualTangentDist * Math.tan(halfAngle);

  // Tangent points
  const t1 = add(pCurr, mul(n1, actualTangentDist));
  const t2 = add(pCurr, mul(n2, actualTangentDist));

  // Center
  const bisector = norm(add(n1, n2));
  const distToCenter = actualRadius / Math.sin(halfAngle);
  const center = add(pCurr, mul(bisector, distToCenter));

  return { 
    t1, 
    t2, 
    center, 
    actualRadius, 
    startAngle: Math.atan2(t1.y - center.y, t1.x - center.x), 
    endAngle: Math.atan2(t2.y - center.y, t2.x - center.x) 
  };
};

/**
 * Generates a filleted path composed of Line and Arc segments.
 * 
 * @param nodes The control points with individual radii
 * @param segmentsPerArc Resolution of the arc
 * @returns An array of segments (lines and arcs)
 */
export const generateFilletedSegments = (
  nodes: RouteNode[],
  segmentsPerArc: number = 20
): RouteSegment[] => {
  if (nodes.length < 2) {
    return [];
  }

  const segments: RouteSegment[] = [];

  // We process the path.
  // We need to keep track of where the last geometry ended to connect with a line.
  // Start with the first point.
  let currentPos: Coordinate = nodes[0];

  for (let i = 1; i < nodes.length - 1; i++) {
    const pPrev = nodes[i - 1];
    const pCurr = nodes[i];
    const pNext = nodes[i + 1];

    const corner = getCornerData(pPrev, pCurr, pNext);

    if (corner) {
      // 1. Draw Line from currentPos to corner start (t1)
      segments.push({
        type: 'line',
        coordinates: [currentPos, corner.t1]
      });

      // 2. Draw Arc
      const arcPoints: Coordinate[] = [];
      let angleDiff = corner.endAngle - corner.startAngle;
      if (angleDiff > Math.PI) angleDiff -= 2 * Math.PI;
      if (angleDiff < -Math.PI) angleDiff += 2 * Math.PI;

      for (let j = 0; j <= segmentsPerArc; j++) {
        const theta = corner.startAngle + (angleDiff * j) / segmentsPerArc;
        arcPoints.push({
          x: corner.center.x + corner.actualRadius * Math.cos(theta),
          y: corner.center.y + corner.actualRadius * Math.sin(theta),
        });
      }
      
      segments.push({
        type: 'arc',
        coordinates: arcPoints
      });

      // Update currentPos to be the end of the arc
      currentPos = corner.t2;
    } else {
      // No corner (straight or r=0), just treating pCurr as a waypoint.
      segments.push({
        type: 'line',
        coordinates: [currentPos, pCurr]
      });
      currentPos = pCurr;
    }
  }

  // Final segment to the last point
  segments.push({
    type: 'line',
    coordinates: [currentPos, nodes[nodes.length - 1]]
  });

  // Clean up zero-length segments
  return segments.filter(s => {
      const p1 = s.coordinates[0];
      const p2 = s.coordinates[s.coordinates.length - 1];
      const dist = Math.sqrt(Math.pow(p1.x - p2.x, 2) + Math.pow(p1.y - p2.y, 2));
      return dist > 0.001;
  });
};
