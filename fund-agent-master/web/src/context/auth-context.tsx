import {
  createContext,
  useContext,
  useState,
  useEffect,
  type ReactNode
} from "react";
import { type User, getCurrentUser, isAuthenticated as checkIsAuthenticated, logout } from "@/utils/request/auth";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (user: User) => void;
  logoutUser: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // 不在这里处理401错误，让ProtectedRoute和组件内部处理
  // 这样可以避免页面刷新和复杂的导航逻辑

  // 初始化认证状态
  useEffect(() => {
    let isMounted = true;

    const initAuth = async () => {
      try {
        const authStatus = checkIsAuthenticated();
        if (authStatus && isMounted) {
          // 如果有token，获取用户信息
          const userData = await getCurrentUser();
          if (isMounted) {
            setUser(userData);
            setIsAuthenticated(true);
          }
        } else if (isMounted) {
          setIsAuthenticated(false);
        }
      } catch (error) {
        console.error("认证初始化失败:", error);
        // 如果获取用户信息失败，清除无效token
        logout();
        if (isMounted) {
          setIsAuthenticated(false);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    initAuth();

    return () => {
      isMounted = false;
    };
  }, []);

  const login = (userData: User) => {
    setUser(userData);
    setIsAuthenticated(true);
  };

  const logoutUser = () => {
    logout();
    setUser(null);
    setIsAuthenticated(false);
  };

  const refreshUser = async () => {
    try {
      const userData = await getCurrentUser();
      setUser(userData);
      setIsAuthenticated(true);
    } catch (error) {
      console.error("刷新用户信息失败:", error);
      logoutUser();
    }
  };

  const value: AuthContextType = {
    user,
    loading,
    isAuthenticated,
    login,
    logoutUser,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}