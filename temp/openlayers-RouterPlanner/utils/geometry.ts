
import { Coordinate, RouteNode, RouteSegment, IndustryMode } from '../types';

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

// Rotate vector 90 degrees counter-clockwise
const perp = (v: Coordinate): Coordinate => ({ x: -v.y, y: v.x });

export interface CornerData {
  t1: Coordinate;
  t2: Coordinate;
  center: Coordinate;
  actualRadius: number;
  startAngle: number;
  endAngle: number;
  // Highway specific
  hasSpirals?: boolean;
  spiralInPoints?: Coordinate[];
  spiralOutPoints?: Coordinate[];
}

/**
 * Standard simple circular fillet (Water Conservancy Mode)
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
  const radius = pCurr.radius || 0;
  
  if (radius <= 0) return null;

  const tangentDist = radius / Math.tan(halfAngle);
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
    endAngle: Math.atan2(t2.y - center.y, t2.x - center.x),
    hasSpirals: false
  };
};

/**
 * Calculates a point on a Clothoid spiral using series expansion.
 * Standard formula for small angles.
 * @param l Length along spiral from TS
 * @param Ls Total length of spiral
 * @param R Radius at end of spiral
 */
const getClothoidPoint = (l: number, Ls: number, R: number): { x: number, y: number } => {
  // A^2 = R * Ls
  // Theta = l^2 / (2 * A^2) = l^2 / (2 * R * Ls)
  
  // Series expansion for x and y in local coordinates
  // x = l - l^5 / (40 * R^2 * Ls^2)
  // y = l^3 / (6 * R * Ls) - l^7 / (336 * R^3 * Ls^3)
  
  const RLs = R * Ls;
  const x = l - Math.pow(l, 5) / (40 * Math.pow(RLs, 2));
  const y = Math.pow(l, 3) / (6 * RLs) - Math.pow(l, 7) / (336 * Math.pow(RLs, 3));
  
  return { x, y };
};

/**
 * Highway Style: Line -> Spiral -> Arc -> Spiral -> Line
 */
