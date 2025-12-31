import { Separator } from "@/components/ui/separator";

const AboutPage: React.FC = () => {
  return (
    <div className="container py-10 flex flex-col items-center">
      <div className="max-w-2xl w-full space-y-8 text-center">
        <h1 className="text-3xl font-bold tracking-tight">智能客服</h1>

        <Separator className="w-3/4 mx-auto" />

        {/* 生成式人工智能算法说明 */}
        <section className="space-y-4">
          <h2 className="text-2xl font-semibold">生成式人工智能算法说明</h2>
          <p className="text-muted-foreground leading-relaxed">
            本服务所采用的智能问答功能，基于阿里云研发的通义千问大语言模型（
            <span className="font-medium text-foreground">Qwen3-32B</span>
            ）。该模型通过海量文本训练，具备自然语言理解与生成能力，旨在辅助用户获取信息、提升效率。
          </p>
          <p className="text-muted-foreground leading-relaxed">
            需特别说明的是，大语言模型的输出内容系基于概率生成，可能存在事实性偏差、逻辑不一致或虚构信息。因此，模型输出
            <span className="font-medium text-foreground">
              不得用于医疗诊断、治疗建议、法律意见、政策执行或任何高风险决策场景
            </span>
            。用户应结合专业渠道进行核实，并自行承担使用风险。
          </p>
          <p className="text-muted-foreground leading-relaxed">
            本系统已对敏感内容与高风险领域实施过滤与提示机制，但无法保证100%准确或覆盖所有情形。请用户理性判断，审慎使用。
          </p>
        </section>
      </div>
    </div>
  );
};

export default AboutPage;