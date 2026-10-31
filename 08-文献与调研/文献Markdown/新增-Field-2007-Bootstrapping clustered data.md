# Field-2007-Bootstrapping clustered data

> 原件：参考文献原件-按论文编号-20261023/待核新增-20261031/Field-2007-Bootstrapping clustered data.pdf

<!-- 第1页 -->
© 2007 Royal Statistical Society
1369–7412/07/69369
J. R. Statist. Soc. B (2007)
69, Part 3, pp. 369–390
Bootstrapping clustered data
C. A. Field
Dalhousie University, Halifax, Canada
and A. H. Welsh
Australian National University, Canberra, Australia
[Received November 2005. Revised December 2006]
Summary. Various bootstraps have been proposed for bootstrapping clustered data from
one-way arrays. The simulation results in the literature suggest that some of these methods
work quite well in practice; the theoretical results are limited and more mixed in their conclu-
sions. For example, McCullagh reached negative conclusions about the use of non-parametric
bootstraps for one-way arrays. The purpose of this paper is to extend our understanding of the
issues by discussing the effect of different ways of modelling clustered data, the criteria for
successful bootstraps used in the literature and extending the theory from functions of the sam-
ple mean to include functions of the between and within sums of squares and non-parametric
bootstraps to include model-based bootstraps. We determine that the consistency of variance
estimates for a bootstrap method depends on the choice of model with the residual bootstrap
giving consistency under the transformation model whereas the cluster bootstrap gives consis-
tent estimates under both the transformation and the random-effect model. In addition we note
that the criteria based on the distribution of the bootstrap observations are not really useful in
assessing consistency.
Keywords: Between and within sums of squares; Bootstrap; Clusters; Hierarchical data;
One-way arrays
1.
Introduction
Our aim in this paper is to address some issues which arise when bootstrapping clustered, hierar-
chical or multilevel data. These issues arise from the dependence structure in the data, different
ways of describing or modelling the data, different ways of bootstrapping and different ways of
evaluating the bootstrap.
The problem of bootstrapping clustered data was ﬁrst discussed in the design-based ﬁnite
population survey literature by Gross (1980), McCarthy and Snowden (1985), Rao and Wu
(1988), Sitter (1992) and others; see Canty and Davison (1999) for a recent application and
Shao (2003) for a recent review. In this work, the observations are ﬁxed and inferences are made
with respect to the random-sampling mechanism, so the main issue is accommodating complex
survey designs arising from various forms of cluster sampling into inference about ﬁnite popu-
lation parameters. The inﬁnite population version of the problem is of quite a different nature
and has led to different bootstrap methods; see for example Davison and Hinkley (1997), pages
100–102, McCullagh (2000), Andersson and Karlsson (2001), Ukoumunne et al. (2003) and
Carpenter et al. (2003). Here, the clusters are treated as arising from the data-generating mech-
anism rather than the sampling scheme and the focus is on making inferences about parameters
Address for correspondence: A. H. Welsh, Centre for Mathematics and Its Applications, Australian National
University, Canberra, ACT 0200, Australia.
E-mail: Alan.Welsh@anu.edu.au

<!-- 第2页 -->
370
C. A. Field and A. H. Welsh
while accommodating the dependence structure in the data. The inﬁnite population approach is
useful in and has been applied to model-based ﬁnite population analysis; see Butar and Lahiri
(2003), Lahiri (2003) and Welsh (2005).
We shall work in the inﬁnite population context so that inference is with respect to the pop-
ulation model rather than the sampling mechanism. This means that it is helpful to specify a
model for how we think the data were generated. We specify two possible models for the data
(called the random-effect model and the transformation model). These models are compatible
in the sense that their ﬁrst and second moments agree but, in general, their higher moments
do not. This means that the variances of statistics like the sums of squares which depend on
fourth or higher moments of the underlying distribution can be different under the two models.
In addition, bootstrap methods can have different properties under the two models. This paper
explores the consequences of this important fact.
There is already a rich class of bootstrap methods for clustered data in the literature but there
is an absence of detailed theoretical results on the properties of these methods. We therefore
concentrate on gaining insight into bootstrapping clustered data by deriving theoretical results
for methods which are already in the literature.
Davison and Hinkley (1997), pages 100–102, discussed the randomized cluster bootstrap
(‘Strategy 1’) in which clusters are selected by simple random sampling with replacement and
then observations within clusters are randomly permuted, the two-stage bootstrap (‘Strategy 2’)
inwhich,afterselectingclustersasintherandomizedclusterbootstrap,observationswithinclus-
ters are selected by simple random sampling with replacement, and the random-effect bootstrap
in which we compute predictors of the random effects in the model, draw bootstrap samples of
these predictors by simple random sampling with replacement from each of the sets of predictors
and then construct bootstrap observations by combining the bootstrap predictors appropriately.
The cluster bootstrap is a simpliﬁed version of the randomized cluster bootstrap in which clusters
are selected by simple random sampling with replacement and there is no subsequent permu-
tation. McCullagh (2000) considered the randomized cluster and the two-stage bootstraps as
well as the reverse two-stage bootstrap in which observations within clusters are ﬁrst selected
by simple random sampling with replacement and then clusters are selected by simple random
sampling with replacement. (The reverse two-stage bootstrap has two levels of variability like
the two-stage bootstrap but differs from it in that clusters which are selected more than once
must contain the same observations each time.) He also considered other non-parametric boot-
straps which involved sampling without replacement or permutation. Andersson and Karlsson
(2001) considered, among others, the random-effects bootstrap and the residual bootstrap in
which we compute appropriate residuals, draw a bootstrap sample of these residuals by simple
random sampling with replacement from the residuals and then reconstruct bootstrap obser-
vations from the bootstrap residuals. Subsequent work has used these bootstraps (Ukoumunne
et al. (2003) used the cluster bootstrap and Carpenter et al. (2003) the random-effect bootstrap)
or parametric versions of them (Butar and Lahiri, 2003; Lahiri, 2003). All these bootstraps can
be viewed as constructing empirical estimates of the distribution function of the data which can
then be used in place of the distribution that actually generated the data to make inferences.
We consider the simplest inﬁnite population problem in which the clustered data can be
arranged in a balanced single classiﬁcation and establish base-line theoretical results for this
case. In spite of the simplicity of this set-up, most of the important issues are already present.
We also focus on the variance parameters rather than the mean parameters. Functions of the
variance components are often of more interest than functions of the mean parameters. Conse-
quently we expand the class of statistics to include those which are functions of the between and
within sums of squares, including various variance component estimates, estimates of ratios of

<!-- 第3页 -->
Bootstrapping
371
variance components and estimates of the intracluster correlation (which were considered by
Ukoumunne et al. (2003)) or heritability. The properties of all such estimators can be derived
from those of the between and within sums of squares, so we derive and present these properties,
including those of the sample total for completeness.
The existing literature uses a range of criteria to evaluate bootstrap methods for clustered data;
for general discussion see Shao and Tu (1995). Davison and Hinkley (1997), focusing on infer-
ence for the mean, argued that the bootstrap observations should mimic the ﬁrst two moment
structure of the original observations as closely as possible. Speciﬁcally, they compared the
expected ﬁrst two bootstrap moments of the bootstrap observations with the ﬁrst two moments
of the observations. They concluded that the randomized cluster bootstrap and the random-
effect bootstrap (with appropriately chosen predictors of the random effects) most closely mimic
the ﬁrst two moment structure of the observations. McCullagh (2000) argued that the bootstrap
distribution should be exchangeable under a suitable group structure. He went on to show that
not all bootstraps which meet this criterion produce consistent estimates of the variance of the
sample mean or total. This means that, even under his restrictive deﬁnition of a bootstrap (he
excluded the random-effect and residual bootstraps and his deﬁnition does not apply to unbal-
anced problems), his criterion does not exclude bootstraps which fail. Andersson and Karlsson
(2001) used a simulation study to investigate the size and power of bootstrap tests of a hypothe-
sis on a slope parameter and obtained good results for their bootstraps. Similarly, Ukoumunne
et al. (2003) and Carpenter et al. (2003) obtained good results in simulation studies to evaluate
the properties of bootstrap conﬁdence intervals for the intracluster correlation coefﬁcient and
for regression parameters and components of variance respectively. The work of Ukoumunne
et al. (2003) shows the importance of using an appropriate transformation when constructing
conﬁdence intervals for functions of the variance components. There is therefore already a good
body of simulation results which we supplement in this paper with detailed theoretical insight.
We adopt the viewpoint that consistent estimation of the variance of a range of statistics is a
minimal requirement for a bootstrap to be useful. We can consider consistency under various
asymptotic situations: cluster asymptotics in which the number of clusters increases, observation
asymptotics in which the number of observations in each of the ﬁxed set of clusters increases and
joint asymptotics in which the number of clusters and the number of observations in each cluster
increase. Not all the variance parameters in the model can be estimated consistently under obser-
vation asymptotics, so we do not consider this approach further; cluster asymptotics require
less of the sequence than joint asymptotics and provide a more stringent criterion in the sense
that consistency under cluster asymptotics will give consistency under joint asymptotics.
The statistics that we consider are invariant to permutation of the clusters and/or of observa-
tions within clusters. This means that the results for the randomized cluster bootstrap and the
cluster bootstrap (which is the same as the randomized cluster bootstrap without the permuta-
tion step) are identical. However, the observations themselves are not invariant to permutation
of the observations within clusters and so have different ﬁrst two moment structures (which have
different expectations) under the randomized cluster bootstrap and the cluster bootstrap. This
observation undermines the value of the moment matching criterion of Davison and Hinkley
(1997). Indeed, we argue that it is unclear how to implement this criterion and that matching the
moments of the observations is not sufﬁciently sophisticated to distinguish between bootstrap
methods. This is not altogether surprising as we consider statistics (like the sums of squares)
which are non-linear functions of the observations and have different properties under different
models.
We show that the random-effect bootstrap gives asymptotically consistent results for the
random-effect model under joint asymptotics and the residual bootstrap gives asymptotically

