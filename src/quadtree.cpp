#include "quadtree.h"

Quadtree::Quadtree(Vector2 position, float size, int level) : position_(position), size_(size), level_(level) {
	leaf_ = false;
}

int Quadtree::subdivide() {
	Vector2 positions[] = {
		Vector2(position_.x + size_ / 2, position_.y),
		Vector2(position_.x, position_.y),
		Vector2(position_.x, position_.y + size_ / 2),
		Vector2(position_.x + size_ / 2, position_.y + size_ / 2)
	};
	leaf_ = true;
	if (!leaf_) {
		childs_.push_back(Quadtree(positions[0], size_ / 2, level_ + 1));
		childs_.push_back(Quadtree(positions[0], size_ / 2, level_ + 1));
		childs_.push_back(Quadtree(positions[0], size_ / 2, level_ + 1));
		childs_.push_back(Quadtree(positions[0], size_ / 2, level_ + 1));
		return level_ + 1;
	}
	childs_[0] = Quadtree(positions[0], size_ / 2, level_ + 1);
	childs_[1] = Quadtree(positions[0], size_ / 2, level_ + 1);
	childs_[2] = Quadtree(positions[0], size_ / 2, level_ + 1);
	childs_[3] = Quadtree(positions[0], size_ / 2, level_ + 1);
	return level_ + 1;
}

Vector2 Quadtree::get_position() {
	return position_;
}

float Quadtree::get_size() {
	return size_;
}

int Quadtree::get_level() {
	return level_;
}

bool Quadtree::is_leaf() {
	return leaf_;
}

auto Quadtree::begin() {
	return childs_.begin();
}
auto Quadtree::end() {
	return childs_.end();
}