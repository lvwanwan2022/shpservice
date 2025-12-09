
export interface Coordinate {
  x: number;
  y: number;
}

export interface RouteNode extends Coordinate {
  radius: number; // Radius for the corner at this node
  spiralLength?: number; // Length of the transition spiral (Highway mode)
}

export interface RouteSegment {
  type: 'line' | 'arc' | 'spiral';
  coordinates: Coordinate[];
}

export enum InteractionMode {
  NONE = 'NONE',
  DRAW = 'DRAW',
  EDIT = 'EDIT'
}

export enum IndustryMode {
  WATER = 'WATER',     // Line -> Arc -> Line
  HIGHWAY = 'HIGHWAY'  // Line -> Spiral -> Arc -> Spiral -> Line
}
