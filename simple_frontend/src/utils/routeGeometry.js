/**
 * 路径规划几何工具函数
 * 用于计算圆弧和路径段
 */

// 行业模式枚举
export const IndustryMode = {
  WATER: 'WATER',     // 水利模式：直线 -> 圆弧 -> 直线
  HIGHWAY: 'HIGHWAY'  // 公路模式：直线 -> 缓和曲线 -> 圆弧 -> 缓和曲线 -> 直线
};

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

// 旋转向量90度（逆时针）
const perp = (v) => ({ x: -v.y, y: v.x });

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
    endAngle: Math.atan2(t2.y - center.y, t2.x - center.x),
    hasSpirals: false
  };
};

/**
 * 计算回旋线（Clothoid）上的点
 * 使用级数展开公式
 * @param {Number} l - 从TS点沿回旋线的长度
 * @param {Number} Ls - 回旋线总长度
 * @param {Number} R - 回旋线终点的半径
 */
const getClothoidPoint = (l, Ls, R) => {
  // A^2 = R * Ls
  // Theta = l^2 / (2 * A^2) = l^2 / (2 * R * Ls)
  
  // 级数展开公式（局部坐标系）
  // x = l - l^5 / (40 * R^2 * Ls^2)
  // y = l^3 / (6 * R * Ls) - l^7 / (336 * R^3 * Ls^3)
  
  const RLs = R * Ls;
  const x = l - Math.pow(l, 5) / (40 * Math.pow(RLs, 2));
  const y = Math.pow(l, 3) / (6 * RLs) - Math.pow(l, 7) / (336 * Math.pow(RLs, 3));
  
  return { x, y };
};

/**
 * 公路模式：计算带缓和曲线的角点数据
 * 连接方式：直线 -> 缓和曲线 -> 圆弧 -> 缓和曲线 -> 直线
 * @param {Object} pPrev - 前一个点 {x, y}
 * @param {Object} pCurr - 当前点 {x, y, radius, spiralLength}
 * @param {Object} pNext - 下一个点 {x, y}
 * @returns {Object|null} 角点数据或null
 */
