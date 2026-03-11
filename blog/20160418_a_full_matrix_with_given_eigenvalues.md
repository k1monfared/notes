# A full matrix with given eigenvalues

## Induction: comprehension and precision

In Theorem 3.1 of "[The combinatorial inverse eigenvalue problems: complete graphs and small graphs with strict inequality, W. Barrett, A. Lazenby, N. Malloy, C. Nelson, W. Sexton, Electronic Journal of Linear Algebra, 656-672 (26) 2013](http://repository.uwyo.edu/cgi/viewcontent.cgi?article=1678&context=ela)" the authors show in an inductive process that $\lambda_1 \geq \lambda_2 \geq \cdots \geq \lambda_n$ are eigenvalues of a real symmetric matrix $A$ with no zero off-diagonal entries if and only if $\lambda_1 > \lambda_n$. Even though they don't mention it, the proof constructs a matrix whose diagonal entries are also nonzero, hence the result matrix is a full matrix. The induction is straightforward and uses a clever starting case, and then extends it using orthogonal similarities. A cool idea in the construction is that the diagonal entries of a real symmetric matrix are bounded by its smallest and largest eigenvalues (Corollary 2.6). Furthermore, if the matrix is **irreducible**, then the diagonal entries of the matrix are **strictly bounded** by the smallest and largest eigenvalues of the matrix (Lemma 2.7).

The following is a SAGE code to produce a full matrix for the given set of eigenvalues following the steps in the proof of Theorem 3.1 of the mentioned paper.

# this is an auxiliary function which computes the direct sum of two given matrices

def direct_sum(A,B):
    ar = A.nrows()
    ac = A.ncols()
    br = B.nrows()
    bc = B.ncols()
    M = matrix.block([[A, zero_matrix(ar,bc)],[zero_matrix(br,ac) ,B]])
    return(M)

# this is the main function which construct the matrix
def nonwhere_zero_matrix_with_spectrum(L):
    # L is a list of desired eigenvalues with at least two of them distinct
    L.sort()
    # This checks to see if at least two of them are distinct
    if L[0] == L[-1]:
        print('Not all eigenvalues can be equal. Such matrix does not exist')
        return()
    # We do an induction. The base of the iduction is a matrix with two eigenvalues that are the two smallest distinct numbers in the list L
    # Start with the first two numbers in the list:
    a = L[0]
    b = L[1]
    count = 0
    # Search until you find the second smallest number in the list that is not equal to the first number in the list
    while true:
        if L[count] > L[0]:
            b = L[count]
            count += 1 # this becomes the size of B
            break
        count += 1
    # Construct the matrix for the base:
    B = (b-a) / (count) * ones_matrix(count) + a * identity_matrix(count)
    # Here c and d will give me an orthogonal matrix Q. I'm letting them to be 1, but one could change them as desired, as long as they are nonzero we'll get what we need
    c = 1
    d = 1
    # This is the inductive step. Each time add a new row and column with a diagonal entry equal to a the next eigenvalue in the list, and then multiply by the orthogonal matrix to make that row and column nowherezero
    while count < len(L):
        B = direct_sum(matrix([L[count]]), B)
        Q = direct_sum(1/sqrt(c^2 + d^2) * matrix([[c,-d],[d,c]]),identity_matrix(count-1))
        B = (Q.transpose()) * B * Q
        count += 1
    # The desired matrix is ready
    return(B)

# Usage
A = nonwhere_zero_matrix_with_spectrum([1,1,1,3,3,6]) 
A.n(16)</pre>

