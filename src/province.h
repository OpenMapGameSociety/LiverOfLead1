#pragma once

#include "godot_cpp/classes/ref_counted.hpp"
#include "godot_cpp/classes/image.hpp"
#include "godot_cpp/classes/wrapped.hpp"
#include "godot_cpp/variant/variant.hpp"

using namespace godot;

class Province : public RefCounted {
    GDCLASS(Province, RefCounted)
    
    private:
        String name;
        int id;
        int size;
    
    public:
        Province(String p_name, int p_id, int p_size) : name(p_name), id(p_id), size(p_size) {};
        String get_name() const;
        int get_id() const;
        int get_size() const;
    
};
    
    