export const getSpiralCornerData = (pPrev, pCurr, pNext) => {
  const R = pCurr.radius || 0.1;
  let Ls = pCurr.spiralLength || 0;

  // 如果没有缓和曲线长度，回退到简单圆弧
  if (Ls <= 1) return getCornerData(pPrev, pCurr, pNext);

  const v1 = sub(pPrev, pCurr);
  const v2 = sub(pNext, pCurr);
  const l1 = len(v1);
  const l2 = len(v2);

  if (l1 < 0.001 || l2 < 0.001) return null;

  const n1 = norm(v1); // 指向Prev的向量
  const n2 = norm(v2); // 指向Next的向量

  // 计算交角（偏转角）
  const dot = n1.x * n2.x + n1.y * n2.y;
  const clampedDot = Math.max(-1, Math.min(1, dot));
  const intersectionAngle = Math.acos(clampedDot);
  const deflectionAngle = Math.PI - intersectionAngle; // 转向角

  // 基本验证：缓和曲线角度 theta_s = Ls / (2R)
  // 总转向角 = deflectionAngle
  // 需要 2个缓和曲线 + 1个圆弧。2 * theta_s 必须 < deflectionAngle 才能有圆弧
  const maxSpiralAngle = deflectionAngle / 2 * 0.9; // 90%的一半角度，为圆弧留出空间
  const currentSpiralAngle = Ls / (2 * R);
  
  if (currentSpiralAngle > maxSpiralAngle) {
    // 减小Ls以适应几何形状
    Ls = maxSpiralAngle * 2 * R;
  }

  // 计算偏移量（p）和切线增量（q）
  // p = Ls^2 / (24 * R)
  // q = Ls / 2 - Ls^3 / (240 * R^2)
  const p = (Ls * Ls) / (24 * R);
  const q = (Ls / 2) - (Math.pow(Ls, 3) / (240 * R * R));

  // 切线距离（Ts）：从IP（pCurr）到TS点的距离
  // Ts = (R + p) * tan(deflectionAngle / 2) + q
  const tanHalf = Math.tan(deflectionAngle / 2);
  const Ts = (R + p) * tanHalf + q;

  // 检查Ts是否适合线段长度
  const maxTs = Math.min(l1, l2) / 1.01;
  if (Ts > maxTs) {
    // 空间不足，回退到简单圆弧
    return getCornerData(pPrev, pCurr, pNext);
  }

  // 1. 计算TS（切线-缓和曲线）和ST（缓和曲线-切线）点
  const TS = add(pCurr, mul(n1, Ts)); // 在进入段上
  const ST = add(pCurr, mul(n2, Ts)); // 在离开段上

  // 2. 生成进入缓和曲线点
  const dirIn = mul(n1, -1); // 从pPrev指向pCurr的方向
  const perpIn = { x: -dirIn.y, y: dirIn.x };
  
  // 判断是左转还是右转
  const cross = dirIn.x * n2.y - dirIn.y * n2.x;
  const isLeftTurn = cross > 0;
  
  const spiralInPoints = [];
  const segments = 20;

  for (let i = 0; i <= segments; i++) {
    const l = (i / segments) * Ls;
    const loc = getClothoidPoint(l, Ls, R);
    // 变换：原点是TS。X轴是dirIn。Y轴是perpIn * (isLeft ? 1 : -1)
    const ySign = isLeftTurn ? 1 : -1;
    
    const globalX = TS.x + loc.x * dirIn.x + loc.y * ySign * perpIn.x;
    const globalY = TS.y + loc.x * dirIn.y + loc.y * ySign * perpIn.y;
    spiralInPoints.push({ x: globalX, y: globalY });
  }

  const SC = spiralInPoints[spiralInPoints.length - 1]; // 缓和曲线-圆弧点

  // 3. 生成离开缓和曲线点（从ST反向）
  const dirOut = n2; // 前进方向
  const dirBack = mul(dirOut, -1); // 指向IP
  const perpBack = { x: -dirBack.y, y: dirBack.x };
  
  // 如果原来是左转，反向看就是右转
  const ySignOut = isLeftTurn ? -1 : 1;

  const spiralOutTemp = [];
  for (let i = 0; i <= segments; i++) {
    const l = (i / segments) * Ls;
    const loc = getClothoidPoint(l, Ls, R);
    
    const globalX = ST.x + loc.x * dirBack.x + loc.y * ySignOut * perpBack.x;
    const globalY = ST.y + loc.x * dirBack.y + loc.y * ySignOut * perpBack.y;
    spiralOutTemp.push({ x: globalX, y: globalY });
  }
  
  // spiralOutTemp从ST到CS，我们需要从CS到ST的路径
  const spiralOutPoints = [...spiralOutTemp].reverse();
  
  const CS = spiralOutPoints[0]; // 圆弧-缓和曲线点

  // 4. 计算圆弧中心
  // 圆弧连接SC和CS
  const midChord = { x: (SC.x + CS.x) / 2, y: (SC.y + CS.y) / 2 };
  const chordLen = Math.sqrt((SC.x - CS.x) ** 2 + (SC.y - CS.y) ** 2);
  const distMidToCenter = Math.sqrt(Math.max(0, R * R - (chordLen / 2) ** 2));
  
  // 从MidChord到Center的方向
  const vMid = sub(midChord, pCurr);
  const vMidNorm = norm(vMid);
  const center = add(midChord, mul(vMidNorm, distMidToCenter));

  // 角度
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
 * 生成带圆角的路径段（直线和圆弧，或直线、缓和曲线、圆弧）
 * 
 * @param {Array} nodes - 控制点数组，每个点包含 {x, y, radius, spiralLength?}
 * @param {String} industryMode - 行业模式 'WATER' | 'HIGHWAY'，默认'WATER'
 * @param {Number} defaultSpiralLen - 默认缓和曲线长度，默认0
 * @param {Number} segmentsPerArc - 每个圆弧的分段数，默认20
 * @returns {Array} 路径段数组，每个段包含 {type: 'line'|'arc'|'spiral', coordinates: [...]}
 */
export const generateFilletedSegments = (nodes, industryMode = IndustryMode.WATER, defaultSpiralLen = 0, segmentsPerArc = 20) => {
  if (nodes.length < 2) {
    return [];
  }

  const segments = [];
  let currentPos = nodes[0];

  for (let i = 1; i < nodes.length - 1; i++) {
    const pPrev = nodes[i - 1];
    const pCurr = nodes[i];
    const pNext = nodes[i + 1];
    
    // 如果节点没有特定的spiralLength，使用全局默认值
    const processingNode = {
      ...pCurr,
      spiralLength: pCurr.spiralLength !== undefined ? pCurr.spiralLength : defaultSpiralLen
    };

    let corner = null;

    if (industryMode === IndustryMode.HIGHWAY) {
      corner = getSpiralCornerData(pPrev, processingNode, pNext);
    } else {
      corner = getCornerData(pPrev, processingNode, pNext);
    }

    if (corner) {
      // 1. 从当前位置到转向起点(t1是TS或PC)
      segments.push({
        type: 'line',
        coordinates: [currentPos, corner.t1]
      });

      if (corner.hasSpirals && corner.spiralInPoints && corner.spiralOutPoints) {
        // 2a. 进入缓和曲线
        segments.push({
          type: 'spiral',
          coordinates: corner.spiralInPoints
        });

        // 2b. 圆弧（SC到CS）
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
        segments.push({ type: 'arc', coordinates: arcPoints });

        // 2c. 离开缓和曲线
        segments.push({
          type: 'spiral',
          coordinates: corner.spiralOutPoints
        });

        currentPos = corner.t2; // ST
      } else {
        // 标准圆弧
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
        currentPos = corner.t2;
      }
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
    if (s.coordinates.length < 2) return false;
    const p1 = s.coordinates[0];
    const p2 = s.coordinates[s.coordinates.length - 1];
    return Math.abs(p1.x - p2.x) > 0.001 || Math.abs(p1.y - p2.y) > 0.001;
  });
};
