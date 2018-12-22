# TODO:
# 1. You'll have to construct cubes by creating 6 square faces that you arrange, making
# each square a part of the cube model
# 2. Load this texture and basically set it to black and white
# 3. instead of setColor you'll use setColorScale to layer colors over the texture
# 4. complete example in the shadows sample
    # Load the scene.
    floorTex = loader.loadTexture('maps/envir-ground.jpg')

    cm = CardMaker('')
    cm.setFrame(-2, 2, -2, 2)
    #wo_front = render.attachNewNode(PandaNode("wo_front"))
    for y in range(10):
      for x in range(10):
        nn = wo_front.model.attachNewNode(cm.generate())
        nn.setP(-90)
        nn.setPos(x*4-10, y*4-10, -10)
    wo_front.model.setTexture(floorTex)
    wo_front.model.flattenStrong()
    wo_front.model.setR(-90)
    wo_front.model.setColorScale(0.7,0,0,1)
