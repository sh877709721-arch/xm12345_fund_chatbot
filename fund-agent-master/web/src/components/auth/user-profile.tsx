import React, { useState, useEffect } from "react";
import { getCurrentUser, logout } from "@/utils/request/auth";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";

const UserProfile: React.FC = () => {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const userData = await getCurrentUser();
        setUser(userData);
      } catch (error) {
        toast.error("获取用户信息失败");
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, []);

  const handleLogout = () => {
    logout();
    toast.success("已退出登录");
    navigate("/login");
  };

  if (loading) return <div>加载中...</div>;
  if (!user) return <div>未找到用户信息</div>;

  return (
    <div>
      <h2>用户信息</h2>
      <p>用户名: {user.username}</p>
      <p>邮箱: {user.email}</p>
      <button onClick={handleLogout}>退出登录</button>
    </div>
  );
};

export default UserProfile;