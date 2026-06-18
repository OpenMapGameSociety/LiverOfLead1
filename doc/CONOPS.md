# Liver Of Lead 1 Game Condition Of Operation
This document is used to specify the scope of the H2OI game.

## Project Abstract
This project proposes a new modular design for organic real time 3D map game. Modular because it will allow easy modification through mods. The game will use lock steps and a deterministic model in order to synchronize multiplayer, allowing a large number of player to easily play multiplayer games. The modularity will allow multiple scenario, a scenario can be the Normandy Landing, The 100 years War, or even the full WW2 from 1939 to 1945.

### High Level Requirement
- Real Time strategic 3D game, using a system of provinces
- Limited Scope Scenarios, possible to expand it to full scale war and multiple theaters. The scaling is handled by the engine itself.
- Modular design, allowing easy integration of mods and custom scenarios
- Locksteps for the multiplayer, allowing a large number of player to play the same game.

### Conceptual Design
From the backend to the frontend:
- The static database: Maps, what country can do, the starting situation, the different buff possible, etc... It is everthing that is fixed and parsed at the start.
- The dynamic database: Unit created, what actions entities are doing, ongoing combats, etc... . It is everything that describe a running game. that will generate the savegame.
- The engine: Every effect possibles, gives functions like Create_Unit, Start_War, etc... Writen in C++. It also handle the multiplayer synchronization.
- Scripting: Part of the static database, it is the mechanics that use the engine functions to create the scenario. Writen in GDScript.
- The display is just a representation of the copmplete database: Doing action in the UI execute scripts that call function from the engines to change the state of the game (Modify the database)

The game will try to stay multiplatform as much as possible

### Required Resources
The Godot engine gives a good basic framework to implement our project. The engin will be written in C++ with the godot-cpp extension. Other needed library will be added if needed during development.


### Background & References
See HoI4 :)
