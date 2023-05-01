# SoftBodyOlympics
This project was created as a final project for the Course ["Physically-based Simulation"](https://cgl.ethz.ch/teaching/simulation21/home.php) during the Autumn Semster 2021 at ETHZ. 

![sumo gameplay](images/sumo-gameplay.gif "sumo gameplay") ![multiplayer client](images/multiplayer-client.gif "multiplayer client")

Soft Body Olympics is a versus game leveraging online multiplayer and compute shaders to simulate a game with one soft body per player where these soft bodies can collide with each other and are tasked to compete in different stages, ranging from Sumo (Stay in the ring) to racing.

## Game
The game is implemented in Python and uses the compute shader library ![Taichi](https://www.taichi-lang.org/) for all simulations and pyglet for the UI. The input is fetched via webrequests to a Golang backend.

## Multiplayer Aspect and Infrastructure
The games can be played by up to 20 simultanious players using web capable devices like smartphones. Player connect to a website where they are assigned a player number and color and are shown a joystick with which they can control their agent. This is shown in the gif above.

# Watch the Presentation (Link to YouTube)
[![Watch the Presentation](https://img.youtube.com/vi/eFkBWQ_0fTQ/maxresdefault.jpg)](https://youtu.be/eFkBWQ_0fTQ)
