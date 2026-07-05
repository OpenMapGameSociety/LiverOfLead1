/**
 * @file quadtree.h
 * @author RF
 * @brief Quadtree data representations for the TerrainMap LOD
 * @version 0.1
 * @date 2026-06-26
 *
 * @copyright Copyright OpenMapGameSociety (c) 2026
 *
 */

#pragma once

#include <vector>

#include "godot_cpp/variant/vector2.hpp"

using namespace godot;

/**
 * @brief 2D Quadtree structure
 * This class implements a 2D Quadtree. It is used in TerrainMap to represent efficiently large span of Terrain
 * by subdividing it into multiple squares.
 * The quadtree object can be iterated upon to get its different childs
 */
class Quadtree {
public:
	/**
	 * @brief Construct a new Quadtree object
	 *
	 * @param position The position of the quadtree (Upper left corner)
	 * @param size Size of the current slice
	 * @param level Current depth
	 */
	Quadtree(Vector2 position, float size, int level);

	/**
	 * @brief Subdivide this quadtree into 4 other quadtrees
	 *
	 * @return int The depth of the created quadtrees
	 */
	int subdivide();

	/**
	 * @brief Get the position of the quadtree
	 *
	 * @return Vector2
	 */
	Vector2 get_position();

	/**
	 * @brief Get the current size of the quadtree
	 *
	 * @return float
	 */
	float get_size();

	/**
	 * @brief Get the current depth of the quadtree
	 *
	 * @return int
	 */
	int get_level();

	/**
	 * @brief Return if the quadtree is subdivided or not
	 *
	 * @return true
	 * @return false
	 */
	bool is_leaf();

	/**
	 * @brief Iterator begin functions, allow the Quadtree to be used in a for loop
	 *
	 * @return auto
	 */
	auto begin();
	/**
	 * @brief Iterator end functions, allow the Quadtree to be used in a for loop
	 *
	 * @return auto
	 */
	auto end();

private:
	Vector2 position_;
	float size_;
	int level_;
	bool leaf_;
	std::vector<Quadtree> childs_;
};