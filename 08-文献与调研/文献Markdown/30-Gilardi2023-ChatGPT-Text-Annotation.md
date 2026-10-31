# 30-Gilardi2023-ChatGPT-Text-Annotation

> 原件：参考文献原件-按论文编号-20261023/30-Gilardi2023-ChatGPT-Text-Annotation.pdf

<!-- 第1页 -->
CHATGPT OUTPERFORMS CROWD-WORKERS
FOR TEXT-ANNOTATION TASKS
Fabrizio Gilardi∗
University of Zurich
Zurich, Switzerland
Meysam Alizadeh
University of Zurich
Zurich, Switzerland
Maël Kubli
University of Zurich
Zurich, Switzerland
Published in the Proceedings of the National Academy of Sciences
https://www.pnas.org/doi/10.1073/pnas.2305016120
ABSTRACT
Many NLP applications require manual text annotations for a variety of tasks, notably
to train classifiers or evaluate the performance of unsupervised models. Depending
on the size and degree of complexity, the tasks may be conducted by crowd-workers
on platforms such as MTurk as well as trained annotators, such as research assistants.
Using four samples of tweets and news articles (n = 6,183), we show that ChatGPT
outperforms crowd-workers for several annotation tasks, including relevance, stance,
topics, and frame detection. Across the four datasets, the zero-shot accuracy of
ChatGPT exceeds that of crowd-workers by about 25 percentage points on average,
while ChatGPT’s intercoder agreement exceeds that of both crowd-workers and
trained annotators for all tasks. Moreover, the per-annotation cost of ChatGPT is
less than $0.003—about thirty times cheaper than MTurk. These results demonstrate
the potential of large language models to drastically increase the efficiency of text
classification.
1
Introduction
Many NLP applications require high-quality labeled data, notably to train classifiers or evaluate
the performance of unsupervised models. For example, researchers often aim to filter noisy social
media data for relevance, assign texts to different topics or conceptual categories, or measure
their sentiment or stance. Regardless of the specific approach used for these tasks (supervised,
semi-supervised, or unsupervised), labeled data are needed to build a training set or a gold standard
against which performance can be assessed. Such data may be available for high-level tasks
such as semantic evaluation (Emerson et al., 2022). More typically, however, researchers have to
conduct original annotations to ensure that the labels match their conceptual categories (Benoit
et al., 2016). Until recently, two main strategies were available. First, researchers can recruit and
train coders, such as research assistants. Second, they can rely on crowd-workers on platforms
∗Corresponding author (https://fabriziogilardi.org/).
arXiv:2303.15056v2  [cs.CL]  19 Jul 2023

<!-- 第2页 -->
ChatGPT outperforms crowd-workers for text-annotation tasks
such as Amazon Mechanical Turk (MTurk). Often, these two strategies are used in combination:
trained annotators create a relatively small gold-standard dataset, and crowd-workers are employed
to increase the volume of labeled data. Trained annotators tend to produce high-quality data,
but involve significant costs. Crowd workers are a much cheaper and more flexible option, but
the quality may be insufficient, particularly for complex tasks and languages other than English.
Moreover, there have been concerns that MTurk data quality has decreased (Chmielewski and
Kucker, 2020), while alternative platforms such as CrowdFlower and FigureEight are no longer
practicable options for academic research since they were acquired by Appen, a company that is
focused on a business market.
This paper explores the potential of large language models (LLMs) for text annotation tasks, with a
focus on ChatGPT, which was released in November 2022. It demonstrates that zero-shot ChatGPT
classifications (that is, without any additional training) outperform MTurk annotations, at a fraction
of the cost. LLMs have been shown to perform very well for a wide range of purposes, including
ideological scaling (Wu et al., 2023), the classification of legislative proposals (Nay, 2023), the
resolution of cognitive psychology tasks (Binz and Schulz, 2023), and the simulation of human
samples for survey research (Argyle et al., 2023). While a few studies suggested that ChatGPT
might perform text annotation tasks of the kinds we have described (Kuzman, Mozetiˇc and Ljubeši´c,
2023; Huang, Kwak and An, 2023), to the best of our knowledge our work is the first systematic
evaluation. Our analysis relies on a sample of 6,183 documents, including tweets and news articles
that we collected for a previous study (Alizadeh et al., 2022) as well as a new sample of tweets
posted in 2023. In our previous study, the texts were labeled by trained annotators (research
assistants) for five different tasks: relevance, stance, topics, and two kinds of frame detection.
Using the same codebooks that we developed to instruct our research assistants, we submitted the
tasks to ChatGPT as zero-shot classifications, as well as to crowd-workers on MTurk. We then
evaluated the performance of ChatGPT against two benchmarks: (i) its accuracy, relative to that
of crowd-workers, and (ii) its intercoder agreement, relative to that of crowd workers as well as
of our trained annotators. We find that across the four datasets, ChatGPT’s zero-shot accuracy is
higher than that of MTurk for most tasks. For all tasks, ChatGPT’s intercoder agreement exceeds
that of both MTurk and trained annotators. Moreover, ChatGPT is significantly cheaper than MTurk.
ChatGPT’s per-annotation cost is about $0.003, or a third of a cent—about thirty times cheaper than
MTurk, with higher quality. At this cost, it might potentially be possible to annotate entire samples,
or to create large training sets for supervised learning. While further research is needed to better
understand how ChatGPT and other LLMs perform in a broader range of contexts, these results
demonstrate their potential to transform how researchers conduct data annotations, and to disrupt
parts of the business model of platforms such as MTurk.
2
Results
We use four datasets (n = 6, 183) including tweets and news articles that we collected and annotated
manually for a previous study on the discourse around content moderation (Alizadeh et al., 2022), as
well as a new sample of tweets posted in 2023 to address the concern that ChatGPT might be relying
on memorization for texts potentially included in the model’s training dataset. We relied on trained
annotators (research assistants) to construct a gold standard for six conceptual categories: relevance
of tweets for the content moderation issue (relevant/irrelevant); relevance of tweets for political
issues (relevant/irrelevant); stance regarding Section 230, a key part of US internet legislation
2

<!-- 第3页 -->
ChatGPT outperforms crowd-workers for text-annotation tasks
Accuracy
Intercoder Agreement
0%
25%
50%
75% 100% 0%
25%
50%
75% 100%
Frames II
Frames I
Topics
Stance
Relevance
A. Tweets (2020−2021)
Accuracy
Intercoder Agreement
0%
25% 50% 75% 100% 0%
25% 50% 75% 100%
Frames I
Relevance
B. News Articles (2020−2021)
Accuracy
Intercoder Agreement
0%
25% 50% 75% 100% 0%
25% 50% 75% 100%
Frames I
Relevance
C. Tweets (2023)
Accuracy
Intercoder Agreement
0%
25% 50% 75% 100% 0%
25% 50% 75% 100%
Frames II
Relevance
D. Tweets (2017−2022)
Trained annotators
MTurk
ChatGPT (temp 1)
ChatGPT (temp 0.2)
Figure 1: ChatGPT zero-shot text annotation performance in four datasets, compared to MTurk
and trained annotators. ChatGPT’s accuracy outperforms that of MTurk for most tasks. ChatGPT’s
intercoder agreement outperforms that of both MTurk and trained annotators in all tasks. Accuracy
means agreement with the trained annotators.
(keep/repeal/neutral); topic identification (six classes); a first set of frames (content moderation
as a problem, as a solution, or neutral); and a second set of frames (fourteen classes). We then
performed these exact same classifications with ChatGPT and with crowd-workers recruited on
MTurk, using the same codebook we developed for our research assistants (see SI Appendix). For
ChatGPT, we conducted four sets of annotations. To explore the effect of ChatGPT’s temperature
parameter, which controls the degree of randomness of the output, we conducted the annotations
with the default value of 1 as well as with a value of 0.2, which implies less randomness. For
each temperature value, we conducted two sets of annotations to compute ChatGPT’s intercoder
agreement. For MTurk, we aimed to select high-quality crowd-workers, notably by filtering for
workers who are classified as “MTurk Masters” by Amazon, who have an approval rate of over
90%, and who are located in the US. Our procedures are described more in detail in the Materials
and Methods section.
Across the four datasets, we report ChatGPT’s zero-shot performance for two different metrics:
accuracy and intercoder agreement (Figure 1). Accuracy is measured as the percentage of correct
annotations (using our trained annotators as a benchmark), while intercoder agreement is computed
as the percentage of tweets that were assigned the same label by two different annotators (research
assistant, crowd-workers, or ChatGPT runs). Regarding accuracy, Figure 1 shows that ChatGPT
outperforms MTurk for most tasks across the four datasets. On average, ChatGPT’s accuracy
exceeds that of MTurk by about 25 percentage points. Moreover, ChatGPT demonstrates adequate
accuracy overall, considering the challenging tasks, number of classes, and zero-shot annotations.
Accuracy rates for relevance tasks, with two classes (relevant/irrelevant) are 70% for content
3

<!-- 第4页 -->
ChatGPT outperforms crowd-workers for text-annotation tasks
moderation tweets, 81% for content moderation news articles, 83% for US Congress tweets, and
59% for 2023 content moderation tweets. In the 2023 sample, ChatGPT performed much better than
MTurk in the second task but struggled with misclassifying tweets about specific user suspensions
in the relevance task due to a lack of examples in the prompt. While these findings do not suggest
that memorization is a major issue, they underscore the importance of high-quality prompts.
Regarding intercoder agreement, Figure 1 shows that ChatGPT’s performance is very high. On
average, intercoder agreement is about 56% for MTurk, 79% for trained annotators, 91% for
ChatGPT with temperature = 1, and 97% for ChatGPT with temperature = 0.2. The correlation
between intercoder agreement and accuracy is positive (Pearson’s r = 0.36). This suggests that a
lower temperature value may be preferable for annotation tasks, as it seems to increase consistency
without decreasing accuracy.
We underscore that the test to which we subjected ChatGPT is hard. Our tasks were originally
conducted in the context of a previous study (Alizadeh et al., 2022), and required considerable
resources. We developed most of the conceptual categories for our particular research purposes.
Moreover, some of the tasks involve a large number of classes and exhibit lower levels of inter-
coder agreement, which indicates a higher degree of annotation difficulty (Bayerl and Paul, 2011).
ChatGPT’s accuracy is positively correlated with the intercoder agreement of trained annotators
(Pearson’s r = 0.46), suggesting better performance for easier tasks. Conversely, ChatGPT’s outper-
formance of MTurk is negatively correlated with the intercoder agreement of trained annotators
(Pearson’s r = −0.37), potentially indicating stronger overperformance for more complex tasks.
We conclude that ChatGPT’s performance is impressive, particularly considering that its annotations
are zero-shot.
3
Discussion
This paper demonstrates the potential of LLMs to transform text-annotation procedures for a variety
of tasks common to many research projects. The evidence is consistent across different types of texts
and time periods. It strongly suggests that ChatGPT may already be a superior approach compared
to crowd-annotations on platforms such as MTurk. At the very least, the findings demonstrate the
importance of studying the text-annotation properties and capabilities of LLMs more in depth. The
following questions seem particularly promising: (i) performance across multiple languages; (ii)
implementation of few-shot learning; (iii) construction of semi-automated data labeling systems in
which a model learns from human annotations and then recommends labeling procedures (Desmond
et al., 2021); (iv) using chain of thought prompting and other strategies to increase the performance
of zero-shot reasoning (Kojima et al., 2022); and (v) comparison across different types of LLMs.
4
Materials and Methods
4.1
Datasets
The analysis relies on four datasets: (i) a random sample of 2,382 tweets drawn from a dataset of 2.6
million tweets on content moderation posted from January 2020 to April 2021; (ii) a random sample
of 1,856 tweets posted by members of the US Congress from 2017 to 2022, drawn from a dataset of
20 million tweets; (iii) a random sample of 1,606 articles newspaper articles on content moderation
4

<!-- 第5页 -->
ChatGPT outperforms crowd-workers for text-annotation tasks
published from January 2020 to April 2021, drawn from a dataset of 980k articles collected via
LexisNexis. Sample size was determined by the number of texts needed to build a training set for
a machine learning classifier. The fourth dataset (iv) replicated the data collection for (i), but for
January 2023. It includes a random sample of 500 tweets (of which 339 were in English) drawn
from a dataset of 1.3 million tweets.
4.2
Annotation Tasks
We implemented several annotation tasks: (1) relevance: whether a tweet is about content modera-
tion or, in a separate task, about politics; (2) topic detection: whether a tweet is about a set of six
pre-defined topics (i.e. Section 230, Trump Ban, Complaint, Platform Policies, Twitter Support,
and others); (3) stance detection: whether a tweet is in favor of, against, or neutral about repealing
Section 230 (a piece of US legislation central to content moderation); (4) general frame detection:
whether a tweet contains a set of two opposing frames (“problem’ and “solution”). The solution
frame describes tweets framing content moderation as a solution to other issues (e.g., hate speech).
The problem frame describes tweets framing content moderation as a problem on its own as well
as to other issues (e.g., free speech); (5) policy frame detection: whether a tweet contains a set
of fourteen policy frames proposed in (Card et al., 2015). The full text of instruction for the five
annotation tasks is presented in SI Appendix. We used the exact same wordings for ChatGPT and
MTurk.
4.3
Trained annotators
We trained three political science students to conduct the annotation tasks. For each task, they
were given the same set of instructions described above and detailed in SI Appendix. The coders
annotated the tweets independently task by task.
4.4
Crowd-workers
We employed MTurk workers to perform the same set of tasks as trained annotators and ChatGPT,
using the same set of instructions (SI Appendix). To ensure annotation quality, we restricted access
to the tasks to workers who are classified as “MTurk Masters” by Amazon, who have a HIT (Human
Intelligence Task) approval rate greater than 90% with at least 50 approved HITs, and who are
located in the US. Moreover, we ensured that no worker could annotate more than 20% of the tweets
for a given task. As with the trained human annotators, each tweet was annotated by two different
crowd-workers.
4.5
ChatGPT
We used the ChatGPT API with the ‘gpt-3.5-turbo’. The annotations were conducted between March
9-20 and April 27-May 4, 2023. For each task, we prompted ChatGPT with the corresponding
annotation instruction text (SI Appendix). We intentionally avoided adding any ChatGPT-specific
prompts to ensure comparability between ChatGPT and MTurk crowd-workers. After testing several
variations, we decided to feed tweets one by one to ChatGPT using the following prompt: “Here’s
the tweet I picked, please label it as [Task Specific Instruction (e.g. ‘one of the topics in the
instruction’)].” We set the temperature parameter at 1 (default value) and 0.2 (which makes the
5

<!-- 第6页 -->
ChatGPT outperforms crowd-workers for text-annotation tasks
output more deterministic; higher values make the output more random). For each temperature
setting, we collected two responses from ChatGPT to compute the intercoder agreement. That is,
we collected four ChatGPT responses for each tweet. We created a new chat session for every tweet
to ensure that the ChatGPT results are not influenced by the history of annotations.
4.6
Evaluation Metrics
First, we computed average accuracy (i.e. percentage of correct predictions), that is, the number of
correctly classified instances over the total number of cases to be classified, using trained human
annotations as our gold standard and considering only texts that both annotators agreed upon.
Second, intercoder agreement refers to the percentage of instances for which both annotators in a
given group report the same class.
4.7
Data Availability
Replication materials are available at the Harvard Dataverse, https://doi.org/10.7910/DVN/
PQYF6M.
Acknowledgments
This project received funding from the European Research Council (ERC) under the European
Union’s Horizon 2020 research and innovation program (grant agreement nr. 883121). We thank
Fabio Melliger, Paula Moser, and Sophie van IJzendoorn for excellent research assistance.
References
Alizadeh, Meysam, Fabrizio Gilardi, Emma Hoes, K Jonathan Klüser, Mael Kubli and Nahema
Marchal. 2022. “Content Moderation As a Political Issue: The Twitter Discourse Around Trump’s
Ban.” Journal of Quantitative Description: Digital Media 2.
Argyle, Lisa P., Ethan C. Busby, Nancy Fulda, Joshua R. Gubler, Christopher Rytting and David
Wingate. 2023. “Out of One, Many: Using Language Models to Simulate Human Samples.”
Political Analysis pp. 1–15.
Bayerl, Petra Saskia and Karsten Ingmar Paul. 2011. “What Determines Inter-Coder Agreement in
Manual Annotations? A Meta-Analytic Investigation.” Computational Linguistics 37(4):699–725.
Benoit, Kenneth, Drew Conway, Benjamin E. Lauderdale, Michael Laver and Slava Mikhaylov.
2016. “Crowd-Sourced Text Analysis: Reproducible and Agile Production of Political Data.”
American Political Science Review 116(2):278–295.
Binz, Marcel and Eric Schulz. 2023. “Using cognitive psychology to understand GPT-3.” Proceed-
ings of the National Academy of Sciences 120(6):e2218523120.
Card, Dallas, Amber Boydstun, Justin H Gross, Philip Resnik and Noah A Smith. 2015. The media
frames corpus: Annotations of frames across issues. In Proceedings of the 53rd Annual Meeting
of the Association for Computational Linguistics and the 7th International Joint Conference on
Natural Language Processing (Volume 2: Short Papers). pp. 438–444.
Chmielewski, Michael and Sarah C. Kucker. 2020. “An MTurk Crisis? Shifts in Data Quality and
the Impact on Study Results.” Social Psychological and Personality Science 11(4):464–473.
6

<!-- 第7页 -->
ChatGPT outperforms crowd-workers for text-annotation tasks
Desmond, Michael, Evelyn Duesterwald, Kristina Brimijoin, Michelle Brachman and Qian Pan.
2021. Semi-automated data labeling. In NeurIPS 2020 Competition and Demonstration Track.
PMLR pp. 156–169.
Emerson, Guy, Natalie Schluter, Gabriel Stanovsky, Ritesh Kumar, Alexis Palmer, Nathan Schneider,
Siddharth Singh and Shyam Ratan, eds. 2022. Proceedings of the 16th International Workshop
on Semantic Evaluation (SemEval-2022). Seattle: Association for Computational Linguistics.
Huang, Fan, Haewoon Kwak and Jisun An. 2023. “Is ChatGPT better than Human Annotators?
Potential and Limitations of ChatGPT in Explaining Implicit Hate Speech.” arXiv preprint
arXiv:2302.07736 .
Kojima, Takeshi, Shixiang Shane Gu, Machel Reid, Yutaka Matsuo and Yusuke Iwasawa. 2022.
“Large language models are zero-shot reasoners.” arXiv preprint arXiv:2205.11916 .
Kuzman, Taja, Igor Mozetiˇc and Nikola Ljubeši´c. 2023. “ChatGPT: Beginning of an End of
Manual Linguistic Data Annotation? Use Case of Automatic Genre Identification.” arXiv e-prints
pp. arXiv–2303.
Nay, John J. 2023. “Large Language Models as Corporate Lobbyists.”.
Wu, Patrick Y., Joshua A. Tucker, Jonathan Nagler and Solomon Messing. 2023. “Large Language
Models Can Be Used to Estimate the Ideologies of Politicians in a Zero-Shot Learning Setting.”.
7

<!-- 第8页 -->
ChatGPT outperforms crowd-workers for text-annotation tasks
S1
Annotation Codebooks
Not all of the annotations described in these codebooks were conducted for every dataset in our study.
First, the manual annotations we use as a benchmark were performed in a previous study, except
for the new 2023 sample, which was specifically annotated for this current study. Second, certain
annotation tasks are not applicable to all datasets. For instance, stance analysis, problem/solution,
and topic modeling were not suitable for analyzing tweets from US Congress members. This is
because these tweets cover a wide range of issues and topics, unlike content moderation topics,
which are more focused. For news articles, our attempts at human annotation for stance, topic, and
policy frames were not successful. This was because the articles primarily revolved around platform
policies, actions, and criticisms thereof.
S1.1
Background on content moderation (to be used for all tasks except the tweets from US
Congressmembers)
For this task, you will be asked to annotate a sample of tweets about content moderation. Before
describing the task, we explain what we mean by “content moderation”.
“Content moderation” refers to the practice of screening and monitoring content posted by users on
social media sites to determine if the content should be published or not, based on specific rules
and guidelines. Every time someone posts something on a platform like Facebook or Twitter, that
piece of content goes through a review process (“content moderation”) to ensure that it is not illegal,
hateful or inappropriate and that it complies with the rules of the site. When that is not the case, that
piece of content can be removed, flagged, labeled as or ‘disputed.’
Deciding what should be allowed on social media is not always easy. For example, many sites ban
child pornography and terrorist content as it is illegal. However, things are less clear when it comes
to content about the safety of vaccines or politics, for example. Even when people agree that some
content should be blocked, they do not always agree about the best way to do so, how effective
it is, and who should do it (the government or private companies, human moderators, or artificial
intelligence).
S1.2
Background on political tweets (to be used for tweets by the US Congress members)
For this task, you will be asked to annotate a sample of tweets to determine if they include political
content or not. For the purposes of this task, tweets are “relevant” if they include political content,
and “irrelevant” if they do not. Before describing the task, we explain what we mean by “political
content”.
“Political content” refers to any tweets that pertain to politics or government policies at the local,
national, or international level. This can include tweets that discuss political figures, events, or
issues, as well as tweets that use political language or hashtags. To determine if tweets include
political content or not, consider several factors, such as the use of political keywords or hashtags,
the mention of political figures or events, the inclusion of links to news articles or other political
sources, and the overall tone and sentiment of the tweet, which may indicate whether it is conveying
a political message or viewpoint.
1

<!-- 第9页 -->
ChatGPT outperforms crowd-workers for text-annotation tasks
S1.3
Task 1: Relevance (Content Moderation)
For each tweet in the sample, follow these instructions:
1. Carefully read the text of the tweet, paying close attention to details.
2. Classify the tweet as either relevant (1) or irrelevant (0)
Tweets should be coded as RELEVANT when they directly relate to content moderation, as defined
above. This includes tweets that discuss: social media platforms’ content moderation rules and
practices, governments’ regulation of online content moderation, and/or mild forms of content
moderation like flagging.
Tweets should be coded as IRRELEVANT if they do not refer to content moderation, as defined
above, or if they are themselves examples of moderated content. This would include, for example, a
Tweet by Donald Trump that Twitter has labeled as “disputed”, a tweet claiming that something is
false, or a tweet containing sensitive content. Such tweets might be subject to content moderation,
but are not discussing content moderation. Therefore, they should be coded as irrelevant for our
purposes.
S1.4
Task 2: Relevance (Political Content)
For each tweet in the sample, follow these instructions:
1. Carefully read the text of the tweet, paying close attention to details.
2. Classify the tweet as either relevant (1) or irrelevant (0)
Tweets should be coded as RELEVANT if they include POLITICAL CONTENT, as defined above.
Tweets should be coded as IRRELEVANT if they do NOT include POLITICAL CONTENT, as
defined above.
S1.5
Task 3: Problem/Solution Frames
Content moderation can be seen from two different perspectives:
• Content moderation can be seen as a PROBLEM; for example, as a restriction of free speech
• Content moderation can be seen as a SOLUTION; for example, as a protection from harmful
speech
For each tweet in the sample, follow these instructions:
1. Carefully read the text of the tweet, paying close attention to details.
2. Classify the tweet as describing content moderation as a problem, as a solution, or neither.
Tweets should be classified as describing content moderation as a PROBLEM if they emphasize
negative effects of content moderation, such as restrictions to free speech, or the biases that can
emerge from decisions regarding what users are allowed to post.
Tweets should be classified as describing content moderation as a SOLUTION if they emphasize
positive effects of content moderation, such as protecting users from various kinds of harmful
content, including hate speech, misinformation, illegal adult content, or spam.
2

<!-- 第10页 -->
ChatGPT outperforms crowd-workers for text-annotation tasks
Tweets should be classified as describing content moderation as NEUTRAL if they do not emphasize
possible negative or positive effects of content moderation, for example if they simply report on the
content moderation activity of social media platforms without linking them to potential advantages
or disadvantages for users or stakeholders.
S1.6
Task 4: Policy Frames (Content Moderation)
Content moderation, as described above, can be linked to various other topics, such as health, crime,
or equality.
For each tweet in the sample, follow these instructions:
1. Carefully read the text of the tweet, paying close attention to details.
2. Classify the tweet into one of the topics defined below.
The topics are defined as follows:
• ECONOMY: The costs, benefits, or monetary/financial implications of the issue (to an
individual, family, community, or to the economy as a whole).
• Capacity and resources: The lack of or availability of physical, geographical, spatial, human,
and financial resources, or the capacity of existing systems and resources to implement or
carry out policy goals.
• MORALITY: Any perspective—or policy objective or action (including proposed action)that
is compelled by religious doctrine or interpretation, duty, honor, righteousness or any other
sense of ethics or social responsibility.
• FAIRNESS AND EQUALITY: Equality or inequality with which laws, punishment, rewards,
and resources are applied or distributed among individuals or groups. Also the balance
between the rights or interests of one individual or group compared to another individual or
group.
• CONSTITUTIONALITY AND JURISPRUDENCE: The constraints imposed on or free-
doms granted to individuals, government, and corporations via the Constitution, Bill of
Rights and other amendments, or judicial interpretation. This deals specifically with the
authority of government to regulate, and the authority of individuals/corporations to act
independently of government.
• POLICY PRESCRIPTION AND EVALUATION: Particular policies proposed for address-
ing an identified problem, and figuring out if certain policies will work, or if existing policies
are effective.
• LAW AND ORDER, CRIME AND JUSTICE: Specific policies in practice and their enforce-
ment, incentives, and implications. Includes stories about enforcement and interpretation of
laws by individuals and law enforcement, breaking laws, loopholes, fines, sentencing and
punishment. Increases or reductions in crime.
• SECURITY AND DEFENSE: Security, threats to security, and protection of one’s person,
family, in-group, nation, etc. Generally an action or a call to action that can be taken to
protect the welfare of a person, group, nation sometimes from a not yet manifested threat.
3

<!-- 第11页 -->
ChatGPT outperforms crowd-workers for text-annotation tasks
• HEALTH AND SAFETY: Health care access and effectiveness, illness, disease, sanitation,
obesity, mental health effects, prevention of or perpetuation of gun violence, infrastructure
and building safety.
• QUALITY OF LIFE: The effects of a policy on individuals’ wealth, mobility, access to
resources, happiness, social structures, ease of day-to-day routines, quality of community
life, etc.
• CULTURAL IDENTITY: The social norms, trends, values and customs constituting cul-
ture(s), as they relate to a specific policy issue.
• PUBLIC OPINION: References to general social attitudes, polling and demographic infor-
mation, as well as implied or actual consequences of diverging from or “getting ahead of”
public opinion or polls.
• POLITICAL: Any political considerations surrounding an issue. Issue actions or efforts or
stances that are political, such as partisan filibusters, lobbyist involvement, bipartisan efforts,
deal-making and vote trading, appealing to one’s base, mentions of political maneuvering.
Explicit statements that a policy issue is good or bad for a particular political party.
• EXTERNAL REGULATION AND REPUTATION: The United States’ external relations
with another nation; the external relations of one state with another; or relations between
groups. This includes trade agreements and outcomes, comparisons of policy outcomes or
desired policy outcomes.
• OTHER: Any topic that does not fit into the above categories.
S1.7
Task 5: Policy Frames (Political Content)
Political content, as described above, can be linked to various other topics, such as health, crime, or
equality.
For each tweet in the sample, follow these instructions:
1. Carefully read the text of the tweet, paying close attention to details.
2. Classify the tweet into one of the topics defined below.
The topics are defined as follows:
• ECONOMY: The costs, benefits, or monetary/financial implications of the issue (to an
individual, family, community, or to the economy as a whole).
• Capacity and resources: The lack of or availability of physical, geographical, spatial, human,
and financial resources, or the capacity of existing systems and resources to implement or
carry out policy goals.
• MORALITY: Any perspective—or policy objective or action (including proposed action)that
is compelled by religious doctrine or interpretation, duty, honor, righteousness or any other
sense of ethics or social responsibility.
• FAIRNESS AND EQUALITY: Equality or inequality with which laws, punishment, rewards,
and resources are applied or distributed among individuals or groups. Also the balance
between the rights or interests of one individual or group compared to another individual or
group.
4

<!-- 第12页 -->
ChatGPT outperforms crowd-workers for text-annotation tasks
• CONSTITUTIONALITY AND JURISPRUDENCE: The constraints imposed on or free-
doms granted to individuals, government, and corporations via the Constitution, Bill of
Rights and other amendments, or judicial interpretation. This deals specifically with the
authority of government to regulate, and the authority of individuals/corporations to act
independently of government.
• POLICY PRESCRIPTION AND EVALUATION: Particular policies proposed for address-
ing an identified problem, and figuring out if certain policies will work, or if existing policies
are effective.
• LAW AND ORDER, CRIME AND JUSTICE: Specific policies in practice and their enforce-
ment, incentives, and implications. Includes stories about enforcement and interpretation of
laws by individuals and law enforcement, breaking laws, loopholes, fines, sentencing and
punishment. Increases or reductions in crime.
• SECURITY AND DEFENSE: Security, threats to security, and protection of one’s person,
family, in-group, nation, etc. Generally an action or a call to action that can be taken to
protect the welfare of a person, group, nation sometimes from a not yet manifested threat.
• HEALTH AND SAFETY: Health care access and effectiveness, illness, disease, sanitation,
obesity, mental health effects, prevention of or perpetuation of gun violence, infrastructure
and building safety.
• QUALITY OF LIFE: The effects of a policy on individuals’ wealth, mobility, access to
resources, happiness, social structures, ease of day-to-day routines, quality of community
life, etc.
• CULTURAL IDENTITY: The social norms, trends, values and customs constituting cul-
ture(s), as they relate to a specific policy issue.
• PUBLIC OPINION: References to general social attitudes, polling and demographic infor-
mation, as well as implied or actual consequences of diverging from or “getting ahead of”
public opinion or polls.
• POLITICAL: Any political considerations surrounding an issue. Issue actions or efforts or
stances that are political, such as partisan filibusters, lobbyist involvement, bipartisan efforts,
deal-making and vote trading, appealing to one’s base, mentions of political maneuvering.
Explicit statements that a policy issue is good or bad for a particular political party.
• EXTERNAL REGULATION AND REPUTATION: The United States’ external relations
with another nation; the external relations of one state with another; or relations between
groups. This includes trade agreements and outcomes, comparisons of policy outcomes or
desired policy outcomes.
• OTHER: Any topic that does not fit into the above categories.
S1.8
Task 6: Stance Detection
In the context of content moderation, Section 230 is a law in the United States that protects websites
and other online platforms from being held legally responsible for the content posted by their users.
This means that if someone posts something illegal or harmful on a website, the website itself
cannot be sued for allowing it to be posted. However, websites can still choose to moderate content
and remove anything that violates their own policies.
5

<!-- 第13页 -->
ChatGPT outperforms crowd-workers for text-annotation tasks
For each tweet in the sample, follow these instructions:
1. Carefully read the text of the tweet, paying close attention to details.
2. Classify the tweet as having a positive stance towards Section 230, a negative stance, or a
neutral stance.
S1.9
Task 7: Topic Detection
Tweets about content moderation may also discuss other related topics, such as:
1. Section 230, which is a law in the United States that protects websites and other online plat-
forms from being held legally responsible for the content posted by their users (SECTION
230).
2. The decision by many social media platforms, such as Twitter and Facebook, to suspend
Donald Trump’s account (TRUMP BAN).
3. Requests directed to Twitter’s support account or help center (TWITTER SUPPORT).
4. Social media platforms’ policies and practices, such as community guidelines or terms of
service (PLATFORM POLICIES).
5. Complaints about platform’s policy and practices in deplatforming and content moderation
or suggestions to suspend particular accounts, or complaints about accounts being suspended
or reported (COMPLAINTS).
6. If a text is not about the SECTION 230, COMPLAINTS, TRUMP BAN, TWITTER
SUPPORT, and PLATFORM POLICIES, then it should be classified in OTHER class
(OTHER).
For each tweet in the sample, follow these instructions:
1. Carefully read the text of the tweet, paying close attention to details.
2. Please classify the following text according to topic (defined by function of the text, author’s
purpose and form of the text). You can choose from the following classes: SECTION
230, TRUMP BAN, COMPLAINTS, TWITTER SUPPORT, PLATFORM POLICIES, and
OTHER
6