<!-- 第4页 -->
372
C. A. Field and A. H. Welsh
consistent results for the transformation model under cluster asymptotics. These methods have
the advantage that they generalize naturally to more complex random or mixed models but the
disadvantage that they are tied to particular models. We also show that the randomized cluster
bootstrap and the cluster bootstrap are asymptotically consistent for both models under cluster
asymptotics and are the best of the exchangeable bootstraps.
In the next section, we introduce our notation and obtain the results that we require to assess
the various bootstrap methods. These results give the second-order moment structure of the
sums of squares for non-normal data and compare them under the two different models that we
consider. In Section 3, we obtain the ﬁrst two bootstrap moments of bootstrap versions of the
sums of squares under various bootstraps and compare these with the results that are obtained
in Section 2. We present simulation results in Section 4 and our conclusions in Section 5.
2.
Notation and basic moment results
Consider a balanced single classiﬁcation with g clusters (groups or blocks) of m observations
each. Let Yij denote the jth observation in the ith cluster, let yT
i = .Yi1,. . . ,Yim/ denote the
m-vector of observations from the ith cluster and let yT =.yT
1 ,. . . ,yT
g / denote the vector of all
mg observations. Then let
¯Yi· =m−1 m

j=1
Yij
denote the mean of the ith cluster and
¯Y·· =.mg/−1 g
i=1
m

j=1
Yij =g−1 g
i=1
¯Yi·
denote the grand mean. Next, deﬁne the sample total
T =mg ¯Y·· =m
g
i=1
¯Yi·
and the between- and within-cluster statistics
SBk =m
g
i=1
. ¯Yi· −¯Y··/k
and
SWk =
g
i=1
SWki,
where
SWki =
m

j=1
.Yij −¯Yi·/k,
k =2,3,4:
These statistics with k = 2 are the between-cluster sum of squares SB2 and the within-cluster
sum of squares SW2.
We shall focus mainly on the between and within sums of squares because many other statis-
tics of interest (including the maximum likelihood estimators under the normal model and the
method-of-moments estimators) can be expressed as smooth functions of the sample total and
these sums of squares. At least asymptotically, the properties of such statistics are easily derived
from those of the total and the two sums of squares. These properties depend on the model and
hence on the way that the data were generated. We consider two simple models and explore the
properties of the estimators under both models.

<!-- 第5页 -->
Bootstrapping
373
The simplest model for a balanced single classiﬁcation is the random-effect model
Yij =μ+βi +"ij,
j =1,. . . ,m,
i=1,. . . ,g,
.1/
where βi are independent and identically distributed random variables with mean 0 and variance
σ2
β, independent of the independent and identically distributed random variables "ij which have
mean 0 and variance σ2
". We assume that E.β4/<∞and E."4/<∞. The observations Yij and
Ykl are independent whenever i̸=k and satisfy E.Yij/=μ and
cov.Yij, Yil/=

σ2
β +σ2
"
if j =l,
σ2
β
otherwise,
.2/
which is known as the homogeneous or exchangeable correlation structure.
The homogeneous correlation structure can also be obtained under the transformation model.
Put
V =σ2
"Im +σ2
βJm,
where Im is the m × m identity matrix and Jm = 1m1T
m is the m × m matrix of 1s (1m is the
m-vector of 1s), and let C denote the mg ×mg block diagonal matrix with g blocks of V along
the diagonal so C =blockdiag.V, . . . ,V/. Let z be an mg-vector of independent and identically
distributed random variables with mean 0, variance 1 and fourth moment ζ4. Then let
y =1mgμ+C1=2z
.3/
so that
E.y/=1mgμ,
var.y/=C,
.4/
corresponding to the mean and covariance structure (2). We use the symmetric matrix square
root throughout.
Although models (1) and (3) produce the same correlation structure, they do not necessarily
produce the same higher moment structure. For example, under both models, the within-block
means ¯Yi· (which determine the properties of the between sum of squares) are independent
random variables with mean μ and variance .σ2
" +mσ2
β/=m. However,
E{. ¯Yi· −μ/4}=

