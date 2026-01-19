import type { User } from "@/utils/request/auth";

/**
 * 检查用户是否有编辑权限
 */
export function canEditKnowledge(user: User | null): boolean {
  if (!user?.user_role) return false;
  return user.user_role !== 'normal_user';
}

/**
 * 检查用户是否有删除权限
 */
export function canDeleteKnowledge(user: User | null): boolean {
  if (!user?.user_role) return false;
  return user.user_role !== 'normal_user';
}

/**
 * 检查用户是否有新增权限
 */
export function canAddKnowledge(user: User | null): boolean {
  if (!user?.user_role) return false;
  return user.user_role !== 'normal_user';
}
