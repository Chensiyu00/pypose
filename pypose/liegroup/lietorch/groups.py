import torch
import numpy as np
from torch import nn
from .types import SO3_type, so3_type, SE3_type, se3_type
from .broadcasting import broadcast_inputs
from .group_ops import exp, log, inv, mul, adj
from .group_ops import adjT, jinv, act3, act4, toMatrix, toVec, fromVec


def SO3(data, **kwargs):
    assert data.shape[-1] == SO3_type.dim, 'Init Dimension Invalid.'
    return LieGroup(data, gtype=SO3_type, **kwargs)

def so3(data, **kwargs):
    assert data.shape[-1] == so3_type.dim, 'Init Dimension Invalid.'
    return LieGroup(data, gtype=so3_type, **kwargs)

def SE3(data, **kwargs):
    assert data.shape[-1] == SE3_type.dim, 'Init Dimension Invalid.'
    return LieGroup(data, gtype=SE3_type, **kwargs)

def se3(data, **kwargs):
    assert data.shape[-1] == se3_type.dim, 'Init Dimension Invalid.'
    return LieGroup(data, gtype=se3_type, **kwargs)

def Exp(x):
    assert isinstance(x, LieGroup), "Not a LieGroup Instance"
    assert x.gtype.is_manifold is True, "Manifold space has no Exp operation"
    inputs, out_shape = broadcast_inputs(x, None)
    out = exp.apply(x.gtype.group_id, *inputs)
    return LieGroup(out.view(out_shape + (-1,)), gtype=x.gtype.mapping_type, requires_grad=x.requires_grad)

def Log(x):
    assert isinstance(x, LieGroup), "Not a LieGroup Instance"
    assert x.gtype.is_manifold is False, "Embedded space has no Log operation"
    inputs, out_shape = broadcast_inputs(x, None)
    out = log.apply(x.gtype.group_id, *inputs)
    return LieGroup(out.view(out_shape + (-1,)), gtype=x.gtype.mapping_type, requires_grad=x.requires_grad)

def randn_so3(*args, requires_grad=False, **kwargs):
    data = torch.randn(*(list(args)+[so3_type.dim]), **kwargs).detach()
    return so3(data, **kwargs).requires_grad_(requires_grad)

def randn_SO3(*args, requires_grad=False, **kwargs):
    data = Exp(randn_so3(*args, **kwargs)).detach()
    return SO3(data, **kwargs).requires_grad_(requires_grad)

def randn_se3(*args, requires_grad=False, **kwargs):
    data = torch.randn(*(list(args)+[se3_type.dim]), **kwargs).detach()
    return se3(data, **kwargs).requires_grad_(requires_grad)

def randn_SE3(*args, requires_grad=False, **kwargs):
    data = Exp(randn_se3(*args, **kwargs)).detach()
    return SE3(data, **kwargs).requires_grad_(requires_grad)


class LieGroup(torch.Tensor):
    """ Lie Group """

    from torch._C import _disabled_torch_function_impl
    __torch_function__ = _disabled_torch_function_impl

    def __init__(self, data, gtype=None, **kwargs):
        self.gtype = gtype

    def __new__(cls, data=None, **kwargs):
        return torch.Tensor.as_subclass(data, LieGroup) 

    def __repr__(self):
        return self.gtype.__class__.__name__ + " Group:\n" + super().__repr__()

    @property
    def gtype(self):
        return self.__gtype

    @gtype.setter
    def gtype(self, val):
        self.__gtype = val

    @property
    def gshape(self):
        return self.shape[:-1]

#    def vec(self):
#        return self.apply_op(ToVec, self.data)

    @classmethod
    def Identity(cls, *batch_shape, **kwargs):
        """ Construct identity element with batch shape """
        
        if isinstance(batch_shape[0], tuple):
            batch_shape = batch_shape[0]
        
        elif isinstance(batch_shape[0], list):
            batch_shape = tuple(batch_shape[0])

        numel = np.prod(batch_shape)
        data = cls.id_elem.reshape(1,-1)

        if 'device' in kwargs:
            data = data.to(kwargs['device'])

        if 'dtype' in kwargs:
            data = data.type(kwargs['dtype'])

        data = data.repeat(numel, 1)
        return cls(data).view(batch_shape)

    @classmethod
    def IdentityLike(cls, G):
        return cls.Identity(G.shape, device=G.data.device, dtype=G.data.dtype)

    @classmethod
    def InitFromVec(cls, data):
        return cls(cls.apply_op(FromVec, data))

    @classmethod
    def Random(cls, *batch_shape, sigma=1.0, **kwargs):
        """ Construct random element with batch_shape by random sampling in tangent space"""

        if isinstance(batch_shape[0], tuple):
            batch_shape = batch_shape[0]
        
        elif isinstance(batch_shape[0], list):
            batch_shape = tuple(batch_shape[0])
        
        tangent_shape = batch_shape + (cls.manifold_dim,)
        xi = torch.randn(tangent_shape, **kwargs)
        return cls.exp(sigma * xi)

    @classmethod
    def apply_op(cls, op, x, y=None):
        """ Apply group operator """
        inputs, out_shape = broadcast_inputs(x, y)

        data = op.apply(cls.group_id, *inputs)
        return data.view(out_shape + (-1,))

    def Exp(self):
        return Exp(self)

    def Quaternion(self):
        """ extract quaternion """
        return self.apply_op(Quat, self.data)

    def Log(self):
        """ logarithm map """
        return Log(self)

    def Inv(self):
        """ group inverse """
        return self.__class__(self.apply_op(Inv, self.data))

    def Mul(self, other):
        """ group multiplication """
        return self.__class__(self.apply_op(Mul, self.data, other.data))

    def Retr(self, a):
        """ retraction: Exp(a) * X """
        dX = self.__class__.apply_op(Exp, a)
        return self.__class__(self.apply_op(Mul, dX, self.data))

    def Adj(self, a):
        """ adjoint operator: b = A(X) * a """
        return self.apply_op(Adj, self.data, a)

    def AdjT(self, a):
        """ transposed adjoint operator: b = a * A(X) """
        return self.apply_op(AdjT, self.data, a)

    def Jinv(self, a):
        return self.apply_op(Jinv, self.data, a)

    def Act(self, p):
        """ action on a point cloud """
        
        # action on point
        if p.shape[-1] == 3:
            return self.apply_op(Act3, self.data, p)
        
        # action on homogeneous point
        elif p.shape[-1] == 4:
            return self.apply_op(Act4, self.data, p)

    def matrix(self):
        """ convert element to 4x4 matrix """
        I = torch.eye(4, dtype=self.dtype, device=self.device)
        I = I.view([1] * (len(self.data.shape) - 1) + [4, 4])
        return self.__class__(self.data[...,None,:]).act(I).transpose(-1,-2)

    def translation(self):
        """ extract translation component """
        p = torch.as_tensor([0.0, 0.0, 0.0, 1.0], dtype=self.dtype, device=self.device)
        p = p.view([1] * (len(self.data.shape) - 1) + [4,])
        return self.apply_op(Act4, self.data, p)

#    def __mul__(self, other):
        # group multiplication
#        if isinstance(other, LieGroup):
#            return self.mul(other)

#        elif isinstance(other, torch.Tensor):
#            return self.act(other)


class Parameter(LieGroup, nn.Parameter):
    def __new__(cls, data=None, gtype=None, requires_grad=True):
            if data is None:
                data = torch.tensor([])
            return LieGroup._make_subclass(cls, data, requires_grad)