import numpy as np
import pandas as pd
import torch


def set_seeds(seed: int):
    """Set random seeds for reproducibility."""
    np.random.seed(seed)
    torch.manual_seed(seed)


def branin(x1, x2):
    y = float(
        (x2 - 5.1 / (4 * np.pi**2) * x1**2 + 5.0 / np.pi * x1 - 6.0) ** 2
        + 10 * (1 - 1.0 / (8 * np.pi)) * np.cos(x1)
        + 10
    )

    return y


def ackley(x1, x2, a=20, b=0.2, c=2 * np.pi): # [-32.768, 32.768]
    """
    ACKLEY FUNCTION

    Authors: Sonja Surjanovic, Simon Fraser University
             Derek Bingham, Simon Fraser University

    Parameters:
    xx : list or numpy array
        Input vector [x1, x2, ..., xd]
    a : float, optional
        Constant (default is 20)
    b : float, optional
        Constant (default is 0.2)
    c : float, optional
        Constant (default is 2*pi)

    Returns:
    y : float
        Output of the Ackley function
    """
    xx = np.array([x1, x2])
    d = len(xx)

    sum1 = np.sum(xx**2)
    sum2 = np.sum(np.cos(c * xx))

    term1 = -a * np.exp(-b * np.sqrt(sum1 / d))
    term2 = -np.exp(sum2 / d)

    y = term1 + term2 + a + np.exp(1)

    return y

# credit: @sgbaird for above code

# dummy functions for testing different generation strategies

def noisy_quadratic(x, noise_scale=0.1, rng=None): # [-5.0, 5.0]
    """Sparse quadratic function with noise.
    Only x[0], x[3], x[6], x[9], x[12] affect the output."""
    if rng is None:
        rng = np.random.default_rng()
    active_params = x[0]**2 + 0.5 * x[3]**2 + 0.3 * x[6] + 0.7 * x[9] - 1.2 * x[12]
    noise = noise_scale * rng.normal()
    return active_params + noise

def noisy_rosenbrock(x, noise_scale=0.1, rng=None): # [-2.0, 2.0]
    """14D Rosenbrock with multiplicative Gaussian noise."""
    if rng is None:
        rng = np.random.default_rng()
    rosenbrock = sum(
        100 * (x[i+1] - x[i]**2)**2 + (1 - x[i])**2 
        for i in range(len(x)-1)
    )
    noise = noise_scale * rosenbrock * rng.normal()
    return rosenbrock + noise

def noisy_mixed(x, noise_scale=0.2, rng=None): # [-3.0, 3.0]
    """Linear + periodic terms with input-dependent noise."""
    if rng is None:
        rng = np.random.default_rng()
    linear_part = 2.0 * x[0] - 1.5 * x[1] + sum(0.1 * x[i] for i in range(2, 8))
    periodic_part = 3.0 * np.sin(2 * np.pi * x[8]) + np.cos(2 * np.pi * x[9])
    interaction_part = x[10] * x[11] - 0.5 * x[12] * x[13]
    noise = noise_scale * (1.0 + np.abs(x[0])) * rng.normal()  # Noise scales with |x[0]|
    return linear_part + periodic_part + interaction_part + noise

def polynomial_14d(x, noise_scale=0.1): # [-5.0, 5.0]
    """14D quadratic function with sparse interactions and noise."""
    rng = np.random.default_rng()
    
    # Objectives (quadratic + sparse linear terms)
    f1 = 2.0 * x[0]**2 - 1.5 * x[1] + 0.3 * x[2]*x[3] + 0.1 * sum(x[4:7]) + noise_scale * rng.normal()
    f2 = 0.5 * x[0] + 0.2 * x[1]**2 - 0.4 * x[5]*x[6] + 0.1 * sum(x[7:10]) + noise_scale * rng.normal()
    f3 = -1.0 * x[0] + 0.7 * x[1]*x[2] + 0.05 * sum(x[10:14]) + noise_scale * rng.normal()
    
    return {"f1": f1, "f2": f2, "f3": f3}

def sigmoid_14d(x, noise_scale=0.1): # [-3.0, 3.0]
    """14D sigmoid-based function with input-dependent noise."""
    rng = np.random.default_rng()
    
    # Sigmoid: S(x) = 1 / (1 + exp(-x))
    f1 = 1.0 / (1 + np.exp(-x[0])) + 0.2 * x[1] - 0.3 / (1 + np.exp(-x[2])) + noise_scale * rng.normal()
    f2 = 0.5 / (1 + np.exp(-2 * x[3])) + 0.1 * sum(x[4:6]) + noise_scale * (1 + abs(x[3])) * rng.normal()
    f3 = -1.0 / (1 + np.exp(-x[6])) + 0.3 * x[7] + 0.05 * sum(x[8:14]) + noise_scale * rng.normal()
    
    return {"f1": f1, "f2": f2, "f3": f3}

def mixed_14d(x, noise_scale=0.15): # [-pi, pi] for x[0], x[2], x[4], x[10], x[11], [-3.0, 3.0] for rest
    """14D mix of sin/cos, linear, and periodic terms."""
    rng = np.random.default_rng()
    
    f1 = np.sin(x[0]) + 0.5 * x[1] + 0.2 * np.cos(x[2]*x[3]) + noise_scale * rng.normal()
    f2 = np.cos(x[4]) - 0.3 * x[5] * x[6] + 0.1 * sum(x[7:10]) + noise_scale * (0.5 + abs(x[4])) * rng.normal()
    f3 = 0.2 * (x[0] + x[1] + x[2]) + np.sin(x[10]) * np.cos(x[11]) + noise_scale * rng.normal()
    
    return {"f1": f1, "f2": f2, "f3": f3}