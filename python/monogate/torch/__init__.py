"""
monogate.torch — Differentiable EML arithmetic layers for PyTorch.

Public API:

    EMLActivation  — EML tree as a scalar activation function.
                     Drop-in replacement for torch.sin / F.gelu / F.relu.

    EMLLayer       — EML layer combining Linear + EMLActivation (default)
                     or out_features independent EML expression trees.

Example::

    from monogate.torch import EMLLayer, EMLActivation
    import torch

    # SIREN-style layer with learned EML activation instead of sin:
    layer = EMLLayer(256, 256, depth=2, operator='EML')
    x     = torch.randn(8, 256)
    y     = layer(x)                    # (8, 256)

    # EML activation standalone:
    act = EMLActivation(depth=2, operator='BEST')
    z   = act(torch.randn(32, 64))      # (32, 64)

    # Interpretable tree mode (shows learned formula):
    layer_tree = EMLLayer(4, 2, depth=2, mode='tree')
    print(layer_tree.formula(['x', 'y', 'z', 'w']))  # list of 2 formulas
"""

from .eml_layer import EMLActivation, EMLLayer, compare_to_native

__all__ = ["EMLActivation", "EMLLayer", "compare_to_native"]
