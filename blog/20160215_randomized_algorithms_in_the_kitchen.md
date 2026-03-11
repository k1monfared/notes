# Randomized algorithms in the kitchen

Officially, I first learned about randomized algorithms and derandomizing them in a course called Randomness in Computations, offered by John Hitchcock at University of Wyoming. It wasn't until then that I realized my old friend Hossein Rahmani had taught me a very cool application of this back in the day when we lived in the dorm in Tehran, without any of us having any idea what we are doing.

Here is a little bit of background: In Iran we have this dish made out of Sausage, potatoes, and eggs. Basically, you cut sausages into rings, cube the potatoes, and fry them, then add the eggs. There are tons of variations of it and it's all quick and easy, hence a good choice for dorm food!

The problem is in frying the ringed sausages. Heat up a big pan and put some oil in it, after the oil is hot add the sausage rings. While they start getting brown it's time to flip them so that the other side also becomes brown! In order to do so, I normally start flipping them one by one, so that I can make sure that nothing is left unflipped. But the problem is at the point you start flipping them in one side of the pan, the ones on the other side of the pan start burning, and that's not cool. Of course, you don't want to also loose time by taking the pan off the stove and flipping them all. So here is a solution: Randomize your algorithm!

I mean, take a big spatchula, dig in, and flip everything you can at random. After a few tries you've flipped about half of the rings quickly. Now the ones which are not flipped look lighter in colour. It's time to derandomize your algorithm now: flip the not-flipped-ones one by one.

Of course the derandomization part is not really a derandomization technique, but certainly can be seen as a combination of randomized and deterministic algorithms. Thanks Hossein and John for making my life so much better.
