# If you treat a network like a dynamical system...

Let's say we have a graph (i.e. network), and we want to cluster the vertices (nodes).  Here, think of the nodes as people, agents, oscillators, some dynamic being, and the edges... the edges tell you if these people are **friends or enemies**, and how much, they tell you if the agents want to collaborate with each other or not, they tell you if the oscillators **attract** each other or **repel** each other, and how much. This means we have a (signed weighted) network that can be treated as a dynamical system. One of the most famous and simple (nonlinear) dynamical systems that can model **attraction/repulsion** is the [Kuramoto ](https://en.wikipedia.org/wiki/Kuramoto_model)model. In simple terms, it says if you have $n$ oscillators $i$ and each of them is moving around the unit circle with a natural frequency $\omega_i$ while being attracted/repelled by other oscillators $j$ as strongly as $a_{ij}$, the derivative of its phase with respect to time (the angular velocity, the rate of change of its phase) is given by

![$frac{rm{d} theta_i}{rm{d} t} = omega_i + frac{k}{n} sum_{j=1}^{n} A_{ij} sin(theta_j - theta_i),$](files/20180921/kuramoto.jpg) The Kuramoto model

where $k$, is called the coupling strength of the system. At the beginning when they are not coupled, their movement looks like this:

 

![kuramoto_uncoupled.gif](files/20180921/kuramoto_uncoupled.gif) Five uncoupled oscillators with some natural frequencies

 

The order parameter, which is simply the length of the vector of the sum of their positions, will look like this:

![kuramoto_uncoupled_order](files/20180921/kuramoto_uncoupled_order.jpg)

There is no synchrony. But if we assume all of them attract each other, that is, if all $a_{ij} = 1$, then they'll start behaving like this:

 

![kuramoto_coupled](files/20180921/kuramoto_coupled1.gif) Five coupled oscillators with some natural frequencies

 

They soon synchronize and stay "together"! The order parameter will look like this:

![kuramoto_coupled_order](files/20180921/kuramoto_coupled_order.jpg)

I'm not sure what those bumps towards the right end are, beginning of a chaos?

Anyways, the fact that all of them synced together tells me that the network is very well connected, and probably I don't want to break it into clusters since there's only one meaningful cluster out there.  But if I start with some network like this: ![outputs_2018_9_18_14_27_15_fig_1.png](files/20180921/outputs_2018_9_18_14_27_15_fig_11.png)

And run the model, I will end up with some final phases like![outputs_2018_9_18_14_27_15_fig_4.png](files/20180921/outputs_2018_9_18_14_27_15_fig_4.png)Which, in turn, will be clustered as

![outputs_2018_9_18_14_27_15_fig_5.png](files/20180921/outputs_2018_9_18_14_27_15_fig_5.png)

This reveals the underlying clustering of my network. Matlab/Octave code for calculations can be found on my [GitHub](https://github.com/k1monfared/kuramoto_clustering).
