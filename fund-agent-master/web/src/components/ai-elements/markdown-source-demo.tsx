"use client";

import { Message, MessageContent } from "./message";
import type { Source } from "@/hooks/use-qwen-chat";

// 示例source数据
const demoSources: Source[] = [
  {
    id: "1",
    title: "厦门市住房公积金管理中心-公积金缴存证明打印",
    url: "https://gjj.xm.gov.cn/cjwt/202303/t20230315_123456.html",
    description: "厦门市公积金缴存证明打印的官方办事指南，包括办理条件、材料要求和办理流程。",
    snippet: "缴存人可通过厦门市住房公积金管理中心官网、微信公众号、自助终端机等多种渠道打印公积金缴存证明。办理时需提供有效身份证件。"
  },
  {
    id: "2",
    title: "福建省住房公积金信息平台-异地购房提取",
    url: "https://gjj.fujian.gov.cn/ydgf/202301/t20230120_654321.html",
    description: "福建省异地购房提取公积金的政策说明和办理流程。",
    snippet: "厦门公积金缴存人员在异地购房后，可申请提取厦门公积金用于偿还贷款或支付购房款。可通过线上平台或线下公积金经办机构办理。"
  }
];

export const MarkdownSourceDemo = () => {
  const assistantMessage = {
    id: 1,
    role: "assistant" as const,
    content: `根据您的问题，我为您提供以下信息：

## 公积金缴存证明打印

您可以通过以下方式打印厦门市的公积金缴存证明：[[source:0]]

## 异地购房提取公积金

厦门公积金缴存人在外地购房的提取需要：[[source:1]]

**具体操作步骤：**

1. **登录系统** - 访问公积金官网或手机APP
2. **准备材料** - 身份证、购房合同、贷款合同等
3. **提交申请** - 在线填写提取申请表
4. **等待审核** - 一般需要3-5个工作日

更多信息请参考相关政策文件。`,
    sources: demoSources
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-4">Markdown中的Source引用功能演示</h2>
      <p className="text-muted-foreground mb-6">
        这个演示展示了如何在Markdown内容中直接嵌入source引用标签。使用 <code>[[source:N]]</code> 语法在文本中插入引用，
        其中N是source的索引号（从0开始）。点击蓝色标签可以查看详细引用信息。
      </p>

      <div className="space-y-4">
        <Message
          from={assistantMessage.role}
          messageId={assistantMessage.id}
          sources={assistantMessage.sources}
        >
          <MessageContent isUser={false} sources={assistantMessage.sources}>
            {assistantMessage.content}
          </MessageContent>
        </Message>
      </div>

      <div className="mt-8 p-4 bg-muted rounded-lg">
        <h3 className="font-semibold mb-2">支持的引用语法：</h3>
        <ul className="space-y-1 text-sm">
          <li><code>[[source:0]]</code> - 引用第一个source</li>
          <li><code>[[source:1]]</code> - 引用第二个source</li>
          <li><code>[[source:文档标题]]</code> - 按标题引用（暂未实现）</li>
        </ul>
      </div>
    </div>
  );
};