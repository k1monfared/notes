# Some March Mathness

I went to several talks and meetings in the past few days, and I am going to talk about some of them, but first let me start with some predicting game:
## A fun problem
> Take 10 coins and put them in a pile. Divide the pile into two piles of arbitrary sizes and multiply the number of coins in the two piles and record that number. Repeat this with each pile and each time record the number, until you can't divide the piles any more. Now add up all the numbers you've recorded. What is the number you got?
Now my job is to guess what that number is. Well let me see, you divided the first pile and then one more time, and then another time, and... emm... I see, at the end you added 9 numbers. OK, so far, so good, then you added this one with that, and... mmm... OK... let's see... and that adds up to... 45?

The problem is very simple if you look at it correctly. The catch is that it doesn't matter how you divide the piles, you'll always get the same number at the end. I think this is one of the first problems that got me interested in math. I read the problem as one of the monthly problems in a math magazine aimed at middle school students. The magazine was called Borhan, and was being published by Madreseh Publications in Iran. The editor of the Magazine, Parviz Shahriari, proposed a bunch of problems in each issue, and he would give hints or solutions in the next issue. If you want to find the actual problem take a look at the first issue. There it is 25 coins and the solution uses some basic algebra. Years later I remembered the problem again but I couldn't remember the solutions. So, I ought to solve it myself. Here is what I came up with:

WARNING: SPOILER!

Draw 10 dots on a paper and divide it into two sets of points, say 7 and 3. Now draw all the lines that connects the dots in the first set to the second set. How many lines you've got? Yes, $7 \times 3$. Now keep doing this with each of the two sets of 3 and 7 dots. At the time that you can't divide any more, you have drawn all possible lines between every pair of points. Adding up all the results of multiplications is just counting the number of lines. As you can see, it didn't matter how you divided them. The question now is how many lines are there. Let's number the dots: 1,2,3, ..., 10. There are 9 lines that pass through 1. Put them away. Now there are 8 lines that pass through 2, put them away. Repeat this until the dot number 9, there is exactly one line. So, the total number of lines is 1+2+3+ ... + 9 = 45. OK. It's easy to do it for 10, but what if I started with 100 points? What is 1+2+3+...+99? Well, it is a famous problem due to Gauss. People say when he was in the school and his lazy teacher wanted to keep them busy after teaching them how to add, so that he could take a nap, he gives them the problem of adding all the numbers from 1 to 100. The Gauss comes up with this idea:

1 + 2 + ... + 99 + 100 = S

100 + 99 + ... + 2 + 1 = S

---------------------

101 + 101 + ... + 101 + 101 = 2S

S0, there are 100 numbers that are added together and all of them are 101. The sum is 10100. But that's twice the sum we are looking for. So let's divide it by 2. The sum is 5050. The fact that Gauss knew how to multiply and divide right after learning how to add is not verified by anyone yet! So, now you tell me, what do you if you did it with 25 coins?

