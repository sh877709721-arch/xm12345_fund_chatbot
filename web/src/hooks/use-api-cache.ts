import * as React from "react";

interface CacheEntry<T = any> {
  data: T;
  timestamp: number;
  expiresAt: number;
}

interface ApiCacheOptions {
  ttl?: number; // 缓存时间（毫秒），默认 5 分钟
  maxSize?: number; // 最大缓存条目数
}

export function useApiCache<T = any>(options: ApiCacheOptions = {}) {
  const [cache, setCache] = React.useState<Map<string, CacheEntry<T>>>(new Map());
  const { ttl = 5 * 60 * 1000, maxSize = 100 } = options;

  // 获取缓存键
  const getCacheKey = React.useCallback((key: string, params?: Record<string, any>) => {
    const keyParts = [key];
    if (params) {
      keyParts.push(JSON.stringify(params));
    }
    return keyParts.join(':');
  }, []);

  // 检查缓存是否过期
  const isExpired = (entry: CacheEntry<T>) => {
    return Date.now() - entry.timestamp > ttl;
  };

  // 清理过期缓存
  const cleanExpiredCache = React.useCallback(() => {
    setCache((prev) => {
      const cleaned = new Map<string, CacheEntry<T>>();
      prev.forEach((entry, key) => {
        if (!isExpired(entry)) {
          cleaned.set(key, entry);
        }
      });
      return cleaned;
    });
  }, [ttl]);

  // 获取缓存数据
  const getCacheData = React.useCallback((key: string, params?: Record<string, any>) => {
    const cacheKey = getCacheKey(key, params);
    const entry = cache.get(cacheKey);

    if (entry && !isExpired(entry)) {
      return entry.data;
    }
    return null;
  }, [cache, getCacheKey, isExpired]);

  // 设置缓存数据
  const setCacheData = React.useCallback((key: string, data: T, params?: Record<string, any>) => {
    const cacheKey = getCacheKey(key, params);

    setCache((prev) => {
      // 检查缓存大小限制
      if (prev.size >= maxSize) {
        // 找到最旧的条目并删除
        let oldestKey = '';
        let oldestTimestamp = Date.now();

        prev.forEach((entry, k) => {
          if (entry.timestamp < oldestTimestamp) {
            oldestTimestamp = entry.timestamp;
            oldestKey = k;
          }
        });

        if (oldestKey) {
          const newCache = new Map(prev);
          newCache.delete(oldestKey);
          newCache.set(cacheKey, {
            data,
            timestamp: Date.now(),
            expiresAt: Date.now() + ttl,
          });
          return newCache;
        }
      }

      // 直接添加新缓存
      const newEntry: CacheEntry<T> = {
        data,
        timestamp: Date.now(),
        expiresAt: Date.now() + ttl,
      };

      return new Map(prev).set(cacheKey, newEntry);
    });
  }, [cache, getCacheKey, maxSize, ttl]);

  // 清除特定缓存
  const clearCache = React.useCallback((key: string) => {
    setCache((prev) => {
      const newCache = new Map(prev);
      newCache.delete(key);
      return newCache;
    });
  }, [cache]);

  return {
    getCacheData,
    setCacheData,
    clearCache,
    cleanExpiredCache,
  };
};