/**
 * 路径规划几何工具函数
 * 用于计算圆弧和路径段
 */

/**
 * 基本向量运算
 */
const sub = (v1, v2) => ({ x: v1.x - v2.x, y: v1.y - v2.y });
const add = (v1, v2) => ({ x: v1.x + v2.x, y: v1.y + v2.y });
const mul = (v, s) => ({ x: v.x * s, y: v.y * s });
const len = (v) => Math.sqrt(v.x * v.x + v.y * v.y);
const norm = (v) => {
  const l = len(v);
  return l === 0 ? { x: 0, y: 0 } : { x: v.x / l, y: v.y / l };
};

/**
 * 计算角点处的圆弧几何数据
 * @param {Object} pPrev - 前一个点 {x, y}
 * @param {Object} pCurr - 当前点 {x, y, radius}
 * @param {Object} pNext - 下一个点 {x, y}
 * @returns {Object|null} 角点数据或null
 */
export const getCornerData = (pPrev, pCurr, pNext) => {
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

  // 如果角度接近180度（直线），不需要圆弧
  if (Math.abs(angle - Math.PI) < 0.01) return null;

  const halfAngle = angle / 2;
  // 半径来自节点本身
  const radius = pCurr.radius || 0;
  
  if (radius <= 0) return null;

  const tangentDist = radius / Math.tan(halfAngle);

  // 限制切线距离不超过相邻线段长度的一半
  const maxDist = Math.min(l1, l2) / 2;
  const actualTangentDist = Math.min(tangentDist, maxDist);
  const actualRadius = actualTangentDist * Math.tan(halfAngle);

  // 切点
  const t1 = add(pCurr, mul(n1, actualTangentDist));
  const t2 = add(pCurr, mul(n2, actualTangentDist));

  // 圆心
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
 * 生成带圆角的路径段（直线和圆弧）
 * 
 * @param {Array} nodes - 控制点数组，每个点包含 {x, y, radius}
 * @param {Number} segmentsPerArc - 每个圆弧的分段数，默认20
 * @returns {Array} 路径段数组，每个段包含 {type: 'line'|'arc', coordinates: [...]}
 */
export const generateFilletedSegments = (nodes, segmentsPerArc = 20) => {
  if (nodes.length < 2) {
    return [];
  }

  const segments = [];

  // 处理路径
  // 需要跟踪上一个几何结束位置以便连接直线
  // 从第一个点开始
  let currentPos = nodes[0];

  for (let i = 1; i < nodes.length - 1; i++) {
    const pPrev = nodes[i - 1];
    const pCurr = nodes[i];
    const pNext = nodes[i + 1];

    const corner = getCornerData(pPrev, pCurr, pNext);

    if (corner) {
      // 1. 从当前位置到角点起点(t1)绘制直线
      segments.push({
        type: 'line',
        coordinates: [currentPos, corner.t1]
      });

      // 2. 绘制圆弧
      const arcPoints = [];
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

      // 更新当前位置为圆弧终点
      currentPos = corner.t2;
    } else {
      // 没有角点（直线或r=0），将pCurr作为路径点
      segments.push({
        type: 'line',
        coordinates: [currentPos, pCurr]
      });
      currentPos = pCurr;
    }
  }

  // 最后一段到最后一个点
  segments.push({
    type: 'line',
    coordinates: [currentPos, nodes[nodes.length - 1]]
  });

  // 清理零长度段
  return segments.filter(s => {
      const p1 = s.coordinates[0];
      const p2 = s.coordinates[s.coordinates.length - 1];
      const dist = Math.sqrt(Math.pow(p1.x - p2.x, 2) + Math.pow(p1.y - p2.y, 2));
      return dist > 0.001;
  });
};
