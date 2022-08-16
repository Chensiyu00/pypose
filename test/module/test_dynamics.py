import sys
sys.path.append("..")
import torch as torch
import pypose as pp
import torch.nn as nn
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def test_dynamics():

    """
    For a System with p inputs, q outputs, and n state variables,
    A, B, C, D are n*n n*p q*n and q*p constant matrices.
    N: channels

    A = torch.randn((N,n,n))
    B = torch.randn((N,n,p))
    C = torch.randn((N,q,n))
    D = torch.randn((N,q,p))
    c1 = torch.randn(N,1,n)
    c2 = torch.randn(N,1,q)
    state = torch.randn((N,1,n))
    input = torch.randn((N,1,p))
    """

    # The most general case that all parameters are in the batch. 
    # The user could change the corresponding values according to the actual physical system and directions above.

    A_1 = torch.randn((5,4,4))
    B_1 = torch.randn((5,4,2))
    C_1 = torch.randn((5,3,4))
    D_1 = torch.randn((5,3,2))
    c1_1 = torch.randn((5,1,4))
    c2_1 = torch.randn((5,1,3))
    state_1 = torch.randn((5,1,4))
    input_1 = torch.randn((5,1,2))

    lti_1 = pp.module.LTI(A_1, B_1, C_1, D_1, c1_1, c2_1)
  
    # The user can implement this line to print each parameter for comparison.

    z_1, y_1 = lti_1(state_1,input_1)

    z_1_ref = state_1.matmul(A_1.mT) + input_1.matmul(B_1.mT) + c1_1
    y_1_ref = state_1.matmul(C_1.mT) + input_1.matmul(D_1.mT) + c2_1

    assert torch.allclose(z_1, z_1_ref)
    assert torch.allclose(y_1, y_1_ref)


    #In this example, A, B, C, D, c1, c2 are single inputs, state and input are in a batch.

    A_2 = torch.randn((4,4))
    B_2 = torch.randn((4,2))
    C_2 = torch.randn((3,4))
    D_2 = torch.randn((3,2))
    c1_2 = torch.randn((1,4))
    c2_2 = torch.randn((1,3))
    state_2 = torch.randn((5,1,4))
    input_2 = torch.randn((5,1,2))

    lti_2 = pp.module.LTI(A_2, B_2, C_2, D_2, c1_2, c2_2)

    z_2, y_2 = lti_2(state_2,input_2)

    z_2_ref = state_2.matmul(A_2.mT) + input_2.matmul(B_2.mT) + c1_2
    y_2_ref = state_2.matmul(C_2.mT) + input_2.matmul(D_2.mT) + c2_2

    assert torch.allclose(z_2, z_2_ref)
    assert torch.allclose(y_2, y_2_ref)


    # In this example, all parameters are single inputs.

    A_3 = torch.randn((4,4))
    B_3 = torch.randn((4,2))
    C_3 = torch.randn((3,4))
    D_3 = torch.randn((3,2))
    c1_3 = torch.randn((1,4))
    c2_3 = torch.randn((1,3))
    state_3 = torch.randn((1,4))
    input_3 = torch.randn((1,2))

    lti_3 = pp.module.LTI(A_3, B_3, C_3, D_3, c1_3, c2_3)

    z_3, y_3 = lti_3(state_3,input_3)

    z_3_ref = state_3.matmul(A_3.mT) + input_3.matmul(B_3.mT) + c1_3
    y_3_ref = state_3.matmul(C_3.mT) + input_3.matmul(D_3.mT) + c2_3

    assert torch.allclose(z_3, z_3_ref)
    assert torch.allclose(y_3, y_3_ref)

    print('Done')


if __name__ == '__main__':
    test_dynamics()