export const getSpiralCornerData = (pPrev: Coordinate, pCurr: RouteNode, pNext: Coordinate): CornerData | null => {
  const R = pCurr.radius || 0.1;
  let Ls = pCurr.spiralLength || 0;

  // If No spiral length, fall back to simple circle
  if (Ls <= 1) return getCornerData(pPrev, pCurr, pNext);

  const v1 = sub(pPrev, pCurr);
  const v2 = sub(pNext, pCurr);
  const l1 = len(v1);
  const l2 = len(v2);

  if (l1 < 0.001 || l2 < 0.001) return null;

  const n1 = norm(v1); // Vector pointing back to Prev
  const n2 = norm(v2); // Vector pointing forward to Next

  // Calculate intersection angle (deflection angle)
  // Dot product = cos(theta)
  const dot = n1.x * n2.x + n1.y * n2.y;
  const clampedDot = Math.max(-1, Math.min(1, dot));
  const intersectionAngle = Math.acos(clampedDot); // Angle between vectors
  const deflectionAngle = Math.PI - intersectionAngle; // The turn angle

  // Basic validation:
  // Spiral angle theta_s = Ls / (2R)
  // Total turn required = deflectionAngle.
  // We need 2 spirals + 1 arc. 2 * theta_s must be < deflectionAngle for an arc to exist.
  // If 2 * theta_s >= deflectionAngle, the spirals meet or overlap (Transitional Curve).
  // For simplicity in this demo, we cap Ls to ensure at least a tiny arc exists.
  
  const maxSpiralAngle = deflectionAngle / 2 * 0.9; // 90% of half angle to leave room for arc
  const currentSpiralAngle = Ls / (2 * R);
  
  if (currentSpiralAngle > maxSpiralAngle) {
    // Reduce Ls to fit geometry
    Ls = maxSpiralAngle * 2 * R;
  }

  // Calculate Shift (p) and Throw (q)
  // p = Ls^2 / (24 * R)
  // q = Ls / 2 - Ls^3 / (240 * R^2)
  const p = (Ls * Ls) / (24 * R);
  const q = (Ls / 2) - (Math.pow(Ls, 3) / (240 * R * R));

  // Tangent Distance (Ts) distance from IP (pCurr) to TS point
  // Ts = (R + p) * tan(deflectionAngle / 2) + q
  const tanHalf = Math.tan(deflectionAngle / 2);
  const Ts = (R + p) * tanHalf + q;

  // Check if Ts fits in the leg lengths
  const maxTs = Math.min(l1, l2) / 1.01;
  if (Ts > maxTs) {
      // Not enough space for this configuration.
      // Fallback: Scale down the whole geometry implicitly by using simple arc
      // or just returning simple arc for stability.
      return getCornerData(pPrev, pCurr, pNext);
  }

  // 1. Calculate TS (Tangent-Spiral) and ST (Spiral-Tangent) points
  const TS = add(pCurr, mul(n1, Ts)); // On the incoming leg
  const ST = add(pCurr, mul(n2, Ts)); // On the outgoing leg

  // 2. Generate Spiral In points
  // We need to transform local spiral coords (x, y) to global coords.
  // Local x aligns with n1 (reversed? No, from TS towards IP). 
  // Wait, vector n1 is FROM pCurr TO pPrev.
  // So direction of travel is -n1.
  const dirIn = mul(n1, -1); // From pPrev towards pCurr
  const perpIn = { x: -dirIn.y, y: dirIn.x }; // Left turn perp?
  
  // Need to know if it's a left or right turn.
  // Cross product (z-component) of dirIn and n2 (dirOut)
  // dirIn = (pCurr - pPrev), n2 = (pNext - pCurr) / len
  // Actually n2 is already normalized (pNext - pCurr).
  const cross = dirIn.x * n2.y - dirIn.y * n2.x;
  const isLeftTurn = cross > 0;
  
  const spiralInPoints: Coordinate[] = [];
  const segments = 20;

  for(let i=0; i<=segments; i++) {
      const l = (i / segments) * Ls;
      const loc = getClothoidPoint(l, Ls, R);
      // Transform: Origin is TS. X-axis is dirIn. Y-axis is perpIn * (isLeft ? 1 : -1)
      const ySign = isLeftTurn ? 1 : -1;
      
      const globalX = TS.x + loc.x * dirIn.x + loc.y * ySign * perpIn.x;
      const globalY = TS.y + loc.x * dirIn.y + loc.y * ySign * perpIn.y;
      spiralInPoints.push({ x: globalX, y: globalY });
  }

  const SC = spiralInPoints[spiralInPoints.length - 1]; // Spiral-Circle point

  // 3. Generate Spiral Out points (reverse logic from ST)
  // Local origin ST. x-axis is -n2 (pointing back to IP). 
  const dirOut = n2; // Forward direction
  const perpOut = { x: -dirOut.y, y: dirOut.x };
  
  const spiralOutPoints: Coordinate[] = [];
  // We generate from CS to ST, but easier to generate from ST backwards mathematically then reverse array?
  // Let's generate from ST backwards (treating it like an entrance spiral)
  const dirBack = mul(dirOut, -1); // Pointing back to IP
  const perpBack = { x: -dirBack.y, y: dirBack.x }; // Relative to looking backwards
  
  // If original was Left Turn, then looking backwards it is a Right Turn.
  // So ySign is inverted.
  const ySignOut = isLeftTurn ? -1 : 1; 

  const spiralOutTemp: Coordinate[] = [];
  for(let i=0; i<=segments; i++) {
    const l = (i / segments) * Ls;
    const loc = getClothoidPoint(l, Ls, R);
    
    const globalX = ST.x + loc.x * dirBack.x + loc.y * ySignOut * perpBack.x;
    const globalY = ST.y + loc.x * dirBack.y + loc.y * ySignOut * perpBack.y;
    spiralOutTemp.push({ x: globalX, y: globalY });
  }
  
  // spiralOutTemp goes ST -> CS. We want CS -> ST for the path.
  spiralOutPoints.push(...spiralOutTemp.reverse());
  
  const CS = spiralOutPoints[0]; // Circle-Spiral point

  // 4. Calculate Center for Arc
  // The Arc connects SC and CS.
  // Midpoint of SC and CS is on the bisector.
  // Actually, standard circle center calculation is easier:
  // Center is offset from the incoming tangent by (R+p) along the bisector? No.
  // Center is perpendicular to the tangent at SC.
  
  // Angle consumed by spiral = theta_s = Ls / 2R.
  const theta_s = Ls / (2 * R);
  
  // Tangent at SC: rotated theta_s from initial tangent.
  // Or simply calculate Circle Center based on Geometry.
  // Center is at distance R from the curve points.
  // Bisector of the corner:
  const bisector = norm(add(mul(n1, 1), n2)); // Points "inward" to the turn center if acute angle?
  
  // Distance from IP (pCurr) to Center = (R + p) / sin(deflectionAngle / 2) ?
  // Yes, (R+p) is the offset of the shifted circle.
  // Direction depends on turn.
  // If left turn, center is to the left.
  
  // Let's use the explicit geometry:
  // Center C = IP + bisector * dist
  // But orientation of bisector needs care.
  // Correct method: Start at IP. Move along bisector.
  const distToCenter = (R + p) / Math.sin(deflectionAngle / 2);
  
  // Ensure bisector points towards the "inside" of the turn.
  // n1+n2 points outwards for sharp turns usually.
  // Let's use cross product logic.
  let bisectorDir = bisector;
  
  // Check if bisector points towards "inside".
  // Inside point should allow (SC - Center) approx = R.
  // Let's try candidate center.
  const centerCand = add(pCurr, mul(bisectorDir, distToCenter));
  // If turn is left, and bisector points right, flip it.
  // Hard to robustly detemine without vector math.
  
  // Alternative: Perpendicular to SC tangent.
  // Tangent at SC is Incoming Dir rotated by theta_s (Left or Right).
  // Then Center is perpendicular to that.
  // Let's stick to what we have: SC and CS are on the circle.
  // Find circle from 2 points and Radius.
  // Center is intersection of perpendiculars from SC and CS?
  // Or midpoint of SC-CS, then move perpendicular.
  
  const midChord = { x: (SC.x + CS.x)/2, y: (SC.y + CS.y)/2 };
  const chordLen = Math.sqrt((SC.x-CS.x)**2 + (SC.y-CS.y)**2);
  const distMidToCenter = Math.sqrt(Math.max(0, R*R - (chordLen/2)**2));
  
  // Direction from MidChord to Center.
  // It's the same direction as IP -> MidChord.
  const vMid = sub(midChord, pCurr);
  const vMidNorm = norm(vMid);
  const center = add(midChord, mul(vMidNorm, distMidToCenter));

  // Angles
  const startAngle = Math.atan2(SC.y - center.y, SC.x - center.x);
  const endAngle = Math.atan2(CS.y - center.y, CS.x - center.x);

  return {
    t1: TS,
    t2: ST,
    center,
    actualRadius: R,
    startAngle,
    endAngle,
    hasSpirals: true,
    spiralInPoints,
    spiralOutPoints
  };
};

