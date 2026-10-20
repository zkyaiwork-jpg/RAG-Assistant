import { useAuth } from '../auth/AuthContext'
import { useDesktopUser } from './useDesktopUser'

/**
 * 统一的名字展示来源：登录账号的真实姓名 → 登录名 → 桌面端本地设置。
 * 之前各处用的都是桌面端本地用户名，浏览器里为空时只能显示“用户”。
 */
export function useDisplayName() {
  const { currentUser } = useAuth()
  const { userName } = useDesktopUser()

  const resolved = currentUser?.real_name?.trim() || currentUser?.username?.trim() || userName.trim()
  const displayName = resolved || '用户'

  return {
    displayName,
    initial: displayName.slice(0, 1),
  }
}
