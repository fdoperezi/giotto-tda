"""Utilities for input validation."""
# License: GNU AGPLv3

import numpy as np


def check_diagram(X, copy=False):
    """Input validation on a persistence diagram.

    """
    if X.ndim != 3:
        raise ValueError(f"X should be a 3d np.array: X.shape = {X.shape}.")
    if X.shape[2] != 3:
        raise ValueError(
            f"X should be a 3d np.array with a 3rd dimension of 3 components: "
            f"X.shape[2] = {X.shape[2]}.")

    homology_dimensions = sorted(list(set(X[0, :, 2])))
    for dim in homology_dimensions:
        if dim == np.inf:
            if len(homology_dimensions) != 1:
                raise ValueError(
                    f"np.inf is a valid homology dimension for a stacked "
                    f"diagram but it should be the only one: "
                    f"homology_dimensions = {homology_dimensions}.")
        else:
            if dim != int(dim):
                raise ValueError(
                    f"All homology dimensions should be integer valued: "
                    f"{dim} can't be cast to an int of the same value.")
            if dim != np.abs(dim):
                raise ValueError(
                    f"All homology dimensions should be integer valued: "
                    f"{dim} can't be cast to an int of the same value.")

    n_points_above_diag = np.sum(X[:, :, 1] >= X[:, :, 0])
    n_points_global = X.shape[0] * X.shape[1]
    if n_points_above_diag != n_points_global:
        raise ValueError(
            f"All points of all persistence diagrams should be above the "
            f"diagonal, X[:,:,1] >= X[:,:,0]. "
            f"{n_points_global - n_points_above_diag} points are under the "
            f"diagonal.")
    if copy:
        return np.copy(X)
    else:
        return X


def check_graph(X):
    return X


def _validate_params_single(parameter, reference, name):
    if reference is None:
        return

    ref_type = reference.get('type', None)

    # Check that parameter has the correct type
    if (ref_type is not None) and (not isinstance(parameter, ref_type)):
        raise TypeError(
            f"Parameter `{name}` is of type {type(parameter)} while "
            f"it should be of type {ref_type}.")

    # If the reference type parameter is not list, tuple, np.ndarray or dict,
    # the checks are performed on the parameter object directly.
    elif ref_type not in [list, tuple, np.ndarray, dict]:
        ref_in = reference.get('in', None)
        ref_other = reference.get('other', None)
        if parameter is not None:
            if (ref_in is not None) and (parameter not in ref_in):
                raise ValueError(
                    f"Parameter `{name}` is {parameter}, which is not in "
                    f"{ref_in}.")
        # Perform any other checks via the callable ref_others
        if ref_other is not None:
            return ref_other(parameter)

    # Explicitly return the type of reference if one of list, tuple, np.ndarray
    # or dict.
    else:
        return ref_type


def _validate_params(parameters, references, rec_name=None):
    for name, parameter in parameters.items():
        if name not in references.keys():
            name_extras = "" if rec_name is None else f" in `{rec_name}`"
            raise KeyError(
                f"`{name}`{name_extras} is not an available parameter. "
                f"Available parameters are in {list(references.keys())}.")

        reference = references[name]
        ref_type = _validate_params_single(parameter, reference, name)
        if ref_type:
            ref_of = reference.get('of', None)
            if ref_type == dict:
                _validate_params(parameter, ref_of, rec_name=name)
            else:  # List, tuple or ndarray type
                for i, parameter_elem in enumerate(parameter):
                    _validate_params_single(
                        parameter_elem, ref_of, f"{name}[{i}]")


def validate_params(parameters, references, exclude=None):
    """Function to automate the validation of (hyper)parameters.

    Parameters
    ----------
    parameters : dict, required
        Dictionary in which the keys parameter names (as strings) and the
        corresponding values are parameter values. Unless `exclude` (see
        below) contains some of the keys in this dictionary, all parameters
        are checked against `references`.

    references : dict, required
        Dictionary in which the keys are parameter names (as strings). Let
        ``name`` and ``parameter`` denote a key-value pair in `parameters`.
        Since ``name`` should also be a key in `references`, let ``reference``
        be the corresponding value there. Then, ``reference`` must be a
        dictionary containing any of the following keys:

        - ``'type'``, mapping to a class or tuple of classes. ``parameter``
          is checked to be an instance of this class or tuple of classes.

        - ``'in'``, mapping to a dictionary, when the value of ``'type'`` is
          not one of ``list``, ``tuple``, ``numpy.ndarray`` or ``dict``.
          Letting ``ref_in`` denote that dictionary, the following check is
          performed: ``parameter in ref_in``.

        - ``'of'``, mapping to a dictionary, when the value of ``'type'``
          is one of ``list``, ``tuple``, ``numpy.ndarray`` or ``dict``.
          Let ``ref_of`` denote that dictionary. Then:

          a) If ``reference['type'] == dict`` – meaning that ``parameter``
             should be a dictionary – ``ref_of`` should have a similar
             structure as `references`, and :func:`validate_params` is called
             recursively on ``(parameter, ref_of)``.
          b) Otherwise, ``ref_of`` should have a similar structure as
             ``reference`` and each entry in ``parameter`` is checked to
             satisfy the constraints in ``ref_of``.

        - ``'other'``, which should map to a callable defining custom checks on
          ``parameter``.

    exclude : list of str, or None, optional, default: ``None``
        List of parameter names which are among the keys in `parameters` but
        should be excluded from validation. ``None`` is equivalent to
        passing the empty list.

    """
    exclude_ = [] if exclude is None else exclude
    parameters_ = {key: value for key, value in parameters.items()
                   if key not in exclude_}
    return _validate_params(parameters_, references)