/**
 * Generates path segments.
 */
export const generateFilletedSegments = (
  nodes: RouteNode[],
  industryMode: IndustryMode = IndustryMode.WATER,
  defaultSpiralLen: number = 0
): RouteSegment[] => {
  if (nodes.length < 2) {
    return [];
  }

  const segments: RouteSegment[] = [];
  let currentPos: Coordinate = nodes[0];

  for (let i = 1; i < nodes.length - 1; i++) {
    const pPrev = nodes[i - 1];
    const pCurr = nodes[i];
    const pNext = nodes[i + 1];
    
    // Inject global default spiral length if node doesn't have specific one
    const processingNode = {
        ...pCurr,
        spiralLength: pCurr.spiralLength !== undefined ? pCurr.spiralLength : defaultSpiralLen
    };

    let corner: CornerData | null = null;

    if (industryMode === IndustryMode.HIGHWAY) {
        corner = getSpiralCornerData(pPrev, processingNode, pNext);
    } else {
        corner = getCornerData(pPrev, processingNode, pNext);
    }

    if (corner) {
      // 1. Line to Start of Turn (t1 is TS or PC)
      segments.push({
        type: 'line',
        coordinates: [currentPos, corner.t1]
      });

      if (corner.hasSpirals && corner.spiralInPoints && corner.spiralOutPoints) {
          // 2a. Spiral In
          segments.push({
              type: 'spiral',
              coordinates: corner.spiralInPoints
          });

          // 2b. Circular Arc (SC to CS)
          const arcPoints: Coordinate[] = [];
          let angleDiff = corner.endAngle - corner.startAngle;
          if (angleDiff > Math.PI) angleDiff -= 2 * Math.PI;
          if (angleDiff < -Math.PI) angleDiff += 2 * Math.PI;
          
          const segmentsPerArc = 20;
          for (let j = 0; j <= segmentsPerArc; j++) {
            const theta = corner.startAngle + (angleDiff * j) / segmentsPerArc;
            arcPoints.push({
              x: corner.center.x + corner.actualRadius * Math.cos(theta),
              y: corner.center.y + corner.actualRadius * Math.sin(theta),
            });
          }
          segments.push({ type: 'arc', coordinates: arcPoints });

          // 2c. Spiral Out
          segments.push({
              type: 'spiral',
              coordinates: corner.spiralOutPoints
          });

          currentPos = corner.t2; // ST
      } else {
          // Standard Arc
          const arcPoints: Coordinate[] = [];
          let angleDiff = corner.endAngle - corner.startAngle;
          if (angleDiff > Math.PI) angleDiff -= 2 * Math.PI;
          if (angleDiff < -Math.PI) angleDiff += 2 * Math.PI;

          const segmentsPerArc = 20;
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
          currentPos = corner.t2;
      }

    } else {
      segments.push({
        type: 'line',
        coordinates: [currentPos, pCurr]
      });
      currentPos = pCurr;
    }
  }

  segments.push({
    type: 'line',
    coordinates: [currentPos, nodes[nodes.length - 1]]
  });

  return segments.filter(s => {
    if (s.coordinates.length < 2) return false;
    // Simple check for zero length
    const p1 = s.coordinates[0];
    const p2 = s.coordinates[s.coordinates.length - 1];
    return Math.abs(p1.x - p2.x) > 0.001 || Math.abs(p1.y - p2.y) > 0.001;
  });
};
