# 创新药论文分析系统

## 项目简介

这是一个基于大模型的创新药学术论文分析系统，能够自动分析论文内容，提取结构化信息，包括主体层级分类、关系类型、创新认知标记等。

## 功能特点

- 🔍 **智能分析**: 使用Claude Sonnet 4模型进行深度论文分析
- 🏷️ **主体分类**: 自动识别药企、政府、科研机构、保险方等主体
- 🔗 **关系识别**: 分析主体间的合作关系、冲突关系、监管关系等
- 💡 **创新标记**: 识别不同主体对创新的认知差异
- ⚡ **多线程处理**: 支持并发分析，提高处理效率
- 📊 **统计分析**: 自动生成分析结果统计报告

## 文件结构

```
创新药.md/
├── academic_paper_analyzer.py    # 主分析脚本
├── tag-academic-paper-prompt.md  # 系统提示词
├── chuangxinyao.json            # 论文数据
├── requirements.txt              # 依赖包
└── README.md                    # 说明文档
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

1. **确保文件存在**:
   - `tag-academic-paper-prompt.md`: 系统提示词文件
   - `chuangxinyao.json`: 论文数据文件

2. **运行分析**:
   ```bash
   python academic_paper_analyzer.py
   ```

3. **查看结果**:
   - `academic_paper_analysis_results.json`: 详细分析结果
   - `analysis_statistics.json`: 统计分析报告

## 输出格式

### 分析结果字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `paper_id` | string | 论文ID (年份_标题前8字) |
| `year` | int | 发表年份 |
| `level1_xxx` | boolean | 一级标签是否出现 |
| `level2_xxx` | string | 二级标签具体内容 |
| `method_type` | string | 研究方法类型 |
| `method_detail` | string | 研究方法详情 |
| `innovation_diff` | boolean | 是否涉及创新认知差异 |
| `multi_stakeholder` | boolean | 是否有多主体评价 |
| `weight_allocation` | boolean | 是否涉及权重分配 |
| `coordination_mechanism` | boolean | 是否有协调机制 |
| `relationships` | string | 主体间关系 |
| `relationship_types` | string | 关系类型 |
| `innovation_view_xxx` | string | 各主体创新观点 |
| `key_assumption` | string | 关键假设 |
| `main_conclusion` | string | 主要结论 |
| `gap_xxx` | string | 研究空白 |

### 主体分类体系

#### 一级标签
- `pharma`: 药企相关
- `government`: 政府部门
- `research`: 科研机构
- `insurance`: 保险方
- `others`: 其他主体

#### 二级标签
- **pharma**: 创新药企、仿制药企、跨国药企、本土药企、原研药企
- **government**: 医保局、卫健委、药监局、科技部、发改委、知识产权局
- **research**: 大学、研究院、医院研发、实验室
- **insurance**: 商业保险公司、健康险
- **others**: 患者、医生、行业协会、投资机构、CRO

## 配置说明

### API配置
脚本中已配置API密钥和URL：
```python
api_key = "REDACTED_API_KEY"
api_url = "https://openai.app.msh.team/v1"
```

### 线程配置
默认使用20个线程进行并发处理，可根据需要调整：
```python
max_workers=20
```

## 性能优化

- **并发处理**: 使用ThreadPoolExecutor实现多线程分析
- **进度监控**: 实时显示处理进度和统计信息
- **错误处理**: 完善的异常处理机制
- **结果验证**: JSON格式验证和错误提示

## 注意事项

1. 确保网络连接稳定，能够访问API服务
2. 大量论文分析可能需要较长时间，请耐心等待
3. 分析结果会保存为JSON格式，便于后续处理
4. 如遇到API限制，可适当减少并发线程数

## 技术支持

如有问题，请检查：
- 依赖包是否正确安装
- 文件路径是否正确
- API密钥是否有效
- 网络连接是否正常 