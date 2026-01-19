"use client";

import { Message, MessageContent } from "./message";
import type { Source } from "@/hooks/use-qwen-chat";

// 示例source数据
const demoSources: Source[] = [
  {
    id: "1",
    title: "厦门市医疗保障管理局-医保参保凭证打印",
    url: "https://ybj.xm.gov.cn/ylbx/czjb/202303/t20230315_123456.html",
    description: "厦门市医保参保凭证打印的官方办事指南，包括办理条件、材料要求和办理流程。",
    snippet: "参保人可通过厦门市医疗保障管理局官网、微信公众号、社保自助终端机等多种渠道打印医保参保凭证。办理时需提供有效身份证件和社保卡。"
  },
  {
    id: "2",
    title: "福建省医疗保障信息平台-异地就医备案",
    url: "https://ybj.fujian.gov.cn/ylbx/ydjy/202301/t20230120_654321.html",
    description: "福建省异地就医备案的政策说明和办理流程。",
    snippet: "厦门医保参保人员在异地就医前，需要办理异地就医备案手续。可通过线上平台或线下医保经办机构办理，备案后可直接结算医疗费用。"
  }
];

export const MarkdownSourceDemo = () => {
  const assistantMessage = {
    id: 1,
    role: "assistant" as const,
    content: `根据您的问题，我为您提供以下信息：

## 医保参保凭证打印

您可以通过以下方式打印厦门市的医保参保凭证：[[source:0]]

## 异地就医报销

厦门参保人在外地就医的费用报销需要：[[source:1]]

**具体操作步骤：**

1. **登录系统** - 访问医保官网或手机APP
2. **准备材料** - 身份证、社保卡、病历资料
3. **提交申请** - 在线填写报销申请表
4. **等待审核** - 一般需要5-7个工作日

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