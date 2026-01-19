export function ParticleBackground() {
  // 围绕主题主色 #3b82f6 (H=210, S=94%, L=60%) 构建协调色
  const baseHue = 210; // 主色色相
  const getHue = (offset: number) => {
    return ((baseHue + offset + 360) % 360); // 安全环绕
  };

  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">

      {/* 网格背景：使用主色和青蓝色变体 */}
      <div
        className="absolute inset-0 opacity-20"
        style={{
          backgroundImage: `
            linear-gradient(to right, hsla(${getHue(-15)}, 100%, 60%, 0.25) 1px, transparent 1px),
            linear-gradient(to bottom, hsla(${getHue(0)}, 94%, 60%, 0.25) 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
        }}
      />

      {/* 正方形粒子 */}
      <div className="absolute inset-0">
        {[...Array(20)].map((_, i) => {
          const randomX = 60 + Math.sin(i * 1.7) * 25 + Math.cos(i * 2.3) * 15;
          const randomY = 55 + Math.cos(i * 1.3) * 30 + Math.sin(i * 3.1) * 20;
          const randomSize = 15 + Math.sin(i * 2.7) * 10;
          const hue = getHue(-10 + (i % 5) * 4); // 200 ~ 216

          return (
            <div
              key={`square-${i}`}
              className="absolute"
              style={{
                left: `${Math.max(55, Math.min(95, randomX))}%`,
                top: `${Math.max(50, Math.min(95, randomY))}%`,
                width: `${randomSize}px`,
                height: `${randomSize}px`,
                animationDelay: `${Math.random() * 5}s`,
                animation: `spinSlow ${15 + Math.random() * 10}s linear infinite`,
              }}
            >
              <div
                className="w-full h-full border-2 opacity-50 transform rotate-45"
                style={{
                  borderColor: `hsl(${hue}, 100%, ${55 + (i % 2) * 10}%)`,
                  boxShadow: `0 0 ${12 + randomSize / 2}px hsl(${hue}, 100%, ${50 + (i % 2) * 10}%)`,
                  filter: `blur(0.5px) drop-shadow(0 0 ${8 + randomSize / 3}px hsl(${hue}, 100%, 55%))`,
                }}
              />
            </div>
          );
        })}
      </div>

      {/* 浮动粒子 */}
      {/* {[...Array(15)].map((_, i) => {
        const randomX = 55 + Math.sin(i * 3.7) * 20 + Math.cos(i * 1.9) * 20;
        const randomY = 60 + Math.cos(i * 2.7) * 20 + Math.sin(i * 4.1) * 15;
        const randomSize = 40 + Math.sin(i * 1.4) * 30;
        const hue1 = getHue(-15 + Math.sin(i) * 8);   // ~195–210
        const hue2 = getHue(0 + Math.cos(i * 2) * 8); // ~202–218

        return (
          <div
            key={`float-${i}`}
            className="absolute rounded-full opacity-60 animate-float"
            style={{
              left: `${Math.max(45, Math.min(95, randomX))}%`,
              top: `${Math.max(55, Math.min(95, randomY))}%`,
              width: `${randomSize}px`,
              height: `${randomSize}px`,
              animationDelay: `${Math.random() * 3}s`,
              background: `radial-gradient(circle,
                hsl(${hue1}, 100%, ${65 + Math.cos(i) * 10}%) 0%,
                hsl(${hue2}, 100%, ${45 + Math.sin(i * 3) * 15}%) 30%,
                transparent 70%)`,
              filter: `blur(${0.8 + Math.random() * 1.5}px) drop-shadow(0 0 ${12 + randomSize / 2}px hsl(${hue1}, 100%, 55%))`,
              boxShadow: `0 0 ${18 + randomSize / 2}px hsl(${hue2}, 100%, 45%)`,
            }}
          />
        );
      })} */}

      {/* 霓虹光晕 */}
      {/* {[...Array(4)].map((_, i) => {
        const randomX = 50 + Math.sin(i * 2.3) * 30 + Math.cos(i * 1.7) * 15;
        const randomY = 60 + Math.cos(i * 2.9) * 25 + Math.sin(i * 3.3) * 15;
        const randomSize = 350 + Math.sin(i * 1.5) * 200;
        const hue = getHue(-12 + (i * 5) % 10); // 198–212

        return (
          <div
            key={`glow-${i}`}
            className="absolute rounded-full"
            style={{
              left: `${Math.max(40, Math.min(85, randomX))}%`,
              top: `${Math.max(50, Math.min(90, randomY))}%`,
              width: `${randomSize}px`,
              height: `${randomSize}px`,
            }}
          >
            <div
              className="w-full h-full rounded-full animate-pulse"
              style={{
                background: `radial-gradient(circle,
                  hsla(${hue}, 100%, 60%, ${0.5 + Math.random() * 0.3}) 0%,
                  hsla(${getHue(5)}, 100%, 45%, ${0.25 + Math.random() * 0.15}) 30%,
                  transparent 70%)`,
                filter: `blur(${30 + Math.random() * 30}px) brightness(1.3)`,
                boxShadow: `0 0 ${60 + randomSize / 3}px hsla(${hue}, 100%, 55%, 0.4),
                           0 0 ${120 + randomSize / 2}px hsla(${getHue(8)}, 100%, 40%, 0.15)`,
                animationDelay: `${Math.random() * 4}s`,
              }}
            />
          </div>
        );
      })} */}

      {/* 霓虹扫描线 */}
      <div className="absolute inset-0 overflow-hidden">
        {[...Array(5)].map((_, i) => {
          const randomY = 45 + Math.sin(i * 2.1) * 30 + Math.cos(i * 3.7) * 15;
          const isHorizontal = Math.random() > 0.4;
          const hue = getHue(-10 + (i * 7) % 12); // 200–215

          return (
            <div
              key={`scan-${i}`}
              className={`absolute animate-pulse ${isHorizontal ? 'h-[1px] w-full' : 'w-[1px] h-full'}`}
              style={{
                background: `linear-gradient(${isHorizontal ? '90deg' : '180deg'},
                  transparent,
                  hsla(${hue}, 100%, 65%, ${0.6 + Math.random() * 0.3}),
                  hsla(${getHue(5)}, 100%, 50%, ${0.5 + Math.random() * 0.3}),
                  transparent)`,
                [isHorizontal ? 'top' : 'left']: `${Math.max(40, Math.min(90, randomY))}%`,
                filter: `blur(${0.6 + Math.random() * 1}px) brightness(1.4)`,
                boxShadow: `0 0 ${8 + Math.random() * 12}px hsla(${hue}, 100%, 60%, 0.7)`,
                animation: `scanLine ${6 + Math.random() * 8}s ease-in-out infinite ${Math.random() * 2}s`,
                opacity: 0.4 + Math.random() * 0.5,
              }}
            />
          );
        })}
      </div>

    </div>
  );
}