import { Separator } from "@/components/ui/separator";

const AboutPage: React.FC = () => {
  return (
    <div className="container py-10 flex flex-col items-center">
      <div className="max-w-2xl w-full space-y-8 text-center">
        <h1 className="text-3xl font-bold tracking-tight">公积金助手</h1>

        <Separator className="w-3/4 mx-auto" />

        {/* 关于公积金助手 */}
        <section className="space-y-4">

          <p className="text-muted-foreground leading-relaxed">
            公积金助手是基于<span className="font-medium text-foreground">大语言模型</span>的智能公积金政策咨询服务平台。我们致力于为用户提供便捷、准确的公积金政策解读，帮助您更好地理解和运用各项公积金政策。
          </p>

          <div className="space-y-3 text-left bg-muted/50 p-6 rounded-lg">
            <div className="flex items-start gap-3">
              <div className="w-2 h-2 rounded-full bg-primary mt-2 shrink-0"></div>
              <p className="text-muted-foreground leading-relaxed">
                <span className="font-medium text-foreground">政策咨询:</span> 提供公积金政策、提取流程、贷款标准等全方位咨询服务
              </p>
            </div>

            <div className="flex items-start gap-3">
              <div className="w-2 h-2 rounded-full bg-primary mt-2 shrink-0"></div>
              <p className="text-muted-foreground leading-relaxed">
                <span className="font-medium text-foreground">智能解读:</span> 基于最新的公积金政策文件，为您提供准确的政策解读
              </p>
            </div>

            <div className="flex items-start gap-3">
              <div className="w-2 h-2 rounded-full bg-primary mt-2 shrink-0"></div>
              <p className="text-muted-foreground leading-relaxed">
                <span className="font-medium text-foreground">便捷服务:</span> 7×24小时在线咨询，随时解答您的公积金疑问
              </p>
            </div>
          </div>
        </section>
        <Separator className="w-3/4 mx-auto" />

        {/* 使用须知与免责声明 */}
        <section className="space-y-4">
          <h2 className="text-2xl font-semibold">使用须知与免责声明</h2>

          <p className="text-muted-foreground leading-relaxed">
            本系统已对公积金政策相关的敏感内容与高风险领域实施过滤与提示机制，但无法保证100%准确或覆盖所有情形。
          </p>

          <div className="space-y-2 text-left text-sm text-muted-foreground bg-muted/30 p-5 rounded-lg">
            <p className="font-medium text-foreground mb-3">请用户注意：</p>

            <div className="flex items-start gap-2">
              <span className="text-primary">•</span>
              <p>本服务仅供参考，不构成任何形式的公积金政策执行依据</p>
            </div>

            <div className="flex items-start gap-2">
              <span className="text-primary">•</span>
              <p>具体提取额度和贷款标准请以缴存地公积金部门规定为准</p>
            </div>

            <div className="flex items-start gap-2">
              <span className="text-primary">•</span>
              <p>涉及重大公积金决策或业务办理时，请咨询当地公积金经办机构</p>
            </div>

            <div className="flex items-start gap-2">
              <span className="text-primary">•</span>
              <p>用户应自行承担使用本服务产生的风险和责任</p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default AboutPage;