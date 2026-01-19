import { LoginForm } from "@/components/auth/login-form";
import { ParticleBackground } from "@/components/ui/particle-background";

export default function LoginPage() {
  return (
    <div className="relative min-h-svh w-full">
      {/* 粒子背景 */}
      <ParticleBackground />

      {/* 登录内容 */}
      <div className="relative z-10 flex min-h-svh w-full items-center justify-center p-6 md:p-10">
        <div className="w-full max-w-md">
          <div className="relative">
            {/* 登录表单背景 */}
            <div className="absolute inset-0 rounded-2xl bg-white/80 backdrop-blur-xl shadow-2xl" />

            {/* 登录表单内容 */}
            <div className="relative z-10">
              <LoginForm />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}