To run the code in sage cell server click [here](http://sagecell.sagemath.org/?z=eJylVt9v2zYQfi_Q_-GAPERqFbfugD4U84B4GLAB7oCgHfZguAYlni0iEumSVB33r99HirKlJEA3TM4vHY_H77777pgr8rVyhC-hSXQPqlHCnmjX6coro-lYq6qmyrSHzrODM5NUlitPrmvJ7MgfDe3VN9bUCm9Vxe7lC8m75LWFV3ZbLPMPL18QHmFpQbczbc3RZXmyVb2tMs3ZVga_5dSvrHrb2K__-REL8fSHWdmY6j5br28L-s7WbHtzJmxRVvmmWI-NpS1ElVOx3Gwm4Sz7zurs49l49T8e7D5THNhrhdJP6dXO2w6k9h4BXc-iNvpYs-XtCPf2qHy9dQfQa8HuauD2ilaxjtQo50NpJDsUQRKrPetvoulQwLCXhKeGBZxC8UINa25RMOcVYPXBVjNnrJ_SfEWfQyJVzdU9kjHkmEntng8nLD8KCc_V-u2GFgv8vplvEuzwHKzSPrv-03gSTTMBXEGXJRN_7UQzo08d6OppIGmwrLGFH3DOdX4JlwoIywD8b4AxQeJKyy5SP0MyTKVwnCCTSis9iemQyFfIa4zJ10g5JBi2hUXXAjaDgSFj0l1bskXVdXSKJVlNyfzkhfXpALjslE0UPrN3aB9aRA5TQ8S3-WYctjKd9rC_fXQWCwvmsKYaOpkOp2kZozuG-uQlg_7wCe6YrkpchzqE2l8gP93RnwptN6DHdjyqdBRBBLmhX2Iuo8VLUr3HdKVP7fWC5pRaqgT2Nk0lp77HSi4fhbMs7i-mS4wpP78-04G0Mza-BpEklEugy8obkdMbymKwnF6R0eyGoZKMr1GrV5AUg3F_mi5eZPk7Wpsq6FKShBIg_TBKqeUgVfRfbfZGg-8E6G5Gf1y3aDYPke37PkMp0B7zgsrOByAhxUaiSYXec2pFN4yCIvzdGOwVkbVTVDGGTBgvdOTrgIAhylDxI1aYZdIVnTmT9IS-z6MBlzoMaTjPhxn9JiA8r0JOUoIVzUfCWI9JY5R3rU5DCc0j-nRBGu6gs9REjKv5wY-6cKy3IgbDGy6hrvHq0JyoPMXlpyQiYCvuuVf1IyDaxGkb2BhruFfNzyBeX8btIIfRRZeqvB70u8kLWo7m0t3Uff7GfcWMrb68g1zkl3dBSkOIdVXcSNxXsqhCmGeFdDPPR8GnqLK7mbdCu4NxnOUh8hLfdz_uhDAVh4sjMYbCoovkaXI7Lv_r7Rguwr-c2IdWugXCf3G1redF-PyEz_twReOfhGz-Pv8HfAyRNQ==&lang=sage), and to follow the code on github click [here](https://github.com/k1monfared/nowherezeromatrixconstruction/blob/master/nowherezeromatrixconstruction).

## Jacobian method: limitations vs. liberty

On the other hand, if you want to have control over the off-diagonal entries, and if the eigenvalues of the matrix are distinct, then you can use Theorem 4.2 from our paper "[Construction of matrices with a given graph and prescribed interlaced spectral data, Keivan Hassani Monfared and Bryan L. Shader, Linear Algebra and Its Applications; 4348–4358 (438) 2013](http://www.sciencedirect.com/science/article/pii/S0024379513001006)". An implementation of the process in the proof of the theorem in SAGE:

# Build variables, and the matrix corresponding to it
def build_variables(n):
    names = [ [[] for i in range(j+1)] for j in range(n) ]
    for i in range(n):
        for j in range(i+1):
            names[i][j] = (SR('x_' + str(j) + '_' + str(i)))
            #names[j][i] = (SR('x_' + str(j) + '_' + str(i)))
            
    return(names)

# Define the function f that maps a matrix to the coefficients of its characteristic polynomial
def CharPoly(Mat):
    X = matrix(Mat)
    n = X.ncols()
    C_X = X.characteristic_polynomial()
    Y = []
    for i in range(n):
        Y.append(C_X[i])
    return(Y)

# This solves that lambda SIEP
def lambda_siep(G,L,iter=100,epsilon = .1):
# G is any graph on n vertices
# L is the list of n desired distinct eigenvalues
# m is the number of itterations of the Newton's method
# epsilon: the off-diagonal entries will be equal to epsilon
    n = G.order()
    my_variables = build_variables(n)
    R = PolynomialRing(CC,[my_variables[i][j] for i in range(n) for j in range(i+1)])
    R.gens()
    R.inject_variables()
    X = [ [[] for i in range(n)] for j in range(n) ]
    for j in range(n):
        for i in range(j+1):
            X[i][j] =  R.gens()[j*(j+1)/2 + i]
            X[j][i] =  R.gens()[j*(j+1)/2 + i]
    Y = matrix(CharPoly(X)) - matrix(CharPoly(diagonal_matrix(L)))
    J = matrix(R,n)
    for i in range(n):
        for j in range(n):
            J[i,j] = derivative(Y[0][i],my_variables[j][j])
    B = diagonal_matrix(L) + epsilon * G.adjacency_matrix()
    count = 0
    while count < iter:
        T = [ B[i,j] for i in range(n) for j in range(i+1)]
        C = (J(T)).solve_right(Y(T).transpose())
        LC = list(C)
        B = B - diagonal_matrix([LC[i][0] for i in range(n)])
        count = count + 1
    return(B)

# This shows the output matrix, its eigenvalues and the eigenvlaues of A(i), and its graph
def check_output_lambda_siep(A,precision=8):
# A is a matrix which is the output of lambda_siep()
# i is the one that also is entered in lambda_siep()
# precision is an integer that shows how many digits do I want to be printed at the end, and I set the default to be 8
    eigA = A.eigenvalues()
    EigA = []
    for e in eigA:
        EigA = EigA + [e.n(precision)]
    print('A is:') 
    print(A.n(precision))
    print(' ')
    print('Eigenvalues of A are: %s') %(EigA)
    AdjA = matrix(A.ncols())
    for i in range(A.ncols()):
        for j in range(A.ncols()):
            if i != j:
                if A[i,j] != 0:
                    AdjA[i,j] = 1
    FinalGraph = Graph(AdjA)
    print(' ' )
    print('And the graph of A is:')
    FinalGraph.show()

# Usage:
G = graphs.CompleteGraph(5)
L = [1,2,3,4,5]
A = lambda_siep(G, L, iter=1000, epsilon=.1)
check_output_lambda_siep(A,precision=32)
</pre>

The proof relies on the Implicit Function Theorem, and that if the eigenvalues that you start with are away from zero, the diagonals of the matrix stay away from zero after adjustment. This way, you can set the off-diagonal entries of the matrix to be any small numbers. In particular you can set them all be equal to each other (that is what the above code does for simplicity), or choose them all to be positive numbers.

To run the code in sage cell server click [here](https://sagecell.sagemath.org/?z=eJyVVm1v2zYQ_h4g_-GKoLDUqJqTrkARzB8ULwsSeEXgZkAMwTBoibKpyaRK0k7z73ckRVlyvDXThzi6F_LuubvndAbXW1blsCOSkWVFVQSE56DXFDZES_YDMiElVbXgOeMr0AKYPj3JaQFL47hoHQMeXp2eAD6cbKiCEaSQpnMohAQGjIMkfEWD8vwidMJyL-QhzJ3vgXV7ptd1nBie1NG2N6dsnpZzvD_4Ng0GPxYDOAelZVCG-M-gfWVhGDpvSfVW8sA6o-j05Ax-pwXj1MJQbHmmmeBQ4CvRCEutgHh0EA9jlAlaFCxjlGsFokCMFGRrIkmmqWRKswxqUb1wsWGkcvCNUf2AsuBPon0eTxi1O9hKGzhR-BTzTFQqaETjxZMV9q9Y7K_whjNThjdAO4tJXVOeB3gy4tcHZtaA8rhmCpSodlhdC0VFNsucwLe7mweXkxMsFKN1cBtNIoahjS6Gw4jWilXCZBLbop3BLeBhhL_ASpJ6DajjsKMS06DK6CdGb6CtMDcDKYecKiZpDrnJFosClK0o35Fq61w23oVvN0sqXR0wAmLKZ8tilF_psxZ8oGBD9VrkxrGJ7srqRVF8zBlZCU4qwHpKhuk-s6qCJQX6fYtSLHrjsq_QbSxkTqUHfvOynwzUvp4VZzZF3UNbtSlOWDAeR2nXu2nnV9U7Ng6-cNMYgWm7ZRozXtJMd-4P9_12dEr5z2a0_I8ZPZj2gxl9auezDTMtP1jLXy5xNtn80L6co8tP7Wf72WlH6ykM4eMrqa_uolFMWia4358xjXyN_gcl8cNk71MW2VyxNdgOG3FHg1k6NAlFvSKXBpPmwmtj_ypGTNVP0QfsNpKXJKM8e_EWjXMmtlzjAUP3-rxmFW2Ev4GZx06Ej7b81y7GtzXY3nlsGPY-eAzD2HLCQrLVWgczlMQaPXBlKBp4ZM0zMS5mnINxR2qyvcYqHWacTsamU4bHerPj7vN1v-dw0aOu6x51rcWzIwix1fVWN6WOLFt3uKTdgE5WESND9khwZ7j1aBwsbznay9Y0-3vhDl10OTCJakkzppB_Rl8c7yWW9_z6wPJka09bTVSiz6Oh8WKtjd1KyL2kUsIIkaGoIUWE55VXe7njWrTRdIXEaA9waOAfjAVpOGcrk1Uu4A6eCUKJJIeEV0vjlAM6WER47hC4A0WdCAEg28rbf3HwI3IJFiWJO7D6Dr1xuu5aoiZ849NpzsbM_pxDSmMetPn4PrTRBQOD6dUghK4w6dmHPXsY9N9vOrU3dQYi6RW8V3jk-8AE0JgneZnsGSLxO_k4T-zV_84XR23Mw3B1wbsRlAfyRpe4kUWD4REDH6rnnmYk_mA4Xbd22-K6Mr-BsTqEBvqCpJmFZk0X0IB9eGZs-iloxu0vRVYUI7vFm6yjisdiU1dUU3fxZzScmCa4iC6jT9Gv0WesqMG2_wUBkwj8N8Qw8vw3wm-I05M3Dd2ny_Af-VEvsg==&lang=sage), and to follow it on github click [here](https://github.com/k1monfared/lambda_siep).

Assuming the eigenvalues are all positive, the induction method gets really close to producing an entrywise positive matrix, but the rotations actually ensure that some of the entries become negative! On the other hand the Jacobian method would result in an entrywise positive matrix if the perturbations of the off-diagonal entries are small enough that the adjustments of the diagonal entries wont make them zero or negative. To be fair, even if you start with a zero eigenvalue (you cannot have more than one, because the Jacobian method requires the matrix to have distinct eigenvalues), since the diagonal entries are strictly bounded by the smallest and largest eigenvalues, we have the following theorem:

**Theorem. **Given real numbers $\lambda_1 > \lambda_2 > \ldots > \lambda_n \geq 0$, there is an entrywise positive matrix with the given eigenvalues.

---

## Old Comments

> **Markus** — January 29, 2019
> 
> Nice one!
> Seems there is some error when running the code in the link though!
> Helped me out a great deal
> 
> > **k1monfared** — January 31, 2019
> > 
> > Ah, thanks for pointing out the error. It is fixed now.

