import sys
import pymc3 as pm
import theano.tensor as tt
import numpy as np

import matplotlib.pyplot as plt

# set the seed
np.random.seed(5)

n = 100 # The number of data points
n2 = 20
X = np.linspace(0, 1, n)[:, None] # The inputs to the GP, they must be arranged as a column vector
X_obs = np.linspace(0.1, 0.9, n2)[:, None] # The inputs to the GP, they must be arranged as a column vector


# Define the true covariance function and its parameters
ℓ_true = 0.5
η_true = 0.01
cov_func = η_true**2 * pm.gp.cov.ExpQuad(1, ℓ_true)

# A mean function that is zero everywhere

a_true = 0.4
b_true = 10
#b_true = (b_true/2)**(1/2)
c_true = 0.4
mean_func_true = a_true * np.exp(-X*b_true) + c_true
mean_func_true = mean_func_true.flatten()

mean_func_obs = a_true * np.exp(-X_obs*b_true) + c_true
mean_func_obs = mean_func_obs.flatten()

#f_true = np.random.multivariate_normal(mean_func,cov_func(X).eval() + 1e-8*np.eye(n), 1).flatten()

f_true = np.random.multivariate_normal(mean_func_obs,
                                       cov_func(X_obs).eval() + 1e-8*np.eye(n2), 1).flatten()


# The observed data is the latent function plus a small amount of T distributed noise
# The standard deviation of the noise is `sigma`, and the degrees of freedom is `nu`
σ_true = 0.01
y = f_true + σ_true * np.random.randn(n2)

## Plot the data and the unobserved latent function
fig = plt.figure(figsize=(12,5)); ax = fig.gca()
ax.plot(X, mean_func_true, "dodgerblue", lw=3, label="True f");
ax.plot(X_obs, y, 'ok', ms=3, label="Data");
ax.set_xlabel("X"); ax.set_ylabel("y"); plt.legend();




class CustomMean(pm.gp.mean.Mean):

    def __init__(self, a = 0, b = 1, c = 0):
        pm.gp.mean.Mean.__init__(self)
        self.a = a
        self.b = b
        self.c = c


    def __call__(self, X):
        rot_prof = tt.squeeze(self.a * tt.exp(tt.dot(-X,self.b)) + self.c)
        print(rot_prof)
        print(rot_prof.ndim,rot_prof.shape)
        return rot_prof

        # A one dimensional column vector of inputs.
        n_param = 20

        X_stumf = np.linspace(0.1, 0.9, n_param)[:, None]


with pm.Model() as model:

    ℓ = pm.Gamma("ℓ", alpha=2, beta=4)
    η = pm.HalfNormal("η", sigma=1.0)

    cov_trend = η**2 * pm.gp.cov.ExpQuad(1, ℓ)


    a_var = pm.Normal("a_var", mu = 0.4, sigma=0.5)
    b_var = pm.Normal("b_var", mu = 10., sigma=0.5)
    c_var = pm.Normal("c_var", mu = 0.4, sigma=0.5)


    mean_trend = CustomMean(a = a_var, b= b_var, c= c_var)

    gp_trend = pm.gp.Latent(mean_func = mean_trend , cov_func=cov_trend)

    f = gp_trend.prior("f", X = X_obs)

    # The Gaussian process is a sum of these three components
    σ  = pm.HalfNormal("σ",  sigma=2.0)

    y_ = pm.StudentT('y', mu = f, sigma = σ, nu = 1 ,observed = y)

    # this line calls an optimizer to find the MAP
    #mp = pm.find_MAP(include_transformed=True)


    trace = pm.sample(1000, chains=1)





fig = plt.figure(figsize=(12,5)); ax = fig.gca()
# plot the samples from the gp posterior with samples and shading
from pymc3.gp.util import plot_gp_dist
plot_gp_dist(ax, trace["f"], X_obs);

# plot the data and the true latent function
ax.plot(X, mean_func_true, "dodgerblue", lw=3, label="True f");
ax.plot(X_obs, y, 'ok', ms=3, label="Data");
ax.set_xlabel("X"); ax.set_ylabel("y"); plt.legend();
# axis labels and title
plt.xlabel("X"); plt.ylabel("True f(x)");
plt.title("Posterior distribution over $f(x)$ at the observed values"); plt.legend();

#create the posterior/trace plots of the variables.
lines = [
    ("η",  {}, η_true**2),
    ("σ", {}, 0.003),
    ("ℓ", {}, ℓ_true),
    ("a_var", {}, 0.4),
    ("b_var", {}, 10),
    ("c_var", {}, 0.4),
]
pm.traceplot(trace, lines=lines, var_names=["η", "σ", "ℓ", "a_var","b_var","c_var"]);
