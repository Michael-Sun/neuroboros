import numpy as np
import scipy.sparse as sparse

from .properties import compute_neighbor_distances, compute_vertex_areas
from .dijkstra import dijkstra


def compute_vertex_nn(nv, indices2, neighbors, neighbor_distances):
    nn = np.zeros((nv, ), dtype=int)
    nnd = np.full((nv, ), np.inf)
    for src in indices2:
        nbrs, dists = dijkstra(src, nv, neighbors, neighbor_distances, max_dist=3.0)
        for nbr, d in zip(nbrs, dists):
            if nnd[nbr] > d:
                nnd[nbr] = d
                nn[nbr] = src

    for max_dist in [4.0, 5.0, 6.0, 8.0, 10.0, np.inf]:
        for src in np.where(np.isinf(nnd))[0]:
            nbrs, dists = dijkstra(src, nv, neighbors, neighbor_distances, max_dist=max_dist)
            idx = np.where(np.isin(nbrs, indices2))[0]
            if len(idx):
                nnd[src] = dists[idx[0]]
                nn[src] = nbrs[idx[0]]

    mapping = np.zeros((nv, ), dtype=int)
    mapping[indices2] = np.arange(len(indices2))
    nn = mapping[nn]

    return nn


def areal(sphere, new_coords, anat_coords):
    combined_sphere, indices0, indices1 = sphere.union(new_coords)
    xform = sphere.barycentric(combined_sphere.coords)
    combined_coords = xform.T @ anat_coords
    assert combined_coords.shape == combined_sphere.coords.shape
    nv, neighbors = combined_sphere.nv, combined_sphere.neighbors
    neighbor_distances = compute_neighbor_distances(
        combined_coords, neighbors)

    nn0 = compute_vertex_nn(nv, indices0, neighbors, neighbor_distances)
    nn1 = compute_vertex_nn(nv, indices1, neighbors, neighbor_distances)
    vertex_areas = compute_vertex_areas(combined_coords, combined_sphere.faces)
    mat = sparse.lil_matrix((sphere.nv, new_coords.shape[0]))

    for n0, n1, va in zip(nn0, nn1, vertex_areas):
        mat[n0, n1] += va
    mat = mat.tocsr()

    return mat