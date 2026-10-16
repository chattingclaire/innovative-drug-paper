#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re, sys

REFS = {
"hu2019": "胡善联．中国基本医疗保险药品目录调整的历程与展望[J]．中国卫生经济，2019，38(1)：5-11．",
"chang2021": "常峰，吴晶，谈在祥．医保药品目录动态调整的价值导向研究[J]．中国医疗保险，2021(2)：32-37．",
"kong2022": "孔繁翠．创新药价值评估的国际经验比较及启示[J]．中国卫生政策研究，2022，15(6)：17-23．",
"duan2017": "段晓托，连桂玉，贾耀珠．我国创新药进入医保目录的障碍与对策[J]．中国药房，2017，28(4)：455-457．",
"zhao2019": "赵华婷，颜建周，邵蓉．法国临床效益评价对我国创新药医保目录动态调整的启示[J]．中国卫生经济，2019，38(5)：94-96．",
"ai2020": "艾丹丹，陈辰，吴婷婷，等．价值医疗背景下创新药品的定价和支付模式综述[J]．中国卫生经济，2020，39(3)：77-79．",
"kang2010": "康姗姗，胡霞，颜建周．药品上市决策中的多方利益博弈[J]．中国药房，2010，21(21)：1921-1925．",
"zhangxx2017": "张新鑫，侯文华，申成霖．价格管制、战略性创新激励与创新药市场绩效[J]．科研管理，2017，38(10)：68-75．",
"tan2024": "谭清立，李永盈，崔洪瑞．创新药医保谈判的博弈分析[J]．卫生经济研究，2024，41(6)：5-9，15．",
"wang2023": "王恩楠，朱铭来．我国专利药品医疗保险价格谈判的演化博弈研究[J]．中国卫生政策研究，2023，16(2)：44-51．",
"lv2024": "吕倩鹏，吴红，刘智勇．政策工具视角下我国创新药物研发政策量化研究[J]．中国卫生事业管理，2024，41(12)：1393-1399．",
"mao2021": "毛心仪，姚峥嵘．制度创新理论视角下我国药品研发制度变迁设计[J]．卫生经济研究，2021，38(7)：38-43．",
"yang2024": "杨钰婷，胡婉慈，左根永．我国医疗保险国谈药品单独支付政策省际比较研究[J]．中国卫生政策研究，2024，17(1)：24-29．",
"casilli2023": "CASILLI G, LIDONNICI D, JOMMI C, et al. Do France, Germany, and Italy Agree on the Added Therapeutic Value of Medicines?[J]. International Journal of Technology Assessment in Health Care, 2023, 39(1): e54.",
"garau2017": "GARAU M, HAMPSON G, DEVLIN N, et al. Applying a Multicriteria Decision Analysis (MCDA) Approach to Elicit Stakeholders' Preferences in Italy: The Case of Obinutuzumab for Rituximab-Refractory Indolent Non-Hodgkin Lymphoma (iNHL)[J]. PharmacoEconomics Open, 2018, 2(2): 153-163.",
"kesselheim2013": "KESSELHEIM A S, WANG B, AVORN J. Defining \"Innovativeness\" in Drug Development: A Systematic Review[J]. Clinical Pharmacology & Therapeutics, 2013, 94(3): 336-348.",
"monleon2022": "MONLEÓN C, SPÄTH H M, CRESPO C, et al. Systematic Literature Review on the Implicit Factors Influencing the Health Technology Assessment Deliberative Process in Europe[J]. Journal of Market Access & Health Policy, 2022, 10(1): 2094047.",
"kallberg2023": "KÅLLBERG C, MATHIESEN L, GOPINATHAN U, et al. The Role of Drug Regulatory Authorities and Health Technology Assessment Agencies in Shaping Incentives for Antibiotic R&D: A Qualitative Study[J]. Journal of Pharmaceutical Policy and Practice, 2023, 16: 53.",
"mundy2024": "MUNDY L, FORREST B, HUANG L Y, et al. Health Technology Assessment and Innovation: Here to Help or Hinder?[J]. International Journal of Technology Assessment in Health Care, 2024, 40(1): e37.",
"janssens2023": "JANSSENS R, BARBIER L, MULLER M, et al. How Can Patient Preferences Be Used and Communicated in the Regulatory Evaluation of Medicinal Products? Findings and Recommendations from IMI PREFER and Call to Action[J]. Frontiers in Pharmacology, 2023, 14: 1192770.",
"mountford2023": "MOUNTFORD N, CAI Y. Towards a Flatter Ontology of Institutional Logics: How Logics Relate in Situations of Institutional Complexity[J]. International Journal of Management Reviews, 2023, 25(2): 363-383.",
"simon1997": "SIMON H A. Administrative Behavior: A Study of Decision-Making Processes in Administrative Organizations[M]. 4th ed. New York: Free Press, 1997.",
"cyert1963": "CYERT R M, MARCH J G. A Behavioral Theory of the Firm[M]. Englewood Cliffs: Prentice-Hall, 1963.",
"walsh1995": "WALSH J P. Managerial and Organizational Cognition: Notes from a Trip Down Memory Lane[J]. Organization Science, 1995, 6(3): 280-321.",
"li2024": "李梦颖，伍琳，王昕妍，等．我国医保谈判药品落地问题的多重制度逻辑分析与政策建议[J]．中国药房，2024，35(14)：1683-1689．",
"freeman1984": "FREEMAN R E. Strategic Management: A Stakeholder Approach[M]. Boston: Pitman, 1984.",
"thornton2008": "THORNTON P H, OCASIO W. Institutional logics[M]//GREENWOOD R, OLIVER C, SAHLIN K, et al. The SAGE Handbook of Organizational Institutionalism. London: SAGE, 2008: 99-129.",
"greenwood2011": "GREENWOOD R, RAYNARD M, KODEIH F, et al. Institutional Complexity and Organizational Responses[J]. Academy of Management Annals, 2011, 5(1): 317-371.",
"ocasio1997": "OCASIO W. Towards an Attention-Based View of the Firm[J]. Strategic Management Journal, 1997, 18(S1): 187-206.",
"wen2014": "文宏．中国政府推进基本公共服务的注意力测量——基于中央政府工作报告（1954—2013）的文本分析[J]．吉林大学社会科学学报，2014，54(2)：20-26．",
"tao2020": "陶鹏，初春．府际结构下领导注意力的议题分配与优先——基于公开批示的分析[J]．公共行政评论，2020，13(1)：63-78．",
"sevenans2014": "SEVENANS J, ALBAUGH Q, SHAHAF T, et al. The Automated Coding of Policy Agendas: A Dictionary-Based Approach (Version 2.0)[R]. The 7th Annual Conference of the Comparative Agendas Project, Konstanz, 2014.",
"zeng2023": "曾润喜，莫敏丽．政府注意力的测量：路径、内容与展望[J]．华中科技大学学报（社会科学版），2023，37(1)：66-73．",
"loughran2011": "LOUGHRAN T, MCDONALD B. When Is a Liability Not a Liability? Textual Analysis, Dictionaries, and 10-Ks[J]. The Journal of Finance, 2011, 66(1): 35-65.",
"grimmer2013": "GRIMMER J, STEWART B M. Text as Data: The Promise and Pitfalls of Automatic Content Analysis Methods for Political Texts[J]. Political Analysis, 2013, 21(3): 267-297.",
"nmpa2020": "国家市场监督管理总局．药品注册管理办法（国家市场监督管理总局令第27号）[Z]．2020．",
"nhc2021": "国家卫生健康委办公厅．药品临床综合评价管理指南（2021年版 试行）（国卫办药政发〔2021〕16号）[Z]．2021．",
"nhsa2020": "国家医疗保障局．基本医疗保险用药管理暂行办法（国家医疗保障局令第1号）[Z]．2020．",
"gov2015": "国务院．关于改革药品医疗器械审评审批制度的意见（国发〔2015〕44号）[Z]．2015．",
"gilardi2023": "GILARDI F, ALIZADEH M, KUBLI M. ChatGPT Outperforms Crowd Workers for Text-Annotation Tasks[J]. Proceedings of the National Academy of Sciences, 2023, 120(30): e2305016120.",
"xie2018": "谢金平，孙圆圆，彭楠，等．药品上市许可持有人（MAH）制度对现行监管制度的影响及衔接建议[J]．中国卫生政策研究，2018，11(12)：1-6．",
"yue2021": "岳晓萌，李钰翔，赵绯丽，等．医保药品目录调整之退出机制的国际经验借鉴[J]．医药导报，2021，40(2)：158-162．",
"maohui2025": "毛晖，张泽丰，陈政弘．和衷共济，利在其中：国家医保谈判的经济效应与健康效应[J]．财经研究，2025，51(9)：64-78．",
"dewar1986": "DEWAR R D, DUTTON J E. The Adoption of Radical and Incremental Innovations: An Empirical Analysis[J]. Management Science, 1986, 32(11): 1422-1433.",
"landis1977": "LANDIS J R, KOCH G G. The Measurement of Observer Agreement for Categorical Data[J]. Biometrics, 1977, 33(1): 159-174.",
"dunlap2010": "DUNLAP-HINKLER D, KOTABE M, MUDAMBI R. A Story of Breakthrough versus Incremental Innovation: Corporate Entrepreneurship in the Global Pharmaceutical Industry[J]. Strategic Entrepreneurship Journal, 2010, 4(2): 106-127.",
}


