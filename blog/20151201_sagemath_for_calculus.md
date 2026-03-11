# Sagemath for calculus

I have used several geogebra applets in my calculus class, but there's always things that you wanna do that there's no applet out there for, or you can't modify them etc. So, I decided to write my own code for computer algebra applications in sage, and that I can share it with students so that they can play around with it, and modify it. It makes learning more fun. I have to look into interactive option for sage, then I can actually get rid of the animations. For now, I'm just going to post a few simple codes that get the work done:
Use [Sage Cloud](https://cloud.sagemath.com/) (requires login) or [Sage Cell server](http://sagecell.sagemath.org/) (does not require login) to run the following codes
```
# Use Newton's method to approximate a root of a function

def Newtons_method(f,a,n):
    var('x')
    f(x) = f
    guess = a
    fprime = f.derivative(x)
    g(x) = x-f(x)/fprime(x)
    N = n
    Sguess = [guess]
    print "Initial Guess: %20.16f"%(guess)
    for i in range(0,N):
        Nguess = g(guess)
        print "Next Guess:    %20.16f"%(Nguess)
        Sguess += [Nguess]
        guess = Nguess.n(digits=15)

    print "An estimate of the root is %20.16f"%(Sguess[N])

# Usage:
Newtons_method(x^2-57,9,5)
########################################################################

# Use Newton's method to approximate a root of a function with animation

var('x')

f(x) = x^2 - 1

xmin = 0
xmax = 3.1
ymin = -3
ymax = 9
guess = 3
fprime = f.derivative(x)
g(x) = x-f(x)/fprime(x)
N = 5
Sguess = [guess]
print "Initial Guess: %20.16f"%(guess)
P = plot(f(x), (xmin,xmax), ymin= ymin, ymax= ymax,color = "green",thickness=3)
Frames = [P]

for i in range(0,N):
    P += plot(point((guess,0),size = 20,rgbcolor=(0, 0, 1)))
    Frames += [P]
    P += plot(point((guess,f(guess)),size = 20,rgbcolor=(1, 0, 0)))
    Frames += [P]
    h = f(guess) + fprime(guess)*(x-guess)
    P += plot(h, (xmin,xmax),ymin= ymin, ymax= ymax, color = "blue")
    Frames += [P]
    Nguess = g(guess)
    print "Next Guess:    %20.16f"%(Nguess)
    Sguess += [Nguess]
    guess = Nguess.n(digits=15)

print "An estimate of the root is %20.16f"%(Sguess[N])

animate(Frames)
########################################################################

# Finding Taylor polynomial of a function with animation

var('x')
from sage.plot.colors import rainbow
n = 20
xmin = -10
xmax = 10

g = sin(x)

P = plot(g, (xmin,xmax), color = rainbow(n+1)[0],thickness=3)
Frames = []
for i in range(n):
    h = g.taylor(x, 0, i)
    P += plot(h, (xmin,xmax), color = rainbow(n+1)[i+1])
    Frames += [P]

m = 0
M = 12
a = animate(Frames,xmin=m,xmax=M,ymin=-1.5,ymax=1.5)
a
########################################################################
# Plot 3D with cross sections

var('x,y,z') 
f = x^2 + y^2
R = 4
sum([plot3d(f,(x,-R,R),(y,level,level+0.1),frame=False) for level in srange(-R,R,1)]+[implicit_plot3d(f==z,(x,-R,R),(y,-R,R),(z,-1,32),color='khaki',opacity=0.7,frame=False)])
########################################################################
# Plot 3D with level curves

var('x,y,z') 
f = x^2 + y^2
R = 4
sum([implicit_plot3d(f==level,(x,-R,R),(y,-R,R),(z,level,level+0.1),frame=False) for level in srange(0,16,2)]+[implicit_plot3d(f==z,(x,-R,R),(y,-R,R),(z,-1,16),color='khaki',opacity=0.7,frame=False)])

```
