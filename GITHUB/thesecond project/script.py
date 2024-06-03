# -*- coding: utf-8 -*-
"""script.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1T9qw5onld7auEDP3KmR0dG_YrkM_jPHx
"""

!pip install plyfile

import numpy as np
import random
import math
!pip install path.py;
from path import Path
!wget http://3dvision.princeton.edu/projects/2014/3DShapeNets/ModelNet10.zip
!unzip -q ModelNet10.zip

path = Path("ModelNet10")

def read_off(file):
    if 'OFF' != file.readline().strip():
        raise('Not a valid OFF header')
    n_verts, n_faces, __ = tuple([int(s) for s in file.readline().strip().split(' ')])
    verts = [[float(s) for s in file.readline().strip().split(' ')] for i_vert in range(n_verts)]
    faces = [[int(s) for s in file.readline().strip().split(' ')][1:] for i_face in range(n_faces)]
    return verts, faces

with open(path/"table/train/table_0001.off", 'r') as f:
    mesh = read_off(f)
verts, faces = mesh
areas = np.zeros((len(faces)))
verts = np.array(verts)

# function to calculate triangle area by its vertices
# https://en.wikipedia.org/wiki/Heron%27s_formula
def triangle_area(pt1, pt2, pt3):
    side_a = np.linalg.norm(pt1 - pt2)
    side_b = np.linalg.norm(pt2 - pt3)
    side_c = np.linalg.norm(pt3 - pt1)
    s = 0.5 * ( side_a + side_b + side_c)
    return max(s * (s - side_a) * (s - side_b) * (s - side_c), 0)**0.5

# we calculate areas of all faces in our mesh
for i in range(len(areas)):
    areas[i] = (triangle_area(verts[faces[i][0]],
                              verts[faces[i][1]],
                              verts[faces[i][2]]))

k = 3000
# we sample 'k' faces with probabilities proportional to their areas
# weights are used to create a distribution.
# they don't have to sum up to one.
sampled_faces = (random.choices(faces,
                                weights=areas,
                                k=k))

# function to sample points on a triangle surface
def sample_point(pt1, pt2, pt3):
    # barycentric coordinates on a triangle
    # https://mathworld.wolfram.com/BarycentricCoordinates.html
    s, t = sorted([random.random(), random.random()])
    f = lambda i: s * pt1[i] + (t-s) * pt2[i] + (1-t) * pt3[i]
    return (f(0), f(1), f(2))

pointcloud = np.zeros((k, 3))

# sample points on chosen faces for the point cloud of size 'k'
for i in range(len(sampled_faces)):
    pointcloud[i] = (sample_point(verts[sampled_faces[i][0]],
                                  verts[sampled_faces[i][1]],
                                  verts[sampled_faces[i][2]]))
import numpy as np
import random
import matplotlib.pyplot as plt
import pandas as pd
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from scipy.spatial import ConvexHull

# Assuming 'pointcloud' is your numpy array of sampled points

from plyfile import PlyData, PlyElement

# Assuming 'pointcloud' is your generated point cloud
data = np.array([(x, y, z) for x, y, z in pointcloud], dtype=[('x', 'f4'), ('y', 'f4'), ('z', 'f4')])

ply_data = PlyData([
    PlyElement.describe(data, 'vertex', comments=['Generated by Python'])
])

# Save the PLY file
ply_data.write('pointcloud.ply')

!pip install pyntcloud

from pyntcloud import PyntCloud
# Create a PyntCloud object
cloud = PyntCloud(pd.DataFrame(pointcloud, columns=["x", "y", "z"]))

# Sample points on the point cloud (if not already sampled)

# Create a convex hull from the sampled points
hull = ConvexHull(cloud.points[["x", "y", "z"]].values)

# Extract triangles from the convex hull
triangles = hull.simplices

# Calculate areas of triangles using the cross product
def triangle_area(pt1, pt2, pt3):
    v1 = pt2 - pt1
    v2 = pt3 - pt1
    cross_product = np.cross(v1, v2)
    area = 0.5 * np.linalg.norm(cross_product)
    return area

areas = [triangle_area(cloud.points.iloc[triangle[0]].to_numpy(),
                       cloud.points.iloc[triangle[1]].to_numpy(),
                       cloud.points.iloc[triangle[2]].to_numpy()) for triangle in triangles]

# Choose a threshold to filter out small triangles
threshold = 0.1  # Adjust as needed

# Filter triangles based on area
filtered_triangles = [triangle for triangle, area in zip(triangles, areas) if area > threshold]

# Convert vertex indices to their corresponding coordinates
verts = [cloud.points[["x", "y", "z"]].iloc[triangle].to_numpy() for triangle in filtered_triangles]

# Visualize the point cloud and reconstructed surface (optional)
fig = plt.figure()
ax = fig.add_subplot(121, projection='3d')
ax.scatter(cloud.points.x, cloud.points.y, cloud.points.z, s=0.1, c='r', marker='.')
ax.set_title("Point Cloud")

ax = fig.add_subplot(122, projection='3d')
ax.add_collection3d(Poly3DCollection(verts, alpha=0.1, edgecolor='k'))
ax.set_title("Reconstructed Surface")

ax.set_xlim([np.min(cloud.points.x), np.max(cloud.points.x)])
ax.set_ylim([np.min(cloud.points.y), np.max(cloud.points.y)])
ax.set_zlim([np.min(cloud.points.z), np.max(cloud.points.z)])


plt.show()
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from scipy.spatial import Delaunay

# Assuming 'pointcloud' is your numpy array of sampled points

# Perform Delaunay triangulation
triangulation = Delaunay(pointcloud[:, :2])  # Assuming 2D coordinates for simplicity

triangles = pointcloud[triangulation.simplices]

fig = plt.figure()
ax = fig.add_subplot(121, projection='3d')
ax.scatter(pointcloud[:, 0], pointcloud[:, 1], pointcloud[:, 2], s=0.1, c='r', marker='.')
ax.set_title("Point Cloud")

ax = fig.add_subplot(122, projection='3d')
ax.add_collection3d(Poly3DCollection(triangles, alpha=0.1, edgecolor='k'))
ax.set_title("Output CAD Surface")
ax.set_xlim([np.min(cloud.points.x), np.max(cloud.points.x)])
ax.set_ylim([np.min(cloud.points.y), np.max(cloud.points.y)])
ax.set_zlim([np.min(cloud.points.z), np.max(cloud.points.z)])
plt.show()

with open("reconstructed_surface.stl", "w") as f:
    f.write("solid reconstructed_surface\n")
    for triangle in triangles:
        for vertex in triangle:
            f.write(f"vertex {vertex[0]} {vertex[1]} {vertex[2]}\n")
    f.write("endsolid reconstructed_surface\n")