/**
 * 流量来源追踪工具模块
 * 用于管理和追踪用户流量来源（web、h5、miniprogram、mp）
 */

// ==================== 类型定义 ====================

/**
 * 流量来源类型
 * - web: PC Web 端
 * - h5: 移动端 H5
 * - miniprogram: 微信小程序
 * - mp: 微信公众号
 */
export type TrafficSource = 'web' | 'h5' | 'miniprogram' | 'mp' | '医保' | 'rexian' | 'test' | 'admin';

// ==================== 常量定义 ====================

/**
 * 默认流量来源
 */
export const DEFAULT_SOURCE: TrafficSource = '医保'; // web

/**
 * localStorage 存储键名
 */
export const TRAFFIC_SOURCE_KEY = 'traffic_source';

/**
 * 有效的流量来源列表
 */
export const VALID_SOURCES: TrafficSource[] = ['web', 'h5', 'miniprogram', 'mp', '医保', 'rexian', 'test', 'admin'];

// ==================== 工具函数 ====================

/**
 * 验证来源值是否有效
 * @param value 待验证的来源值
 * @returns 是否为有效的流量来源
 */
function isValidSource(value: string): value is TrafficSource {
  return VALID_SOURCES.includes(value as TrafficSource);
}

/**
 * 设置流量来源到 localStorage
 * @param source 流量来源值
 */
function setTrafficSource(source: TrafficSource): void {
  localStorage.setItem(TRAFFIC_SOURCE_KEY, source);
}

// ==================== 公共 API ====================

/**
 * 初始化流量来源
 * 从 URL 参数 ?from=xxx 获取流量来源，如果存在则更新 localStorage
 * @returns 当前流量来源值
 */
export function initTrafficSource(): TrafficSource {
  // 从 URL 获取 from 参数
  const urlParams = new URLSearchParams(window.location.search);
  const fromParam = urlParams.get('from');

  // 验证并存储
  if (fromParam && isValidSource(fromParam)) {
    setTrafficSource(fromParam);
    return fromParam;
  }

  // 如果 URL 没有参数或无效，返回已有的或默认值
  return getTrafficSource();
}

/**
 * 获取当前流量来源
 * 从 localStorage 读取，如果不存在则返回默认值
 * @returns 当前流量来源值
 */
export function getTrafficSource(): TrafficSource {
  const stored = localStorage.getItem(TRAFFIC_SOURCE_KEY);
  if (stored && isValidSource(stored)) {
    return stored;
  }
  return DEFAULT_SOURCE;
}

/**
 * 清除流量来源（仅用于开发调试）
 * 生产环境不应调用此函数
 */
export function clearTrafficSource(): void {
  localStorage.removeItem(TRAFFIC_SOURCE_KEY);
}
