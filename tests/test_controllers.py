#! /home/song3/anaconda3/envs/pilco/bin/python 
import sys
sys.path.append("/home/song3/Research/PILCO-gpytorch")
from pilco.controllers import RbfController, LinearController, squash_sin
import numpy as np
import os
import torch
# import oct2py
# octave = oct2py.Oct2Py()
# dir_path = os.path.dirname(os.path.realpath("__file__")) + "/tests/Matlab Code"
# octave.addpath(dir_path)


def test_rbf():
    np.random.seed(0)
    d = 3  # Input dimension
    k = 2  # Number of outputs
    b = 100 # basis functions

    # Training Dataset
    X0 = np.random.rand(100, d)
    A = np.random.rand(d, k)
    Y0 = np.sin(X0).dot(A) + 1e-3*(np.random.rand(100, k) - 0.5)  #  Just something smooth
    rbf = RbfController(3, 2, b)
    rbf.set_XY(X0, Y0)

    # Generate input
    m = np.random.rand(1, d)  # But MATLAB defines it as m'
    s = np.random.rand(d, d)
    s = s.dot(s.T)  # Make s positive semidefinite

    M, S, V = rbf.compute_action(m, s, squash=False)

    print("M\n",M)
    print("S\n",S)
    print("V\n",V)
    # convert data to the struct expected by the MATLAB implementation
    lengthscales = rbf.model.covar_module.lengthscale.cpu().detach().numpy().squeeze()
    variance = 1*np.ones(k)  
    noise = rbf.model.likelihood.noise.cpu().detach().numpy().squeeze()


    hyp = np.log(np.hstack(
        (lengthscales,
         np.sqrt(variance[:, None]),
         np.sqrt(noise[:, None]))
    )).T

    gpmodel = oct2py.io.Struct()
    gpmodel.hyp = hyp
    gpmodel.inputs = X0
    gpmodel.targets = Y0

    # Call gp0 in octave
    M_mat, S_mat, V_mat = octave.gp2(gpmodel, m.T, s, nout=3)

    assert M.shape == M_mat.T.shape
    assert S.shape == S_mat.shape
    assert V.shape == V_mat.shape
    np.testing.assert_allclose(M, M_mat.T, rtol=1e-4)
    np.testing.assert_allclose(S, S_mat, rtol=1e-4)
    np.testing.assert_allclose(V, V_mat, rtol=1e-4)

def test_linear():
    np.random.seed(0)
    d = 3  # Input dimension
    k = 2  # Output dimension
    # Generate input
    m = np.random.rand(1, d)  # But MATLAB defines it as m'
    s = np.random.rand(d, d)
    s = s.dot(s.T)  # Make s positive semidefinite

    W = np.random.rand(k, d)  # But MATLAB defines it as m'
    b = np.random.rand(1, k)

    linear = LinearController(d, k)
    linear.W = torch.from_numpy(W).float().cuda()
    linear.b = torch.from_numpy(b).float().cuda()

    M, S, V = linear.compute_action(m, s,squash=False)

    # convert data to the struct expected by the MATLAB implementation
    policy = oct2py.io.Struct()
    policy.p = oct2py.io.Struct()
    policy.p.w = W
    policy.p.b = b.T

    # Call function in octave
    M_mat, S_mat, V_mat = octave.conlin(policy, m.T, s, nout=3)

    assert M.shape == M_mat.T.shape
    assert S.shape == S_mat.shape
    assert V.shape == V_mat.shape
    np.testing.assert_allclose(M, M_mat.T, rtol=1e-4)
    np.testing.assert_allclose(S, S_mat, rtol=1e-4)
    np.testing.assert_allclose(V, V_mat, rtol=1e-4)

def test_squash():
    np.random.seed(0)
    d = 3  # Control dimensions

    m = np.random.rand(1, d)  # But MATLAB defines it as m'
    s = np.random.rand(d, d)
    s = s.dot(s.T)
    e = 7.0

    M, S, V = squash_sin(torch.tensor(m).float().cuda(), torch.tensor(s).float().cuda(), torch.tensor(e).float().cuda())

    M_mat, S_mat, V_mat = octave.gSin(m.T, s, e, nout=3)
    M_mat = np.asarray(M_mat)
    import pdb;pdb.set_trace()

    assert M.shape == M_mat.T.shape
    assert S.shape == S_mat.shape
    assert V.shape == V_mat.shape

    np.testing.assert_allclose(M, M_mat.T, rtol=1e-4)
    np.testing.assert_allclose(S, S_mat, rtol=1e-4)
    np.testing.assert_allclose(V, V_mat, rtol=1e-4)


if __name__ == '__main__':
    test_rbf()
    # test_linear()
    # test_squash()