REFS_EN = {
"hu2019": "Hu S L. Retrospect and Prospect of the Adjustment of China's Basic Medical Insurance Drug List [J]. Chinese Health Economics, 2019, 38(1): 5-11.",
"chang2021": "Chang F, Wu J, Tan Z X. Research on the Value Orientation of Dynamic Adjustment of the Medical Insurance Drug Catalogue [J]. China Health Insurance, 2021(2): 32-37.",
"kong2022": "Kong F C. International Experience Comparison and Implications of Value Assessment of Innovative Drugs [J]. Chinese Journal of Health Policy, 2022, 15(6): 17-23.",
"duan2017": "Duan X T, Lian G Y, Jia Y Z. Obstacles and Countermeasures for Innovative Drugs to Enter the Medical Insurance Catalogue in China [J]. China Pharmacy, 2017, 28(4): 455-457.",
"zhao2019": "Zhao H T, Yan J Z, Shao R. Implications of France's Clinical Benefit Assessment for the Dynamic Adjustment of China's Medical Insurance Catalogue for Innovative Drugs [J]. Chinese Health Economics, 2019, 38(5): 94-96.",
"ai2020": "Ai D D, Chen C, Wu T T, et al. Review on Pricing and Payment Models of Innovative Drugs under Value-Based Healthcare [J]. Chinese Health Economics, 2020, 39(3): 77-79.",
"kang2010": "Kang S S, Hu X, Yan J Z. Multi-Party Interest Game in Drug Marketing Decision [J]. China Pharmacy, 2010, 21(21): 1921-1925.",
"zhangxx2017": "Zhang X X, Hou W H, Shen C L. Price Regulation, Strategic Innovation Incentives and Market Performance of Innovative Drugs [J]. Science Research Management, 2017, 38(10): 68-75.",
"tan2024": "Tan Q L, Li Y Y, Cui H R. Game Analysis of Medical Insurance Negotiation for Innovative Drugs [J]. Health Economics Research, 2024, 41(6): 5-9, 15.",
"wang2023": "Wang E N, Zhu M L. Evolutionary Game Study on Medical Insurance Price Negotiation of Patented Drugs in China [J]. Chinese Journal of Health Policy, 2023, 16(2): 44-51.",
"lv2024": "Lv Q P, Wu H, Liu Z Y. Quantitative Research on China's Innovative Drug R&D Policies from the Perspective of Policy Instruments [J]. Chinese Health Service Management, 2024, 41(12): 1393-1399.",
"mao2021": "Mao X Y, Yao Z R. Institutional Change of China's Drug R&D System from the Perspective of Institutional Innovation Theory [J]. Health Economics Research, 2021, 38(7): 38-43.",
"yang2024": "Yang Y T, Hu W C, Zuo G Y. Inter-Provincial Comparative Study on Separate Payment Policies for Nationally Negotiated Drugs in China [J]. Chinese Journal of Health Policy, 2024, 17(1): 24-29.",
"li2024": "Li M Y, Wu L, Wang X Y, et al. Multiple Institutional Logics Analysis and Policy Suggestions on the Implementation of Negotiated Drugs in China [J]. China Pharmacy, 2024, 35(14): 1683-1689.",
"wen2014": "Wen H. Measuring Government Attention to Basic Public Services: A Text Analysis of Central Government Work Reports (1954-2013) [J]. Jilin University Journal Social Sciences Edition, 2014, 54(2): 20-26.",
"tao2020": "Tao P, Chu C. Issue Allocation and Priority of Leadership Attention in Intergovernmental Structure: An Analysis Based on Public Instructions [J]. Journal of Public Administration, 2020, 13(1): 63-78.",
"zeng2023": "Zeng R X, Mo M L. Measuring Government Attention: Approaches, Contents and Prospects [J]. Journal of Huazhong University of Science and Technology (Social Science Edition), 2023, 37(1): 66-73.",
"xie2018": "Xie J P, Sun Y Y, Peng N, et al. Impact of the Marketing Authorization Holder (MAH) System on Current Regulatory Institutions and Suggestions for Convergence [J]. Chinese Journal of Health Policy, 2018, 11(12): 1-6.",
"yue2021": "Yue X M, Li Y X, Zhao F L, et al. International Experience of Exit Mechanisms in Medical Insurance Drug Catalogue Adjustment [J]. Herald of Medicine, 2021, 40(2): 158-162.",
"maohui2025": "Mao H, Zhang Z F, Chen Z H. Economic and Health Effects of National Medical Insurance Negotiation [J]. Journal of Finance and Economics, 2025, 51(9): 64-78.",
"nmpa2020": "State Administration for Market Regulation. Provisions for Drug Registration (SAMR Order No. 27) [Z]. 2020.",
"nhc2021": "General Office of the National Health Commission. Administrative Guidelines for Comprehensive Clinical Evaluation of Drugs (2021 Edition, for Trial Implementation) [Z]. 2021.",
"nhsa2020": "National Healthcare Security Administration. Interim Measures for the Administration of Basic Medical Insurance Drugs (NHSA Order No. 1) [Z]. 2020.",
"gov2015": "The State Council. Opinions on Reforming the Review and Approval System for Drugs and Medical Devices (No. 44 [2015]) [Z]. 2015.",
}

src = open(sys.argv[1], encoding='utf-8').read()

keys_in_order = []
for m in re.finditer(r'\[@([A-Za-z0-9]+)\]', src):
    k = m.group(1)
    if k not in REFS:
        sys.exit(f"UNKNOWN KEY: {k}")
    if k not in keys_in_order:
        keys_in_order.append(k)

num = {k: i+1 for i, k in enumerate(keys_in_order)}

# replace groups of adjacent citations
def repl_group(m):
    ks = re.findall(r'\[@([A-Za-z0-9]+)\]', m.group(0))
    inner = ''.join(f'\\[{num[k]}\\]' for k in ks)
    return f'^{inner}^'

out = re.sub(r'(?:\[@[A-Za-z0-9]+\])+', repl_group, src)

def refline(k):
    line = f'\\[{num[k]}\\] {REFS[k]}'
    if k in REFS_EN:
        line += '\\\n' + REFS_EN[k]
    return line
reflist = '\n\n'.join(refline(k) for k in keys_in_order)
out = out.replace('REFS_PLACEHOLDER', reflist)

unused = [k for k in REFS if k not in num]
open(sys.argv[2], 'w', encoding='utf-8').write(out)
print(f"citations: {len(keys_in_order)} refs; unused defined: {unused}")
