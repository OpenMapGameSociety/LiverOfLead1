#pragma once

#include "godot_cpp/classes/mesh_instance3d.hpp"
#include "godot_cpp/classes/array_mesh.hpp"
#include "godot_cpp/classes/image.hpp"
#include "godot_cpp/classes/wrapped.hpp"
#include "godot_cpp/variant/array.hpp"
#include "godot_cpp/variant/variant.hpp"
#include "godot_cpp/variant/vector3.hpp"

using namespace godot;

class Map: public MeshInstance3D {
    GDCLASS(Map, MeshInstance3D)

    private:
        Image *map_image;
        ArrayMesh *mesh;

    public:
        Map();
        ~Map();

        void set_map_image(Image *image);

        Image *get_map_image() const;
};