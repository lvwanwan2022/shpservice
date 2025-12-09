
export interface Coordinate {
  x: number;
  y: number;
}

export interface RouteNode extends Coordinate {
  radius: number; // Radius for the corner at this node
}

export interface RouteSegment {
  type: 'line' | 'arc';
  coordinates: Coordinate[];
}

export enum InteractionMode {
  NONE = 'NONE',
  DRAW = 'DRAW',
  EDIT = 'EDIT'
}
