#include "map.h"

void Map::_ready() {
    // This function is called when the node is added to the scene.
    // You can use it to initialize your node or perform any setup tasks.
    Array surfaceArray = Array();
    surfaceArray.resize(Mesh::ARRAY_MAX);
    PackedVector3Array verts;
    PackedVector2Array uvs;
    PackedVector3Array normals;
    PackedInt32Array indices;

    verts.append(Vector3(0, 0, 0));
    verts.append(Vector3(0, 0, 1));
    verts.append(Vector3(1, 0, 0));
    verts.append(Vector3(1, 0, 1));

    uvs.append(Vector2(0, 0));
    uvs.append(Vector2(1, 0));
    uvs.append(Vector2(0, 1));
    uvs.append(Vector2(1, 1));

    normals.append(Vector3(0, 1, 0));
    normals.append(Vector3(0, 1, 0));
    normals.append(Vector3(0, 1, 0));
    normals.append(Vector3(0, 1, 0));

    indices.append(0);
    indices.append(2);
    indices.append(1);
    indices.append(2);
    indices.append(3);
    indices.append(1);

    surfaceArray[Mesh::ARRAY_VERTEX] = verts;
    surfaceArray[Mesh::ARRAY_TEX_UV] = uvs;
    surfaceArray[Mesh::ARRAY_NORMAL] = normals;
    surfaceArray[Mesh::ARRAY_INDEX] = indices;

    mesh->add_surface_from_arrays(Mesh::PRIMITIVE_TRIANGLES, surfaceArray);

};