m−3{m3E.β4/+6m2σ2
βσ2
" +E."4/+3.m−1/σ4
"}
random-effect model,
m−3.σ2
" +mσ2
β/2.ζ4 −3+3m/
transformation model.
These fourth-order moments are the same under normality but are difﬁcult to compare in general
without specifying all the quantities that are involved in the expressions. In the particular case
that β=σβ and "=σ" have the same distribution as z, we only have to specify .m,γ =σβ=σ",ζ4/.
For the Student t-distribution with 5 degrees of freedom, ζ4 =9 and we obtain
E{. ¯Yi· −μ/4}=

3m−3σ4
".3m3γ4 +2m2γ2 +m+2/
random-effect model,
3m−3σ4
".1+mγ2/2.m+2/
transformation model.
Fig. 1 partitions the .m, γ/-space for the Student t-distribution with 5 degrees of freedom
into the region in which the within-group mean has greater fourth moment under the trans-
formation model and the region in which it has greater fourth moment under the random-effect
model. We see that, for this distribution, unless γ and m are small, the within-group mean
has greater fourth moment under the random-effect than the transformation model. Although
it is convenient for making comparisons, we should keep in mind that there is no reason in

<!-- 第6页 -->
374
C. A. Field and A. H. Welsh
Random-effect model
Transformation model
2
3
4
5
6
7
8
m
0.2183 0.2582 0.3163
0.4083
0.5774
1
2
γ
Fig. 1.
Partition of the (m, γ) space for the Student t-distribution with 5 degrees of freedom into the region
in which the within-group mean has greater fourth moment under the transformation model and the
region in which it has greater fourth moment under the random-effect model: the γ-axis is on the log2-
scale
practice to constrain β=σβ, "=σ" and z to have the same distribution, never mind this particular
distribution.
Our evaluation of various bootstrap resampling methods will be based on the ﬁrst two
moments of T, SB2 and SW2. These moments are readily available under normality where
(for both models) E.T/=mgμ, var.T/=mg.mσ2
β +σ2
"/, E.SB2/=.g −1/.mσ2
β +σ2
"/, var.SB2/=
2.g −1/.mσ2
β +σ2
"/2, ESW2 =g.m−1/σ2
", var.SW2/=2g.m−1/σ4
" and cov.SB2,SW2/=0. How-
ever, we require the moments for non-normal distributions. In this case, we obtain different
results for the two models.
Theorem 1. Suppose that the random-effect model (1) holds. Then the total T has mean mgμ
and variance mg.mσ2
β +σ2
"/. The sums of squares SB2 and SW2 have means .g −1/.mσ2
β +σ2
"/
and g.m−1/σ2
" respectively and
var.SB2/=g −1
g
{m2.g−1/E.β4/+4mgσ2
βσ2
" + g −1
m E."4/+2mg −3g +3
m
σ4
" −m2.g −3/σ4
β},
var.SW2/= .m−1/g
m
{.m−1/E."4/−.m−3/σ4
"},
and

<!-- 第7页 -->
Bootstrapping
375
cov.SB2, SW2/= .m−1/.g −1/
m
{E."4/−3σ4
"}:
.5/
The kinds of calculations that are used in the proof can be found in Tukey (1956) or Scheffé
(1959), pages 343–346.
It is generally too stringent to require the bootstrap to reproduce the ﬁrst two moments of a
statistic in ﬁnite samples so we often impose the weaker requirement that this be achieved asymp-
totically. Corollary 1 is given for later reference. As discussed in Section 1, various asymptotic
schemes are possible and we consider the two cases when g →∞(with m ﬁxed) and g,m→∞.
We use the notation an ∼bn to mean that an=bn →1 as n →∞and in this case say that an is
asymptotic to bn.
Corollary 1. Suppose that the random-effect model (1) holds. Then, as g →∞with m ﬁxed,
the mean of the total T is asymptotic to mgμ and the variance is asymptotic to mg.mσ2
β +σ2
"/.
The means of the sums of squares SB2 and SW2 are asymptotic to g.mσ2
β +σ2
"/ and .m−1/gσ2
"
respectively and
var.SB2/∼m2 g E.β4/+4mgσ2
βσ2
" + g
mE."4/+ .2m−3/g
m
σ4
" −m2gσ4
β,
var.SW2/∼.m−1/g
m
{.m−1/E."4/−.m−3/σ4
"}
and
cov.SB2, SW2/∼.m−1/g
m
{E."4/−3σ4
"}:
As m,g →∞, the mean of the total T is asymptotic to mgμ and the variance to m2gσ2
β. The
means of the sums of squares SB2 and SW2 are asymptotic to mgσ2
β and mgσ2
" respectively and
var.SB2/∼m2g{E.β4/−σ4
β},
var.SW2/∼mg{E."4/−σ4
"}
and
cov.SB2, SW2/∼g{E."4/−3σ4
"}:
Under the transformation model, the moments of the sums of squares are given in theorem 2.
Theorem 2. Suppose that the transformation model (3) holds. Then the sample total T has
the same mean and variance as under the random-effect model, the sums of squares have the
same means as under the random-effect model but
var.SB2/= g −1
mg .σ2
" +mσ2
β/2{.g −1/ζ4 +2mg −3g +3},
var.SW2/= .m−1/g
m
σ4
"{.m−1/ζ4 −.m−3/}
and
cov.SB2, SW2/= .m−1/.g −1/
m
.σ2
" +mσ2
β/σ2
".ζ4 −3/:
Proof. Write the sums of squares as quadratic forms and then use the fact that
E.zTFzzTGz/=ζ4

i
FiiGii + 
i̸=j
.FiiGjj +FijGij +FijGji/:
□

<!-- 第8页 -->
376
C. A. Field and A. H. Welsh
The variances and covariance of the sums of squares are different under the two models. In
the special case that β=σβ and "=σ" have the same distribution as z, the expressions are simpler
to compare and we note the following properties.
(a) The expressions for the variance of the between sum of squares both follow from the fact
that
var.SB2/= m2.g −1/2
g
E{. ¯Yi· −μ/4}−m2.g −1/.g −3/
g
E{. ¯Yi· −μ/2}2:
Since E. ¯Yi· −μ/2 is the same under the two models, we can compare the variances of the
between sum of squares by comparing E{. ¯Yi· −μ/4} under both models as was done for
the Student t-distribution with 5 degrees of freedom in Fig. 1.
(b) The variance of the within sum of squares is the same for both models.
(c) The covariance of the sums of squares is greater in absolute value for the transformation
model than for the random-effect model.
As we noted before, there is no reason to constrain β=σβ and "=σ" to have the same distribution.
Some more general comparisons of the variances that were obtained in theorems 1 and 2 (not
Table 1.
Comparison of the target values .g1/.mσ2
β Cσ2"/ and g.m1/σ2" estimated by the between and
within sums of squares respectively and the exact variances of the total, between and within sums of squares
and the exact covariance of the between and within sums of squares under the random-effect model (theorem
1) and under the transformation model (theorem 2)†
g =5
Target values
Between
20.00
22.67
30.67
33.33
Within
15.00
25.00
15.00
25.00
Random effect
β–"
N–N
N–t(5)
t(5)–N
t(5)–t(5)
Total
100.00
113.33
153.33
166.67
Between
200.00
270.22
1323.56
1422.22
Within
30.00
270.83
30.00
270.83
Covariance of sums of squares
0.00
50.00
0.00
50.00
Transformation
z, .σ 2
β, σ2"/
N (1,1)
t*(5) (1,5/3)
t*(5) (5/3,1)
t*(5) (5/3,5/3)
Total
100.00
113.33
153.33
166.67
Between
200.00
411.02
752.36
888.89
Within
30.00
270.83
97.50
270.83
Covariance of sums of squares
0.00
170.00
138.00
250.00
g =15
Target values
Between
70.00
79.33
107.33
116.67
Within
45.00
75.00
45.00
75.00
Random effect
β−"
N–N
N–t(5)
t(5)–N
t(5)–t(5)
Total
300.00
340.00
460.00
500.00
Between
700.00
953.56
5130.22
5483.33
Within
90.00
812.50
90.00
812.50
Covariance of sums of squares
0.00
175.00
0.00
175.00
Transformation
z, .σ 2
β, σ2"/
N (1,1)
t*(5) (1,5/3)
t*(5) (5/3,1)
t*(5) (5/3,5/3)
Total
300.00
340.00
460.00
500.00
Between
700.00
1528.49
2797.82
3305.56
Within
90.00
812.50
292.50
812.50
Covariance of sums of squares
0.00
595.00
483.00
875.00
†The results are presented for m = 4 and g = 5 or g = 15. The symbol N denotes the standard normal distribu-
tion, t(5) the Student t-distribution with 5 degrees of freedom and tÅ.5/ = √.3=5/t.5/ the standardized Student
t-distribution with 5 degrees of freedom. For the random-effect model, the distributions are given as that of the
random effect β followed by that of "; for the transformation model, the distribution is that of z followed by the
values of .σ2
β, σ2"/. The settings have been chosen so that the target values are the same under both models.

<!-- 第9页 -->
Bootstrapping
377
necessarily assuming that the distributions are the same) are given in Table 1. We can choose a
wide variety of settings for the random-effect and transformation models. For consistency we
have arranged for the between and within sums of squares to estimate the same target value
under the two models (although the targets change with g and the particular distributions). As
we would expect, the variance of the sample total is the same under the two models because it
depends only on the second-moment structures, which agree under the two models. Although
the variances and covariance of the sums of squares are the same for the two models under nor-
mality, in general, the variance of the between and within sum of squares can be substantially
different under the two models. The covariance is the same as or larger in the transformation
model than in the random-effect model. Note that the ﬁrst (the N−N or N (1,1)) and the last
(the t(5)–t(5) or t*(5) (5/3, 5/3)) columns in Table 1 are covered by Fig. 1 (and the numbers are
consistent with the conclusions that were drawn above) but the other two columns are not. It
is interesting that the size of the differences in the variances under the two models can be so
large.
3.
Bootstrap methods
We now consider the issue of bootstrapping to obtain estimates of the variance and covariance
of the between sum of squares SB2 and the within sum of squares SW2 along with results for the
sample total T. There are various seemingly attractive approaches that can be used to obtain
bootstrap estimates and we explore several of them.
For each bootstrap, we give the exact bootstrap means and variances of the total, between
and within sums of squares. Since these bootstrap calculations are made conditionally on the
observed data, they depend on the type of bootstrap but not on the underlying model. We
then describe the asymptotic behaviour of these bootstrap moments which depends on the
convergence of sample statistics to population quantities of the underlying model. Hence the
convergence results do depend on the underlying model.
3.1.
Random-effect bootstrap
The random-effect bootstrap method is based on the random-effect model: we construct pre-
dictors ˆβi and ˆ"ij of βi and "ij respectively which satisfy ¯ˆβ = 0 and ¯ˆ" = 0, draw a sample of
size g independently with replacement from { ˆβi :i=1,. . . ,g} to produce the bootstrap sample
{ ˆβÅ
i :i=1, . . . ,g} and then independently draw a sample of size mg independently with replace-
ment from {ˆ"ij : j = 1, . . . ,m, i = 1, . . . ,g} to produce the bootstrap sample {ˆ"Å
ij : j = 1,. . . ,m,
i = 1, . . . ,g}. The bootstrap observations are constructed as suggested by the random-effect
model (1) as
YÅ
ij = ¯Y·· + ˆβÅ
i + ˆ"Å
ij,
j =1,. . . ,m,
i=1,. . . ,g:
The ˆ"Å
ij are independent and identically distributed random variables with bootstrap mean
¯ˆ"=0, variance
u"2 =.mg/−1 g
i=1
m

j=1
ˆ"2
ij
and fourth central moment
u"4 =.mg/−1 g
i=1
m

j=1
ˆ"4
ij:

<!-- 第10页 -->
378
C. A. Field and A. H. Welsh
They are independent of the ˆβÅ
i which are independent and identically distributed random vari-
ables with bootstrap mean ¯ˆβ =0, variance
uβ2 =g−1 g
i=1
ˆβ2
i
and fourth moment
uβ4 =g−1 g
i=1
ˆβ4
i :
It follows that the observations YÅ
ij and YÅ
kl are (conditionally) independent when i̸ = k, have
EÅ.YÅ
ij/= ¯Y·· and
covÅ.YÅ
ij, YÅ
il /=
uβ2 +u"2
if j =l,
uβ2
otherwise.
Comparing this result with expression (2), we see that the bootstrap observations have the same
ﬁrst- and second-moment structure as the original data. Also,
EÅ{. ¯YÅ
i· −¯Y··/4}=uβ4 +6uβ2u"2=m+{u"4 +3.m−1/u2
"2}=m3,
which has the same form as the fourth moment of the within-group mean under the random-
effect model. The expected bootstrap moments depend on the choice of the predictors ˆβi and ˆ"ij.
The properties of the random-effect bootstrap statistics follow from theorem 1.
Theorem 3. The random-effects bootstrap mean and variance of TÅ are T and m2guβ2 +mgu"2
respectively. The random-effect bootstrap means of SÅ
B2 and SÅ
W2 are .g −1/.muβ2 +u"2/ and
.m−1/gu"2 respectively. The random-effect bootstrap variances and covariances are
varÅ.SÅ
B2/=g −1
g

m2.g −1/uβ4 +4mguβ2u"2+g −1
m u"4+2mg −3g +3
m
u2
"2 −m2.g −3/u2
β2

,
varÅ.SÅ
W2/= g.m−1/2
m
u"4 −g.m−1/.m−3/
m
u2
"2
and
covÅ.SÅ
B2, SÅ
W2/= .m−1/.g −1/
m
.u"4 −3u2
"2/:
It follows that the random-effect bootstrap variance of the total and the random-effect boot-
strap estimates of the sums of squares are consistent under the random-effect model provided
that uβ2 ∼σ2
β and u"2 ∼σ2
". Since the expressions for the variances and covariance of the sums
of squares in theorem 3 are of the same form as those in theorem 1, it follows that, under the
random-effect model, the bootstrap variances of the sums of squares are consistent provided, in
addition, that uβ4 ∼E.β4/ and u"4 ∼E."4/: They are not consistent under the transformation
model.
The usual predictor of "ij is ˜"ij = Yij −¯Yi· and the estimated best linear unbiased predictor
of βi (when the variance components are known) is
˜βi = SB2=.g −1/−SW2=g.m−1/
SB2=g
. ¯Yi· −¯Y··/,
provided that SB2=.g −1/>SW2=g.m−1/ (Searle et al. (1992), page 55). Note that, asymptoti-
cally, we can estimate the denominator just as well by SB2=.g −1/, which matches the numerator

<!-- 第11页 -->
Bootstrapping
379
better. However, as we shall see below, the choice of g rather than g −1 leads to smaller bias. The
sum of squares g−1Σg
i=1 ˜β2
i converges to .mσ2
β +σ2
"/−1mσ4
β, which is too small. We can obtain
the result required if we set
ˆβi =
SB2=.g −1/−SW2=g.m−1/
SB2=g

. ¯Yi· −¯Y··/
so that
uβ2 = 1
g
g
i=1
ˆβ2
i =
1
m.g −1/SB2 −
1
m.m−1/g SW2
is the usual unbiased (and consistent) estimator of σ2
β. The predictor ˆβi is still shrunk towards
0 but not as much as ˜βi. Similarly, we deﬁne the expanded predictor
ˆ"ij =

m
m−1

.Yij −¯Yi·/
so that
u"2 = 1
mg
g
i=1
m

j=1
ˆ"2
ij =
1
g.m−1/SW2
is unbiased for σ2
". These are the same as the adjustments that were recommended by Davison
and Hinkley (1997), page 102. With this choice of predictors,
covÅ.YÅ
ij, YÅ
il /=
⎧
⎪
⎪
⎨
⎪
⎪
⎩
1
m.g −1/SB2 + 1
mg SW2
if j =l,
1
m.g −1/SB2 −
1
m.m−1/g SW2
otherwise.
This looks more like the covariance structure (2) if, for j̸ =l, we write covÅ.YÅ
ij,YÅ
il /=varÅ.YÅ
ij/−
{.m−1/g}−1SW2 and the expected bootstrap moments equal expression (2) exactly.
For the fourth moments,
uβ4 =
SB2=.g −1/−SW2=g.m−1/
SB2=g
2 1
g
g
i=1
. ¯Yi· −¯Y··/4
=
SB2=.g −1/−SW2=g.m−1/
SB2=g
2 1
mg SB4
and
u"4 =
m
.m−1/2g
g
i=1
m

j=1
.Yij −¯Yi·/4
=
m
.m−1/2g SW4:
The asymptotic version of theorem 3 follows from the fact that as g →∞with m ﬁxed
1
mg SB4 ∼E{.βi + ¯"i·/4}= 1
m3 {m3 E.β4/+6m2σ2
βσ2
" +E."4/+3.m−1/σ4
"}
and

<!-- 第12页 -->
380
C. A. Field and A. H. Welsh
1
mg SW4 ∼1
m3 {.m3 −4m2 +6m−3/E."4/+3.m−1/.2m−1/σ4
"}:
Corollary 2. Suppose that the random-effect model holds. As g →∞with m ﬁxed, the random-
effect bootstrap mean and variance of TÅ are mgμ and mg.mσ2
β +σ2
"/ respectively. The random-
effect bootstrap means of SÅ
B2 and SÅ
W2 are g.mσ2
β + σ2
"/ and g.m −1/σ2
" respectively. The
random-effect bootstrap variances and covariances are
varÅ.SÅ
B2/∼m4g
σ4
β
.mσ2
β +σ2"/2 E{.βi + ¯"i·/4}+4mgσ2
βσ2
"+
g
m2.m−1/2 {.m3−4m2+6m−3/E."4/
+3.m−1/.2m−3/σ4
"}+ .2m−3/g
m
σ4
" −m2gσ4
β,
varÅ.SÅ
W2/∼g
m2 {.m3 −4m2 +6m−3/E."4/+3.m−1/.2m−3/σ4
"}−.m−3/.m−1/g
m
σ4
"
and
covÅ.SÅ
B2,SÅ
W2/∼
g
m2.m−1/{.m3 −4m2 +6m−3/E."4/+3.m−1/.2m−3/σ4
" −3m.m−1/2σ4
"}:
As m,g →∞, the random-effect bootstrap variances of TÅ, SÅ
B2 and SÅ
W2 and the covariances
between the sums of squares are asymptotically correct.
As we have seen, the bootstrap observations have the same ﬁrst-, second- and fourth-moment
structure as the original data under the random-effect model. The bootstrap estimates the ﬁrst
and second moments of the total and the ﬁrst moments of the between and within sums of
squares as g →∞with m ﬁxed. However, the bootstrap estimates the variance and covariance
of the between and within sums of squares when m,g →∞but not when g →∞with m ﬁxed.
3.2.
Residual bootstrap
The residual bootstrap is motivated by the transformation model: the idea is to compute resid-
uals which can be bootstrapped and then used to reconstruct bootstrap observations.
Let ˆV and ˆC denote the matrices V and C respectively, with the unknown variances σ2
" and
σ2
β replaced by estimators. Then deﬁne the residuals
r = ˆC−1=2.y −1mg ¯Y··/
and the centred and standardized residuals
rc ={r −.mg/−11mg1T
mgr}=sr,
where s2
r =.mg/−1{rTr −.mg/−1.1T
mgr/2}. We obtain a bootstrap sample by drawing a sample
rÅ
c of size mg independently with replacement from rc and setting
yÅ =1nb ¯Y·· + ˆC1=2rÅ
c :
The residuals have bootstrap mean 0, variance Img and
EÅ{.rÅ
c ⊗rÅ
c /.rÅ
c ⊗rÅ
c /T}=EÅ.rÅ
cirÅ
cjrÅ
ckrÅ
cl/,
where
EÅ.rÅ
cirÅ
cjrÅ
ckrÅ
cl/=
⎧
⎪
⎨
⎪
⎩
.mg/−1
mg

i=1
r4
ci
if i=j =k =l,
1
if i=j̸ =k =l,i=k̸ =j =l, or i=l̸=j =k,
0
otherwise.

<!-- 第13页 -->
Bootstrapping
381
It follows that EÅ.yÅ/ = 1mg ¯Y·· and varÅ.yÅ/ = ˆC, which is an empirical version of expression
(4) so the bootstrap sample yÅ has the same ﬁrst- and second-moment structure as the original
data y. The expected bootstrap moments are E{EÅ.yÅ/} = 1nbμ and E{varÅ.yÅ/} = E. ˆC/ so
the ﬁrst two moments match exactly if E. ˆC/=C. For the within-group mean, we have
EÅ{. ¯YÅ
i· −¯YÅ
··/4}=m−3.ˆσ2
" +mˆσ2
β/2. ˆζ4 −3+3m/,
where ˆσβ and ˆσ" are the estimates of σβ and σ" that are used in ˆC, and
ˆζ4 =.mg/−1 mg

i=1
r4
ci:
We show in the proof of corollary 3 below that this moment is consistent under the transforma-
tion model; it is not consistent under the random-effect model.
Theorem 4. The residual bootstrap mean and variance of TÅ are T and mg.ˆσ2
" +mˆσ2
β/ respec-
tively. The residual bootstrap means of SÅ
B2 and SÅ
W2 are .g −1/.ˆσ2
" + mˆσ2
β/ and g.m −1/ˆσ2
"
respectively. The residual bootstrap variances and covariances are
var.SB2/= g −1
mg .ˆσ2
" +mˆσ2
β/2{.g −1/ ˆζ4 +2mg −3g +3},
var.SW2/= .m−1/g
m
ˆσ4
"{.m−1/ ˆζ4 +m−3}
and
cov.SB2, SW2/= .m−1/.g −1/
m
.ˆσ2
" +mˆσ2
β/ˆσ2
". ˆζ4 −3/:
The proof is very similar to that for theorem 2 and is omitted.
Theorem 4 shows that the residual bootstrap variances and covariance are of the same form
as the variances and covariance that are given in theorem 2 with ˆC in place of C and rc in place
of z. As a result, the consistency of the bootstrap variance estimates under the transformation
model becomes a question of the consistency of the estimates, ˆC and the second and fourth
moments of the rcs. We have the following result.
Corollary 3. Suppose that the transformation model holds. Provided that ˆV ∼V as g →∞
with m ﬁxed, the residual bootstrap means and variances of TÅ, SÅ
B2 and SÅ
W2 and the bootstrap
covariance between SÅ
B2 and SÅ
W2 are asymptotically correct as g →∞with m ﬁxed.
Proof. Since ˆV ∼V, the result follows if we can show that s2
r =1+op.1/ and
.mg/−1 mg

i=1
r4
ci =ζ4 +op.1/:
We have
¯r = 1
mg 1T
mg ˆC−1=2.y −1mg ¯Y··/
= 1
mg 1T
m ˆV −1=2 g
i=1
.yi −1m ¯Y··/
=Op.g−1=2/

<!-- 第14页 -->
382
C. A. Field and A. H. Welsh
so
s2
r = 1
mg rTr −¯r2
= 1
mg .y −1mg ¯Y··/T ˆC−1.y −1mg ¯Y··/+Op.g−1/
= 1
mg
g
i=1
.yi −1m ¯Y··/T ˆV −1.yi −1m ¯Y··/+Op.g−1/
=tr

ˆV −1 1
mg
g
i=1
.yi −1m ¯Y··/.yi −1m ¯Y··/T

+Op.g−1/
= 1
mtr.Im/+op.1/+Op.g−1/:
Next,
.mg/−1 mg

i=1
r4
ci =.mg/−1 mg

i=1
.ri −¯r/4=s4
r
=

.mg/−1 mg

i=1
r4
i −4.mg/−1 mg

i=1
r3
i ¯r +6.mg/−1 mg

i=1
r2
i ¯r2 −3¯r4

s4
r
so we just need to establish that
.mg/−1 mg

i=1
r4
i =ζ4 +op.1/:
Let δj be the n-vector with jth component equal to 1 and all other components 0. Note that, in
the following expression, we can assume that μ=0. Then we have
.mg/−1 mg

i=1
r4
i =.mg/−1 g
i=1
m

j=1
{δT
j ˆV −1=2.yi −¯Y··/}4
=.mg/−1 g
i=1
m

j=1
.δT
j ˆV −1=2yi/4 −4.mg/−1 g
i=1
m

j=1
.δT
j ˆV −1=2yi/3δT
j ˆV −1=2 ¯Y··
+6.mg/−1 g
i=1
m

j=1
.δT
j ˆV −1=2yi/2.δT
j ˆV −1=2 ¯Y··/2 −3m−1 m

j=1
.δT
j ˆV −1=2 ¯Y··/4:
.6/
Write zT =.zT
1 , . . . ,zT
g /. Then, noting that vec.zizT
i /=zi ⊗zi, we have
.mg/−1 g
i=1
m

j=1
.δT
j ˆV −1=2yi/4 =.mg/−1 g
i=1
m

j=1
.δT
j ˆV −1=2V 1=2zi/4
=.mg/−1 g
i=1
m

j=1
{.V 1=2 ˆV −1=2δj ⊗V 1=2 ˆV −1=2δj/T.zi ⊗zi/}2
=.mg/−1 g
i=1
m

j=1
{.V 1=2 ˆV −1=2δj ⊗V 1=2 ˆV −1=2δj/T.zi ⊗zi/}
×{.zi ⊗zi/T.V 1=2 ˆV −1=2δj ⊗V 1=2 ˆV −1=2δj/}
=.mg/−1 g
i=1
m

j=1
tr{.V 1=2 ˆV −1=2δj ⊗V 1=2 ˆV −1=2δj/.V 1=2 ˆV −1=2δj
⊗V 1=2 ˆV −1=2δj/T.zi ⊗zi/.zi ⊗zi/T}

<!-- 第15页 -->
Bootstrapping
383
=m−1 m

j=1
tr{.V 1=2 ˆV −1=2δj ⊗V 1=2 ˆV −1=2δj/.V 1=2 ˆV −1=2δj ⊗V 1=2 ˆV −1=2δj/T
×g−1 g
i=1
.zi ⊗zi/.zi ⊗zi/T}
=m−1 m

j=1
tr[.δj ⊗δj/.δj ⊗δj/T E{.zi ⊗zi/.zi ⊗zi/T}]+op.1/
=m−1 m

j=1
E[{.δj ⊗δj/.zi ⊗zi/}2]+op.1/
=m−1 m

j=1
E{.δT
j zi/4}+op.1/
=ζ4 +op.1/:
The result follows from the fact that ¯Y·· =Op.g−1=2/ so the remaining terms in equation (6) are all
of smaller order than the leading fourth-power term.
□
The Davison and Hinkley (1997) criterion requiring that the bootstrap observations have the
same low order moment structure as the original data cannot distinguish between the residual
and random-effect bootstraps.
3.3.
Cluster bootstrap
The simple cluster bootstrap is based on drawing samples of g clusters independently with
replacement. The bootstrap sample is the set of mg observations YÅ
ij where the g m-vectors
.YÅ
i1, . . . ,YÅ
im/ corresponding to clusters are independently and identically distributed with the
distribution placing probability 1=g on each of the g m-vectors .Yi1,. . . ,Yim/. This means that
the observations YÅ
ij and YÅ
kl are bootstrap independent whenever i̸=k with
EÅ.YÅ
ij/=g−1 g
i=1
Yij = ¯Y:j
and
covÅ.YÅ
ij, YÅ
il /=
⎧
⎪
⎪
⎨
⎪
⎪
⎩
1
g
g
i=1
.Yij −¯Y·j/2
if j =l,
1
g
g
i=1
.Yij −¯Y·j/.Yil −¯Y·l/
otherwise.
This is not the same ﬁrst two moment structure as the original data shown in expression (2),
although E{EÅ.YÅ
ij/} = μ, E{varÅ.YÅ
ij/} = g−1.g −1/.σ2
β + σ2
"/ and E{covÅ.YÅ
ij,YÅ
il /} = g−1 ×
.g −1/σ2
β, so this structure is recovered as g →∞. Alternatively, as in the random-effect
bootstrap, we can rescale the observations by √{g=.g −1/} to make the result exact. For the
within-group mean, we ﬁnd that
EÅ{. ¯YÅ
i· −¯Y··/4}= 1
mg SB4 ∼E{. ¯Yi· −μ/4}
which is correct under either model. This is the main advantage of using a non-parametric boot-

<!-- 第16页 -->
384
C. A. Field and A. H. Welsh
strap which is not based on a particular model—it is possible to be consistent under different
models.
The above moment calculations treat the cluster vectors as exchangeable observations but
do not take into account the fact that the components of these vectors are also exchangeable.
Following Davison and Hinkley (1997) and McCullagh (2000), we can do this by permuting
the observations within the clusters. This produces the randomized cluster bootstrap. The per-
mutation step has no effect on our statistics, which are all invariant to permutation, but does
change the calculations for the moments of individual observations as these are not invariant
to permutation. In particular,
EÅ.YÅ
ij/=.mg/−1 g
i=1
m

j=1
Yij = ¯Y··
and
covÅ.YÅ
ij, YÅ
il /=
⎧
⎪
⎪
⎨
⎪
⎪
⎩
1
mg .SB2 +SW2/
if j =l,
1
mg {SB2 −.m−1/−1SW2}
otherwise.
As with the random-effect bootstrap, this looks more like the covariance structure (2) if, for
j̸ =l, we write
covÅ.YÅ
ij, YÅ
il /=varÅ.YÅ
ij/−{.m−1/g}−1SW2
but note that here the expected variance
E{varÅ.YÅ
ij/}=.mg/−1{m.g −1/σ2
β +.mg −1/σ2
"}
and the expected covariance
E{covÅ.YÅ
ij, YÅ
il /}=.mg/−1{m.g −1/σ2
β −σ2
"}
which are both too small and only correct when g →∞.
The ﬁrst two cluster bootstrap (and randomized cluster bootstrap) moments of the total,
between and within sums of squares are given in theorem 5.
Theorem 5. The cluster bootstrap mean and variance of TÅ are T and mg2SB2 respectively. The
cluster bootstrap means of SÅ
B2 and SÅ
W2 are .g −1/g−1SB2 and SW2 respectively. The cluster
bootstrap variances and covariances are
varÅ.SÅ
B2/= m.g −1/2
g2
SB4 −.g −1/.g −3/
g3
S2
B2,
varÅ.SÅ
W2/=
g
i=1
S2
W2i −1
g S2
W2
and
covÅ.SÅ
B2, SÅ
W2/= m.g −1/
g
g
i=1
SW2i. ¯Yi· −¯Y··/2 −g −1
g2 SW2SB2
respectively.

<!-- 第17页 -->
Bootstrapping
385
Proof. From general results on simple random sampling with replacement (e.g. Särndal et al.
(1992), page 52), the cluster bootstrap sample total TÅ is unbiased for the ‘population’ total T
and has variance nSB2. The results for the cluster bootstrap between sum of squares SÅ
B2 follow
from the fact that SÅ
B2 is the scaled sample variance of the independent random variables ¯YÅ
i·.
For the cluster bootstrap within sum of squares, we obtain
E.SÅ
W2/=
g
i=1
SW2i =SW2
and
varÅ.SÅ
W2/= g −1
g
g
i=1
S2
W2i −1
g
g
i̸=h
SW2iSW2h
= g −1
g
g
i=1
S2
W2i −1
g
 g
i=1
SW2i
2
+ 1
g
g
i=1
S2
W2i
=
g
i=1
S2
W2i −1
g S2
W2:
The proof of the expression for the covariance is given in Appendix A.
□
As we noted, the cluster bootstrap has the advantage of being non-parametric and not depend-
ing on any model. This makes it possible for the bootstrap estimates of the means, variances
and covariances to be consistent under both models.
Corollary 4. Under both the random-effect and the transformation model, the cluster boot-
strap variances of TÅ, SÅ
B2 and SÅ
W2 and the covariance between the sums of squares are asymp-
totically correct as g →∞with m ﬁxed.
Corollary 4 shows that the cluster bootstrap applied to groups is a sensible estimator of the
sampling variances of both the mean and the variance components in large samples. The cluster
bootstrap variance of the mean is exactly the variance of the mean if we scale the block means by
√{g=.g −1/}. This is not surprising because, under both models, the group vectors are simply
independent and identically distributed random vectors.
3.4.
Other bootstraps
We have not yet considered the two-stage bootstrap and the reverse two-stage bootstrap that
were described in Section 1. The results for the cluster bootstrap suggest that excess variation is
generated in these bootstraps. McCullagh’s (2000) results show that the two-stage and reverse
two-stage bootstraps do not produce consistent estimators for the variance of TÅ unless both m
and g tend to ∞. Thus, the two-stage and reverse two-stage bootstraps are inferior to the other
bootstraps. Under the two-stage bootstrap
covÅ.YÅ
ij, YÅ
il /=
⎧
⎪
⎪
⎨
⎪
⎪
⎩
1
mg .SB2 +SW2/
if j =l,
1
mg SB2
otherwise.
This mimics the structure (2) very closely and, as with the random-effect bootstrap, for j̸ = l,
we can write covÅ.YÅ
ij, YÅ
il /=varÅ.YÅ
ij/−.mg/−1SW2. However, for the two-stage bootstrap, the
expected variance

<!-- 第18页 -->
386
C. A. Field and A. H. Welsh
E{varÅ.YÅ
ij/}=.mg/−1{m.g −1/σ2
β +.mg −1/σ2
"}
and the expected covariance
covÅ.YÅ
ij, YÅ
il /=g−1.g −1/.σ2
β +m−1σ2
"/
which are not correct unless both m and g tend to ∞. Thus we reach opposite conclusions
from the bootstrap moments and the expected bootstrap moments. Extensive calculations show
that the two-stage bootstrap variance of the within sum of squares and the two-stage bootstrap
covariance of the between and within sums of squares are not consistent even when m,g →∞.
Thus the fact that the observations have the correct low moment structure does not imply that
the bootstrap will be consistent for a general statistic.
McCullagh (2000) also considered some further bootstraps which involve sampling with-
out replacement or permutation. As we saw in discussing the cluster and randomized cluster
bootstraps, permutation does not affect the between and within sums of squares because they
are invariant to permutation. It does, however, affect the bootstrap moments and expected
bootstrap moments of observations, undermining the value of criteria that are based on these
moments.
Finally, it is worth noting that, if we specify the distribution of the random effect and residu-
als in model (1), we can construct parametric bootstraps. These bootstraps do produce consis-
tent estimators of the variances and covariances that we require but only under the additional
requirement that the distributions assumed are correct. This makes them of less interest in
practice unless the distributional assumptions can be veriﬁed, and we do not consider them
further.
4.
Simulation
We carried out simulations for the random-effect, residual and cluster bootstrap for data that
were generated by both the random-effect model and the transformation model. Although we
have already shown in Table 1 that the theoretical target values for the variances and covariances
of the sums of squares vary substantially both according to the model and to the generating dis-
tribution(s), it is useful to provide numerical results for small sample sizes. As we shall show, the
numerical results demonstrate that the appropriate bootstrap gives reasonable results which are
a substantial improvement over what would be obtained from normal theory when the normal
is replaced by a t-distribution.
In each situation from Table 1, we generated 1000 data sets. For each data set, we computed
the bootstrap variance for the total, SB2 and SW2 using 100 bootstrap replications. Table 2 gives
the means and their standard deviation of these 1000 bootstrap variances for several of the
cases. Results for the intermediate cases that are not shown typically lay between those given in
Table 2. It is important to be cautious in interpreting the numerical results as the distributions
of the bootstrap variance are very long tailed to the right, especially for the t(5) distribution.
For instance under the random-effect model with t(5)–t(5) the distribution of the random-effect
bootstrap variance has third quartile 1020 and maximum value 346600 with similar patterns
for the other bootstraps under both models. The extreme skewness in the distributions suggests
that, if we are going to construct conﬁdence intervals, we should do so on the log-scale.
The random-effect bootstrap gives good results for the total and SB2 under the random-effect
model. For the transformation model, it underestimates the SB2-variance for the t-distribution.
Across all models, the SW2 variance is underestimated for the t-distribution. The residual boot-
strap is reliable for the total and for SB2 for the transformation model and the t-distribution. Its

<!-- 第19页 -->
Bootstrapping
387
Table 2.
Results from simulations based on 1000 data sets with 100 bootstrap replicates per data set†
g =5
Random effect
N–N
Target
Random-effect bootstrap
Residual bootstrap
Cluster bootstrap
Total
100
102 (2)
102 (2)
81 (2)
Between
200
202 (8)
298 (14)
112 (5)
Within
30
29 (1)
30 (1)
24 (1)
Transformation
N (1,1)
Target
Random-effect bootstrap
Residual bootstrap
Cluster bootstrap
Total
100
98 (2)
100 (2)
79 (2)
Between
200
204 (10)
293 (17)
113 (6)
Within
30
30 (1)
31 (1)
25 (1)
Random effect
t(5)–t(5)
Target
Random-effect bootstrap
Residual bootstrap
Cluster bootstrap
Total
167
177 (7)
183 (7)
141 (5)
Between
1422
1284 (428)
1550 (359)
739 (236)
Within
271
128 (7)
140 (10)
134 (10)
Transformation
t*(5) (5/3,5/3)
Target
Random-effect bootstrap
Residual bootstrap
Cluster bootstrap
Total
167
163 (4)
170 (4)
130 (3)
Between
889
620 (44)
1057 (91)
336 (23)
Within
271
133 (13)
167 (16)
139 (17)
g =15
Random effect
t(5)–t(5)
Target
Random-effect bootstrap
Residual bootstrap
Cluster bootstrap
Total
500
504 (11)
521 (11)
468 (9)
Between
5483
4755 (1076)
3315 (280)
4148 (853)
Within
813
442 (36)
463 (42)
552 (55)
Transformation
t*(5) (5/3,5/3)
Target
Random-effect bootstrap
Residual bootstrap
Cluster bootstrap
Total
500
502 (7)
524 (8)
467 (7)
Between
3306
2643 (153)
3576 (231)
2326 (156)
Within
813
476 (45)
607 (64)
592 (68)
†Entries give the target values from Table 1 and the mean of the 1000 bootstrap estimates of the variance along
with their standard deviation in parentheses. The distribution labels are as in Table 1.
performance for SB2 under normality is conservative but we note that we may be seeing difﬁcul-
ties due to the long tail. The medians of the bootstrap variance for SB2 are 149 and 124 for the
two models. Again the bootstrap variance for SW2 is underestimated for the t-distribution but
there is a slight improvement over the random-effect bootstrap. The cluster bootstrap consis-
tently underestimates the bootstrap variance for all the statistics. However, we should note that
for the cluster bootstrap we are essentially working with ﬁve and 15 observations respectively.
In addition, one can argue that the cluster results should be scaled by g=.g −1/. However, the
effect of this rescaling does not overcome the underestimation.
We observe that, for non-normal data, using any of the bootstraps gives a substantially better
variance estimate than would be obtained under a normal approximation. For instance with
SB2 and the random-effect model with t(5)–t(5), the normal theory gives a variance estimate of
about 200 with a target of 1422 for g =5. The three bootstraps give variance estimates of 1284,
1550 and 739, all moving well in the direction of the target.
5.
Conclusions
We have considered two different models for describing clustered data and shown that, in the
non-normal case, the between and within sum of squares have different properties under the two
models. We also demonstrated varying behaviour for the bootstrap variances and covariances of
the between and within sum of squares under different bootstrap schemes and the two models.
Criteria based on the distribution of observations such as the moment criterion of Davison and
Hinkley (1997) and the exchangeability criterion of McCullagh (2000) are not really useful for
anticipating the properties of general statistics. Instead, we have focused directly on consistent

<!-- 第20页 -->
388
C. A. Field and A. H. Welsh
variance estimation for a class of statistics. In this framework, the random-effect bootstrap gives
consistent variance estimates under the random-effect model as the number of clusters and the
size of each cluster increases. The residual bootstrap which is reminiscent of the usual boot-
strap in regression models gives consistent variance estimates under the transformation model
as the number of clusters increases. The cluster bootstrap provides a very simple resampling
scheme which yields consistent variance estimates as the number of clusters increases for both
the random-effect and the transformation model. However, the cluster bootstrap is not as easily
generalized to more complicated random and mixed models as the random-effect and residual
bootstraps.
Acknowledgements
This research has been supported by the Engineering and Physical Sciences Research Council
(GR/S21977/01), Australian Research Council (DP0559135) and Natural Science and Engineer-
ing Research Council of Canada. We are grateful to the Joint Editor, Associate Editor and two
referees for comments which improved this paper.
Apppendix A
A.1.
Derivation of equation (5) for the covariance, cov(SB2, SW2)
We have
E.SB2SW2/=E

m
g
i=1
.β2
i +2βi¯"i· + ¯"2
i·/−mg.¯β2 +2¯β¯"·· + ¯"2
··/
 g
i=1
m

j=1
"2
ij −m
g
i=1
¯"2
i·

=m E
 g
i=1
.β2
i +2βi¯"i· + ¯"2
i·/
g
i=1
m

j=1
"2
ij

−mg E

.¯β2 +2¯β¯"·· + ¯"2
··/
g
i=1
m

j=1
"2
ij

−m2 E
 g
i=1
.β2
i +2βi¯"i· + ¯"2
i·/
g
i=1
¯"2
i·

+m2g E

.¯β2 +2¯β¯"·· + ¯"2
··/
g
i=1
¯"2
i·

=.mg/2σ2
βσ2
" +m E
 g
i=1
¯"2
i·
g
i=1
m

j=1
"2
ij

−m2gσ2
βσ2
" −mg E

¯"2
··
g
i=1
m

j=1
"2
ij

−mg2σ2
βσ2
"
−m2 E
 g
i=1
¯"2
i·
2
+mgσ2
βσ2
" +m2g E

¯"2
··
g
i=1
¯"2
i·

=mg.m−1/.g −1/σ2
βσ2
"+ 1
mE
 g
i=1
 m

j=1
"ij
2
g
i=1
m

j=1
"2
ij

−1
mg E
 g
i=1
m

j=1
"ij
2 g
i=1
m

j=1
"2
ij

−m2 g −1
g
E
 g
i=1
¯"2
i·
2
=mg.m−1/.g −1/σ2
βσ2
"+ 1
m E
 g
i=1
 m

j=1
"ij
2
g
i=1
m

j=1
"2
ij

−1
mg E
 g
i=1
 m

j=1
"2
ij + 
j̸=k
"ij"ik
 g
i=1
m

j=1
"2
ij

−m2 g −1
g
E
 g
i=1
¯"4
i· +
i̸=h
¯"2
i·¯"2
h·

=mg.m−1/.g −1/σ2
βσ2
" + g −1
mg E
 g
i=1
 m

j=1
"ij
2
g
i=1
m

j=1
"2
ij

−m2 g −1
g
	
g 1
m4 {m E."4/
+3m.m−1/σ4
"}+ g.g −1/
m2
σ4
"

=mg.m−1/.g −1/σ2
βσ2
" + g −1
mg E
 g
i=1
m

j=1
"2
ij +
g
i=1

j̸=k
"ij"ik
 g
i=1
m

j=1
"2
ij

−g −1
m E."4/
−.g −1/
3.m−1/
m
+g −1

σ4
"

<!-- 第21页 -->
Bootstrapping
389
=mg.m−1/.g −1/σ2
βσ2
" + g −1
mg E
 g
i=1
m

j=1
"2
ij
2
−g −1
m E."4/−g −1
m .2m−3+mg/σ4
"
=mg.m−1/.g −1/σ2
βσ2
" + g −1
mg E
 g
i=1
m

j=1
"4
ij +
g
i=1
m

j̸=k
"2
ij"2
ik +
i̸=h
m

j=1
"2
ij"2
hj +
i̸=h
m

j̸=k
"2
ij"2
hk

−g −1
m E."4/−g −1
m .2m−3+mg/σ4
"
=mg.m−1/.g −1/σ2
βσ2
" +.g −1/E."4/+.g −1/{.m−1/+.g −1/+.m−1/.g −1/}σ4
"
−g −1
m E."4/−g −1
m .2m−3+mg/σ4
"
=mg.m−1/.g −1/σ2
βσ2
" + .m−1/.g −1/
m
E."4/+.g −1/

.m−1/+.g −1/+.m−1/.g −1/
−1
m.2m−3+mg/

σ4
"
=mg.m−1/.g −1/σ2
βσ2
" + .m−1/.g −1/
m
E."4/+ g −1
m .m−1/.mg −3/σ4
"
so
cov.SB2, SW2/=E.SB2SW2/−E.SB2/ E.SW2/
=mg.m−1/.g −1/σ2
βσ2
" + .m−1/.g −1/
m
E."4/+ g −1
m .m−1/.mg −3/σ4
"
−.m−1/g.g −1/.mσ2
βσ2
" +σ4
"/
= .m−1/.g −1/
m
{E."4/−3σ4
"},
giving the result.
A.2.
Derivation of the expression for the covariance covÅ(SÅ
B2, SÅ
W2) in theorem 5
Note ﬁrst that
0=
g
i=1
SW2i
 g
i=1
. ¯Y i· −¯Y ··/
2
=
g
i=1
SW2i. ¯Y i· −¯Y ··/2 +
i̸=h
SW2i. ¯Y h· −¯Y ··/2 +2 
i̸=h
SW2i. ¯Y i· −¯Y ··/. ¯Y h· −¯Y ··/+ 
i̸=h̸=k
SW2i. ¯Y h· −¯Y ··/. ¯Y k· −¯Y ··/
= 1
mSW2SB2 −2
g
i=1
SW2i. ¯Y i· −¯Y ··/2 + 
i̸=h̸=k
SW2i. ¯Y h· −¯Y ··/. ¯Y k· −¯Y ··/
so

i̸=h̸=k
SW2i. ¯Y h· −¯Y ··/. ¯Y k· −¯Y ··/=2
g
i=1
SW2i. ¯Y i· −¯Y ··/2 −1
mSW2SB2:
Let Δi equal the number of times that cluster i appears in the sample, so .Δ1, . . . , Δg/∼multinomial.g,
1=g, . . . , 1=g/. Then,
EÅ.SÅ
W2SÅ
B2/=mEÅ g
i=1
ΔiSW2i
g
i=1
Δi. ¯Y i· −¯Y ··/2
−m
g EÅ g
i=1
ΔiSW2i
 g
i=1
Δi. ¯Y i· −¯Y ··/
2
=mEÅ g
i=1
Δ2
i SW2i. ¯Y i· −¯Y ··/2
+mEÅ 
i̸=h
ΔiΔhSW2i. ¯Y h· −¯Y ··/2
−m
g EÅ g
i=1
ΔiSW2i
 g
i=1
Δ2
i . ¯Y i· −¯Y ··/2 +
i̸=h
ΔiΔh. ¯Y i· −¯Y ··/. ¯Y h· −¯Y ··/


<!-- 第22页 -->
390
C. A. Field and A. H. Welsh
=m2g −1
g
g
i=1
SW2i. ¯Y i· −¯Y ··/2 +mg −1
g

i̸=h
SW2i. ¯Y h· −¯Y ··/2 −m
g EÅ g
i=1
Δ3
i SW2i. ¯Y i· −¯Y ··/2
−m
g EÅ 
i̸=h
ΔiΔ2
hSW2i. ¯Y h· −¯Y ··/2
−2m
g EÅ
i̸=h
Δ2
i ΔhSW2i. ¯Y i·−¯Y ··/. ¯Y h· −¯Y ··/

−m
g EÅ 
i̸=h̸=k
ΔiΔhΔgSW2i. ¯Y h·−¯Y ··/. ¯Y k·−¯Y ··/

=m2g −1
g
g
i=1
SW2i. ¯Y i· −¯Y ··/2+mg −1
g

i̸=h
SW2i. ¯Y h· −¯Y ··/2−m
g3 .5g2−6g+2/
g
i=1
SW2i. ¯Y i· −¯Y ··/2
−m
g3 .2g2 −4g +2/ 
i̸=h
SW2i. ¯Y h· −¯Y ··/2 −2 m
g3 .2g2 −4g +2/ 
i̸=h
SW2i. ¯Y i· −¯Y ··/. ¯Y h· −¯Y ··/
−m
g3 .g2 −3g +2/ 
i̸=h̸=k
SW2i. ¯Y h· −¯Y ··/. ¯Y k· −¯Y ··/
=m
2g −1
g
−g −1
g
 g
i=1
SW2i. ¯Y i· −¯Y ··/2 + g −1
g
SW2SB2 −m
g3 .5g2 −6g +2−2g2 +4g −2/
×
g
i=1
SW2i. ¯Y i· −¯Y ··/2 −1
g3 .2g2 −4g +2/SW2SB2 +2 m
g3 .2g2 −4g +2/
g
i=1
SW2i. ¯Y i· −¯Y ··/2
−m
g3 .g2 −3g +2/

2
g
i=1
SW2i. ¯Y i· −¯Y ··/2 −1
mSW2SB2

= m.g −1/
g
g
i=1
SW2i. ¯Y i· −¯Y ··/2 + .g −1/2
g2
SW2SB2
and the result follows.
References
Andersson, M. K. and Karlsson, S. (2001) Bootstrapping error component models. Computnl Statist., 16, 221–
231.
Butar, F. B. and Lahiri, P. (2003) On measures of uncertainty of empirical Bayes small area estimators. J. Statist.
Planng Inf., 112, 63–76.
Canty, A. J. and Davison, A. C. (1999) Resampling-based variance estimation for labour force surveys. Statistician,
48, 379–391.
Carpenter, J. R., Goldstein, H. and Rasbash, J. (2003) A novel bootstrap procedure for assessing the relationship
between class size and achievement. Appl. Statist., 52, 431–443.
Davison, A. C and Hinkley, D. V. (1997) Bootstrap Methods and Their Application. Cambridge: Cambridge
University Press.
Gross, S. (1980) Median estimation in sample surveys. Proc. Surv. Res. Meth. Sect. Am. Statist. Ass., 181–184.
Lahiri, P. (2003) On the impact of bootstrap in survey sampling and small-area estimation. Statist. Sci., 18,
199–210.
McCarthy, P. J. and Snowden, C. B. (1985) The bootstrap and ﬁnite population sampling. Vital and Health
Statistics, 2-95. Washington, DC: US Government Printing Ofﬁce.
McCullagh, P. (2000) Re-sampling and exchangeable arrays. Bernoulli, 6, 285–301.
Rao, J. N. K. and Wu, C.-F. J. (1988) Resampling inference with complex survey data. J. Am. Statist. Ass., 83,
231–241.
Särndal, C.-E., Swensson, B. and Wretman, J. (1992) Model Assisted Survey Sampling. New York: Springer.
Scheffé, H. (1959) The Analysis of Variance. New York: Wiley.
Searle, S., Casella, G. and McCulloch, C. E. (1992) Variance Components. New York: Wiley.
Shao, J. (2003) Impact of the bootstrap on sample surveys. Statist. Sci., 18, 191–198.
Shao, J. and Tu, D. (1995) The Jackknife and Bootstrap. New York: Springer.
Sitter, R. (1992) A resampling procedure for complex survey data. J. Am. Statist. Ass., 87, 755–765.
Tukey, J. W. (1956) Variances of variance components: I, Balanced designs. Ann. Math. Statist., 27, 722–736.
Ukoumunne, O. C., Davison, A. C., Gulliford, M. C. and Chinn, S. (2003) Non-parametric bootstrap conﬁdence
intervals for the intraclass correlation coefﬁcient. Statist. Med., 22, 3805–3821.
Welsh, A. H. (2005) Bootstrapping in clustered populations. 55th Sessn International Statistical Institute, Sydney.
