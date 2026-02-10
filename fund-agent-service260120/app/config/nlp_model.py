import spacy

def get_nlp_model():
    """获取中文 spaCy 模型，如果不存在则自动下载"""
    try:
        nlp = spacy.load("zh")
        return nlp
    except OSError:
        print("中文模型未找到，正在下载...")
        # 下载并安装中文基础包
        spacy.cli.download("zh_core_web_sm")
        # 加载下载的模型
        nlp = spacy.load("zh_core_web_sm")
        print("中文模型下载并加载完成！")
        return nlp

def extract_question(text):
    doc = nlp(text)
    
    # 寻找疑问动词或疑问词
    question_indicators = ["查询"]
    
    for i, token in enumerate(doc):
        if any(indicator in token.text for indicator in question_indicators):
            # 从这个token开始到句子末尾
            question_tokens = []
            for j in range(i, len(doc)):
                if doc[j].text in ["？", "?"]:
                    question_tokens.append(doc[j].text)
                    break
                question_tokens.append(doc[j].text)
            
            return "".join(question_tokens).strip("？？")
    
    return None


if __name__ =='__main__':
    text = "我的姓名有变更，咨询个人公积金账户信息变更如何办理？"
    question = extract_question(text)
    print(f"提取的问题: {question}")