## Project-based calculus
One of the talks was about teaching calculus with projects, by [Peter ](http://www.mtroyal.ca/ProgramsCourses/FacultiesSchoolsCentres/ScienceTechnology/Departments/MathematicsComputing/Faculty/MPE_BIO_PZIZLER.HTM)[ Zizler](http://www.mtroyal.ca/ProgramsCourses/FacultiesSchoolsCentres/ScienceTechnology/Departments/MathematicsComputing/Faculty/MPE_BIO_PZIZLER.HTM) from Mount Royal University. There are a lot of people talking about this and there are good resources available for launching a calculus course that is entirely/mostly based on projects. To list a few

	- the book "[Calculus: An Active Approach with Projects](http://www.maa.org/press/ebooks/calculus-an-active-approach-with-projects)" by Stephen Hilbert, Diane D. Schwartz, Stan Seltzer, John Maceli, and Eric Robinson, and published by MAA, provides a good collection of projects.
	- [Gavin's Calculus Projects](http://www.math.lsa.umich.edu/~glarose/courseinfo/calc/calcprojects.html) are useful.
	- The Cornell's website for [Project-based calculus](http://www.math.cornell.edu/~projcalc/) also has a nice collection and samples of implementing it in a class.

The purpose is that students will be interested in learning if they can connect to it, and it's not all abstract knowledge for them. Hence projects are good motivations. The talk wasn't really about a project-based course. It was mostly on advertising the use of "best 3 out of 5" test results, and that to make it not too generous, one can limit the students to choose at least one from the last two tests. After I asked about the change in the results of the first two tests, he said students' grade did drop in the first two tests compared to previous method (all 5), and there's not much that we can do about it. His suggestion was to use the fear strategy that "if you don't do well in the first couple of tests the rest are usually harder...". Peter also introduced the book "Calculus with Applications" by Margaret Lial et al. which has many applications. You can find a series of this books [here](http://www.pearsonhighered.com/lgrseries/). And now that we are talking about this take a look at [this article](http://www.fandm.edu/annalisa-crannell/writing-projects-in-math-classes) by Annalisa Crannell of Franklin and Marshall College, about incorporating essay assignments in math classes that can be challenging, and seems wild to many.
## Linear Markov Chain Markov Fields
Another talk was on Markov Chain Markov Fields by University of Calgary's own [Deniz Sezer](https://people.ucalgary.ca/~adsezer/). The talk was a review on the paper "Markov Chain Markov Field dynamics: Models and statistics" by Xavier Guyon and Cécile Hardouin, 2002 (DOI: 10.1080/02331880213192). The idea is that when dealing with Markov processes people tend to ignore the structure, because a lot of times it's just so complicated that you really don't know much about them. On the other hand, if you know something about the structure of what interacts with what, then you can tell a lot more about the behaviour of the system. In this talk, the focus was on the cases that only pairs interact with each other, and hence you can look at a graph. A neighbourhood of a set is defined and some properties such as ergodicity and strong law of large numbers are explored. A couple of interesting things mentioned were the notion of conditional independence of two sets $A$ and $B$ given a set $C$. This notion is related to edges of a graph to be present or not, and disconnectedness of the graph, though it wasn't really mentioned in the talk. Another interesting concept is a set of variables $Y_A$ is called Markovian, if $A$ and $A^c$ are conditionally independent given $\partial A$ (neighbourhood of $A$). Then a theorem says

> **Theorem. **A set of variables is Markovian if and only if all *active *sets in it are simplicies.
I wondered about the cases when more than just pairs can interact with each other, and hence we need something more to talk about the structure of the system, like a simplex. Apparently some few studies are done in that direction and Deniz thinks some might be found in the book "Guyon, X. (1995). Randon Fields on a Network: Modelling, Statistics and Applications (Springer)".
## Low-rank matrix completions in geophysics
[Mauricio D. Sacchi](http://www.ualberta.ca/~msacchi/), Professor of geophysics at University of Alberta gave this interesting talk on New and not-so-new applications of low-rank matrix and tensor completions to seismic data processing. He started by mentioning the [Julia Seismic software](https://github.com/SeismicJulia/Seismic.jl). He explained thath the Imaging is about "where" and inversion is about "what". Then he suggested to look at the 5-dimensional data regularization. The 5 dimensions come up as 2 dimensions from the receiver, 2 dimensions from the source, and 1 is natural to be time, but it actually is the frequency. In the Parsimonious model you want to have some sparsity/simplicity, predictability, and  rank to be small (where tensor completion methods and Hankel methods play a role). The problem is that the algorithms around require regular and dense data. The solutions is to use linear and multilinear algebraic inverse theory. But there are infinitely many solutions, hence we need to put constraints (sparsity, stability, rank etc.) to get unique solutions. For example if you have

$\begin{bmatrix} d_1 \\ 0 \\ d_3 \\ d_4 \end{bmatrix} = \begin{bmatrix} 1 \\ & 0 \\ && 1 \\ &&& 1 \end{bmatrix} \begin{bmatrix} x_1 \\ x_2 \\ x_3 \\ x_4 \end{bmatrix}$,

where $d_i$s are observed data and $x_i$s are the true data, you can assume that $x = Fc$ for some Fourier transform $F$ and a sparse $c$. Then $d = SFc$. This tells us that signals that admit a sparse representation are important.

	- Levy, Walker Ulrych, and Fullagar in 1982 used linear programming to solve the problem but that method is old now.
	- Richard Baraniuk in 2007 used compressed sensing, but he had to assume random sampling.
	- Lustig Donoho, and Pauly in 2007 also used compressed sensing for rapid MRI imaging (sparse MRI).

The problem with all of them is that they cannot guarantee e.g. 99% recovery of data.

On the other hand there is always noise. Actually the noise increases the rank, so people use rank-reduction for de-noising the data. One of the most common ways for rank reduction is by using SVD (singular value decomposition) and keeping only the largest singular values. If you find a low-rank approximation then you will have

$M^{obs} = SM$,

$M^k = M^{obs} + (I-S) R [M^{k-1}]$.
